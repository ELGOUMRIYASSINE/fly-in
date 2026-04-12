from enum  import Enum

class ZoneType(Enum):
    NORMAL = "NORMAL"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    PRIORITY = "PRIORITY"

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
    def __init__(self, from_hub, to_hub, max_link_capacity, ):
        