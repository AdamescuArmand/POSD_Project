from __future__ import annotations

from core.board import BoardState
from core.rules import is_checkmate, is_stalemate

pieceScore = {"K": 0, "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9}

knightScores = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]

bishopScores = [
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [4, 3, 2, 1, 1, 2, 3, 4],
]

queenScores = [
    [1, 1, 1, 3, 1, 1, 1, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 1, 2, 3, 3, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1, 1],
]

rookScores = [
    [4, 3, 4, 4, 4, 4, 3, 4],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [4, 3, 4, 4, 4, 4, 3, 4],
]

whitePawnScores = [
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [1, 2, 3, 3, 2, 2, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

blackPawnScores = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 3, 2, 2, 1, 1],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
]

piecePositionScores = {
    "N": knightScores,
    "Q": queenScores,
    "B": bishopScores,
    "R": rookScores,
    "wP": whitePawnScores,
    "bP": blackPawnScores,
}

CHECKMATE = 1000
STALEMATE = 0
POSITION_WEIGHT = 0.1


def materialScore(board: list[list[str]]) -> float:
    score = 0.0
    for row in board:
        for square in row:
            if square == "--":
                continue
            if square[0] == "w":
                score += pieceScore[square[1]]
            else:
                score -= pieceScore[square[1]]
    return score


def boardScore(state: BoardState) -> float:
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
                    piece_position_score = piecePositionScores[square][row][col]
                else:
                    piece_position_score = piecePositionScores[square[1]][row][col]

            piece_total = pieceScore[square[1]] + piece_position_score * POSITION_WEIGHT
            if square[0] == "w":
                score += piece_total
            else:
                score -= piece_total
    return score


__all__ = [
    "CHECKMATE",
    "STALEMATE",
    "pieceScore",
    "piecePositionScores",
    "materialScore",
    "boardScore",
]