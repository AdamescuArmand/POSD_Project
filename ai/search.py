"""Move search for chess positions.

Public entry points:

* :func:`find_random_move` - choose a random legal move.
* :func:`find_best_move_one_ply` - shallow 1-ply move selection
  (kept for completeness, but :func:`find_best_move` is generally
  preferred).
* :func:`find_best_move` - choose the best move using negamax
  with alpha-beta pruning.
* :func:`negamax_alpha_beta` - the pure recursive search routine;
  exposed primarily so tests can probe its score values directly.

Scores are returned from the perspective of the side whose turn it is
to move at that node: positive values are good for the moving side,
negative are bad. ``MATE_SCORE`` is used as the alpha-beta bound and
is intentionally larger than any ``board_score`` value so that
mate scores dominate heuristic ones.
"""
from __future__ import annotations

import random
from typing import Optional

from core.board import BoardState
from core.move import Move
from core.rules import generate_legal_moves, is_in_check

from .evaluation import board_score


DEPTH = 3
MATE_SCORE = 100_000


def find_random_move(valid_moves: list[Move]) -> Optional[Move]:
    """Return a uniformly random legal move, or ``None`` if the list is empty."""
    if not valid_moves:
        return None
    return random.choice(valid_moves)


def find_best_move_one_ply(
    state: BoardState, valid_moves: list[Move]
) -> Optional[Move]:
    """Pick the move where the opponent's best response is least harmful.

    This is a simple two-ply lookahead (our move, then opponent's best
    reply) using only the static evaluation. It is kept mainly for
    benchmarking; :func:`find_best_move` is stronger at any depth.
    """
    if not valid_moves:
        return None

    turn_multiplier = 1 if state.white_to_move else -1
    best_score = -MATE_SCORE
    best_move: Optional[Move] = None
    candidate_moves = list(valid_moves)
    random.shuffle(candidate_moves)

    for player_move in candidate_moves:
        state.apply_move(player_move)
        opponent_moves = generate_legal_moves(state)

        if not opponent_moves:
            # Opponent has no moves: either mate (very good for us) or stalemate.
            score = turn_multiplier * board_score(state)
        else:
            # Opponent picks the move that's worst for us.
            opponent_min_score = MATE_SCORE
            for opponent_move in opponent_moves:
                state.apply_move(opponent_move)
                response_score = turn_multiplier * board_score(state)
                if response_score < opponent_min_score:
                    opponent_min_score = response_score
                state.undo_move()
            score = opponent_min_score

        state.undo_move()

        if score > best_score:
            best_score = score
            best_move = player_move

    return best_move


def find_best_move(
    state: BoardState, valid_moves: list[Move], depth: int = DEPTH
) -> Optional[Move]:
    """Return the best move found by negamax with alpha-beta pruning.

    The root iterates over the legal moves directly so the chosen move
    can be tracked locally — no globals, and the recursive search
    function stays pure (returns score only).
    """
    if not valid_moves:
        return None

    turn_multiplier = 1 if state.white_to_move else -1
    candidate_moves = list(valid_moves)
    random.shuffle(candidate_moves)

    best_move: Optional[Move] = None
    best_score = -MATE_SCORE
    alpha = -MATE_SCORE
    beta = MATE_SCORE

    for move in candidate_moves:
        state.apply_move(move)
        next_moves = generate_legal_moves(state)
        score = -negamax_alpha_beta(
            state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier
        )
        state.undo_move()

        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score

    return best_move


def negamax_alpha_beta(
    state: BoardState,
    valid_moves: list[Move],
    depth: int,
    alpha: float,
    beta: float,
    turn_multiplier: int,
) -> float:
    """Return the negamax score of ``state`` from the side-to-move's perspective.

    Terminal handling:

    * No legal moves + in check => mate. Returns ``-MATE_SCORE - depth``
      so that shallower mates score higher than deeper ones (the search
      prefers faster mates and slower losses).
    * No legal moves + not in check => stalemate, scores ``0``.
    * ``depth == 0`` => returns the static evaluation, normalised to
      the moving side's perspective.
    """
    if not valid_moves:
        if is_in_check(state):
            return -MATE_SCORE - depth
        return 0

    if depth == 0:
        return turn_multiplier * board_score(state)

    max_score = -MATE_SCORE
    for move in valid_moves:
        state.apply_move(move)
        next_moves = generate_legal_moves(state)
        score = -negamax_alpha_beta(
            state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier
        )
        state.undo_move()

        if score > max_score:
            max_score = score
        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    return max_score


__all__ = [
    "DEPTH",
    "MATE_SCORE",
    "find_random_move",
    "find_best_move_one_ply",
    "find_best_move",
    "negamax_alpha_beta",
]
