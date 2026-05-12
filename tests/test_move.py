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