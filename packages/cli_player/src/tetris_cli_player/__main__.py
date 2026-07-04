import sys
import io
import time
import os
if os.name == 'posix':
    import tty
    import termios
elif os.name == 'nt':
    sys.exit(1)

import tetris_game
from tetris_game import TetrisGame, TetrisGameBoard, BOARD_WIDTH, BOARD_HEIGHT, BOARD_DISPLAY_HEIGHT

from .input.keyboard import start_keyboard_input_daemon, stop_keyboard_input_daemon

COLOR_RESET = "\x1b[0m"
COLOR_BG_BLACK = "\x1b[40m"
COLOR_BG_RED = "\x1b[41m"
COLOR_BG_GREEN = "\x1b[42m"
COLOR_BG_YELLOW = "\x1b[43m"
COLOR_BG_BLUE = "\x1b[44m"
COLOR_BG_MAGENTA = "\x1b[45m"
COLOR_BG_CYAN = "\x1b[46m"
COLOR_BG_WHITE = "\x1b[47m"
COLOR_BG_ORANGE = "\x1b[48;5;208m"

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


def visualize_game(game: TetrisGame):
    global _last_shown_board

    if _last_shown_board is None:
        # never been displayed yet
        _last_shown_board = TetrisGameBoard()

        # draw game frame (outline)
        sys.stdout.write(COLOR_BG_WHITE)
        sys.stdout.write("  " * (BOARD_WIDTH + 2))
        sys.stdout.write(COLOR_RESET)
        sys.stdout.write("\n")
        for y in reversed(range(BOARD_DISPLAY_HEIGHT)):
            sys.stdout.write(f"{COLOR_BG_WHITE}  {COLOR_BG_BLACK}")
            cur_col = COLOR_BG_BLACK
            for x in range(BOARD_WIDTH):
                target_col = CELL_COLOR_MAP[game.board.get(x, y)]
                if cur_col != target_col:
                    sys.stdout.write(target_col)
                    cur_col = target_col
                sys.stdout.write("  ")
            sys.stdout.write(f"{COLOR_BG_WHITE}  {COLOR_RESET}\n")
        sys.stdout.write(COLOR_BG_WHITE)
        sys.stdout.write("  " * (BOARD_WIDTH + 2))
        sys.stdout.write(COLOR_RESET)
        sys.stdout.write("\n")
    
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
        sys.stdout.write(f"\x1b[{line - cursor_y}A")
        cursor_y = line

        for col, value in col_diffs:
            # move to column and write block
            if col > cursor_x:
                sys.stdout.write(f"\x1b[{(col - cursor_x) * 2}C")
            elif col < cursor_x:
                sys.stdout.write(f"\x1b[{(cursor_x - col) * 2}D")
            sys.stdout.write(f"{CELL_COLOR_MAP[value]}  {COLOR_RESET}")
            cursor_x = col + 1
    
    # reset cursor
    if cursor_y != -2:
        sys.stdout.write(f"\x1b[{cursor_y + 2}B")
    if cursor_x != -1:
        sys.stdout.write("\r")

    sys.stdout.flush()

    if different:
        # remember state
        _last_shown_board = cur_board.copy()

def handle_key(game: TetrisGame, key: bytes):
    if key == b'LEFT':
        game.shift_left()
    elif key == b'RIGHT':
        game.shift_right()
    elif key == b'UP':
        game.rotate_cw()
    elif key == b'DOWN':
        game.rotate_ccw()

def main():
    try:
        game = TetrisGame()
        game._piece_bb_y = 10

        q = start_keyboard_input_daemon()

        while True:
            while not q.empty():
                handle_key(game, q.get())

            time.sleep(1.0 / 30.0)
            #game._piece_rot = (game._piece_rot + 1) % 4
            visualize_game(game)
    except KeyboardInterrupt:
        stop_keyboard_input_daemon()


if __name__ == "__main__":
    main()
