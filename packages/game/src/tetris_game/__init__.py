import random
from collections import deque
import dataclasses

from .data import PIECE_DATA

BOARD_WIDTH = 10
BOARD_HEIGHT = 40
BOARD_DISPLAY_HEIGHT = 21

PIECE_NULL = 0
PIECE_I = 1
PIECE_L = 2
PIECE_J = 3
PIECE_S = 4
PIECE_Z = 5
PIECE_T = 6
PIECE_O = 7

_FULL_SEVEN_BAG = [PIECE_I, PIECE_L, PIECE_J, PIECE_S, PIECE_Z, PIECE_T, PIECE_O]

@dataclasses.dataclass
class TetrisGameState:

    score: int
    next_piece: int

    falling_piece: int
    falling_piece_rot: int
    falling_piece_bb_x: int
    falling_piece_bb_y: int
    falling_piece_cells: list[tuple[int, int]]

    board_data: list[int]

    def __post_init__(self):
        if len(self.board_data) != BOARD_WIDTH * BOARD_HEIGHT:
            raise ValueError(f"Game board data must be an array of length {BOARD_WIDTH * BOARD_HEIGHT}, got {len(self.board_data)}")
    
    def get_board(self, x: int, y: int) -> int:
        """
        Gets the value of a specific position on the board
        """
        return self.board_data[y * BOARD_WIDTH + x]

    def set_board(self, x: int, y: int, value: int) -> int:
        """
        Sets the value at a specific position on the board, returning the old value
        """
        old = self.board_data[y * BOARD_WIDTH + x]
        self.board_data[y * BOARD_WIDTH + x] = value
        return old

    def copy(self) -> 'TetrisGameState':
        return dataclasses.replace(self, board_data=list(self.board_data))

class TetrisGame:
    def __init__(self):

        # init board
        self._board: list[int] = [PIECE_NULL] * (BOARD_WIDTH * BOARD_HEIGHT)

        self._score: int = 123000

        self._piece_queue: deque[int] = deque()
        self._extend_piece_queue()

        self._falling_piece = self._piece_queue.popleft()
        self._falling_piece_rot: int
        self._falling_piece_bb_x: int
        self._falling_piece_bb_y: int
        self._place_new_piece()
    
    def get_state(self) -> TetrisGameState:
        if len(self._piece_queue) == 0:
            self._extend_piece_queue()

        return TetrisGameState(
            board_data=list(self._board),
            score=self._score,
            next_piece=self._piece_queue[0],
            falling_piece_cells=self.falling_piece_cells(),
            falling_piece=self._falling_piece,
            falling_piece_rot=self._falling_piece_rot,
            falling_piece_bb_x=self._falling_piece_bb_x,
            falling_piece_bb_y=self._falling_piece_bb_y,
        )
    
    def falling_piece_cells(self) -> list[tuple[int, int]]:
        """
        Returns the cell positions of all the blocks in the falling piece
        """
        a = [(x + self._falling_piece_bb_x, y + self._falling_piece_bb_y) for x, y in PIECE_DATA[self._falling_piece][self._falling_piece_rot]]
        return a

    def tick_gravity(self):
        self._piece_bb_y -= 1

    def shift_left(self):
        """
        Attempts to move the falling piece to the left
        """
        for x, _ in self.falling_piece_cells():
            # checking if any pieces would be out of bounds
            if x <= 0:
                return
        self._falling_piece_bb_x -= 1

    def shift_right(self):
        """
        Attempts to move the falling piece to the right
        """
        for x, _ in self.falling_piece_cells():
            # checking if any pieces would be out of bounds
            if x >= BOARD_WIDTH - 1:
                return
        self._falling_piece_bb_x += 1
    
    def rotate_cw(self):
        """
        Attempts to rotate the falling piece clockwise
        """
        # TODO SRS
        self._falling_piece_rot = (self._falling_piece_rot + 1) % 4

    def rotate_ccw(self):
        """
        Attempts to rotate the falling piece counter-clockwise
        """
        # TODO SRS
        self._falling_piece_rot = (self._falling_piece_rot - 1) % 4
    
    def soft_drop(self):
        self._falling_piece_bb_y += 1

    def hard_drop(self):
        self._falling_piece_bb_y += 2
    
    def current_piece(self) -> int:
        return self._current_piece

    def _place_new_piece(self):
        """
        """
        self._falling_piece_rot = 0
        self._falling_piece_bb_x = 3
        self._falling_piece_bb_y = 19
    
    def _extend_piece_queue(self):
        bag = list(_FULL_SEVEN_BAG)
        while len(bag) > 0:
            choice_index = random.randint(0, len(bag) - 1)
            choice = bag[choice_index]
            bag.pop(choice_index)
            self._piece_queue.append(choice)
         

