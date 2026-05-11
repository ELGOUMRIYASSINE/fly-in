import A_stare_search
import graph_builder_test
import time
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
    def __init__(self, graph, drones_number, path):
        self.drones_history = {}
        self.graph = graph
        self.drones_numebr = drones_number
        self.drones = graph.drones
        self.paths = path
        self.turns = 0
    def bring_connections(self, start_point, end_point):
        used_connections = {}
        if f"{start_point} {end_point}" in used_connections:
            return used_connections[f"{start_point} {end_point}"]
        for connection in self.graph.connections:
            if connection.zone_a.name == start_point and connection.zone_b.name == end_point:
                used_connections[f"{start_point} {end_point}"] = connection
                return connection
    def create_paths_objects(self):
        paths_obj = []
        for p in self.paths:
            min_capacity = 9999999
            for zone in p:
                if self.graph.zones[zone].max_drones < min_capacity:
                    min_capacity = self.graph.zones[zone].max_drones
            p.reverse()
            paths_obj.append(Path(p, min_capacity))
        return paths_obj

    def get_strategy(self):
        paths_obj = self.create_paths_objects()
        for drone in self.drones:
            best_arrival = sys.maxsize
            best_path = paths_obj[0]
            for path in paths_obj:
                enter_turn = (path.sent_drones // path.capacity) + 1
                arrival = enter_turn + path.length - 1
                if arrival <= best_arrival:
                    best_path = path
                    best_arrival = arrival
            drone.path = best_path.path
            best_path.sent_drones += 1   
                         
    def drone_mover(self):
        while self.graph.end.current_drones != self.drones_numebr:

            # ===== Sort drones =====
            # Front drones move first
            priority_drones = sorted(
                self.drones,
                key=lambda drone: drone.my_position,
                reverse=True
            )

            # ===== Reservation system =====
            future_occupancy = {}

            for zone_name, zone in self.graph.zones.items():
                future_occupancy[zone_name] = zone.current_drones

            # ===== Planned movements =====
            planned_moves = []

            # ===== Phase 1: Planning =====
            for drone in priority_drones:

                if drone.my_state == "DELIVERED":
                    continue

                # ===== End of path =====
                if drone.my_position + 1 >= len(drone.path):
                    drone.my_state = "DELIVERED"
                    continue

                current = self.graph.zones[
                    drone.path[drone.my_position]
                ]

                to_move = self.graph.zones[
                    drone.path[drone.my_position + 1]
                ]

                # ===== Reservation capacity check =====
                if future_occupancy[to_move.name] < to_move.max_drones:

                    planned_moves.append(
                        (drone, current, to_move)
                    )

                    # Reserve slot immediately
                    future_occupancy[to_move.name] += 1
                    future_occupancy[current.name] -= 1

                    drone.my_state = "READY_TO_MOVE"

                else:
                    drone.my_state = "WAITING"

            # ===== Phase 2: Apply movements =====
            for drone, current, to_move in planned_moves:

                current.current_drones -= 1
                to_move.current_drones += 1

                drone.my_position += 1
                drone.my_state = "IN_TRANSITE"

                print(f"D{drone.id}-{to_move.name} ",end="")

                # ===== Goal reached =====
                if to_move.name == self.graph.end.name:
                    drone.my_state = "DELIVERED"
                    # print(f"D{drone.id} DELIVERED")

            # ===== Tick separator =====
            # print("\n--- NEXT TICK ---\n")
            print("\n")
                        
                            

    # def drone_mover(self):
    #     self.graph.create_drones(self.drones_numebr)
    #     self.graph.start.current_drones = self.drones_numebr
    #     self.graph.start.drones_in_station = self.graph.drones
    #     while self.graph.end.current_drones != self.drones_numebr:
    #         # i used -1 beacause i want to compare the current point with the next one
    #         #  so if i reach the end of the path i will compare the current point with the next one which is the end point
    #         turn = {}
    #         for i in range(len(self.path) - 1):
    #             current = self.graph.zones[self.path[i]]
    #             start_station = self.graph.zones[self.path[i + 1]]
    #             connection = self.bring_connections(start_station.name, current.name)
    #             # this line is to check if the drone can move to the next station or not if the current 
    #             # station has less drones than the max drones or if the current station is the end station
    #             if current.current_drones < current.max_drones or current.name == self.graph.end.name:
    #                 if current.zone_type == graph_builder_test.ZoneType.RESTRICTED:
    #                     if connection.current_usage > 0:
    #                         # change state for end point
    #                         drone = connection.current_drones.pop(0)
    #                         drone.my_state = "WAITING"
    #                         current.drones_in_station.append(drone)
    #                         current.current_drones += 1
    #                         # change state for the connection
    #                         connection.current_usage -= 1
    #                         # add the move to history
    #                         # turn[f"D{drone.id}"] = {"connection": current.name}
    #                         turn[f"D{drone.id}"] = f"[transit]->{current.name}"
    #                     if start_station.current_drones > 0:
    #                         drone = start_station.drones_in_station.pop(0)
    #                         drone.my_state = "IN_TRANSITE"
    #                         connection.current_drones.append(drone)
    #                         connection.current_usage += 1
    #                         start_station.current_drones -= 1
    #                         # turn[f"D{drone.id}"] = {start_station.name: "connection"}
    #                         turn[f"D{drone.id}"] = f"{start_station.name}->[transit]->{current.name}"
    #                 else:
    #                     if start_station.current_drones > 0:
    #                         # print("cc")
    #                         # exit()
    #                         for _ in range(connection.max_capacity):
    #                             drone = start_station.drones_in_station.pop(0)
    #                             drone.my_state = "WAITING"
    #                             current.drones_in_station.append(drone)
    #                             current.current_drones += 1
    #                             start_station.current_drones -= 1
    #                             # turn[f"D{drone.id}"] = {start_station.name: current.name}
    #                             turn[f"D{drone.id}"] = f"{start_station.name}->{current.name}"
    #                             # self.drones_history[f"D{drone}"] = str(connection)
    #                             if current.max_drones > current.current_drones:
    #                                 break
    #         self.turns += 1
    #         self.drones_history[f"Turn {self.turns}"] = turn

    #     return self.drones_history


def compute_path():
    graph, nb_drones = graph_builder_test.build_graph()
    graph.create_drones(nb_drones)
    searcher = A_stare_search.AStarSearch(graph, nb_drones)
    paths = searcher.get_paths()
    return graph, nb_drones, paths


if __name__ == "__main__":
    graph, nb_drones, paths = compute_path()
    mover = DroneMover(graph, nb_drones, paths)
    mover.get_strategy()
    mover.drone_mover()
    # history = mover.drone_mover()
    # for turn, moves in history.items():
    #     print(turn, end=" ")
    #     for drone, move in moves.items():
    #         print(f"{drone}: {move}", end=" ")
    #     print()
    # print(f"turns number : {mover.turns}")
    # print(path)

