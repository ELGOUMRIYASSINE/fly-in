"""
╔══════════════════════════════════════════════════════╗
║          DRONE SWARM VISUALIZER  —  pygame           ║
║  Drop-in replacement for the matplotlib Drawer.      ║
║  Plug your Graph + history in at the bottom.         ║
╚══════════════════════════════════════════════════════╝

Requirements:
    pip install pygame

Usage:
    Replace the `if __name__ == "__main__":` block at the
    bottom with your real Graph + history, then run:
        python drone_visualizer.py
"""

import math
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import pygame
import pygame.gfxdraw

# ──────────────────────────────────────────────────────────────────────────────
# THEME
# ──────────────────────────────────────────────────────────────────────────────
BG          = (222, 198, 148)
PANEL_BG    = (80,  58,  32)
EDGE_COL    = (130,  96,  52)
EDGE_ACTIVE = (245, 178,  82)
NODE_BORDER = (244, 232, 202)
TEXT_BRIGHT = (250, 245, 232)
TEXT_DIM    = (172, 135,  88)
ACCENT      = (232, 160,  68)
ACCENT2     = (190, 140,  78)
TRAIL_COL   = (232, 160,  68, 60)

DRONE_PALETTE = [
    (255, 100, 100),
    (100, 255, 160),
    (100, 180, 255),
    (255, 220,  60),
    (200, 100, 255),
    (255, 160,  60),
    ( 60, 230, 230),
    (255, 130, 200),
]

NODE_PALETTE = [
    (30,  60, 120),
    (50,  90,  50),
    (90,  40,  80),
    (30,  80,  90),
    (90,  70,  20),
    (60,  30,  90),
    (20,  80,  70),
    (90,  50,  30),
]

# ──────────────────────────────────────────────────────────────────────────────
# MOCK GRAPH OBJECTS (replace with your real imports)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Zone:
    name: str
    x: float
    y: float
    color: str | None = None

@dataclass
class Link:
    zone_a: Zone
    zone_b: Zone

@dataclass
class Drone:
    id: int
    path: list[str] = field(default_factory=list)

@dataclass
class Graph:
    zones: dict[str, Zone] = field(default_factory=dict)
    connections: list[Link] = field(default_factory=list)
    drones: list[Drone] = field(default_factory=list)
    start: Zone | None = None


# ──────────────────────────────────────────────────────────────────────────────
# PARTICLE SYSTEM
# ──────────────────────────────────────────────────────────────────────────────

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 2.5)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.max_life = random.uniform(0.4, 1.2)
        self.color = color
        self.size = random.uniform(2, 5)

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.03 * dt * 60          # gentle gravity
        self.life -= dt / self.max_life
        return self.life > 0

    def draw(self, surf: pygame.Surface) -> None:
        alpha = int(self.life * 200)
        r, g, b = self.color
        s = max(1, int(self.size * self.life))
        pygame.gfxdraw.filled_circle(surf, int(self.x), int(self.y), s,
                                     (r, g, b, alpha))


# ──────────────────────────────────────────────────────────────────────────────
# TRAIL SYSTEM
# ──────────────────────────────────────────────────────────────────────────────

class Trail:
    MAX = 30

    def __init__(self, color: tuple[int, int, int]) -> None:
        self.pts: list[tuple[float, float]] = []
        self.color = color

    def add(self, x: float, y: float) -> None:
        self.pts.append((x, y))
        if len(self.pts) > self.MAX:
            self.pts.pop(0)

    def draw(self, surf: pygame.Surface) -> None:
        if len(self.pts) < 2:
            return
        n = len(self.pts)
        for i in range(1, n):
            alpha = int(200 * (i / n))
            width = max(1, int(4 * (i / n)))
            r, g, b = self.color
            # draw with gfxdraw for alpha support
            x1, y1 = int(self.pts[i - 1][0]), int(self.pts[i - 1][1])
            x2, y2 = int(self.pts[i][0]),     int(self.pts[i][1])
            pygame.draw.line(surf, (r, g, b, alpha), (x1, y1), (x2, y2), width)


