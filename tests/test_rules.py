from core.board import BoardState, CastlingRights, EMPTY
from core.move import Move
from core import rules


def _empty_board() -> BoardState:
    """Build a board with only kings on it for focused tests."""
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=True,
        white_king_pos=(7, 4),
        black_king_pos=(0, 4),
        castling_rights=CastlingRights(False, False, False, False),
    )
    state.set_piece(7, 4, "wK")
    state.set_piece(0, 4, "bK")
    return state


def test_initial_position_has_twenty_legal_moves():
    state = BoardState.initial()
    moves = rules.generate_legal_moves(state)
    assert len(moves) == 20


def test_initial_position_pawn_double_push_available():
    state = BoardState.initial()
    moves = rules.generate_legal_moves(state)
    pawn_starts = [m for m in moves if m.piece_moved == "wP" and m.start_row == 6]
    # Each of 8 pawns has 2 forward moves
    assert len(pawn_starts) == 16


def test_pawn_double_push_only_from_starting_rank():
    state = _empty_board()
    state.set_piece(5, 4, "wP")  # already moved once
    moves = list(rules.generate_pseudo_legal_moves(state))
    pawn_moves = [m for m in moves if m.piece_moved == "wP"]
    assert len(pawn_moves) == 1
    assert pawn_moves[0].end == (4, 4)


def test_knight_jumps_over_pieces():
    state = BoardState.initial()
    knight_moves = [
        m for m in rules.generate_legal_moves(state) if m.piece_moved == "wN"
    ]
    # Each knight has 2 squares it can reach (Na3/Nc3 and Nf3/Nh3)
    assert len(knight_moves) == 4


def test_bishop_blocked_by_own_pawns_in_starting_position():
    state = BoardState.initial()
    bishop_moves = [
        m for m in rules.generate_legal_moves(state) if m.piece_moved == "wB"
    ]
    assert bishop_moves == []


def test_promotion_generates_four_moves():
    state = _empty_board()
    state.set_piece(1, 0, "wP")
    moves = [m for m in rules.generate_legal_moves(state) if m.piece_moved == "wP"]
    promotions = [m for m in moves if m.is_promotion]
    assert len(promotions) == 4
    assert {m.promotion_piece for m in promotions} == {"Q", "R", "B", "N"}


def test_en_passant_available_after_double_push():
    state = _empty_board()
    state.set_piece(6, 4, "wP")
    state.set_piece(4, 5, "bP")
    # White double-pushes e2-e4 — this sets the en passant target.
    state.apply_move(Move(6, 4, 4, 4, "wP"))
    moves = list(rules.generate_pseudo_legal_moves(state))
    ep_moves = [m for m in moves if m.is_en_passant]
    assert len(ep_moves) == 1
    assert ep_moves[0].end == (5, 4)


def test_castling_kingside_available_when_clear():
    state = _empty_board()
    state.set_piece(7, 7, "wR")
    state.castling_rights = CastlingRights(
        white_kingside=True, white_queenside=False,
        black_kingside=False, black_queenside=False,
    )
    moves = list(rules.generate_pseudo_legal_moves(state))
    castles = [m for m in moves if m.is_castling]
    assert len(castles) == 1
    assert castles[0].end == (7, 6)


def test_castling_blocked_by_piece_between():
    state = _empty_board()
    state.set_piece(7, 7, "wR")
    state.set_piece(7, 5, "wN")  # blocks the path
    state.castling_rights = CastlingRights(
        white_kingside=True, white_queenside=False,
        black_kingside=False, black_queenside=False,
    )
    moves = list(rules.generate_pseudo_legal_moves(state))
    assert not any(m.is_castling for m in moves)


def test_castling_not_allowed_when_king_in_check():
    state = _empty_board()
    state.set_piece(7, 7, "wR")
    state.set_piece(3, 4, "bR")  # checks the white king
    state.castling_rights = CastlingRights(
        white_kingside=True, white_queenside=False,
        black_kingside=False, black_queenside=False,
    )
    moves = list(rules.generate_pseudo_legal_moves(state))
    assert not any(m.is_castling for m in moves)


def test_castling_not_allowed_through_attacked_square():
    state = _empty_board()
    state.set_piece(7, 7, "wR")
    state.set_piece(3, 5, "bR")  # attacks f1, which the king must cross
    state.castling_rights = CastlingRights(
        white_kingside=True, white_queenside=False,
        black_kingside=False, black_queenside=False,
    )
    moves = list(rules.generate_pseudo_legal_moves(state))
    assert not any(m.is_castling for m in moves)


def test_pinned_piece_cannot_move():
    state = _empty_board()
    state.set_piece(6, 4, "wN")  # pinned along the e-file
    state.set_piece(3, 4, "bR")
    moves = rules.generate_legal_moves(state)
    knight_moves = [m for m in moves if m.piece_moved == "wN"]
    assert knight_moves == []


def test_is_in_check_detects_attack():
    state = _empty_board()
    state.set_piece(7, 0, "bR")  # rook on a1 attacks king on e1
    assert rules.is_in_check(state, "w") is True


def test_scholars_mate_is_checkmate():
    # Build the position after 1.e4 e5 2.Bc4 Bc5 3.Qh5 Nf6?? 4.Qxf7#
    # We can construct it more directly to keep the test focused.
    state = _empty_board()
    state.set_piece(0, 4, "bK")
    state.set_piece(0, 3, "bQ")
    state.set_piece(0, 5, "bB")
    state.set_piece(0, 6, "bN")
    state.set_piece(0, 7, "bR")
    state.set_piece(0, 0, "bR")
    state.set_piece(0, 1, "bN")
    state.set_piece(0, 2, "bB")
    state.set_piece(1, 0, "bP")
    state.set_piece(1, 1, "bP")
    state.set_piece(1, 2, "bP")
    state.set_piece(1, 3, "bP")
    state.set_piece(2, 5, "bN")
    state.set_piece(3, 4, "bP")
    state.set_piece(1, 5, "wQ")  # Queen on f7 delivers mate
    state.set_piece(4, 2, "wB")  # Bishop on c4 defends the queen
    state.set_piece(7, 4, "wK")
    state.white_to_move = False  # black to move, and mated
    assert rules.is_in_check(state, "b") is True
    assert rules.is_checkmate(state) is True


def test_stalemate_position():
    # Classic stalemate: black king on a8, white queen on c7, white king on c6.
    state = _empty_board()
    # Clear the kings that _empty_board set up
    state.board[7][4] = EMPTY
    state.board[0][4] = EMPTY
    state.set_piece(0, 0, "bK")
    state.set_piece(1, 2, "wQ")
    state.set_piece(2, 2, "wK")
    state.white_to_move = False
    assert rules.is_in_check(state, "b") is False
    assert rules.is_stalemate(state) is True


def test_undo_after_legality_check_leaves_state_intact():
    state = BoardState.initial()
    original_fen = state.fen()
    rules.generate_legal_moves(state)
    assert state.fen() == original_fen


def test_castling_not_generated_when_king_not_on_start_square():
    """Even with castling rights set, the king must be on its original square."""
    state = _empty_board()
    state.clear_square(7, 4)  # remove the white king from e1
    state.clear_square(0, 4)  # remove the black king from e8
    state.set_piece(0, 0, "bK")  # place black king on a8 instead
    state.set_piece(0, 7, "bR")  # rook is on its starting square
    state.castling_rights = CastlingRights(
        white_kingside=False, white_queenside=False,
        black_kingside=True, black_queenside=False,
    )
    state.white_to_move = False
    moves = rules.generate_legal_moves(state)
    assert not any(m.is_castling for m in moves)
