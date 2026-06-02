from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from . import rules
from .board import BoardState
from .move import Move


class GameStatus(Enum):
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW_FIFTY_MOVES = "draw_fifty_moves"
    DRAW_INSUFFICIENT_MATERIAL = "draw_insufficient_material"


class GameResult(Enum):
    WHITE_WINS = "1-0"
    BLACK_WINS = "0-1"
    DRAW = "1/2-1/2"


@dataclass
class Game:
    state: BoardState = field(default_factory=BoardState.initial)

    @classmethod
    def new(cls) -> "Game":
        return cls()

    def legal_moves(self) -> list[Move]:
        return rules.generate_legal_moves(self.state)

    def make_move(self, move: Move) -> None:
        legal = self.legal_moves()
        if move not in legal:
            raise ValueError(f"Illegal move: {move}")
        self.state.apply_move(move)

    def undo_move(self) -> None:
        self.state.undo_move()

    def is_check(self) -> bool:
        return rules.is_in_check(self.state)

    def is_checkmate(self) -> bool:
        return rules.is_checkmate(self.state)

    def is_stalemate(self) -> bool:
        return rules.is_stalemate(self.state)

    def is_fifty_move_rule(self) -> bool:
        # The fifty-move rule is 50 full moves without a pawn move
        # or capture, which is 100 halfmoves.
        return self.state.halfmove_clock >= 100

    def is_insufficient_material(self) -> bool:
        """Return True for K vs K, K+B vs K, and K+N vs K endgames."""
        non_king_pieces = {"w": [], "b": []}
        for _, _, piece in self.state.all_pieces():
            if piece[1] != "K":
                non_king_pieces[piece[0]].append(piece[1])

        if not non_king_pieces["w"] and not non_king_pieces["b"]:
            return True
        for side, other in (("w", "b"), ("b", "w")):
            if not non_king_pieces[other] and non_king_pieces[side] in (["B"], ["N"]):
                return True
        return False

    def status(self) -> GameStatus:
        if self.is_checkmate():
            return GameStatus.CHECKMATE
        if self.is_stalemate():
            return GameStatus.STALEMATE
        if self.is_fifty_move_rule():
            return GameStatus.DRAW_FIFTY_MOVES
        if self.is_insufficient_material():
            return GameStatus.DRAW_INSUFFICIENT_MATERIAL
        return GameStatus.ONGOING

    def result(self) -> Optional[GameResult]:
        status = self.status()
        if status == GameStatus.CHECKMATE:
            # If it's white to move and they're checkmated, black wins
            return (
                GameResult.BLACK_WINS
                if self.state.white_to_move
                else GameResult.WHITE_WINS
            )
        if status in (
            GameStatus.STALEMATE,
            GameStatus.DRAW_FIFTY_MOVES,
            GameStatus.DRAW_INSUFFICIENT_MATERIAL,
        ):
            return GameResult.DRAW
        return None

    def is_over(self) -> bool:
        return self.status() != GameStatus.ONGOING

    def fen(self) -> str:
        return self.state.fen()


__all__ = ["Game", "GameStatus", "GameResult"]