# ──────────────────────────────────────────────────────────────────────────────
# PULSE RING (appears when drone lands on a zone)
# ──────────────────────────────────────────────────────────────────────────────

class PulseRing:
    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        self.x, self.y = x, y
        self.color = color
        self.life = 1.0
        self.radius = 14.0

    def update(self, dt: float) -> bool:
        self.life -= dt * 1.5
        self.radius += dt * 80
        return self.life > 0

    def draw(self, surf: pygame.Surface) -> None:
        a = int(self.life * 180)
        r, g, b = self.color
        pygame.gfxdraw.aacircle(surf, int(self.x), int(self.y),
                                int(self.radius), (r, g, b, a))


# ──────────────────────────────────────────────────────────────────────────────
# MAIN VISUALIZER
# ──────────────────────────────────────────────────────────────────────────────

class DroneVisualizer:
    W, H     = 1280, 800
    PANEL_W  = 280           # right-side info panel
    MAP_PAD  = 60            # padding around the graph area

    ANIM_SPEED = 1.5         # turns per second during auto-play

    def __init__(self, graph: Graph,
                 history: list[list[tuple[Any, Any, Any]]]) -> None:
        self.graph   = graph
        self.history = history
        self.turn    = 0
        self.playing = False
        self._play_acc = 0.0

        self.particles: list[Particle] = []
        self.rings:     list[PulseRing] = []
        self.trails: dict[int, Trail] = {}

        # assign colors
        self.drone_colors: dict[int, tuple[int, int, int]] = {
            d.id: DRONE_PALETTE[i % len(DRONE_PALETTE)]
            for i, d in enumerate(graph.drones)
        }
        self.node_colors: dict[str, tuple[int, int, int]] = {
            name: NODE_PALETTE[i % len(NODE_PALETTE)]
            for i, name in enumerate(graph.zones)
        }

        self.states = self._make_states()
        self._prev_places: dict[int, tuple[Any, ...]] = {}

        # smooth drone positions (lerp)
        self._display_pos: dict[int, tuple[float, float]] = {}
        self._target_pos:  dict[int, tuple[float, float]] = {}
        self._lerp_t:      dict[int, float] = {}
        self.panel_scroll = 0

        # background dust field; generated once the window size is known
        self.stars: list[tuple[int, int, float]] = []

    # ── state machine ─────────────────────────────────────────────────────────

    def _make_states(self) -> list[dict[int, tuple[Any, ...]]]:
        if self.graph.start is None:
            raise RuntimeError("Graph has no start hub")
        pos: dict[int, tuple[Any, ...]] = {
            d.id: ("zone", self.graph.start.name) for d in self.graph.drones
        }
        step = {d.id: 0 for d in self.graph.drones}
        states = [pos.copy()]
        for moves in self.history:
            pos = pos.copy()
            for drone, start, end in moves:
                if end == "IN_TRANSITE":
                    nxt = drone.path[step[drone.id] + 1]
                    pos[drone.id] = ("edge", start.name, nxt)
                else:
                    step[drone.id] += 1
                    pos[drone.id] = ("zone", end.name)
            states.append(pos)
        return states

    # ── coordinate mapping ────────────────────────────────────────────────────

    def _map_rect(self) -> pygame.Rect:
        """The drawable area (excluding right panel and padding)."""
        return pygame.Rect(self.MAP_PAD, self.MAP_PAD,
                           self.W - self.PANEL_W - self.MAP_PAD * 2,
                           self.H - self.MAP_PAD * 2)

    def _world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        zones = list(self.graph.zones.values())
        xs = [z.x for z in zones]
        ys = [z.y for z in zones]
        mn_x, mx_x = min(xs), max(xs)
        mn_y, mx_y = min(ys), max(ys)
        rng_x = mx_x - mn_x or 1
        rng_y = mx_y - mn_y or 1
        r = self._map_rect()
        sx = r.left + (wx - mn_x) / rng_x * r.width
        sy = r.bottom - (wy - mn_y) / rng_y * r.height
        return sx, sy

    def _place_to_screen(self, place: tuple[Any, ...]) -> tuple[float, float]:
        if place[0] == "zone":
            z = self.graph.zones[place[1]]
            return self._world_to_screen(z.x, z.y)
        a = self.graph.zones[place[1]]
        b = self.graph.zones[place[2]]
        return self._world_to_screen((a.x + b.x) / 2, (a.y + b.y) / 2)

    # ── turn control ──────────────────────────────────────────────────────────

    def _go_to(self, t: int) -> None:
        prev = self.states[self.turn]
        self.turn = max(0, min(t, len(self.states) - 1))
        cur  = self.states[self.turn]
        for drone in self.graph.drones:
            did   = drone.id
            place = cur[did]
            tx, ty = self._place_to_screen(place)
            self._target_pos[did]  = (tx, ty)
            self._lerp_t[did]      = 0.0
            # spawn particles + ring when arriving at a zone
            if place[0] == "zone" and prev.get(did) != place:
                col = self.drone_colors[did]
                for _ in range(18):
                    self.particles.append(Particle(tx, ty, col))
                self.rings.append(PulseRing(tx, ty, col))
            # init display pos if first time
            if did not in self._display_pos:
                self._display_pos[did] = (tx, ty)
            # init trail
            if did not in self.trails:
                self.trails[did] = Trail(self.drone_colors[did])

    # ── update ────────────────────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        # auto-play
        if self.playing:
            self._play_acc += dt
            if self._play_acc >= 1.0 / self.ANIM_SPEED:
                self._play_acc = 0.0
                if self.turn < len(self.states) - 1:
                    self._go_to(self.turn + 1)
                else:
                    self.playing = False

        # lerp drone display positions
        LERP_SPEED = 6.0
        for drone in self.graph.drones:
            did = drone.id
            if did not in self._display_pos:
                continue
            dx, dy = self._display_pos[did]
            tx, ty = self._target_pos.get(did, (dx, dy))
            alpha  = min(1.0, (self._lerp_t.get(did, 1.0) + dt * LERP_SPEED))
            self._lerp_t[did]     = alpha
            nx = dx + (tx - dx) * alpha
            ny = dy + (ty - dy) * alpha
            self._display_pos[did] = (nx, ny)
            self.trails[did].add(nx, ny)

        # particles
        self.particles = [p for p in self.particles if p.update(dt)]
        self.rings      = [r for r in self.rings      if r.update(dt)]

    # ── draw helpers ──────────────────────────────────────────────────────────

    def _draw_stars(self, surf: pygame.Surface) -> None:
        t = time.time()
        for x, y, size in self.stars:
            bri = int(60 + 40 * math.sin(t * 0.7 + x * 0.05))
            pygame.gfxdraw.filled_circle(surf, x, y, max(1, int(size)),
                                         (bri + 60, bri + 25, 10, 120))

    def _make_stars(self) -> list[tuple[int, int, float]]:
        return [(random.randint(0, max(1, self.W - 1)),
                 random.randint(0, max(1, self.H - 1)),
                 random.uniform(0.3, 1.5)) for _ in range(120)]

    def _draw_background(self, surf: pygame.Surface) -> None:
        top = (242, 224, 180)
        bottom = (197, 160, 96)
        for y in range(self.H):
            mix = y / max(1, self.H - 1)
            r = int(top[0] + (bottom[0] - top[0]) * mix)
            g = int(top[1] + (bottom[1] - top[1]) * mix)
            b = int(top[2] + (bottom[2] - top[2]) * mix)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.W, y))

        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(glow, int(self.W * 0.82), int(self.H * 0.2),
                                     int(min(self.W, self.H) * 0.18), (255, 236, 185, 26))
        pygame.gfxdraw.filled_circle(glow, int(self.W * 0.78), int(self.H * 0.22),
                                     int(min(self.W, self.H) * 0.10), (255, 243, 208, 20))
        surf.blit(glow, (0, 0))

        dune = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        points = [
            (0, int(self.H * 0.78)),
            (int(self.W * 0.18), int(self.H * 0.72)),
            (int(self.W * 0.36), int(self.H * 0.80)),
            (int(self.W * 0.56), int(self.H * 0.74)),
            (int(self.W * 0.76), int(self.H * 0.83)),
            (self.W, int(self.H * 0.76)),
            (self.W, self.H),
            (0, self.H),
        ]
        pygame.draw.polygon(dune, (186, 138, 72, 65), points)
        surf.blit(dune, (0, 0))

    def _draw_grid(self, surf: pygame.Surface) -> None:
        r = self._map_rect()
        step = 60
        for gx in range(r.left, r.right, step):
            pygame.draw.line(surf, (25, 30, 50), (gx, r.top), (gx, r.bottom))
        for gy in range(r.top, r.bottom, step):
            pygame.draw.line(surf, (25, 30, 50), (r.left, gy), (r.right, gy))

    def _draw_edges(self, surf: pygame.Surface) -> None:
        cur = self.states[self.turn]
        active_pairs: set[frozenset[str]] = set()
        for drone in self.graph.drones:
            place = cur[drone.id]
            if place[0] == "edge":
                active_pairs.add(frozenset([place[1], place[2]]))

        for link in self.graph.connections:
            ax, ay = self._world_to_screen(link.zone_a.x, link.zone_a.y)
            bx, by = self._world_to_screen(link.zone_b.x, link.zone_b.y)
            pair = frozenset([link.zone_a.name, link.zone_b.name])
            if pair in active_pairs:
                # glowing active edge
                for w, alpha in ((14, 30), (8, 70), (3, 180)):
                    pygame.draw.line(surf, (*EDGE_ACTIVE, alpha),
                                     (int(ax), int(ay)), (int(bx), int(by)), w)
            else:
                pygame.draw.line(surf, EDGE_COL,
                                 (int(ax), int(ay)), (int(bx), int(by)), 3)

    def _draw_nodes(self, surf: pygame.Surface, font_sm: pygame.font.Font,
                    font_label: pygame.font.Font) -> None:
        cur = self.states[self.turn]
        occupied: set[str] = set()
        for drone in self.graph.drones:
            p = cur[drone.id]
            if p[0] == "zone":
                occupied.add(p[1])

        for i, (name, zone) in enumerate(self.graph.zones.items()):
            sx, sy = self._world_to_screen(zone.x, zone.y)
            col = self.node_colors[name]
            r   = 22

            # outer glow ring if occupied
            if name in occupied:
                for wr, wa in ((36, 20), (30, 50), (26, 100)):
                    pygame.gfxdraw.filled_circle(surf, int(sx), int(sy), wr,
                                                 (*ACCENT, wa))

            # node body
            pygame.gfxdraw.filled_circle(surf, int(sx), int(sy), r, (*col, 255))
            pygame.gfxdraw.aacircle(surf,     int(sx), int(sy), r, NODE_BORDER)

            # node name label  (above / below alternating)
            label   = font_label.render(name, True, TEXT_BRIGHT)
            lw, lh  = label.get_size()
            offset  = -r - 10 if i % 2 == 0 else r + 6
            lx      = int(sx - lw / 2)
            ly      = int(sy + offset - lh / 2)
            # pill background
            pad = 6
            pill = pygame.Surface((lw + pad * 2, lh + pad), pygame.SRCALPHA)
            pill.fill((10, 15, 30, 200))
            pygame.draw.rect(pill, (*ACCENT, 120),
                             pill.get_rect(), border_radius=8, width=1)
            surf.blit(pill, (lx - pad, ly - pad // 2))
            surf.blit(label, (lx, ly))

    def _draw_trails(self, surf: pygame.Surface) -> None:
        trail_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for trail in self.trails.values():
            trail.draw(trail_surf)
        surf.blit(trail_surf, (0, 0))

    def _draw_drones(self, surf: pygame.Surface,
                     font_sm: pygame.font.Font) -> None:
        t = time.time()
        for drone in self.graph.drones:
            did = drone.id
            if did not in self._display_pos:
                continue
            dx, dy = self._display_pos[did]
            col    = self.drone_colors[did]
            r      = 14

            # pulsing halo
            pulse = 0.5 + 0.5 * math.sin(t * 4 + did * 1.3)
            halo_r = int(r + 8 + pulse * 6)
            pygame.gfxdraw.filled_circle(surf, int(dx), int(dy), halo_r,
                                         (*col, 40))

            # body
            pygame.gfxdraw.filled_circle(surf, int(dx), int(dy), r, (*col, 230))
            pygame.gfxdraw.aacircle(surf, int(dx), int(dy), r, (255, 255, 255, 200))

            # rotor cross lines
            for angle in (0, math.pi / 2):
                ex = int(dx + math.cos(t * 6 + angle + did) * (r - 3))
                ey = int(dy + math.sin(t * 6 + angle + did) * (r - 3))
                pygame.draw.line(surf, (255, 255, 255, 160),
                                 (int(dx), int(dy)), (ex, ey), 2)

            # ID label
            lbl = font_sm.render(f"D{did}", True, (10, 10, 20))
            lw, lh = lbl.get_size()
            surf.blit(lbl, (int(dx - lw / 2), int(dy - lh / 2)))

    def _draw_particles(self, surf: pygame.Surface) -> None:
        ps = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for p in self.particles:
            p.draw(ps)
        surf.blit(ps, (0, 0))

    def _draw_rings(self, surf: pygame.Surface) -> None:
        rs = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for ring in self.rings:
            ring.draw(rs)
        surf.blit(rs, (0, 0))

    def _draw_panel(self, surf: pygame.Surface, font_title: pygame.font.Font,
                    font_sm: pygame.font.Font, font_xs: pygame.font.Font) -> None:
        px = self.W - self.PANEL_W
        panel = pygame.Surface((self.PANEL_W, self.H), pygame.SRCALPHA)
        panel.fill((*PANEL_BG, 230))
        # vertical accent line
        pygame.draw.line(panel, (*ACCENT, 120), (0, 0), (0, self.H), 2)
        surf.blit(panel, (px, 0))

        # title
        title = font_title.render("fly-project 1337", True, ACCENT)
        surf.blit(title, (px + 20, 22))
        sub = font_sm.render("Drone Visualizer", True, TEXT_DIM)
        surf.blit(sub, (px + 22, 60))

        # turn counter
        pygame.draw.rect(surf, (25, 35, 70),
                         (px + 16, 95, self.PANEL_W - 32, 52),
                         border_radius=10)
        tc = font_title.render(f"Turn-{self.turn:03d}", True, TEXT_BRIGHT)
        surf.blit(tc, (px + 24, 100))
        tc2 = font_xs.render(f"of {len(self.states) - 1} turns", True, TEXT_DIM)
        surf.blit(tc2, (px + 26, 134))

        # progress bar
        bx, by = px + 16, 158
        bw, bh = self.PANEL_W - 32, 8
        pygame.draw.rect(surf, (30, 40, 70), (bx, by, bw, bh), border_radius=4)
        progress = self.turn / max(1, len(self.states) - 1)
        pygame.draw.rect(surf, ACCENT,
                         (bx, by, int(bw * progress), bh), border_radius=4)

        # drone list with scrolling
        list_top = 185
        list_bottom = self.H - 190
        list_width = self.PANEL_W - 32
        sep = font_xs.render("─" * 22, True, (40, 50, 80))
        surf.blit(sep, (px + 16, list_top)); list_top += 22
        head = font_sm.render("DRONES", True, TEXT_DIM)
        surf.blit(head, (px + 16, list_top)); list_top += 26

        row_h = 44
        row_w = list_bottom - list_top
        total_rows = len(self.graph.drones) * row_h
        max_scroll = max(0, total_rows - row_w)
        self.panel_scroll = max(0, min(self.panel_scroll, max_scroll))

        cur = self.states[self.turn]
        for index, drone in enumerate(self.graph.drones):
            col   = self.drone_colors[drone.id]
            place = cur[drone.id]
            if place[0] == "zone":
                where = f"@ {place[1]}"
                status_col = (100, 255, 140)
            else:
                where = f"→ {place[2]}"
                status_col = (255, 200, 60)

            y_off = list_top + index * row_h - self.panel_scroll
            if y_off + row_h < list_top or y_off > list_bottom:
                continue

            pygame.gfxdraw.filled_circle(surf, px + 24, y_off + 9, 7, (*col, 220))
            did_lbl  = font_sm.render(f"D{drone.id}", True, TEXT_BRIGHT)
            loc_lbl  = font_xs.render(where, True, status_col)
            surf.blit(did_lbl,  (px + 38, y_off))
            surf.blit(loc_lbl,  (px + 38, y_off + 18))

        if max_scroll > 0:
            track_x = px + self.PANEL_W - 12
            track_y = list_top
            track_h = row_w
            pygame.draw.rect(surf, (100, 74, 40),
                             (track_x, track_y, 5, track_h), border_radius=3)
            thumb_h = max(24, int(track_h * (row_w / total_rows)))
            thumb_y = track_y + int((track_h - thumb_h) * (self.panel_scroll / max_scroll))
            pygame.draw.rect(surf, ACCENT,
                             (track_x - 1, thumb_y, 7, thumb_h), border_radius=3)

        # controls legend
        y_off = self.H - 170
        surf.blit(sep, (px + 16, y_off)); y_off += 22
        ctrl_head = font_sm.render("CONTROLS", True, TEXT_DIM)
        surf.blit(ctrl_head, (px + 16, y_off)); y_off += 26
        for key, action in [
            ("← →", "prev / next turn"),
            ("SPACE", "play / pause"),
            ("R",     "restart"),
            ("ESC",   "quit"),
        ]:
            k_lbl = font_xs.render(key,    True, ACCENT)
            a_lbl = font_xs.render(action, True, TEXT_DIM)
            surf.blit(k_lbl, (px + 16, y_off))
            surf.blit(a_lbl, (px + 80, y_off))
            y_off += 22

        # play / pause badge
        status_txt  = "▶ PLAYING" if self.playing else "⏸ PAUSED"
        status_col2 = (100, 255, 140) if self.playing else TEXT_DIM
        badge = font_xs.render(status_txt, True, status_col2)
        surf.blit(badge, (px + 16, self.H - 30))

    def _draw_scan_line(self, surf: pygame.Surface) -> None:
        """Subtle CRT-style scan line sweep."""
        t    = time.time()
        y    = int((t * 120) % self.H)
        line = pygame.Surface((self.W, 2), pygame.SRCALPHA)
        line.fill((180, 220, 255, 12))
        surf.blit(line, (0, y))

    def _scroll_panel(self, amount: int) -> None:
        row_h = 44
        list_top = 185 + 22 + 26
        list_bottom = self.H - 190
        viewport_h = max(0, list_bottom - list_top)
        total_h = len(self.graph.drones) * row_h
        max_scroll = max(0, total_h - viewport_h)
        self.panel_scroll = max(0, min(self.panel_scroll + amount, max_scroll))

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption("fly-project 1337")
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            desktop_w, desktop_h = desktop_sizes[0]
            self.W = max(1280, min(desktop_w - 80, 1800))
            self.H = max(800, min(desktop_h - 80, 1200))
        flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        screen = pygame.display.set_mode((self.W, self.H), flags)
        clock  = pygame.time.Clock()
        self.stars = self._make_stars()

        pygame.font.init()
        try:
            font_title = pygame.font.SysFont("consolas",     38, bold=True)
            font_sm    = pygame.font.SysFont("consolas",     16, bold=True)
            font_xs    = pygame.font.SysFont("consolas",     13)
            font_label = pygame.font.SysFont("consolas",     12, bold=True)
        except Exception:
            font_title = pygame.font.SysFont(None, 38, bold=True)
            font_sm    = pygame.font.SysFont(None, 16, bold=True)
            font_xs    = pygame.font.SysFont(None, 13)
            font_label = pygame.font.SysFont(None, 12, bold=True)

        # initialise drone positions at turn 0
        for drone in self.graph.drones:
            place = self.states[0][drone.id]
            tx, ty = self._place_to_screen(place)
            self._display_pos[drone.id] = (tx, ty)
            self._target_pos[drone.id]  = (tx, ty)
            self._lerp_t[drone.id]      = 1.0
            self.trails[drone.id]       = Trail(self.drone_colors[drone.id])

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            # events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.W = max(900, event.w)
                    self.H = max(600, event.h)
                    screen = pygame.display.set_mode((self.W, self.H), flags)
                    self.stars = self._make_stars()
                    self.panel_scroll = 0
                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if mouse_x >= self.W - self.PANEL_W:
                        self._scroll_panel(-event.y * 36)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RIGHT:
                        self.playing = False
                        self._go_to(self.turn + 1)
                    elif event.key == pygame.K_LEFT:
                        self.playing = False
                        self._go_to(self.turn - 1)
                    elif event.key == pygame.K_SPACE:
                        if not self.playing and self.turn >= len(self.states) - 1:
                            self._go_to(0)
                        self.playing = not self.playing
                        self._play_acc = 0.0
                    elif event.key == pygame.K_r:
                        self.playing = False
                        self._go_to(0)

            self._update(dt)

            # ── render ────────────────────────────────────────────────────────
            self._draw_background(screen)
            self._draw_stars(screen)
            self._draw_grid(screen)
            self._draw_edges(screen)
            self._draw_trails(screen)
            self._draw_rings(screen)
            self._draw_nodes(screen, font_sm, font_label)
            self._draw_particles(screen)
            self._draw_drones(screen, font_sm)
            self._draw_panel(screen, font_title, font_sm, font_xs)
            self._draw_scan_line(screen)

            pygame.display.flip()

        pygame.quit()


# ──────────────────────────────────────────────────────────────────────────────
# DEMO  —  replace this block with your real Graph + history
# ──────────────────────────────────────────────────────────────────────────────

def _build_demo() -> tuple[Graph, list[list[tuple[Any, Any, Any]]]]:
    """Build a synthetic 8-node graph with 3 drones for testing."""

    g = Graph()
    positions = [
        ("HUB",    0.5, 0.5),
        ("Alpha",  0.1, 0.1),
        ("Bravo",  0.9, 0.1),
        ("Charlie",0.9, 0.9),
        ("Delta",  0.1, 0.9),
        ("Echo",   0.5, 0.0),
        ("Foxtrot",1.0, 0.5),
        ("Golf",   0.5, 1.0),
    ]
    for name, x, y in positions:
        g.zones[name] = Zone(name=name, x=x, y=y)

    edges = [
        ("HUB","Alpha"), ("HUB","Bravo"), ("HUB","Charlie"),
        ("HUB","Delta"), ("HUB","Echo"),  ("HUB","Foxtrot"),
        ("HUB","Golf"),  ("Alpha","Echo"),("Bravo","Foxtrot"),
        ("Charlie","Golf"),("Delta","Golf"),
    ]
    for a, b in edges:
        g.connections.append(Link(g.zones[a], g.zones[b]))

    g.start = g.zones["HUB"]

    paths = [
        ["HUB","Alpha","Echo","HUB","Golf","HUB"],
        ["HUB","Bravo","Foxtrot","Charlie","Golf","Delta","HUB"],
        ["HUB","Echo","Alpha","HUB","Delta","Golf","HUB"],
    ]
    g.drones = [Drone(id=i, path=paths[i]) for i in range(3)]

    # generate history from paths  (simplified: one move per turn)
    history: list[list[tuple[Any, Any, Any]]] = []
    max_turns = max(len(p) - 1 for p in paths)
    steps = {d.id: 0 for d in g.drones}

    for turn in range(max_turns):
        moves: list[tuple[Any, Any, Any]] = []
        for drone in g.drones:
            s = steps[drone.id]
            if s + 1 < len(drone.path):
                start_z = g.zones[drone.path[s]]
                end_z   = g.zones[drone.path[s + 1]]
                # alternate: go IN_TRANSITE first, then arrive next turn
                # for simplicity just arrive directly
                moves.append((drone, start_z, end_z))
                steps[drone.id] += 1
        history.append(moves)

    return g, history


if __name__ == "__main__":
    graph, history = _build_demo()
    viz = DroneVisualizer(graph, history)
    viz.run()