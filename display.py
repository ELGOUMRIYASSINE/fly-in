import tkinter as tk
import graph_builder_test


class Drawer():

    def __init__(self, graph, history):
        self.graph = graph
        self.history = history

        self.scale = 100
        self.offset_x = 100
        self.offset_y = 400

    def get_real_codrdinates(self, x, y):

        screen_x = x * self.scale + self.offset_x
        screen_y = self.offset_y - y * self.scale

        return screen_x, screen_y

    def _build_turn_states(self):

        start_name = self.graph.start.name

        positions = {drone.id: start_name for drone in self.graph.drones}
        trails = {drone.id: [start_name] for drone in self.graph.drones}

        states = [{
            "summary": "Initial state",
            "positions": positions.copy(),
            "trails": {drone_id: trail[:] for drone_id, trail in trails.items()}
        }]

        for turn_number, turn in enumerate(self.history, start=1):
            move_texts = []

            for drone, from_zone, to_zone in turn:
                destination = to_zone if hasattr(to_zone, "name") else from_zone
                destination_name = destination.name
                from_name = getattr(from_zone, "name", str(from_zone))

                positions[drone.id] = destination_name
                trails[drone.id].append(destination_name)

                move_texts.append(
                    f"D{drone.id}: {from_name} -> {destination_name}"
                )

            states.append({
                "summary": f"Turn {turn_number}: " + " | ".join(move_texts),
                "positions": positions.copy(),
                "trails": {drone_id: trail[:] for drone_id, trail in trails.items()}
            })

        return states

    def _zone_color(self, zone):

        if zone.name == self.graph.start.name:
            return "blue"

        if zone.zone_type == graph_builder_test.ZoneType.RESTRICTED:
            return "red"

        return "gray"

    def _drone_color(self, drone_id):

        colors = [
            "#2ecc71",
            "#3498db",
            "#e67e22",
            "#9b59b6",
            "#e74c3c",
            "#16a085",
            "#f1c40f",
            "#34495e"
        ]

        return colors[drone_id % len(colors)]

    def draw_map(self):

        root = tk.Tk()
        root.title("Fly In")

        turn_states = self._build_turn_states()
        current_turn = 0

        top_bar = tk.Frame(root)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        status_var = tk.StringVar()

        canvas = tk.Canvas(
            root,
            width=1200,
            height=800,
            bg="white",
            scrollregion=(-2000, -2000, 5000, 5000)
        )

        # ================= SCROLLBARS =================

        h_scroll = tk.Scrollbar(
            root,
            orient=tk.HORIZONTAL,
            command=canvas.xview
        )

        v_scroll = tk.Scrollbar(
            root,
            orient=tk.VERTICAL,
            command=canvas.yview
        )

        canvas.configure(
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )

        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.pack(fill=tk.BOTH, expand=True)

        # ================= DRAW CONNECTIONS =================

        for connection in self.graph.connections:

            x1, y1 = self.get_real_codrdinates(
                connection.zone_a.x,
                connection.zone_a.y
            )
            x2, y2 = self.get_real_codrdinates(
                connection.zone_b.x,
                connection.zone_b.y
            )

            canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#888888",
                width=2
            )

        # ================= DRAW ZONES =================

        for zone_name in self.graph.zones:

            zone = self.graph.zones[zone_name]

            x, y = self.get_real_codrdinates(
                zone.x,
                zone.y
            )

            if zone.name == self.graph.start.name:

                color = "blue"
                start_x = x
                start_y = y

            else:
                color = "gray"

            if zone.zone_type == graph_builder_test.ZoneType.RESTRICTED:
                color = "red"

            r = 20

            canvas.create_oval(
                x-r, y-r,
                x+r, y+r,
                fill=color
            )

            canvas.create_text(
                x,
                y-r-10,
                text=zone.name,
                font=("Arial", 8)
            )

        # ================= CENTER CAMERA =================

        def center_on_start():

            canvas.update_idletasks()

            scroll_region = canvas.cget("scrollregion").split()

            rx1, ry1, rx2, ry2 = map(int, scroll_region)

            total_w = rx2 - rx1
            total_h = ry2 - ry1

            fx = (start_x - rx1) / total_w
            fy = (start_y - ry1) / total_h

            canvas.xview_moveto(max(0, fx - 0.1))
            canvas.yview_moveto(max(0, fy - 0.1))

        root.after(100, center_on_start)

        # ================= DRAG CAMERA =================

        def start_pan(event):
            canvas.scan_mark(event.x, event.y)

        def pan_graph(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", start_pan)
        canvas.bind("<B1-Motion>", pan_graph)

        # ================= ARROW KEYS =================

        def arrow_scroll(event):

            if event.keysym == "Left":
                canvas.xview_scroll(-1, "units")

            elif event.keysym == "Right":
                canvas.xview_scroll(1, "units")

            elif event.keysym == "Up":
                canvas.yview_scroll(-1, "units")

            elif event.keysym == "Down":
                canvas.yview_scroll(1, "units")

        root.bind("<Left>", arrow_scroll)
        root.bind("<Right>", arrow_scroll)
        root.bind("<Up>", arrow_scroll)
        root.bind("<Down>", arrow_scroll)

        # ================= TURN CONTROLS =================

        def redraw_turn():

            state = turn_states[current_turn]

            canvas.delete("dynamic")

            for drone_id, trail in state["trails"].items():
                if len(trail) > 1:
                    points = []

                    for zone_name in trail:
                        zone = self.graph.zones[zone_name]
                        points.extend(self.get_real_codrdinates(zone.x, zone.y))

                    canvas.create_line(
                        *points,
                        fill=self._drone_color(drone_id),
                        width=2,
                        tags="dynamic"
                    )

            for drone_id, zone_name in state["positions"].items():
                zone = self.graph.zones[zone_name]
                x, y = self.get_real_codrdinates(zone.x, zone.y)

                canvas.create_oval(
                    x-9, y-9,
                    x+9, y+9,
                    fill=self._drone_color(drone_id),
                    outline="black",
                    tags="dynamic"
                )
                canvas.create_text(
                    x,
                    y,
                    text=f"D{drone_id}",
                    fill="white",
                    font=("Arial", 8, "bold"),
                    tags="dynamic"
                )

            status_var.set(f"{state['summary']}    ({current_turn}/{len(turn_states) - 1})")

        def restart_turns():
            nonlocal current_turn
            current_turn = 0
            redraw_turn()

        def previous_turn():
            nonlocal current_turn
            if current_turn > 0:
                current_turn -= 1
                redraw_turn()

        def next_turn():
            nonlocal current_turn
            if current_turn < len(turn_states) - 1:
                current_turn += 1
                redraw_turn()

        tk.Button(top_bar, text="Restart", command=restart_turns).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(top_bar, text="Back", command=previous_turn).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(top_bar, text="Next", command=next_turn).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Label(top_bar, textvariable=status_var).pack(side=tk.LEFT, padx=12)

        def key_controls(event):

            if event.keysym in ("Left", "BackSpace"):
                previous_turn()
            elif event.keysym in ("Right", "space"):
                next_turn()
            elif event.keysym in ("Home", "r", "R"):
                restart_turns()

        root.bind("<Left>", key_controls)
        root.bind("<Right>", key_controls)
        root.bind("<BackSpace>", key_controls)
        root.bind("<space>", key_controls)
        root.bind("<Home>", key_controls)
        root.bind("<r>", key_controls)
        root.bind("<R>", key_controls)

        redraw_turn()

        root.mainloop()