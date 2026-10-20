"""Uma estrelinha percorre o contorno do coração soltando fogo e faíscas,
deixando um rastro de brasas. Quando o contorno fecha, o fogo sobe da
ponta e o coração inteiro queima.

python coracao_fogo.py             # anima
python coracao_fogo.py --gravar    # grava coracao_fogo.mp4 (captura a janela)
"""
import math, random, sys, time, subprocess
import tkinter as tk

W, H = 800, 800
BG = (0, 0, 0)
VOLTA = 6.0          # segundos para percorrer o contorno
INCENDIO = 1.6       # segundos para o fogo subir da ponta ao topo
QUEIMA = 5.0         # segundos com o coração inteiro em chamas
ESCALA = 19
SEMENTE = 7

AMARELO, BRASA = (255, 244, 170), (255, 90, 30)
RAMPA = [(255, 255, 230), (255, 225, 110), (255, 140, 30), (225, 60, 15), (120, 20, 8)]


def cor_fogo(age):
    """Rampa contínua do branco ao vermelho escuro ao longo da vida."""
    pos = min(age, 0.999) * (len(RAMPA) - 1)
    i, f = int(pos), pos - int(pos)
    a, b = RAMPA[i], RAMPA[i + 1]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def blend(rgb, a):
    a = max(0.0, min(1.0, a))
    return "#%02x%02x%02x" % tuple(int(BG[i] + (rgb[i] - BG[i]) * a) for i in range(3))


def coracao(t):
    """t=0 no vinco de cima; cresce pela direita, ponta em t=π, volta pela esquerda."""
    x = 16 * math.sin(t) ** 3
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
    return W / 2 + x * ESCALA, H / 2 - y * ESCALA - 10


