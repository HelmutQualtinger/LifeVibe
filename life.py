# ============================================================================
# Conway's Game of Life - Pygame Implementation
# ============================================================================
# This module implements Conway's Game of Life with a Pygame GUI.
# Features include interactive grid editing, pattern loading, and color-coded
# cell visualization based on neighbor counts.

import pygame           # GUI and graphics rendering
import sys             # System utilities for exit
import numpy as np     # Efficient array operations for grid
from numba import jit  # JIT compilation for performance optimization
from patterns import PATTERNS  # Pattern library for preset configurations

# ============================================================================
# CONFIGURATION: Game parameters and display settings
# ============================================================================

# Grid dimensions (120 columns x 80 rows = 9600 cells)
GRID_WIDTH = 120      # Number of columns in the game grid
GRID_HEIGHT = 80      # Number of rows in the game grid

# Cell visualization settings
CELL_SIZE = 8         # Pixel width/height of each cell
MARGIN = 1            # Gap (in pixels) between cells for visual separation

# Display layout
BUTTON_PANEL_HEIGHT = 50  # Height of control button area at bottom
WIDTH = GRID_WIDTH * (CELL_SIZE + MARGIN) + MARGIN      # Total window width
HEIGHT = GRID_HEIGHT * (CELL_SIZE + MARGIN) + MARGIN + BUTTON_PANEL_HEIGHT  # Total window height

# Performance settings
FPS = 120             # Target frames per second for the game loop

# ============================================================================
# COLOR PALETTE: RGB tuples for game rendering and UI
# ============================================================================

# Base UI colors
BLACK = (20, 20, 20)                # Very dark black
BACKGROUND_GREY = (128, 128, 128)   # Grid background color
GRID_COLOR = (40, 40, 40)           # Unused - grid lines color
GRID_DARK_BLUE = (0, 0, 139)        # Color for dead cells
WHITE = (255, 255, 255)             # Used for text and UI borders
GREY = (100, 100, 100)              # Unused - general grey
BUTTON_COLOR = (50, 50, 50)         # Button background color
BUTTON_TEXT_COLOR = (255, 255, 255) # Button text color

# ============================================================================
# HEATMAP COLORS: Cell colors based on neighbor count (Conway's Rules)
# ============================================================================
# These colors help visualize cell state and stability:
# - Lonely cells: Underpopulated (0-1 neighbors), will die
# - Stable cells: Sustainable (2-3 neighbors), healthy population
# - Crowded cells: Overpopulated (4+ neighbors), will die

COLOR_LONELY = (0, 255, 255)   # Cyan: 0-1 neighbors (underpopulated)
COLOR_STABLE = (0, 255, 0)     # Green: 2-3 neighbors (stable/healthy)
COLOR_CROWDED = (255, 69, 0)   # Orange: 4+ neighbors (overpopulated)

# ============================================================================
# BUTTON CONFIGURATION: Control panel layout and definitions
# ============================================================================

# Button dimensions for UI rendering
BUTTON_WIDTH = 100   # Width of each button in pixels
BUTTON_HEIGHT = 30   # Height of each button in pixels
BUTTON_MARGIN = 10   # Space between buttons in pixels

# All available buttons and their actions
# Buttons dynamically shown/hidden based on game state (paused vs running)
ALL_BUTTONS = [
    {"text": "Start", "action": "start"},      # Resume game from paused state
    {"text": "Stop", "action": "stop"},        # Pause the running game
    {"text": "Step", "action": "step"},        # Advance one generation manually
    {"text": "Clear", "action": "clear"},      # Clear grid and reset counter
    {"text": "Patterns", "action": "patterns"},# Open pattern selection menu
    {"text": "Quit", "action": "quit"},        # Exit the application
]

# ============================================================================
# GRID INITIALIZATION AND PATTERN LOADING
# ============================================================================

def init_grid():
    """
    Creates an empty game grid filled with dead cells.

    Returns:
        np.ndarray: A 2D boolean array of shape (GRID_HEIGHT, GRID_WIDTH).
                   False = dead cell, True = alive cell.
                   Uses boolean dtype for memory efficiency (8x less than int8).
    """
    return np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=bool)


