"""Pygame-based chess UI.

The :class:`PygameUI` class is the main entry point. It owns:

* the game state (a :class:`Game` instance),
* an AI move-picking function,
* its own ephemeral UI state (selected square, click history, etc.),
* loaded piece images and fonts.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

import pygame

import config
from core.game import Game, GameResult, GameStatus
from core.move import Move


# Type alias for any function that picks a move for the AI side.
AIMoveFunction = Callable[[Game], Optional[Move]]


def flip_coords(row: int, col: int) -> tuple[int, int]:
    """Mirror ``(row, col)`` for black-perspective rendering."""
    return 7 - row, 7 - col


def format_move_log_lines(moves: list[Move]) -> list[str]:
    """Format ``moves`` into displayable lines like ``"1.  e2e4   e7e5"``."""
    lines: list[str] = []
    for i in range(0, len(moves), 2):
        text = f"{i // 2 + 1}.  {moves[i].uci()}"
        if i + 1 < len(moves):
            text += f"   {moves[i + 1].uci()}"
        lines.append(text)
    return lines


def find_legal_move(
    game: Game,
    start: tuple[int, int],
    end: tuple[int, int],
    promotion_piece: str = "Q",
) -> Optional[Move]:
    """Return the legal move from ``start`` to ``end`` or ``None``.

    When the move would be a promotion, the move promoting to
    ``promotion_piece`` is returned.
    """
    for move in game.legal_moves():
        if move.start != start or move.end != end:
            continue
        if move.is_promotion and move.promotion_piece != promotion_piece:
            continue
        return move
    return None


@dataclass
class UIState:
    """Ephemeral UI state that doesn't belong to :class:`Game`."""

    selected_square: Optional[tuple[int, int]] = None
    player_clicks: list[tuple[int, int]] = field(default_factory=list)
    animate_next: bool = False
    game_over: bool = False

    def reset_selection(self) -> None:
        self.selected_square = None
        self.player_clicks = []


