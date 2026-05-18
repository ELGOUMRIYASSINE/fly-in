from graph_builder_test import Connection, Drone, Graph, Zone
import sys
from typing import TypeAlias


MoveTarget: TypeAlias = Zone | str
PlannedMove: TypeAlias = tuple[Drone, MoveTarget, MoveTarget]


class Path:
    def __init__(self, path: list[str], capacity: int) -> None:
        self.length = len(path)
        self.capacity = capacity
        self.sent_drones = 0
        self.path = path
        self.my_position = 0
        self.drone_state = "WAITING"


class DroneMover:
    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        self.graph = graph
        self.drones_numebr = graph.nb_drones
        self.drones = graph.drones
        self.paths = paths
        self.turns = 0
        self.drones_history: list[list[PlannedMove]] = []
        self.used_connections: dict[tuple[str, str], Connection] = {}

    def is_restricted(self, zone: Zone) -> bool:
        return zone.zone_type == "restricted"

    def bring_connections(self, start_point: str, end_point: str) -> Connection:
        # A -> B and B -> A should resolve to the same connection key.
        sorted_points = sorted((start_point, end_point))
        connection_key = (sorted_points[0], sorted_points[1])
        if connection_key in self.used_connections:
            return self.used_connections[connection_key]
        for connection in self.graph.connections:
            if {connection.zone_a.name, connection.zone_b.name} == {start_point, end_point}:
                self.used_connections[connection_key] = connection
                return connection
        raise RuntimeError(f"No connection found between {start_point} and {end_point}")

    def calculate_path_cost(self, path: list[str]) -> int:
        path_cost = 0
        for zone in path:
            if self.is_restricted(self.graph.zones[zone]):
                path_cost += 2
            else:
                path_cost += 1
        return path_cost

    def create_paths_objects(self) -> list[Path]:
        paths_obj: list[Path] = []
        for p in self.paths:
            min_capacity = 9999999
            for zone in p:
                if self.graph.zones[zone].max_drones < min_capacity:
                    min_capacity = self.graph.zones[zone].max_drones
            paths_obj.append(Path(list(p), min_capacity))
        return paths_obj

    def get_strategy(self) -> None:
        paths_obj = self.create_paths_objects()
        if not paths_obj:
            raise RuntimeError("No valid path found for drones")
        for drone in self.drones:
            best_arrival = sys.maxsize
            best_path = paths_obj[0]
            for path in paths_obj:
                # check in wish turn this drone will start in this path
                enter_turn = (path.sent_drones // path.capacity) + 1
                # check the arrival of this drone in this path
                arrival = enter_turn + self.calculate_path_cost(path.path)
                if arrival <= best_arrival:
                    best_path = path
                    best_arrival = arrival
            drone.path = best_path.path
            best_path.sent_drones += 1

    def drone_mover(self) -> list[list[PlannedMove]]:
        print("\n\n")
        print("Simulation Starts\n")
        self.get_strategy()  # assign to each drone path
        history_lines: list[str] = []
        if self.graph.start is None or self.graph.end is None:
            raise RuntimeError("Graph is missing start or end hub")
        self.graph.start.current_drones = self.drones_numebr
        while self.graph.end.current_drones != self.drones_numebr:
            # sort drones by position to start by the front drones
            priority_drones = sorted(self.drones, key=lambda drone: drone.my_position, reverse=True)

            future_occupancy: dict[str, int] = {}  # list to store current drones on each zone
            for zone_name, zone in self.graph.zones.items():
                future_occupancy[zone_name] = zone.current_drones

            planned_moves: list[PlannedMove] = []  # to store turn moves

            for drone in priority_drones:  # ignore delivered drones
                if drone.my_state == "DELIVERED":
                    continue

                # check if the drone in the end zone to change it's state to delivered
                if drone.my_position + 1 >= len(drone.path):
                    drone.my_state = "DELIVERED"
                    continue

                current = self.graph.zones[drone.path[drone.my_position]]
                to_move = self.graph.zones[drone.path[drone.my_position + 1]]
                # get connection of the current with the goal
                connection = self.bring_connections(current.name, to_move.name)
                # check if the zone still have places
                if future_occupancy[to_move.name] < to_move.max_drones:
                    # check if the drone restricted so it will take two turns
                    if self.is_restricted(to_move):
                        if drone.my_state == "IN_TRANSITE":
                            planned_moves.append((drone, "IN_TRANSITE", to_move))
                            print(f"D{drone.id}-{to_move}", end=" ")
                            drone.my_state = "WAITING"  # change the state to waiting
                            future_occupancy[to_move.name] += 1
                            connection.current_drones -= 1
                        elif connection.current_drones < connection.max_capacity:
                            if connection.current_drones < to_move.max_drones:
                                # move the drone to the connection
                                planned_moves.append((drone, current, "IN_TRANSITE"))
                                print(f"D{drone.id}-{current}-{to_move}", end=" ")
                                drone.my_state = "IN_TRANSITE"
                                future_occupancy[current.name] -= 1
                                connection.current_drones += 1
                    else:  # if the zone to move to is normal
                        # move the drone easly to the zone
                        planned_moves.append((drone, current, to_move))
                        future_occupancy[to_move.name] += 1  # update current drones on the zone
                        print(f"D{drone.id}-{to_move}", end=" ")

                        # update the current drones on the current zone
                        future_occupancy[current.name] -= 1
                        drone.my_state = "WAITING"  # change the state to waiting

            self.drones_history.append(planned_moves)
            # applicate the planned moves
            for drone, current_target, destination in planned_moves:

                if destination != "IN_TRANSITE":
                    if isinstance(destination, Zone):
                        destination.current_drones += 1
                    drone.my_position += 1
                    drone.my_state = "WAITING"

                if isinstance(current_target, Zone):
                    current_target.current_drones -= 1

                if isinstance(destination, Zone):
                    if destination.name == self.graph.end.name:
                        drone.my_state = "DELIVERED"
            if planned_moves:
                history_lines.append(" ".join(
                    f"D{drone.id}-{getattr(destination, 'name', destination)}"
                    for drone, _, destination in planned_moves
                ))
            print()
            # if self.drones_numebr <= 30:
            #     time.sleep(0.1)
            if not planned_moves:
                raise RuntimeError(
                    "No drone could move this turn; check the path strategy or zone capacities")
        print("=> Drones Arrived Correctly")
        return self.drones_history
