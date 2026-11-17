"""
TRIQUI NEON  -  Tic Tac Toe: Tú vs Máquina
Juego de escritorio hecho con Python + Tkinter (sin dependencias externas).

Controles:
    Clic ........ jugar / elegir dificultad / nueva partida
    R ........... nueva partida
    Esc ......... salir
"""
import math
import random
import time
import tkinter as tk

# ───────────────────────── Configuración visual ─────────────────────────
W, H = 500, 700
CELL = 150
OX, OY = 25, 172            # esquina superior izquierda del tablero

BG = "#0a0d1c"
PANEL = "#0f1328"
PANEL_BORDER = "#252b55"
GRID = "#5b6cff"
XCOL = "#00e5ff"
OCOL = "#ff2e93"
GOLD = "#ffd23f"
WHITE = "#ffffff"

WIN_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
             (0, 3, 6), (1, 4, 7), (2, 5, 8),
             (0, 4, 8), (2, 4, 6)]


# ───────────────────────── Utilidades de color ─────────────────────────
def _rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def blend(c1, c2, t):
    """Mezcla c1 con c2. t=1 -> c1, t=0 -> c2."""
    a, b = _rgb(c1), _rgb(c2)
    return "#%02x%02x%02x" % tuple(int(b[i] + (a[i] - b[i]) * t) for i in range(3))


# ───────────────────────── Lógica del juego / IA ─────────────────────────
def winner(board):
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], (a, b, c)
    return None, None


def minimax(board, turn, ai, alpha, beta, depth):
    w, _ = winner(board)
    if w == ai:
        return 10 - depth
    if w:
        return depth - 10
    if all(board):
        return 0
    other = "X" if turn == "O" else "O"
    if turn == ai:
        best = -99
        for i in range(9):
            if not board[i]:
                board[i] = turn
                best = max(best, minimax(board, other, ai, alpha, beta, depth + 1))
                board[i] = ""
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        return best
    best = 99
    for i in range(9):
        if not board[i]:
            board[i] = turn
            best = min(best, minimax(board, other, ai, alpha, beta, depth + 1))
            board[i] = ""
            beta = min(beta, best)
            if beta <= alpha:
                break
    return best


def best_move(board, ai):
    other = "X" if ai == "O" else "O"
    scores = {}
    for i in range(9):
        if not board[i]:
            board[i] = ai
            scores[i] = minimax(board, other, ai, -99, 99, 1)
            board[i] = ""
    top = max(scores.values())
    return random.choice([i for i, s in scores.items() if s == top])


def win_or_block(board, ai):
    human = "X" if ai == "O" else "O"
    for who in (ai, human):
        for i in range(9):
            if not board[i]:
                board[i] = who
                w, _ = winner(board)
                board[i] = ""
                if w:
                    return i
    return None


def choose_move(board, ai, level):
    empty = [i for i in range(9) if not board[i]]
    if level == "easy":
        return random.choice(empty)
    if level == "medium":
        m = win_or_block(board, ai)
        if m is not None:
            return m
        if not board[4]:
            return 4
        return random.choice(empty)
    return best_move(board, ai)          # "hard": imposible de vencer