class PygameUI:
    """Pygame chess UI driven by a :class:`Game` and an AI move function."""

    def __init__(
        self,
        game: Game,
        ai_move: AIMoveFunction,
        human_plays_white: bool = True,
    ):
        self.game = game
        self.ai_move = ai_move
        self.human_plays_white = human_plays_white
        self.ui_state = UIState()

        pygame.init()
        self.sq_size = config.BOARD_SIZE // config.DIMENSION
        screen_width = config.BOARD_SIZE + config.MOVE_LOG_PANEL_WIDTH
        screen_height = config.BOARD_SIZE
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.move_log_font = pygame.font.SysFont(
            config.MOVE_LOG_FONT_NAME, config.MOVE_LOG_FONT_SIZE
        )
        self.end_game_font = pygame.font.SysFont(
            config.END_GAME_FONT_NAME, config.END_GAME_FONT_SIZE, bold=True
        )
        self.images = self._load_images()
        self.board_colors = (config.BOARD_COLOR_LIGHT, config.BOARD_COLOR_DARK)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_images(self) -> dict[str, pygame.Surface]:
        pieces = ["bP", "bR", "bN", "bB", "bQ", "bK",
                  "wP", "wR", "wN", "wB", "wQ", "wK"]
        images: dict[str, pygame.Surface] = {}
        for piece in pieces:
            path = os.path.join(config.IMAGE_FOLDER, f"{piece}.png")
            image = pygame.image.load(path)
            images[piece] = pygame.transform.scale(image, (self.sq_size, self.sq_size))
        return images

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the event loop. Returns when the user closes the window."""
        running = True
        while running:
            human_turn = self._is_human_turn()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if human_turn and not self.ui_state.game_over:
                        self._handle_mouse_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    self._handle_key_press(event.key)

            if not human_turn and not self.ui_state.game_over:
                self._take_ai_turn()

            self._update_game_over()
            self._draw()
            self.clock.tick(config.MAX_FPS)
            pygame.display.flip()

        pygame.quit()

    def _is_human_turn(self) -> bool:
        if self.human_plays_white:
            return self.game.state.white_to_move
        return not self.game.state.white_to_move

    def _update_game_over(self) -> None:
        if self.game.is_over():
            self.ui_state.game_over = True

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _handle_mouse_click(self, mouse_pos: tuple[int, int]) -> None:
        pixel_x, pixel_y = mouse_pos
        col = pixel_x // self.sq_size
        row = pixel_y // self.sq_size

        # Clicks on the move log panel are ignored.
        if col < 0 or col >= config.DIMENSION:
            return

        # Convert from screen perspective to logical board coordinates.
        if not self.human_plays_white:
            row, col = flip_coords(row, col)

        # Clicking the same square twice deselects.
        if self.ui_state.selected_square == (row, col):
            self.ui_state.reset_selection()
            return

        self.ui_state.selected_square = (row, col)
        self.ui_state.player_clicks.append((row, col))

        if len(self.ui_state.player_clicks) == 2:
            self._try_apply_player_move()

    def _try_apply_player_move(self) -> None:
        start, end = self.ui_state.player_clicks
        move = find_legal_move(self.game, start, end)
        if move is None:
            # Treat the second click as the start of a new selection.
            self.ui_state.player_clicks = [self.ui_state.selected_square]
            return
        self.game.make_move(move)
        self.ui_state.animate_next = True
        self.ui_state.reset_selection()

    def _handle_key_press(self, key: int) -> None:
        if key == pygame.K_z:
            self._undo_one_full_turn()
        elif key == pygame.K_r:
            self.game = Game.new()
            self.ui_state = UIState()

    def _undo_one_full_turn(self) -> None:
        """Undo both the AI's move and the human's move so the human moves again."""
        for _ in range(2):
            try:
                self.game.undo_move()
            except ValueError:
                break
        self.ui_state.game_over = False
        self.ui_state.reset_selection()

    # ------------------------------------------------------------------
    # AI turn
    # ------------------------------------------------------------------

    def _take_ai_turn(self) -> None:
        move = self.ai_move(self.game)
        if move is None:
            return
        self.game.make_move(move)
        self.ui_state.animate_next = True

    # ------------------------------------------------------------------
    # Coordinate translation
    # ------------------------------------------------------------------

    def _to_screen(self, row: int, col: int) -> tuple[int, int]:
        """Translate board coords to screen coords (flipping if needed)."""
        if not self.human_plays_white:
            return flip_coords(row, col)
        return row, col

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        if self.ui_state.animate_next and self.game.state.move_history:
            self._animate_move(self.game.state.move_history[-1])
            self.ui_state.animate_next = False

        self._draw_board()
        self._draw_selection_highlights()
        self._draw_last_move_highlight()
        self._draw_check_highlight()
        self._draw_pieces()
        self._draw_move_log()
        if self.ui_state.game_over:
            self._draw_end_game_text()

    def _draw_board(self) -> None:
        for r in range(config.DIMENSION):
            for c in range(config.DIMENSION):
                color = self.board_colors[(r + c) % 2]
                rect = pygame.Rect(
                    c * self.sq_size,
                    r * self.sq_size,
                    self.sq_size,
                    self.sq_size,
                )
                pygame.draw.rect(self.screen, color, rect)

    def _draw_selection_highlights(self) -> None:
        selected = self.ui_state.selected_square
        if selected is None:
            return
        row, col = selected
        piece = self.game.state.piece_at(row, col)
        ally = "w" if self.game.state.white_to_move else "b"
        if piece == "--" or piece[0] != ally:
            return

        # Highlight the picked-up piece's square.
        screen_row, screen_col = self._to_screen(row, col)
        surface = pygame.Surface((self.sq_size, self.sq_size))
        surface.set_alpha(100)
        surface.fill(config.HIGHLIGHT_SELECTED)
        self.screen.blit(surface, (screen_col * self.sq_size, screen_row * self.sq_size))

        # Highlight legal destination squares for that piece.
        surface.fill(config.HIGHLIGHT_MOVE)
        for move in self.game.legal_moves():
            if move.start_row == row and move.start_col == col:
                end_r, end_c = self._to_screen(move.end_row, move.end_col)
                self.screen.blit(surface, (end_c * self.sq_size, end_r * self.sq_size))

    def _draw_last_move_highlight(self) -> None:
        if not self.game.state.move_history:
            return
        last = self.game.state.move_history[-1]
        surface = pygame.Surface((self.sq_size, self.sq_size))
        surface.set_alpha(100)
        surface.fill(config.HIGHLIGHT_LAST_MOVE)
        for row, col in (last.start, last.end):
            screen_row, screen_col = self._to_screen(row, col)
            self.screen.blit(surface, (screen_col * self.sq_size, screen_row * self.sq_size))

    def _draw_check_highlight(self) -> None:
        if not self.game.is_check():
            return
        color = "w" if self.game.state.white_to_move else "b"
        king_row, king_col = self.game.state.king_position(color)
        screen_row, screen_col = self._to_screen(king_row, king_col)
        surface = pygame.Surface((self.sq_size, self.sq_size))
        surface.set_alpha(100)
        surface.fill(config.HIGHLIGHT_CHECK)
        self.screen.blit(surface, (screen_col * self.sq_size, screen_row * self.sq_size))

    def _draw_pieces(self) -> None:
        for r in range(config.DIMENSION):
            for c in range(config.DIMENSION):
                board_row, board_col = (r, c) if self.human_plays_white else flip_coords(r, c)
                piece = self.game.state.piece_at(board_row, board_col)
                if piece != "--":
                    self.screen.blit(
                        self.images[piece],
                        pygame.Rect(c * self.sq_size, r * self.sq_size,
                                    self.sq_size, self.sq_size),
                    )

    def _draw_move_log(self) -> None:
        rect = pygame.Rect(
            config.BOARD_SIZE, 0,
            config.MOVE_LOG_PANEL_WIDTH, config.BOARD_SIZE,
        )
        pygame.draw.rect(self.screen, pygame.Color("black"), rect)

        lines = format_move_log_lines(self.game.state.move_history)
        padding_x = 5
        padding_y = 5
        line_spacing = 5
        for line in lines:
            obj = self.move_log_font.render(line, True, pygame.Color("white"))
            if padding_y + obj.get_height() >= config.BOARD_SIZE - 1:
                # Wrap into the next column when we run out of vertical space.
                padding_y = 5
                padding_x += 100
            self.screen.blit(obj, rect.move(padding_x, padding_y))
            padding_y += obj.get_height() + line_spacing

    def _draw_end_game_text(self) -> None:
        text = self._end_game_text()
        if text is None:
            return
        obj = self.end_game_font.render(text, True, pygame.Color("white"))
        location = pygame.Rect(0, 0, config.BOARD_SIZE, config.BOARD_SIZE).move(
            (config.BOARD_SIZE - obj.get_width()) / 2,
            (config.BOARD_SIZE - obj.get_height()) / 2,
        )
        # Subtle drop shadow for legibility against any board square.
        shadow = self.end_game_font.render(text, True, pygame.Color("black"))
        self.screen.blit(shadow, location.move(2, 2))
        self.screen.blit(obj, location)

    def _end_game_text(self) -> Optional[str]:
        status = self.game.status()
        result = self.game.result()
        if status == GameStatus.CHECKMATE:
            winner = "Black" if result == GameResult.BLACK_WINS else "White"
            return f"{winner} Wins by Checkmate"
        if status == GameStatus.STALEMATE:
            return "Draw by Stalemate"
        if status == GameStatus.DRAW_FIFTY_MOVES:
            return "Draw by 50-move Rule"
        if status == GameStatus.DRAW_INSUFFICIENT_MATERIAL:
            return "Draw - Insufficient Material"
        return None

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _animate_move(self, move: Move) -> None:
        """Slide ``move``'s piece from start to end square over a few frames.

        ``apply_move`` has already been called by the time we get here,
        so the board reflects the post-move state. We hide the piece at
        the destination square and redraw it at an interpolated position
        for each animation frame.
        """
        dr = move.end_row - move.start_row
        dc = move.end_col - move.start_col
        frame_count = (abs(dr) + abs(dc)) * config.ANIMATION_FRAMES_PER_SQUARE
        if frame_count == 0:
            return

        screen_end_row, screen_end_col = self._to_screen(move.end_row, move.end_col)
        screen_start_row, _ = self._to_screen(move.start_row, move.start_col)

        for frame in range(frame_count + 1):
            # Interpolated board position of the moving piece.
            interp_row = move.start_row + dr * frame / frame_count
            interp_col = move.start_col + dc * frame / frame_count
            if not self.human_plays_white:
                interp_row, interp_col = flip_coords(interp_row, interp_col)

            self._draw_board()
            self._draw_pieces()

            # Erase the moved piece from the destination square.
            end_square_color = self.board_colors[(screen_end_row + screen_end_col) % 2]
            end_rect = pygame.Rect(
                screen_end_col * self.sq_size,
                screen_end_row * self.sq_size,
                self.sq_size, self.sq_size,
            )
            pygame.draw.rect(self.screen, end_square_color, end_rect)

            # Re-draw the captured piece for the duration of the animation.
            if move.piece_captured != "--":
                if move.is_en_passant:
                    captured_rect = pygame.Rect(
                        screen_end_col * self.sq_size,
                        screen_start_row * self.sq_size,
                        self.sq_size, self.sq_size,
                    )
                else:
                    captured_rect = end_rect
                self.screen.blit(self.images[move.piece_captured], captured_rect)

            # Draw the moving piece at the interpolated position. For a
            # promotion we keep showing the pawn until the final frame.
            piece_to_draw = move.piece_moved
            if move.is_promotion and frame == frame_count:
                piece_to_draw = move.color + move.promotion_piece
            self.screen.blit(
                self.images[piece_to_draw],
                pygame.Rect(
                    interp_col * self.sq_size,
                    interp_row * self.sq_size,
                    self.sq_size, self.sq_size,
                ),
            )

            pygame.display.flip()
            self.clock.tick(config.ANIMATION_FPS)


__all__ = [
    "PygameUI",
    "UIState",
    "AIMoveFunction",
    "flip_coords",
    "format_move_log_lines",
    "find_legal_move",
]
