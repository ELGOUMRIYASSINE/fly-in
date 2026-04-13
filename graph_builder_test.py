from enum import Enum
from typing import Dict, List


# ---------------- ENUM ----------------
class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


# ---------------- ZONE ----------------
class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1
    ):
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: str | None = color
        self.max_drones: int = max_drones
        self.current_drones: int = 0
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
        max_capacity: int = 1
    ):
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_capacity: int = max_capacity
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

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def connect(self, name_a: str, name_b: str, capacity: int = 1) -> None:
        a = self.zones[name_a]
        b = self.zones[name_b]

        a.add_neighbor(b)
        b.add_neighbor(a)

        self.connections.append(Connection(a, b, capacity))


# ---------------- BUILD GRAPH ----------------
def build_graph() -> tuple[Graph, int]:
    graph = Graph()

    # Create zones
    start = Zone("start", 0, 0, color="green", max_drones=9999)  # start = unlimited
    junction = Zone("junction", 1, 0, color="yellow", max_drones=2)
    path_a = Zone("path_a", 2, 1, color="blue", max_drones=1)
    path_b = Zone("path_b", 2, -1, color="blue", max_drones=1)
    goal = Zone("goal", 3, 0, color="red", max_drones=3)

    # Add zones to graph
    for zone in [start, junction, path_a, path_b, goal]:
        graph.add_zone(zone)

    # Define start & end
    graph.start = start
    graph.end = goal

    # Create connections
    graph.connect("start", "junction")
    graph.connect("junction", "path_a")
    graph.connect("junction", "path_b")
    graph.connect("path_a", "goal")
    graph.connect("path_b", "goal")

    nb_drones = 3

    return graph, nb_drones