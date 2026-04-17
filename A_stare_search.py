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
        self.visited = []
    
    # get the heuristic value by calculating the distance between the current zone and the end zone
    def heuristic(self) -> list[int]:
        self.graph.heuristic()
        # print([zone.distance_to_goal for zone in self.graph.zones.values()])
    def push_heap(self, cost):
        heapq.heappush(self.zone_heap, cost)
    def pop_heap(self):
        return heapq.heappop(self.zone_heap)

    
    

A_start = AStarSearch(graph)

A_start.heuristic()
