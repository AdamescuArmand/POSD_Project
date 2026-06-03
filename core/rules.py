from __future__ import annotations

from typing import Iterator

from .board import BoardState, EMPTY
from .move import Move, PROMOTION_PIECES


KNIGHT_OFFSETS: list[tuple[int, int]] = [
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
]
BISHOP_DIRECTIONS: list[tuple[int, int]] = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRECTIONS: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
KING_OFFSETS: list[tuple[int, int]] = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


def enemy_color(color: str) -> str:
    if color == "w":
        return "b"
    if color == "b":
        return "w"
    raise ValueError("color must be 'w' or 'b'")


def generate_legal_moves(state: BoardState) -> list[Move]:
    """Return all legal moves for the side to move."""
    color = state.side_to_move()
    enemy = enemy_color(color)
    legal: list[Move] = []
    for move in generate_pseudo_legal_moves(state):
        state.apply_move(move)
        king_row, king_col = state.king_position(color)
        if not is_square_attacked(state, king_row, king_col, enemy):
            legal.append(move)
        state.undo_move()
    return legal


def generate_pseudo_legal_moves(state: BoardState) -> Iterator[Move]:
    """Yield every move that follows piece movement rules.

    Pseudo-legal moves do not filter out moves that leave the moving
    side's king in check — that filtering is done in
    :func:`generate_legal_moves`.
    """
    color = state.side_to_move()
    for row, col, piece in list(state.pieces_of_color(color)):
        kind = piece[1]
        if kind == "P":
            yield from _pawn_moves(state, row, col, color)
        elif kind == "N":
            yield from _knight_moves(state, row, col, color)
        elif kind == "B":
            yield from _sliding_moves(state, row, col, color, BISHOP_DIRECTIONS, "B")
        elif kind == "R":
            yield from _sliding_moves(state, row, col, color, ROOK_DIRECTIONS, "R")
        elif kind == "Q":
            yield from _sliding_moves(
                state, row, col, color, BISHOP_DIRECTIONS + ROOK_DIRECTIONS, "Q"
            )
        elif kind == "K":
            yield from _king_moves(state, row, col, color)


def is_in_check(state: BoardState, color: str | None = None) -> bool:
    if color is None:
        color = state.side_to_move()
    king_row, king_col = state.king_position(color)
    return is_square_attacked(state, king_row, king_col, enemy_color(color))


def is_checkmate(state: BoardState) -> bool:
    return is_in_check(state) and not generate_legal_moves(state)


def is_stalemate(state: BoardState) -> bool:
    return not is_in_check(state) and not generate_legal_moves(state)


def is_square_attacked(state: BoardState, row: int, col: int, by_color: str) -> bool:
    """Return True if ``(row, col)`` is attacked by any piece of ``by_color``."""
    # Pawn attacks. If by_color is white, white pawns attack "upward"
    # (toward lower rows), so a white pawn attacking (row, col) sits at
    # (row + 1, col +/- 1).
    pawn_row_offset = 1 if by_color == "w" else -1
    for dc in (-1, 1):
        ar, ac = row + pawn_row_offset, col + dc
        if 0 <= ar < 8 and 0 <= ac < 8:
            if state.board[ar][ac] == f"{by_color}P":
                return True

    # Knight attacks
    for dr, dc in KNIGHT_OFFSETS:
        ar, ac = row + dr, col + dc
        if 0 <= ar < 8 and 0 <= ac < 8:
            if state.board[ar][ac] == f"{by_color}N":
                return True

    # Diagonal sliding attacks (bishop, queen)
    for dr, dc in BISHOP_DIRECTIONS:
        ar, ac = row + dr, col + dc
        while 0 <= ar < 8 and 0 <= ac < 8:
            target = state.board[ar][ac]
            if target != EMPTY:
                if target[0] == by_color and target[1] in ("B", "Q"):
                    return True
                break
            ar += dr
            ac += dc

    # Orthogonal sliding attacks (rook, queen)
    for dr, dc in ROOK_DIRECTIONS:
        ar, ac = row + dr, col + dc
        while 0 <= ar < 8 and 0 <= ac < 8:
            target = state.board[ar][ac]
            if target != EMPTY:
                if target[0] == by_color and target[1] in ("R", "Q"):
                    return True
                break
            ar += dr
            ac += dc

    # Adjacent king
    for dr, dc in KING_OFFSETS:
        ar, ac = row + dr, col + dc
        if 0 <= ar < 8 and 0 <= ac < 8:
            if state.board[ar][ac] == f"{by_color}K":
                return True

    return False


# ---------------------------------------------------------------------------
# Per-piece move generators
# ---------------------------------------------------------------------------


