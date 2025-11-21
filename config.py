"""
Configuration module for Flood Control ACO Simulation
Contains all constants, colors, and enums
"""

from enum import Enum

# ==================== WINDOW & DISPLAY ====================
GRID_SIZE = 15  # Grid dimensions (15x15)
CELL_SIZE = 50  # Default size, will be dynamic
INFO_PANEL_WIDTH = 400  # Right panel width

# Default window size
DEFAULT_WINDOW_WIDTH = (GRID_SIZE * CELL_SIZE) + INFO_PANEL_WIDTH
DEFAULT_WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + 50

# ==================== GAME PARAMETERS ====================
MAX_WATER_THRESHOLD = 5000  # Game over if total water exceeds this
RAIN_INTENSITY_MIN = 0.3
RAIN_INTENSITY_MAX = 2.0
RAIN_INTENSITY_DEFAULT = 0.6

# ==================== BUDGET SYSTEM ====================
# All values in Philippine Peso (₱)
DEFAULT_BUDGET = 1000000000  # ₱1 Billion
BUDGET_MIN = 100000000  # ₱100 Million
BUDGET_MAX = 5000000000  # ₱5 Billion
DRAIN_COST = 200000000  # ₱200 Million per drain
PIPE_COST_PER_CELL = 10000000  # ₱10 Million per cell
MAX_TOTAL_PIPE_LENGTH = 500  # Maximum cells for all routes combined

# ==================== ACO PARAMETERS ====================
# Default values
DEFAULT_NUM_ANTS = 20
DEFAULT_EVAPORATION_RATE = 0.15
DEFAULT_PHEROMONE_STRENGTH = 2.0
ACO_ALPHA = 1.0  # Pheromone importance
ACO_BETA = 2.0  # Heuristic importance
ACO_MAX_STEPS = 150  # Maximum steps per ant
CONVERGENCE_THRESHOLD = 20  # Iterations without improvement to stop
# MIN_ITERATIONS_BEFORE_CONVERGENCE = 30  # Removed in favor of stagnation check

# Configurable ranges for user control
NUM_ANTS_MIN = 5
NUM_ANTS_MAX = 50
ALPHA_MIN = 0.1
ALPHA_MAX = 5.0
BETA_MIN = 0.1
BETA_MAX = 5.0
EVAPORATION_RATE_MIN = 0.01
EVAPORATION_RATE_MAX = 0.5

# ==================== GAME TIMING ====================
TARGET_FPS = 60
VICTORY_TIME_SECONDS = 20  # Survive this long to win
VICTORY_TIME_FRAMES = VICTORY_TIME_SECONDS * TARGET_FPS
STABILIZATION_THRESHOLD = 60  # Frames to check water stability

# ==================== MODERN COLOR PALETTE ====================
# Primary vibrant colors (HSL-based for modern feel)
PRIMARY_BLUE = (59, 130, 246)
PRIMARY_PURPLE = (139, 92, 246)
PRIMARY_GREEN = (34, 197, 94)
PRIMARY_ORANGE = (249, 115, 22)
PRIMARY_RED = (239, 68, 68)
PRIMARY_CYAN = (6, 182, 212)
PRIMARY_YELLOW = (234, 179, 8)

# Legacy colors (keeping for compatibility)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (220, 220, 220)
GREEN = (34, 197, 94)  # Updated to PRIMARY_GREEN
DARK_GREEN = (22, 163, 74)
BROWN = (139, 90, 43)
BLUE = (59, 130, 246)  # Updated to PRIMARY_BLUE
DARK_BLUE = (29, 78, 216)
RED = (239, 68, 68)  # Updated to PRIMARY_RED
YELLOW = (234, 179, 8)  # Updated to PRIMARY_YELLOW
CYAN = (6, 182, 212)  # Updated to PRIMARY_CYAN
PURPLE = (139, 92, 246)  # Updated to PRIMARY_PURPLE
ORANGE = (249, 115, 22)  # Updated to PRIMARY_ORANGE

# Specialized colors
WATER_BLUE = (65, 105, 225)
LIGHT_BLUE = (173, 216, 230)

# Gradient colors for panels
GRADIENT_START = (99, 102, 241)  # Indigo
GRADIENT_END = (168, 85, 247)  # Purple

# Glassmorphism effect colors
GLASS_PANEL = (255, 255, 255, 25)  # Semi-transparent white
GLASS_BORDER = (255, 255, 255, 50)

# Status colors
SUCCESS_COLOR = (34, 197, 94)
WARNING_COLOR = (249, 115, 22)
DANGER_COLOR = (239, 68, 68)
INFO_COLOR = (59, 130, 246)

# ==================== ENUMS ====================
class CellType(Enum):
    """Types of cells in the city grid"""
    EMPTY = 0
    ROAD = 1
    HOUSE = 2
    TREE = 3
    DRAIN = 4
    OBSTACLE = 5


class GamePhase(Enum):
    """Game phases for the flood control simulation"""
    SETUP = 1       # Player places drains
    OPTIMIZING = 2  # ACO finds paths
    DEFENDING = 3   # Rain starts, survive!
    GAME_OVER = 4   # Failed to manage water
    VICTORY = 5     # Successfully survived


# ==================== HELPER FUNCTIONS ====================
def format_currency(amount):
    """
    Format amount in Philippine Peso with B/M suffix
    
    Args:
        amount: Amount in pesos
        
    Returns:
        Formatted string (e.g., "Php 1.50B", "Php 200M")
    """
    if amount >= 1000000000:  # Billion
        return f"Php {amount / 1000000000:.2f}B"
    elif amount >= 1000000:  # Million
        return f"Php {amount / 1000000:.0f}M"
    else:
        return f"Php {amount:,.0f}"


def get_phase_color(phase):
    """
    Get the color associated with a game phase
    
    Args:
        phase: GamePhase enum value
        
    Returns:
        Tuple of (color, phase_text)
    """
    phase_colors = {
        GamePhase.SETUP: (PURPLE, "PHASE 1: SETUP"),
        GamePhase.OPTIMIZING: (ORANGE, "PHASE 2: OPTIMIZING"),
        GamePhase.DEFENDING: (RED, "PHASE 3: DEFENDING"),
        GamePhase.GAME_OVER: (RED, "GAME OVER"),
        GamePhase.VICTORY: (GREEN, "VICTORY!"),
    }
    return phase_colors.get(phase, (GRAY, "UNKNOWN"))
