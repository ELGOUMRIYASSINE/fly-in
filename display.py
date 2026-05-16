import matplotlib.pyplot as plt
import matplotlib.colors as colors
from colorir import Palette
from matplotlib.widgets import Button
plt.rcParams["font.family"] = "DejaVu Sans"
DEFAULT_COLOR = "#7dd3fc"
COLOR_NAMES = Palette.load("css", warnings=False)
HARD_COLORS = {
    "rainbow":     ["red", "orange", "yellow", "green", "blue", "indigo", "violet"],
    "neongreen":   "#39ff14",
    "electricblue":"#7df9ff",
    "rosegold":    "#b76e79",
    # ↓ add whatever custom names your zones/drones use
    "amber":       "#f59e0b",
    "teal":        "#14b8a6",
    "indigo":      "#6366f1",  # CSS3 indigo is very dark; this is the nicer one
}

class Drawer:
    def __init__(self, graph, history):
        self.graph, self.history, self.turn = graph, history, 0
        self.states = self.make_states()
    def make_states(self):
        pos = {d.id: ("zone", self.graph.start.name) for d in self.graph.drones}
        step = {d.id: 0 for d in self.graph.drones}
        states = [pos.copy()]
        for moves in self.history:
            pos = pos.copy()
            for drone, start, end in moves:
                if end == "IN_TRANSITE":
                    next_zone = drone.path[step[drone.id] + 1]
                    pos[drone.id] = ("edge", start.name, next_zone)
                else:
                    step[drone.id] += 1; pos[drone.id] = ("zone", end.name)
            states.append(pos)
        return states
    def draw_map(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 6), facecolor="#f7f9fc")
        plt.subplots_adjust(bottom=0.18)
        self.back_btn = Button(self.fig.add_axes([0.30, 0.04, 0.15, 0.08]), "Back", color="#e8edf5", hovercolor="#d6e4ff")
        self.next_btn = Button(self.fig.add_axes([0.55, 0.04, 0.15, 0.08]), "Next", color="#e8edf5", hovercolor="#d6e4ff")
        self.back_btn.on_clicked(lambda event: self.move(-1))
        self.next_btn.on_clicked(lambda event: self.move(1))
        self.redraw(); plt.show()
    def move(self, value):
        self.turn = max(0, min(self.turn + value, len(self.states) - 1))
        self.redraw()
    def get_xy(self, place):
        if place[0] == "zone":
            zone = self.graph.zones[place[1]]; return zone.x, zone.y
        a, b = self.graph.zones[place[1]], self.graph.zones[place[2]]
        return (a.x + b.x) / 2, (a.y + b.y) / 2
    def get_color(self, color, index):
        name = str(color or "").lower().replace(" ", "").replace("_", "")
        if name in HARD_COLORS and type(HARD_COLORS[name]) is list:
            return HARD_COLORS[name][index % len(HARD_COLORS[name])]
        if name in HARD_COLORS:
            return HARD_COLORS[name]
        found = COLOR_NAMES.get(name)
        return found.hex() if found else (color if colors.is_color_like(color) else DEFAULT_COLOR)
    def redraw(self):
        self.ax.clear(); self.ax.set_title(f"Turn {self.turn} / {len(self.states) - 1}", fontsize=15, weight="bold", color="#1f2937", pad=14)
        self.ax.set_aspect("equal"); self.ax.axis("off"); self.ax.set_facecolor("#f7f9fc")
        for link in self.graph.connections:
            self.ax.plot([link.zone_a.x, link.zone_b.x], [link.zone_a.y, link.zone_b.y], color="#9aa7b8", linewidth=2, zorder=1)
        for i, zone in enumerate(self.graph.zones.values()):
            color = self.get_color(zone.color, i)
            self.ax.scatter(zone.x, zone.y, s=700, color=color, edgecolors="white", linewidth=2, zorder=2)
            self.ax.text(zone.x, zone.y + 0.26, zone.name, ha="center", fontsize=8, color="#111827", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#d1d5db", alpha=0.9), zorder=3)
        used = {}
        for drone in self.graph.drones:
            place = self.states[self.turn][drone.id]; x, y = self.get_xy(place)
            used[place] = used.get(place, 0) + 1
            x += (used[place] % 5 - 2) * 0.08; y += (used[place] // 5) * 0.08
            self.ax.scatter(x, y, s=170, color="#f59e0b", edgecolors="white", linewidth=1.5, zorder=4)
            self.ax.text(x, y, f"D{drone.id}", ha="center", va="center", fontsize=7, weight="bold", color="white", zorder=5)
        self.fig.canvas.draw_idle()
