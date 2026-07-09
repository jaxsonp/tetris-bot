import sys
from typing import LiteralString

from tetris_game import TetrisGame, TetrisGameState, Piece, GameStatus

from . import style

HELP_TEXT: list[LiteralString] = [
    "Controls:",
    "  L/R arrow - Shift left/right",
    "   Up arrow - Rotate cw",
    " Down arrow - Soft drop",
    "  Space bar - Hard drop",
    "  Shift / C - Hold piece",
    " L-ctrl / Z - Rotate ccw",
    "        Esc - Pause/resume",
    "          Q - Quit game",
    "",
]

PIECE_BG_COLOR_MAP: list[LiteralString] = [
    style.BG_COL_RESET,     # NULL
    style.BG_COL_CYAN,      # I
    style.BG_COL_ORANGE,    # L
    style.BG_COL_BLUE,      # J
    style.BG_COL_GREEN,     # S
    style.BG_COL_RED,       # Z
    style.BG_COL_MAGENTA,   # T
    style.BG_COL_YELLOW,    # O
]

PIECE_FG_COLOR_MAP: list[LiteralString] = [
    style.FG_COL_RESET,     # NULL
    style.FG_COL_CYAN,      # I
    style.FG_COL_ORANGE,    # L
    style.FG_COL_BLUE,      # J
    style.FG_COL_GREEN,     # S
    style.FG_COL_RED,       # Z
    style.FG_COL_MAGENTA,   # T
    style.FG_COL_YELLOW,    # O
]

PIECE_CHAR_MAP: list[LiteralString] = [
    " ", # NULL
    "I", # I
    "L", # L
    "J", # J
    "S", # S
    "Z", # Z
    "T", # T
    "O", # O
]

BOARD_WIDTH = TetrisGame.BOARD_WIDTH
BOARD_DISPLAY_HEIGHT = 21

MESSAGE_BANNER_TOP_ROW = int(BOARD_DISPLAY_HEIGHT / 2) + 7
MESSAGE_BANNER_TEXT_ROW = int(BOARD_DISPLAY_HEIGHT / 2) + 6
MESSAGE_BANNER_BOTTOM_ROW = int(BOARD_DISPLAY_HEIGHT / 2) + 5

_last_shown_state = None
_last_shown_message = None

_cursor_x = 0
_cursor_y = 0

def move_cursor(x, y):
    """
    Prints the escape sequences to move the cursor to a location relative to
    (0, 0), the bottom right of the game screen
    """
    global _cursor_x, _cursor_y
    if x > _cursor_x:
        sys.stdout.write(f"\x1b[{int(x - _cursor_x)}C")
        _cursor_x = x
    elif x < _cursor_x:
        sys.stdout.write(f"\x1b[{int(_cursor_x - x)}D")
        _cursor_x = x

    if y < _cursor_y:
        sys.stdout.write(f"\x1b[{int(_cursor_y - y)}B")
        _cursor_y = y
    elif y > _cursor_y:
        sys.stdout.write(f"\x1b[{int(y - _cursor_y)}A")
        _cursor_y = y

