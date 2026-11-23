import os
import sys
import time
from typing import Callable, LiteralString

from tetris_game import TetrisGame, TetrisGameState

from tetris_cli_player.input import keyboard
from tetris_cli_player import render

USAGE_TEXT: list[LiteralString] = [
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


def main():
    global USAGE_TEXT

    # require sudo on linux, for reading the keyboard
    if os.name == "posix" and os.geteuid() != 0:
        # re-execute with sudo for keyboard input reading on linux
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    try:
        game = TetrisGame(state_change_callback=on_state_change)

        keyboard.start_keyboard_input_daemon(callback=key_handler_factory(game))

        # inital render
        render.visualize_state(game.get_state(), message="ENTER to start", details_text=USAGE_TEXT)

        time.sleep(1)
        game.join()

    except KeyboardInterrupt:
        pass
    finally:
        render.cleanup()


def on_state_change(state: TetrisGameState):
    """
    Called by the game thread when the state changes
    """
    render.visualize_state(state)


def key_handler_factory(game: TetrisGame) -> Callable:
    def handle_key(key: keyboard.Key, pressed: bool):
        """
        Called by the keyboard listener on a key event
        """
        if game is None:
            if key == keyboard.Key.Q:
                sys.exit(0)
            else:
                return

        match key:
            case keyboard.Key.Q:
                game.quit()
            case keyboard.Key.LEFT:
                game.shift_left(hold=pressed)
            case keyboard.Key.RIGHT:
                game.shift_right(hold=pressed)
            case keyboard.Key.DOWN:
                game.soft_drop(hold=pressed)
            case keyboard.Key.ENTER:
                game.start()

        if pressed:
            match key:
                case keyboard.Key.UP:
                    game.rotate_cw()
                case keyboard.Key.L_CTRL | keyboard.Key.Z:
                    game.rotate_ccw()
                case keyboard.Key.SPACE:
                    game.hard_drop()
                case keyboard.Key.L_SHIFT | keyboard.Key.R_SHIFT | keyboard.Key.C:
                    game.hold()
                case keyboard.Key.ESCAPE:
                    game.toggle_pause()
    return handle_key


if __name__ == "__main__":
    main()
