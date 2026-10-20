"""Monta o reel 9:16: tela de notebook simulada rodando o coração de fogo.

python montar_916.py                 # gera reel.mp4 (1080x1920, 30 fps, com trilha)
python montar_916.py --so-quadro 60  # salva só o quadro 60 em _prev/quadro.png
"""
import math, random, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
VIDEO = AQUI / "coracao_fogo.mp4"
SAIDA = AQUI / "reel.mp4"
CAMA = AQUI.parent.parent / "FILES/brand/audio/bed-dark.mp3"
CODIGO = (AQUI / "coracao_fogo.py").read_text(encoding="utf-8").splitlines()

W, H, FPS = 1080, 1920, 30
PRE = 1.5                 # segundos de VS Code antes da janela abrir
GANCHO = "Pedi um coração e o Python\nentregou pegando fogo"
random.seed(3)

def fonte(nome, tam):
    return ImageFont.truetype(nome, tam)

F_GANCHO = fonte("segoeuib.ttf", 46)
F_CODE = fonte("CascadiaMono.ttf", 15)
F_UI = fonte("segoeui.ttf", 14)
F_TITULO = fonte("segoeui.ttf", 15)


# ---------- fundo: quarto escuro com luz quente ----------
def fundo():
    img = Image.new("RGB", (W, H), (14, 9, 6))
    d = ImageDraw.Draw(img)
    # luz de abajur no canto superior esquerdo
    luz = Image.new("RGB", (W, H), (0, 0, 0))
    ld = ImageDraw.Draw(luz)
    ld.ellipse((-500, -400, 700, 700), fill=(150, 80, 30))
    luz = luz.filter(ImageFilter.GaussianBlur(220))
    img = Image.blend(img, Image.composite(luz, img, luz.convert("L").point(lambda v: min(255, v * 2))), 0.9)
    # pôsteres desfocados na parede
    parede = Image.new("RGB", (W, H), (0, 0, 0))
    pd = ImageDraw.Draw(parede)
    cores = [(120, 40, 30), (160, 110, 40), (60, 70, 110), (140, 60, 90), (90, 100, 50)]
    for i in range(7):
        x = random.randint(-100, W - 150); y = random.randint(60, 760)
        w = random.randint(180, 320); h = random.randint(220, 380)
        pd.rectangle((x, y, x + w, y + h), fill=random.choice(cores))
    parede = parede.filter(ImageFilter.GaussianBlur(18))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, W, 820), fill=70)
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(parede, img, mask)
    # mesa escura embaixo
    md = ImageDraw.Draw(img)
    md.rectangle((0, 1500, W, H), fill=(22, 14, 10))
    return img.filter(ImageFilter.GaussianBlur(1.5))


# ---------- notebook ----------
TELA = (120, 520, 960, 1045)     # área útil da tela (x1, y1, x2, y2)

def notebook(base):
    img = base.copy()
    d = ImageDraw.Draw(img)
    x1, y1, x2, y2 = TELA
    # tampa / bezel
    d.rounded_rectangle((x1 - 34, y1 - 40, x2 + 34, y2 + 40), radius=26, fill=(24, 24, 27))
    d.rounded_rectangle((x1 - 30, y1 - 36, x2 + 30, y2 + 36), radius=22, fill=(10, 10, 12))
    # dobradiça e base
    d.rectangle((x1 - 60, y2 + 40, x2 + 60, y2 + 70), fill=(30, 30, 34))
    d.polygon([(x1 - 60, y2 + 70), (x2 + 60, y2 + 70), (x2 + 130, y2 + 420), (x1 - 130, y2 + 420)],
              fill=(28, 28, 32))
    # teclado com brilho RGB
    kx1, ky1, kx2, ky2 = x1 - 20, y2 + 110, x2 + 20, y2 + 330
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(14):
        cor = [(255, 40, 80), (255, 120, 20), (60, 220, 120), (40, 140, 255), (170, 60, 255)][i % 5]
        gd.rectangle((kx1 + i * 60, ky1 - 10, kx1 + i * 60 + 58, ky2 + 10), fill=cor)
    glow = glow.filter(ImageFilter.GaussianBlur(22))
    img = Image.blend(img, Image.composite(glow, img, Image.new("L", (W, H), 140)), 0.5)
    d = ImageDraw.Draw(img)
    for r in range(6):
        for c in range(20):
            kx = kx1 + 6 + c * 42; ky = ky1 + 6 + r * 36
            d.rounded_rectangle((kx, ky, kx + 36, ky + 30), radius=4, fill=(16, 16, 18))
    d.rounded_rectangle((x1 + 260, ky2 + 24, x2 - 260, ky2 + 110), radius=8, fill=(22, 22, 26))
    return img


