import A_stare_search
import graph_builder_test
import time



class DroneMover():
    def __init__(self, graph, drones_number, path):
        self.drones_history = {}
        self.graph = graph
        self.drones_numebr = drones_number
        self.path = path
        self.turns = 0
    def bring_connections(self, start_point, end_point):
        used_connections = {}
        if f"{start_point} {end_point}" in used_connections:
            return used_connections[f"{start_point} {end_point}"]
        for connection in self.graph.connections:
            if connection.zone_a.name == start_point and connection.zone_b.name == end_point:
                used_connections[f"{start_point} {end_point}"] = connection
                return connection
    def drone_mover(self):
        # print(self.path)
        self.graph.create_drones(self.drones_numebr)
        self.graph.start.current_drones = self.drones_numebr
        self.graph.start.drones_in_station = self.graph.drones
        while self.graph.end.current_drones != self.drones_numebr:
            # i used -1 beacause i want to compare the current point with the next one
            #  so if i reach the end of the path i will compare the current point with the next one which is the end point
            turn = {}
            for i in range(len(self.path) - 1):
                current = self.graph.zones[self.path[i]]
                start_station = self.graph.zones[self.path[i + 1]]
                connection = self.bring_connections(start_station.name, current.name)
                # this line is to check if the drone can move to the next station or not if the current 
                # station has less drones than the max drones or if the current station is the end station
                if current.current_drones < current.max_drones or current.name == self.graph.end.name:
                    if current.zone_type == graph_builder_test.ZoneType.RESTRICTED:
                        if connection.current_usage > 0:
                            # change state for end point
                            drone = connection.current_drones.pop(0)
                            drone.my_state = "WAITING"
                            current.drones_in_station.append(drone)
                            current.current_drones += 1
                            # change state for the connection
                            connection.current_usage -= 1
                            # add the move to history
                            # turn[f"D{drone.id}"] = {"connection": current.name}
                            turn[f"D{drone.id}"] = f"[transit]->{current.name}"
                        if start_station.current_drones > 0:
                            drone = start_station.drones_in_station.pop(0)
                            drone.my_state = "IN_TRANSITE"
                            connection.current_drones.append(drone)
                            connection.current_usage += 1
                            start_station.current_drones -= 1
                            # turn[f"D{drone.id}"] = {start_station.name: "connection"}
                            turn[f"D{drone.id}"] = f"{start_station.name}->[transit]->{current.name}"
                    else:
                        if start_station.current_drones > 0:
                            # print("cc")
                            # exit()
                            for _ in range(connection.max_capacity):
                                drone = start_station.drones_in_station.pop(0)
                                drone.my_state = "WAITING"
                                current.drones_in_station.append(drone)
                                current.current_drones += 1
                                start_station.current_drones -= 1
                                # turn[f"D{drone.id}"] = {start_station.name: current.name}
                                turn[f"D{drone.id}"] = f"{start_station.name}->{current.name}"
                                # self.drones_history[f"D{drone}"] = str(connection)
                                if current.max_drones > current.current_drones:
                                    break
            self.turns += 1
            self.drones_history[f"Turn {self.turns}"] = turn

        # for turn, move in self.drones_history.values:
        #     # print(f"{turn}")
        #     print(turn, move)
        return self.drones_history


def compute_path():
    graph, nb_drones = graph_builder_test.build_graph()
    searcher = A_stare_search.AStarSearch(graph, nb_drones)
    searcher.find()
    path = searcher.extract_path()
    return graph, nb_drones, path


if __name__ == "__main__":
    graph, nb_drones, path = compute_path()
    mover = DroneMover(graph, nb_drones, path)
    history = mover.drone_mover()
    for turn, moves in history.items():
        print(turn, end=" ")
        for drone, move in moves.items():
            print(f"{drone}: {move}", end=" ")
        print()
    print(f"turns number : {mover.turns}")
    print(path)

