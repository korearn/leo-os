"""Íconos pixel de 12x12 (originales) para los blinkies de intereses.

Cada ícono es una función icono(f) -> lista de 12 filas de 12 caracteres para el cuadro f (0..7),
más una paleta {caracter: color}. Solo formas genéricas: nada de diseños reconocibles de una
franquicia (máscaras, Pokémon, naves, logos), para que el sitio pueda usarlos sin problema.
"""
import math

def vacio():
    return [["."] * 12 for _ in range(12)]

def filas(m):
    return ["".join(r) for r in m]

def mover(rows, dy):
    if dy == 0:
        return rows
    vac = "." * 12
    return ([vac] * dy + rows[:12 - dy]) if dy > 0 else (rows[-dy:] + [vac] * (-dy))

BOB = [0, 0, -1, -1, 0, 0, 1, 1]

# ---------- dibujados a mano ----------
NOTA = ["....XXXXXXX.", "....XyyyyyX.", "....XXXXXyX.", "....X...XyX.", "....X...XyX.", "....X...XyX.",
        "..XXX..XXyX.", ".XyyX.XyyyX.", ".XyyX.XyyyX.", "..XX...XXX..", "............", "............"]
CRISTAL = [".....XX.....", "....XcwX....", "...XccwcX...", "..XcccwccX..", "..XccwcccX..", "..XcwccccX..",
           "..XwcccccX..", "..XccccdcX..", "...XcccdX...", "....XcdX....", ".....XX.....", "............"]
TROFEO = ["..XXXXXXXX..", ".XyyyyyyyyX.", "XXyyyywyyyXX", "XyXyyywyyXyX", "X.XyyyyyyX.X", "..XyyyyyyX..",
          "...XyyyyX...", "....XyyX....", ".....XX.....", "....XyyX....", "...XXXXXX...", "...XddddX..."]
PLATANO = ["........XX..", ".......XbX..", "......XyyX..", ".....XyyyX..", "....XyyyX...", "...XyyyyX...",
           "..XyyyyX....", ".XyyyyX.....", ".XyyyX......", "XyyyX.......", "XyyX........", ".XX........."]
FANTASMA = ["....XXXX....", "..XXwwwwXX..", ".XwwwwwwwwX.", ".XwEEwwEEwX.", ".XwEEwwEEwX.", ".XwwwwwwwwX.",
            ".XwwwEEwwwX.", ".XwwwwwwwwX.", ".XwwwwwwwwX.", ".XwXwwXwwXX.", ".XX.XX.XX...", "............"]
VENTANA = ["XXXXXXXXXXXX", "XbbbbbbbbrrX", "XbbbbbbbbrwX", "XXXXXXXXXXXX", "XwwwwwwwwwwX", "XwggwwwwwwwX",
           "XwggwwwwwwwX", "XwwwwwwwwwwX", "XwwwwwyywwwX", "XwwwwwyywwwX", "XwwwwwwwwwwX", "XXXXXXXXXXXX"]
CASETE = ["............", "XXXXXXXXXXXX", "XggggggggggX", "XgwwwwwwwwgX", "XgwXXwwXXwgX", "XgwXwXXwXwgX",
          "XgwXXwwXXwgX", "XgwwwwwwwwgX", "XggggggggggX", "XgggXXXXgggX", "XXXXXXXXXXXX", "............"]
GUITARRA = ["..........XX", ".........XmX", "........XmX.", ".......XmX..", "......XmX...", "..XXXXmX....",
            ".XrrrrXX....", "XrrXXrrX....", "XrrXXrrX....", "XrrrrrX.....", ".XrrrX......", "..XXX......."]
OVNI = ["............", "....XXXX....", "...XccccX...", "...XcwccX...", ".XXXXXXXXXX.", "XggggggggggX",
        "Xg1gg2gg3ggX", ".XXXXXXXXXX.", "...y.y.y.y..", "..y.y.y.y...", "............", "............"]
POW = ["X....X....X.", ".X..XyX..X..", "..XXyyyXX...", ".XyyyyyyyX..", "XyyrryrryyX.", ".XyryryryyyX",
       "XyyrryrrryX.", ".XyryyryyyyX", "..XyyyyyyX..", ".X.XXyXX.X..", "X....X....X.", "............"]
