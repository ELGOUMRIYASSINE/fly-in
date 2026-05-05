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
    def __init__(self, id, state, current_hub, path):
        self.id = id
        self.state = state
        self.current_hub = current_hub
        self.path = []
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
        max_drones: int = 1
    ):
        self.name: str = name
        self.distance_to_goal: int = distance_to_goal
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.zone_cost = self.zone_state_cost[self.zone_type.name]
        self.total_cost = total_cost
        self.color: str | None = color
        self.max_drones: int = max_drones
        self.current_drones: int = 0
        self.neighbors: List["Zone"] = []
        self.drones_in_station = []

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
        max_capacity: int = 1
    ):
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_capacity: int = max_capacity
        self.current_usage: int = 0
        self.current_drones = []

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
            self.drones.append(Drone(i, "WAITING", self.start.name, None))
    # def path_giver(self, path):



def build_graph():
    graph = Graph()

    # ===== Zones =====
    start           = Zone("start",           0,  0,  zone_type=ZoneType.NORMAL,   max_drones=15)

    # Layer 1: Distribution gates
    dist_gate1      = Zone("dist_gate1",      1,  0,  zone_type=ZoneType.NORMAL,   max_drones=1)
    dist_gate2      = Zone("dist_gate2",      1,  1,  zone_type=ZoneType.NORMAL,   max_drones=1)
    dist_gate3      = Zone("dist_gate3",      1,  -1, zone_type=ZoneType.NORMAL,   max_drones=1)

    # Layer 2: Dead end maze with loops
    maze_trap1      = Zone("maze_trap1",      2,  2,  zone_type=ZoneType.NORMAL)
    maze_trap2      = Zone("maze_trap2",      3,  2,  zone_type=ZoneType.NORMAL)
    maze_loop1      = Zone("maze_loop1",      2,  1,  zone_type=ZoneType.RESTRICTED)
    maze_loop2      = Zone("maze_loop2",      3,  1,  zone_type=ZoneType.RESTRICTED)
    maze_loop3      = Zone("maze_loop3",      4,  1,  zone_type=ZoneType.RESTRICTED)
    maze_loop4      = Zone("maze_loop4",      4,  2,  zone_type=ZoneType.RESTRICTED)
    maze_correct    = Zone("maze_correct",    2,  0,  zone_type=ZoneType.NORMAL)

    # Layer 3: Capacity nightmare
    bottleneck1     = Zone("bottleneck1",     3,  0,  zone_type=ZoneType.NORMAL,   max_drones=2)
    bottleneck2     = Zone("bottleneck2",     4,  0,  zone_type=ZoneType.NORMAL,   max_drones=1)
    overflow1       = Zone("overflow1",       3,  -1, zone_type=ZoneType.RESTRICTED, max_drones=3)
    overflow2       = Zone("overflow2",       4,  -1, zone_type=ZoneType.RESTRICTED, max_drones=3)

    # Layer 4: Priority puzzle
    priority_hub    = Zone("priority_hub",    5,  0,  zone_type=ZoneType.PRIORITY,  max_drones=4)
    priority_trap1  = Zone("priority_trap1",  5,  1,  zone_type=ZoneType.PRIORITY)
    priority_trap2  = Zone("priority_trap2",  6,  1,  zone_type=ZoneType.PRIORITY)
    priority_dead   = Zone("priority_dead_end", 6, 2, zone_type=ZoneType.NORMAL)
    priority_correct= Zone("priority_correct",6,  0,  zone_type=ZoneType.PRIORITY,  max_drones=3)

    # Layer 5: Multi-path convergence
    conv_restricted1= Zone("conv_restricted1",7,  0,  zone_type=ZoneType.RESTRICTED, max_drones=2)
    conv_restricted2= Zone("conv_restricted2",8,  0,  zone_type=ZoneType.RESTRICTED, max_drones=2)
    conv_normal1    = Zone("conv_normal1",    7,  -1, zone_type=ZoneType.NORMAL,   max_drones=3)
    conv_normal2    = Zone("conv_normal2",    8,  -1, zone_type=ZoneType.NORMAL,   max_drones=3)
    conv_priority1  = Zone("conv_priority1",  7,  1,  zone_type=ZoneType.PRIORITY,  max_drones=2)
    conv_priority2  = Zone("conv_priority2",  8,  1,  zone_type=ZoneType.PRIORITY,  max_drones=2)

    # Layer 6: Final gauntlet
    final_merge     = Zone("final_merge",     9,  0,  zone_type=ZoneType.NORMAL,   max_drones=8)
    final_gate1     = Zone("final_gate1",     10, 0,  zone_type=ZoneType.NORMAL,   max_drones=3)
    final_gate2     = Zone("final_gate2",     11, 0,  zone_type=ZoneType.NORMAL,   max_drones=2)
    final_gate3     = Zone("final_gate3",     12, 0,  zone_type=ZoneType.NORMAL,   max_drones=1)
    goal            = Zone("goal",            13, 0,  zone_type=ZoneType.NORMAL,   max_drones=15)

    # ===== Add zones =====
    for z in [
        start,
        dist_gate1, dist_gate2, dist_gate3,
        maze_trap1, maze_trap2, maze_loop1, maze_loop2,
        maze_loop3, maze_loop4, maze_correct,
        bottleneck1, bottleneck2, overflow1, overflow2,
        priority_hub, priority_trap1, priority_trap2,
        priority_dead, priority_correct,
        conv_restricted1, conv_restricted2,
        conv_normal1, conv_normal2,
        conv_priority1, conv_priority2,
        final_merge, final_gate1, final_gate2, final_gate3,
        goal
    ]:
        graph.add_zone(z)

    graph.start = start
    graph.end   = goal

    # ===== Connections =====

    # Layer 1
    graph.connect("start",          "dist_gate1")
    graph.connect("start",          "dist_gate2")
    graph.connect("start",          "dist_gate3")

    # Layer 2: maze
    graph.connect("dist_gate1",     "maze_correct")
    graph.connect("dist_gate2",     "maze_trap1")
    graph.connect("dist_gate3",     "maze_loop1")
    graph.connect("maze_trap1",     "maze_trap2")
    graph.connect("maze_loop1",     "maze_loop2")
    graph.connect("maze_loop2",     "maze_loop3")
    graph.connect("maze_loop3",     "maze_loop4")
    graph.connect("maze_loop4",     "maze_loop1")   # closes the loop
    graph.connect("maze_loop2",     "maze_correct")

    # Layer 3: capacity nightmare
    graph.connect("maze_correct",   "bottleneck1")
    graph.connect("bottleneck1",    "bottleneck2")
    graph.connect("bottleneck1",    "overflow1")
    graph.connect("overflow1",      "overflow2")
    graph.connect("overflow2",      "bottleneck2")

    # Layer 4: priority puzzle
    graph.connect("bottleneck2",    "priority_hub")
    graph.connect("priority_hub",   "priority_trap1")
    graph.connect("priority_hub",   "priority_correct")
    graph.connect("priority_trap1", "priority_trap2")
    graph.connect("priority_trap2", "priority_dead_end")
    graph.connect("priority_correct","conv_restricted1")
    graph.connect("priority_correct","conv_normal1")
    graph.connect("priority_correct","conv_priority1")

    # Layer 5: convergence
    graph.connect("conv_restricted1","conv_restricted2")
    graph.connect("conv_normal1",    "conv_normal2")
    graph.connect("conv_priority1",  "conv_priority2")
    graph.connect("conv_restricted2","final_merge")
    graph.connect("conv_normal2",    "final_merge")
    graph.connect("conv_priority2",  "final_merge")

    # Layer 6: final gauntlet
    graph.connect("final_merge",    "final_gate1")
    graph.connect("final_gate1",    "final_gate2")
    graph.connect("final_gate2",    "final_gate3")
    graph.connect("final_gate3",    "goal")

    # Emergency bypass
    graph.connect("overflow2",      "conv_normal1")
    graph.connect("priority_hub",   "conv_priority1")

    # ===== Heuristic =====
    graph.heuristic()

    return graph, 15
