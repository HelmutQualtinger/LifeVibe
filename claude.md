# Game of Life - Development Notes

## Current State

### Project Overview
A fully functional Conway's Game of Life implementation with dual versions:
1. **Python/Pygame** - Desktop application
2. **HTML/JavaScript** - Web version

Both versions are feature-complete and share the same game mechanics and UI design.

### Python Version (life.py)

#### Architecture
- **Grid**: 120x80 cells using NumPy with boolean dtype for memory efficiency
- **Rendering**: Pygame with 8px cells + 1px margins
- **Performance**: 60 FPS with Numba JIT compilation (parallel=True, fastmath=True)

#### Key Components
- `init_grid()`: Creates empty boolean grid
- `_count_neighbors()`: Numba-compiled neighbor counting with Moore neighborhood (8 surrounding cells)
- `_update_grid_numba()`: Applies Conway's rules in parallel
- `draw_buttons()`: Dynamic button rendering based on paused state
- `main()`: Event loop and game logic

#### Features Implemented
- ✅ State-dependent button display (Start/Stop toggling)
- ✅ Left click to toggle cells
- ✅ Right click to kill cells
- ✅ Step mode for manual advancement
- ✅ Clear button to reset grid
- ✅ Generation counter
- ✅ Active cell counter
- ✅ Color-coded cells (cyan/green/orange based on neighbors)
- ✅ Edit mode indicator (white border when paused)
- ✅ Pattern loading from 28 preset patterns
- ✅ 60 FPS performance

#### Technical Optimizations
- Boolean grid uses 8x less memory than int8
- Numba JIT with parallel execution for O(n*m) grid updates
- fastmath=True for arithmetic operations
- Single-pass rendering with early neighbor counting

### Web Version (index.html)

#### Architecture
- **Grid**: Same 120x80 cells using JavaScript 2D arrays
- **Rendering**: HTML5 Canvas with requestAnimationFrame
- **Performance**: 60 FPS with optimized Canvas rendering

#### Key Components
- `initGrid()`: Creates empty grid
- `countNeighbors()`: Pure JavaScript neighbor counting
- `updateGrid()`: Applies Conway's rules
- `getCellFromMouse()`: Fixed click position detection with DPI scaling
- `draw()`: Canvas rendering
- `gameLoop()`: requestAnimationFrame-based update loop

#### Features Implemented
- ✅ Dynamic button generation based on state
- ✅ Click to toggle cells
- ✅ Right-click to kill cells (contextmenu prevention)
- ✅ Step mode
- ✅ Clear functionality
- ✅ Generation and cell counter
- ✅ Color-coded visualization
- ✅ Paused state indicator (white border)
- ✅ Fixed click position accuracy with DPI scaling
- ✅ Pattern loading from 28 preset patterns via modal UI

#### Technical Notes
- Click detection accounts for canvas scaling and DPI
- requestAnimationFrame for smooth 60 FPS
- Efficient grid copying with map/spread operators
- CSS Flexbox for responsive layout

### Shared Design Decisions

#### Color Scheme
- Background: Medium grey (#808080)
- Dead cells: Dark blue (#00008B)
- Lonely (0-1 neighbors): Cyan (#00FFFF)
- Stable (2-3 neighbors): Green (#00FF00)
- Crowded (4+ neighbors): Orange (#FF4500)
- UI: Dark grey buttons (#323232)

#### Button Logic
- **Paused state**: Shows Start, Step, Clear, Patterns, Quit
- **Running state**: Shows Stop, Step, Clear, Patterns, Quit
- Clear always available for quick reset
- Step only advances when paused
- Patterns button opens modal with 28 preset patterns

#### Grid Specifications
- Dimensions: 120x80 cells
- Cell size: 8 pixels
- Margin: 1 pixel between cells
- Rendering offset: 1 pixel margin on all sides

## Recent Changes

1. **Button State Management**: Implemented dynamic button filtering - Start/Stop buttons toggle based on paused state
2. **FPS Optimization**: Increased from 10 to 60 FPS
3. **Cell Toggle**: Changed left-click from "set alive" to "toggle" for better editing
4. **Clear Button**: Added with generation reset
5. **Boolean Grid**: Converted from int8 to bool for 8x memory savings
6. **Web Version**: Created full HTML5/JS implementation with fixed click detection
7. **Documentation**: Added README.md and claude.md

## Known Issues & Limitations

None currently. Both versions are stable and feature-complete.

## Possible Future Enhancements

### Feature Additions
- Preset patterns (gliders, blinkers, oscillators, beacons)
- Pattern library/loading
- Zoom and pan controls
- Variable speed/FPS adjustment
- Fullscreen mode

### UI/UX Improvements
- Color theme customization
- Button tooltips
- Keyboard shortcuts (Space=Start/Stop, C=Clear, etc.)
- Touch support for mobile web version

### Technical Improvements
- Save/load grid state to JSON
- Export as image (PNG) or GIF animation
- Dark/light theme toggle
- Statistics display (population history graph)

### Performance
- Web Worker for JS computation (move grid updates off main thread)
- WebGL rendering for larger grids
- Spatial hashing for sparse grids

## File Structure

```
Life/
├── life.py              # Python/Pygame implementation (235 lines)
├── index.html           # Web implementation (290 lines, fully embedded)
├── README.md            # User documentation
└── claude.md            # This file - development notes
```

## Version Control Notes

- Main branch contains stable, working versions
- Both implementations use identical game mechanics
- Web version fixed click position detection via DPI scaling
- Code is optimized for readability and performance
