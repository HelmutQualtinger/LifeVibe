import pygame
import sys
import numpy as np
from numba import jit
from patterns import PATTERNS

# --- Configuration ---
GRID_WIDTH = 120      # 120 columns
GRID_HEIGHT = 80      # 80 rows
CELL_SIZE = 8         # Pixel size of each cell
MARGIN = 1            # Gap between cells

BUTTON_PANEL_HEIGHT = 50 # Height for the button panel
WIDTH = GRID_WIDTH * (CELL_SIZE + MARGIN) + MARGIN
HEIGHT = GRID_HEIGHT * (CELL_SIZE + MARGIN) + MARGIN + BUTTON_PANEL_HEIGHT
FPS = 120              # Speed of the game

# --- Colors (R, G, B) ---
BLACK = (20, 20, 20)
BACKGROUND_GREY = (128, 128, 128)
GRID_COLOR = (40, 40, 40)
GRID_DARK_BLUE = (0, 0, 139)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
BUTTON_COLOR = (50, 50, 50)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Neighbor-based Colors (Heatmap)
# 0-1 Neighbors (Underpopulated - Dying): Blue/Cyan
COLOR_LONELY = (0, 255, 255) 
# 2-3 Neighbors (Stable/Reporducing - Healthy): Green
COLOR_STABLE = (0, 255, 0)    
# 4+ Neighbors (Overpopulated - Dying): Red/Orange
COLOR_CROWDED = (255, 69, 0)  

# Button properties
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
BUTTON_MARGIN = 10

ALL_BUTTONS = [
    {"text": "Start", "action": "start"},
    {"text": "Stop", "action": "stop"},
    {"text": "Step", "action": "step"},
    {"text": "Clear", "action": "clear"},
    {"text": "Patterns", "action": "patterns"},
    {"text": "Quit", "action": "quit"},
]

def init_grid():
    """Creates an empty 80x120 grid."""
    return np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=bool)


def load_pattern(grid, pattern_name, offset=(0, 0)):
    """Loads a pattern from the PATTERNS dictionary onto the grid."""
    pattern_string = PATTERNS.get(pattern_name)
    if not pattern_string:
        return

    pattern_lines = pattern_string.strip().split('\n')
    for r, line in enumerate(pattern_lines):
        for c, char in enumerate(line.strip()):
            if char == 'O':
                row, col = r + offset[0], c + offset[1]
                if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
                    grid[row, col] = 1

@jit(nopython=True, parallel=True,fastmath=True)
def _count_neighbors(grid, r, c, height, width):
    """
    Counts alive neighbors for cell at (r, c).
    Numba-compiled for speed.
    """
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            nr, nc = r + i, c + j
            if 0 <= nr < height and 0 <= nc < width:
                count += grid[nr, nc]
    return count

@jit(nopython=True, parallel=True,fastmath=True)
def _update_grid_numba(grid, height, width):
    """Applies Conway's Game of Life Rules. Numba-compiled."""
    new_grid = grid.copy()

    for r in range(height):
        for c in range(width):
            neighbors = _count_neighbors(grid, r, c, height, width)
            state = grid[r, c]

            if state == 1:  # If Alive
                if neighbors < 2 or neighbors > 3:
                    new_grid[r, c] = 0
            else:  # If Dead
                if neighbors == 3:
                    new_grid[r, c] = 1

    return new_grid

def update_grid(grid):
    """Applies Conway's Game of Life Rules."""
    return _update_grid_numba(grid, GRID_HEIGHT, GRID_WIDTH)

def get_neighbors(grid, r, c):
    """
    Counts alive neighbors for cell at (r, c).
    Checks the 8 surrounding cells (Moore Neighborhood).
    """
    return _count_neighbors(grid, r, c, GRID_HEIGHT, GRID_WIDTH)

