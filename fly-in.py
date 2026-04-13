from enum  import Enum
import graph_builder_test

class ZoneType(Enum):
    NORMAL = "NORMAL"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    PRIORITY = "PRIORITY"

class DroneState(Enum):
    WAITING = "WAITING"
    FLYING = "FLYING"
    IN_TRANSITE = "IN_TRANSITE"

class Zone():
    def __init__(self, name, x, y, zone_type, color, current_drones, max_drones):
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.current_drones = current_drones
        self.max_drones = max_drones


class Connection():
    def __init__(self, from_hub, to_hub, max_link_capacity, current_drones):
        self.from_hub = from_hub
        self.to_hub = to_hub
        self.max_link_capacity = max_link_capacity
        self.current_drones = current_drones

class Graph():
    def __init__(self):
        self.hubs = []
        self.connections = []
    
class Drone():
    def __init__(self, id, state, current_hub, path, turns_transit):
        self.id = id
        self.state = state
        self.current_hub = current_hub
        self.path = []
        self.turns_transit = turns_transit


graph, nb_drones = graph_builder_test.build_graph()
for i in graph.connections:
    print(f"{i.zone_a.neighbors} linked with {i.zone_b.neighbors}")
    
print(graph.connections[0].zone_a)