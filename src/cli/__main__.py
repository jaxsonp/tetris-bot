import sys
import io
import time

import tetris_game
from tetris_game import TetrisGame, TetrisGameBoard, BOARD_WIDTH, BOARD_HEIGHT, BOARD_DISPLAY_HEIGHT

COLOR_RESET = b"\x1b[0m"
COLOR_BG_BLACK = b"\x1b[40m"
COLOR_BG_RED = b"\x1b[41m"
COLOR_BG_GREEN = b"\x1b[42m"
COLOR_BG_YELLOW = b"\x1b[43m"
COLOR_BG_BLUE = b"\x1b[44m"
COLOR_BG_MAGENTA = b"\x1b[45m"
COLOR_BG_CYAN = b"\x1b[46m"
COLOR_BG_WHITE = b"\x1b[47m"
COLOR_BG_ORANGE = b"\x1b[48;5;208m"

CELL_COLOR_MAP = {
    tetris_game.PIECE_NULL: COLOR_RESET,
    tetris_game.PIECE_I: COLOR_BG_CYAN,
    tetris_game.PIECE_L: COLOR_BG_ORANGE,
    tetris_game.PIECE_J: COLOR_BG_BLUE,
    tetris_game.PIECE_S: COLOR_BG_GREEN,
    tetris_game.PIECE_Z: COLOR_BG_RED,
    tetris_game.PIECE_T: COLOR_BG_MAGENTA,
    tetris_game.PIECE_O: COLOR_BG_YELLOW,
}

_last_shown_board = None

term_out = io.BufferedWriter(sys.stdout.buffer)

def visualize_game(game: TetrisGame):
    global _last_shown_board

    if _last_shown_board is None:
        # never been displayed yet
        _last_shown_board = TetrisGameBoard()

        # draw game frame (outline)
        term_out.write(COLOR_BG_WHITE)
        term_out.write(b"  " * (BOARD_WIDTH + 2))
        term_out.write(COLOR_RESET)
        term_out.write(b"\n")
        for y in reversed(range(BOARD_DISPLAY_HEIGHT)):
            term_out.write(COLOR_BG_WHITE + b"  " + COLOR_BG_BLACK)
            cur_col = COLOR_BG_BLACK
            for x in range(BOARD_WIDTH):
                target_col = CELL_COLOR_MAP[game.board.get(x, y)]
                if cur_col != target_col:
                    term_out.write(target_col)
                    cur_col = target_col
                term_out.write(b"  ")
            term_out.write(COLOR_BG_WHITE + b"  " + COLOR_RESET + b"\n")
        term_out.write(COLOR_BG_WHITE)
        term_out.write(b"  " * (BOARD_WIDTH + 2))
        term_out.write(COLOR_RESET + b"\n")
    
    cur_board = game.board.copy()
    
    # show falling piece    
    for block_x, block_y in game.falling_piece_cells():
        cur_board.set(block_x, block_y, game.current_piece())
    
    # calculate diffs
    different = False
    row_diffs: list[None | list[tuple[int, int]]] = [None] * BOARD_DISPLAY_HEIGHT
    for y in range(BOARD_DISPLAY_HEIGHT):
        for x in range(BOARD_WIDTH):
            # check for differences
            if cur_board.get(x, y) != _last_shown_board.get(x, y):
                different = True
                if row_diffs[y] is None:
                    row_diffs[y] = []
                row_diffs[y].append((x, cur_board.get(x, y)))
    
    # draw changed cells
    cursor_y = -2
    cursor_x = -1
    for line, col_diffs in enumerate(row_diffs):
        # skip lines w no changes
        if col_diffs is None:
            continue
        # move up to the correct line
        term_out.write(b"\x1b[" + str(line - cursor_y).encode() + b"A")
        cursor_y = line

        for col, value in col_diffs:
            # move to column and write block
            if col > cursor_x:
                term_out.write(b"\x1b[" + str((col - cursor_x) * 2).encode() + b"C")
            elif col < cursor_x:
                term_out.write(b"\x1b[" + str((cursor_x - col) * 2).encode() + b"D")
            term_out.write(CELL_COLOR_MAP[value] + b"  " + COLOR_RESET)
            cursor_x = col + 1
    
    # reset cursor
    if cursor_y != -2:
        term_out.write(b"\x1b[" + str(cursor_y + 2).encode() + b"B")
    if cursor_x != -1:
        term_out.write(b"\r")

    term_out.flush()

    if different:
        # remember state
        print(row_diffs, end="\r")
        _last_shown_board = cur_board.copy()



def main():
    game = TetrisGame()
    game._piece_bb_y = 10
    while True:
        time.sleep(1)
        game._piece_rot = (game._piece_rot + 1) % 4
        visualize_game(game)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