# ───────────────────────── Aplicación ─────────────────────────
class Triqui:
    def __init__(self, root):
        self.root = root
        root.title("TRIQUI NEON  ·  Tú vs Máquina")
        root.configure(bg=BG)
        root.resizable(False, False)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw - W) // 2}+{max(0, (sh - H) // 2 - 20)}")

        self.cv = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Leave>", lambda e: setattr(self, "hover", None))
        root.bind("<r>", lambda e: self.new_round())
        root.bind("<R>", lambda e: self.new_round())
        root.bind("<Escape>", lambda e: root.destroy())

        self.level = "hard"
        self.score = {"X": 0, "O": 0, "draw": 0}
        self.starter = "X"
        self.hover = None
        self.particles = []
        self.stars = [{"x": random.uniform(0, W), "y": random.uniform(0, H),
                       "r": random.choice((1, 1, 1.5, 2)),
                       "v": random.uniform(4, 16),
                       "ph": random.uniform(0, 6.28),
                       "sp": random.uniform(1, 3)} for _ in range(70)]

        # botones de dificultad
        labels = [("Fácil", "easy"), ("Medio", "medium"), ("Imposible", "hard")]
        bw, gap = 104, 12
        x0 = (W - (3 * bw + 2 * gap)) / 2
        self.btns = []
        for k, (txt, key) in enumerate(labels):
            x1 = x0 + k * (bw + gap)
            self.btns.append((txt, key, x1, 130, x1 + bw, 158))

        self.new_round()
        self.last = time.perf_counter()
        # traer la ventana al frente (útil al lanzar desde VS Code)
        root.lift()
        root.attributes("-topmost", True)
        root.after(500, lambda: root.attributes("-topmost", False))
        self.tick()

    # ── estado ──
    def new_round(self):
        now = time.perf_counter()
        self.board = [""] * 9
        self.times = [0.0] * 9
        self.state = "playing"
        self.result = None
        self.win_line = None
        self.over_at = 0
        self.burst_pending = False
        self.turn = self.starter
        self.starter = "O" if self.starter == "X" else "X"
        self.ai_at = now + 0.8 if self.turn == "O" else 0

    def set_level(self, key):
        self.level = key
        self.score = {"X": 0, "O": 0, "draw": 0}
        self.starter = "X"
        self.new_round()

    def place(self, i, sym):
        now = time.perf_counter()
        self.board[i] = sym
        self.times[i] = now
        w, line = winner(self.board)
        if w:
            self.finish(w, line)
        elif all(self.board):
            self.finish("draw", None)
        else:
            self.turn = "O" if sym == "X" else "X"
            if self.turn == "O":
                self.ai_at = now + random.uniform(0.55, 0.95)

    def finish(self, result, line):
        self.state = "over"
        self.result = result
        self.win_line = line
        self.over_at = time.perf_counter()
        self.score[result] += 1
        self.burst_pending = result in ("X", "O")

    # ── entrada ──
    def cell_at(self, x, y):
        if OX <= x < OX + 3 * CELL and OY <= y < OY + 3 * CELL:
            return int((y - OY) // CELL) * 3 + int((x - OX) // CELL)
        return None

    def over_button(self, x, y):
        for _, key, x1, y1, x2, y2 in self.btns:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key
        return None

    def on_motion(self, e):
        self.hover = self.cell_at(e.x, e.y)
        clickable = (self.over_button(e.x, e.y) is not None
                     or self.state == "over"
                     or (self.state == "playing" and self.turn == "X"
                         and self.hover is not None and not self.board[self.hover]))
        self.cv.config(cursor="hand2" if clickable else "")

    def on_click(self, e):
        key = self.over_button(e.x, e.y)
        if key:
            self.set_level(key)
            return
        if self.state == "over":
            if time.perf_counter() - self.over_at > 0.7:
                self.new_round()
            return
        if self.state == "playing" and self.turn == "X":
            i = self.cell_at(e.x, e.y)
            if i is not None and not self.board[i]:
                self.place(i, "X")

    # ── bucle ──
    def tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last)
        self.last = now

        if self.state == "playing" and self.turn == "O" and now >= self.ai_at:
            self.place(choose_move(self.board, "O", self.level), "O")
        if self.burst_pending and now >= self.over_at + 0.6:
            self.burst_pending = False
            self.burst(self.result)

        for s in self.stars:
            s["y"] -= s["v"] * dt
            if s["y"] < -5:
                s["y"], s["x"] = H + 5, random.uniform(0, W)
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 650 * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

        self.draw(now)
        self.root.after(16, self.tick)

    def burst(self, who):
        cols = ([XCOL, GOLD, WHITE, "#7dffb3", "#5b6cff"] if who == "X"
                else [OCOL, "#ff6b6b", GOLD, "#b517ff"])
        n = 150 if who == "X" else 70
        for _ in range(n):
            a = random.uniform(math.pi * 1.1, math.pi * 1.9)
            sp = random.uniform(180, 620)
            life = random.uniform(1.0, 1.9)
            self.particles.append([W / 2, 360, math.cos(a) * sp, math.sin(a) * sp,
                                   life, life, random.choice(cols), random.uniform(3, 7)])

    # ── dibujo ──
    def rrect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.cv.create_polygon(pts, smooth=True, **kw)

    def glow_line(self, x1, y1, x2, y2, color, width=8):
        for extra, f in ((18, 0.10), (11, 0.20), (5, 0.42)):
            self.cv.create_line(x1, y1, x2, y2, width=width + extra,
                                fill=blend(color, BG, f), capstyle=tk.ROUND)
        self.cv.create_line(x1, y1, x2, y2, width=width, fill=color, capstyle=tk.ROUND)
        self.cv.create_line(x1, y1, x2, y2, width=max(2, width // 3),
                            fill=blend(WHITE, color, 0.55), capstyle=tk.ROUND)

    def glow_arc(self, cx, cy, r, extent, color, width=8):
        box = (cx - r, cy - r, cx + r, cy + r)
        ext = -min(359.9, extent)
        for extra, f in ((18, 0.10), (11, 0.20), (5, 0.42)):
            self.cv.create_arc(*box, start=90, extent=ext, style=tk.ARC,
                               width=width + extra, outline=blend(color, BG, f))
        self.cv.create_arc(*box, start=90, extent=ext, style=tk.ARC,
                           width=width, outline=color)
        self.cv.create_arc(*box, start=90, extent=ext, style=tk.ARC,
                           width=max(2, width // 3), outline=blend(WHITE, color, 0.55))

    def glow_text(self, x, y, text, size, color, anchor="center", glow=0.28):
        font = ("Helvetica", size, "bold")
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            self.cv.create_text(x + dx, y + dy, text=text, font=font, anchor=anchor,
                                fill=blend(color, BG, glow))
        self.cv.create_text(x, y, text=text, font=font, anchor=anchor, fill=color)

    def draw(self, now):
        cv = self.cv
        cv.delete("all")

        # estrellas
        for s in self.stars:
            tw = 0.5 + 0.5 * math.sin(now * s["sp"] + s["ph"])
            col = blend("#9fb4ff", BG, 0.12 + 0.45 * tw)
            r = s["r"]
            cv.create_oval(s["x"] - r, s["y"] - r, s["x"] + r, s["y"] + r, fill=col, outline="")

        # título
        self.glow_text(W / 2 + 4, 38, "TRI", 32, XCOL, anchor="e")
        self.glow_text(W / 2 + 8, 38, "QUI", 32, OCOL, anchor="w")

        # marcador
        boxes = [("TÚ  (X)", self.score["X"], XCOL),
                 ("EMPATES", self.score["draw"], GOLD),
                 ("MÁQUINA  (O)", self.score["O"], OCOL)]
        for k, (label, val, col) in enumerate(boxes):
            x1 = 25 + k * 155
            active = self.state == "playing" and ((k == 0 and self.turn == "X") or
                                                  (k == 2 and self.turn == "O"))
            pulse = 0.6 + 0.4 * math.sin(now * 6) if active else 0
            if active:
                self.rrect(x1 - 3, 65, x1 + 143, 123, 14, fill=blend(col, BG, 0.10 + 0.15 * pulse))
            self.rrect(x1, 68, x1 + 140, 120, 12, fill=PANEL,
                       outline=col if active else PANEL_BORDER, width=2)
            cv.create_text(x1 + 70, 82, text=label, font=("Helvetica", 9, "bold"),
                           fill=blend(col, BG, 0.85))
            cv.create_text(x1 + 70, 104, text=str(val), font=("Helvetica", 20, "bold"), fill=col)

        # dificultad
        for txt, key, x1, y1, x2, y2 in self.btns:
            sel = key == self.level
            col = {"easy": "#7dffb3", "medium": GOLD, "hard": OCOL}[key]
            self.rrect(x1, y1, x2, y2, 14,
                       fill=blend(col, BG, 0.28) if sel else PANEL,
                       outline=col if sel else PANEL_BORDER, width=2)
            cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=txt,
                           font=("Helvetica", 10, "bold"),
                           fill=col if sel else blend(WHITE, BG, 0.55))

        # casilla resaltada
        if (self.state == "playing" and self.turn == "X" and self.hover is not None
                and not self.board[self.hover]):
            r, c = divmod(self.hover, 3)
            x1, y1 = OX + c * CELL + 8, OY + r * CELL + 8
            self.rrect(x1, y1, x1 + CELL - 16, y1 + CELL - 16, 16, fill="#141a3a")
            cx, cy = x1 + (CELL - 16) / 2, y1 + (CELL - 16) / 2
            m = 26
            ghost = blend(XCOL, "#141a3a", 0.22)
            cv.create_line(cx - m, cy - m, cx + m, cy + m, width=6, fill=ghost, capstyle=tk.ROUND)
            cv.create_line(cx + m, cy - m, cx - m, cy + m, width=6, fill=ghost, capstyle=tk.ROUND)

        # cuadrícula
        for k in (1, 2):
            self.glow_line(OX + k * CELL, OY + 12, OX + k * CELL, OY + 3 * CELL - 12, GRID, 4)
            self.glow_line(OX + 12, OY + k * CELL, OX + 3 * CELL - 12, OY + k * CELL, GRID, 4)

        # fichas
        for i, sym in enumerate(self.board):
            if not sym:
                continue
            p = min(1.0, (now - self.times[i]) / 0.40)
            p = 1 - (1 - p) ** 3
            cx = OX + (i % 3) * CELL + CELL / 2
            cy = OY + (i // 3) * CELL + CELL / 2
            base = XCOL if sym == "X" else OCOL
            if self.state == "over" and self.win_line and i not in self.win_line:
                base = blend(base, BG, 0.30)
            if sym == "X":
                m = 38
                p1, p2 = min(1, p * 2), max(0, p * 2 - 1)
                self.glow_line(cx - m, cy - m, cx - m + 2 * m * p1, cy - m + 2 * m * p1, base, 9)
                if p2 > 0:
                    self.glow_line(cx + m, cy - m, cx + m - 2 * m * p2, cy - m + 2 * m * p2, base, 9)
            else:
                self.glow_arc(cx, cy, 38, 360 * p, base, 9)

        # línea ganadora
        if self.state == "over" and self.win_line:
            t = max(0.0, min(1.0, (now - self.over_at - 0.25) / 0.5))
            t = 1 - (1 - t) ** 3
            a, c = self.win_line[0], self.win_line[2]
            x1 = OX + (a % 3) * CELL + CELL / 2
            y1 = OY + (a // 3) * CELL + CELL / 2
            x2 = OX + (c % 3) * CELL + CELL / 2
            y2 = OY + (c // 3) * CELL + CELL / 2
            d = math.hypot(x2 - x1, y2 - y1) or 1
            ux, uy = (x2 - x1) / d, (y2 - y1) / d
            x1, y1, x2, y2 = x1 - ux * 28, y1 - uy * 28, x2 + ux * 28, y2 + uy * 28
            if t > 0:
                self.glow_line(x1, y1, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t,
                               GOLD, 8 + 2 * math.sin(now * 9))

        # partículas
        for x, y, _, _, life, maxlife, col, size in self.particles:
            f = max(0, life / maxlife)
            cv.create_rectangle(x, y, x + size, y + size * 0.7, outline="",
                                fill=blend(col, BG, min(1, f * 1.4)))

        # estado / resultado
        if self.state == "playing":
            if self.turn == "X":
                self.glow_text(W / 2, 655, "TU TURNO", 15, XCOL, glow=0.2)
            else:
                dots = "." * (1 + int(now * 3) % 3)
                self.glow_text(W / 2, 655, "LA MÁQUINA PIENSA" + dots, 15, OCOL, glow=0.2)
        else:
            msg, col = {"X": ("¡GANASTE!", XCOL),
                        "O": ("LA MÁQUINA GANA", OCOL),
                        "draw": ("¡EMPATE!", GOLD)}[self.result]
            if now - self.over_at > 0.4:
                self.glow_text(W / 2, 650, msg, 22, col)
                a = 0.5 + 0.5 * math.sin(now * 4)
                cv.create_text(W / 2, 682, text="Haz clic para jugar otra vez  ·  R",
                               font=("Helvetica", 9), fill=blend(WHITE, BG, 0.35 + 0.35 * a))


def main():
    root = tk.Tk()
    Triqui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