# ---------- conteúdo da tela ----------
CORES_TOKEN = {"def": (197, 134, 192), "class": (197, 134, 192), "import": (197, 134, 192),
               "return": (197, 134, 192), "if": (197, 134, 192), "for": (197, 134, 192),
               "else": (197, 134, 192), "elif": (197, 134, 192), "while": (197, 134, 192),
               "self": (156, 220, 254), "random": (78, 201, 176), "math": (78, 201, 176)}

def vscode(largura, altura, scroll):
    img = Image.new("RGB", (largura, altura), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, largura, 30), fill=(60, 60, 60))                 # barra de título
    d.text((10, 7), "coracao_fogo.py - tkinter-fx - Visual Studio Code", font=F_UI, fill=(200, 200, 200))
    d.rectangle((0, 30, 48, altura), fill=(51, 51, 51))                 # activity bar
    d.rectangle((48, 30, 230, altura), fill=(37, 37, 38))               # explorer
    d.text((60, 44), "EXPLORER", font=F_UI, fill=(190, 190, 190))
    for i, n in enumerate(["tkinter-fx", "  fx.py", "  coracao_fogo.py", "  montar_916.py", "  README.md"]):
        d.text((64, 70 + i * 20), n, font=F_UI, fill=(230, 230, 230) if "coracao" in n else (160, 160, 160))
    d.rectangle((230, 30, largura, 58), fill=(37, 37, 38))
    d.rectangle((230, 30, 390, 58), fill=(30, 30, 30))
    d.text((242, 38), "coracao_fogo.py", font=F_UI, fill=(255, 255, 255))
    editor = Image.new("RGB", (largura - 230, altura - 58 - 22), (30, 30, 30))
    ed = ImageDraw.Draw(editor)
    y = 12 - scroll
    for i, linha in enumerate(CODIGO):
        if -20 < y < editor.height:
            ed.text((10, y), f"{i + 1:>3}", font=F_CODE, fill=(110, 110, 110))
            if "#" in linha and not linha.strip().startswith('"""'):
                cod, com = linha.split("#", 1)
                pinta(ed, 50, y, cod, F_CODE)
                ed.text((50 + ed.textlength(cod, font=F_CODE), y), "#" + com, font=F_CODE, fill=(106, 153, 85))
            else:
                pinta(ed, 50, y, linha, F_CODE)
        y += 19
    img.paste(editor, (230, 58))
    d.rectangle((0, altura - 22, largura, altura), fill=(0, 122, 204))  # status bar
    d.text((10, altura - 19), "Python 3.14   UTF-8   Ln 1, Col 1", font=F_UI, fill=(255, 255, 255))
    return img

def pinta(d, x, y, texto, f):
    import re
    for m in re.finditer(r'"[^"]*"|\'[^\']*\'|\w+|\W+', texto):
        t = m.group(0)
        if t[0] in "\"'":
            cor = (206, 145, 120)
        elif t in CORES_TOKEN:
            cor = CORES_TOKEN[t]
        elif t[0].isdigit():
            cor = (181, 206, 168)
        elif t[0].isalpha() and texto[m.end():m.end() + 1] == "(":
            cor = (220, 220, 170)
        else:
            cor = (212, 212, 212)
        d.text((x, y), t, font=f, fill=cor)
        x += d.textlength(t, font=f)


def janela_tk(quadro, escala):
    """Janela do Tkinter com barra de título, com o quadro do coração dentro."""
    lado = int(430 * escala)
    img = Image.new("RGB", (lado, lado + 28), (240, 240, 240))
    d = ImageDraw.Draw(img)
    d.text((8, 6), "coração de fogo", font=F_TITULO, fill=(20, 20, 20))
    d.text((lado - 64, 4), "–    ▢    ×", font=F_TITULO, fill=(40, 40, 40))
    img.paste(quadro.resize((lado, lado), Image.LANCZOS), (0, 28))
    return img


