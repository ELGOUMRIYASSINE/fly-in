from __future__ import annotations

import json
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import graph_builder_test


HOST = "127.0.0.1"
PORT = 8765


def build_route(graph: graph_builder_test.Graph) -> list[str]:
        queue = deque([graph.start.name])
        came_from: dict[str, str | None] = {graph.start.name: None}

        while queue:
                current_name = queue.popleft()
                if current_name == graph.end.name:
                        break

                current_zone = graph.zones[current_name]
                for neighbor in current_zone.neighbors:
                        if neighbor.name not in came_from:
                                came_from[neighbor.name] = current_name
                                queue.append(neighbor.name)

        if graph.end.name not in came_from:
                raise RuntimeError("No route found from start to end")

        route: list[str] = []
        current_name: str | None = graph.end.name
        while current_name is not None:
                route.append(current_name)
                current_name = came_from[current_name]

        return list(reversed(route))


def safe_layout_value(value: int) -> int:
        return 0 if abs(value) > 1000 else value


def build_payload() -> dict[str, Any]:
        graph, drone_count = graph_builder_test.build_graph()
        route = build_route(graph)

        nodes = []
        for zone in graph.zones.values():
                nodes.append(
                        {
                                "name": zone.name,
                                "x": zone.x,
                                "y": safe_layout_value(zone.y),
                                "type": zone.zone_type.value,
                                "max_drones": zone.max_drones,
                                "color": zone.color,
                        }
                )

        links = []
        seen_links: set[tuple[str, str]] = set()
        for connection in graph.connections:
                edge_key = tuple(sorted((connection.zone_a.name, connection.zone_b.name)))
                if edge_key in seen_links:
                        continue
                seen_links.add(edge_key)
                links.append(
                        {
                                "source": connection.zone_a.name,
                                "target": connection.zone_b.name,
                                "capacity": connection.max_capacity,
                        }
                )

        return {
                "drone_count": drone_count,
                "route": route,
                "nodes": nodes,
                "links": links,
                "start": graph.start.name,
                "end": graph.end.name,
        }


PAGE = r"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Drone Route Viewer</title>
    <style>
        :root {
            color-scheme: dark;
            --bg: #08111f;
            --panel: rgba(12, 20, 34, 0.82);
            --panel-border: rgba(148, 163, 184, 0.18);
            --text: #e5eefb;
            --muted: #9fb0c7;
            --accent: #60a5fa;
            --accent-2: #34d399;
            --danger: #fb7185;
            --warning: #fbbf24;
            --node-normal: #94a3b8;
            --node-blocked: #f87171;
            --node-restricted: #f59e0b;
            --node-priority: #22c55e;
            --shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
        }

        * { box-sizing: border-box; }
        html, body { height: 100%; }
        body {
            margin: 0;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(96, 165, 250, 0.18), transparent 32%),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 28%),
                linear-gradient(180deg, #06101d 0%, #0a1322 42%, #050b14 100%);
            overflow: hidden;
        }

        .app {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 340px;
            gap: 18px;
            height: 100%;
            padding: 18px;
        }

        .stage, .panel {
            border: 1px solid var(--panel-border);
            border-radius: 24px;
            background: var(--panel);
            backdrop-filter: blur(18px);
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .stage {
            position: relative;
            min-width: 0;
            display: flex;
            flex-direction: column;
        }

        .stage-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 20px 10px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }

        .title {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .title h1 {
            margin: 0;
            font-size: 18px;
            letter-spacing: 0.02em;
        }

        .title p {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(96, 165, 250, 0.14);
            border: 1px solid rgba(96, 165, 250, 0.28);
            color: #dbeafe;
            font-size: 12px;
            white-space: nowrap;
        }

        .canvas-wrap {
            position: relative;
            flex: 1;
            min-height: 0;
            padding: 10px;
        }

        svg {
            width: 100%;
            height: 100%;
            display: block;
            border-radius: 18px;
            background:
                radial-gradient(circle at center, rgba(15, 23, 42, 0.92), rgba(2, 6, 23, 0.98));
        }

        .panel {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 18px;
        }

        .panel h2 {
            margin: 0;
            font-size: 15px;
            letter-spacing: 0.01em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }

        .stat {
            padding: 14px;
            border-radius: 16px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.14);
        }

        .stat span {
            display: block;
            color: var(--muted);
            font-size: 12px;
            margin-bottom: 6px;
        }

        .stat strong {
            font-size: 18px;
        }

        .controls {
            display: grid;
            gap: 12px;
            padding: 14px;
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.14);
        }

        .control-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        button {
            appearance: none;
            border: 1px solid rgba(96, 165, 250, 0.3);
            background: rgba(30, 41, 59, 0.95);
            color: var(--text);
            border-radius: 12px;
            padding: 10px 12px;
            cursor: pointer;
            font: inherit;
            transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease;
        }

        button:hover {
            transform: translateY(-1px);
            border-color: rgba(96, 165, 250, 0.55);
            background: rgba(37, 49, 70, 0.98);
        }

        button.primary {
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(14, 165, 233, 0.92));
            border-color: transparent;
        }

        label {
            display: grid;
            gap: 8px;
            color: var(--muted);
            font-size: 12px;
        }

        input[type="range"] {
            width: 100%;
            accent-color: var(--accent);
        }

        .legend {
            display: grid;
            gap: 10px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--muted);
            font-size: 13px;
        }

        .swatch {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            flex: 0 0 auto;
        }

        .feed {
            flex: 1;
            min-height: 0;
            padding: 14px;
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.14);
            overflow: auto;
        }

        .feed-item {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.08);
            font-size: 13px;
        }

        .feed-item:last-child { border-bottom: 0; }
        .muted { color: var(--muted); }

        .tooltip {
            position: absolute;
            pointer-events: none;
            opacity: 0;
            transform: translate(-50%, calc(-100% - 12px));
            background: rgba(2, 6, 23, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.22);
            color: var(--text);
            padding: 10px 12px;
            border-radius: 12px;
            font-size: 12px;
            max-width: 220px;
            box-shadow: var(--shadow);
            transition: opacity 0.12s ease;
        }

        @media (max-width: 980px) {
            body { overflow: auto; }
            .app {
                grid-template-columns: 1fr;
                height: auto;
            }
            .stage { min-height: 70vh; }
        }
    </style>