def visualize_state(state: TetrisGameState, message: str | None = None):
    """
    Draw a game state

    Expects the cursor to be left at column 0 row 0 (with an exception for the
    first invocation)
    """
    global _last_shown_state, _last_shown_message, _cursor_y, _cursor_x

    if _last_shown_state is None:
        # never been displayed yet

        # draw game frame
        sys.stdout.write(f"\n{style.FG_COL_RESET}{style.BG_COL_RESET} ╻{" " * (BOARD_WIDTH * 2)}╻\n")
        for y in range(BOARD_DISPLAY_HEIGHT):
            sys.stdout.write(" ┃" + (" " * (BOARD_WIDTH * 2)))
            match y:
                case 0:
                    sys.stdout.write("┠Hold\n")
                case 1:
                    sys.stdout.write( "┃   │\n")
                case 2:
                    sys.stdout.write("┠───╯\n")
                case 3:
                    sys.stdout.write("┠Next\n")
                case 4:
                    sys.stdout.write("┃   │\n")
                case 5:
                    sys.stdout.write("┠───╯\n")
                case _:
                    sys.stdout.write("┃\n")
        sys.stdout.write(f" ┡{"━" * (BOARD_WIDTH * 2)}┩\n")
        sys.stdout.write(f" │ Score: {state.score:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" │ Level: {state.level:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" │ Lines: {state.lines_cleared:>{(BOARD_WIDTH * 2) - 9}} │\n")
        sys.stdout.write(f" ╰{"─" * (BOARD_WIDTH * 2)}╯{style.RESET}\n")

        # help text
        sys.stdout.write(f"\x1b[{len(HELP_TEXT)}A")
        for help_text_line in HELP_TEXT:
            sys.stdout.write(f"\x1b[{(BOARD_WIDTH * 2) + 4}C{help_text_line}\n")

        _last_shown_state = state.copy()
        _last_shown_state.held_piece = Piece.NULL
        _last_shown_state.next_piece = Piece.NULL
        _cursor_x = 0
        _cursor_y = 0
    
    # show falling piece
    for block_x, block_y in state.falling_piece_cells():
        state.set_board(block_x, block_y, state.falling_piece)
    
    # calculate diffs from bottom to top (list of (x, y, value))
    changes: list[tuple[int, int, int]] = []
    for y in range(BOARD_DISPLAY_HEIGHT + 1):
        # get changes in side to side manner for optimization maybe?
        for x in (range(BOARD_WIDTH) if y % 2 == 0 else reversed(range(BOARD_WIDTH))):
            # check for differences
            if state.get_board(x, y) != _last_shown_state.get_board(x, y):
                changes.append((x, y, state.get_board(x, y)))
    
    # redraw changed cells
    for col, row, value in changes:
        move_cursor(2 + (col * 2), 6 + row)
        sys.stdout.write(f"{PIECE_BG_COLOR_MAP[value]}  {style.BG_COL_RESET}")
        _cursor_x += 2

    # redraw changed held/next pieces
    if state.held_piece != _last_shown_state.held_piece:
        move_cursor((BOARD_WIDTH * 2) + 4, BOARD_DISPLAY_HEIGHT + 4)
        sys.stdout.write(style.WT_BOLD + PIECE_FG_COLOR_MAP[state.held_piece] + PIECE_CHAR_MAP[state.held_piece] + style.RESET)
        _cursor_x += 1
    if state.next_piece != _last_shown_state.next_piece:
        move_cursor((BOARD_WIDTH * 2) + 4, BOARD_DISPLAY_HEIGHT + 1)
        sys.stdout.write(style.WT_BOLD + PIECE_FG_COLOR_MAP[state.next_piece] + PIECE_CHAR_MAP[state.next_piece] + style.RESET)
        _cursor_x += 1

    # check if message needs to be displayed
    if message is not None:
        pass
    elif state.status == GameStatus.PAUSED:
        message = "Paused"
    elif state.status == GameStatus.GAME_OVER:
        message = "Game over"

    if _last_shown_message is None and message is not None:
        # show new message
        move_cursor(2, MESSAGE_BANNER_TOP_ROW)
        sys.stdout.write("─" * (BOARD_WIDTH * 2))
        _cursor_x += BOARD_WIDTH * 2
        move_cursor(2, MESSAGE_BANNER_TEXT_ROW)
        sys.stdout.write(message[:(BOARD_WIDTH * 2)].center(BOARD_WIDTH * 2))
        _cursor_x += BOARD_WIDTH * 2
        move_cursor(2, MESSAGE_BANNER_BOTTOM_ROW)
        sys.stdout.write("─" * (BOARD_WIDTH * 2))
        _cursor_x += BOARD_WIDTH * 2
    elif _last_shown_message is not None and message is not None:
        # overwite previous message
        move_cursor(2, int(BOARD_DISPLAY_HEIGHT / 2) + 6)
        sys.stdout.write(message[:(BOARD_WIDTH * 2)].center(BOARD_WIDTH * 2))
        _cursor_x += BOARD_WIDTH * 2
    elif _last_shown_message is not None:
        # clear message box (redraw all cells below)
        for y in [MESSAGE_BANNER_TOP_ROW, MESSAGE_BANNER_TEXT_ROW, MESSAGE_BANNER_BOTTOM_ROW]:
            row = y - 6
            for col in range(BOARD_WIDTH):
                move_cursor(2 + (col * 2), y)
                sys.stdout.write(f"{PIECE_BG_COLOR_MAP[state.get_board(col, row)]}  {style.BG_COL_RESET}")
                _cursor_x += 2
        pass
    _last_shown_message = message

    # redraw changed score values
    if state.score != _last_shown_state.score:
        move_cursor(10, 4)
        sys.stdout.write(str(state.score).rjust((BOARD_WIDTH * 2) - 9))
        _cursor_x += (BOARD_WIDTH * 2) - 9
    if state.level != _last_shown_state.level:
        move_cursor(10, 3)
        sys.stdout.write(str(state.level).rjust((BOARD_WIDTH * 2) - 9))
        _cursor_x += (BOARD_WIDTH * 2) - 9
    if state.lines_cleared != _last_shown_state.lines_cleared:
        move_cursor(10, 2)
        sys.stdout.write(str(state.lines_cleared).rjust((BOARD_WIDTH * 2) - 9))
        _cursor_x += (BOARD_WIDTH * 2) - 9
    
    
    # reset cursor
    move_cursor(0, 0)

    # render
    sys.stdout.flush()

    # remember state
    _last_shown_state = state.copy()


def cleanup():
    """
    To be called on exit to return cursor/text style to default states
    """
    sys.stdout.write(style.RESET)
    sys.stdout.flush()