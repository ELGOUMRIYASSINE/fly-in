from enum  import Enum
from graph_builder_test import Graph
import heapq

class AStarSearch:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.start = graph.start
        self.end = graph.end
        self.zone_heap = []
        self.visited = set()
        self.came_from = {}
        self.begin = True
        self.paths = []
        self.drones_number = graph.nb_drones
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
                self.increaesers.remove(picked_zone)
                tmp_costs[picked_zone] += 1000
                break
    def find(self, tmp_costs):
        first = False
        if self.paths_counter == 0:
            first = True
        if self.graph.end:
            self.g_scores[self.graph.start.name] = 0
            self.push_heap(0, 0, self.graph.start.name)
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
                        if zone.name not in self.visited and zone.zone_type != "blocked":
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
        if not self.start or not self.end:
            return []

        max_paths = min(4, self.drones_number)
        cost_margin = 1
        heap = [(0, 1, self.start.name, (self.start.name,))]
        best_cost = None
        founded_paths = []

        while heap and len(founded_paths) < max_paths:
            cost, path_length, zone_name, path = heapq.heappop(heap)

            if best_cost is not None and cost > best_cost + cost_margin:
                break

            if zone_name == self.end.name:
                if best_cost is None:
                    best_cost = cost
                founded_paths.append(list(reversed(path)))
                continue

            current = self.graph.zones[zone_name]
            for neighbor in current.neighbors:
                if neighbor.name in path or neighbor.zone_type == "blocked":
                    continue
                new_cost = cost + neighbor.zone_cost
                new_path = path + (neighbor.name,)
                heapq.heappush(
                    heap,
                    (new_cost, path_length + 1, neighbor.name, new_path)
                )

        return founded_paths
