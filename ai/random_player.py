"""Fallback AI that picks a random legal move.

This is a temporary placeholder.
"""
from __future__ import annotations

import random
from typing import Optional

from core.game import Game
from core.move import Move


def random_move(game: Game, rng: random.Random | None = None) -> Optional[Move]:
    """Return a uniformly random legal move, or ``None`` if no moves exist."""
    moves = game.legal_moves()
    if not moves:
        return None
    if rng is None:
        return random.choice(moves)
    return rng.choice(moves)


__all__ = ["random_move"]
