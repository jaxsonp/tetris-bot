import sys
import time

import tetris_game
from tetris_game import TetrisGame, TetrisGameState, BOARD_WIDTH, BOARD_HEIGHT, BOARD_DISPLAY_HEIGHT

from .input.keyboard import start_keyboard_input_daemon, stop_keyboard_input_daemon

COLOR_RESET = "\x1b[0m"

COLOR_FG_RESET = "\x1b[39m"
COLOR_FG_BLACK = "\x1b[30m"
COLOR_FG_GRAY = "\x1b[38;5;7m"
COLOR_FG_WHITE = "\x1b[38;5;15m"
COLOR_FG_RED = "\x1b[38;5;9m"
COLOR_FG_GREEN = "\x1b[38;5;10m"
COLOR_FG_YELLOW = "\x1b[38;5;226m"
COLOR_FG_BLUE = "\x1b[38;5;12m"
COLOR_FG_MAGENTA = "\x1b[38;5;13m"
COLOR_FG_CYAN = "\x1b[38;5;51m"
COLOR_FG_ORANGE = "\x1b[38;5;208m"

COLOR_BG_RESET = "\x1b[49m"
COLOR_BG_BLACK = "\x1b[40m"
COLOR_BG_GRAY = "\x1b[48;5;7m"
COLOR_BG_WHITE = "\x1b[48;5;15m"
COLOR_BG_RED = "\x1b[38;5;9m"
COLOR_BG_GREEN = "\x1b[48;5;10m"
COLOR_BG_YELLOW = "\x1b[48;5;226m"
COLOR_BG_BLUE = "\x1b[48;5;12m"
COLOR_BG_MAGENTA = "\x1b[48;5;13m"
COLOR_BG_CYAN = "\x1b[48;5;51m"
COLOR_BG_ORANGE = "\x1b[48;5;208m"

PIECE_BG_COLOR_MAP: dict[int, str] = {
    tetris_game.PIECE_NULL: COLOR_BG_RESET,
    tetris_game.PIECE_I: COLOR_BG_CYAN,
    tetris_game.PIECE_L: COLOR_BG_ORANGE,
    tetris_game.PIECE_J: COLOR_BG_BLUE,
    tetris_game.PIECE_S: COLOR_BG_GREEN,
    tetris_game.PIECE_Z: COLOR_BG_RED,
    tetris_game.PIECE_T: COLOR_BG_MAGENTA,
    tetris_game.PIECE_O: COLOR_BG_YELLOW,
}

PIECE_FG_COLOR_MAP: dict[int, str] = {
    tetris_game.PIECE_NULL: COLOR_FG_RESET,
    tetris_game.PIECE_I: COLOR_FG_CYAN,
    tetris_game.PIECE_L: COLOR_FG_ORANGE,
    tetris_game.PIECE_J: COLOR_FG_BLUE,
    tetris_game.PIECE_S: COLOR_FG_GREEN,
    tetris_game.PIECE_Z: COLOR_FG_RED,
    tetris_game.PIECE_T: COLOR_FG_MAGENTA,
    tetris_game.PIECE_O: COLOR_FG_YELLOW,
}

PIECE_CHAR_MAP: dict[int, str] = {
    tetris_game.PIECE_NULL: " ",
    tetris_game.PIECE_I: "I",
    tetris_game.PIECE_L: "L",
    tetris_game.PIECE_J: "J",
    tetris_game.PIECE_S: "S",
    tetris_game.PIECE_Z: "Z",
    tetris_game.PIECE_T: "T",
    tetris_game.PIECE_O: "O",
}

_last_shown_state = None


def visualize_state(state: TetrisGameState):
    global _last_shown_state

    if _last_shown_state is None:
        # never been displayed yet

        # draw game frame (outline)
        sys.stdout.write(f"{COLOR_FG_RESET}{COLOR_BG_RESET} ╷{" " * (BOARD_WIDTH * 2)}╷\n")
        for y in range(BOARD_DISPLAY_HEIGHT):
            sys.stdout.write(f" │{" " * (BOARD_WIDTH * 2)}│\n")
        sys.stdout.write(f" ├{"─" * (BOARD_WIDTH * 2)}┤\n")
        sys.stdout.write(f" │ Next: {PIECE_FG_COLOR_MAP[state.next_piece]}{PIECE_CHAR_MAP[state.next_piece]}{COLOR_FG_RESET} {" " * ((BOARD_WIDTH * 2) - 10)} │\n")
        sys.stdout.write(f" │ Score: {state.score:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" ╰{"─" * (BOARD_WIDTH * 2)}╯{COLOR_RESET}\n")

        _last_shown_state = state.copy()
    
    # show falling piece
    for block_x, block_y in state.falling_piece_cells:
        state.set_board(block_x, block_y, state.falling_piece)
    
    # calculate diffs
    row_diffs: list[None | list[tuple[int, int]]] = [None] * BOARD_DISPLAY_HEIGHT
    for y in range(BOARD_DISPLAY_HEIGHT):
        for x in range(BOARD_WIDTH):
            # check for differences
            if state.get_board(x, y) != _last_shown_state.get_board(x, y):
                if row_diffs[y] is None:
                    row_diffs[y] = []
                row_diffs[y].append((x, state.get_board(x, y)))
    
    # draw changed cells
    cursor_y = 0
    cursor_x = 0
    for line, col_diffs in enumerate(row_diffs):
        # skip lines w no changes
        if col_diffs is None:
            continue
        # move up to the correct line
        target_cursor_y = 5 + line
        sys.stdout.write(f"\x1b[{target_cursor_y - cursor_y}A")
        cursor_y = target_cursor_y

        for col, value in col_diffs:
            # move to column and write block
            target_cursor_x = 2 + (col * 2)
            if target_cursor_x > cursor_x:
                sys.stdout.write(f"\x1b[{target_cursor_x - cursor_x}C")
            elif target_cursor_x < cursor_x:
                sys.stdout.write(f"\x1b[{cursor_x - target_cursor_x}D")
            sys.stdout.write(f"{PIECE_BG_COLOR_MAP[value]}  {COLOR_BG_RESET}")
            cursor_x = target_cursor_x + 2
    
    if state.next_piece != _last_shown_state.next_piece:
        pass
    
    # reset cursor
    if cursor_y > 0:
        sys.stdout.write(f"\x1b[{cursor_y}B")
    elif cursor_y < 0:
        sys.stdout.write(f"\x1b[{cursor_y}A")
    if cursor_x != 0:
        sys.stdout.write("\r")
    sys.stdout.flush()

    # remember state
    _last_shown_state = state.copy()

def handle_key(game: TetrisGame, key: bytes):
    if key == b'LEFT':
        game.shift_left()
    elif key == b'RIGHT':
        game.shift_right()
    elif key == b'UP':
        game.rotate_cw()
    elif key == b'Z':
        game.rotate_ccw()

def main():
    try:
        game = TetrisGame()
        game._falling_piece_bb_y = 10

        q = start_keyboard_input_daemon()

        while True:
            while not q.empty():
                handle_key(game, q.get())

            time.sleep(1.0 / 30.0)
            #game._piece_rot = (game._piece_rot + 1) % 4
            state = game.get_state()
            visualize_state(state)
    except KeyboardInterrupt:
        stop_keyboard_input_daemon()


if __name__ == "__main__":
    main()
