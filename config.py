"""Configuration values for the pygame UI and game runner.

All display sizes are expressed in pixels. Colours are RGB tuples.
"""

# --- Display ---
BOARD_SIZE = 480                      # square board area
MOVE_LOG_PANEL_WIDTH = 300            # extra width for the move log column
MAX_FPS = 60
DIMENSION = 8                         # 8x8 chess board

# --- Fonts ---
MOVE_LOG_FONT_NAME = "Arial"
MOVE_LOG_FONT_SIZE = 16
END_GAME_FONT_NAME = "Arial"
END_GAME_FONT_SIZE = 32

# --- Board colours ---
BOARD_COLOR_LIGHT = (241, 223, 197)
BOARD_COLOR_DARK = (178, 135, 108)

# --- Highlight colours ---
HIGHLIGHT_SELECTED = (50, 100, 200)   # currently picked-up piece
HIGHLIGHT_MOVE = (200, 200, 50)       # legal destinations of selected piece
HIGHLIGHT_CHECK = (200, 50, 50)       # king's square when in check
HIGHLIGHT_LAST_MOVE = (240, 130, 180) # last move start + end squares

# --- Paths ---
IMAGE_FOLDER = "./images/"

# --- Player setup ---
HUMAN_PLAYS_WHITE = True              # if False, human plays black

# --- Animation ---
ANIMATION_FRAMES_PER_SQUARE = 3
ANIMATION_FPS = 60