def _pawn_moves(state: BoardState, row: int, col: int, color: str) -> Iterator[Move]:
    direction = -1 if color == "w" else 1
    start_row = 6 if color == "w" else 1
    promotion_row = 0 if color == "w" else 7
    piece = f"{color}P"
    enemy = enemy_color(color)

    one_forward = row + direction
    if 0 <= one_forward < 8 and state.board[one_forward][col] == EMPTY:
        if one_forward == promotion_row:
            for promo in sorted(PROMOTION_PIECES):
                yield Move(row, col, one_forward, col, piece, promotion_piece=promo)
        else:
            yield Move(row, col, one_forward, col, piece)
            if row == start_row:
                two_forward = row + 2 * direction
                if state.board[two_forward][col] == EMPTY:
                    yield Move(row, col, two_forward, col, piece)

    for dc in (-1, 1):
        target_col = col + dc
        target_row = row + direction
        if not (0 <= target_col < 8 and 0 <= target_row < 8):
            continue
        target_piece = state.board[target_row][target_col]
        if target_piece != EMPTY and target_piece[0] != color:
            if target_row == promotion_row:
                for promo in sorted(PROMOTION_PIECES):
                    yield Move(
                        row, col, target_row, target_col, piece,
                        piece_captured=target_piece, promotion_piece=promo,
                    )
            else:
                yield Move(
                    row, col, target_row, target_col, piece,
                    piece_captured=target_piece,
                )
        if state.en_passant_target == (target_row, target_col):
            yield Move(
                row, col, target_row, target_col, piece,
                piece_captured=f"{enemy}P", is_en_passant=True,
            )


def _knight_moves(state: BoardState, row: int, col: int, color: str) -> Iterator[Move]:
    piece = f"{color}N"
    for dr, dc in KNIGHT_OFFSETS:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        target = state.board[nr][nc]
        if target == EMPTY:
            yield Move(row, col, nr, nc, piece)
        elif target[0] != color:
            yield Move(row, col, nr, nc, piece, piece_captured=target)


def _sliding_moves(
    state: BoardState,
    row: int,
    col: int,
    color: str,
    directions: list[tuple[int, int]],
    piece_kind: str,
) -> Iterator[Move]:
    piece = f"{color}{piece_kind}"
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            target = state.board[nr][nc]
            if target == EMPTY:
                yield Move(row, col, nr, nc, piece)
            elif target[0] != color:
                yield Move(row, col, nr, nc, piece, piece_captured=target)
                break
            else:
                break
            nr += dr
            nc += dc


def _king_moves(state: BoardState, row: int, col: int, color: str) -> Iterator[Move]:
    piece = f"{color}K"
    for dr, dc in KING_OFFSETS:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        target = state.board[nr][nc]
        if target == EMPTY:
            yield Move(row, col, nr, nc, piece)
        elif target[0] != color:
            yield Move(row, col, nr, nc, piece, piece_captured=target)
    yield from _castling_moves(state, row, col, color)


def _castling_moves(state: BoardState, row: int, col: int, color: str) -> Iterator[Move]:
    piece = f"{color}K"
    enemy = enemy_color(color)
    rights = state.castling_rights

    # King must be on its original square to castle
    if color == "w":
        if (row, col) != (7, 4):
            return
        kingside = rights.white_kingside
        queenside = rights.white_queenside
        rook_kingside_square = (7, 7)
        rook_queenside_square = (7, 0)
    else:
        if (row, col) != (0, 4):
            return
        kingside = rights.black_kingside
        queenside = rights.black_queenside
        rook_kingside_square = (0, 7)
        rook_queenside_square = (0, 0)

    if is_square_attacked(state, row, col, enemy):
        return

    if kingside:
        rook_row, rook_col = rook_kingside_square
        if state.board[rook_row][rook_col] == f"{color}R":
            if state.board[row][5] == EMPTY and state.board[row][6] == EMPTY:
                if (
                    not is_square_attacked(state, row, 5, enemy)
                    and not is_square_attacked(state, row, 6, enemy)
                ):
                    yield Move(row, col, row, 6, piece, is_castling=True)

    if queenside:
        rook_row, rook_col = rook_queenside_square
        if state.board[rook_row][rook_col] == f"{color}R":
            if (
                state.board[row][1] == EMPTY
                and state.board[row][2] == EMPTY
                and state.board[row][3] == EMPTY
            ):
                if (
                    not is_square_attacked(state, row, 3, enemy)
                    and not is_square_attacked(state, row, 2, enemy)
                ):
                    yield Move(row, col, row, 2, piece, is_castling=True)


__all__ = [
    "generate_legal_moves",
    "generate_pseudo_legal_moves",
    "is_in_check",
    "is_checkmate",
    "is_stalemate",
    "is_square_attacked",
    "enemy_color",
]