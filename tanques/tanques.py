"""
TANQUES NEON  -  Juego de tanques para 2 jugadores (mismo teclado)
Hecho con Python + Tkinter (sin dependencias externas).

JUGADOR 1 (cian)    : W / S avanzar-retroceder, A / D girar, F o ESPACIO disparar
JUGADOR 2 (magenta) : ↑ / ↓ avanzar-retroceder, ← / → girar, ENTER o CTRL derecho disparar

Las balas rebotan en las paredes (¡y también pueden darte a ti!).
Gana la partida el primero en llegar a 5 puntos.
R = reiniciar partida  ·  Esc = salir
"""
import math
import random
import time
import tkinter as tk

# ───────────────────────── Configuración ─────────────────────────
CELL, COLS, ROWS = 30, 30, 20
AW, AH = CELL * COLS, CELL * ROWS          # arena 900 x 600
HUD_H = 70

TR = 15            # radio del tanque
BR = 4             # radio de la bala
SPEED = 150        # px/s
TURN = 3.3         # rad/s
B_SPEED = 340      # px/s
B_LIFE = 6.0       # segundos de vida de una bala
COOL = 0.30        # tiempo entre disparos
MAX_B = 5          # balas simultáneas por jugador
WIN = 5            # puntos para ganar
READY_T = 2.4      # cuenta regresiva

BG = "#0a0d1c"
PANEL = "#0f1328"
WALL = "#5b6cff"
C1 = "#00e5ff"
C2 = "#ff2e93"
GOLD = "#ffd23f"
WHITE = "#ffffff"

# Cada mapa es la mitad izquierda (15 columnas); la derecha se genera en espejo.
MAPS = [
    [  # Bloques
        "###############",
        "#..............",
        "#..............",
        "#...###........",
        "#...#..........",
        "#...#.....#....",
        "#.........#....",
        "#.........#....",
        "#..............",
        "#......##......",
        "#..............",
        "#..............",
        "#......##......",
        "#..............",
        "#.........#....",
        "#.........#....",
        "#...#.....#....",
        "#...#..........",
        "#...###........",
        "###############",
    ],
    [  # Pasillos
        "###############",
        "#..............",
        "#..##########..",
        "#..............",
        "#..............",
        "#.....#........",
        "#.....#.....###",
        "#.....#........",
        "#..............",
        "#...#..........",
        "#...#..........",
        "#...#..........",
        "#..............",
        "#..............",
        "#.....#........",
        "#.....#.....###",
        "#.....#........",
        "#..............",
        "#..##########..",
        "###############",
    ],
    [  # Laberinto abierto
        "###############",
        "#..............",
        "#.....#........",
        "#.....#........",
        "#..............",
        "#..##..........",
        "#..#...........",
        "#........#.....",
        "#........#.....",
        "#..............",
        "#..............",
        "#..............",
        "#........#.....",
        "#........#.....",
        "#..#...........",
        "#..##..........",
        "#..............",
        "#.....#........",
        "#.....#........",
        "###############",
    ],
]