def draw_buttons(screen, font, paused, button_rects):
    """Draws the control buttons at the bottom of the screen."""
    # Filter buttons based on paused state
    if paused:
        visible_buttons = [b for b in ALL_BUTTONS if b["action"] != "stop"]
    else:
        visible_buttons = [b for b in ALL_BUTTONS if b["action"] != "start"]

    # Calculate starting x position to center the buttons
    total_button_width = len(visible_buttons) * BUTTON_WIDTH + (len(visible_buttons) - 1) * BUTTON_MARGIN
    start_x = (WIDTH - total_button_width) // 2

    # Position buttons below the grid
    button_y = HEIGHT - BUTTON_PANEL_HEIGHT + (BUTTON_PANEL_HEIGHT - BUTTON_HEIGHT) // 2

    button_rects.clear()
    for i, button in enumerate(visible_buttons):
        x = start_x + i * (BUTTON_WIDTH + BUTTON_MARGIN)
        rect = pygame.Rect(x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        button_rects[button["action"]] = rect

        pygame.draw.rect(screen, BUTTON_COLOR, rect)

        # Render text
        text_surface = font.render(button["text"], True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

def get_cell_color(neighbors):
    """Returns color based on neighbor count."""
    if neighbors < 2:
        return COLOR_LONELY
    elif neighbors <= 3:        return COLOR_STABLE
    elif neighbors == 0:
        return WHITE

        return COLOR_STABLE
    else:
        return COLOR_CROWDED


def draw_pattern_menu(screen, font):
    """Draws the pattern selection menu."""
    menu_rect = pygame.Rect(WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(screen, (100, 100, 100), menu_rect)
    pygame.draw.rect(screen, (255, 255, 255), menu_rect, 2) # border

    y_offset = menu_rect.top + 20
    pattern_rects = {}
    for pattern_name in sorted(PATTERNS.keys()):
        text_surface = font.render(pattern_name, True, (255, 255, 255))
        text_rect = text_surface.get_rect(centerx=menu_rect.centerx, top=y_offset)
        screen.blit(text_surface, text_rect)
        pattern_rects[pattern_name] = text_rect
        y_offset += 30
    return pattern_rects


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game of Life - Color Heatmap")
    clock = pygame.time.Clock()
    pygame.font.init() # Initialize font module
    font = pygame.font.Font(None, 24) # Default font, size 24

    grid = init_grid()
    running = True
    paused = True # Start paused so user can draw
    generation = 0
    active_cells = 0
    button_rects = {}
    show_pattern_menu = False
    pattern_rects = {}

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if show_pattern_menu:
                    for pattern_name, rect in pattern_rects.items():
                        if rect.collidepoint(pos):
                            grid = init_grid()
                            pattern_lines = PATTERNS[pattern_name].strip().split('\n')
                            pattern_height = len(pattern_lines)
                            pattern_width = max(len(line.strip()) for line in pattern_lines)
                            offset_r = (GRID_HEIGHT - pattern_height) // 2
                            offset_c = (GRID_WIDTH - pattern_width) // 2
                            load_pattern(grid, pattern_name, offset=(offset_r, offset_c))
                            show_pattern_menu = False
                            paused = True
                            generation = 0
                            break
                elif pos[1] < HEIGHT - BUTTON_PANEL_HEIGHT: # Click on grid
                    # Calculate grid index from pixel position
                    c = pos[0] // (CELL_SIZE + MARGIN)
                    r = pos[1] // (CELL_SIZE + MARGIN)
                    if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                        grid[r][c] = 1 - grid[r][c] # Toggle cell
                else: # Click on button panel
                    for action, rect in button_rects.items():
                        if rect.collidepoint(pos):
                            if action == "start":
                                paused = False
                            elif action == "stop":
                                paused = True
                            elif action == "step":
                                if paused: # Only step if paused
                                    grid = update_grid(grid)
                            elif action == "clear":
                                grid = init_grid()
                                generation = 0
                            elif action == "patterns":
                                show_pattern_menu = not show_pattern_menu
                            elif action == "quit":
                                running = False

            if pygame.mouse.get_pressed()[0]: # Left Click
                pass # Already handled above

            if not show_pattern_menu and pygame.mouse.get_pressed()[2]: # Right Click
                pos = pygame.mouse.get_pos()
                c = pos[0] // (CELL_SIZE + MARGIN)
                r = pos[1] // (CELL_SIZE + MARGIN)
                if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                    grid[r][c] = 0 # Set to Dead

            # Keyboard Controls

        # --- Logic ---
        if not paused:
            grid = update_grid(grid)
            generation += 1

        # Count active cells
        active_cells = np.sum(grid)

        # --- Drawing ---
        screen.fill(BACKGROUND_GREY)

        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                # Determine draw position
                x = c * (CELL_SIZE + MARGIN) + MARGIN
                y = r * (CELL_SIZE + MARGIN) + MARGIN

                # We draw dead cells as dark grey for grid effect, alive cells get color
                if grid[r][c] == 1:
                    # Calculate neighbors just for coloring
                    n_count = get_neighbors(grid, r, c)
                    color = get_cell_color(n_count)
                    pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    pygame.draw.rect(screen, GRID_DARK_BLUE, (x, y, CELL_SIZE, CELL_SIZE))

        if show_pattern_menu:
            pattern_rects = draw_pattern_menu(screen, font)
        else:
            # Draw buttons
            draw_buttons(screen, font, paused, button_rects)

        # Draw generation and active cells counter
        gen_text = font.render(f"Gen: {generation}  Cells: {int(active_cells)}", True, WHITE)
        screen.blit(gen_text, (10, HEIGHT - BUTTON_PANEL_HEIGHT + 10))

        # Draw specific UI indicators
        if paused:
            # Draw a small white border to indicate "Edit Mode"
            pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), 2)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()