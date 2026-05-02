from enum  import Enum
import graph_builder_test
from graph_builder_test import Graph
import math
import heapq


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
        self.path = []
    
    # get the heuristic value by calculating the distance between the current zone and the end zone
    def heuristic(self) -> list[int]:
        self.graph.heuristic()
        # print([zone.distance_to_goal for zone in self.graph.zones.values()])
    def push_heap(self, cost, distance_to_goal, zone_name):
        heapq.heappush(self.zone_heap, (cost, distance_to_goal, zone_name))
    def pop_heap(self):
        return heapq.heappop(self.zone_heap)
    # def extract_path(self):
    #     current = self.end.name
    #     while True:
    #         self.path.append(self.came_from)
    #         if name == current:
    #             self.path.append(name)
    #             current = came_from
    #     print(self.path)
    def add_came_from(self, zone_name, from_name):
        self.came_from[zone_name] = from_name
    def find(self):
        order = 0
        # calculate the cost of all drones 
        self.heuristic()

        if self.graph.end:
            while True:
                if self.begin:
                    self.begin = False
                    self.push_heap(graph.start.zone_cost, graph.start.distance_to_goal, graph.start.name)
                current_zone = self.pop_heap()
                if current_zone[2] == self.graph.end.name:
                    # self.graph.end.total_cost =
                    self.visited.add(self.graph.end.name)               
                    # self.extract_path()
                    break
                else:
                    self.visited.add(current_zone[2])
                    current = self.graph.zones[current_zone[2]]
                    for zone in current.neighbors:
                        if zone.name not in self.visited:
                            zone.zone_cost =  zone.zone_cost + current.zone_cost
                            self.push_heap(zone.zone_cost, zone.distance_to_goal, zone.name)
                            self.add_came_from(zone.name, current_zone[2])
        # self.extract_path()
        return (self.came_from)
    
test = AStarSearch(graph)
print(test.find())
