_This project has been created as part of the 42 curriculum by yelgoumr._

# Fly-in

## Description

Fly-in is a drone routing and simulation project. The goal is to move a fleet of drones from a start hub to an end hub through a graph of connected hubs while respecting map constraints such as blocked zones, restricted zones, hub capacity, and link capacity.

The program reads a map file, builds an internal graph, searches for efficient routes, assigns drones to selected paths, simulates the movement turn by turn, and displays the result with an interactive visual map.

The project is inspired by classic pathfinding and flow problems: the challenge is not only to find a path, but to coordinate several drones so they do not exceed the capacity of zones or connections.

## Instructions

### Requirements

- Python 3
- `pip`
- Python packages listed in `requirements.txt`

Install dependencies:

```sh
make install
```

This runs:

```sh
python3 -m pip install -r requirements.txt
```

### Run

Start the program with:

```sh
make
```

or:

```sh
make run
```

The program opens an interactive prompt where you can choose one of the provided maps:

- `e1` to `e4`: easy maps
- `m1` to `m3`: medium maps
- `h1` to `h3`: hard maps
- `c1`: challenger map
- `0`: custom map path inside the `maps/` directory

Example custom map input:

```text
easy/01_linear_path.txt
```

### Debug

Run with Python debugger:

```sh
make debug
```

### Clean

Remove Python cache files:

```sh
make clean
```

## Map Format

Maps are stored in the `maps/` directory. A map describes:

- the number of drones
- the start hub
- the end hub
- intermediate hubs
- connections between hubs
- optional metadata for hub type, color, capacity, and link capacity

Example:

```text
nb_drones: 2

start_hub: start 0 0 [color=green max_drones=2]
hub: waypoint1 1 0 [zone=restricted color=blue]
hub: waypoint2 2 0 [zone=restricted color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1 [max_link_capacity=2]
connection: waypoint1-waypoint2 [max_link_capacity=2]
connection: waypoint2-goal
```

Supported zone types:

- `normal`: standard movement cost
- `priority`: preferred when path costs are close
- `restricted`: slower movement, requiring an in-transit step
- `blocked`: unavailable for routing

Supported metadata:

- `color=<name>` for visual display
- `max_drones=<number>` for hub capacity
- `max_link_capacity=<number>` for connection capacity

## Algorithm Choices and Implementation Strategy

### Graph Construction

The parser reads the selected map file and validates its structure. It rejects invalid metadata, duplicate hubs, duplicate connections, missing required fields, and connections that reference undefined hubs.

After parsing, the graph builder creates:

- `Zone` objects for hubs
- `Connection` objects for undirected links
- `Drone` objects for each drone in the simulation

Connections are stored as bidirectional neighbor relationships because drones can move across a link in either direction.

### Path Search

Path discovery is implemented in `path_finder.py` using a priority queue with `heapq`, following a Dijkstra-style search strategy.

The search prioritizes paths using:

- total movement cost
- zone priority
- path length
- zone name as a stable tie-breaker

Blocked zones are ignored, and cycles are avoided by refusing to revisit a zone already present in the current path.

The search keeps several good paths instead of only one. The maximum number of selected paths is limited by the number of drones, with an upper bound of 4 paths. This gives the simulator alternatives for distributing drones across the graph while keeping the search small and predictable.

### Path Cost Model

The movement model uses simple costs:

- normal and priority zones cost 1
- restricted zones cost 2
- blocked zones are excluded from valid movement

Restricted zones are more expensive because entering them takes two simulation phases: the drone first enters the connection as `IN_TRANSITE`, then reaches the restricted zone on a later turn.

### Drone Assignment Strategy

Before the simulation starts, each drone is assigned to one of the discovered paths. The assignment estimates when the drone would arrive if placed on each path.

For every candidate path, the program considers:

- the number of drones already assigned to that path
- the path capacity
- the calculated path cost

The drone is assigned to the path with the best estimated arrival time. This helps spread drones across multiple routes instead of forcing all drones through the same bottleneck.

### Turn-Based Movement

The simulator moves drones turn by turn until every drone reaches the end hub.

Each turn:

- drones closer to the destination move first
- future zone occupancy is calculated before applying moves
- hub capacity is checked
- connection capacity is checked
- restricted-zone transit is handled separately
- valid moves are recorded in a history list

The history is later reused by the visualizer, so the display represents the exact simulation that was executed.

### Connection Cache

Connections are undirected, so the program stores connection lookups with a sorted key:

```python
tuple(sorted((start_point, end_point)))
```

This means `A-B` and `B-A` resolve to the same cached connection and avoids duplicate lookup work.

## Visual Representation

The visual output is implemented with `matplotlib`.

After the simulation finishes, the display opens an interactive window showing:

- hubs positioned according to their map coordinates
- links between connected hubs
- zone colors from the map metadata
- drone positions for the current turn
- drones on links while they are in transit
- a turn counter
- `Back` and `Next` buttons for step-by-step navigation

This improves the user experience by making the simulation easier to understand than terminal output alone. Instead of only reading movement logs, users can inspect bottlenecks, capacity conflicts, restricted-zone delays, and path choices visually.

The visualizer also offsets drones that occupy the same hub or link, making crowded states easier to read.

## Project Structure

```text
.
├── fly-in.py              # Main entry point and map selector
├── graph_builder_test.py  # Graph, zone, connection, and drone models
├── path_finder.py         # Path search logic
├── drone_mover.py         # Drone assignment and turn simulation
├── display.py             # Matplotlib visual representation
├── parser/
│   └── parser.py          # Map parser and validation
├── maps/                  # Provided test maps
├── requirements.txt       # Python dependencies
└── makefile               # Common commands
```

## Resources

Classic references related to the project:

- Python documentation: `heapq` priority queue module
- Python documentation: `enum` module
- Matplotlib documentation: plotting, scatter plots, and widgets
- Dijkstra's shortest path algorithm
- Graph traversal concepts: weighted graphs, cycles, and adjacency lists
- Multi-agent pathfinding concepts
- Flow and capacity constraints in graphs

AI usage:

- AI was used to help draft and organize this README in English according to the required 42 curriculum structure.

- AI was used to review and suggest improvements to the code, including refactoring for readability, adding comments, and optimizing certain functions.

- AI was used to generate test cases and edge cases for the map parser and pathfinding logic, ensuring robustness against invalid input and complex graph structures.
