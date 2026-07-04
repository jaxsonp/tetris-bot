import random
from collections import deque

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

# For each piece, for each rotation, what cells are part of the piece (form (x,y) relative
# to BOTTOM-RIGHT of the bounding box)
PIECE_DATA = (
    # null piece
    (),
    # I piece
    (
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    # L piece
    (
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 2), (1, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 2), (1, 2), (1, 1), (1, 0)),
    ),
    # J piece
    (
        ((0, 2), (0, 1), (1, 1), (2, 1)),
        ((2, 2), (1, 2), (1, 1), (1, 0)),
        ((0, 1), (1, 1), (2, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    # S piece
    (
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 2), (1, 1), (2, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((0, 2), (0, 1), (1, 1), (1, 0)),
    ),
    # Z piece
    (
        ((0, 2), (1, 2), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 1), (1, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    # T piece
    (
        ((1, 1), (0, 1), (1, 2), (2, 1)),
        ((1, 1), (1, 2), (2, 1), (1, 0)),
        ((1, 1), (2, 1), (1, 0), (0, 1)),
        ((1, 1), (1, 0), (0, 1), (1, 2)),
    ),
)

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
        self._piece_rot: int = 0
        self._piece_bb_x: int = 4
        self._piece_bb_y: int = 22
        self._place_new_piece()
    
    def falling_piece_cells(self) -> list[tuple[int, int]]:
        """
        Returns the cell positions of all the blocks in the falling piece
        """
        a = [(x + self._piece_bb_x, y + self._piece_bb_y) for x, y in PIECE_DATA[self._current_piece][self._piece_rot]]
        return a

    def tick(self):
        self._piece_bb_y -= 1
    
    def current_piece(self) -> int:
        return self._current_piece

    def _place_new_piece(self):
        """
        """
        self._piece_rot: int = 0
        self._piece_bb_x = 4
        self._piece_bb_y = 22
    
    def _extend_piece_queue(self):
        bag = list(_FULL_SEVEN_BAG)
        while len(bag) > 0:
            choice_index = random.randint(0, len(bag) - 1)
            choice = bag[choice_index]
            bag.pop(choice_index)
            self._piece_queue.append(choice)
         