TELE = ["...X....X...", "....X..X....", ".....XX.....", "XXXXXXXXXXXX", "XssssssssgdX", "XsSsssssXgdX",
        "XssssssssgdX", "XsssssSssgdX", "XssssssssgdX", "XXXXXXXXXXXX", ".XX......XX.", "............"]
CAMARA = ["............", "...XXX......", "XXXXwXXXXXXX", "XggggggggggX", "XgggXXXXgggX", "XggXcccwXggX",
          "XggXcwccXggX", "XggXccccXggX", "XgggXXXXgggX", "XggggggggggX", "XXXXXXXXXXXX", "............"]

def a_mano(rows, anim="bob"):
    def fn(f):
        return mover(rows, BOB[f % 8]) if anim == "bob" else rows
    return fn

# ---------- procedurales ----------
def reloj(f):
    m = vacio()
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - 5.5, y - 5.5)
            if d <= 5.6:
                m[y][x] = "X" if d > 4.6 else "w"
    for y, x in ((1, 5), (1, 6), (10, 5), (10, 6), (5, 1), (6, 1), (5, 10), (6, 10)):
        m[y][x] = "d"
    ang = f / 8 * 2 * math.pi
    for r in range(4):
        x = round(5.5 + math.sin(ang) * r - .5 + .5)
        y = round(5.5 - math.cos(ang) * r - .5 + .5)
        m[min(11, max(0, y))][min(11, max(0, x))] = "r"
    m[5][5] = m[6][6] = "X"
    return filas(m)

def burbuja(f):
    m = vacio()
    dy = [0, -1, -1, -2, -2, -1, -1, 0][f % 8]
    cy = 6 + dy
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - 5.5, y - cy + .5)
            if 3.6 < d <= 4.6:
                m[y][x] = "c"
            elif d <= 3.6:
                m[y][x] = "a"
    for y, x in ((cy - 3, 4), (cy - 2, 3), (cy - 3, 5)):
        if 0 <= y < 12:
            m[y][x] = "w"
    if f % 4 < 2:
        m[11][9] = "c"; m[10][10] = "c"
    return filas(m)

