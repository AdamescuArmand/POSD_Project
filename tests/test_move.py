from core.move import Move, algebraic_to_square, square_to_algebraic


def test_square_to_algebraic_and_back_round_trip():
    assert square_to_algebraic(6, 4) == "e2"
    assert algebraic_to_square("e2") == (6, 4)
    assert algebraic_to_square(square_to_algebraic(0, 0)) == (0, 0)


def test_move_uci_without_promotion():
    move = Move(6, 4, 4, 4, "wP")
    assert move.uci() == "e2e4"
    assert str(move) == "e2e4"


def test_move_uci_with_promotion():
    move = Move(1, 0, 0, 0, "wP", promotion_piece="Q")
    assert move.is_promotion is True
    assert move.uci() == "a7a8q"


def test_move_capture_flag_for_normal_capture():
    move = Move(6, 4, 5, 5, "wP", piece_captured="bN")
    assert move.is_capture is True


def test_move_capture_flag_for_en_passant():
    move = Move(3, 4, 2, 5, "wP", is_en_passant=True)
    assert move.is_capture is True


def test_move_matches_start_and_end():
    move = Move(7, 6, 5, 5, "wN")
    assert move.matches((7, 6), (5, 5)) is True
    assert move.matches((7, 6), (5, 4)) is False


def test_move_with_promotion_returns_new_move():
    move = Move(1, 7, 0, 7, "wP")
    promoted = move.with_promotion("N")
    assert move.promotion_piece is None
    assert promoted.promotion_piece == "N"
    assert promoted.uci() == "h7h8n"


def test_invalid_square_coordinates_raise_value_error():
    try:
        Move(8, 0, 0, 0, "wP")
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_invalid_piece_code_raises_value_error():
    try:
        Move(6, 4, 4, 4, "pawn")
        assert False, "Expected ValueError"
    except ValueError:
        assert True
