# ruff: noqa: E741

import time
import random
import dataclasses
import enum
from typing import Callable
import threading

from tetris_game import game_data


class GameStatus(enum.IntEnum):
    # Game not started yet
    READY = enum.auto()
    # Game in progress
    PLAYING = enum.auto()
    # Game paused
    PAUSED = enum.auto()
    # Game completed
    GAME_OVER = enum.auto()
    # Game exited early
    QUIT = enum.auto()

class Piece(enum.IntEnum):
    NULL = 0
    I = 1
    L = 2
    J = 3
    S = 4
    Z = 5
    T = 6
    O = 7

@dataclasses.dataclass
class TetrisGameState:

    status: GameStatus

    score: int
    level: int
    lines_cleared: int

    falling_piece: Piece
    falling_piece_rot: int
    falling_piece_bb_x: int
    falling_piece_bb_y: int

    next_piece: Piece
    held_piece: Piece
    held_already: bool

    board_data: list[int]

    def __post_init__(self):
        if len(self.board_data) != TetrisGame.BOARD_WIDTH * TetrisGame.BOARD_HEIGHT:
            raise ValueError(f"Game board data must be an array of length {TetrisGame.BOARD_WIDTH * TetrisGame.BOARD_HEIGHT}, got {len(self.board_data)}")
    
    def get_board(self, x: int, y: int) -> Piece:
        """
        Gets the value of a specific position on the board
        """
        return self.board_data[y * TetrisGame.BOARD_WIDTH + x]

    def set_board(self, x: int, y: int, value: int) -> int:
        """
        Sets the value at a specific position on the board, returning the old value
        """
        old = self.board_data[y * TetrisGame.BOARD_WIDTH + x]
        self.board_data[y * TetrisGame.BOARD_WIDTH + x] = value
        return old

    def copy(self) -> 'TetrisGameState':
        return dataclasses.replace(self, board_data=list(self.board_data))

    def get_speed(self) -> float:
        """
        Calculate current G-value of falling pieces
        """
        if self.level <= 0:
            raise ValueError(f"Invalid level: {self.level}")
        elif self.level < len(game_data.LEVEL_SPEEDS):
            return game_data.LEVEL_SPEEDS[self.level - 1]
        else:
            return game_data.LEVEL_SPEEDS[-1]
    
    def falling_piece_cells(self) -> list[tuple[int, int]]:
        """
        Returns the cell positions of all the blocks in the falling piece
        """
        a = [(x + self.falling_piece_bb_x, y + self.falling_piece_bb_y) for x, y in game_data.PIECE_SHAPES[self.falling_piece][self.falling_piece_rot]]
        return a



