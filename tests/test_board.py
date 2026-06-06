from core.board import BoardState, EMPTY
from core.move import Move


def test_initial_board_state_has_expected_defaults():
    board = BoardState.initial()
    assert board.white_to_move is True
    assert board.white_king_pos == (7, 4)
    assert board.black_king_pos == (0, 4)
    assert board.piece_at(7, 4) == "wK"
    assert board.piece_at(0, 4) == "bK"
    assert board.en_passant_target is None
    assert board.fullmove_number == 1


def test_copy_creates_independent_board_grid_and_state():
    board = BoardState.initial()
    copied = board.copy()
    copied.set_piece(4, 4, "wQ")
    assert board.piece_at(4, 4) == EMPTY
    assert copied.piece_at(4, 4) == "wQ"


def test_set_piece_updates_king_position():
    board = BoardState.initial()
    board.clear_square(7, 4)
    board.set_piece(6, 4, "wK")
    assert board.white_king_pos == (6, 4)


def test_apply_simple_pawn_move_updates_board_and_turn():
    board = BoardState.initial()
    move = Move(6, 4, 4, 4, "wP")
    board.apply_move(move)
    assert board.piece_at(6, 4) == EMPTY
    assert board.piece_at(4, 4) == "wP"
    assert board.white_to_move is False
    assert board.en_passant_target == (5, 4)
    assert board.move_history[-1] == move


def test_apply_capture_tracks_captured_piece_and_resets_halfmove_clock():
    board = BoardState.initial()
    board.set_piece(5, 5, "bN")
    move = Move(6, 4, 5, 5, "wP", piece_captured="bN")
    board.halfmove_clock = 9
    board.apply_move(move)
    assert board.piece_at(5, 5) == "wP"
    assert board.captured_pieces[-1] == "bN"
    assert board.halfmove_clock == 0


def test_apply_en_passant_removes_captured_pawn():
    board = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=True,
        white_king_pos=(7, 4),
        black_king_pos=(0, 4),
    )
    board.set_piece(7, 4, "wK")
    board.set_piece(0, 4, "bK")
    board.set_piece(3, 4, "wP")
    board.set_piece(3, 5, "bP")
    move = Move(3, 4, 2, 5, "wP", piece_captured="bP", is_en_passant=True)
    board.apply_move(move)
    assert board.piece_at(3, 5) == EMPTY
    assert board.piece_at(2, 5) == "wP"
    assert board.captured_pieces[-1] == "bP"


def test_apply_castling_moves_rook_too():
    board = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=True,
        white_king_pos=(7, 4),
        black_king_pos=(0, 4),
    )
    board.set_piece(7, 4, "wK")
    board.set_piece(7, 7, "wR")
    board.set_piece(0, 4, "bK")
    move = Move(7, 4, 7, 6, "wK", is_castling=True)
    board.apply_move(move)
    assert board.piece_at(7, 6) == "wK"
    assert board.piece_at(7, 5) == "wR"
    assert board.piece_at(7, 7) == EMPTY


def test_promotion_replaces_pawn_with_selected_piece():
    board = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=True,
        white_king_pos=(7, 4),
        black_king_pos=(0, 4),
    )
    board.set_piece(7, 4, "wK")
    board.set_piece(0, 4, "bK")
    board.set_piece(1, 0, "wP")
    move = Move(1, 0, 0, 0, "wP", promotion_piece="Q")
    board.apply_move(move)
    assert board.piece_at(0, 0) == "wQ"


def test_rook_move_updates_castling_rights():
    board = BoardState.initial()
    move = Move(7, 7, 5, 7, "wR")
    board.apply_move(move)
    assert board.castling_rights.white_kingside is False
    assert board.castling_rights.white_queenside is True


def test_fen_for_starting_position_is_correct():
    board = BoardState.initial()
    assert board.fen() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
