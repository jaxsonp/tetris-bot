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

cursor_x = 0
cursor_y = 0

def move_cursor(x, y):
    """
    Prints the escape sequences to move the cursor to a location relative to
    (0, 0), the bottom right of the game screen
    """
    global cursor_x, cursor_y
    if x > cursor_x:
        sys.stdout.write(f"\x1b[{x - cursor_x}C")
        cursor_x = x
    elif x < cursor_x:
        sys.stdout.write(f"\x1b[{cursor_x - x}D")
        cursor_x = x

    if y < cursor_y:
        sys.stdout.write(f"\x1b[{cursor_y - y}B")
        cursor_y = y
    elif y > cursor_y:
        sys.stdout.write(f"\x1b[{y - cursor_y}A")
        cursor_y = y

def visualize_state(state: TetrisGameState):
    global _last_shown_state, cursor_y, cursor_x

    if _last_shown_state is None:
        # never been displayed yet

        # draw game frame
        sys.stdout.write(f"\n{color.FG_RESET}{color.BG_RESET} ╻{" " * (BOARD_WIDTH * 2)}╻\n")
        for y in range(BOARD_DISPLAY_HEIGHT):
            sys.stdout.write(" ┃" + (" " * (BOARD_WIDTH * 2)))
            match y:
                case 0:
                    sys.stdout.write("┠Hold╮\n")
                case 1:
                    sys.stdout.write(f"┃  {PIECE_FG_COLOR_MAP[state.held_piece]}{PIECE_CHAR_MAP[state.held_piece]}{color.FG_RESET} │\n")
                case 2:
                    sys.stdout.write("┠────╯\n")
                case 3:
                    sys.stdout.write("┠Next╮\n")
                case 4:
                    sys.stdout.write(f"┃  {PIECE_FG_COLOR_MAP[state.next_piece]}{PIECE_CHAR_MAP[state.next_piece]}{color.FG_RESET} │\n")
                case 5:
                    sys.stdout.write("┠────╯\n")
                case _:
                    sys.stdout.write("┃\n")
        sys.stdout.write(f" ┡{"━" * (BOARD_WIDTH * 2)}┩\n")
        sys.stdout.write(f" │ Score: {state.score:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" │ Level: {state.level:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" │ Lines: {100:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" ╰{"─" * (BOARD_WIDTH * 2)}╯{color.RESET}\n")

        # help text
        sys.stdout.write(f"\x1b[{len(HELP_TEXT)}A")
        for help_text_line in HELP_TEXT:
            sys.stdout.write(f"\x1b[{(BOARD_WIDTH * 2) + 4}C{help_text_line}\n")

        _last_shown_state = state.copy()
        cursor_x = 0
        cursor_y = 0
    
    # show falling piece
    for block_x, block_y in state.falling_piece_cells:
        state.set_board(block_x, block_y, state.falling_piece)
    
    # calculate diffs from bottom to top (list of (x, y, value))
    changes: list[tuple[int, int, int]] = []
    for y in range(BOARD_DISPLAY_HEIGHT):
        # get changes in side to side manner for optimization maybe?
        for x in (range(BOARD_WIDTH) if y % 2 == 0 else reversed(range(BOARD_WIDTH))):
            # check for differences
            if state.get_board(x, y) != _last_shown_state.get_board(x, y):
                changes.append((x, y, state.get_board(x, y)))
    
    # draw changed cells
    for col, row, value in changes:
        move_cursor(2 + (col * 2), 5 + row)
        sys.stdout.write(f"{PIECE_BG_COLOR_MAP[value]}  {color.BG_RESET}")
        cursor_x += 2

    # held / next piece
    if state.held_piece != _last_shown_state.held_piece:
        move_cursor((BOARD_WIDTH * 2) + 5, BOARD_DISPLAY_HEIGHT + 4)
        sys.stdout.write(f"{PIECE_FG_COLOR_MAP[state.held_piece]}{PIECE_CHAR_MAP[state.held_piece]}{color.FG_RESET}")
        cursor_x += 1
    if state.next_piece != _last_shown_state.next_piece:
        move_cursor((BOARD_WIDTH * 2) + 5, BOARD_DISPLAY_HEIGHT + 1)
        sys.stdout.write(f"{PIECE_FG_COLOR_MAP[state.next_piece]}{PIECE_CHAR_MAP[state.next_piece]}{color.FG_RESET}")
        cursor_x += 1
    
    
    # reset cursor
    move_cursor(0, 0)

    # render
    sys.stdout.flush()

    # remember state
    _last_shown_state = state.copy()