from __future__ import annotations

from core.board import BoardState, EMPTY
from core.move import Move
from core.rules import generate_legal_moves, is_checkmate
from ai.search import (
    DEPTH,
    findBestMove,
    findBestMoveMinMax,
    findMoveNegaMaxAlphaBetaPruning,
    findRandomMove,
)
from ai.evaluation import CHECKMATE, boardScore


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


def test_find_random_move_returns_none_for_empty_list() -> None:
    assert findRandomMove([]) is None


def test_find_random_move_returns_member_of_valid_moves() -> None:
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    chosen = findRandomMove(moves)
    assert chosen in moves


def test_find_best_move_minmax_returns_legal_move_in_start_position() -> None:
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves)
    assert best in moves


def test_find_best_move_returns_legal_move_in_start_position() -> None:
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    best = findBestMove(state, moves)
    assert best in moves


def test_search_prefers_capturing_higher_value_piece() -> None:
    state = base_kings_only_state()
    state.set_piece(6, 3, "wQ")
    state.set_piece(5, 3, "bR")
    state.set_piece(5, 4, "bP")
    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves, depth=1)
    assert move_uci(best) == "d2d3"


def test_search_finds_winning_move_for_white_endgame() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(2, 2, "wK")
    state.set_piece(1, 1, "wQ")
    state.set_piece(0, 0, "bK")
    state.white_to_move = True

    moves = generate_legal_moves(state)
    before = boardScore(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    assert best in moves

    state.apply_move(best)
    after = boardScore(state)
    assert after >= before


def test_search_finds_winning_move_for_black_endgame() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)
    state.set_piece(5, 2, "bK")
    state.set_piece(6, 1, "bQ")
    state.set_piece(7, 0, "wK")
    state.white_to_move = False

    moves = generate_legal_moves(state)
    before = boardScore(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    assert best in moves

    state.apply_move(best)
    after = boardScore(state)
    assert after <= before


def test_search_does_not_mutate_state_after_search() -> None:
    state = BoardState.initial()
    original_fen = state.fen()
    original_history = list(state.move_history)
    moves = generate_legal_moves(state)
    _ = findBestMoveMinMax(state, moves, depth=2)
    assert state.fen() == original_fen
    assert state.move_history == original_history


def test_alpha_beta_returns_numeric_score() -> None:
    state = BoardState.initial()
    moves = generate_legal_moves(state)
    score = findMoveNegaMaxAlphaBetaPruning(
        state,
        moves,
        depth=1,
        alpha=-CHECKMATE,
        beta=CHECKMATE,
        turnMultiplier=1,
        rootDepth=1,
    )
    assert isinstance(score, (int, float))


def test_search_returns_none_when_no_valid_moves_supplied() -> None:
    state = BoardState.initial()
    assert findBestMoveMinMax(state, [], depth=DEPTH) is None


def test_search_chooses_move_that_improves_evaluation_at_depth_one() -> None:
    state = base_kings_only_state()
    state.set_piece(6, 3, "wQ")
    state.set_piece(5, 3, "bR")
    state.set_piece(4, 7, "wP")
    moves = generate_legal_moves(state)
    before = boardScore(state)
    best = findBestMoveMinMax(state, moves, depth=1)
    assert best is not None
    state.apply_move(best)
    after = boardScore(state)
    assert after > before

def mating_moves(state) -> list[str]:
    mates = []
    for move in generate_legal_moves(state):
        state.apply_move(move)
        if is_checkmate(state):
            mates.append(move_uci(move))
        state.undo_move()
    return mates

def test_search_picks_a_mate_in_one_for_white() -> None:
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
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    assert move_uci(best) in mates

def test_search_picks_a_mate_in_one_for_black() -> None:
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
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    assert move_uci(best) in mates

def test_simple_and_minmax_search_both_return_legal_moves() -> None:
    state = base_kings_only_state()
    state.set_piece(6, 3, "wQ")
    state.set_piece(5, 3, "bR")
    moves = generate_legal_moves(state)
    simple_best = findBestMove(state, moves)
    minmax_best = findBestMoveMinMax(state, moves, depth=1)
    assert simple_best in moves
    assert minmax_best in moves

def test_search_black_mate_in_one_king_and_rook() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)

    state.set_piece(7, 7, "wK")  
    state.set_piece(6, 5, "bK")  
    state.set_piece(4, 7, "bR")  

    state.white_to_move = False

    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)

def test_search_finds_mate_in_one_for_white_simple() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)

    state.set_piece(2, 7, "wK")  
    state.set_piece(1, 6, "wQ")  
    state.set_piece(0, 7, "bK")  
    state.white_to_move = True

    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)

def test_search_white_mate_in_one_with_rook_and_queen() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)

    state.set_piece(2, 6, "wK")  
    state.set_piece(7, 7, "wR")  
    state.set_piece(1, 7, "wQ")  
    state.set_piece(0, 6, "bK")  
    state.white_to_move = True

    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)

def test_search_finds_mate_in_one_for_black_simple() -> None:
    state = base_kings_only_state()
    state.clear_square(7, 4)
    state.clear_square(0, 4)

    state.set_piece(5, 7, "bK")  # h3
    state.set_piece(6, 6, "bQ")  # g2
    state.set_piece(7, 7, "wK")  # h1
    state.white_to_move = False

    moves = generate_legal_moves(state)
    best = findBestMoveMinMax(state, moves, depth=2)

    assert best is not None
    state.apply_move(best)
    assert is_checkmate(state)