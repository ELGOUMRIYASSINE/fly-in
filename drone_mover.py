import A_stare_search
from enum  import Enum
import graph_builder_test
from graph_builder_test import Graph
import math
import heapq


class DroneMover():
    def __init__(self, graph, drones_number, path):
        self.drones_history = {}
        self.graph = graph
        self.drones_numebr = drones_number
        self.path = path
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
        while graph.end.current_drones != self.drones_numebr:
            # i used -1 beacause i want to compare the current point with the next one
            #  so if i reach the end of the path i will compare the current point with the next one which is the end point
            for i in range(len(self.path) - 1): 
                current = self.graph.zones[self.path[i]]
                start_station = self.graph.zones[self.path[i + 1]]
                connection = self.bring_connections(start_station.name, current.name)
                # this line is to check if the drone can move to the next station or not if the current 
                # station has less drones than the max drones or if the current station is the end station
                if current.current_drones < current.max_drones or current.name == self.graph.end.name:
                    if current.zone_type == "restricted":
                        if connection.current_usage > 0:
                            current.drones_in_station.append(connection.current_drones[0])
                            current.current_drones += 1
                            connection.current_drones.remove(connection.current_drones[0])
                            connection.current_usage -= 1
                            self.drones_history[f"D{}"] = {"connection": current.name}
                    else:
                        if start_station.current_drones > 0:
                            for drone in range(connection.max_capacity):
                                current.drones_in_station.append(start_station.drones_in_station[0])
                                current.current_drones += 1
                                start_station.drones_in_station.remove(start_station.drones_in_station[0])
                                start_station.current_drones -= 1
                                self.drones_history[f"D{drone}"] = str(connection)
                print(self.drones_history)
                        


            exit()
                


graph, nb_drones = graph_builder_test.build_graph()
searcher = A_stare_search.AStarSearch(graph, nb_drones)
searcher.find()
mover = DroneMover(graph, nb_drones, searcher.extract_path())  
mover.drone_mover()              