</head>
<body>
    <div class="app">
        <section class="stage">
            <div class="stage-top">
                <div class="title">
                    <h1>Drone Route Viewer</h1>
                    <p>Interactive map of the route found through the graph.</p>
                </div>
                <div class="badge" id="statusBadge">Loading route...</div>
            </div>
            <div class="canvas-wrap">
                <svg id="map" viewBox="0 0 1400 820" preserveAspectRatio="xMidYMid meet"></svg>
                <div class="tooltip" id="tooltip"></div>
            </div>
        </section>

        <aside class="panel">
            <h2>Playback</h2>
            <div class="stats">
                <div class="stat"><span>Turn</span><strong id="turnValue">0</strong></div>
                <div class="stat"><span>Drones</span><strong id="droneValue">0</strong></div>
                <div class="stat"><span>Route</span><strong id="routeValue">0</strong></div>
                <div class="stat"><span>Speed</span><strong id="speedValue">1.0x</strong></div>
            </div>

            <div class="controls">
                <div class="control-row">
                    <button class="primary" id="playBtn">Play</button>
                    <button id="stepBackBtn">Step -</button>
                    <button id="stepForwardBtn">Step +</button>
                    <button id="resetBtn">Reset</button>
                </div>
                <label>
                    Timeline
                    <input id="timeline" type="range" min="0" max="100" value="0" />
                </label>
                <label>
                    Speed
                    <input id="speed" type="range" min="0.25" max="3" value="1" step="0.25" />
                </label>
            </div>

            <div>
                <h2>Legend</h2>
                <div class="legend">
                    <div class="legend-item"><span class="swatch" style="background: var(--node-normal);"></span>Normal zone</div>
                    <div class="legend-item"><span class="swatch" style="background: var(--node-restricted);"></span>Restricted zone</div>
                    <div class="legend-item"><span class="swatch" style="background: var(--node-priority);"></span>Priority zone</div>
                    <div class="legend-item"><span class="swatch" style="background: var(--accent);"></span>Drone path</div>
                </div>
            </div>

            <div>
                <h2>Active Drones</h2>
                <div class="feed" id="droneFeed"></div>
            </div>
        </aside>
    </div>

    <script>
        const DATA = __PAYLOAD__;

        const svg = document.getElementById('map');
        const tooltip = document.getElementById('tooltip');
        const statusBadge = document.getElementById('statusBadge');
        const turnValue = document.getElementById('turnValue');
        const droneValue = document.getElementById('droneValue');
        const routeValue = document.getElementById('routeValue');
        const speedValue = document.getElementById('speedValue');
        const droneFeed = document.getElementById('droneFeed');
        const playBtn = document.getElementById('playBtn');
        const stepBackBtn = document.getElementById('stepBackBtn');
        const stepForwardBtn = document.getElementById('stepForwardBtn');
        const resetBtn = document.getElementById('resetBtn');
        const timeline = document.getElementById('timeline');
        const speed = document.getElementById('speed');

        const nodes = DATA.nodes;
        const links = DATA.links;
        const route = DATA.route;
        const routeSet = new Set(route);

        const coordinates = new Map();
        const duplicateCounter = new Map();

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        for (const node of nodes) {
            minX = Math.min(minX, node.x);
            maxX = Math.max(maxX, node.x);
            minY = Math.min(minY, node.y);
            maxY = Math.max(maxY, node.y);
        }

        function keyFor(node) {
            return `${node.x}:${node.y}`;
        }

        function assignCoordinates() {
            for (const node of nodes) {
                const key = keyFor(node);
                const index = duplicateCounter.get(key) || 0;
                duplicateCounter.set(key, index + 1);
                const offset = index * 0.35;
                coordinates.set(node.name, {
                    x: node.x,
                    y: node.y + offset,
                });
            }
        }

        assignCoordinates();

        // compute and store zone radii so drones can be placed "inside" zones
        const zoneRadii = new Map();
        for (const node of nodes) {
            const isRoute = routeSet.has(node.name);
            const radius = node.name === DATA.start ? 18 : node.name === DATA.end ? 20 : isRoute ? 16 : 13;
            zoneRadii.set(node.name, radius);
        }
        function scalePoint(point) {
            const padding = 90;
            const innerWidth = 1400 - padding * 2;
            const innerHeight = 820 - padding * 2;
            const xRange = Math.max(1, maxX - minX);
            const yRange = Math.max(1, maxY - minY);
            const x = padding + ((point.x - minX) / xRange) * innerWidth;
            const y = padding + innerHeight - ((point.y - minY) / yRange) * innerHeight;
            return { x, y };
        }

        function zoneColor(type) {
            if (type === 'restricted') return 'var(--node-restricted)';
            if (type === 'priority') return 'var(--node-priority)';
            if (type === 'blocked') return 'var(--node-blocked)';
            return 'var(--node-normal)';
        }

        function clearSvg() {
            while (svg.firstChild) svg.removeChild(svg.firstChild);
        }

        function makeSvg(tag, attrs = {}) {
            const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
            for (const [key, value] of Object.entries(attrs)) {
                element.setAttribute(key, value);
            }
            return element;
        }

        function lineFor(source, target, attrs = {}) {
            const a = scalePoint(coordinates.get(source));
            const b = scalePoint(coordinates.get(target));
            return makeSvg('line', {
                x1: a.x,
                y1: a.y,
                x2: b.x,
                y2: b.y,
                ...attrs,
            });
        }

        function routePathPoints() {
            return route.map((name) => scalePoint(coordinates.get(name)));
        }

        function drawMap() {
            clearSvg();

            const defs = makeSvg('defs');
            const glow = makeSvg('filter', { id: 'glow', x: '-50%', y: '-50%', width: '200%', height: '200%' });
            glow.appendChild(makeSvg('feGaussianBlur', { stdDeviation: '4', result: 'blur' }));
            glow.appendChild(makeSvg('feMerge', {}));
            defs.appendChild(glow);

            const routeGradient = makeSvg('linearGradient', { id: 'routeGradient', x1: '0%', y1: '0%', x2: '100%', y2: '0%' });
            routeGradient.appendChild(makeSvg('stop', { offset: '0%', 'stop-color': '#38bdf8' }));
            routeGradient.appendChild(makeSvg('stop', { offset: '100%', 'stop-color': '#22c55e' }));
            defs.appendChild(routeGradient);
            svg.appendChild(defs);

            for (const link of links) {
                svg.appendChild(lineFor(link.source, link.target, {
                    stroke: 'rgba(148, 163, 184, 0.18)',
                    'stroke-width': 2,
                    'stroke-linecap': 'round',
                }));
            }

            for (let i = 0; i < route.length - 1; i += 1) {
                const from = route[i];
                const to = route[i + 1];
                svg.appendChild(lineFor(from, to, {
                    stroke: 'url(#routeGradient)',
                    'stroke-width': 6,
                    'stroke-linecap': 'round',
                    filter: 'url(#glow)',
                }));
            }

            for (const node of nodes) {
                const point = scalePoint(coordinates.get(node.name));
                const isRoute = routeSet.has(node.name);
                const radius = zoneRadii.get(node.name) || (isRoute ? 14 : 11);

                const halo = makeSvg('circle', {
                    cx: point.x,
                    cy: point.y,
                    r: radius + 14,
                    fill: zoneColor(node.type),
                    opacity: '0.22',
                });
                svg.appendChild(halo);

                const circle = makeSvg('circle', {
                    cx: point.x,
                    cy: point.y,
                    r: radius,
                    fill: zoneColor(node.type),
                    'fill-opacity': '0.94',
                    stroke: isRoute ? 'rgba(219,234,254,0.85)' : 'rgba(255,255,255,0.06)',
                    'stroke-width': isRoute ? 3.5 : 2.5,
                });
                circle.addEventListener('mouseenter', (event) => {
                    tooltip.style.opacity = '1';
                    tooltip.textContent = `${node.name} | ${node.type} | capacity ${node.max_drones}`;
                    tooltip.style.left = `${event.offsetX}px`;
                    tooltip.style.top = `${event.offsetY}px`;
                });
                circle.addEventListener('mousemove', (event) => {
                    tooltip.style.left = `${event.offsetX}px`;
                    tooltip.style.top = `${event.offsetY}px`;
                });
                circle.addEventListener('mouseleave', () => {
                    tooltip.style.opacity = '0';
                });
                svg.appendChild(circle);

                const label = makeSvg('text', {
                    x: point.x,
                    y: point.y - (radius + 12),
                    fill: '#dbeafe',
                    'font-size': '12',
                    'font-weight': '600',
                    'text-anchor': 'middle',
                });
                label.textContent = node.name;
                svg.appendChild(label);
            }
        }

        const droneState = Array.from({ length: DATA.drone_count }, (_, index) => ({
            id: index,
            delay: index * 1.25,
        }));

        let currentStep = 0;
        let playing = false;
        let timer = null;
        const maxStep = route.length - 1 + droneState.length * 1.25 + 4;

        function colorForDrone(index) {
            const hue = (index * 137.5) % 360;
            return `hsl(${hue} 92% 66%)`;
        }

        // deterministic jitter per drone+node so drones sit nicely "inside" zones
        function jitterFor(droneId, nodeName) {
            const s = `${droneId}:${nodeName}`;
            let h = 2166136261 >>> 0;
            for (let i = 0; i < s.length; i++) {
                h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0;
            }
            const angle = (h % 360) * Math.PI / 180;
            const mag = 0.35 + ((h >>> 8) % 100) / 100 * 0.65; // 0.35..1.0
            return { dx: Math.cos(angle) * mag, dy: Math.sin(angle) * mag };
        }

        function updateStats() {
            turnValue.textContent = String(Math.round(currentStep));
            droneValue.textContent = String(DATA.drone_count);
            routeValue.textContent = String(route.length);
            speedValue.textContent = `${Number(speed.value).toFixed(2).replace(/\.00$/, '')}x`;
            timeline.max = String(Math.max(1, Math.ceil(maxStep)));
            timeline.value = String(currentStep);
            statusBadge.textContent = playing ? 'Playing' : 'Paused';
            playBtn.textContent = playing ? 'Pause' : 'Play';
        }

        function dronePosition(drone) {
            const local = currentStep - drone.delay;
            if (local < 0) return null;
            const segment = Math.min(Math.floor(local), route.length - 1);
            const rawProgress = Math.min(Math.max(local - segment, 0), 1);
            const currentName = route[segment];
            const nextName = route[Math.min(segment + 1, route.length - 1)];
            const current = scalePoint(coordinates.get(currentName));
            const next = scalePoint(coordinates.get(nextName));

            // snap into zone interiors near the ends of segments
            const snapIn = 0.25; // <= snap to source
            const snapOut = 0.75; // >= snap to target
            if (rawProgress <= snapIn || (segment >= route.length - 1 && rawProgress >= 0)) {
                const r = (zoneRadii.get(currentName) || 12) - 4;
                const j = jitterFor(drone.id, currentName);
                return {
                    x: current.x + j.dx * r,
                    y: current.y + j.dy * r,
                    arrived: segment >= route.length - 1 && rawProgress >= 1,
                    node: currentName,
                };
            }
            if (rawProgress >= snapOut) {
                const r = (zoneRadii.get(nextName) || 12) - 4;
                const j = jitterFor(drone.id, nextName);
                return {
                    x: next.x + j.dx * r,
                    y: next.y + j.dy * r,
                    arrived: segment >= route.length - 1,
                    node: nextName,
                };
            }

            // in transit between zone interiors
            const t = (rawProgress - snapIn) / (snapOut - snapIn);
            return {
                x: current.x + (next.x - current.x) * t,
                y: current.y + (next.y - current.y) * t,
                arrived: false,
                node: currentName,
            };
        }

        function drawDrones() {
            const existing = svg.querySelectorAll('.drone-layer');
            existing.forEach((node) => node.remove());

            const layer = makeSvg('g', { class: 'drone-layer' });
            const active = [];

            for (const drone of droneState) {
                const position = dronePosition(drone);
                if (!position) continue;
                active.push({ drone, position });

                const dot = makeSvg('circle', {
                    cx: position.x,
                    cy: position.y,
                    r: position.arrived ? 7.5 : 6.5,
                    fill: colorForDrone(drone.id),
                    stroke: 'rgba(2,6,23,0.95)',
                    'stroke-width': 2.5,
                });
                layer.appendChild(dot);
            }

            svg.appendChild(layer);

            droneFeed.innerHTML = active.slice(0, 12).map(({ drone, position }) => {
                return `<div class="feed-item"><span>D${drone.id} <span class="muted">${position.node}</span></span><span>${position.arrived ? 'arrived' : 'moving'}</span></div>`;
            }).join('') || '<div class="muted">No drones active at this step.</div>';
        }

        function render() {
            updateStats();
            drawMap();
            drawDrones();
        }

        function setStep(value) {
            currentStep = Math.max(0, Math.min(maxStep, Number(value)));
            render();
        }

        function tick() {
            if (!playing) return;
            currentStep += Number(speed.value) * 0.35;
            if (currentStep >= maxStep) {
                currentStep = maxStep;
                playing = false;
            }
            render();
            if (playing) {
                timer = window.setTimeout(tick, 30);
            }
        }

        playBtn.addEventListener('click', () => {
            playing = !playing;
            render();
            if (playing) tick();
            if (!playing && timer) {
                window.clearTimeout(timer);
            }
        });

        stepBackBtn.addEventListener('click', () => setStep(currentStep - 1));
        stepForwardBtn.addEventListener('click', () => setStep(currentStep + 1));
        resetBtn.addEventListener('click', () => {
            playing = false;
            currentStep = 0;
            if (timer) window.clearTimeout(timer);
            render();
        });
        timeline.addEventListener('input', (event) => setStep(event.target.value));
        speed.addEventListener('input', () => render());

        window.addEventListener('keydown', (event) => {
            if (event.code === 'Space') {
                event.preventDefault();
                playBtn.click();
            } else if (event.code === 'ArrowLeft') {
                setStep(currentStep - 1);
            } else if (event.code === 'ArrowRight') {
                setStep(currentStep + 1);
            }
        });

        render();
        updateStats();
    </script>
</body>
</html>
"""


class DroneViewerHandler(BaseHTTPRequestHandler):
        payload = build_payload()

        def _send_text(self, text: str, content_type: str = "text/html; charset=utf-8") -> None:
                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
                if self.path == "/data":
                        payload = json.dumps(self.payload)
                        self._send_text(payload, "application/json; charset=utf-8")
                        return

                html = PAGE.replace("__PAYLOAD__", json.dumps(self.payload))
                self._send_text(html)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return


def main() -> None:
        server = ThreadingHTTPServer((HOST, PORT), DroneViewerHandler)
        url = f"http://{HOST}:{PORT}"
        print(f"Drone viewer running at {url}")
        print("Open that address in your browser to watch the drones move.")
        try:
                server.serve_forever()
        except KeyboardInterrupt:
                pass
        finally:
                server.server_close()


if __name__ == "__main__":
        main()