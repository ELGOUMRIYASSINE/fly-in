import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.markers import MarkerStyle
from matplotlib.widgets import Button
import matplotlib.animation as animation
from typing import Any, cast
import random
from graph_builder_test import Graph


class Drawer:
    """Render the graph and drone history using matplotlib controls."""
    DEFAULT_COLOR = "#7dd3fc"
    COLOR_NAMES = colors.CSS4_COLORS  # type: ignore[attr-defined]
    HARD_COLORS: dict[str, str] = {
        "rainbow":     "#8F00FF",
        "neongreen":   "#39ff14",
        "electricblue": "#7df9ff",
        "rosegold":    "#b76e79",
        "amber":       "#f59e0b",
        "teal":        "#14b8a6",
        "indigo":      "#6366f1",
    }

    def __init__(self, graph: Graph, history: list[list[tuple[Any, Any, Any]]]) -> None:
        """Initialize the drawer with graph data and move history."""
        self.graph, self.history, self.turn = graph, history, 0
        self.states = self.make_states()
        self.playing = False
        self.anim: animation.FuncAnimation | None = None
        self.drones_colors: dict[int, str] = {}

    def make_states(self) -> list[dict[int, tuple[Any, ...]]]:
        """Expand move history into per-turn drone placement states."""
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
        """Reset playback to the first turn and redraw."""
        self.turn = 0
        self.redraw()

    def draw_map(self) -> None:
        """Create the matplotlib figure, controls, and initial render."""
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
        """Start or pause animation playback."""
        if self.playing:
            self.playing = False
            if self.anim:
                self.anim.event_source.stop()  # type: ignore[attr-defined]
            self.play_btn.label.set_text("Play")   # type: ignore[attr-defined]
            self.play_btn.color = "#a3e635"        # type: ignore[attr-defined]
        else:
            if self.turn >= len(self.states) - 1:
                self.turn = 0  # restart from beginning
            self.playing = True
            self.play_btn.label.set_text("Pause")  # type: ignore[attr-defined]
            self.play_btn.color = "#fca5a5"        # type: ignore[attr-defined]
            self.anim = animation.FuncAnimation(
                self.fig,
                self._anim_step,
                interval=400,  # ms between turns, lower = faster
                repeat=False
            )
        self.fig.canvas.draw_idle()

    def _anim_step(self, frame: int) -> list[Any]:
        """Advance the animation one turn when playing."""
        if not self.playing or self.turn >= len(self.states) - 1:
            self.playing = False
            self.play_btn.label.set_text("Play")  # type: ignore[attr-defined]
            self.play_btn.color = "#a3e635"       # type: ignore[attr-defined]
            if self.anim:
                self.anim.event_source.stop()     # type: ignore[attr-defined]
            return []
        self.turn += 1
        self.redraw()
        return []

    def move(self, value: int) -> None:
        """Step forward or backward by a single turn."""
        if self.playing:
            self.toggle_play()  # stop playing when manually stepping
        self.turn = max(0, min(self.turn + value, len(self.states) - 1))
        self.redraw()

    def get_xy(self, place: tuple[Any, ...]) -> tuple[float, float]:
        """Return the xy position for a zone or edge midpoint."""
        if place[0] == "zone":
            zone = self.graph.zones[place[1]]
            return zone.x, zone.y
        a, b = self.graph.zones[place[1]], self.graph.zones[place[2]]
        return (a.x + b.x) / 2, (a.y + b.y) / 2

    def get_color(self, color: str | None, index: int) -> str:
        """Resolve a color name or palette entry for a zone index."""
        name = str(color or "").lower().replace(" ", "").replace("_", "")
        if name in self.HARD_COLORS and isinstance(self.HARD_COLORS[name], list):
            palette = cast(list[str], self.HARD_COLORS[name])
            return palette[index % len(palette)]
        if name in self.HARD_COLORS:
            return self.HARD_COLORS[name]
        if name in self.COLOR_NAMES:
            return str(self.COLOR_NAMES[name])
        if isinstance(color, str) and colors.is_color_like(color):
            return color
        return self.DEFAULT_COLOR

    def colories(self) -> None:
        for drone in self.graph.drones:
            self.drones_colors[drone.id] = random.choice(list(self.COLOR_NAMES.keys()))

    def redraw(self) -> None:
        """Redraw the full scene for the current turn."""
        self.ax.clear()
        self.ax.set_title(f"Turn {self.turn} / {len(self.states) - 1}",
                          fontsize=15, weight="bold", color="#1f2937", pad=14)
        zones = list(self.graph.zones.values())
        self.ax.axis("off")
        self.ax.set_facecolor("#fcf7fb")

        for link in self.graph.connections:
            self.ax.plot([link.zone_a.x, link.zone_b.x], [link.zone_a.y,
                         link.zone_b.y], color="#9aa7b8", linewidth=10, zorder=1, alpha=0.7)
        for i, zone in enumerate(zones):
            color = self.get_color(zone.color, i)
            self.ax.scatter(zone.x, zone.y, s=700, color=color,
                            edgecolors="white", linewidth=2, zorder=2,)
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
        if self.drones_colors == {}:
            self.colories()  # give each drone a random color
        for drone in self.graph.drones:
            place = self.states[self.turn][drone.id]
            x, y = self.get_xy(place)
            self.ax.scatter(x, y, s=250, color=self.drones_colors[drone.id],
                            edgecolors="white", linewidth=1.5, zorder=4,
                            marker=MarkerStyle("X"))
            self.ax.text(x, y, f"D{drone.id}", ha="center", va="center",
                         fontsize=8, weight="bold", color="white", zorder=5)

        self.ax.autoscale()
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        pad = 0.5
        self.ax.set_xlim(x0 - pad, x1 + pad)
        self.ax.set_ylim(y0 - pad, y1 + pad)

        self.fig.canvas.draw_idle()
