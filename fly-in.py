import graph_builder_test
import display
import path_finder
import drone_mover

if __name__ == "__main__":
	graph = graph_builder_test.Graph()
	graph.build_graph()
	paths = path_finder.AStarSearch(graph).get_paths()
	mover = drone_mover.DroneMover(graph, paths)
	history = mover.drone_mover()
	displayer = display.Drawer(graph, history)
	displayer.draw_map()



