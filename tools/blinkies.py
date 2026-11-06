"""Blinkies de LeOS: GIFs de 150x20 con texto en una fuente pixel de 5x7.

Uso (desde la carpeta del sitio):
    python tools/blinkies.py

Para hacer uno nuevo, agrega una entrada a BLINKIES y vuelve a correrlo.
Los GIF salen en img/blinkies/<nombre>.gif. Necesita Pillow.
Para rehacer solo uno: python tools/blinkies.py pixel-art

Estilos de animación:
    "parpadeo"  el texto alterna entre dos colores
    "arcoiris"  cada letra cambia de color en ola (colores del N64)
    "brillos"   estrellitas que titilan a los lados
    "barrido"   una franja de luz recorre el fondo
"""
from pathlib import Path
from PIL import Image

try:
    from blinkies_iconos import ICONOS, cuadro as cuadro_icono
except ImportError:  # al correrlo desde otra carpeta
    import sys as _s
    _s.path.insert(0, str(Path(__file__).resolve().parent))
    from blinkies_iconos import ICONOS, cuadro as cuadro_icono

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "img" / "blinkies"

BLINKIES = [
    # nombre, texto, fondo (arriba, abajo), borde, colores de texto, estilo[, ícono de blinkies_iconos.py]
    ("hecho-a-mano", "* HECHO A MANO *", ("#2a2463", "#1a1645"), "#5fe0ff", ("#5fe0ff", "#e8f4ff"), "parpadeo"),
    ("team-3ds", "TEAM 3DS", ("#9a80ff", "#7b5cff"), "#2a1f6e", ("#ffffff", "#ffc20e"), "brillos"),
    ("n64-kid", "N64 KID", ("#1a1645", "#0b0920"), "#9aa6d6", ("#e2231a", "#ffc20e", "#00a650", "#4a9bff"), "arcoiris"),
    # colores de las Game Boy Color: Teal de fondo, letras Dandelion, brillos Kiwi
    ("pixel-art", "+ PIXEL ART +", ("#1fb5ad", "#0b7f7a"), "#063f3c", ("#ffe04a", "#b5e61d"), "brillos"),
    ("shoegaze", "ESCUCHO SHOEGAZE", ("#3d3489", "#c3a8ff"), "#120f2e", ("#ffffff", "#e8f4ff"), "barrido"),
    ("modo-noche", "MODO NOCHE: ON", ("#0b0920", "#120f2e"), "#ffc20e", ("#ffc20e", "#fff3a0"), "brillos"),
    ("insert-coin", "INSERT COIN", ("#000000", "#1a0000"), "#e2231a", ("#ff3b2f", "#000000"), "parpadeo"),
    ("explora", "?Y SI EXPLORAS?", ("#000000", "#0b0920"), "#ffc20e", ("#ffc20e", "#e8f4ff"), "parpadeo"),

    # ---- Intereses (ventana "Intereses" de la portada). Solo texto: nada de logos ni personajes.
    ("i-majoras-mask", "MAJORA'S MASK", ("#3b1d5e", "#1a0b2e"), "#ffc20e", ("#ffc20e", "#ff6f91"), "parpadeo", "reloj"),
    ("i-ocarina", "OCARINA OF TIME", ("#1f6b3a", "#0d3b1f"), "#c9a227", ("#f2d16b", "#ffffff"), "brillos", "nota"),
    ("i-pokemon-crystal", "POKÉMON CRYSTAL", ("#5fc8e8", "#1c8fc4"), "#0b3a5e", ("#ffffff", "#e8f4ff"), "brillos", "cristal"),
    ("i-stadium", "POKÉMON STADIUM", ("#c8302a", "#7a1a16"), "#000000", ("#ffffff", "#ffc20e"), "barrido", "trofeo"),
    ("i-dkc", "DONKEY KONG COUNTRY", ("#6b3b1a", "#3a1f0b"), "#ffc20e", ("#ffc20e", "#ffffff"), "parpadeo", "platano"),
    ("i-starfox", "STAR FOX 64", ("#0b0920", "#1a1645"), "#4a9bff", ("#e8f4ff", "#4a9bff"), "brillos", "estrella"),
    ("i-creepypastas", "CREEPYPASTAS 2010", ("#000000", "#1a0000"), "#5a0000", ("#e2231a", "#5a0000"), "parpadeo", "fantasma"),
    ("i-frutiger", "FRUTIGER AERO", ("#bfe9ff", "#5fc8e8"), "#1c8fc4", ("#0b3a5e", "#ffffff"), "barrido", "burbuja"),
    ("i-windows-xp", "NOSTALGIA DE XP", ("#3d95ff", "#0052e5"), "#003dd7", ("#ffffff", "#bfe9ff"), "barrido", "ventana"),
    ("i-y2k", "Y2K FOREVER", ("#c3a8ff", "#7b5cff"), "#2a1f6e", ("#ffffff", "#5fe0ff", "#ffc20e", "#ff8ad8"), "arcoiris", "disco"),
    ("i-britpop", "BRITPOP & INDIE", ("#1a1645", "#0b0920"), "#e2231a", ("#e8f4ff", "#4a9bff", "#e2231a"), "arcoiris", "casete"),
    ("i-guitarra", "TOCO LA GUITARRA", ("#2a1a0b", "#120b05"), "#c2862a", ("#f2d16b", "#ffffff"), "brillos", "guitarra"),
    ("i-produzco", "PRODUZCO MÚSICA", ("#0b3a5e", "#120f2e"), "#5fe0ff", ("#5fe0ff", "#ffffff"), "parpadeo", "ecualizador"),
    ("i-scifi", "CIENCIA FICCIÓN", ("#0b0920", "#000000"), "#00a650", ("#00a650", "#bdf6ff"), "brillos", "ovni"),
    ("i-comics", "LECTOR DE CÓMICS", ("#ffc20e", "#e0a000"), "#000000", ("#000000", "#c8302a"), "parpadeo", "pow"),
    ("i-fisica", "FÍSICA Y FILOSOFÍA", ("#2a2463", "#120f2e"), "#9aa6d6", ("#e8f4ff", "#9aa6d6"), "barrido", "atomo"),
    ("i-anime", "ANIME DE LOS 2000", ("#ff8ad8", "#c3a8ff"), "#5a1048", ("#ffffff", "#120f2e"), "barrido", "tele"),
    ("i-foto", "FOTO ANALÓGICA", ("#3a2a20", "#1a120b"), "#ff8a1f", ("#ff8a1f", "#f4f1e8"), "parpadeo", "camara"),
]