def load_pattern(grid, pattern_name, offset=(0, 0)):
    """
    Loads a preset pattern from the PATTERNS library onto the game grid.

    Args:
        grid (np.ndarray): The game grid to modify.
        pattern_name (str): Name of the pattern to load (e.g., "Glider", "Blinker").
        offset (tuple): (row_offset, col_offset) for positioning pattern on grid.
                       Defaults to (0, 0) for top-left placement.

    Note:
        - Pattern strings use 'O' for live cells and '.' for dead cells
        - Cells are placed at (r + offset[0], c + offset[1])
        - Out-of-bounds cells are silently skipped
        - Pattern format example: "O.O\n.O.\nO.O"
    """
    pattern_string = PATTERNS.get(pattern_name)
    if not pattern_string:
        return

    pattern_lines = pattern_string.strip().split('\n')
    for r, line in enumerate(pattern_lines):
        for c, char in enumerate(line.strip()):
            # Only place live cells (marked with 'O')
            if char == 'O':
                row, col = r + offset[0], c + offset[1]
                # Boundary check to prevent placing cells outside grid
                if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
                    grid[row, col] = 1  # Set cell to alive (True)

# ============================================================================
# CORE GAME LOGIC: Conway's Game of Life Rules with Numba Optimization
# ============================================================================
# Numba JIT decorators enable fast C-like compilation:
# - nopython=True: Compile to machine code (no Python interpreter)
# - parallel=True: Use all CPU cores for nested loops
# - fastmath=True: Use IEEE float approximations for speed

@jit(nopython=True, parallel=True, fastmath=True)
def _count_neighbors(grid, r, c, height, width):
    """
    Counts the number of alive neighbors for a cell at position (r, c).

    Checks all 8 surrounding cells (Moore neighborhood):
        (r-1,c-1) (r-1,c) (r-1,c+1)
        (r,  c-1) (r,  c) (r,  c+1)
        (r+1,c-1) (r+1,c) (r+1,c+1)

    Args:
        grid (np.ndarray): 2D boolean grid of cell states.
        r (int): Row index of the cell.
        c (int): Column index of the cell.
        height (int): Number of rows in grid.
        width (int): Number of columns in grid.

    Returns:
        int: Count of alive neighbors (0-8).

    Note:
        This function is compiled with Numba for high performance.
        Boundary checking prevents out-of-bounds access.
    """
    count = 0
    # Check all 8 surrounding cells
    for i in range(-1, 2):      # -1, 0, 1 (vertical offset)
        for j in range(-1, 2):  # -1, 0, 1 (horizontal offset)
            if i == 0 and j == 0:  # Skip the center cell itself
                continue
            nr, nc = r + i, c + j  # Calculate neighbor position
            # Boundary check: ensure neighbor is within grid bounds
            if 0 <= nr < height and 0 <= nc < width:
                count += grid[nr, nc]  # Increment if neighbor is alive (True)
    return count


@jit(nopython=True, parallel=True, fastmath=True)
def _update_grid_numba(grid, height, width):
    """
    Applies Conway's Game of Life rules to all cells simultaneously.

    Conway's Rules:
    1. Any live cell with 2-3 neighbors survives to next generation
    2. Any dead cell with exactly 3 neighbors becomes alive
    3. All other cells die or stay dead (underpopulation/overpopulation)

    Args:
        grid (np.ndarray): Current generation's 2D boolean grid.
        height (int): Number of rows.
        width (int): Number of columns.

    Returns:
        np.ndarray: New grid for the next generation.

    Note:
        Creates a copy of the grid to allow simultaneous evaluation
        (all cells are evaluated based on current state, not updated state).
        Compiled with Numba and parallel execution for speed.
    """
    new_grid = grid.copy()  # Create copy to avoid in-place updates

    # Evaluate all cells in parallel
    for r in range(height):
        for c in range(width):
            neighbors = _count_neighbors(grid, r, c, height, width)
            state = grid[r, c]  # Current state (True/False)

            if state == 1:  # Cell is currently ALIVE
                # Survival rule: live with 2-3 neighbors
                if neighbors < 2 or neighbors > 3:
                    new_grid[r, c] = 0  # Dies from underpopulation or overpopulation
            else:  # Cell is currently DEAD
                # Birth rule: dead cell becomes alive with exactly 3 neighbors
                if neighbors == 3:
                    new_grid[r, c] = 1  # Becomes alive

    return new_grid


