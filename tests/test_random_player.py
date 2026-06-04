from __future__ import annotations

import random

from ai.random_player import random_move
from core.board import BoardState, CastlingRights, EMPTY
from core.game import Game


def test_random_move_returns_a_legal_move():
    game = Game.new()
    legal = game.legal_moves()
    move = random_move(game)
    assert move is not None
    assert move in legal


def test_random_move_is_deterministic_with_seeded_rng():
    game = Game.new()
    rng_a = random.Random(42)
    rng_b = random.Random(42)
    assert random_move(game, rng=rng_a) == random_move(game, rng=rng_b)


def test_random_move_returns_none_when_no_legal_moves():
    # Fool's-mate-style position with black checkmated: black has no legal moves.
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=False,
        castling_rights=CastlingRights(False, False, False, False),
    )
    state.set_piece(0, 0, "bK")
    state.set_piece(1, 1, "wQ")
    state.set_piece(2, 2, "wK")
    game = Game(state=state)
    assert random_move(game) is None
