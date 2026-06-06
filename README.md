# Chess Engine

A chess game with a pygame UI and an AI opponent, built as a software
engineering course project. The repository demonstrates a clean layered
architecture, comprehensive automated testing, a CI pipeline running on
every push, and a disciplined Git workflow with protected branches and
peer-reviewed pull requests.

## Features

- Full chess rules, including castling, en passant, pawn promotion, the
  fifty-move rule, and insufficient-material draws
- AI opponent using negamax search with alpha-beta pruning
- Pygame UI with animated piece movement, move highlights, last-move
  indicator, in-check warning, and a side panel showing the move log
- Undo (Z) and reset (R) keyboard shortcuts
- Configurable side (human plays white or black) via `config.py`
- 83 automated tests covering rules, AI evaluation, search, and UI
  helpers; run on every push via GitHub Actions

## Requirements

- Python 3.12
- Dependencies listed in `requirements.txt` (pygame, pytest, pytest-cov)

## Installation and Running

```bash
# 1. Clone the repository
git clone https://github.com/AdamescuArmand/POSD_Project.git
cd POSD_Project

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the game
python main.py
```

## Controls

| Input          | Action                       |
| -------------- | ---------------------------- |
| Click + click  | Select a piece, then a square |
| `Z`            | Undo the last full turn      |
| `R`            | Reset to a new game          |
| Close window   | Quit                         |

## Running the Tests

```bash
# Run the full test suite
pytest tests/

# With coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

## Project Structure

```
.
├── core/                # Game logic (no pygame dependency)
│   ├── board.py         # BoardState, CastlingRights, apply/undo move
│   ├── move.py          # Move dataclass, algebraic notation helpers
│   ├── rules.py         # Move generation, check/checkmate detection
│   └── game.py          # High-level Game state machine
├── ai/                  # AI engine
│   ├── evaluation.py    # Static board scoring with piece-square tables
│   ├── search.py        # Negamax with alpha-beta pruning
│   └── random_player.py # Random-move placeholder used for testing
├── ui/                  # Presentation layer
│   └── pygame_ui.py     # Pygame display, input handling, animations
├── tests/               # Mirrors the source structure
│   ├── test_board.py
│   ├── test_move.py
│   ├── test_rules.py
│   ├── test_game.py
│   ├── test_evaluation.py
│   ├── test_search.py
│   ├── test_random_player.py
│   └── test_pygame_ui.py
├── images/              # Piece sprites referenced by the UI
├── .github/workflows/   # CI pipeline definition
├── config.py            # Display, colour, and player settings
├── main.py              # Entry point
└── requirements.txt
```

The project follows a strict layered architecture:

```
ui  ────► ai  ────► core
                     ▲
                    (no upward dependencies)
```

`core/` has zero dependency on pygame or any AI logic, which means the
game rules and game state machine can be exercised entirely in headless
unit tests. `ai/` depends only on `core/`. `ui/` is the only layer that
touches pygame.

## Development Workflow

This project was developed following the practices taught in the SE
course:

- **Protected `main` branch.** Direct pushes are forbidden; all changes
  arrive via pull requests with at least one approving review.
- **Integration branch (`dev`).** Feature branches are opened off `dev`
  and merged back into it; `dev` is periodically promoted to `main`.
- **Feature branches.** Every change of any size has its own branch
  named `feature/...`
- **Squash-merge.** Feature commits are squashed on merge so the
  history of `dev` reads as one commit per feature.
- **Continuous integration.** The GitHub Actions workflow in
  `.github/workflows/ci.yml` runs the full test suite on every push
  and pull request. A pull request cannot be merged until CI is green.
- **Peer review.** Every pull request was reviewed by the other author;
  feedback was applied as additional commits on the same branch before
  re-requesting review.

## Architecture Highlights

- **Pure-function move generation.** `rules.py` exposes
  `generate_legal_moves(state)` as a function, not a class method,
  which keeps unit tests trivial to write.
- **Undo via internal stack.** `BoardState.apply_move` pushes a small
  snapshot onto an internal undo stack so `BoardState.undo_move` can
  reverse mutations in O(1). This is critical for the AI search, which
  applies and undoes millions of moves during negamax traversal.
- **No global state in the search.** The negamax routine is a pure
  recursive function returning a score; the root-level
  `find_best_move` iterates over candidate moves and tracks the best
  one in a local variable.
- **Pluggable AI.** The UI accepts any
  `Callable[[Game], Optional[Move]]` as its move-picking function, so
  the placeholder `random_move` can be swapped for `find_best_move`
  with a single import change.

## Authors

- Adamescu Armand-Adelin
- Mateusz Waglowski