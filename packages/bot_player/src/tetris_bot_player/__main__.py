import sys
import enum
import threading
from typing import NamedTuple
import time

from tetris_game import TetrisGame, TetrisGameState, Piece, GameStatus
from tetris_cli_player import render as cli_render


class BotState(enum.IntEnum):
    Ready = enum.auto()
    Evaluating = enum.auto()
    Executing = enum.auto()
    GameOver = enum.auto()


class MoveSequence(NamedTuple):
    # Number of clockwise rotations
    rot: int
    # Lateral shift, <0 is left, >0 is right
    shift: int

start_evaluating_flag = threading.Event()

bot_state: BotState = BotState.Ready


# All move sequences to test for the O piece
MOVE_SEQUENCES_O: list[MoveSequence] = [MoveSequence(*t) for t in [
    (0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)
]]

# All move sequences to test for the I piece
MOVE_SEQUENCES_I: list[MoveSequence] = [MoveSequence(*t) for t in [
    (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3),
    (1, -5), (1, -4), (1, -3), (1, -2), (1, -1), (0, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    (2, -3), (2, -2), (2, -1), (2, 0), (2, 1), (2, 2), (2, 3),
    (1, -4), (1, -3), (1, -2), (1, -1), (0, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
]]

# All move sequences to test for the L, J, S, Z, and T pieces
MOVE_SEQUENCES_LJSZT: list[MoveSequence] = [MoveSequence(*t) for t in [
    (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
    (1, -4), (1, -3), (1, -2), (1, -1), (0, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    (2, -3), (2, -2), (2, -1), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
    (3, -3), (3, -2), (3, -1), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), 
]]

def apply_move_sequence(game: TetrisGame, seq: MoveSequence):
    """
    Applies rotations and shifts from a move sequence (no hard drop)
    """
    match seq.rot:
        case 1:
            game.rotate_cw()
        case 2:
            game.rotate_cw()
            game.rotate_cw()
        case 3:
            game.rotate_ccw()
    if seq.shift < 0:
        for _ in range(-seq.shift):
            game.shift_left()
    elif seq.shift > 0:
        for _ in range(seq.shift):
            game.shift_right()

def action_count(seq: MoveSequence) -> int:
    """
    How "expensive" a move sequence is
    """
    actions = abs(seq.shift)
    if seq.rot % 4 == 3:
        actions += 1
    else:
        actions += seq.rot % 4
    return actions


def rate_game_state(game_state: TetrisGameState) -> float:
    """
    Where the magic happens
    """
    score = float(TetrisGame.BOARD_HEIGHT)

    for y in range(0, TetrisGame.BOARD_HEIGHT):
        empty = True
        for x in range(0, TetrisGame.BOARD_WIDTH):
            if game_state.get_board(x, y) == Piece.NULL:
                # check for holes
                if y + 1 < TetrisGame.BOARD_HEIGHT and game_state.get_board(x, y+1) != Piece.NULL:
                    score -= 4.0
            else:
                empty = False
        if empty:
            return score
        score -= 1.0


def main():
    global bot_state, start_evaluating_flag

    try:
        live_game = TetrisGame(state_change_callback=on_state_change)

        # inital render
        cli_render.visualize_state(live_game.get_state(), show_ghost_piece=False)

        # start game thread
        live_game.start()

        while True:
            # wait for time to evaluate
            while not start_evaluating_flag.wait(1.0):
                print("checking", bot_state)
                if bot_state == BotState.GameOver:
                    sys.exit(0)
            start_evaluating_flag.clear()

            bot_state = BotState.Evaluating

            game_state = live_game.get_state()
            game_copy = live_game.get_frozen_copy()

            sequences = MOVE_SEQUENCES_LJSZT
            if game_state.falling_piece == Piece.O:
                sequences = MOVE_SEQUENCES_O
            elif game_state.falling_piece == Piece.I:
                sequences = MOVE_SEQUENCES_I

            best_score = float("-inf")
            should_hold = False
            best_seq = None
            for seq in sequences:
                for holding in (True, False):
                    new_game = game_copy.get_frozen_copy()
                    if holding:
                        new_game.hold()
                    apply_move_sequence(new_game, seq)
                    new_game.hard_drop()
                    score = rate_game_state(new_game.get_state())

                    if score > best_score:
                        best_score = score
                        best_seq = seq
                        should_hold = holding


            assert best_seq is not None

            # execute best seq
            print(f"Executing sequence: {best_seq} (score: {best_score})", end="\r")

            bot_state = BotState.Executing
            if should_hold:
                live_game.hold()
            apply_move_sequence(live_game, best_seq)
            live_game.hard_drop()

            bot_state = BotState.Ready

    except KeyboardInterrupt:
        pass
    finally:
        cli_render.cleanup()

def on_state_change(game_state: TetrisGameState):
    """
    Callback called by the game's thread when game state updates (supposed to be light)
    """
    global bot_state, start_evaluating_flag

    if game_state.status == GameStatus.GAME_OVER:
        bot_state = BotState.GameOver

    match bot_state:
        case BotState.Ready:
            if game_state.status == GameStatus.PLAYING:
                # start evaluating
                start_evaluating_flag.set()
        case BotState.Evaluating:
            # uhhh I think this is a problem (TODO think about handinglin this)
            pass
        case BotState.Executing:
            # do nothing
            pass
        case BotState.GameOver:
            pass

    details = [
        f"State: {bot_state}"
    ]

    cli_render.visualize_state(game_state, show_ghost_piece=False, details_text=details)



