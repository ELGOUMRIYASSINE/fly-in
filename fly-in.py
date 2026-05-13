import graph_builder_test
import display
import path_finder
import drone_mover

if __name__ == "__main__":
	graph, nb_drones = graph_builder_test.build_graph()
	graph.create_drones(nb_drones)
	paths = path_finder.AStarSearch(graph, nb_drones).get_paths()
	mover = drone_mover.DroneMover(graph=graph, drones_number=nb_drones, paths=paths)
	history = mover.drone_mover()
	displayer = display.Drawer(graph, history)
	displayer.draw_map()



