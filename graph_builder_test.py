from __future__ import annotations
from enum import Enum
from typing import Dict, List
import math
from parser import parser


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

class Zone:
    zone_state_cost = {"NORMAL":1, "BLOCKED":9999999, "RESTRICTED":2, "PRIORITY":0.9}
    zone_move_state = ["WAITING", "IN_TRANSITE", "DELIVERED"]
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: str | None = None,
        zone_type: ZoneType = ZoneType.NORMAL,
        max_drones: int = None,
        total_cost: int = None
    ):
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.zone_cost = self.zone_state_cost[self.zone_type.upper()]
        # self.total_cost = total_cost
        self.color: str | None = color
        self.max_drones: int = max_drones
        self.current_drones: int = 0
        self.neighbors: List["Zone"] = []
        self.drones_in_station = []

    def add_neighbor(self, zone: "Zone") -> None:
        self.neighbors.append(zone)

    def __repr__(self) -> str:
        return f"{self.name}"

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
        self.current_drones: int = 0
        self.drones_in_station = []

    def __repr__(self) -> str:
        return f"{self.zone_a.name} <-> {self.zone_b.name}"

class Graph:
    def __init__(self):
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start: Zone | None = None
        self.end: Zone | None = None
        self.drones = []
        self.nb_drones = 0

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def connect(self, name_a: str, name_b: str, capacity: int = 1) -> None:
        a = self.zones[name_a]
        b = self.zones[name_b]

        a.add_neighbor(b)
        b.add_neighbor(a)
        self.connections.append(Connection(a, b, capacity))
    
    def create_drones(self, drones_number):
        for i in range(drones_number):
            self.drones.append(Drone(i, "WAITING", self.start.name, None))

    def build_graph(self):
        map = input("enter the map name: ")
        parsed_data = parser.parser(map)

        for hub in parsed_data["hubs"]:
            self.add_zone(Zone(hub["name"], hub["coordinates"][0], hub["coordinates"][1], hub['zone']['color'], hub['zone']['type'], hub['zone']['max_drones']))
        for connection in parsed_data["connections"]:
            self.connect(connection["from"], connection["to"], connection['max_link_capacity'])
        self.start = self.zones.get(parsed_data["start_hub"])
        self.end   = self.zones.get(parsed_data["end_hub"])
        self.nb_drones = int(parsed_data["nb_drones"])
        self.create_drones(self.nb_drones)
