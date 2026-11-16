# Board matrix values
BLANK = 0
PLAY1 = 1
PLAY2 = 2

# Game phases
PHASE1 = 1  # placement
PHASE2 = 2  # adjacent movement / flying when a player has 3 pieces

# Board size and pieces
ROWS = 7
COLS = 7
TOTAL_MENS = 9
THREEFOLD_REPETITION_COUNT = 3
MAX_MOVES_WITHOUT_CAPTURE = 50

# Current positions on the board; each NineMensMorrisGame deep-copies this.
CURRENT_POSITION = [[BLANK for _ in range(COLS)] for _ in range(ROWS)]

VALID_POINTS = [
    (0, 0),
    (0, 3),
    (0, 6),
    (1, 1),
    (1, 3),
    (1, 5),
    (2, 2),
    (2, 3),
    (2, 4),
    (3, 0),
    (3, 1),
    (3, 2),
    (3, 4),
    (3, 5),
    (3, 6),
    (4, 2),
    (4, 3),
    (4, 4),
    (5, 1),
    (5, 3),
    (5, 5),
    (6, 0),
    (6, 3),
    (6, 6),
]

# All legal mills. This intentionally excludes diagonals.
MILLS = [
    ((0, 0), (0, 3), (0, 6)),
    ((1, 1), (1, 3), (1, 5)),
    ((2, 2), (2, 3), (2, 4)),
    ((3, 0), (3, 1), (3, 2)),
    ((3, 4), (3, 5), (3, 6)),
    ((4, 2), (4, 3), (4, 4)),
    ((5, 1), (5, 3), (5, 5)),
    ((6, 0), (6, 3), (6, 6)),
    ((0, 0), (3, 0), (6, 0)),
    ((1, 1), (3, 1), (5, 1)),
    ((2, 2), (3, 2), (4, 2)),
    ((0, 3), (1, 3), (2, 3)),
    ((4, 3), (5, 3), (6, 3)),
    ((2, 4), (3, 4), (4, 4)),
    ((1, 5), (3, 5), (5, 5)),
    ((0, 6), (3, 6), (6, 6)),
]

ADJACENT_POSITIONS = {
    (0, 0): [(0, 3), (3, 0)],
    (0, 3): [(0, 0), (0, 6), (1, 3)],
    (0, 6): [(0, 3), (3, 6)],
    (1, 1): [(1, 3), (3, 1)],
    (1, 3): [(1, 1), (1, 5), (0, 3), (2, 3)],
    (1, 5): [(1, 3), (3, 5)],
    (2, 2): [(2, 3), (3, 2)],
    (2, 3): [(2, 2), (2, 4), (1, 3)],
    (2, 4): [(2, 3), (3, 4)],
    (3, 0): [(0, 0), (3, 1), (6, 0)],
    (3, 1): [(1, 1), (3, 0), (3, 2), (5, 1)],
    (3, 2): [(2, 2), (3, 1), (4, 2)],
    (3, 4): [(2, 4), (3, 5), (4, 4)],
    (3, 5): [(1, 5), (3, 4), (3, 6), (5, 5)],
    (3, 6): [(0, 6), (3, 5), (6, 6)],
    (4, 2): [(3, 2), (4, 3)],
    (4, 3): [(4, 2), (4, 4), (5, 3)],
    (4, 4): [(3, 4), (4, 3)],
    (5, 1): [(3, 1), (5, 3)],
    (5, 3): [(5, 1), (5, 5), (4, 3), (6, 3)],
    (5, 5): [(3, 5), (5, 3)],
    (6, 0): [(3, 0), (6, 3)],
    (6, 3): [(6, 0), (6, 6), (5, 3)],
    (6, 6): [(3, 6), (6, 3)],
}

# Board line coordinates for rendering.
LINES = [
    [3.5, 0.5, 3.5, 2.5],
    [0.5, 3.5, 2.5, 3.5],
    [3.5, 4.5, 3.5, 6.5],
    [4.5, 3.5, 6.5, 3.5],
    [0.5, 0.5, 6.5, 0.5],
    [6.5, 0.5, 6.5, 6.5],
    [6.5, 6.5, 0.5, 6.5],
    [0.5, 6.5, 0.5, 0.5],
    [1.5, 1.5, 5.5, 1.5],
    [5.5, 1.5, 5.5, 5.5],
    [5.5, 5.5, 1.5, 5.5],
    [1.5, 5.5, 1.5, 1.5],
    [2.5, 2.5, 4.5, 2.5],
    [4.5, 2.5, 4.5, 4.5],
    [4.5, 4.5, 2.5, 4.5],
    [2.5, 4.5, 2.5, 2.5],
]

# Screen and rendering
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720
MIN_DISPLAY_WIDTH = 900
MIN_DISPLAY_HEIGHT = 720
SUPPORTED_DISPLAY_SCALES = (1.0, 1.25, 1.5)
BOARD_PIXELS = 560
SQUARESIZE = 80
SIDEBAR_X = 610
CIRCLE_RADIUS = 16
LINE_WIDTH = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GOLD = (218, 165, 32)

# Player piece colors (Black and White)
PLAY1_COLOR_DARK = (40, 40, 50)  # Dark gray-black
PLAY1_COLOR_MAIN = (80, 80, 90)  # Medium gray-black
PLAY1_COLOR_LIGHT = (180, 180, 190)  # Light gray
PLAY2_COLOR_DARK = (240, 240, 245)  # Very light (white)
PLAY2_COLOR_MAIN = (255, 255, 255)  # Pure white
PLAY2_COLOR_LIGHT = (200, 200, 200)  # Light gray

# Dark wood board colors
BOARD_DARK = (139, 90, 43)  # Dark wood
BOARD_LINE_COLOR = (50, 30, 10)  # Very dark lines

PLAYER1_MESSAGE = "Player 1 (Black): place a piece"
PLAYER2_MESSAGE = "Player 2 (White): place a piece"
PLAY1_MOVE_MESSAGE = "Player 1 (Black): select a piece to move"
PLAY2_MOVE_MESSAGE = "Player 2 (White): select a piece to move"
REMOVE_MESSAGE = "Remove one opponent piece"
FLY_MESSAGE = ": flying is available"
H_VS_H = 0
H_VS_C = 1

POSITIONS = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g"}
GAME_STATE_FILE = "game_state.txt"

# Game difficulty levels for the computer player
EASY = 0
NORMAL = 1
HARD = 2
HARD_AI_DEPTH = 3

# Animation
ANIMATION_DURATION = 300  # milliseconds
ANIMATION_SPEED = 8  # pixels per frame
