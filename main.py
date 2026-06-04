"""Entry point for the chess game.

Wires together :class:`Game`, the AI move function, and the pygame UI.
"""
from __future__ import annotations

import config
from ai.random_player import random_move
from core.game import Game
from ui.pygame_ui import PygameUI


def main() -> None:
    game = Game.new()
    ui = PygameUI(
        game=game,
        ai_move=random_move,
        human_plays_white=config.HUMAN_PLAYS_WHITE,
    )
    ui.run()


if __name__ == "__main__":
    main()
