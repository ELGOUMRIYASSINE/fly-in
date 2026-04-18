from enum  import Enum
import graph_builder_test
from graph_builder_test import Graph
import math
import heapq

class Drone():
    def __init__(self, id, state, current_hub, path, turns_transit):
        self.id = id
        self.state = state
        self.current_hub = current_hub
        self.path = []
        self.turns_transit = turns_transit


graph, nb_drones = graph_builder_test.build_graph()
class AStarSearch:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.start = graph.start
        self.end = graph.end
        self.zone_heap = []
        self.visited = set()
        self.came_from = {}
        self.begin = True
    
    # get the heuristic value by calculating the distance between the current zone and the end zone
    def heuristic(self) -> list[int]:
        self.graph.heuristic()
        # print([zone.distance_to_goal for zone in self.graph.zones.values()])
    def push_heap(self, zone_name):
        heapq.heappush(self.zone_heap, (self.graph.zones_total_cost[zone_name]))
    def pop_heap(self):
        return heapq.heappop(self.zone_heap)
    def extract_path(self):
        pass
    def add_came_from(self, zone_name, from_name):
        self.came_from[zone_name] = from_name
    def find(self):
        order = 0
        # calculate the cost of all drones 
        self.heuristic()

        # check if we are at the begining of the graph
        if self.graph.end:
            while True:
                if self.begin:
                    self.begin = False
                    self.push_heap(graph.start.name)
                current_zone = self.pop_heap()
                if current_zone[2].name == self.graph.end.name:    
                    self.visited.add(current_zone[2].name)                
                    self.extract_path()
                    break
                else:
                    self.visited.add(current_zone[2].name)  
                    for zone in current_zone[2].neighbors:
                        if zone.name not in self.visited:
                            self.push_heap(zone.name)
                            self.add_came_from(zone.name, current_zone[2].name)
        print(self.came_from)

A_start = AStarSearch(graph)

A_start.find()