class TetrisGame:
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 40

    FPS = 60.0
    FRAME_DURATION = 1.0 / FPS

    # delayed auto start
    DAS_ENTRY = 10 # frames
    DAS_RATE = 2 # frames

    # lock delay
    LOCK_DELAY_MOVES = 15
    LOCK_DELAY_TIME = 0.5

    def __init__(self, state_change_callback: Callable | None = None):
        """
        Create a new game.

        Args:
         - state_change_callback: Callable | None - Optional callback to be
            called after each frame, with a `TetrisGameState` object passed as
            the first argument
        """

        self._state_change_callback: Callable | None = state_change_callback

        self._frame: int = 0

        self._piece_queue = self._piece_generator()

        self._state = TetrisGameState(
            status=GameStatus.READY,
            score=0,
            level=1,
            lines_cleared=0,
            falling_piece=next(self._piece_queue),
            falling_piece_bb_x=0,
            falling_piece_bb_y=0,
            falling_piece_rot=0,
            next_piece=next(self._piece_queue),
            held_piece=Piece.NULL,
            held_already=False,
            board_data=[Piece.NULL] * (TetrisGame.BOARD_WIDTH * TetrisGame.BOARD_HEIGHT)
        )

        # place starting piece at top
        self._new_piece()

        # variables to track if keys are being held for DAS (delayed auto shift)
        self._das_left_press_frame: int | None = None
        self._das_right_press_frame: int | None = None
        self._das_down_press_frame: int | None = None

        self._piece_grounded = False
        self._lock_delay_start_t: float = 0.0
        self._lock_delay_moves: int = 0

        self._bg_thread = threading.Thread(target=self._background_routine, name="tetris_game_thread", daemon=True)
        self._bg_thread.start()
    
    def _background_routine(self):

        prev_gravity_frame = self._frame
        prev_frame_t = time.perf_counter()

        while True:
            if self._state.status == GameStatus.READY or self._state.status == GameStatus.PAUSED:
                # idle until game starts/resumes
                time.sleep(0.1)

            elif self._state.status == GameStatus.PLAYING:
                current_t = time.perf_counter()
                delta_t = current_t - prev_frame_t
                if delta_t < TetrisGame.FRAME_DURATION:
                    # not yet time for a new frame
                    time.sleep(0.0) # yield thread
                    continue
                prev_frame_t = current_t

                # delayed auto shift
                for press_start_frame, action in (
                    (self._das_left_press_frame, self.shift_left), 
                    (self._das_right_press_frame, self.shift_right),
                    (self._das_down_press_frame, self.soft_drop)
                ):
                    if press_start_frame is not None:
                        hold_duration = self._frame - press_start_frame
                        if hold_duration > TetrisGame.DAS_ENTRY and hold_duration % TetrisGame.DAS_RATE == 0:
                            action()
                            self._check_piece_pos()
                
                if not self._piece_grounded:
                    # do gravity
                    if float(self._frame) >= float(prev_gravity_frame) + (1.0 / self._state.get_speed()):
                        self._fall()
                        prev_gravity_frame = self._frame
                else:
                    # lock delay
                    if current_t >= self._lock_delay_start_t + TetrisGame.LOCK_DELAY_TIME:
                        # ran out of time, lock it in
                        self._fall()

                
                self._do_state_change_callback()

                self._frame += 1
            else:
                # game done
                break

    def _do_state_change_callback(self):
        if self._state_change_callback is not None:
            self._state_change_callback(self.get_state())
    
    
    def start(self):
        """
        Start the game, does nothing if game has already been started
        """
        if self._state.status == GameStatus.READY:
            self._state.status = GameStatus.PLAYING
            self._do_state_change_callback()

    def toggle_pause(self):
        """
        Pause or unpause game
        """
        if self._state.status == GameStatus.PAUSED:
            self._state.status = GameStatus.PLAYING
            self._do_state_change_callback()
        elif self._state.status == GameStatus.PLAYING:
            self._state.status = GameStatus.PAUSED
            self._do_state_change_callback()

    def quit(self):
        """
        Quit the game
        """
        self._state.status = GameStatus.QUIT
        self._do_state_change_callback()
    
    def join(self):
        """
        Block until game is finished
        """
        if self._bg_thread.is_alive():
            self._bg_thread.join()
    
    def get_state(self) -> TetrisGameState:
        return self._state.copy()

    def shift_left(self, hold: bool | None = None):
        """
        Attempts to move the falling piece to the left

        Args:
         - hold: bool | None - If provided, this function is treated as the 
           start (if True) or end (if False) of "holding down the left button".
           If omitted, this function is treated as a quick "down-up"
        """
        if self._state.status != GameStatus.PLAYING:
            return

        if hold is None or hold:
            # checking if any pieces would be out of bounds
            for x, y in self._state.falling_piece_cells():
                if x <= 0 or self._state.get_board(x-1, y) != Piece.NULL:
                    return

            # move
            self._state.falling_piece_bb_x -= 1

            self._check_lock_delay()
            self._check_piece_pos()
            self._do_state_change_callback()

            if hold is not None:
                # hold on
                self._das_left_press_frame = self._frame
        else:
            # hold off
            self._das_left_press_frame = None

    def shift_right(self, hold: bool | None = None):
        """
        Attempts to move the falling piece to the right

        Args:
         - hold: bool | None - If provided, this function is treated as the 
           start (if True) or end (if False) of "holding down the right button".
           If omitted, this function is treated as a quick "down-up"
        """
        if self._state.status != GameStatus.PLAYING:
            return

        if hold is None or hold:
            # checking if any pieces would be out of bounds
            for x, y in self._state.falling_piece_cells():
                if x >= TetrisGame.BOARD_WIDTH - 1 or self._state.get_board(x+1, y) != Piece.NULL:
                    return
            # move
            self._state.falling_piece_bb_x += 1

            self._check_lock_delay()
            self._check_piece_pos()
            self._do_state_change_callback()

            if hold is not None:
                # hold on
                self._das_right_press_frame = self._frame
        else:
            # hold off
            self._das_right_press_frame = None
    
    
    def soft_drop(self, hold: bool | None = None):
        """
        Attempts to move the falling piece to the left

        Args:
         - hold: bool | None - If provided, this function is treated as the 
           start (if True) or end (if False) of "holding down the left button".
           If omitted, this function is treated as a quick "down-up"
        """
        if self._state.status != GameStatus.PLAYING:
            return

        if hold is None or hold:
            self._fall()
            if hold is not None:
                # hold on
                self._das_down_press_frame = self._frame
        else:
            # hold off
            self._das_down_press_frame = None

    def hard_drop(self):
        """
        Move piece down until it lands
        """
        if self._state.status != GameStatus.PLAYING:
            return

        while not self._fall():
            pass

    def rotate_cw(self):
        """
        Attempts to rotate the falling piece clockwise
        """
        if self._state.status != GameStatus.PLAYING:
            return
            
        # TODO SRS
        self._state.falling_piece_rot = (self._state.falling_piece_rot + 1) % 4
        self._check_piece_pos()
        self._do_state_change_callback()

    def rotate_ccw(self):
        """
        Attempts to rotate the falling piece counter-clockwise
        """
        if self._state.status != GameStatus.PLAYING:
            return

        # TODO SRS
        self._state.falling_piece_rot = (self._state.falling_piece_rot - 1) % 4
        self._check_piece_pos()
        self._do_state_change_callback()

    def hold(self):
        """
        Attempts to hold a piece
        """
        if self._state.status != GameStatus.PLAYING:
            return

        if not self._state.held_already:
            self._state.held_already = True
            if self._state.held_piece == Piece.NULL:
                # no piece has been held yet, get next piece from queue
                self._state.held_piece = self._state.falling_piece
                self._new_piece()
            else:
                # bank current piece, spawn instance of held piece
                last_held_piece = self._state.held_piece
                self._state.held_piece = self._state.falling_piece
                self._new_piece(last_held_piece)

    def _fall(self) -> bool:
        """
        Move the falling piece down and handle landing logic. Returns True if
        the piece lands and is locked in
        """

        if self._piece_grounded:
            # piece is already touching the ground, lock it in

            for x, y in self._state.falling_piece_cells():
                if y >= 21:
                    self._game_over()
                    return True
                self._state.set_board(x, y, self._state.falling_piece)
            
            # check for line clears
            cleared_lines = 0
            for y in range(TetrisGame.BOARD_HEIGHT):
                cleared = True
                for piece in self._state.board_data[(y*TetrisGame.BOARD_WIDTH):((y+1)*TetrisGame.BOARD_WIDTH)]:
                    if piece == Piece.NULL:
                        cleared = False
                        break
                if cleared_lines != 0:
                    # move this line down if lines under this have been cleared
                    target_y = y - cleared_lines
                    self._state.board_data[(target_y*TetrisGame.BOARD_WIDTH):((target_y+1)*TetrisGame.BOARD_WIDTH)] = self._state.board_data[(y*TetrisGame.BOARD_WIDTH):((y+1)*TetrisGame.BOARD_WIDTH)]
                if cleared:
                    cleared_lines += 1
            self._state.lines_cleared += cleared_lines
            
            # spawn new piece
            self._state.held_already = False
            self._new_piece()

            return True
        else:
            # piece is not already touching the ground, move it down
            self._state.falling_piece_bb_y -= 1
            self._check_piece_pos()
            return False

    def _check_piece_pos(self):
        """
        Checks if a piece is clipped or touching the ground, and handles it.
        This function is to be called after the piece moves
        """
        for x, y in self._state.falling_piece_cells():
            if self._state.get_board(x, y) != Piece.NULL:
                self._game_over()
                return
            elif not self._piece_grounded and (y == 0 or self._state.get_board(x, y-1) != Piece.NULL):
                self._piece_grounded = True
                self._lock_delay_start_t = time.perf_counter()
                self._lock_delay_moves = TetrisGame.LOCK_DELAY_MOVES
                return
    
    def _check_lock_delay(self):
        """
        Checks if lock delay is out of moves, and handles it
        This function is to be called after the piece moves
        """
        if self._piece_grounded:
            if self._lock_delay_moves == 0:
                # lock in piece, ran out of lock delay moves
                self._fall()
                self._lock_delay_moves = TetrisGame.LOCK_DELAY_MOVES
            else:
                self._lock_delay_start_t = time.perf_counter()
                self._lock_delay_moves -= 1
    
    def _game_over(self):
        self._state.status = GameStatus.GAME_OVER
        self._do_state_change_callback()

    def _new_piece(self, peice_override: Piece | None = None):
        """
        Pops the next piece from queue (unless overridden), places it in its
        spawn location, and checks for game over induced by spawning being
        inhibited
        """

        if peice_override is not None:
            self._state.falling_piece = peice_override
        else:
            self._state.falling_piece = self._state.next_piece
            self._state.next_piece = next(self._piece_queue)

        # place it at top of board
        self._state.falling_piece_rot = 0
        self._state.falling_piece_bb_x = int((TetrisGame.BOARD_WIDTH / 2) - 2)
        self._state.falling_piece_bb_y = 20 
        if self._state.falling_piece == Piece.I:
            self._state.falling_piece_bb_y -= 1 # I piece needs to start one lower cus bigger bounding box
        self._piece_grounded = False

        self._check_piece_pos()
        self._do_state_change_callback()
    
    def _piece_generator(self):
        """
        Infinite generator for pieces, using the 7-bag strategy
        """
        while True:
            bag = list([Piece.I, Piece.L, Piece.J, Piece.S, Piece.Z, Piece.T, Piece.O])

            while len(bag) > 0:
                choice_index = random.randint(0, len(bag) - 1)
                choice = bag[choice_index]
                bag.pop(choice_index)
                yield choice
         

