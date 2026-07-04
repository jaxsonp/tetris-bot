import random
from collections import deque

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

class TetrisGameBoard:
    def __init__(self, data: list[int] | None = None):
        if data is not None and len(data) != BOARD_WIDTH * BOARD_HEIGHT:
            raise ValueError(f"GameBoard data must be an array of length {BOARD_WIDTH * BOARD_HEIGHT}, got {len(data)}")
        self._data = [PIECE_NULL] * (BOARD_WIDTH * BOARD_HEIGHT) if data is None else list(data)
    
    def get(self, x: int, y: int) -> int:
        """
        Gets the value of a specific position on the board
        """
        return self._data[y * BOARD_WIDTH + x]

    def set(self, x: int, y: int, value: int) -> int:
        """
        Sets the value at a specific position on the board, returning the old value
        """
        old = self._data[y * BOARD_WIDTH + x]
        self._data[y * BOARD_WIDTH + x] = value
        return old

    def copy(self) -> 'TetrisGameBoard':
        return TetrisGameBoard(data=self._data)

class TetrisGame:
    def __init__(self):

        # init board
        self.board = TetrisGameBoard()

        self._piece_queue: deque[int] = deque()
        self._extend_piece_queue()

        self._current_piece = self._piece_queue.popleft()
        self._piece_rot: int
        self._piece_bb_x: int
        self._piece_bb_y: int
        self._place_new_piece()
    
    def falling_piece_cells(self) -> list[tuple[int, int]]:
        """
        Returns the cell positions of all the blocks in the falling piece
        """
        a = [(x + self._piece_bb_x, y + self._piece_bb_y) for x, y in PIECE_DATA[self._current_piece][self._piece_rot]]
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
        self._piece_bb_x -= 1

    def shift_right(self):
        """
        Attempts to move the falling piece to the right
        """
        for x, _ in self.falling_piece_cells():
            # checking if any pieces would be out of bounds
            if x >= BOARD_WIDTH - 1:
                return
        self._piece_bb_x += 1
    
    def rotate_cw(self):
        """
        Attempts to rotate the falling piece clockwise
        """
        # TODO SRS
        self._piece_rot = (self._piece_rot + 1) % 4

    def rotate_ccw(self):
        """
        Attempts to rotate the falling piece counter-clockwise
        """
        # TODO SRS
        self._piece_rot = (self._piece_rot - 1) % 4
    
    def current_piece(self) -> int:
        return self._current_piece

    def _place_new_piece(self):
        """
        """
        self._piece_rot: int = 0
        self._piece_bb_x = 3
        self._piece_bb_y = 22
    
    def _extend_piece_queue(self):
        bag = list(_FULL_SEVEN_BAG)
        while len(bag) > 0:
            choice_index = random.randint(0, len(bag) - 1)
            choice = bag[choice_index]
            bag.pop(choice_index)
            self._piece_queue.append(choice)
         

