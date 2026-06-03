"""Static evaluation of a chess position.

Provides two scoring functions:

* :func:`material_score` - sum of piece values only.
* :func:`board_score` - material plus piece-square table bonuses,
  with checkmate and stalemate handled explicitly.

Scores are returned from white's perspective: positive values favour
white, negative values favour black.
"""
from __future__ import annotations

from core.board import BoardState
from core.rules import is_checkmate, is_stalemate


CHECKMATE = 1000
STALEMATE = 0
POSITION_WEIGHT = 0.1

PIECE_VALUES: dict[str, int] = {
    "K": 0,
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
}

KNIGHT_SCORES: list[list[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]

BISHOP_SCORES: list[list[int]] = [
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [4, 3, 2, 1, 1, 2, 3, 4],
]

QUEEN_SCORES: list[list[int]] = [
    [1, 1, 1, 3, 1, 1, 1, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 1, 2, 3, 3, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1, 1],
]

ROOK_SCORES: list[list[int]] = [
    [4, 3, 4, 4, 4, 4, 3, 4],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [4, 3, 4, 4, 4, 4, 3, 4],
]

WHITE_PAWN_SCORES: list[list[int]] = [
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [1, 2, 3, 3, 2, 2, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

BLACK_PAWN_SCORES: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 3, 2, 2, 1, 1],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
]

PIECE_POSITION_SCORES: dict[str, list[list[int]]] = {
    "N": KNIGHT_SCORES,
    "Q": QUEEN_SCORES,
    "B": BISHOP_SCORES,
    "R": ROOK_SCORES,
    "wP": WHITE_PAWN_SCORES,
    "bP": BLACK_PAWN_SCORES,
}


def material_score(board: list[list[str]]) -> float:
    """Return the material balance of ``board`` from white's perspective."""
    score = 0.0
    for row in board:
        for square in row:
            if square == "--":
                continue
            if square[0] == "w":
                score += PIECE_VALUES[square[1]]
            else:
                score -= PIECE_VALUES[square[1]]
    return score


def board_score(state: BoardState) -> float:
    """Return the positional score of ``state`` from white's perspective.

    Returns ``CHECKMATE`` when the side to move is checkmated and is
    losing, ``-CHECKMATE`` for the opposite case, and ``STALEMATE`` for
    a drawn position.
    """
    if is_checkmate(state):
        return -CHECKMATE if state.white_to_move else CHECKMATE
    if is_stalemate(state):
        return STALEMATE

    score = 0.0
    for row in range(8):
        for col in range(8):
            square = state.board[row][col]
            if square == "--":
                continue

            piece_position_score = 0.0
            if square[1] != "K":
                if square[1] == "P":
                    piece_position_score = PIECE_POSITION_SCORES[square][row][col]
                else:
                    piece_position_score = PIECE_POSITION_SCORES[square[1]][row][col]

            piece_total = PIECE_VALUES[square[1]] + piece_position_score * POSITION_WEIGHT
            if square[0] == "w":
                score += piece_total
            else:
                score -= piece_total
    return score


__all__ = [
    "CHECKMATE",
    "STALEMATE",
    "POSITION_WEIGHT",
    "PIECE_VALUES",
    "PIECE_POSITION_SCORES",
    "material_score",
    "board_score",
]
