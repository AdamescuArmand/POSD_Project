from __future__ import annotations

import random
from typing import Optional

from core.board import BoardState
from core.move import Move
from core.rules import generate_legal_moves
from core.rules import generate_legal_moves, is_in_check

from .evaluation import CHECKMATE, boardScore

DEPTH = 3
MATE_SCORE = 100000
nextMove: Optional[Move] = None


def findRandomMove(validMoves: list[Move]) -> Optional[Move]:
    if not validMoves:
        return None
    return random.choice(validMoves)


def findBestMove(state: BoardState, validMoves: list[Move]) -> Optional[Move]:
    turnMultiplier = 1 if state.white_to_move else -1
    playerMaxScore = -CHECKMATE
    bestMove: Optional[Move] = None
    candidateMoves = list(validMoves)
    random.shuffle(candidateMoves)

    for playerMove in candidateMoves:
        state.apply_move(playerMove)
        opponentMoves = generate_legal_moves(state)

        if not opponentMoves:
            score = -turnMultiplier * boardScore(state)
            state.undo_move()
            if score > playerMaxScore:
                playerMaxScore = score
                bestMove = playerMove
            continue

        opponentMinScore = CHECKMATE
        for opponentMove in opponentMoves:
            state.apply_move(opponentMove)
            score = turnMultiplier * boardScore(state)
            if score < opponentMinScore:
                opponentMinScore = score
            state.undo_move()

        if playerMaxScore < opponentMinScore:
            playerMaxScore = opponentMinScore
            bestMove = playerMove
        state.undo_move()

    return bestMove


def findBestMoveMinMax(state: BoardState, validMoves: list[Move], depth: int = DEPTH) -> Optional[Move]:
    global nextMove
    nextMove = None
    candidateMoves = list(validMoves)
    random.shuffle(candidateMoves)
    findMoveNegaMaxAlphaBetaPruning(
        state,
        candidateMoves,
        depth,
        -MATE_SCORE,
        MATE_SCORE,
        1 if state.white_to_move else -1,
        depth,
    )
    return nextMove


def findMoveNegaMax(state: BoardState, validMoves: list[Move], depth: int, turnMultiplier: int) -> float:
    global nextMove

    if not validMoves:
        if is_in_check(state):
            return -MATE_SCORE - depth
        return 0

    if depth == 0:
        return turnMultiplier * boardScore(state)

    maxScore = -MATE_SCORE
    for move in validMoves:
        state.apply_move(move)
        nextMoves = generate_legal_moves(state)
        score = -findMoveNegaMax(state, nextMoves, depth - 1, -turnMultiplier)
        state.undo_move()

        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move

    return maxScore


def findMoveNegaMaxAlphaBetaPruning(
    state: BoardState,
    validMoves: list[Move],
    depth: int,
    alpha: float,
    beta: float,
    turnMultiplier: int,
    rootDepth: Optional[int] = None,
) -> float:
    global nextMove

    if rootDepth is None:
        rootDepth = depth

    if not validMoves:
        if is_in_check(state):
            return -MATE_SCORE - depth
        return 0

    if depth == 0:
        return turnMultiplier * boardScore(state)

    maxScore = -MATE_SCORE

    for move in validMoves:
        state.apply_move(move)
        nextMoves = generate_legal_moves(state)
        score = -findMoveNegaMaxAlphaBetaPruning(
            state,
            nextMoves,
            depth - 1,
            -beta,
            -alpha,
            -turnMultiplier,
            rootDepth,
        )
        state.undo_move()

        if score > maxScore:
            maxScore = score
            if depth == rootDepth:
                nextMove = move

        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break

    return maxScore



__all__ = [
    "DEPTH",
    "findRandomMove",
    "findBestMove",
    "findBestMoveMinMax",
    "findMoveNegaMax",
    "findMoveNegaMaxAlphaBetaPruning",
]