def dentro(px, py):
    x = (px - W / 2) / (ESCALA * 13.5)
    y = (H / 2 - 10 - py) / (ESCALA * 13.5) + 0.25
    return (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0


TOPO, FUNDO = coracao(0.75 * math.pi + math.pi / 2)[1], coracao(math.pi)[1]
TOPO = min(coracao(t)[1] for t in [i / 200 * math.tau for i in range(200)])


class App:
    def __init__(self, gravar=False):
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        random.seed(SEMENTE)
        self.root = tk.Tk()
        self.root.title("coração de fogo")
        self.root.geometry("+40+40")
        self.cv = tk.Canvas(self.root, width=W, height=H, bg=blend(BG, 1), highlightthickness=0)
        self.cv.pack()
        self.parts, self.brasas = [], []
        self.miolo = []                      # pontos internos que viram focos de fogo
        while len(self.miolo) < 700:
            px, py = random.uniform(100, W - 100), random.uniform(TOPO, FUNDO)
            if dentro(px, py):
                self.miolo.append((px, py))
        self.t0 = time.perf_counter()
        self.last = self.t0
        self.sim = 0.0
        self.ff = None
        if gravar:
            self.root.attributes("-topmost", True)
            self.root.protocol("WM_DELETE_WINDOW", lambda: None)
            self.root.update()
            self.ff = subprocess.Popen(
                ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                 "-r", "30", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                 "coracao_fogo.mp4"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.root.after(0, self.frame)
        self.root.mainloop()

    # ---------- partículas ----------
    def add(self, kind, x, y, vx, vy, size, life):
        if kind == "spark":
            item = self.cv.create_line(x, y, x, y, fill="#ffbc3e", width=2, capstyle="round")
        elif kind == "fire":
            casca = self.cv.create_polygon(0, 0, 0, 0, 0, 0, outline="", smooth=True)
            nucleo = self.cv.create_polygon(0, 0, 0, 0, 0, 0, outline="", smooth=True)
            item = (casca, nucleo)
        else:
            item = self.cv.create_oval(x, y, x, y, outline="")
        self.parts.append([item, kind, x, y, vx, vy, size, life, life, random.random() * math.tau])

    def lingua(self, x, y, w, h, ph, tempo):
        """Contorno de uma língua de fogo: base larga, ponta fina que oscila."""
        o = math.sin(tempo * 14 + ph) * w * 0.6
        o2 = math.sin(tempo * 9 + ph * 1.7) * w * 0.35
        return [x - w, y, x - w * 0.9, y - h * 0.35 + o2, x - w * 0.45 + o * 0.5, y - h * 0.7,
                x + o, y - h, x + w * 0.45 + o * 0.5, y - h * 0.7, x + w * 0.9, y - h * 0.35 - o2,
                x + w, y]

    def chama(self, x, y, forca=1.0):
        """Uma língua de fogo nascendo em (x, y). forca escala tamanho e subida."""
        self.add("fire", random.gauss(x, 3), y + random.uniform(-2, 4),
                 random.uniform(-12, 12), random.uniform(-150, -80) * forca,
                 random.uniform(8, 15) * forca, random.uniform(0.55, 1.1) * forca)

    def faisca(self, x, y, v=(60, 220)):
        a = random.uniform(0, math.tau)
        s = random.uniform(*v)
        self.add("spark", x, y, math.cos(a) * s, math.sin(a) * s, 2, random.uniform(0.4, 1.0))

    def brasa(self, x, y, r):
        self.brasas.append(self.cv.create_oval(x - r, y - r, x + r, y + r, outline="",
                                               fill=blend(BRASA, 1)))

    # ---------- fases ----------
    def estrelinha(self, prog, dt):
        # rastro contínuo: várias brasas por quadro, espalhadas entre o passo anterior e o atual
        passo = dt / VOLTA
        for k in range(6):
            t = (prog - passo * k / 6) * math.tau
            x, y = coracao(t)
            self.brasa(x + random.uniform(-1.5, 1.5), y + random.uniform(-1.5, 1.5),
                       random.uniform(2.2, 3.6))
        # cabeça: núcleo branco + fogo + faíscas
        x, y = coracao(prog * math.tau)
        for _ in range(3):
            self.chama(x, y, forca=0.9)
        self.add("core", x, y, 0, 0, 7, 0.12)
        for _ in range(3):
            self.faisca(x, y)

    def incendio(self, prog):
        """O fogo sobe da ponta (FUNDO) ao topo (TOPO). prog em 0..1."""
        frente = FUNDO - (FUNDO - TOPO) * prog
        for i, b in enumerate(self.brasas):
            x1, y1, x2, y2 = self.cv.coords(b)
            if (y1 + y2) / 2 >= frente - 12 and random.random() < 0.18:
                self.chama((x1 + x2) / 2, (y1 + y2) / 2)
        for (px, py) in self.miolo:
            if py >= frente and random.random() < 0.12:
                self.chama(px, py, forca=random.uniform(0.8, 1.3))
        if random.random() < 0.8:
            x, y = random.choice(self.miolo)
            if y >= frente:
                self.faisca(x, y, (40, 160))

    def queima(self, tempo):
        """Coração inteiro em chamas, com faíscas subindo."""
        for b in self.brasas:
            if random.random() < 0.12:
                x1, y1, x2, y2 = self.cv.coords(b)
                self.chama((x1 + x2) / 2, (y1 + y2) / 2, forca=random.uniform(0.8, 1.2))
        for (px, py) in self.miolo:
            if random.random() < 0.09:
                self.chama(px, py, forca=random.uniform(0.9, 1.4))
        for _ in range(2):
            x, y = random.choice(self.miolo)
            self.add("spark", x, y, random.uniform(-25, 25), random.uniform(-160, -90),
                     1.5, random.uniform(0.8, 1.6))
        for i, b in enumerate(self.brasas):   # brasas cintilam
            self.cv.itemconfigure(b, fill=blend(AMARELO if random.random() < 0.08 else BRASA,
                                                0.7 + 0.3 * math.sin(tempo * 6 + i * 0.3)))

    # ---------- laço ----------
    def frame(self):
        if self.ff:                      # gravando: relógio simulado, 30 quadros por segundo
            dt = 1 / 30
            self.sim += dt
            tempo = self.sim
        else:
            now = time.perf_counter()
            dt = min(0.033, now - self.last)
            self.last = now
            tempo = now - self.t0

        if tempo <= VOLTA:
            self.estrelinha(tempo / VOLTA, dt)
        elif tempo <= VOLTA + INCENDIO:
            self.incendio((tempo - VOLTA) / INCENDIO)
        elif tempo <= VOLTA + INCENDIO + QUEIMA:
            self.queima(tempo)

        vivos = []
        for p in self.parts:
            item, kind, x, y, vx, vy, size, life, maxlife, ph = p
            life -= dt
            age = 1 - life / maxlife
            if kind == "fire":
                vx += math.sin(ph + age * 11) * 35 * dt
                vy -= 16 * dt
                x += vx * dt; y += vy * dt
                size *= 1 - 0.75 * dt
                alpha = 1.0 if age < 0.65 else (1 - age) / 0.35
                casca, nucleo = item
                w, h = size, size * 3.4
                self.cv.coords(casca, *self.lingua(x, y, w, h, ph, tempo))
                self.cv.itemconfigure(casca, fill=blend(cor_fogo(min(1, age + 0.25)), alpha))
                if age < 0.55:
                    enc = 1 - age / 0.55                      # o núcleo encolhe, não desbota
                    self.cv.coords(nucleo, *self.lingua(x, y + 1, w * 0.5 * enc, h * 0.55 * enc, ph + 1, tempo))
                    self.cv.itemconfigure(nucleo, fill=blend(cor_fogo(0.15 + age * 0.4), 1))
                else:
                    self.cv.coords(nucleo, 0, 0, 0, 0, 0, 0)
            elif kind == "core":
                self.cv.itemconfigure(item, fill=blend((255, 255, 240), 1 - age))
                self.cv.coords(item, x - size, y - size, x + size, y + size)
            else:
                vy += 300 * dt; vx *= 0.995
                ox, oy = x, y
                x += vx * dt; y += vy * dt
                self.cv.itemconfigure(item, fill=blend((255, 188, 62), max(0, life / maxlife)))
                self.cv.coords(item, x, y, ox, oy)
            if life > 0:
                vivos.append([item, kind, x, y, vx, vy, size, life, maxlife, ph])
            elif kind == "fire":
                self.cv.delete(item[0]); self.cv.delete(item[1])
            else:
                self.cv.delete(item)
        self.parts = vivos

        if self.ff:
            from PIL import ImageGrab
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.update()
            x0, y0 = self.cv.winfo_rootx(), self.cv.winfo_rooty()
            self.ff.stdin.write(ImageGrab.grab((x0, y0, x0 + W, y0 + H)).convert("RGB").tobytes())
            if tempo > VOLTA + INCENDIO + QUEIMA + 1.5:
                self.ff.stdin.close(); self.ff.wait(); self.root.destroy(); return
        self.root.after(16, self.frame)


if __name__ == "__main__":
    App(gravar="--gravar" in sys.argv)
