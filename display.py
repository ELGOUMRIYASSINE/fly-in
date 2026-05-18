import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.widgets import Button
import matplotlib.animation as animation
from typing import Any, cast

from graph_builder_test import Graph

DEFAULT_COLOR = "#7dd3fc"
COLOR_NAMES = colors.CSS4_COLORS
HARD_COLORS: dict[str, str | list[str]] = {
    "rainbow":     ["red", "orange", "yellow", "green", "blue", "indigo", "violet"],
    "neongreen":   "#39ff14",
    "electricblue": "#7df9ff",
    "rosegold":    "#b76e79",
    "amber":       "#f59e0b",
    "teal":        "#14b8a6",
    "indigo":      "#6366f1",
}


class Drawer:
    def __init__(self, graph: Graph, history: list[list[tuple[Any, Any, Any]]]) -> None:
        self.graph, self.history, self.turn = graph, history, 0
        self.states = self.make_states()
        self.playing = False
        self.anim: animation.FuncAnimation | None = None

    def make_states(self) -> list[dict[int, tuple[Any, ...]]]:
        if self.graph.start is None:
            raise RuntimeError("Graph is missing start hub")
        pos: dict[int, tuple[Any, ...]] = {
            d.id: ("zone", self.graph.start.name) for d in self.graph.drones
        }
        step = {d.id: 0 for d in self.graph.drones}
        states = [pos.copy()]
        for moves in self.history:
            pos = pos.copy()
            for drone, start, end in moves:
                if end == "IN_TRANSITE":
                    next_zone = drone.path[step[drone.id] + 1]
                    pos[drone.id] = ("edge", start.name, next_zone)
                else:
                    step[drone.id] += 1
                    pos[drone.id] = ("zone", end.name)
            states.append(pos)
        return states

    def restart_animation(self) -> None:
        self.turn = 0
        self.redraw()

    def draw_map(self) -> None:
        self.fig, self.ax = plt.subplots(figsize=(10, 6), facecolor="#4A4848")
        plt.subplots_adjust(bottom=0.18)
        # (left, bottom, width, height) 0 -> 1
        self.back_btn = Button(self.fig.add_axes(
            (0.30, 0.04, 0.15, 0.08)), "N9ess", color="#C5C5C5", hovercolor="#d6e4ff")
        self.next_btn = Button(self.fig.add_axes(
            (0.55, 0.04, 0.15, 0.08)), "Zid", color="#C5C5C5", hovercolor="#d6e4ff")
        self.play_btn = Button(self.fig.add_axes(
            (0.80, 0.04, 0.15, 0.08)), "Play", color="#a3e635", hovercolor="#bef264")
        self.restart = Button(self.fig.add_axes(
            (0.05, 0.04, 0.15, 0.08)), "Restart", color="#f87171", hovercolor="#fca5a5"
        )
        self.back_btn.on_clicked(lambda event: self.move(-1))
        self.next_btn.on_clicked(lambda event: self.move(1))
        self.play_btn.on_clicked(lambda event: self.toggle_play())
        self.restart.on_clicked(lambda event: self.restart_animation())
        self.redraw()
        plt.show()

    def toggle_play(self) -> None:
        if self.playing:
            self.playing = False
            if self.anim:
                self.anim.event_source.stop()
            self.play_btn.label.set_text("Play")
            self.play_btn.color = "#a3e635"
        else:
            if self.turn >= len(self.states) - 1:
                self.turn = 0  # restart from beginning
            self.playing = True
            self.play_btn.label.set_text("Pause")
            self.play_btn.color = "#fca5a5"
            self.anim = animation.FuncAnimation(
                self.fig,
                self._anim_step,
                interval=300,  # ms between turns, lower = faster
                repeat=False
            )
        self.fig.canvas.draw_idle()

    def _anim_step(self, frame: int) -> list[Any]:
        if not self.playing or self.turn >= len(self.states) - 1:
            self.playing = False
            self.play_btn.label.set_text("Play")
            self.play_btn.color = "#a3e635"
            if self.anim:
                self.anim.event_source.stop()
            return []
        self.turn += 1
        self.redraw()
        return []

    def move(self, value: int) -> None:
        if self.playing:
            self.toggle_play()  # stop playing when manually stepping
        self.turn = max(0, min(self.turn + value, len(self.states) - 1))
        self.redraw()

    def get_xy(self, place: tuple[Any, ...]) -> tuple[float, float]:
        if place[0] == "zone":
            zone = self.graph.zones[place[1]]
            return zone.x, zone.y
        a, b = self.graph.zones[place[1]], self.graph.zones[place[2]]
        return (a.x + b.x) / 2, (a.y + b.y) / 2

    def get_color(self, color: str | None, index: int) -> str:
        name = str(color or "").lower().replace(" ", "").replace("_", "")
        if name in HARD_COLORS and isinstance(HARD_COLORS[name], list):
            palette = cast(list[str], HARD_COLORS[name])
            return palette[index % len(palette)]
        if name in HARD_COLORS:
            return cast(str, HARD_COLORS[name])
        if name in COLOR_NAMES:
            return str(COLOR_NAMES[name])
        if isinstance(color, str) and colors.is_color_like(color):
            return color
        return DEFAULT_COLOR

    def redraw(self) -> None:
        self.ax.clear()
        self.ax.set_title(f"Turn {self.turn} / {len(self.states) - 1}",
                          fontsize=15, weight="bold", color="#1f2937", pad=14)
        zones = list(self.graph.zones.values())
        self.ax.axis("off")
        self.ax.set_facecolor("#fcf7fb")  # came back to here

        for link in self.graph.connections:
            self.ax.plot([link.zone_a.x, link.zone_b.x], [link.zone_a.y,
                         link.zone_b.y], color="#9aa7b8", linewidth=10, zorder=1, alpha=0.7)   
        for i, zone in enumerate(zones):
            color = self.get_color(zone.color, i)
            self.ax.scatter(zone.x, zone.y, s=700, color=color,
                            edgecolors="black", linewidth=2, zorder=2,)
            p = 0.2
            if i % 2 == 0:
                p = -0.2
            self.ax.text(
                zone.x,
                zone.y + p,
                zone.name,
                ha="center",
                fontsize=8,
                color="#111827",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    fc="white",
                    ec="#d1d5db",
                    alpha=0.9,
                ),
                zorder=3,
            )

        used: dict[tuple[Any, ...], int] = {}
        for drone in self.graph.drones:
            place = self.states[self.turn][drone.id]
            x, y = self.get_xy(place)
            used[place] = used.get(place, 0) + 1
            count = used[place]
            x += ((count - 1) % 3 - 1) * 0.22
            y += ((count - 1) // 3) * 0.22
            self.ax.scatter(x, y, s=250, color="#f59e0b",
                            edgecolors="white", linewidth=1.5, zorder=4, marker="X")
            self.ax.text(x, y, f"D{drone.id}", ha="center", va="center",
                         fontsize=8, weight="bold", color="white", zorder=5)

        self.ax.autoscale()
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        pad = 0.5
        self.ax.set_xlim(x0 - pad, x1 + pad)
        self.ax.set_ylim(y0 - pad, y1 + pad)

        self.fig.canvas.draw_idle()
