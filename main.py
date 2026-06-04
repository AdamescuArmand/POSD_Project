"""Entry point for the chess game."""
from __future__ import annotations

from typing import Optional

import config
from ai.search import find_best_move
from core.game import Game
from core.move import Move
from ui.pygame_ui import PygameUI


def ai_move_function(game: Game) -> Optional[Move]:
    """Adapter from search.find_best_move to the UI's (game) -> move signature."""
    return find_best_move(game.state, game.legal_moves())


def main() -> None:
    game = Game.new()
    ui = PygameUI(
        game=game,
        ai_move=ai_move_function,
        human_plays_white=config.HUMAN_PLAYS_WHITE,
    )
    ui.run()


if __name__ == "__main__":
    main()