# Fuente 5x7 (solo mayúsculas, números y algunos signos). "?" al inicio se dibuja como "¿"; "<3" es un corazón.
FUENTE = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "Ñ": ["01110", "00000", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    "*": ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "¿": ["00100", "00000", "00100", "01000", "10000", "10001", "01110"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00001", "00010", "00100", "01000", "10000", "10000"],
    "♥": ["00000", "01010", "11111", "11111", "01110", "00100", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
}
W, H = 150, 20


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def preparar(texto):
    t = texto.replace("<3", "♥")
    if t.startswith("?"):
        t = "¿" + t[1:]
    return t


def fondo(c1, c2, borde, franja=None):
    im = Image.new("RGB", (W, H))
    a, b = rgb(c1), rgb(c2)
    for y in range(H):
        k = y / (H - 1)
        col = tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))
        for x in range(W):
            c = col
            if franja is not None and abs(x - franja - y) < 6:
                c = tuple(min(255, v + 55) for v in col)
            im.putpixel((x, y), c)
    br = rgb(borde)
    for x in range(W):
        im.putpixel((x, 0), br); im.putpixel((x, H - 1), br)
    for y in range(H):
        im.putpixel((0, y), br); im.putpixel((W - 1, y), br)
    return im


ACENTOS = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}
TILDE = ["00010", "00100"]  # se dibuja encima de la letra, fuera de sus 7 filas


def texto_en(im, t, colores, sombra=(0, 0, 0), izquierda=0):
    ancho = len(t) * 6 - 1
    x0, y0 = izquierda + (W - izquierda - ancho) // 2, (H - 7) // 2
    for i, ch in enumerate(t):
        g = FUENTE.get(ACENTOS.get(ch, ch), FUENTE[" "])
        if ch in ACENTOS:
            g = TILDE + g
        col = colores[i % len(colores)] if isinstance(colores, list) else colores
        dy = -2 if ch in ACENTOS else 0
        for y, fila in enumerate(g, start=dy):
            for x, bit in enumerate(fila):
                if bit == "1":
                    px, py = x0 + i * 6 + x, y0 + y
                    if px + 1 < W - 1 and py + 1 < H - 1:
                        im.putpixel((px + 1, py + 1), sombra)
                    im.putpixel((px, py), col)


def brillo(im, x, y, fase, color=(255, 255, 255)):
    puntos = [(0, 0)] if fase == 0 else [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)] if fase == 1 else \
        [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)]
    for dx, dy in puntos:
        if 0 < x + dx < W - 1 and 0 < y + dy < H - 1:
            im.putpixel((x + dx, y + dy), color)


def pegar_icono(im, nombre, f):
    rows, pal = cuadro_icono(nombre, f)
    for y, fila in enumerate(rows):
        for x, ch in enumerate(fila):
            if ch in pal:
                im.putpixel((4 + x, 4 + y), rgb(pal[ch]))


def hacer(nombre, texto, bg, borde, colores, estilo, icono=None):
    t = preparar(texto)
    cols = [rgb(c) for c in colores]
    cuadros = []
    n = 8 if (estilo in ("arcoiris", "barrido") or icono) else 4
    izq = 16 if icono else 0
    for f in range(n):
        im = fondo(bg[0], bg[1], borde, franja=(f * 24 - 20) if estilo == "barrido" else None)
        if estilo == "parpadeo":
            texto_en(im, t, cols[(f // (2 if n == 8 else 1)) % 2], izquierda=izq)
        elif estilo == "arcoiris":
            texto_en(im, t, [cols[(i + f) % len(cols)] for i in range(len(t))], izquierda=izq)
        else:
            texto_en(im, t, cols[0], izquierda=izq)
        if estilo == "brillos":
            puntos = ((W - 8, 6), (W - 15, 13)) if icono else ((7, 6), (14, 13), (W - 8, 6), (W - 15, 13))
            for k, (x, y) in enumerate(puntos):
                brillo(im, x, y, (f + k) % 3, cols[1])
        if icono:
            pegar_icono(im, icono, f)
        cuadros.append(im.convert("P", palette=Image.Palette.ADAPTIVE, colors=64))
    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / f"{nombre}.gif"
    cuadros[0].save(ruta, save_all=True, append_images=cuadros[1:], duration=(150 if icono else 180) if n == 8 else 380, loop=0)
    print(f"  ✓ {ruta.relative_to(RAIZ)}")


if __name__ == "__main__":
    import sys
    solo = set(sys.argv[1:])
    for b in BLINKIES:
        if not solo or b[0] in solo:
            hacer(*b)