def conteudo_tela(largura, altura, t, quadro):
    scroll = int(min(1.0, t / PRE) * 90)
    tela = vscode(largura, altura, scroll)
    if quadro is not None:
        abrindo = min(1.0, (t - PRE) / 0.25)
        esc = 0.85 + 0.15 * (1 - (1 - abrindo) ** 3)
        jan = janela_tk(quadro, esc)
        tela.paste(jan, ((largura - jan.width) // 2 + 100, (altura - jan.height) // 2 + 8))
    return tela


# ---------- acabamento ----------
def vinheta():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse((-200, -300, W + 200, H + 300), fill=255)
    return m.filter(ImageFilter.GaussianBlur(260))

VINHETA = vinheta()
GRAO = [Image.effect_noise((W, H), 18).convert("L") for _ in range(6)]

def quadro_final(base_notebook, t, quadro, i):
    img = base_notebook.copy()
    x1, y1, x2, y2 = TELA
    tela = conteudo_tela(x2 - x1, y2 - y1, t, quadro)
    img.paste(tela, (x1, y1))
    # reflexo suave da tela no bezel e brilho do fogo no ambiente
    if quadro is not None:
        glow = tela.resize((W, H)).filter(ImageFilter.GaussianBlur(120))
        img = Image.blend(img, Image.composite(glow, img, Image.new("L", (W, H), 60)), 0.5)
        img.paste(tela, (x1, y1))
    # tremor de mão: leve translação + rotação
    dx = 3 * math.sin(t * 1.3) + 1.5 * math.sin(t * 3.7)
    dy = 2 * math.cos(t * 1.1) + 1.2 * math.sin(t * 2.9)
    ang = 0.25 * math.sin(t * 0.7)
    img = img.rotate(ang, resample=Image.BICUBIC, center=(W / 2, H / 2), translate=(dx, dy))
    # vinheta + grão
    img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), VINHETA)
    g = GRAO[i % len(GRAO)]
    img = Image.blend(img, Image.merge("RGB", (g, g, g)), 0.06)
    # gancho no topo
    d = ImageDraw.Draw(img)
    for linha_i, linha in enumerate(GANCHO.split("\n")):
        tw = d.textlength(linha, font=F_GANCHO)
        x = (W - tw) / 2; y = 300 + linha_i * 60
        d.text((x + 2, y + 3), linha, font=F_GANCHO, fill=(0, 0, 0))
        d.text((x, y), linha, font=F_GANCHO, fill=(255, 255, 255))
    return img


def ler_video():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(VIDEO), "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = p.stdout.read(800 * 800 * 3)
        if len(raw) < 800 * 800 * 3:
            break
        yield Image.frombytes("RGB", (800, 800), raw)


def main():
    base = notebook(fundo())
    quadros_video = ler_video()
    n_pre = int(PRE * FPS)
    so = None
    if "--so-quadro" in sys.argv:
        so = int(sys.argv[sys.argv.index("--so-quadro") + 1])
    ff = None
    if so is None:
        ff = subprocess.Popen(["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-stream_loop", "-1", "-i", str(CAMA),
                               "-filter_complex", "[1:a]volume=-9dB,afade=t=in:d=1,afade=t=out:st=14.2:d=1.4[a]",
                               "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                               "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", str(SAIDA)],
                              stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    i = 0
    quadro = None
    while True:
        t = i / FPS
        if i >= n_pre:
            quadro = next(quadros_video, None)
            if quadro is None:
                break
        img = quadro_final(base, t, quadro, i)
        if so is not None:
            if i == so:
                (AQUI / "_prev").mkdir(exist_ok=True)
                img.save(AQUI / "_prev/quadro.png"); print("salvo"); return
        else:
            ff.stdin.write(img.tobytes())
        i += 1
    ff.stdin.close(); ff.wait()
    print("gerado", SAIDA, "quadros", i)


if __name__ == "__main__":
    main()
