import os
import sys
import time

from tetris_game import TetrisGame, TetrisGameState

from tetris_cli_player.input.keyboard import start_keyboard_input_daemon, Key
from tetris_cli_player.render import visualize_state

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
        game = TetrisGame(update_callback=on_update)
        # game._falling_piece_bb_y = 10

        start_keyboard_input_daemon(callback=handle_key)

        game.start()

        time.sleep(1)
        game.join()

    except KeyboardInterrupt:
        pass


def on_update(state: TetrisGameState):
    """
    Called by the game thread once per frame
    """
    visualize_state(state)


def handle_key(key: Key, pressed: bool):
    """
    Called by the keyboard listener on a key event
    """
    global game

    if game is None:
        if key == Key.Q:
            sys.exit(0)
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

    if pressed:
        match key:
            case Key.UP:
                game.rotate_cw()
            case Key.L_CTRL | Key.Z:
                game.rotate_ccw()
            case Key.SPACE:
                # TODO hard drop
                pass
            case Key.L_SHIFT | Key.R_SHIFT | Key.C:
                game.hold()


if __name__ == "__main__":
    main()
