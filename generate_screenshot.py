import pygame
import numpy as np

# Configuration
GRID_WIDTH = 120
GRID_HEIGHT = 80
CELL_SIZE = 8
MARGIN = 1
BUTTON_PANEL_HEIGHT = 50
WIDTH = GRID_WIDTH * (CELL_SIZE + MARGIN) + MARGIN
HEIGHT = GRID_HEIGHT * (CELL_SIZE + MARGIN) + MARGIN + BUTTON_PANEL_HEIGHT

# Colors
BACKGROUND_GREY = (128, 128, 128)
GRID_DARK_BLUE = (0, 0, 139)
COLOR_LONELY = (0, 255, 255)
COLOR_STABLE = (0, 255, 0)
COLOR_CROWDED = (255, 69, 0)
WHITE = (255, 255, 255)
BUTTON_COLOR = (50, 50, 50)
BUTTON_TEXT_COLOR = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.Font(None, 24)

# Create a sample grid with some cells
grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=bool)

# Add some sample patterns
# Glider
grid[10, 10] = True
grid[11, 11] = True
grid[12, 9] = True
grid[12, 10] = True
grid[12, 11] = True

# Blinker
grid[20, 20] = True
grid[20, 21] = True
grid[20, 22] = True

# Random cells
for _ in range(20):
    r = np.random.randint(0, GRID_HEIGHT)
    c = np.random.randint(0, GRID_WIDTH)
    grid[r, c] = True

# Draw the grid
screen.fill(BACKGROUND_GREY)

def count_neighbors(grid, r, c):
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            nr, nc = r + i, c + j
            if 0 <= nr < GRID_HEIGHT and 0 <= nc < GRID_WIDTH:
                count += grid[nr, nc]
    return count

def get_cell_color(neighbors):
    if neighbors < 2:
        return COLOR_LONELY
    elif neighbors <= 3:
        return COLOR_STABLE
    else:
        return COLOR_CROWDED

# Render cells
for r in range(GRID_HEIGHT):
    for c in range(GRID_WIDTH):
        x = c * (CELL_SIZE + MARGIN) + MARGIN
        y = r * (CELL_SIZE + MARGIN) + MARGIN

        if grid[r, c]:
            neighbors = count_neighbors(grid, r, c)
            color = get_cell_color(neighbors)
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
        else:
            pygame.draw.rect(screen, GRID_DARK_BLUE, (x, y, CELL_SIZE, CELL_SIZE))

# Draw button panel background
button_y = HEIGHT - BUTTON_PANEL_HEIGHT
pygame.draw.rect(screen, BACKGROUND_GREY, (0, button_y, WIDTH, BUTTON_PANEL_HEIGHT))

# Draw some sample buttons
buttons = ["Start", "Step", "Clear", "Quit"]
button_width = 100
button_height = 30
button_margin = 10
total_button_width = len(buttons) * button_width + (len(buttons) - 1) * button_margin
start_x = (WIDTH - total_button_width) // 2
button_panel_y = button_y + (BUTTON_PANEL_HEIGHT - button_height) // 2

for i, text in enumerate(buttons):
    x = start_x + i * (button_width + button_margin)
    pygame.draw.rect(screen, BUTTON_COLOR, (x, button_panel_y, button_width, button_height))
    pygame.draw.rect(screen, (100, 100, 100), (x, button_panel_y, button_width, button_height), 2)
    
    text_surface = font.render(text, True, BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(x + button_width // 2, button_panel_y + button_height // 2))
    screen.blit(text_surface, text_rect)

# Draw info text
gen_text = font.render("Gen: 0  Cells: " + str(int(np.sum(grid))), True, WHITE)
screen.blit(gen_text, (10, button_y + 10))

# Save screenshot
pygame.image.save(screen, "/Users/haraldbeker/PythonProjects/Life/screenshot.png")
print("Screenshot saved as screenshot.png")

pygame.quit()
