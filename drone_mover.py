from graph_builder_test import ZoneType
import sys
import time


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
        connection_key = tuple(sorted((start_point, end_point))) # A -> B it is the same as B -> A so that's why i always sorte to get the same connection (avoid duplication)
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
            paths_obj.append(Path(list(p), min_capacity))
        return paths_obj

    def get_strategy(self):
        paths_obj = self.create_paths_objects()
        for drone in self.drones:
            best_arrival = sys.maxsize
            best_path = None
            for path in paths_obj:
                enter_turn = (path.sent_drones // path.capacity) + 1 # check in wish turn this drone will start in this path
                arrival = enter_turn + self.calculate_path_cost(path.path) # check the arrival of this drone in this path
                if arrival <= best_arrival:
                    best_path = path
                    best_arrival = arrival
            drone.path = best_path.path
            best_path.sent_drones += 1

    def drone_mover(self):
        print("\n\n")
        print("Simulation Starts\n")
        self.get_strategy() # assign to each drone path 
        history_lines = [] # list to store history of moving for display part
        self.graph.start.current_drones = self.drones_numebr # assign the drone number to start zone
        while self.graph.end.current_drones != self.drones_numebr:
            # sort drones by position to start by the front drones
            priority_drones = sorted(self.drones, key=lambda drone: drone.my_position, reverse=True)

            future_occupancy = {} # list to store current drones on each zone
            for zone_name, zone in self.graph.zones.items():
                future_occupancy[zone_name] = zone.current_drones

            planned_moves = [] # to store turn moves

            for drone in priority_drones: # ignore delivered drones
                if drone.my_state == "DELIVERED":
                    continue

                if drone.my_position + 1 >= len(drone.path): # check if the drone in the end zone to change it's state to delivered
                    drone.my_state = "DELIVERED"
                    continue

                current = self.graph.zones[drone.path[drone.my_position]]
                to_move = self.graph.zones[drone.path[drone.my_position + 1]]
                connection = self.bring_connections(current.name, to_move.name) # get connection of the current with the goal
                if future_occupancy[to_move.name] < to_move.max_drones: # check if the zone still have places
                    if self.is_restricted(to_move): # check if the drone restricted so it will take two turns
                        if drone.my_state == "IN_TRANSITE":
                            planned_moves.append((drone, "IN_TRANSITE", to_move)) # move the drone from the connection to the goal zone and add it to the list
                            print(f"D{drone.id}-{to_move}",end=" ")
                            drone.my_state = "WAITING"  # change the state to waiting
                            future_occupancy[to_move.name] += 1 # change current drones on the zone
                            connection.current_drones -= 1        # remove the drone from the connection
                        elif connection.current_drones < connection.max_capacity: # check if the connection have a place to hold the drone or not
                            if connection.current_drones < to_move.max_drones:
                                planned_moves.append((drone, current, "IN_TRANSITE")) # move the drone to the connection
                                print(f"D{drone.id}-{current}-{to_move}",end=" ") 
                                drone.my_state = "IN_TRANSITE" # change the state to in Transite
                                future_occupancy[current.name] -= 1 # update zone current drones
                                connection.current_drones += 1    # update connection current drones
                    else: # if the zone to move to is normal 
                        planned_moves.append((drone, current, to_move)) # move the drone easly to the zone
                        future_occupancy[to_move.name] += 1 # update current drones on the zone
                        print(f"D{drone.id}-{to_move}", end=" ")

                        future_occupancy[current.name] -= 1 # update the current drones on the current zone
                        drone.my_state = "WAITING" # change the state to waiting

            self.drones_history.append(planned_moves)
            # applicate the planned moves
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
            print()
            if self.drones_numebr <= 30:
                time.sleep(0.1)
            if not planned_moves:
                raise RuntimeError("No drone could move this turn; check the path strategy or zone capacities")
        print("=> Drones Arrived Correctly")
        return self.drones_history
