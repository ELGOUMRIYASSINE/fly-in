from __future__ import annotations
from enum import Enum
from typing import Dict, List
import math


# ---------------- ENUM ----------------
class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

class Drone():
    def __init__(self, id, state, current_hub, path, turns_transit):
        self.id = id
        self.state = state
        self.current_hub = current_hub
        self.path = []
        self.turns_transit = turns_transit
        self.my_path = path
        self.my_position = 0
        self.my_state = "WAITING"


# ---------------- ZONE ----------------
class Zone:
    zone_state_cost = {"NORMAL":1, "BLOCKED":9999999, "RESTRICTED":2, "PRIORITY":0.9}
    zone_move_state = ["WAITING", "IN_TRANSITE", "DELIVERED"]
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        parent_zone: Zone = None,
        distance_to_goal: int = 0,
        zone_type: ZoneType = ZoneType.NORMAL,
        total_cost: int = None,
        color: str | None = None,
        max_link_capacity_drones: int = 1
    ):
        self.name: str = name
        self.distance_to_goal: int = distance_to_goal
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.zone_cost = self.zone_state_cost[self.zone_type.name]
        self.total_cost = total_cost
        self.color: str | None = color
        self.max_link_capacity_drones: int = max_link_capacity_drones
        self.current_drones: int = 0
        self.military = []
        self.neighbors: List["Zone"] = []

    def add_neighbor(self, zone: "Zone") -> None:
        self.neighbors.append(zone)

    def __repr__(self) -> str:
        return f"{self.name}"


# ---------------- CONNECTION ----------------
class Connection:
    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_link_capacity_capacity: int = 1
    ):
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_link_capacity_capacity: int = max_link_capacity_capacity
        self.current_usage: int = 0

    def __repr__(self) -> str:
        return f"{self.zone_a.name} <-> {self.zone_b.name}"


# ---------------- GRAPH ----------------
class Graph:
    def __init__(self):
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start: Zone | None = None
        self.end: Zone | None = None
        self.drones = []
        self.zones_total_cost = {}

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def connect(self, name_a: str, name_b: str, capacity: int = 1) -> None:
        a = self.zones[name_a]
        b = self.zones[name_b]

        a.add_neighbor(b)
        b.add_neighbor(a)
        self.connections.append(Connection(a, b, capacity))
    def heuristic(self) -> list[int]:
        for zone in self.zones.values():
            zone.distance_to_goal = round(math.sqrt((self.end.x - zone.x)**2 + (self.end.y - zone.y)**2), 2)
    def create_drones(self, drones_number):
        for i in range(drones_number):
            self.drones.append(Drone(i, "WAITING", self.start.name, None, 0))
    # def path_giver(self, path):