def update_grid(grid):
    """
    Wrapper function to update the grid for one generation.

    This is the main entry point for advancing the game by one generation.
    It delegates to the Numba-compiled _update_grid_numba function.

    Args:
        grid (np.ndarray): Current generation's grid.

    Returns:
        np.ndarray: Next generation's grid after applying Conway's rules.
    """
    return _update_grid_numba(grid, GRID_HEIGHT, GRID_WIDTH)


def get_neighbors(grid, r, c):
    """
    Returns the neighbor count for a cell at position (r, c).

    Used primarily for color coding cells based on neighbor count.
    Delegates to the Numba-compiled _count_neighbors function.

    Args:
        grid (np.ndarray): The game grid.
        r (int): Row index.
        c (int): Column index.

    Returns:
        int: Number of alive neighbors (0-8).
    """
    return _count_neighbors(grid, r, c, GRID_HEIGHT, GRID_WIDTH)

# ============================================================================
# UI RENDERING: Button drawing and color visualization
# ============================================================================

def draw_buttons(screen, font, paused, button_rects):
    """
    Renders control buttons on the button panel at the bottom of the screen.

    Buttons shown depend on game state:
    - Paused: Start, Step, Clear, Patterns, Quit
    - Running: Stop, Step, Clear, Patterns, Quit

    Args:
        screen: Pygame display surface to draw on.
        font: Pygame font object for text rendering.
        paused (bool): True if game is paused, False if running.
        button_rects (dict): Dictionary to store button rectangles for click detection.
                           Maps action name to pygame.Rect.

    Note:
        - Buttons are centered horizontally in the button panel
        - button_rects dict is cleared and repopulated each frame
        - Used in event handling to detect button clicks
    """
    # Filter buttons based on current game state
    if paused:
        # Paused: show Start (not Stop)
        visible_buttons = [b for b in ALL_BUTTONS if b["action"] != "stop"]
    else:
        # Running: show Stop (not Start)
        visible_buttons = [b for b in ALL_BUTTONS if b["action"] != "start"]

    # Calculate horizontal centering of button group
    total_button_width = len(visible_buttons) * BUTTON_WIDTH + (len(visible_buttons) - 1) * BUTTON_MARGIN
    start_x = (WIDTH - total_button_width) // 2

    # Position buttons vertically centered in the button panel
    button_y = HEIGHT - BUTTON_PANEL_HEIGHT + (BUTTON_PANEL_HEIGHT - BUTTON_HEIGHT) // 2

    button_rects.clear()  # Reset rectangles for new positions
    for i, button in enumerate(visible_buttons):
        # Calculate button position (spread horizontally with margins)
        x = start_x + i * (BUTTON_WIDTH + BUTTON_MARGIN)
        rect = pygame.Rect(x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        button_rects[button["action"]] = rect

        # Draw button background
        pygame.draw.rect(screen, BUTTON_COLOR, rect)

        # Draw button text centered on button
        text_surface = font.render(button["text"], True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)


def get_cell_color(neighbors):
    """
    Determines cell color based on neighbor count (heatmap visualization).

    Color mapping reflects cell stability in Conway's Game of Life:
    - Cyan: 0-1 neighbors (underpopulated, will die)
    - Green: 2-3 neighbors (stable, healthy population)
    - Orange: 4+ neighbors (overpopulated, will die)

    Args:
        neighbors (int): Count of alive neighbors (0-8).

    Returns:
        tuple: RGB color tuple (r, g, b) for Pygame rendering.
    """
    if neighbors < 2:
        return COLOR_LONELY        # 0-1 neighbors: underpopulated (cyan)
    elif neighbors <= 3:
        return COLOR_STABLE        # 2-3 neighbors: stable (green)
    else:
        return COLOR_CROWDED       # 4+ neighbors: overpopulated (orange)


def draw_pattern_menu(screen, font):
    """
    Renders a modal menu for pattern selection.

    Displays all available patterns from the PATTERNS library in a centered
    modal window. Patterns are listed alphabetically for easy browsing.

    Args:
        screen: Pygame display surface to draw on.
        font: Pygame font object for text rendering.

    Returns:
        dict: Dictionary mapping pattern names to their text rectangles for
              click detection in the main event loop.

    Note:
        - Menu is centered on screen (occupies middle 50% of width/height)
        - Has grey background and white border
        - Patterns are rendered as clickable text items
    """
    # Create modal rectangle centered on screen
    menu_rect = pygame.Rect(WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2)

    # Draw menu background and border
    pygame.draw.rect(screen, (100, 100, 100), menu_rect)          # Grey background
    pygame.draw.rect(screen, (255, 255, 255), menu_rect, 2)       # White border

    # Render pattern list
    y_offset = menu_rect.top + 20  # Start below top of menu
    pattern_rects = {}

    # Draw each pattern name alphabetically
    for pattern_name in sorted(PATTERNS.keys()):
        text_surface = font.render(pattern_name, True, (255, 255, 255))
        text_rect = text_surface.get_rect(centerx=menu_rect.centerx, top=y_offset)
        screen.blit(text_surface, text_rect)
        pattern_rects[pattern_name] = text_rect  # Store for click detection
        y_offset += 30  # Space between pattern names

    return pattern_rects


# ============================================================================
# MAIN GAME LOOP: Event handling, logic, and rendering
# ============================================================================

def main():
    """
    Main game loop for Conway's Game of Life.

    Initializes Pygame, manages the game state, handles user input, updates
    the grid according to Conway's rules, and renders everything each frame.

    Game Flow:
    1. Initialize Pygame and display
    2. Create empty grid
    3. Enter main loop:
       - Handle user input (mouse/button clicks)
       - Update grid if running
       - Render grid, buttons, and UI
       - Maintain 120 FPS

    State Variables:
    - paused: Whether game is currently paused (can edit grid)
    - generation: Counter for number of generations
    - show_pattern_menu: Whether pattern selection modal is visible
    """
    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    pygame.init()  # Initialize all Pygame modules
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game of Life - Color Heatmap")
    clock = pygame.time.Clock()  # For frame rate control

    # Font setup for text rendering
    pygame.font.init()
    font = pygame.font.Font(None, 24)  # Default system font, size 24

    # ========================================================================
    # GAME STATE INITIALIZATION
    # ========================================================================

    grid = init_grid()              # Create empty grid
    running = True                  # Main loop condition
    paused = True                   # Start paused so user can draw patterns
    generation = 0                  # Generation counter (increments each update)
    active_cells = 0                # Number of alive cells
    button_rects = {}               # Dictionary for button click detection
    show_pattern_menu = False       # Whether pattern selection modal is open
    pattern_rects = {}              # Dictionary for pattern menu click detection

    # ========================================================================
    # MAIN GAME LOOP
    # ========================================================================

    while running:
        # ====================================================================
        # EVENT HANDLING: Keyboard, mouse clicks, and window events
        # ====================================================================

        for event in pygame.event.get():
            # --- Window Close Event ---
            if event.type == pygame.QUIT:
                running = False

            # --- Mouse Click Events ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()

                # Check if pattern menu is open
                if show_pattern_menu:
                    # User clicked on pattern menu - handle pattern selection
                    for pattern_name, rect in pattern_rects.items():
                        if rect.collidepoint(pos):
                            # Clear grid and load selected pattern
                            grid = init_grid()
                            pattern_lines = PATTERNS[pattern_name].strip().split('\n')
                            pattern_height = len(pattern_lines)
                            pattern_width = max(len(line.strip()) for line in pattern_lines)
                            # Center pattern on grid
                            offset_r = (GRID_HEIGHT - pattern_height) // 2
                            offset_c = (GRID_WIDTH - pattern_width) // 2
                            load_pattern(grid, pattern_name, offset=(offset_r, offset_c))
                            show_pattern_menu = False  # Close menu
                            paused = True               # Pause after loading
                            generation = 0              # Reset counter
                            break

                # Check if click is on game grid (not on button panel)
                elif pos[1] < HEIGHT - BUTTON_PANEL_HEIGHT:
                    # Convert pixel coordinates to grid coordinates
                    c = pos[0] // (CELL_SIZE + MARGIN)
                    r = pos[1] // (CELL_SIZE + MARGIN)
                    # Toggle cell state (alive <-> dead)
                    if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                        grid[r][c] = 1 - grid[r][c]

                # Check if click is on button panel
                else:
                    for action, rect in button_rects.items():
                        if rect.collidepoint(pos):
                            # Handle each button action
                            if action == "start":
                                paused = False  # Resume game
                            elif action == "stop":
                                paused = True   # Pause game
                            elif action == "step":
                                # Advance one generation (only when paused)
                                if paused:
                                    grid = update_grid(grid)
                                    generation += 1
                            elif action == "clear":
                                # Clear grid and reset counters
                                grid = init_grid()
                                generation = 0
                                active_cells = 0
                            elif action == "patterns":
                                # Toggle pattern menu visibility
                                show_pattern_menu = not show_pattern_menu
                            elif action == "quit":
                                # Exit application
                                running = False

            # --- Continuous Right Click: Kill cells ---
            # Right-click while holding to continuously kill cells
            if not show_pattern_menu and pygame.mouse.get_pressed()[2]:
                pos = pygame.mouse.get_pos()
                c = pos[0] // (CELL_SIZE + MARGIN)
                r = pos[1] // (CELL_SIZE + MARGIN)
                # Set cell to dead (False)
                if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                    grid[r][c] = 0

        # ====================================================================
        # GAME LOGIC: Update grid state
        # ====================================================================

        # Apply Conway's Game of Life rules if game is running
        if not paused:
            grid = update_grid(grid)  # Advance to next generation
            generation += 1           # Increment generation counter

        # Count total alive cells (for display statistics)
        active_cells = np.sum(grid)

        # ====================================================================
        # RENDERING: Draw everything to the screen
        # ====================================================================

        # Clear screen with background color
        screen.fill(BACKGROUND_GREY)

        # --- Draw Grid ---
        # Iterate through all cells and render them
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                # Calculate pixel position for this cell
                # Each cell takes up (CELL_SIZE + MARGIN) pixels, with MARGIN offset
                x = c * (CELL_SIZE + MARGIN) + MARGIN
                y = r * (CELL_SIZE + MARGIN) + MARGIN

                # Color cell based on alive/dead state
                if grid[r][c] == 1:
                    # ALIVE: Color based on neighbor count (heatmap)
                    n_count = get_neighbors(grid, r, c)
                    color = get_cell_color(n_count)
                    pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    # DEAD: Display as dark blue
                    pygame.draw.rect(screen, GRID_DARK_BLUE, (x, y, CELL_SIZE, CELL_SIZE))

        # --- Draw UI Elements ---
        if show_pattern_menu:
            # Pattern menu is open: render pattern selection modal
            pattern_rects = draw_pattern_menu(screen, font)
        else:
            # Pattern menu is closed: render control buttons
            draw_buttons(screen, font, paused, button_rects)

        # --- Draw Statistics Panel ---
        # Display generation counter and active cell count
        gen_text = font.render(f"Gen: {generation}  Cells: {int(active_cells)}", True, WHITE)
        screen.blit(gen_text, (10, HEIGHT - BUTTON_PANEL_HEIGHT + 10))

        # --- Draw Paused Indicator ---
        # When paused, draw white border around entire grid to indicate edit mode
        if paused:
            pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), 2)

        # Update display
        pygame.display.flip()

        # Frame rate control: maintain consistent FPS
        clock.tick(FPS)

    # ========================================================================
    # CLEANUP: Exit the application
    # ========================================================================

    pygame.quit()   # Clean up Pygame resources
    sys.exit()      # Exit Python program
    

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Entry point for the Game of Life application.

    Only runs main() if this file is executed directly (not imported).
    This allows the module to be imported without starting the game loop.
    """
    main()