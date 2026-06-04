from __future__ import annotations

from ai.evaluation import board_score
from ai.search import (
    DEPTH,
    MATE_SCORE,
    find_best_move,
    find_best_move_one_ply,
    find_random_move,
    negamax_alpha_beta,
)
from core.board import BoardState, EMPTY
from core.move import Move
from core.rules import generate_legal_moves, is_checkmate


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


def move_uci(move: Move | None) -> str | None:
    return None if move is None else move.uci()


def mating_moves(state: BoardState) -> list[str]:
    """Return the UCI strings of every legal move that delivers mate."""
    mates: list[str] = []
    for move in generate_legal_moves(state):
        state.apply_move(move)
        if is_checkmate(state):
            mates.append(move.uci())
        state.undo_move()
    return mates


# ---------------------------------------------------------------------------
# find_random_move
# ---------------------------------------------------------------------------


def test_find_random_move_returns_none_for_empty_list():
    assert find_random_move([]) is None


def test_find_random_move_returns_member_of_valid_moves():
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    chosen = find_random_move(moves)
    assert chosen in moves


# ---------------------------------------------------------------------------
# find_best_move_one_ply
# ---------------------------------------------------------------------------


def test_find_best_move_one_ply_returns_legal_move_in_start_position():
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    best = find_best_move_one_ply(state, moves)
    assert best in moves


def test_find_best_move_one_ply_returns_none_when_no_moves():
    state = BoardState.initial()
    assert find_best_move_one_ply(state, []) is None


# ---------------------------------------------------------------------------
# find_best_move (full negamax search)
# ---------------------------------------------------------------------------


def test_find_best_move_returns_legal_move_in_start_position():
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    best = find_best_move(state, moves)
    assert best in moves


def test_find_best_move_returns_none_when_no_valid_moves_supplied():
    state = BoardState.initial()
    assert find_best_move(state, [], depth=DEPTH) is None


def test_find_best_move_does_not_mutate_state():
    state = BoardState.initial()
    original_fen = state.fen()
    original_history = list(state.move_history)
    moves = generate_legal_moves(state)
    _ = find_best_move(state, moves, depth=2)
    assert state.fen() == original_fen
    assert state.move_history == original_history


def test_find_best_move_improves_evaluation_at_depth_one():
    state = base_kings_only_state()
    state.set_piece(6, 3, "wQ")
    state.set_piece(5, 3, "bR")
    state.set_piece(4, 7, "wP")
    moves = generate_legal_moves(state)
    before = board_score(state)
    best = find_best_move(state, moves, depth=1)
    assert best is not None
    state.apply_move(best)
    after = board_score(state)
    assert after > before


def test_find_best_move_finds_mate_in_one_for_white():
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(2, 7, "wK")
    state.set_piece(1, 6, "wQ")
    state.set_piece(0, 7, "bK")
    state.white_to_move = True

    mates = mating_moves(state)
    assert mates, "Test position is not actually mate in one"

    moves = generate_legal_moves(state)
    best = find_best_move(state, moves, depth=2)
    assert best is not None
    assert move_uci(best) in mates


def test_find_best_move_finds_mate_in_one_for_black():
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(5, 7, "bK")
    state.set_piece(6, 6, "bQ")
    state.set_piece(7, 7, "wK")
    state.white_to_move = False

    mates = mating_moves(state)
    assert mates, "Test position is not actually mate in one"

    moves = generate_legal_moves(state)
    best = find_best_move(state, moves, depth=2)
    assert best is not None
    assert move_uci(best) in mates


def test_find_best_move_finds_mate_with_rook_and_queen_for_white():
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(2, 6, "wK")
    state.set_piece(7, 7, "wR")
    state.set_piece(1, 7, "wQ")
    state.set_piece(0, 6, "bK")
    state.white_to_move = True

    moves = generate_legal_moves(state)
    best = find_best_move(state, moves, depth=2)
    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)


def test_find_best_move_finds_mate_with_king_and_rook_for_black():
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(7, 7, "wK")
    state.set_piece(6, 5, "bK")
    state.set_piece(4, 7, "bR")
    state.white_to_move = False

    moves = generate_legal_moves(state)
    best = find_best_move(state, moves, depth=2)
    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)


# ---------------------------------------------------------------------------
# negamax_alpha_beta (the recursive scoring function)
# ---------------------------------------------------------------------------


def test_negamax_alpha_beta_returns_numeric_score():
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    score = negamax_alpha_beta(
        state, moves, depth=1, alpha=-MATE_SCORE, beta=MATE_SCORE, turn_multiplier=1
    )
    assert isinstance(score, (int, float))


def test_negamax_returns_zero_for_stalemate_position():
    """Stalemate: side to move has no legal moves and isn't in check."""
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(0, 0, "bK")
    state.set_piece(2, 1, "wQ")
    state.set_piece(2, 2, "wK")
    state.white_to_move = False

    moves = generate_legal_moves(state)
    score = negamax_alpha_beta(
        state, moves, depth=3, alpha=-MATE_SCORE, beta=MATE_SCORE, turn_multiplier=-1
    )
    assert score == 0
