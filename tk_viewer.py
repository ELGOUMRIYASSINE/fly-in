from __future__ import annotations

import math
from collections import defaultdict
import tkinter as tk

import A_stare_search
import graph_builder_test
from drone_mover import DroneMover


ZONE_COLORS: dict[str, str] = {
    "normal": "#4A90D9",
    "restricted": "#E67E22",
    "priority": "#27AE60",
    "blocked": "#7F8C8D",
}
DRONE_COLORS = [
    "#E74C3C", "#9B59B6", "#1ABC9C", "#F39C12",
    "#2ECC71", "#3498DB", "#E91E63", "#FF5722",
    "#00BCD4", "#8BC34A", "#FF9800", "#673AB7",
    "#F44336", "#009688", "#CDDC39", "#795548",
    "#607D8B", "#FF4081", "#69F0AE", "#40C4FF",
    "#FFD740", "#FF6D00", "#EEFF41", "#EA80FC",
    "#FFFFFF",
]
BG_COLOR = "#1E1E2E"
LINE_COLOR = "#4E4E72"
TEXT_COLOR = "#FFFFFF"
PANEL_COLOR = "#24243A"
TRANSIT_COLOR = "#F1C40F"


class DroneSimulator:
    def __init__(self, graph: graph_builder_test.Graph, history: dict, nb_drones: int) -> None:
        self.graph = graph
        self.history = history
        self.turns = list(history.keys())
        self.nb_drones = nb_drones
        self.current_turn_idx = 0

        self.zone_positions: dict[str, tuple[int, int]] = {}
        self.zone_radii: dict[str, int] = {}
        self.drone_states: dict[int, tuple[str, ...]] = {}

        self.canvas_w, self.canvas_h = self._build_layout()

        self.root = tk.Tk()
        self.root.title("Fly-in Drone Simulator")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry(f"{self.canvas_w + 36}x{self.canvas_h + 160}")
        self.root.minsize(1200, 820)

        self._build_ui()
        self._reset_state()

        self.root.bind("<Return>", self._on_enter)
        self.root.bind("<KP_Enter>", self._on_enter)

    def _build_layout(self) -> tuple[int, int]:
        zones = list(self.graph.zones.values())
        unique_x = sorted({zone.x for zone in zones})
        unique_y = sorted({zone.y for zone in zones})

        margin_x = 70
        margin_y = 70
        x_step = max(56, min(82, (1440 - 2 * margin_x) / max(1, len(unique_x) - 1)))
        y_step = max(84, min(118, (820 - 2 * margin_y) / max(1, len(unique_y) - 1)))

        x_index = {value: index for index, value in enumerate(unique_x)}
        y_index = {value: index for index, value in enumerate(unique_y)}

        groups: dict[tuple[int, int], list[graph_builder_test.Zone]] = defaultdict(list)
        for zone in zones:
            groups[(zone.x, zone.y)].append(zone)

        for (x, y), group in groups.items():
            col = x_index[x]
            row = len(unique_y) - 1 - y_index[y]
            center_x = int(margin_x + col * x_step)
            center_y = int(margin_y + row * y_step)

            ordered = sorted(group, key=lambda zone: zone.name)
            if len(ordered) == 1:
                zone = ordered[0]
                self.zone_positions[zone.name] = (center_x, center_y)
                self.zone_radii[zone.name] = 24
                continue

            spread = 12 + min(12, len(ordered) * 2)
            for index, zone in enumerate(ordered):
                angle = (2 * math.pi * index) / len(ordered)
                px = int(center_x + math.cos(angle) * spread)
                py = int(center_y + math.sin(angle) * spread * 0.75)
                self.zone_positions[zone.name] = (px, py)
                self.zone_radii[zone.name] = 24

        canvas_w = int(margin_x * 2 + (len(unique_x) - 1) * x_step + 100)
        canvas_h = int(margin_y * 2 + (len(unique_y) - 1) * y_step + 100)
        return canvas_w, canvas_h

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(
            frame,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        ctrl = tk.Frame(self.root, bg=PANEL_COLOR)
        ctrl.pack(fill=tk.X, padx=10, pady=(0, 10))

        btn_cfg = dict(bg="#3A3A5E", fg=TEXT_COLOR, relief=tk.FLAT, padx=12, pady=5, cursor="hand2")
        tk.Button(ctrl, text="Reset", command=self._reset_state, **btn_cfg).pack(side=tk.LEFT, padx=4, pady=8)
        tk.Button(ctrl, text="Next turn", command=self._on_enter, **btn_cfg).pack(side=tk.LEFT, padx=4, pady=8)

        tk.Label(
            ctrl,
            text="Press Enter to advance one turn",
            bg=PANEL_COLOR,
            fg="#D0D0F0",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, padx=16)

        self.info_var = tk.StringVar(value="Turn 0 / 0")
        tk.Label(ctrl, textvariable=self.info_var, bg=PANEL_COLOR, fg="#A0A0CC", font=("Courier", 11)).pack(
            side=tk.RIGHT,
            padx=12,
        )

        log_frame = tk.Frame(self.root, bg=BG_COLOR)
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(log_frame, text="Turn log:", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W)
        self.log_box = tk.Text(
            log_frame,
            height=5,
            bg=PANEL_COLOR,
            fg="#D7D7F7",
            font=("Courier", 10),
            state=tk.DISABLED,
            relief=tk.FLAT,
        )
        self.log_box.pack(fill=tk.X)

    def _reset_state(self) -> None:
        self.current_turn_idx = 0
        self.drone_states = {did: ("zone", self.graph.start.name) for did in range(self.nb_drones)}
        self._draw_all()
        self._update_panel()

    def _draw_all(self) -> None:
        self.canvas.delete("all")
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()
        self._draw_legend()

    def _draw_connections(self) -> None:
        for conn in self.graph.connections:
            x1, y1 = self.zone_positions[conn.zone_a.name]
            x2, y2 = self.zone_positions[conn.zone_b.name]
            self.canvas.create_line(x1, y1, x2, y2, fill=LINE_COLOR, width=3)

            if conn.max_capacity > 1:
                mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                self.canvas.create_text(
                    mx,
                    my - 10,
                    text=f"cap {conn.max_capacity}",
                    fill="#B6B6D8",
                    font=("Arial", 8),
                )

    def _draw_zones(self) -> None:
        for zone in self.graph.zones.values():
            sx, sy = self.zone_positions[zone.name]
            radius = self.zone_radii.get(zone.name, 24)
            color = ZONE_COLORS.get(zone.zone_type.value, "#888888")

            if zone.name == self.graph.start.name:
                color = "#2ECC71"
            elif zone.name == self.graph.end.name:
                color = "#E74C3C"

            self.canvas.create_oval(
                sx - radius - 8,
                sy - radius - 8,
                sx + radius + 8,
                sy + radius + 8,
                fill="",
                outline=color,
                width=4,
            )
            self.canvas.create_oval(
                sx - radius,
                sy - radius,
                sx + radius,
                sy + radius,
                fill=color,
                outline="#FFFFFF",
                width=2,
            )
            self.canvas.create_text(
                sx,
                sy - 1,
                text=zone.name.replace("_", "\n"),
                fill=TEXT_COLOR,
                font=("Arial", 7, "bold"),
                justify=tk.CENTER,
            )

            if zone.max_drones > 1:
                badge_x = sx + radius - 3
                badge_y = sy - radius + 3
                self.canvas.create_oval(
                    badge_x - 9,
                    badge_y - 9,
                    badge_x + 9,
                    badge_y + 9,
                    fill="#1B1B28",
                    outline="#FFD700",
                    width=2,
                )
                self.canvas.create_text(
                    badge_x,
                    badge_y,
                    text=str(zone.max_drones),
                    fill="#FFD700",
                    font=("Arial", 7, "bold"),
                )

    def _draw_legend(self) -> None:
        lx, ly = 10, 10
        items = [
            ("normal", "Normal"),
            ("restricted", "Restricted"),
            ("priority", "Priority"),
            ("blocked", "Blocked"),
        ]
        for index, (key, label) in enumerate(items):
            y = ly + index * 18
            color = ZONE_COLORS[key]
            self.canvas.create_rectangle(lx, y, lx + 14, y + 12, fill=color, outline="")
            self.canvas.create_text(lx + 18, y + 6, anchor=tk.W, text=label, fill=TEXT_COLOR, font=("Arial", 8))

    def _zone_center(self, zone_name: str) -> tuple[int, int]:
        return self.zone_positions[zone_name]

    def _parse_move(self, move_str: str) -> tuple[list[str], bool]:
        parts = [part.strip() for part in move_str.split("->")]
        return parts, any(part == "[transit]" for part in parts)

    def _advance_turn(self) -> None:
        if self.current_turn_idx >= len(self.turns):
            return

        turn_key = self.turns[self.current_turn_idx]
        moves = self.history.get(turn_key, {})

        for drone_key, move_str in moves.items():
            did = int(drone_key[1:])
            parts, has_transit = self._parse_move(move_str)

            if len(parts) == 3 and has_transit:
                left, middle, right = parts
                if middle == "[transit]":
                    if left == "[transit]":
                        self.drone_states[did] = ("zone", right)
                    else:
                        self.drone_states[did] = ("transit", left, right)
                else:
                    self.drone_states[did] = ("zone", right)
            elif len(parts) == 2:
                left, right = parts
                if right == "[transit]":
                    self.drone_states[did] = ("transit", left, left)
                elif left == "[transit]":
                    self.drone_states[did] = ("zone", right)
                else:
                    self.drone_states[did] = ("zone", right)
            elif parts:
                self.drone_states[did] = ("zone", parts[-1])

        self.current_turn_idx += 1
        self._draw_all()
        self._update_panel(turn_key)

    def _on_enter(self, event=None):
        self._advance_turn()
        return "break"

    def _drone_position(self, drone_id: int, zone_groups: dict[str, list[int]]) -> tuple[int, int]:
        state = self.drone_states.get(drone_id, ("zone", self.graph.start.name))
        if not state:
            return self._zone_center(self.graph.start.name)

        kind = state[0]
        if kind == "transit" and len(state) == 3:
            from_zone, to_zone = state[1], state[2]
            x1, y1 = self._zone_center(from_zone)
            x2, y2 = self._zone_center(to_zone)
            mx = int((x1 + x2) / 2)
            my = int((y1 + y2) / 2)
            dx = x2 - x1
            dy = y2 - y1
            length = max(1.0, math.hypot(dx, dy))
            offset = 8 + (drone_id % 3) * 3
            perp_x = -dy / length
            perp_y = dx / length
            mx += int(perp_x * offset)
            my += int(perp_y * offset)
            return mx, my

        zone_name = state[1] if len(state) > 1 else self.graph.start.name
        cx, cy = self._zone_center(zone_name)
        drones_here = zone_groups.get(zone_name, [])
        if len(drones_here) <= 1:
            return cx, cy

        index = drones_here.index(drone_id)
        radius = 9 + min(8, len(drones_here))
        angle = (2 * math.pi * index) / len(drones_here)
        return int(cx + math.cos(angle) * radius), int(cy + math.sin(angle) * radius * 0.75)

    def _draw_drones(self) -> None:
        self.canvas.delete("drone")
        zone_groups: dict[str, list[int]] = defaultdict(list)
        for drone_id, state in self.drone_states.items():
            if state and state[0] == "zone" and len(state) > 1:
                zone_groups[state[1]].append(drone_id)

        for group in zone_groups.values():
            group.sort()

        for drone_id in range(self.nb_drones):
            sx, sy = self._drone_position(drone_id, zone_groups)
            color = DRONE_COLORS[drone_id % len(DRONE_COLORS)]
            state = self.drone_states.get(drone_id, ("zone", self.graph.start.name))
            is_transit = state and state[0] == "transit"
            outline = TRANSIT_COLOR if is_transit else "#FFFFFF"
            self.canvas.create_oval(sx - 7, sy - 7, sx + 7, sy + 7, fill=color, outline=outline, width=2, tags="drone")
            self.canvas.create_text(sx, sy, text=str(drone_id), fill="#000000", font=("Arial", 6, "bold"), tags="drone")

    def _update_panel(self, turn_key: str = "") -> None:
        total = len(self.turns)
        self.info_var.set(f"Turn {self.current_turn_idx} / {total}   |   {turn_key}")

        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        if turn_key and turn_key in self.history:
            for drone, move in self.history[turn_key].items():
                self.log_box.insert(tk.END, f"  {drone}: {move}\n")
        self.log_box.config(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    graph, nb_drones = graph_builder_test.build_graph()
    searcher = A_stare_search.AStarSearch(graph, nb_drones)
    searcher.find()
    path = searcher.extract_path()

    mover = DroneMover(graph, nb_drones, path)
    history = mover.drone_mover()

    print(f"Total turns: {mover.turns}")
    print(f"Path: {path}")

    sim = DroneSimulator(graph, history, nb_drones)
    sim.run()


if __name__ == "__main__":
    main()