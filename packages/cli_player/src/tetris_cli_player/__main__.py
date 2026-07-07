import os
import sys
import time

from tetris_game import TetrisGame

from tetris_cli_player.input.keyboard import start_keyboard_input_daemon, Key
from tetris_cli_player.render import visualize_state

game: TetrisGame | None = None
stopped = False
show_help = True

def handle_key(key: Key, pressed: bool):
    """
    Callback called by the keyboard listener
    """
    global game, stopped

    if key == Key.H:
        show_help != show_help
        return
    elif key == Key.Q:
        stopped = True
        sys.exit(0)

    if game is not None:
        if pressed:
            match key:
                case Key.LEFT:
                    game.shift_left()
                case Key.RIGHT:
                    game.shift_right()
                case Key.UP:
                    game.rotate_cw()
                case Key.L_CTRL | Key.Z:
                    game.rotate_ccw()
                case Key.DOWN:
                    # TODO soft drop
                    pass
                case Key.SPACE:
                    # TODO hard drop
                    pass
                case Key.L_SHIFT | Key.R_SHIFT:
                    # TODO hold
                    pass

def main():
    global game

    if os.name == "posix" and os.geteuid() != 0:
        # re-execute with sudo for keyboard input reading on linux
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    try:
        game = TetrisGame()
        game._falling_piece_bb_y = 10

        start_keyboard_input_daemon(handle_key)

        while not stopped:

            time.sleep(1.0 / 30.0)
            #game._piece_rot = (game._piece_rot + 1) % 4
            state = game.get_state()
            visualize_state(state, show_help=show_help)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