def disco(f):
    m = vacio()
    cols = "pcyg"
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - 5.5, y - 5.5)
            if d > 5.8:
                continue
            if d < 1.2:
                m[y][x] = "."
            elif d < 2.2:
                m[y][x] = "X"
            elif d > 5:
                m[y][x] = "X"
            else:
                a = (math.degrees(math.atan2(y - 5.5, x - 5.5)) + f * 45) % 360
                m[y][x] = cols[int(a // 90)]
    return filas(m)

def ecualizador(f):
    alturas = [[3, 6, 9, 5, 7, 4], [5, 9, 6, 8, 4, 7], [8, 5, 7, 10, 6, 3], [6, 7, 4, 6, 9, 8],
               [4, 10, 8, 5, 6, 9], [7, 6, 10, 7, 3, 6], [9, 4, 6, 9, 8, 5], [5, 8, 5, 4, 10, 7]][f % 8]
    m = vacio()
    for i, h in enumerate(alturas):
        for y in range(12 - h, 12):
            col = "r" if y < 3 else "y" if y < 6 else "g"
            m[y][i * 2] = col
            m[y][i * 2 + 1] = col
    return filas(m)

def atomo(f):
    m = vacio()
    for t in range(0, 360, 6):
        r = math.radians(t)
        for k, rot in enumerate((0, 60, 120)):
            a = math.radians(rot)
            x = 5.5 + 5.2 * math.cos(r) * math.cos(a) - 2.0 * math.sin(r) * math.sin(a)
            y = 5.5 + 5.2 * math.cos(r) * math.sin(a) + 2.0 * math.sin(r) * math.cos(a)
            m[round(y)][round(x)] = "c"
    for y, x in ((5, 5), (5, 6), (6, 5), (6, 6)):
        m[y][x] = "r"
    for k, rot in enumerate((0, 60, 120)):
        r = math.radians(f * 45 + k * 120)
        a = math.radians(rot)
        x = 5.5 + 5.2 * math.cos(r) * math.cos(a) - 2.0 * math.sin(r) * math.sin(a)
        y = 5.5 + 5.2 * math.cos(r) * math.sin(a) + 2.0 * math.sin(r) * math.cos(a)
        m[round(y)][round(x)] = "w"
    return filas(m)

def estrella_fugaz(f):
    m = vacio()
    x0 = [9, 8, 7, 6, 5, 4, 3, 2][f % 8]
    y0 = [2, 3, 4, 5, 6, 7, 8, 9][f % 8]
    for k in range(1, 5):
        xx, yy = x0 + k, y0 - k
        if 0 <= xx < 12 and 0 <= yy < 12:
            m[yy][xx] = "c" if k < 3 else "d"
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x0 + dx < 12 and 0 <= y0 + dy < 12:
            m[y0 + dy][x0 + dx] = "y" if (dx, dy) != (0, 0) else "w"
    return filas(m)

ICONOS = {
    "reloj": (reloj, {"X": "#120f2e", "w": "#f4f1e8", "d": "#7b5cff", "r": "#e2231a"}),
    "nota": (a_mano(NOTA), {"X": "#120f2e", "y": "#ffc20e"}),
    "cristal": (a_mano(CRISTAL), {"X": "#0b3a5e", "c": "#5fe0ff", "w": "#ffffff", "d": "#1c8fc4"}),
    "trofeo": (a_mano(TROFEO), {"X": "#3a2a00", "y": "#ffc20e", "w": "#fff3a0", "d": "#8a6400"}),
    "platano": (a_mano(PLATANO), {"X": "#3a2a00", "y": "#ffe04a", "b": "#6b3b1a"}),
    "estrella": (estrella_fugaz, {"y": "#ffc20e", "w": "#ffffff", "c": "#4a9bff", "d": "#1c3d8f"}),
    "fantasma": (a_mano(FANTASMA), {"X": "#000000", "w": "#e8f4ff", "E": "#000000"}),
    "burbuja": (burbuja, {"c": "#1c8fc4", "a": "#bfe9ff", "w": "#ffffff"}),
    "ventana": (a_mano(VENTANA, "fijo"), {"X": "#003dd7", "b": "#3d95ff", "r": "#e9765b", "w": "#ffffff", "g": "#8fd16a", "y": "#ffc20e"}),
    "disco": (disco, {"X": "#4d44a6", "p": "#f3c6ff", "c": "#bfe9ff", "y": "#fff6b8", "g": "#b8ffd9"}),
    "casete": (a_mano(CASETE), {"X": "#000000", "g": "#4d44a6", "w": "#e8f4ff"}),
    "guitarra": (a_mano(GUITARRA), {"X": "#120b05", "m": "#c2862a", "r": "#e2231a"}),
    "ecualizador": (ecualizador, {"r": "#e2231a", "y": "#ffc20e", "g": "#00a650"}),
    "ovni": (a_mano(OVNI), {"X": "#120f2e", "c": "#5fe0ff", "w": "#ffffff", "g": "#9aa6d6", "1": "#e2231a", "2": "#ffc20e", "3": "#00a650", "y": "#fff3a0"}),
    "pow": (a_mano(POW, "fijo"), {"X": "#000000", "y": "#ffe04a", "r": "#e2231a"}),
    "atomo": (atomo, {"c": "#9aa6d6", "r": "#e2231a", "w": "#ffffff"}),
    "tele": (a_mano(TELE, "fijo"), {"X": "#120f2e", "s": "#5fe0ff", "S": "#ffffff", "g": "#4d44a6", "d": "#2a2463"}),
    "camara": (a_mano(CAMARA, "fijo"), {"X": "#120f2e", "g": "#9aa6d6", "c": "#4a9bff", "w": "#ffffff"}),
}

def cuadro(nombre, f):
    fn, pal = ICONOS[nombre]
    rows = fn(f)
    if nombre == "tele" and f % 2:          # estática: cambia unos pixeles
        rows = [r.replace("s", "S", 1) if i in (5, 7) else r for i, r in enumerate(rows)]
    if nombre == "camara" and f in (2, 3):  # flash
        rows = ["...XXX..www." if i == 1 else r.replace("X", "X") for i, r in enumerate(rows)]
        pal = dict(pal, w="#ffffff")
    if nombre == "fantasma" and f % 4 == 3: # parpadea
        rows = [r.replace("EE", "ww") if i in (3, 4) else r for i, r in enumerate(rows)]
    if nombre == "pow" and f % 2:
        pal = dict(pal, y="#ffffff", r="#e2231a")
    return rows, pal
