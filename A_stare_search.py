from enum  import Enum
import graph_builder_test
from graph_builder_test import Graph
import math
import heapq
import random


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
        self.paths_counter = 0
        self.increaesers = []
    
    def push_heap(self, cost, distance_to_goal, zone_name):
        heapq.heappush(self.zone_heap, (cost, distance_to_goal, zone_name))
    def pop_heap(self):
        return heapq.heappop(self.zone_heap)
    def extract_path(self, path_index):
        current = self.end.name
        current_path = []
        current_path.append(current)
        while current != "start":
            current_path.append(self.came_from[path_index][current])
            current = self.came_from[path_index][current]
        return current_path
    def add_came_from(self, zone_name, from_name):
        if self.paths_counter not in self.came_from:
            self.came_from[self.paths_counter] = {}
        self.came_from[self.paths_counter][zone_name] = from_name
    def fake_costs(self):
        operation_costs = {}
        for name, zone in self.graph.zones.items():
            operation_costs[name] = zone.zone_cost
        return operation_costs
    def increase_zone(self, tmp_costs, old_path):
        for zone_name in reversed(old_path):
            if zone_name in self.increaesers:
                picked_zone = zone_name
                print(picked_zone)
                self.increaesers.remove(picked_zone)
                tmp_costs[picked_zone] += 1000
                break
    def find(self, tmp_costs):
        first = False
        if self.paths_counter == 0:
            first = True
        if self.graph.end:
            self.g_scores[self.start.name] = 0
            self.push_heap(0, 0, graph.start.name)
            while True:
                current_zone = self.pop_heap()
                if current_zone[2] in self.visited:
                    continue
                if current_zone[2] == self.graph.end.name:
                    break
                else:
                    self.visited.add(current_zone[2])
                    current = self.graph.zones[current_zone[2]]
                    counter = 0
                    for zone in current.neighbors:
                        if zone.name not in self.visited and zone.zone_state_cost != "blocked":
                            if first:
                                if zone.name not in self.increaesers:
                                    self.increaesers.append(zone.name)
                            if zone.name in self.g_scores:
                                if self.g_scores[zone.name] > self.g_scores[current.name] + tmp_costs[zone.name]:
                                    self.g_scores[zone.name] = self.g_scores[current.name] + tmp_costs[zone.name]
                                    self.push_heap(self.g_scores[zone.name], tmp_costs[zone.name], zone.name)
                                    self.add_came_from(zone.name, current_zone[2])
                            else:                                     
                                self.g_scores[zone.name] = self.g_scores[current.name] + tmp_costs[zone.name]
                                self.push_heap(self.g_scores[zone.name], tmp_costs[zone.name], zone.name)
                                self.add_came_from(zone.name, current_zone[2])
                            counter += 1
                    if first and counter == 1:
                        self.increaesers.pop()
            
        
    def get_paths(self):
        tmp_costs = self.fake_costs()
        self.find(tmp_costs)
        founded_path = self.extract_path(self.paths_counter)
        for i in range(len(self.increaesers) + 1):
            self.paths_counter += 1
            self.zone_heap = []
            self.g_scores = {}
            self.visited = set()
            self.increase_zone(tmp_costs, founded_path)
            print(tmp_costs)
            self.find(tmp_costs)
            founded_path = self.extract_path(self.paths_counter)
            if founded_path in self.path:
                break
            if founded_path not in self.path:
                self.path.append(founded_path)
        print(self.path)
        return self.came_from


graph, drones_nbr = graph_builder_test.build_graph()
test = AStarSearch(graph, drones_nbr)
test.get_paths()
