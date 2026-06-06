from core.board import BoardState, CastlingRights, EMPTY
from core.game import Game, GameResult, GameStatus
from core.move import Move


def test_new_game_has_twenty_legal_moves():
    game = Game.new()
    assert len(game.legal_moves()) == 20


def test_new_game_status_is_ongoing():
    game = Game.new()
    assert game.status() == GameStatus.ONGOING
    assert game.result() is None
    assert game.is_over() is False


def test_make_move_advances_state():
    game = Game.new()
    move = Move(6, 4, 4, 4, "wP")
    game.make_move(move)
    assert game.state.white_to_move is False
    assert game.state.piece_at(4, 4) == "wP"


def test_illegal_move_raises_value_error():
    game = Game.new()
    illegal = Move(6, 4, 3, 4, "wP")  # pawn jumping 3 squares
    try:
        game.make_move(illegal)
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_undo_move_restores_previous_state():
    game = Game.new()
    initial_fen = game.fen()
    game.make_move(Move(6, 4, 4, 4, "wP"))
    game.undo_move()
    assert game.fen() == initial_fen


def test_checkmate_result_is_winning_side():
    # Set up scholars-mate position
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        white_to_move=False,
        white_king_pos=(7, 4),
        black_king_pos=(0, 4),
        castling_rights=CastlingRights(False, False, False, False),
    )
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
    state.set_piece(1, 5, "wQ")
    state.set_piece(4, 2, "wB")
    state.set_piece(7, 4, "wK")
    game = Game(state=state)
    assert game.is_checkmate() is True
    assert game.status() == GameStatus.CHECKMATE
    assert game.result() == GameResult.WHITE_WINS
    assert game.is_over() is True


def test_insufficient_material_king_versus_king():
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        castling_rights=CastlingRights(False, False, False, False),
    )
    state.set_piece(7, 4, "wK")
    state.set_piece(0, 4, "bK")
    game = Game(state=state)
    assert game.is_insufficient_material() is True
    assert game.status() == GameStatus.DRAW_INSUFFICIENT_MATERIAL
    assert game.result() == GameResult.DRAW


def test_insufficient_material_king_and_bishop_versus_king():
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        castling_rights=CastlingRights(False, False, False, False),
    )
    state.set_piece(7, 4, "wK")
    state.set_piece(7, 3, "wB")
    state.set_piece(0, 4, "bK")
    game = Game(state=state)
    assert game.is_insufficient_material() is True


def test_sufficient_material_with_pawn():
    state = BoardState(
        board=[[EMPTY for _ in range(8)] for _ in range(8)],
        castling_rights=CastlingRights(False, False, False, False),
    )
    state.set_piece(7, 4, "wK")
    state.set_piece(6, 4, "wP")
    state.set_piece(0, 4, "bK")
    game = Game(state=state)
    assert game.is_insufficient_material() is False


def test_fifty_move_rule_triggered():
    game = Game.new()
    game.state.halfmove_clock = 100
    assert game.is_fifty_move_rule() is True
    assert game.status() == GameStatus.DRAW_FIFTY_MOVES