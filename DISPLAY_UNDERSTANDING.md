# Display Understanding

This document explains how the display system in `display.py` works, what each
matplotlib call does, and why specific calculations (like multipliers) are used.

## Big Picture Flow (Start to End)

1. `Drawer` is created with a `Graph` and a move `history`.
2. `__init__` calls `make_states()` to expand the move history into per-turn
   positions for every drone.
3. `draw_map()` creates the matplotlib figure, builds the UI buttons, renders
   the first frame, then shows the window.
4. User interactions (buttons) call `move()`, `toggle_play()`, or
   `restart_animation()`.
5. Each turn calls `redraw()` to clear and re-render the whole scene.

## Class Structure

### `Drawer`
Holds the graph, the precomputed states, and matplotlib state (figure, axes,
buttons, and animation controller). It is a stateful object so the UI can update
based on user actions.

## Step-by-Step: Each Function

### `__init__(graph, history)`
- Saves input data and initializes the state (`turn`, `playing`, `anim`).
- Calls `make_states()` once so drawing is fast later.

### `make_states()`
- Builds a list where each element is a full snapshot of where every drone is
  at that turn.
- Each position is stored as a tuple:
  - `("zone", name)` for drones on a zone
  - `("edge", from_name, to_name)` for drones in transit
- Uses `step` to track where each drone is on its path so it can identify the
  next zone during transit.

### `draw_map()`
- Creates the figure and axes:
  - `plt.subplots()` creates the `fig` (window) and `ax` (drawing canvas).
  - `facecolor` sets the outer window background.
- `plt.subplots_adjust(bottom=0.18)` leaves room for buttons.
- Creates the UI buttons with `matplotlib.widgets.Button`.
- Connects button clicks to methods like `move()` and `toggle_play()`.
- Calls `redraw()` for the first frame, then `plt.show()` to block and display
  the UI.

### `toggle_play()`
- Starts or pauses the animation.
- When starting, it creates `animation.FuncAnimation` that repeatedly calls
  `_anim_step` every `interval` milliseconds.
- When stopping, it halts the animation and updates the button label.

### `_anim_step(frame)`
- Runs on each animation tick.
- If already at the end, it stops and resets the play state.
- Otherwise, it increments the turn and calls `redraw()`.

### `move(value)`
- Manual step forward/backward.
- Stops playback if it was running.
- Clamps the new turn between 0 and the last state index.

### `get_xy(place)`
- Converts a logical place tuple into an `(x, y)` coordinate.
- For zones: uses the zone's own coordinates.
- For edges: returns the midpoint between the two connected zones.

### `get_color(color, index)`
- Normalizes names (lowercase, no spaces/underscores).
- Uses custom palettes from `HARD_COLORS` (including list palettes).
- Falls back to CSS4 color names, then any valid matplotlib color string.
- Finally falls back to `DEFAULT_COLOR`.

### `redraw()`
The main renderer. It clears the axes and draws everything in order:

1. `ax.clear()` removes previous frame drawings.
2. `ax.set_title(...)` updates the turn counter title.
3. `ax.axis("off")` hides axis lines and ticks.
4. `ax.set_facecolor(...)` sets the canvas background.
5. Draw edges with `ax.plot(...)`.
6. Draw zones with `ax.scatter(...)` and their labels using `ax.text(...)`.
7. Draw drones with `ax.scatter(...)` and labels with `ax.text(...)`.
8. `ax.autoscale()` adjusts the view to include all elements.
9. Expand the view a bit with padding so content is not clipped.
10. `fig.canvas.draw_idle()` schedules the actual screen redraw.

## Matplotlib Functions Used and Why

- `plt.subplots(figsize, facecolor)`
  Creates the figure and axes. `figsize` sets the window size; `facecolor`
  sets the window background color.

- `plt.subplots_adjust(bottom=...)`
  Adds extra bottom margin so buttons fit without overlapping the plot.

- `Button(fig.add_axes(...), label, color, hovercolor)`
  Adds interactive buttons in fixed positions (normalized 0..1 coordinates).

- `ax.clear()`
  Removes all old drawings to avoid ghost frames.

- `ax.set_title(...)`
  Shows the current frame counter at the top of the plot.

- `ax.axis("off")`
  Hides axes for a clean, map-like look.

- `ax.set_facecolor(...)`
  Sets the plot background (inside the axes).

- `ax.plot(x_list, y_list, ...)`
  Draws each connection line between zones.

- `ax.scatter(x, y, s, color, edgecolors, ...)`
  Draws points for zones and drones. `s` is marker size in points^2.

- `ax.text(x, y, text, ...)`
  Writes zone names and drone labels.

- `ax.autoscale()`
  Auto-fits the view to the drawn elements.

- `ax.set_xlim`, `ax.set_ylim`
  Adds padding beyond the autoscaled bounds so markers do not touch edges.

- `fig.canvas.draw_idle()`
  Asks matplotlib to redraw when it is idle (avoids redundant redraws).

- `animation.FuncAnimation(fig, func, interval, repeat)`
  Runs an animation by repeatedly calling `func` on a timer.

## Why We Multiply and Offset Values

### Drone stacking offsets
When multiple drones share the same logical place, their markers would overlap.
To avoid this, we offset each drone by a small grid:

- `x += ((count - 1) % 3 - 1) * 0.22`
- `y += ((count - 1) // 3) * 0.22`

Explanation:
- `count` is how many drones are already at that place.
- `((count - 1) % 3 - 1)` cycles through `-1, 0, 1` to spread drones across a
  3-column mini-grid.
- `((count - 1) // 3)` moves to the next row after every 3 drones.
- `0.22` is the spacing scale chosen to separate markers without pushing them
  too far away from the zone/edge position.

### Label vertical offset for zones
The label y-offset uses `p = 0.2` or `-0.2` to alternate label positions:
- This reduces label overlap when nodes are close.
- Alternating above and below the point improves readability.

## Data Shapes at a Glance

- `states`: `list[dict[int, tuple[Any, ...]]]`
  - Index = turn
  - Key = drone id
  - Value = place tuple

- `place`:
  - `( "zone", zone_name )`
  - `( "edge", from_zone_name, to_zone_name )`

## Summary

The display system is a single stateful class that:
- Precomputes the per-turn positions for all drones.
- Renders the full scene from scratch every time the turn changes.
- Provides interactive controls to step or animate through the history.
- Uses small, intentional offsets to keep the visualization readable.
