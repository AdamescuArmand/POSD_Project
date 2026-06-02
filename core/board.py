from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .move import Move, square_to_algebraic

BoardGrid = list[list[str]]
EMPTY = "--"
STARTING_BOARD: BoardGrid = [
    ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
    ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
    ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
]


@dataclass(slots=True)
class CastlingRights:
    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True

    def copy(self) -> "CastlingRights":
        return CastlingRights(
            white_kingside=self.white_kingside,
            white_queenside=self.white_queenside,
            black_kingside=self.black_kingside,
            black_queenside=self.black_queenside,
        )

    def fen_fragment(self) -> str:
        rights = []
        if self.white_kingside:
            rights.append("K")
        if self.white_queenside:
            rights.append("Q")
        if self.black_kingside:
            rights.append("k")
        if self.black_queenside:
            rights.append("q")
        return "".join(rights) or "-"


@dataclass(slots=True)
class _UndoRecord:
    """Internal snapshot of state required to reverse a single move."""

    move: Move
    captured_piece: str
    castling_rights: CastlingRights
    en_passant_target: Optional[tuple[int, int]]
    halfmove_clock: int
    white_king_pos: tuple[int, int]
    black_king_pos: tuple[int, int]
    fullmove_number: int
    had_capture: bool


@dataclass(slots=True)
class BoardState:
    board: BoardGrid = field(default_factory=lambda: [row[:] for row in STARTING_BOARD])
    white_to_move: bool = True
    white_king_pos: tuple[int, int] = (7, 4)
    black_king_pos: tuple[int, int] = (0, 4)
    castling_rights: CastlingRights = field(default_factory=CastlingRights)
    en_passant_target: Optional[tuple[int, int]] = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    move_history: list[Move] = field(default_factory=list)
    captured_pieces: list[str] = field(default_factory=list)
    _undo_stack: list[_UndoRecord] = field(default_factory=list)

    @classmethod
    def initial(cls) -> "BoardState":
        return cls()

    def copy(self) -> "BoardState":
        return BoardState(
            board=[row[:] for row in self.board],
            white_to_move=self.white_to_move,
            white_king_pos=self.white_king_pos,
            black_king_pos=self.black_king_pos,
            castling_rights=self.castling_rights.copy(),
            en_passant_target=self.en_passant_target,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            move_history=list(self.move_history),
            captured_pieces=list(self.captured_pieces),
            _undo_stack=list(self._undo_stack),
        )

    def piece_at(self, row: int, col: int) -> str:
        self._validate_square(row, col)
        return self.board[row][col]

    def set_piece(self, row: int, col: int, piece: str) -> None:
        self._validate_square(row, col)
        self.board[row][col] = piece
        if piece == "wK":
            self.white_king_pos = (row, col)
        elif piece == "bK":
            self.black_king_pos = (row, col)

    def clear_square(self, row: int, col: int) -> None:
        self.set_piece(row, col, EMPTY)

    def is_empty(self, row: int, col: int) -> bool:
        return self.piece_at(row, col) == EMPTY

    def color_at(self, row: int, col: int) -> Optional[str]:
        piece = self.piece_at(row, col)
        return None if piece == EMPTY else piece[0]

    def occupied_by(self, row: int, col: int, color: str) -> bool:
        return self.color_at(row, col) == color

    def enemy_of_side_to_move(self) -> str:
        return "b" if self.white_to_move else "w"

    def side_to_move(self) -> str:
        return "w" if self.white_to_move else "b"

    def king_position(self, color: str) -> tuple[int, int]:
        if color == "w":
            return self.white_king_pos
        if color == "b":
            return self.black_king_pos
        raise ValueError("color must be 'w' or 'b'")

    def all_pieces(self) -> Iterable[tuple[int, int, str]]:
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != EMPTY:
                    yield row, col, piece

    def pieces_of_color(self, color: str) -> Iterable[tuple[int, int, str]]:
        for row, col, piece in self.all_pieces():
            if piece[0] == color:
                yield row, col, piece

    def apply_move(self, move: Move) -> None:
        moving_piece = self.piece_at(move.start_row, move.start_col)

        if move.is_en_passant:
            captured_piece = self.piece_at(move.start_row, move.end_col)
        else:
            captured_piece = self.piece_at(move.end_row, move.end_col)
        had_capture = captured_piece != EMPTY

        self._undo_stack.append(
            _UndoRecord(
                move=move,
                captured_piece=captured_piece,
                castling_rights=self.castling_rights.copy(),
                en_passant_target=self.en_passant_target,
                halfmove_clock=self.halfmove_clock,
                white_king_pos=self.white_king_pos,
                black_king_pos=self.black_king_pos,
                fullmove_number=self.fullmove_number,
                had_capture=had_capture,
            )
        )

        self.clear_square(move.start_row, move.start_col)

        if move.is_en_passant:
            self.clear_square(move.start_row, move.end_col)

        placed_piece = moving_piece
        if move.is_promotion:
            placed_piece = moving_piece[0] + move.promotion_piece

        self.set_piece(move.end_row, move.end_col, placed_piece)

        if move.is_castling:
            if move.end_col == 6:
                rook = self.piece_at(move.end_row, 7)
                self.clear_square(move.end_row, 7)
                self.set_piece(move.end_row, 5, rook)
            elif move.end_col == 2:
                rook = self.piece_at(move.end_row, 0)
                self.clear_square(move.end_row, 0)
                self.set_piece(move.end_row, 3, rook)

        if had_capture:
            self.captured_pieces.append(captured_piece)

        self.move_history.append(move)
        self._update_clocks(moving_piece, captured_piece)
        self._update_en_passant_target(moving_piece, move)
        self._update_castling_rights(moving_piece, move, captured_piece)

        if not self.white_to_move:
            self.fullmove_number += 1
        self.white_to_move = not self.white_to_move

    def undo_move(self) -> None:
        if not self._undo_stack:
            raise ValueError("No moves to undo")

        record = self._undo_stack.pop()
        move = record.move

        # Restore turn and counters
        self.white_to_move = not self.white_to_move
        self.castling_rights = record.castling_rights
        self.en_passant_target = record.en_passant_target
        self.halfmove_clock = record.halfmove_clock
        self.fullmove_number = record.fullmove_number

        # Put the moved piece back (demote if it was a promotion)
        original_piece = move.piece_moved
        self.board[move.start_row][move.start_col] = original_piece

        # Restore the destination square
        if move.is_en_passant:
            self.board[move.end_row][move.end_col] = EMPTY
            self.board[move.start_row][move.end_col] = record.captured_piece
        else:
            self.board[move.end_row][move.end_col] = record.captured_piece

        # Undo castling rook move
        if move.is_castling:
            if move.end_col == 6:
                rook = self.board[move.end_row][5]
                self.board[move.end_row][5] = EMPTY
                self.board[move.end_row][7] = rook
            elif move.end_col == 2:
                rook = self.board[move.end_row][3]
                self.board[move.end_row][3] = EMPTY
                self.board[move.end_row][0] = rook

        # Restore king positions (must come after board restore)
        self.white_king_pos = record.white_king_pos
        self.black_king_pos = record.black_king_pos

        self.move_history.pop()
        if record.had_capture:
            self.captured_pieces.pop()

    def board_rows(self) -> list[str]:
        return [" ".join(row) for row in self.board]

    def fen_board(self) -> str:
        rows = []
        for row in self.board:
            empty_count = 0
            fen_row = []
            for piece in row:
                if piece == EMPTY:
                    empty_count += 1
                else:
                    if empty_count:
                        fen_row.append(str(empty_count))
                        empty_count = 0
                    color, kind = piece[0], piece[1]
                    fen_row.append(kind.upper() if color == "w" else kind.lower())
            if empty_count:
                fen_row.append(str(empty_count))
            rows.append("".join(fen_row))
        return "/".join(rows)

    def fen(self) -> str:
        side = "w" if self.white_to_move else "b"
        en_passant = "-"
        if self.en_passant_target is not None:
            en_passant = square_to_algebraic(*self.en_passant_target)
        return (
            f"{self.fen_board()} {side} {self.castling_rights.fen_fragment()} "
            f"{en_passant} {self.halfmove_clock} {self.fullmove_number}"
        )

    def _update_clocks(self, moving_piece: str, captured_piece: str) -> None:
        if moving_piece[1] == "P" or captured_piece != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

    def _update_en_passant_target(self, moving_piece: str, move: Move) -> None:
        self.en_passant_target = None
        if moving_piece[1] == "P" and abs(move.end_row - move.start_row) == 2:
            middle_row = (move.start_row + move.end_row) // 2
            self.en_passant_target = (middle_row, move.start_col)

    def _update_castling_rights(self, moving_piece: str, move: Move, captured_piece: str) -> None:
        if moving_piece == "wK":
            self.castling_rights.white_kingside = False
            self.castling_rights.white_queenside = False
        elif moving_piece == "bK":
            self.castling_rights.black_kingside = False
            self.castling_rights.black_queenside = False
        elif moving_piece == "wR":
            if (move.start_row, move.start_col) == (7, 0):
                self.castling_rights.white_queenside = False
            elif (move.start_row, move.start_col) == (7, 7):
                self.castling_rights.white_kingside = False
        elif moving_piece == "bR":
            if (move.start_row, move.start_col) == (0, 0):
                self.castling_rights.black_queenside = False
            elif (move.start_row, move.start_col) == (0, 7):
                self.castling_rights.black_kingside = False

        if captured_piece == "wR":
            if (move.end_row, move.end_col) == (7, 0):
                self.castling_rights.white_queenside = False
            elif (move.end_row, move.end_col) == (7, 7):
                self.castling_rights.white_kingside = False
        elif captured_piece == "bR":
            if (move.end_row, move.end_col) == (0, 0):
                self.castling_rights.black_queenside = False
            elif (move.end_row, move.end_col) == (0, 7):
                self.castling_rights.black_kingside = False

    @staticmethod
    def _validate_square(row: int, col: int) -> None:
        if not (0 <= row < 8 and 0 <= col < 8):
            raise ValueError(f"Invalid square coordinates: ({row}, {col})")


__all__ = [
    "BoardState",
    "CastlingRights",
    "STARTING_BOARD",
    "BoardGrid",
    "EMPTY",
]