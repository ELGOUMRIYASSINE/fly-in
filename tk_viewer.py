from __future__ import annotations

import math
import re
from collections import defaultdict
import tkinter as tk

import A_stare_search
import graph_builder_test
from drone_mover import DroneMover


# ── visual constants ──────────────────────────────────────────────────────────
ZONE_TYPE_COLORS: dict[str, str] = {
    "normal":     "#4A90D9",
    "restricted": "#E67E22",
    "priority":   "#27AE60",
    "blocked":    "#7F8C8D",
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
BG_COLOR      = "#1E1E2E"
LINE_COLOR    = "#4E4E72"
TEXT_COLOR    = "#FFFFFF"
PANEL_COLOR   = "#24243A"
TRANSIT_COLOR = "#F1C40F"

CANVAS_W = 1500   # fixed logical canvas width
MARGIN_X = 80
MARGIN_Y = 70


# ── text-format parser ────────────────────────────────────────────────────────

def parse_text_history(raw: str) -> tuple[list[dict[int, str]], int]:
    TOKEN = re.compile(r'D(\d+)-(\S+)')
    turns: list[dict[int, str]] = []
    nb_drones = 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        snapshot: dict[int, str] = {}
        for m in TOKEN.finditer(line):
            did  = int(m.group(1))
            zone = m.group(2)
            snapshot[did] = zone
            nb_drones = max(nb_drones, did + 1)
        if snapshot:
            turns.append(snapshot)
    return turns, nb_drones


# ── layout builder ────────────────────────────────────────────────────────────

def _build_zone_positions(
    graph: graph_builder_test.Graph,
    all_zone_names: set[str],
) -> tuple[dict[str, tuple[int, int]], dict[str, int], int, int]:
    """
    Returns (zone_positions, zone_radii, canvas_w, canvas_h).

    Uses the zone x/y grid coords, but:
      - clamps extreme outliers (anything > median*10 is treated as a dead-end
        and placed at the same grid slot as its neighbour)
      - nudges zones that share the exact same (x,y) so they don't overlap
    """
    zones = list(graph.zones.values())

    # ── gather raw coords, detect outliers ──────────────────────────────────
    xs_raw = [z.x for z in zones]
    ys_raw = [z.y for z in zones]

    def median(lst):
        s = sorted(lst)
        n = len(s)
        return s[n // 2]

    med_x = median(xs_raw) or 1
    med_y = median(ys_raw) or 1
    THRESH = 100   # if a coord is >100× the median it's an outlier

    def clamp_x(v):
        return v if abs(v) <= abs(med_x) * THRESH + 50 else med_x

    def clamp_y(v):
        return v if abs(v) <= abs(med_y) * THRESH + 50 else med_y

    clamped = {z.name: (clamp_x(z.x), clamp_y(z.y)) for z in zones}

    # ── unique grid values after clamping ────────────────────────────────────
    unique_x = sorted({cx for cx, cy in clamped.values()})
    unique_y = sorted({cy for cx, cy in clamped.values()})

    xi = {v: i for i, v in enumerate(unique_x)}
    yi = {v: i for i, v in enumerate(unique_y)}

    n_cols = max(1, len(unique_x))
    n_rows = max(1, len(unique_y))

    col_step = max(70, (CANVAS_W - 2 * MARGIN_X) // n_cols)
    row_step = 80   # fixed row height — comfortable for labels

    canvas_h = MARGIN_Y * 2 + (n_rows - 1) * row_step + 60

    # ── group zones that land on the same grid cell ───────────────────────────
    grid_groups: dict[tuple[int, int], list[str]] = defaultdict(list)
    for name, (cx, cy) in clamped.items():
        grid_groups[(xi[cx], yi[cy])].append(name)

    zone_positions: dict[str, tuple[int, int]] = {}
    zone_radii:     dict[str, int]             = {}

    for (col, row), names in grid_groups.items():
        # y-axis: low y-value = bottom of screen → invert
        px_x = MARGIN_X + col * col_step
        px_y = MARGIN_Y + (n_rows - 1 - row) * row_step

        ordered = sorted(names)
        if len(ordered) == 1:
            zone_positions[ordered[0]] = (px_x, px_y)
            zone_radii[ordered[0]]     = 22
        else:
            # spread clashing zones in a small circle
            spread = 14 + min(16, len(ordered) * 3)
            for idx, name in enumerate(ordered):
                angle = (2 * math.pi * idx) / len(ordered)
                zone_positions[name] = (
                    int(px_x + math.cos(angle) * spread),
                    int(px_y + math.sin(angle) * spread * 0.7),
                )
                zone_radii[name] = 18

    # ── zones that appear only in snapshots (not in graph) ───────────────────
    missing = all_zone_names - set(zone_positions.keys())
    if missing:
        fallback_x = CANVAS_W - MARGIN_X - 40
        for idx, name in enumerate(sorted(missing)):
            zone_positions[name] = (fallback_x, MARGIN_Y + idx * 40)
            zone_radii[name]     = 16

    canvas_w = MARGIN_X * 2 + (n_cols - 1) * col_step + 80
    return zone_positions, zone_radii, canvas_w, canvas_h


# ── simulator ─────────────────────────────────────────────────────────────────

class DroneSimulator:
    def __init__(
        self,
        graph: graph_builder_test.Graph,
        raw_text: str,
        nb_drones: int | None = None,
    ) -> None:
        self.graph = graph
        self.turns, detected = parse_text_history(raw_text)
        self.nb_drones = nb_drones if nb_drones is not None else detected
        self.current_turn_idx = 0
        self.drone_states: dict[int, tuple] = {}

        # collect every zone name that appears in snapshots
        snap_zones: set[str] = set()
        for snap in self.turns:
            snap_zones.update(v for v in snap.values() if v != "[transit]")

        self.zone_positions, self.zone_radii, self.canvas_w, self.canvas_h = \
            _build_zone_positions(graph, snap_zones)

        print(f"[layout] {len(self.zone_positions)} zones  "
              f"canvas={self.canvas_w}x{self.canvas_h}  "
              f"turns={len(self.turns)}  drones={self.nb_drones}")

        self.root = tk.Tk()
        self.root.title("Fly-in Drone Simulator")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1300x800")
        self.root.minsize(900, 600)

        self._build_ui()
        self._reset_state()

        self.root.bind("<Return>",   self._on_enter)
        self.root.bind("<KP_Enter>", self._on_enter)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=BG_COLOR)
        outer.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        hbar = tk.Scrollbar(outer, orient=tk.HORIZONTAL)
        vbar = tk.Scrollbar(outer, orient=tk.VERTICAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT,  fill=tk.Y)

        self.canvas = tk.Canvas(
            outer,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=BG_COLOR,
            highlightthickness=0,
            xscrollcommand=hbar.set,
            yscrollcommand=vbar.set,
            scrollregion=(0, 0, self.canvas_w, self.canvas_h),
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hbar.config(command=self.canvas.xview)
        vbar.config(command=self.canvas.yview)

        ctrl = tk.Frame(self.root, bg=PANEL_COLOR)
        ctrl.pack(fill=tk.X, padx=6, pady=(0, 4))

        btn = dict(bg="#3A3A5E", fg=TEXT_COLOR, relief=tk.FLAT,
                   padx=12, pady=5, cursor="hand2")
        tk.Button(ctrl, text="⟳ Reset",     command=self._reset_state, **btn).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(ctrl, text="Next turn ▶", command=self._on_enter,    **btn).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Label(ctrl, text="  [Enter] to step",
                 bg=PANEL_COLOR, fg="#D0D0F0", font=("Arial", 10)).pack(side=tk.LEFT)

        self.info_var = tk.StringVar(value="Turn 0 / 0")
        tk.Label(ctrl, textvariable=self.info_var,
                 bg=PANEL_COLOR, fg="#A0A0CC",
                 font=("Courier", 11)).pack(side=tk.RIGHT, padx=12)

        log_frame = tk.Frame(self.root, bg=BG_COLOR)
        log_frame.pack(fill=tk.X, padx=6, pady=(0, 6))
        tk.Label(log_frame, text="Turn log:", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W)
        self.log_box = tk.Text(
            log_frame, height=4,
            bg=PANEL_COLOR, fg="#D7D7F7",
            font=("Courier", 10),
            state=tk.DISABLED, relief=tk.FLAT,
        )
        self.log_box.pack(fill=tk.X)

    # ── state ─────────────────────────────────────────────────────────────────

    def _reset_state(self) -> None:
        self.current_turn_idx = 0
        start_name = self.graph.start.name
        if self.turns:
            snap = self.turns[0]
            self.drone_states = {
                did: ("zone", snap.get(did, start_name))
                for did in range(self.nb_drones)
            }
        else:
            self.drone_states = {
                did: ("zone", start_name)
                for did in range(self.nb_drones)
            }
        self._draw_all()
        self._update_panel()

    def _advance_turn(self) -> None:
        if self.current_turn_idx >= len(self.turns):
            return
        snap = self.turns[self.current_turn_idx]
        for did in range(self.nb_drones):
            token = snap.get(did)
            if token is None:
                continue
            if token == "[transit]":
                prev = self.drone_states.get(did, ("zone", self.graph.start.name))
                from_zone = prev[1] if len(prev) > 1 else self.graph.start.name
                self.drone_states[did] = ("transit", from_zone, from_zone)
            else:
                self.drone_states[did] = ("zone", token)
        self.current_turn_idx += 1
        self._draw_all()
        self._update_panel(self.current_turn_idx - 1)

    def _on_enter(self, event=None):
        self._advance_turn()
        return "break"

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_all(self) -> None:
        self.canvas.delete("all")
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()
        self._draw_legend()

    def _draw_connections(self) -> None:
        drawn: set[frozenset] = set()
        for conn in self.graph.connections:
            key = frozenset({conn.zone_a.name, conn.zone_b.name})
            if key in drawn:
                continue
            drawn.add(key)
            a, b = conn.zone_a.name, conn.zone_b.name
            if a not in self.zone_positions or b not in self.zone_positions:
                continue
            x1, y1 = self.zone_positions[a]
            x2, y2 = self.zone_positions[b]
            self.canvas.create_line(x1, y1, x2, y2, fill=LINE_COLOR, width=2)
            cap = getattr(conn, "max_capacity", 1)
            if cap > 1:
                mx, my = (x1+x2)//2, (y1+y2)//2
                self.canvas.create_text(mx, my - 9,
                                        text=f"cap {cap}",
                                        fill="#B6B6D8", font=("Arial", 7))

    def _draw_zones(self) -> None:
        for name, (sx, sy) in self.zone_positions.items():
            zone   = self.graph.zones.get(name)
            radius = self.zone_radii.get(name, 22)

            # colour by type
            if zone is not None:
                type_val = getattr(zone.zone_type, "value", "normal")
                color = ZONE_TYPE_COLORS.get(type_val, "#4A90D9")
            else:
                color = "#888888"

            if name == self.graph.start.name:
                color = "#2ECC71"
            elif name == self.graph.end.name:
                color = "#E74C3C"

            # glow ring
            self.canvas.create_oval(
                sx-radius-5, sy-radius-5,
                sx+radius+5, sy+radius+5,
                fill="", outline=color, width=3,
            )
            # filled node
            self.canvas.create_oval(
                sx-radius, sy-radius,
                sx+radius, sy+radius,
                fill=color, outline="#FFFFFF", width=1,
            )
            # label (short, 2 lines max)
            label = name.replace("_", "\n")
            self.canvas.create_text(
                sx, sy, text=label,
                fill=TEXT_COLOR, font=("Arial", 6, "bold"),
                justify=tk.CENTER,
            )
            # capacity badge
            if zone is not None:
                max_d = getattr(zone, "max_drones", 1)
                if max_d > 1:
                    bx, by = sx + radius - 2, sy - radius + 2
                    self.canvas.create_oval(bx-8, by-8, bx+8, by+8,
                                            fill="#1B1B28", outline="#FFD700", width=2)
                    self.canvas.create_text(bx, by, text=str(max_d),
                                            fill="#FFD700", font=("Arial", 6, "bold"))

    def _draw_legend(self) -> None:
        lx, ly = 12, 12
        items = [
            ("#2ECC71",    "Start"),
            ("#E74C3C",    "End / Goal"),
            ("#4A90D9",    "Normal"),
            ("#E67E22",    "Restricted"),
            ("#27AE60",    "Priority"),
            ("#7F8C8D",    "Blocked"),
            (TRANSIT_COLOR,"In transit"),
        ]
        for idx, (color, label) in enumerate(items):
            y = ly + idx * 17
            self.canvas.create_rectangle(lx, y, lx+12, y+11, fill=color, outline="")
            self.canvas.create_text(lx+16, y+5, anchor=tk.W,
                                    text=label, fill=TEXT_COLOR, font=("Arial", 8))

    def _zone_center(self, name: str) -> tuple[int, int]:
        return self.zone_positions.get(name, (MARGIN_X, MARGIN_Y))

    def _drone_position(self, did: int, zone_groups: dict[str, list[int]]) -> tuple[int, int]:
        state = self.drone_states.get(did, ("zone", self.graph.start.name))
        kind  = state[0] if state else "zone"

        if kind == "transit" and len(state) == 3:
            x1, y1 = self._zone_center(state[1])
            x2, y2 = self._zone_center(state[2])
            mx, my  = (x1+x2)//2, (y1+y2)//2
            dx, dy  = x2-x1, y2-y1
            length  = max(1.0, math.hypot(dx, dy))
            offset  = 8 + (did % 3) * 3
            return (int(mx - dy/length * offset),
                    int(my + dx/length * offset))

        zone_name   = state[1] if len(state) > 1 else self.graph.start.name
        cx, cy      = self._zone_center(zone_name)
        drones_here = zone_groups.get(zone_name, [])
        if len(drones_here) <= 1:
            return cx, cy
        idx    = drones_here.index(did)
        r      = 10 + min(12, len(drones_here) * 2)
        angle  = (2 * math.pi * idx) / len(drones_here)
        return (int(cx + math.cos(angle) * r),
                int(cy + math.sin(angle) * r * 0.75))

    def _draw_drones(self) -> None:
        self.canvas.delete("drone")
        zone_groups: dict[str, list[int]] = defaultdict(list)
        for did, state in self.drone_states.items():
            if state and state[0] == "zone" and len(state) > 1:
                zone_groups[state[1]].append(did)
        for g in zone_groups.values():
            g.sort()

        for did in range(self.nb_drones):
            sx, sy  = self._drone_position(did, zone_groups)
            color   = DRONE_COLORS[did % len(DRONE_COLORS)]
            state   = self.drone_states.get(did, ("zone", self.graph.start.name))
            outline = TRANSIT_COLOR if (state and state[0] == "transit") else "#FFFFFF"
            self.canvas.create_oval(sx-7, sy-7, sx+7, sy+7,
                                    fill=color, outline=outline, width=2,
                                    tags="drone")
            self.canvas.create_text(sx, sy, text=str(did),
                                    fill="#000", font=("Arial", 6, "bold"),
                                    tags="drone")

    def _update_panel(self, turn_idx: int | None = None) -> None:
        total = len(self.turns)
        label = f"Turn {self.current_turn_idx} / {total}"
        if turn_idx is not None:
            label += f"   |   snapshot {turn_idx}"
        self.info_var.set(label)

        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        idx = self.current_turn_idx - 1
        if 0 <= idx < len(self.turns):
            snap = self.turns[idx]
            for did in sorted(snap):
                self.log_box.insert(tk.END, f"  D{did}: {snap[did]}\n")
        self.log_box.config(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    graph, nb_drones = graph_builder_test.build_graph()

    searcher  = A_stare_search.AStarSearch(graph, nb_drones)
    all_paths = searcher.get_paths()

    if not all_paths:
        print("No path found — check graph / start / end.")
        return

    path = all_paths[0]
    print(f"Paths found : {len(all_paths)}")
    print(f"Using path  : {path}")

    mover    = DroneMover(graph, nb_drones, path)
    raw_text: str = mover.drone_mover()

    print(f"Total turns : {mover.turns}")
    turns_parsed, _ = parse_text_history(raw_text)
    print(f"Turns parsed: {len(turns_parsed)}")
    print("--- snapshot preview (first 3 lines) ---")
    for line in raw_text.splitlines()[:3]:
        if line.strip():
            print(" ", line)

    sim = DroneSimulator(graph, raw_text, nb_drones)
    sim.run()


if __name__ == "__main__":
    main()