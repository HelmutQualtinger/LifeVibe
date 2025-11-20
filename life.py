import pygame
import sys
import copy

# --- Configuration ---
GRID_SIZE = 40        # 40x40 Grid
CELL_SIZE = 15        # Pixel size of each cell
MARGIN = 1            # Gap between cells
BUTTON_PANEL_HEIGHT = 50 # Height for the button panel
WIDTH = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN
HEIGHT = WIDTH + BUTTON_PANEL_HEIGHT # Square window + button panel
FPS = 10              # Speed of the game

# --- Colors (R, G, B) ---
BLACK = (20, 20, 20)
GRID_COLOR = (40, 40, 40)
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

buttons = [
    {"text": "Start", "action": "start", "rect": None},
    {"text": "Stop", "action": "stop", "rect": None},
    {"text": "Step", "action": "step", "rect": None},
    {"text": "Quit", "action": "quit", "rect": None},
]

def init_grid():
    """Creates an empty 40x40 grid."""
    return [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def get_neighbors(grid, r, c):
    """
    Counts alive neighbors for cell at (r, c).
    Checks the 8 surrounding cells (Moore Neighborhood).
    """
    count = 0
    # Loop through -1, 0, 1 relative positions
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue # Skip self
            
            # Check boundaries
            nr, nc = r + i, c + j
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                count += grid[nr][nc]
    return count

def update_grid(grid):
    """Applies Conway's Game of Life Rules."""
    new_grid = copy.deepcopy(grid)
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            neighbors = get_neighbors(grid, r, c)
            state = grid[r][c]
            
            if state == 1: # If Alive
                # Rule 1 & 3: Die if < 2 or > 3 neighbors
                if neighbors < 2 or neighbors > 3:
                    new_grid[r][c] = 0
            else: # If Dead
                # Rule 4: Reproduction if exactly 3 neighbors
                if neighbors == 3:
                    new_grid[r][c] = 1
                    
    return new_grid

def get_cell_color(neighbors):
    """Returns color based on neighbor count."""
    if neighbors < 2:
        return COLOR_LONELY
    elif neighbors <= 3:
        return COLOR_STABLE
    else:
        return COLOR_CROWDED

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game of Life - Color Heatmap")
    clock = pygame.time.Clock()

    grid = init_grid()
    running = True
    paused = True # Start paused so user can draw

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mouse Controls
            if pygame.mouse.get_pressed()[0]: # Left Click
                pos = pygame.mouse.get_pos()
                # Calculate grid index from pixel position
                c = pos[0] // (CELL_SIZE + MARGIN)
                r = pos[1] // (CELL_SIZE + MARGIN)
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    grid[r][c] = 1 # Set to Alive
            
            if pygame.mouse.get_pressed()[2]: # Right Click
                pos = pygame.mouse.get_pos()
                c = pos[0] // (CELL_SIZE + MARGIN)
                r = pos[1] // (CELL_SIZE + MARGIN)
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    grid[r][c] = 0 # Set to Dead

            # Keyboard Controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_c:
                    grid = init_grid() # Clear
        
        # --- Logic ---
        if not paused:
            grid = update_grid(grid)

        # --- Drawing ---
        screen.fill(BLACK)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
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
                    pygame.draw.rect(screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE))

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