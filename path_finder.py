from graph_builder_test import Graph
import heapq

class Djsearch:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.start = graph.start
        self.end = graph.end
        self.drones_number = graph.nb_drones
        self.priority = {"normal":1, "priority":0, "restricted": 2}


    # def get_paths(self):
    #     if not self.start or not self.end:
    #         raise ValueError("No Path can be founded")

    #     # initialisation
    #     max_paths = min(4, self.drones_number)
    #     heap = [(0, self.priority[self.start.zone_type], 0, self.start.name,  (self.start.name, ))]
    #     best_path = None
    #     margin = 1
    #     founded_paths = []

    #     while heap and len(founded_paths) < max_paths:
    #         cost, priority, length, name, path = heapq.heappop(heap)

    #         if best_path and cost > best_path + margin:
    #             break

    #         if name == self.end.name:
    #             if best_path is None:
    #                 best_path = cost
    #             founded_paths.append(list(path))
    #             continue
            
    #         current = self.graph.zones[name]
    #         for zone in current.neighbors:
    #             if zone.name in path or zone.zone_type == "blocked":
    #                 continue
    #             new_cost = cost + zone.zone_cost
    #             new_priority = priority + self.priority[zone.zone_type]
    #             new_path = path + (zone.name,)

    #             heapq.heappush(heap,
    #                            (
    #                                new_cost,
    #                                new_priority,
    #                                length + 1,
    #                                zone.name,
    #                                new_path
    #                            ))
    #     return founded_paths



    def get_paths(self):
        if not self.start or not self.end:
            return []

        max_paths = min(4, self.drones_number)
        cost_margin = 1
        heap = [(0, self.priority[self.start.zone_type], 1, self.start.name, (self.start.name,))]
        best_cost = None
        founded_paths = []

        while heap and len(founded_paths) < max_paths:
            cost, priority, length, zone_name, path = heapq.heappop(heap)

            if best_cost is not None and cost > best_cost + cost_margin:
                break

            if zone_name == self.end.name:
                if best_cost is None:
                    best_cost = cost
                founded_paths.append(list(path))
                continue

            current = self.graph.zones[zone_name]
            for neighbor in current.neighbors:
                if neighbor.name in path or neighbor.zone_type == "blocked":
                    continue
                new_cost = cost + neighbor.zone_cost
                new_priority = priority + self.priority[neighbor.zone_type]
                new_path = path + (neighbor.name,)
                heapq.heappush(
                    heap,
                    (new_cost,
                    new_priority,
                    length + 1,
                    neighbor.name,
                    new_path)
                )
        return founded_paths
