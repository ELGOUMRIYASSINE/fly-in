from enum  import Enum
import graph_builder_test
from graph_builder_test import Graph
import math
import heapq


graph, nb_drones = graph_builder_test.build_graph()
class AStarSearch:
    def __init__(self, graph: Graph, drones_number: int):
        self.graph = graph
        self.start = graph.start
        self.end = graph.end
        self.zone_heap = []
        self.visited = set()
        self.came_from = {}
        self.begin = True
        self.path = []
        self.drones_number = drones_number
        self.g_scores = {}
    
    def push_heap(self, cost, distance_to_goal, zone_name):
        heapq.heappush(self.zone_heap, (cost, distance_to_goal, zone_name))
    def pop_heap(self):
        return heapq.heappop(self.zone_heap)
    def extract_path(self):
        current = self.end.name
        self.path.append(current)
        while current != "start":
            self.path.append(self.came_from[current])
            current = self.came_from[current]
        return self.path
    def add_came_from(self, zone_name, from_name):
        self.came_from[zone_name] = from_name
    def find(self):
        if self.graph.end:
            self.g_scores[self.start.name] = 0        
            self.push_heap(0, 0, graph.start.name)
            while True:
                current_zone = self.pop_heap()
                if current_zone[2] == self.graph.end.name:
                    break
                else:
                    self.visited.add(current_zone[2])
                    current = self.graph.zones[current_zone[2]]
                    for zone in current.neighbors:
                        if zone.name not in self.visited:
                            if zone.name in self.g_scores:
                                if self.g_scores[zone.name] > self.g_scores[current.name] + zone.zone_cost:
                                    self.g_scores[zone.name] = self.g_scores[current.name] + zone.zone_cost
                                    self.push_heap(self.g_scores[zone.name], zone.zone_cost, zone.name)
                                    self.add_came_from(zone.name, current_zone[2])
                            else:                                     
                                self.g_scores[zone.name] = self.g_scores[current.name] + zone.zone_cost
                                self.push_heap(self.g_scores[zone.name], zone.zone_cost, zone.name)
                                self.add_came_from(zone.name, current_zone[2])
        
        return (self.came_from)
                


# test.find()
# test.extract_path()