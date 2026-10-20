import tkinter as tk
import random
import math
import time
from dataclasses import dataclass

W, H = 960, 600
BG = (7, 11, 22)


def blend(rgb, alpha):
    alpha = max(0.0, min(1.0, alpha))
    return '#%02x%02x%02x' % tuple(
        int(BG[i] + (rgb[i] - BG[i]) * alpha) for i in range(3)
    )


@dataclass(slots=True)
class Particle:
    item: int
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    size: float
    life: float
    max_life: float
    phase: float = 0.0


class FXApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Tkinter FX — 1 Partículas | 2 Fogo | 3 Chuva | 4 Neve')
        self.root.geometry(f'{W}x{H}')
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            self.root, width=W, height=H, bg=blend(BG, 1),
            highlightthickness=0
        )
        self.canvas.pack()
        self.particles = []
        self.mode = 'fire'
        self.wind = 20.0
        self.mouse_x, self.mouse_y = W / 2, H * 0.82
        self.last = time.perf_counter()
        self.title = self.canvas.create_text(
            16, 16, anchor='nw', fill='#dbeafe',
            font=('TkDefaultFont', 13, 'bold'), text=''
        )
        self.help = self.canvas.create_text(
            16, H - 16, anchor='sw', fill='#64748b',
            font=('TkDefaultFont', 10),
            text='1 partículas  •  2 fogo  •  3 chuva  •  4 neve  •  mover mouse altera a origem'
        )
        self.root.bind('<Key>', self.on_key)
        self.canvas.bind('<Motion>', self.on_mouse)
        self.set_mode('fire')
        self.root.after(0, self.frame)

    def on_key(self, event):
        modes = {'1': 'sparks', '2': 'fire', '3': 'rain', '4': 'snow'}
        if event.char in modes:
            self.set_mode(modes[event.char])

    def on_mouse(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y

    def set_mode(self, mode):
        self.mode = mode
        for p in self.particles:
            self.canvas.delete(p.item)
        self.particles.clear()
        names = {'sparks': 'PARTÍCULAS', 'fire': 'FOGO', 'rain': 'CHUVA', 'snow': 'NEVE'}
        self.canvas.itemconfigure(self.title, text=names[mode])
        if mode in ('rain', 'snow'):
            target = 260 if mode == 'rain' else 190
            for _ in range(target):
                self.spawn(initial=True)

    def add(self, kind, x, y, vx, vy, size, life, phase=0.0):
        if kind in ('rain', 'spark'):
            item = self.canvas.create_line(
                0, 0, 0, 0, fill='#8cc8ff',
                width=max(1, int(size)), capstyle='round'
            )
        else:
            item = self.canvas.create_oval(0, 0, 0, 0, outline='')
        self.particles.append(
            Particle(item, kind, x, y, vx, vy, size, life, life, phase)
        )

    def spawn(self, initial=False):
        if self.mode == 'fire':
            x = random.gauss(self.mouse_x, 26)
            y = self.mouse_y + random.uniform(-4, 8)
            self.add(
                'fire', x, y,
                random.uniform(-18, 18), random.uniform(-145, -75),
                random.uniform(5, 13), random.uniform(0.55, 1.05),
                random.random() * math.tau
            )
        elif self.mode == 'sparks':
            angle = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            speed = random.uniform(90, 310)
            self.add(
                'spark', self.mouse_x, self.mouse_y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(1.5, 4.5), random.uniform(0.65, 1.4)
            )
        elif self.mode == 'rain':
            y = random.uniform(-H, H) if initial else random.uniform(-100, -10)
            speed = random.uniform(520, 900)
            self.add(
                'rain', random.uniform(-100, W), y,
                random.uniform(80, 150), speed,
                random.uniform(1, 2.3), (H - y + 160) / speed
            )
        elif self.mode == 'snow':
            y = random.uniform(-H, H) if initial else random.uniform(-40, -5)
            speed = random.uniform(28, 82)
            self.add(
                'snow', random.uniform(0, W), y,
                random.uniform(-8, 8), speed,
                random.uniform(1.8, 5.2), (H - y + 80) / speed,
                random.random() * math.tau
            )

    def emit(self, dt):
        rates = {'fire': 150, 'sparks': 75, 'rain': 0, 'snow': 0}
        count = int(rates[self.mode] * dt + random.random())
        for _ in range(count):
            self.spawn()

    def update_particle(self, p, dt):
        p.life -= dt
        age = 1.0 - p.life / p.max_life

        if p.kind == 'fire':
            p.vx += math.sin(p.phase + age * 11) * 35 * dt
            p.vy -= 16 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.size *= 1.0 - 0.75 * dt
            if age < 0.28:
                color = (255, 244, 170)
            elif age < 0.62:
                color = (255, 112, 24)
            else:
                color = (100, 24, 12)
            alpha = min(1.0, age * 7) * max(0.0, 1.0 - age)
            self.canvas.itemconfigure(p.item, fill=blend(color, alpha))
            r = p.size
            self.canvas.coords(
                p.item, p.x-r, p.y-r*1.35, p.x+r, p.y+r*1.35
            )

        elif p.kind == 'spark':
            p.vy += 300 * dt
            p.vx *= 0.995
            old_x, old_y = p.x, p.y
            p.x += p.vx * dt
            p.y += p.vy * dt
            alpha = max(0.0, p.life / p.max_life)
            self.canvas.itemconfigure(
                p.item, fill=blend((255, 188, 62), alpha),
                width=max(1, int(p.size * alpha))
            )
            self.canvas.coords(p.item, p.x, p.y, old_x, old_y)

        elif p.kind == 'rain':
            p.x += (p.vx + self.wind) * dt
            p.y += p.vy * dt
            length = 12 + p.vy * 0.025
            self.canvas.coords(
                p.item, p.x, p.y,
                p.x-(p.vx+self.wind)*0.025, p.y-length
            )
            depth = min(1.0, p.vy / 900)
            self.canvas.itemconfigure(
                p.item,
                fill=blend((130, 204, 255), 0.35 + depth * 0.55)
            )
            if p.y > H + 40:
                p.life = 0

        elif p.kind == 'snow':
            p.phase += dt * (1.3 + p.size * 0.15)
            p.x += (
                p.vx + math.sin(p.phase) * (12 + p.size * 3)
            ) * dt
            p.y += p.vy * dt
            alpha = 0.45 + min(0.5, p.size / 10)
            self.canvas.itemconfigure(
                p.item, fill=blend((235, 246, 255), alpha)
            )
            r = p.size
            self.canvas.coords(p.item, p.x-r, p.y-r, p.x+r, p.y+r)
            if p.y > H + 10:
                p.life = 0

    def frame(self):
        now = time.perf_counter()
        dt = min(0.033, now - self.last)
        self.last = now
        self.emit(dt)

        alive = []
        for p in self.particles:
            self.update_particle(p, dt)
            if p.kind in ('rain', 'snow') and (
                p.life <= 0 or not -180 < p.x < W + 180
            ):
                self.canvas.delete(p.item)
                self.spawn()
            elif p.life > 0 and -180 < p.x < W + 180:
                alive.append(p)
            else:
                self.canvas.delete(p.item)

        self.particles = alive
        self.canvas.tag_raise(self.title)
        self.canvas.tag_raise(self.help)
        self.root.after(16, self.frame)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    FXApp().run()
