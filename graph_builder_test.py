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
    start       = Zone("start",      0, 0, zone_type=ZoneType.NORMAL)
    loop_a      = Zone("loop_a",     1, 0, zone_type=ZoneType.RESTRICTED)
    loop_b      = Zone("loop_b",     2, 0, zone_type=ZoneType.RESTRICTED)
    loop_c      = Zone("loop_c",     2, 1, zone_type=ZoneType.RESTRICTED)
    loop_d      = Zone("loop_d",     1, 1, zone_type=ZoneType.RESTRICTED)
    exit_point  = Zone("exit_point", 3, 0, zone_type=ZoneType.NORMAL)
    goal        = Zone("goal",       4, 0, zone_type=ZoneType.NORMAL)

    # ===== Add zones =====
    for z in [start, loop_a, loop_b, loop_c, loop_d, exit_point, goal]:
        graph.add_zone(z)

    graph.start = start
    graph.end   = goal

    # ===== Connections =====
    graph.connect("start",      "loop_a")
    graph.connect("loop_a",     "loop_b")
    graph.connect("loop_b",     "loop_c")
    graph.connect("loop_c",     "loop_d")
    graph.connect("loop_d",     "loop_a")   # closes the circular loop
    graph.connect("loop_b",     "exit_point")
    graph.connect("exit_point", "goal")

    # ===== Heuristic =====
    graph.heuristic()

    return graph, 6