def build_graph():
    graph = Graph()

    # ===== Zones =====

    # Layer 0 — Start & bottleneck gates
    start        = Zone("start",        0,  9,  zone_type=ZoneType.NORMAL,     max_drones=25)
    gate_hell1   = Zone("gate_hell1",   1,  0,  zone_type=ZoneType.NORMAL,     max_drones=1)
    gate_hell2   = Zone("gate_hell2",   2,  0,  zone_type=ZoneType.NORMAL)
    gate_hell3   = Zone("gate_hell3",   3,  3,  zone_type=ZoneType.NORMAL,     max_drones=1)
    gate_hell4   = Zone("gate_hell4",   4,  0,  zone_type=ZoneType.NORMAL,     max_drones=1)
    gate_hell5   = Zone("gate_hell5",   5,  0,  zone_type=ZoneType.NORMAL,     max_drones=1)

    # Layer 1 — Maze of Despair
    maze_trap_a1 = Zone("maze_trap_a1", 1,  1,  zone_type=ZoneType.NORMAL)
    maze_trap_a2 = Zone("maze_trap_a2", 2,  1,  zone_type=ZoneType.NORMAL)
    maze_trap_a3 = Zone("maze_trap_a3", 3,  1,  zone_type=ZoneType.NORMAL)
    maze_dead_a  = Zone("maze_dead_a",  4, -1,  zone_type=ZoneType.NORMAL)  # dead end

    maze_trap_b1 = Zone("maze_trap_b1", 1, -1,  zone_type=ZoneType.NORMAL)
    maze_trap_b2 = Zone("maze_trap_b2", 2, -1,  zone_type=ZoneType.NORMAL)
    maze_trap_b3 = Zone("maze_trap_b3", 3, -1,  zone_type=ZoneType.NORMAL)
    maze_dead_b  = Zone("maze_dead_b",  4, -1,  zone_type=ZoneType.NORMAL)  # dead end (same coords as maze_dead_a — intentional in source)

    maze_loop1   = Zone("maze_loop1",   1,  2,  zone_type=ZoneType.NORMAL)
    maze_loop2   = Zone("maze_loop2",   2,  2,  zone_type=ZoneType.RESTRICTED)
    maze_loop3   = Zone("maze_loop3",   3,  2,  zone_type=ZoneType.RESTRICTED)
    maze_loop4   = Zone("maze_loop4",   4,  2,  zone_type=ZoneType.RESTRICTED)
    maze_loop5   = Zone("maze_loop5",   5,  2,  zone_type=ZoneType.RESTRICTED)
    maze_loop6   = Zone("maze_loop6",   5,  1,  zone_type=ZoneType.RESTRICTED)

    # Layer 2 — Capacity Nightmare
    micro_gate1      = Zone("micro_gate1",      6,  0,         zone_type=ZoneType.NORMAL,     max_drones=1)
    micro_gate2      = Zone("micro_gate2",      7,  0,         zone_type=ZoneType.NORMAL,     max_drones=1)
    micro_gate3      = Zone("micro_gate3",      8,  0,         zone_type=ZoneType.NORMAL,     max_drones=1)

    overflow_hell1   = Zone("overflow_hell1",   6,  1,         zone_type=ZoneType.RESTRICTED,  max_drones=2)
    overflow_hell2   = Zone("overflow_hell2",   7,  1,         zone_type=ZoneType.RESTRICTED,  max_drones=2)
    overflow_hell3   = Zone("overflow_hell3",   8,  1,         zone_type=ZoneType.RESTRICTED,  max_drones=2)
    overflow_hell4   = Zone("overflow_hell4",   6, -1,         zone_type=ZoneType.RESTRICTED,  max_drones=2)
    overflow_hell5   = Zone("overflow_hell5",   7, -1,         zone_type=ZoneType.RESTRICTED,  max_drones=2)
    overflow_hell6   = Zone("overflow_hell6",   8,  900000000, zone_type=ZoneType.RESTRICTED,  max_drones=2)

    # Layer 3 — False Hope
    false_hope1      = Zone("false_hope1",      9,  0,  zone_type=ZoneType.PRIORITY,  max_drones=3)
    false_hope2      = Zone("false_hope2",      10, 0,  zone_type=ZoneType.PRIORITY,  max_drones=2)
    false_hope3      = Zone("false_hope3",      11, 0,  zone_type=ZoneType.PRIORITY,  max_drones=1)

    priority_trap1   = Zone("priority_trap1",   9,  1,  zone_type=ZoneType.PRIORITY)
    priority_trap2   = Zone("priority_trap2",   10, 1,  zone_type=ZoneType.PRIORITY)
    priority_dead    = Zone("priority_dead",    11, 1,  zone_type=ZoneType.NORMAL)   # dead end

    priority_trap3   = Zone("priority_trap3",   9, -1,  zone_type=ZoneType.PRIORITY)
    priority_trap4   = Zone("priority_trap4",   10,-1,  zone_type=ZoneType.PRIORITY)
    priority_dead2   = Zone("priority_dead2",   11,-1,  zone_type=ZoneType.NORMAL)   # dead end

    # Layer 4 — Convergence Hell
    conv_restricted1 = Zone("conv_restricted1", 12,  2,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted2 = Zone("conv_restricted2", 13,  2,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted3 = Zone("conv_restricted3", 14,  2,  zone_type=ZoneType.RESTRICTED, max_drones=1)

    conv_restricted4 = Zone("conv_restricted4", 12,  0,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted5 = Zone("conv_restricted5", 13,  0,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted6 = Zone("conv_restricted6", 14,  0,  zone_type=ZoneType.RESTRICTED, max_drones=1)

    conv_restricted7 = Zone("conv_restricted7", 12, -2,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted8 = Zone("conv_restricted8", 13, -2,  zone_type=ZoneType.RESTRICTED, max_drones=1)
    conv_restricted9 = Zone("conv_restricted9", 14, -2,  zone_type=ZoneType.RESTRICTED, max_drones=1)

    # Layer 5 — Final Gauntlet
    final_merge      = Zone("final_merge",      15, 0,  zone_type=ZoneType.NORMAL,     max_drones=5)
    final_torture1   = Zone("final_torture1",   16, 0,  zone_type=ZoneType.NORMAL,     max_drones=2)
    final_torture2   = Zone("final_torture2",   17, 0,  zone_type=ZoneType.NORMAL,     max_drones=1)
    final_torture3   = Zone("final_torture3",   18, 0,  zone_type=ZoneType.NORMAL,     max_drones=1)
    final_torture4   = Zone("final_torture4",   19, 0,  zone_type=ZoneType.NORMAL,     max_drones=1)
    final_torture5   = Zone("final_torture5",   20, 0,  zone_type=ZoneType.NORMAL,     max_drones=1)

    # Goal
    impossible_goal  = Zone("impossible_goal",  21, 0,  zone_type=ZoneType.NORMAL,     max_drones=25)

    # ===== Add zones =====
    all_zones = [
        start,
        gate_hell1, gate_hell2, gate_hell3, gate_hell4, gate_hell5,
        maze_trap_a1, maze_trap_a2, maze_trap_a3, maze_dead_a,
        maze_trap_b1, maze_trap_b2, maze_trap_b3, maze_dead_b,
        maze_loop1, maze_loop2, maze_loop3, maze_loop4, maze_loop5, maze_loop6,
        micro_gate1, micro_gate2, micro_gate3,
        overflow_hell1, overflow_hell2, overflow_hell3,
        overflow_hell4, overflow_hell5, overflow_hell6,
        false_hope1, false_hope2, false_hope3,
        priority_trap1, priority_trap2, priority_dead,
        priority_trap3, priority_trap4, priority_dead2,
        conv_restricted1, conv_restricted2, conv_restricted3,
        conv_restricted4, conv_restricted5, conv_restricted6,
        conv_restricted7, conv_restricted8, conv_restricted9,
        final_merge,
        final_torture1, final_torture2, final_torture3, final_torture4, final_torture5,
        impossible_goal,
    ]
    for z in all_zones:
        graph.add_zone(z)

    graph.start = start
    graph.end   = impossible_goal

    # ===== Connections =====

    # Layer 0 — bottleneck gates (max_link_capacity=1 on each)
    graph.connect("start",      "gate_hell1",  max_link_capacity=1)
    # NOTE: "connection: -" in source is malformed/intentional noise — skipped
    graph.connect("gate_hell2", "gate_hell3",  max_link_capacity=1)
    graph.connect("gate_hell3", "gate_hell4",  max_link_capacity=1)
    graph.connect("gate_hell4", "gate_hell5",  max_link_capacity=1)

    # Layer 1 — Maze of Despair
    graph.connect("gate_hell1", "maze_trap_a1")
    graph.connect("gate_hell2", "maze_trap_b1")
    graph.connect("gate_hell3", "maze_loop1")

    graph.connect("maze_trap_a1", "maze_trap_a2")
    graph.connect("maze_trap_a2", "maze_trap_a3")
    graph.connect("maze_trap_a3", "maze_dead_a")     # dead end

    graph.connect("maze_trap_b1", "maze_trap_b2")
    graph.connect("maze_trap_b2", "maze_trap_b3")
    graph.connect("maze_trap_b3", "maze_dead_b")     # dead end

    graph.connect("maze_loop1", "maze_loop2")        # loop
    graph.connect("maze_loop2", "maze_loop3")
    graph.connect("maze_loop3", "maze_loop4")
    graph.connect("maze_loop4", "maze_loop5")
    graph.connect("maze_loop5", "maze_loop6")
    graph.connect("maze_loop6", "maze_loop1")        # back-edge: closes the loop

    # Escape routes from maze
    graph.connect("maze_trap_a2", "micro_gate1")
    graph.connect("maze_trap_b2", "micro_gate1")
    graph.connect("maze_loop3",   "micro_gate2")

    # Layer 2 — Capacity Nightmare
    graph.connect("gate_hell5",  "micro_gate1")
    graph.connect("micro_gate1", "micro_gate2")
    graph.connect("micro_gate2", "micro_gate3")

    # Overflow connections
    graph.connect("micro_gate1", "overflow_hell1")
    graph.connect("micro_gate2", "overflow_hell2")
    graph.connect("micro_gate3", "overflow_hell3")
    graph.connect("micro_gate1", "overflow_hell4")
    graph.connect("micro_gate2", "overflow_hell5")
    graph.connect("micro_gate3", "overflow_hell6")

    graph.connect("overflow_hell1", "overflow_hell2")
    graph.connect("overflow_hell2", "overflow_hell3")
    graph.connect("overflow_hell4", "overflow_hell5")
    graph.connect("overflow_hell5", "overflow_hell6")

    graph.connect("overflow_hell3", "false_hope1")
    graph.connect("overflow_hell6", "false_hope1")

    # Layer 3 — False Hope
    graph.connect("micro_gate3",  "false_hope1")
    graph.connect("false_hope1",  "false_hope2")
    graph.connect("false_hope2",  "false_hope3")

    graph.connect("false_hope1", "priority_trap1")
    graph.connect("false_hope2", "priority_trap2")
    graph.connect("false_hope3", "priority_dead")    # dead end

    graph.connect("false_hope1", "priority_trap3")
    graph.connect("false_hope2", "priority_trap4")
    graph.connect("false_hope3", "priority_dead2")   # dead end

    graph.connect("priority_trap1", "priority_trap2")
    graph.connect("priority_trap3", "priority_trap4")

    # Layer 4 — Convergence Hell
    graph.connect("false_hope3", "conv_restricted1")
    graph.connect("false_hope3", "conv_restricted4")
    graph.connect("false_hope3", "conv_restricted7")

    graph.connect("conv_restricted1", "conv_restricted2")
    graph.connect("conv_restricted2", "conv_restricted3")
    graph.connect("conv_restricted4", "conv_restricted5")
    graph.connect("conv_restricted5", "conv_restricted6")
    graph.connect("conv_restricted7", "conv_restricted8")
    graph.connect("conv_restricted8", "conv_restricted9")

    graph.connect("conv_restricted3", "final_merge")
    graph.connect("conv_restricted6", "final_merge")
    graph.connect("conv_restricted9", "final_merge")

    # Layer 5 — Final Gauntlet
    graph.connect("final_merge",    "final_torture1")
    graph.connect("final_torture1", "final_torture2")
    graph.connect("final_torture2", "final_torture3")
    graph.connect("final_torture3", "final_torture4")
    graph.connect("final_torture4", "final_torture5")
    graph.connect("final_torture5", "impossible_goal")

    # Emergency bypass routes
    graph.connect("overflow_hell1", "conv_restricted1")
    graph.connect("overflow_hell4", "conv_restricted7")
    graph.connect("priority_trap1", "conv_restricted4")

    # ===== Heuristic =====
    graph.heuristic()

    return graph, 25
