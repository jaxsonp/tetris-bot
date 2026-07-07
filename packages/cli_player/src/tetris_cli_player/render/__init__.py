import sys

from tetris_game import TetrisGameState, Piece, BOARD_WIDTH, BOARD_DISPLAY_HEIGHT

from . import color

_last_shown_state = None

HELP_TEXT = [
    "Controls:",
    "  L/R arrow - Shift left/right",
    "   Up arrow - Rotate cw",
    " Down arrow - Soft drop",
    "  Space bar - Hard drop",
    "  Shift / C - Hold piece",
    " L-ctrl / Z - Rotate ccw",
    "          Q - Quit game",
    "",
]

PIECE_BG_COLOR_MAP: dict[int, str] = {
    Piece.NULL: color.BG_RESET,
    Piece.I: color.BG_CYAN,
    Piece.L: color.BG_ORANGE,
    Piece.J: color.BG_BLUE,
    Piece.S: color.BG_GREEN,
    Piece.Z: color.BG_RED,
    Piece.T: color.BG_MAGENTA,
    Piece.O: color.BG_YELLOW,
}

PIECE_FG_COLOR_MAP: dict[int, str] = {
    Piece.NULL: color.FG_RESET,
    Piece.I: color.FG_CYAN,
    Piece.L: color.FG_ORANGE,
    Piece.J: color.FG_BLUE,
    Piece.S: color.FG_GREEN,
    Piece.Z: color.FG_RED,
    Piece.T: color.FG_MAGENTA,
    Piece.O: color.FG_YELLOW,
}

PIECE_CHAR_MAP: dict[int, str] = {
    Piece.NULL: " ",
    Piece.I: "I",
    Piece.L: "L",
    Piece.J: "J",
    Piece.S: "S",
    Piece.Z: "Z",
    Piece.T: "T",
    Piece.O: "O",
}

def visualize_state(state: TetrisGameState):
    global _last_shown_state

    if _last_shown_state is None:
        # never been displayed yet

        # draw game frame
        sys.stdout.write(f"\n{color.FG_RESET}{color.BG_RESET} ╷{" " * (BOARD_WIDTH * 2)}╷\n")
        for y in range(BOARD_DISPLAY_HEIGHT):
            sys.stdout.write(f" │{" " * (BOARD_WIDTH * 2)}│\n")
        sys.stdout.write(f" ├{"─" * (BOARD_WIDTH * 2)}┤\n")
        sys.stdout.write(f" │ Next: {PIECE_FG_COLOR_MAP[state.next_piece]}{PIECE_CHAR_MAP[state.next_piece]}{color.FG_RESET} {" " * ((BOARD_WIDTH * 2) - 10)} │\n")
        sys.stdout.write(f" │ Score: {state.score:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" ╰{"─" * (BOARD_WIDTH * 2)}╯{color.RESET}\n")

        # help text
        sys.stdout.write(f"\x1b[{len(HELP_TEXT)}A")
        for help_text_line in HELP_TEXT:
            sys.stdout.write(f"\x1b[{(BOARD_WIDTH * 2) + 4}C{help_text_line}\n")

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
            sys.stdout.write(f"{PIECE_BG_COLOR_MAP[value]}  {color.BG_RESET}")
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