from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

FILES = "abcdefgh"
RANKS = "87654321"
PROMOTION_PIECES = {"Q", "R", "B", "N"}


def square_to_algebraic(row: int, col: int) -> str:
    if not (0 <= row < 8 and 0 <= col < 8):
        raise ValueError(f"Invalid square coordinates: ({row}, {col})")
    return f"{FILES[col]}{RANKS[row]}"


def algebraic_to_square(square: str) -> tuple[int, int]:
    if len(square) != 2 or square[0] not in FILES or square[1] not in "12345678":
        raise ValueError(f"Invalid algebraic square: {square!r}")
    col = FILES.index(square[0])
    row = 8 - int(square[1])
    return row, col


@dataclass(frozen=True, slots=True)
class Move:
    start_row: int
    start_col: int
    end_row: int
    end_col: int
    piece_moved: str
    piece_captured: str = "--"
    promotion_piece: Optional[str] = None
    is_en_passant: bool = False
    is_castling: bool = False

    def __post_init__(self) -> None:
        for value in (self.start_row, self.start_col, self.end_row, self.end_col):
            if not (0 <= value < 8):
                raise ValueError("Move coordinates must be between 0 and 7")

        if len(self.piece_moved) != 2 or self.piece_moved[0] not in {"w", "b"}:
            raise ValueError(f"Invalid moved piece: {self.piece_moved!r}")

        if self.piece_captured != "--":
            if len(self.piece_captured) != 2 or self.piece_captured[0] not in {"w", "b"}:
                raise ValueError(f"Invalid captured piece: {self.piece_captured!r}")

        if self.promotion_piece is not None and self.promotion_piece not in PROMOTION_PIECES:
            raise ValueError("promotion_piece must be one of 'Q', 'R', 'B', 'N'")

    @property
    def start(self) -> tuple[int, int]:
        return self.start_row, self.start_col

    @property
    def end(self) -> tuple[int, int]:
        return self.end_row, self.end_col

    @property
    def color(self) -> str:
        return self.piece_moved[0]

    @property
    def piece_type(self) -> str:
        return self.piece_moved[1]

    @property
    def is_capture(self) -> bool:
        return self.piece_captured != "--" or self.is_en_passant

    @property
    def is_promotion(self) -> bool:
        return self.promotion_piece is not None

    def uci(self) -> str:
        move = f"{self.start_square()}{self.end_square()}"
        if self.promotion_piece:
            move += self.promotion_piece.lower()
        return move

    def start_square(self) -> str:
        return square_to_algebraic(self.start_row, self.start_col)

    def end_square(self) -> str:
        return square_to_algebraic(self.end_row, self.end_col)

    def to_tuple(self) -> tuple[int, int, int, int]:
        return self.start_row, self.start_col, self.end_row, self.end_col

    def matches(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        return self.start == start and self.end == end

    def with_promotion(self, promotion_piece: str) -> "Move":
        return Move(
            start_row=self.start_row,
            start_col=self.start_col,
            end_row=self.end_row,
            end_col=self.end_col,
            piece_moved=self.piece_moved,
            piece_captured=self.piece_captured,
            promotion_piece=promotion_piece,
            is_en_passant=self.is_en_passant,
            is_castling=self.is_castling,
        )

    def __str__(self) -> str:
        return self.uci()


__all__ = [
    "Move",
    "square_to_algebraic",
    "algebraic_to_square",
    "PROMOTION_PIECES",
]
