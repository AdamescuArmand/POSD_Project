from __future__ import annotations

from core.board import BoardState, EMPTY
from ai.evaluation import CHECKMATE, STALEMATE, boardScore, materialScore
from core.move import Move


def clear_board(state: BoardState) -> BoardState:
    for r in range(8):
        for c in range(8):
            state.set_piece(r, c, EMPTY)
    state.white_to_move = True
    state.en_passant_target = None
    state.halfmove_clock = 0
    state.fullmove_number = 1
    state.move_history.clear()
    state.captured_pieces.clear()
    return state


def base_kings_only_state() -> BoardState:
    state = clear_board(BoardState.initial())
    state.set_piece(7, 4, "wK")
    state.set_piece(0, 4, "bK")
    return state


def test_material_score_starting_position_is_equal() -> None:
    state = BoardState.initial()
    assert materialScore(state.board) == 0


def test_material_score_white_up_a_queen_is_positive() -> None:
    state = base_kings_only_state()
    state.set_piece(3, 3, "wQ")
    assert materialScore(state.board) == 9


def test_material_score_black_up_a_rook_is_negative() -> None:
    state = base_kings_only_state()
    state.set_piece(3, 3, "bR")
    assert materialScore(state.board) == -5


def test_board_score_starting_position_is_near_equal() -> None:
    state = BoardState.initial()
    assert abs(boardScore(state)) < 1e-9


def test_board_score_rewards_extra_material() -> None:
    state = base_kings_only_state()
    state.set_piece(4, 4, "wQ")
    assert boardScore(state) > 8.0


def test_board_score_penalizes_black_material_advantage() -> None:
    state = base_kings_only_state()
    state.set_piece(4, 4, "bQ")
    assert boardScore(state) < -8.0


def test_board_score_prefers_better_knight_square() -> None:
    center_state = base_kings_only_state()
    rim_state = base_kings_only_state()
    center_state.set_piece(4, 4, "wN")
    rim_state.set_piece(7, 0, "wN")
    assert boardScore(center_state) > boardScore(rim_state)


def test_board_score_prefers_advanced_white_pawn() -> None:
    advanced = base_kings_only_state()
    starting = base_kings_only_state()
    advanced.set_piece(3, 3, "wP")
    starting.set_piece(6, 3, "wP")
    assert boardScore(advanced) > boardScore(starting)


def test_board_score_prefers_advanced_black_pawn_for_black() -> None:
    advanced = base_kings_only_state()
    starting = base_kings_only_state()
    advanced.set_piece(4, 3, "bP")
    starting.set_piece(1, 3, "bP")
    assert boardScore(advanced) < boardScore(starting)


def test_board_score_detects_checkmate_against_side_to_move() -> None:
    state = base_kings_only_state()
    state.set_piece(0, 0, "bK")
    state.set_piece(1, 1, "wQ")
    state.set_piece(2, 2, "wK")
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.white_to_move = False
    assert boardScore(state) == CHECKMATE


def test_board_score_detects_checkmate_for_black_win() -> None:
    state = base_kings_only_state()
    state.set_piece(7, 0, "wK")
    state.set_piece(6, 1, "bQ")
    state.set_piece(5, 2, "bK")
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.white_to_move = True
    assert boardScore(state) == -CHECKMATE


def test_board_score_detects_stalemate() -> None:
    state = base_kings_only_state()
    state.set_piece(0, 0, "bK")
    state.set_piece(1, 2, "wQ")
    state.set_piece(2, 1, "wK")
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.white_to_move = False
    assert boardScore(state) == STALEMATE


def test_board_score_changes_after_capture() -> None:
    state = base_kings_only_state()
    state.set_piece(4, 4, "wQ")
    state.set_piece(4, 6, "bR")
    before = boardScore(state)
    move = Move(4, 4, 4, 6, "wQ", piece_captured="bR")
    state.apply_move(move)
    after = boardScore(state)
    assert after > before