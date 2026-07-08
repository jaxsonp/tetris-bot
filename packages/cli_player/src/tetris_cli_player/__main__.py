import os
import sys
import time

from tetris_game import TetrisGame

from tetris_cli_player.input.keyboard import start_keyboard_input_daemon, Key
from tetris_cli_player.render import visualize_state

FPS = 60.0
FRAME_DURATION = 1.0 / FPS

DAS_ENTRY = 10 # frames
DAS_RATE = 2 # frames

game: TetrisGame | None = None
stopped = False

# game frame count
t = 0

# variables to track if keys are being held for DAS (delayed auto shift)
das_left_press_t: int | None = None
das_right_press_t: int | None = None

def main():
    global game, t

    if os.name == "posix" and os.geteuid() != 0:
        # re-execute with sudo for keyboard input reading on linux
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    
    try:
        game = TetrisGame()
        game._falling_piece_bb_y = 10

        start_keyboard_input_daemon(callback=handle_key)

        prev_frame_time = time.perf_counter()
        while not stopped:

            current_t = time.perf_counter()
            delta_t = current_t - prev_frame_time
            if delta_t < FRAME_DURATION:
                # not time for a new frame
                continue
            prev_frame_time = current_t

            # delayed auto shift
            if das_left_press_t is not None:
                hold_duration = t - das_left_press_t
                if hold_duration > DAS_ENTRY and hold_duration % DAS_RATE == 0:
                    game.shift_left()
            if das_right_press_t is not None:
                hold_duration = t - das_right_press_t
                if hold_duration > DAS_ENTRY and hold_duration % DAS_RATE == 0:
                    game.shift_right()

            # game._falling_piece_rot = (game._falling_piece_rot + 1) % 4
            state = game.get_state()
            visualize_state(state)

            t += 1
    except KeyboardInterrupt:
        pass


def handle_key(key: Key, pressed: bool):
    """
    Callback called by the keyboard listener
    """
    global game, stopped, das_left_press_t, das_right_press_t

    if key == Key.Q:
        stopped = True
        sys.exit(0)

    if game is  None:
        return

    if pressed:
        match key:
            case Key.LEFT:
                game.shift_left()
                das_left_press_t = t
            case Key.RIGHT:
                game.shift_right()
                das_right_press_t = t
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
            case Key.L_SHIFT | Key.R_SHIFT | Key.C:
                game.hold()
    else:
        match key:
            case Key.LEFT:
                das_left_press_t = None
            case Key.RIGHT:
                das_right_press_t = None


if __name__ == "__main__":
    main()
