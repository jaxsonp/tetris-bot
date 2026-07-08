# ruff: noqa: E741

import time
import random
from collections import deque
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
    FINISHED = enum.auto()
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

_FULL_SEVEN_BAG = [Piece.I, Piece.L, Piece.J, Piece.S, Piece.Z, Piece.T, Piece.O]

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

    def __init__(self, update_callback: Callable | None = None):
        """
        Create a new game.

        Args:
         - update_callback: Callable | None - Optional callback to be called
            after each frame, with a `TetrisGameState` object passed as the
            first argument
        """

        self._update_callback: Callable | None = update_callback

        self._frame: int = 0

        self._piece_queue: deque[Piece] = deque()
        self._extend_piece_queue()
        assert len(self._piece_queue) >= 2

        self._state = TetrisGameState(
            status=GameStatus.READY,
            score=0,
            level=1,
            lines_cleared=0,
            falling_piece=self._piece_queue.popleft(),
            falling_piece_bb_x=0,
            falling_piece_bb_y=0,
            falling_piece_rot=0,
            next_piece=self._piece_queue.popleft(),
            held_piece=Piece.NULL,
            held_already=False,
            board_data=[Piece.NULL] * (TetrisGame.BOARD_WIDTH * TetrisGame.BOARD_HEIGHT)
        )

        # place starting piece at top
        self._place_new_piece()

        # variables to track if keys are being held for DAS (delayed auto shift)
        self._das_left_press_frame: int | None = None
        self._das_right_press_frame: int | None = None
        self._das_down_press_frame: int | None = None

        self._piece_grounded = False
        self._lock_delay_start_t: float | None = None
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
                
                # gravity
                if float(self._frame) >= float(prev_gravity_frame) + (1.0 / self._state.get_speed()):
                    self._fall()
                    prev_gravity_frame = self._frame
                
                if self._update_callback is not None:
                    self._update_callback(self._state.copy())

                self._frame += 1
            else:
                # game done
                break
    
    def start(self):
        """
        Start the game
        """
        if self._state.status != GameStatus.READY:
            raise RuntimeError("TetrisGame.start() called after game already started")

        self._state.status = GameStatus.PLAYING

    def quit(self):
        """
        Quit the game
        """
        self._state.status = GameStatus.QUIT
    
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
        if hold is None or hold:
            
            # checking if any pieces would be out of bounds
            for x, _ in self._state.falling_piece_cells():
                if x <= 0:
                    return
            # move
            self._state.falling_piece_bb_x -= 1

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
        if hold is None or hold:
            
            # checking if any pieces would be out of bounds
            for x, _ in self._state.falling_piece_cells():
                if x >= TetrisGame.BOARD_WIDTH - 1:
                    return
            # move
            self._state.falling_piece_bb_x += 1

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
        while self._fall():
            pass

    def rotate_cw(self):
        """
        Attempts to rotate the falling piece clockwise
        """
        # TODO SRS
        self._state.falling_piece_rot = (self._state.falling_piece_rot + 1) % 4

    def rotate_ccw(self):
        """
        Attempts to rotate the falling piece counter-clockwise
        """
        # TODO SRS
        self._state.falling_piece_rot = (self._state.falling_piece_rot - 1) % 4

    def hold(self):
        """
        Attempts to hold a piece
        """
        if not self._state.held_already:
            last_held_piece = self._state.held_piece

            # hold current piece
            self._state.held_piece = self._state.falling_piece
            self._state.held_already = True

            if last_held_piece != Piece.NULL:
                # pull out previously held piece if it exists
                self._state.falling_piece = last_held_piece
            else:
                # otherwise get next piece
                self._state.falling_piece = self._state.next_piece
                self._place_new_piece()

                if len(self._piece_queue) < 1:
                    self._extend_piece_queue()
                self._state.next_piece = self._piece_queue.popleft()
            
            # move piece to top
            self._place_new_piece()

    
    def _fall(self) -> bool:
        """
        Move the falling piece down and handle landing logic. Returns True if
        the piece lands and is locked in
        """

        if self._piece_grounded:
            # lock in piece
            for x, y in self._state.falling_piece_cells():
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
            self._state.falling_piece = self._state.next_piece
            self._place_new_piece()

            if len(self._piece_queue) == 0:
                self._extend_piece_queue()
            self._state.next_piece = self._piece_queue.popleft()

            self._piece_grounded = False
            return True
        else:
            self._state.falling_piece_bb_y -= 1
            for x, y in self._state.falling_piece_cells():
                if y == 0 or self._state.get_board(x, y-1) != Piece.NULL:
                    self._piece_grounded = True
                    # don't lock in this piece if it just landed
                    break
            return False

    def _place_new_piece(self):
        """
        Moves the current falling piece to its spawn location
        """
        self._state.falling_piece_rot = 0
        self._state.falling_piece_bb_x = 3
        self._state.falling_piece_bb_y = 19
    
    def _extend_piece_queue(self):
        bag = list(_FULL_SEVEN_BAG)
        while len(bag) > 0:
            choice_index = random.randint(0, len(bag) - 1)
            choice = bag[choice_index]
            bag.pop(choice_index)
            self._piece_queue.append(choice)
         