def blend(c1, c2, t):
    """Mezcla c1 con c2. t=1 -> c1, t=0 -> c2."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(b[i] + (a[i] - b[i]) * t) for i in range(3))


class Tank:
    def __init__(self, idx, color, keys):
        self.idx = idx
        self.color = color
        self.keys = keys
        self.score = 0
        self.reset(0, 0, 0)

    def reset(self, x, y, ang):
        self.x, self.y, self.ang = x, y, ang
        self.alive = True
        self.last = 0.0


class Game:
    def __init__(self, root):
        self.root = root
        root.title("TANQUES NEON  ·  2 jugadores")
        root.configure(bg=BG)
        root.resizable(False, False)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        tw, th = AW, AH + HUD_H
        root.geometry(f"{tw}x{th}+{max(0, (sw - tw) // 2)}+{max(0, (sh - th) // 2 - 20)}")

        self.hud = tk.Canvas(root, width=AW, height=HUD_H, bg=BG, highlightthickness=0)
        self.hud.pack()
        self.cv = tk.Canvas(root, width=AW, height=AH, bg=BG, highlightthickness=0)
        self.cv.pack()

        self.pressed = set()
        root.bind("<KeyPress>", self.on_key_down)
        root.bind("<KeyRelease>", self.on_key_up)
        root.bind("<FocusOut>", lambda e: self.pressed.clear())
        self.cv.bind("<Button-1>", lambda e: self.restart_if_over())
        self.hud.bind("<Button-1>", lambda e: self.restart_if_over())
        root.bind("<Escape>", lambda e: root.destroy())

        self.tanks = [
            Tank(1, C1, {"left": "a", "right": "d", "up": "w", "down": "s",
                         "shoot": {"f", "space"}}),
            Tank(2, C2, {"left": "left", "right": "right", "up": "up", "down": "down",
                         "shoot": {"return", "kp_enter", "control_r"}}),
        ]
        self.map_index = -1
        self.walls = set()
        self.bullets = []
        self.particles = []
        self.rings = []
        self.state = "ready"
        self.state_at = 0.0
        self.fight_at = -99.0
        self.msg = ""
        self.msg_color = GOLD
        self.match_winner = None

        self.new_round()
        self.last = time.perf_counter()
        root.lift()
        root.attributes("-topmost", True)
        root.after(500, lambda: root.attributes("-topmost", False))
        root.focus_force()
        self.tick()

    # ── entrada ──
    def on_key_down(self, e):
        k = e.keysym.lower()
        self.pressed.add(k)
        if k == "r":
            self.new_match()
        elif k in ("return", "space", "kp_enter") and self.state == "matchover":
            self.restart_if_over()

    def on_key_up(self, e):
        self.pressed.discard(e.keysym.lower())

    def restart_if_over(self):
        if self.state == "matchover" and time.perf_counter() - self.state_at > 1.2:
            self.new_match()

    # ── partidas y rondas ──
    def new_match(self):
        for t in self.tanks:
            t.score = 0
        self.match_winner = None
        self.new_round()

    def new_round(self):
        now = time.perf_counter()
        choices = [i for i in range(len(MAPS)) if i != self.map_index]
        self.map_index = random.choice(choices)
        self.build_map(MAPS[self.map_index])
        self.tanks[0].reset(CELL * 2 + CELL / 2, AH / 2 - CELL / 2 + 0, 0.0)
        self.tanks[1].reset(AW - CELL * 2 - CELL / 2, AH / 2 - CELL / 2 + 0, math.pi)
        self.bullets.clear()
        self.particles.clear()
        self.rings.clear()
        self.state = "ready"
        self.state_at = now
        self.fight_at = -99.0
        self.pressed.clear()

    def build_map(self, half):
        self.walls = set()
        for r, row in enumerate(half):
            full = row + row[::-1]
            for c, ch in enumerate(full):
                if ch == "#":
                    self.walls.add((r, c))
        self.cv.delete("all")
        for x in range(0, AW + 1, CELL):
            self.cv.create_line(x, 0, x, AH, fill=blend("#5b6cff", BG, 0.07), tags="map")
        for y in range(0, AH + 1, CELL):
            self.cv.create_line(0, y, AW, y, fill=blend("#5b6cff", BG, 0.07), tags="map")
        for x1, y1, x2, y2 in self.wall_rects():
            x1, y1, x2, y2 = x1 + 2, y1 + 2, x2 - 2, y2 - 2
            for w, f in ((9, 0.10), (5, 0.22)):
                self.cv.create_rectangle(x1, y1, x2, y2, outline=blend(WALL, BG, f),
                                         width=w, tags="map")
            self.cv.create_rectangle(x1, y1, x2, y2, fill=blend(WALL, BG, 0.16),
                                     outline=WALL, width=2, tags="map")

    def wall_rects(self):
        seen, rects = set(), []
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) in self.walls and (r, c) not in seen:
                    c2 = c
                    while (r, c2 + 1) in self.walls and (r, c2 + 1) not in seen:
                        c2 += 1
                    r2 = r
                    while all((r2 + 1, cc) in self.walls and (r2 + 1, cc) not in seen
                              for cc in range(c, c2 + 1)):
                        r2 += 1
                    for rr in range(r, r2 + 1):
                        for cc in range(c, c2 + 1):
                            seen.add((rr, cc))
                    rects.append((c * CELL, r * CELL, (c2 + 1) * CELL, (r2 + 1) * CELL))
        return rects

    # ── física ──
    def point_in_wall(self, x, y):
        if x < 0 or y < 0 or x >= AW or y >= AH:
            return True
        return (int(y // CELL), int(x // CELL)) in self.walls

    def hits_wall(self, x, y, r):
        for rr in range(int((y - r) // CELL), int((y + r) // CELL) + 1):
            for cc in range(int((x - r) // CELL), int((x + r) // CELL) + 1):
                if (rr, cc) in self.walls or rr < 0 or cc < 0 or rr >= ROWS or cc >= COLS:
                    nx = min(max(x, cc * CELL), cc * CELL + CELL)
                    ny = min(max(y, rr * CELL), rr * CELL + CELL)
                    if (x - nx) ** 2 + (y - ny) ** 2 < r * r:
                        return True
        return False

    def blocked(self, t, x, y):
        if self.hits_wall(x, y, TR):
            return True
        for o in self.tanks:
            if o is not t and o.alive:
                dn = math.hypot(x - o.x, y - o.y)
                if dn < 2 * TR and dn < math.hypot(t.x - o.x, t.y - o.y):
                    return True
        return False

    def control(self, t, dt, now):
        k, ks = t.keys, self.pressed
        if k["left"] in ks:
            t.ang -= TURN * dt
        if k["right"] in ks:
            t.ang += TURN * dt
        fwd = (k["up"] in ks) - (k["down"] in ks)
        if fwd:
            sp = SPEED * (1 if fwd > 0 else 0.65) * fwd * dt
            nx, ny = t.x + math.cos(t.ang) * sp, t.y + math.sin(t.ang) * sp
            if not self.blocked(t, nx, t.y):
                t.x = nx
            if not self.blocked(t, t.x, ny):
                t.y = ny
        if (k["shoot"] & ks) and now - t.last >= COOL:
            self.fire(t, now)

    def fire(self, t, now):
        if sum(1 for b in self.bullets if b["owner"] is t) >= MAX_B:
            return
        c, s = math.cos(t.ang), math.sin(t.ang)
        tip = (t.x + c * (TR + 13), t.y + s * (TR + 13))
        if self.point_in_wall(*tip):
            tip = (t.x + c * (TR - 4), t.y + s * (TR - 4))
            if self.point_in_wall(*tip):
                return
        self.bullets.append({"x": tip[0], "y": tip[1], "dx": c, "dy": s,
                             "owner": t, "born": now, "trail": []})
        t.last = now
        for _ in range(6):
            a = t.ang + random.uniform(-0.6, 0.6)
            sp = random.uniform(80, 240)
            self.particles.append([tip[0], tip[1], math.cos(a) * sp, math.sin(a) * sp,
                                   0.25, 0.25, t.color, 2.5])

    def update_bullets(self, now, dt):
        alive = []
        for b in self.bullets:
            if now - b["born"] > B_LIFE:
                continue
            dist = B_SPEED * dt
            n = int(dist // 4) + 1
            d = dist / n
            for _ in range(n):
                nx = b["x"] + b["dx"] * d
                if self.point_in_wall(nx, b["y"]):
                    b["dx"] = -b["dx"]
                    self.sparks(b["x"], b["y"], b["owner"].color)
                else:
                    b["x"] = nx
                ny = b["y"] + b["dy"] * d
                if self.point_in_wall(b["x"], ny):
                    b["dy"] = -b["dy"]
                    self.sparks(b["x"], b["y"], b["owner"].color)
                else:
                    b["y"] = ny
            b["trail"].append((b["x"], b["y"]))
            del b["trail"][:-7]
            hit = False
            for t in self.tanks:
                if t.alive and (t is not b["owner"] or now - b["born"] > 0.25):
                    if math.hypot(b["x"] - t.x, b["y"] - t.y) < TR + BR:
                        self.kill(t, now)
                        hit = True
                        break
            if not hit:
                alive.append(b)
        self.bullets = alive

    def sparks(self, x, y, color):
        for _ in range(3):
            a = random.uniform(0, math.tau)
            sp = random.uniform(40, 160)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp,
                                   0.3, 0.3, color, 2])

    def kill(self, t, now):
        t.alive = False
        for _ in range(80):
            a = random.uniform(0, math.tau)
            sp = random.uniform(50, 420)
            life = random.uniform(0.5, 1.2)
            self.particles.append([t.x, t.y, math.cos(a) * sp, math.sin(a) * sp, life, life,
                                   random.choice((t.color, t.color, WHITE, GOLD)),
                                   random.uniform(2, 5)])
        self.rings.append([t.x, t.y, now, t.color])
        if self.state == "playing":
            self.state = "ending"
            self.state_at = now

    def evaluate(self, now):
        alive = [t for t in self.tanks if t.alive]
        if len(alive) == 1:
            w = alive[0]
            w.score += 1
            self.msg = f"JUGADOR {w.idx} ANOTA"
            self.msg_color = w.color
            if w.score >= WIN:
                self.match_winner = w
                self.state = "matchover"
                self.state_at = now
                return
        else:
            self.msg = "EMPATE"
            self.msg_color = GOLD
        self.state = "result"
        self.state_at = now

    # ── bucle ──
    def tick(self):
        now = time.perf_counter()
        dt = min(0.04, now - self.last)
        self.last = now

        if self.state == "ready" and now - self.state_at >= READY_T:
            self.state = "playing"
            self.fight_at = now
        if self.state in ("playing", "ending"):
            for t in self.tanks:
                if t.alive:
                    self.control(t, dt, now)
        self.update_bullets(now, dt)
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            damp = max(0.0, 1 - 3.0 * dt)
            p[2] *= damp
            p[3] *= damp
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        self.rings = [r for r in self.rings if now - r[2] < 0.7]

        if self.state == "ending" and now - self.state_at >= 0.9:
            self.evaluate(now)
        elif self.state == "result" and now - self.state_at >= 1.9:
            self.new_round()

        self.draw(now)
        self.root.after(16, self.tick)

    # ── dibujo ──
    def glow_text(self, cv, x, y, text, size, color, anchor="center", glow=0.28):
        font = ("Helvetica", size, "bold")
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            cv.create_text(x + dx, y + dy, text=text, font=font, anchor=anchor,
                           fill=blend(color, BG, glow), tags="dyn")
        cv.create_text(x, y, text=text, font=font, anchor=anchor, fill=color, tags="dyn")

    def draw_tank(self, t):
        cv, col = self.cv, t.color
        c, s = math.cos(t.ang), math.sin(t.ang)

        def R(px, py):
            return (t.x + px * c - py * s, t.y + px * s + py * c)

        body = [v for p in (R(-16, -12), R(16, -12), R(16, 12), R(-16, 12)) for v in p]
        for w, f in ((11, 0.10), (6, 0.25)):
            cv.create_polygon(body, fill="", outline=blend(col, BG, f), width=w,
                              joinstyle=tk.ROUND, tags="dyn")
        cv.create_polygon(body, fill=blend(col, BG, 0.22), outline=col, width=2, tags="dyn")
        for side in (-1, 1):
            a, b = R(-16, side * 12), R(16, side * 12)
            cv.create_line(*a, *b, width=5, fill=blend(col, BG, 0.55), tags="dyn")
        tip = R(TR + 12, 0)
        cv.create_line(t.x, t.y, *tip, width=10, fill=blend(col, BG, 0.22),
                       capstyle=tk.ROUND, tags="dyn")
        cv.create_line(t.x, t.y, *tip, width=5, fill=col, capstyle=tk.ROUND, tags="dyn")
        cv.create_oval(t.x - 9, t.y - 9, t.x + 9, t.y + 9, fill=blend(col, BG, 0.55),
                       outline=blend(WHITE, col, 0.6), width=2, tags="dyn")

    def draw(self, now):
        cv = self.cv
        cv.delete("dyn")

        # anillos de explosión
        for x, y, t0, col in self.rings:
            k = (now - t0) / 0.7
            r = 10 + k * 170
            cv.create_oval(x - r, y - r, x + r, y + r, outline=blend(col, BG, 1 - k),
                           width=max(1, int(6 * (1 - k))), tags="dyn")

        # balas
        for b in self.bullets:
            col = b["owner"].color
            n = len(b["trail"])
            for i, (tx, ty) in enumerate(b["trail"]):
                f = (i + 1) / (n + 1)
                r = BR * f
                cv.create_oval(tx - r, ty - r, tx + r, ty + r,
                               fill=blend(col, BG, 0.5 * f), outline="", tags="dyn")
            x, y = b["x"], b["y"]
            for r, f in ((BR + 6, 0.12), (BR + 3, 0.30)):
                cv.create_oval(x - r, y - r, x + r, y + r, fill=blend(col, BG, f),
                               outline="", tags="dyn")
            cv.create_oval(x - BR, y - BR, x + BR, y + BR, fill=blend(WHITE, col, 0.7),
                           outline=col, tags="dyn")

        # tanques
        for t in self.tanks:
            if t.alive:
                self.draw_tank(t)

        # partículas
        for x, y, _, _, life, maxlife, col, size in self.particles:
            f = max(0.0, life / maxlife)
            cv.create_rectangle(x, y, x + size, y + size, outline="",
                                fill=blend(col, BG, f), tags="dyn")

        # mensajes
        if self.state == "ready":
            rem = READY_T - (now - self.state_at)
            n = 3 if rem > 1.6 else 2 if rem > 0.8 else 1
            frac = (rem % 0.8) / 0.8
            self.glow_text(cv, AW / 2, AH / 2, str(n), 70 + int(26 * frac), GOLD)
        elif self.state == "playing" and now - self.fight_at < 0.7:
            self.glow_text(cv, AW / 2, AH / 2, "¡FUEGO!", 46, GOLD)
        elif self.state == "result":
            self.glow_text(cv, AW / 2, AH / 2, self.msg, 34, self.msg_color)
        elif self.state == "matchover" and now - self.state_at > 0.6:
            w = self.match_winner
            self.rrect(cv, AW / 2 - 290, AH / 2 - 95, AW / 2 + 290, AH / 2 + 95, 22,
                       fill=PANEL, outline=w.color, width=3)
            self.glow_text(cv, AW / 2, AH / 2 - 35, f"¡JUGADOR {w.idx} GANA LA PARTIDA!",
                           24, w.color)
            a = 0.5 + 0.5 * math.sin(now * 4)
            cv.create_text(AW / 2, AH / 2 + 35, text="Pulsa ENTER, ESPACIO o haz clic para jugar otra vez",
                           font=("Helvetica", 11), fill=blend(WHITE, BG, 0.4 + 0.45 * a),
                           tags="dyn")
            cv.create_text(AW / 2, AH / 2 + 62, text="Esc para salir", font=("Helvetica", 9),
                           fill=blend(WHITE, BG, 0.4), tags="dyn")
        if self.state == "ready" and self.match_is_fresh():
            cv.create_text(AW / 2, AH - 24,
                           text="J1: W A S D + F          J2: flechas + ENTER          las balas rebotan",
                           font=("Helvetica", 10, "bold"), fill=blend(WHITE, BG, 0.5), tags="dyn")

        self.draw_hud()

    def match_is_fresh(self):
        return all(t.score == 0 for t in self.tanks)

    def rrect(self, cv, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return cv.create_polygon(pts, smooth=True, tags="dyn", **kw)

    def draw_hud(self):
        h = self.hud
        h.delete("all")
        self.glow_text(h, AW / 2 + 4, 26, "TANQ", 24, C1, anchor="e")
        self.glow_text(h, AW / 2 + 8, 26, "UES", 24, C2, anchor="w")
        h.create_line(0, HUD_H - 1, AW, HUD_H - 1, fill=blend(WALL, BG, 0.4))
        for t in self.tanks:
            left = t.idx == 1
            x = 30 if left else AW - 30
            self.glow_text(h, x, 22, f"JUGADOR {t.idx}", 14, t.color,
                           anchor="w" if left else "e")
            for i in range(WIN):
                cx = (x + 8 + i * 28) if left else (x - 8 - i * 28)
                filled = i < t.score
                h.create_oval(cx - 9, 54 - 9, cx + 9, 54 + 9,
                              fill=t.color if filled else BG,
                              outline=t.color if filled else blend(t.color, BG, 0.35), width=2)


def main():
    root = tk.Tk()
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
