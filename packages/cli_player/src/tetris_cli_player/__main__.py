import os
import sys
import time

from tetris_game import TetrisGame, TetrisGameState

from tetris_cli_player.input.keyboard import start_keyboard_input_daemon, Key
from tetris_cli_player import render

game: TetrisGame | None = None
stopped = False

# game frame count
frame = 0


def main():
    global game, frame

    if os.name == "posix" and os.geteuid() != 0:
        # re-execute with sudo for keyboard input reading on linux
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    
    try:
        game = TetrisGame(state_change_callback=on_state_change)

        start_keyboard_input_daemon(callback=handle_key)

        # inital render
        render.visualize_state(game.get_state(), message="ENTER to start")

        time.sleep(1)
        game.join()
        game = None

    except KeyboardInterrupt:
        pass
    finally:
        render.cleanup()


def on_state_change(state: TetrisGameState):
    """
    Called by the game thread when the state changes
    """
    render.visualize_state(state)


def handle_key(key: Key, pressed: bool):
    """
    Called by the keyboard listener on a key event
    """
    global game

    if game is None:
        if key == Key.Q:
            sys.exit(0)
        else:
            return

    match key:
        case Key.Q:
            game.quit()
        case Key.LEFT:
            game.shift_left(hold=pressed)
        case Key.RIGHT:
            game.shift_right(hold=pressed)
        case Key.DOWN:
            game.soft_drop(hold=pressed)
        case Key.ENTER:
            game.start()

    if pressed:
        match key:
            case Key.UP:
                game.rotate_cw()
            case Key.L_CTRL | Key.Z:
                game.rotate_ccw()
            case Key.SPACE:
                game.hard_drop()
            case Key.L_SHIFT | Key.R_SHIFT | Key.C:
                game.hold()
            case Key.ESCAPE:
                game.toggle_pause()


if __name__ == "__main__":
    main()
