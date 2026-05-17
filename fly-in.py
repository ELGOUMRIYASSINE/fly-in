import graph_builder_test
import display
import path_finder
import drone_mover


class Engine():
	MAPS = {
		"e1": "easy/01_linear_path.txt",
		"e2": "easy/02_simple_fork.txt",
		"e3": "easy/03_basic_capacity.txt",
		"e4": "easy/04_priority_tie_test.txt",
		"m1": "medium/01_dead_end_trap.txt",
		"m2": "medium/02_circular_loop.txt",
		"m3": "medium/03_priority_puzzle.txt",
		"h1": "hard/01_maze_nightmare.txt",
		"h2": "hard/02_capacity_hell.txt",
		"h3": "hard/03_ultimate_challenge.txt",
		"c1": "challenger/01_the_impossible_dream.txt",
	}

	def on(self):
		try:
			graph = graph_builder_test.Graph()
			print("Flyyyyyyyyyyy-in")
			print("select map =>")
			print("easy:")
			print("  e1: 01_linear_path.txt")
			print("  e2: 02_simple_fork.txt")
			print("  e3: 03_basic_capacity.txt")
			print("  e4: 04_priority_tie_test.txt")
			print("medium:")
			print("  m1: 01_dead_end_trap.txt")
			print("  m2: 02_circular_loop.txt")
			print("  m3: 03_priority_puzzle.txt")
			print("hard:")
			print("  h1: 01_maze_nightmare.txt")
			print("  h2: 02_capacity_hell.txt")
			print("  h3: 03_ultimate_challenge.txt")
			print("challenger:")
			print("  c1: 01_the_impossible_dream.txt")
			print("you own map: 0")
			value = input("Enter map option: ").strip()
			if value == "0":
				map = input("Enter your map name (example: easy/01_linear_path.txt): ").strip()
			else:
				if value not in self.MAPS:
					raise ValueError(f"Unknown map option: {value}")
				map = self.MAPS[value]
			graph.build_graph(f"maps/{map}")
			paths = path_finder.Djsearch(graph).get_paths()
			mover = drone_mover.DroneMover(graph, paths)
			history = mover.drone_mover()
			displayer = display.Drawer(graph, history)
			displayer.draw_map()
		except Exception as e:
			print(e)

Eng = Engine()
Eng.on()


