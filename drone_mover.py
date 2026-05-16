from graph_builder_test import ZoneType
import sys


class Path():
    def __init__(self, path, capacity):
        self.length = len(path)
        self.capacity = capacity
        self.sent_drones = 0
        self.path = path
        self.my_position = 0
        self.drone_state = "WAITING"

class DroneMover():
    def __init__(self, graph, paths):
        self.drones_history = {}
        self.graph = graph
        self.drones_numebr = graph.nb_drones
        self.drones = graph.drones
        self.paths = paths
        self.turns = 0
        self.drones_history = []
        self.used_connections = {}

    def is_restricted(self, zone):
        return zone.zone_type == "restricted" or zone.zone_type == ZoneType.RESTRICTED

    def bring_connections(self, start_point, end_point):
        connection_key = tuple(sorted((start_point, end_point)))
        if connection_key in self.used_connections:
            return self.used_connections[connection_key]
        for connection in self.graph.connections:
            if {connection.zone_a.name, connection.zone_b.name} == {start_point, end_point}:
                self.used_connections[connection_key] = connection
                return connection
        raise RuntimeError(f"No connection found between {start_point} and {end_point}")

    def calculate_path_cost(self, path):
        path_cost = 0
        for zone in path:
            if self.is_restricted(self.graph.zones[zone]):
                path_cost += 2
            else:
                path_cost += 1
        return path_cost
    def create_paths_objects(self):
        paths_obj = []
        for p in self.paths:
            min_capacity = 9999999
            for zone in p:
                if self.graph.zones[zone].max_drones < min_capacity:
                    min_capacity = self.graph.zones[zone].max_drones
            paths_obj.append(Path(list(reversed(p)), min_capacity))
        return paths_obj
    def get_strategy(self):
        paths_obj = self.create_paths_objects()
        for drone in self.drones:
            best_arrival = sys.maxsize
            best_path = None
            for path in paths_obj:
                enter_turn = (path.sent_drones // path.capacity) + 1
                arrival = enter_turn + self.calculate_path_cost(path.path)
                if arrival <= best_arrival:
                    best_path = path
                    best_arrival = arrival
            drone.path = best_path.path
            best_path.sent_drones += 1
        

    def drone_mover(self):
        self.get_strategy()
        history_lines = []
        if self.graph.start.current_drones == 0:
            self.graph.start.current_drones = self.drones_numebr
        while self.graph.end.current_drones != self.drones_numebr:
            priority_drones = sorted(self.drones, key=lambda drone: drone.my_position, reverse=True)

            future_occupancy = {}
            for zone_name, zone in self.graph.zones.items():
                future_occupancy[zone_name] = zone.current_drones

            planned_moves = []

            for drone in priority_drones:

                if drone.my_state == "DELIVERED":
                    continue


                if drone.my_position + 1 >= len(drone.path):
                    drone.my_state = "DELIVERED"
                    continue

                current = self.graph.zones[drone.path[drone.my_position]]
                to_move = self.graph.zones[drone.path[drone.my_position + 1]]
                connection = self.bring_connections(current.name, to_move.name)
                if future_occupancy[to_move.name] < to_move.max_drones:
                    if self.is_restricted(to_move):
                        if drone.my_state == "IN_TRANSITE":
                            planned_moves.append((drone, "IN_TRANSITE", to_move))
                            drone.my_state = "WAITING"  
                            future_occupancy[to_move.name] += 1
                            connection.current_drones -= 1        
                        elif connection.current_drones < connection.max_capacity:
                            planned_moves.append((drone, current, "IN_TRANSITE"))
                            drone.my_state = "IN_TRANSITE"
                            future_occupancy[current.name] -= 1
                            connection.current_drones += 1        
                    else:
                        future_occupancy[to_move.name] += 1
                        planned_moves.append((drone, current, to_move))

                        future_occupancy[current.name] -= 1
                        drone.my_state = "WAITING"

                else:
                    if drone.my_state != "IN_TRANSITE":
                        drone.my_state = "WAITING"
            self.drones_history.append(planned_moves)
            for drone, current, to_move in planned_moves:

                if to_move != "IN_TRANSITE":
                    to_move.current_drones += 1
                    drone.my_position += 1
                    drone.my_state = "WAITING"

                if hasattr(current, 'current_drones'):
                    current.current_drones -= 1

                if hasattr(to_move, 'name'):
                    if to_move.name == self.graph.end.name:
                        drone.my_state = "DELIVERED"
            if planned_moves:
                history_lines.append(" ".join(
                    f"D{drone.id}-{getattr(to_move, 'name', to_move)}" for drone, _, to_move in planned_moves
                ))

            if not planned_moves:
                raise RuntimeError("No drone could move this turn; check the path strategy or zone capacities")
        return self.drones_history
