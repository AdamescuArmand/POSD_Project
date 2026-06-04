from __future__ import annotations

from core.game import Game
from core.move import Move
from ui.pygame_ui import find_legal_move, flip_coords, format_move_log_lines


def test_flip_coords_mirrors_around_center():
    assert flip_coords(0, 0) == (7, 7)
    assert flip_coords(7, 7) == (0, 0)
    assert flip_coords(3, 4) == (4, 3)


def test_flip_coords_is_its_own_inverse():
    for row in range(8):
        for col in range(8):
            r, c = flip_coords(row, col)
            assert flip_coords(r, c) == (row, col)


def test_format_move_log_pairs_moves_by_full_turn():
    moves = [
        Move(6, 4, 4, 4, "wP"),
        Move(1, 4, 3, 4, "bP"),
        Move(7, 6, 5, 5, "wN"),
    ]
    lines = format_move_log_lines(moves)
    assert lines == ["1.  e2e4   e7e5", "2.  g1f3"]


def test_format_move_log_handles_empty_history():
    assert format_move_log_lines([]) == []


def test_find_legal_move_returns_matching_move():
    game = Game.new()
    move = find_legal_move(game, start=(6, 4), end=(4, 4))
    assert move is not None
    assert move.start == (6, 4)
    assert move.end == (4, 4)


def test_find_legal_move_returns_none_for_illegal_move():
    game = Game.new()
    # Pawn cannot jump three squares.
    assert find_legal_move(game, start=(6, 4), end=(3, 4)) is None


def test_find_legal_move_picks_requested_promotion_piece():
    # Set up a position where a white pawn is one move from promotion.
    game = Game.new()
    # Manually place the pawn — easier than playing a long opening.
    game.state.clear_square(6, 0)
    game.state.set_piece(1, 0, "wP")
    # Make sure there is nothing on the promotion square or its diagonals
    # so the pawn has a single straight-line promotion path.
    game.state.clear_square(0, 0)
    move = find_legal_move(game, start=(1, 0), end=(0, 0), promotion_piece="N")
    assert move is not None
    assert move.promotion_piece == "N"
