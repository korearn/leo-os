"""Banners pixelados para la pantalla de arriba de la 3DS (portada).

La 3DS de la portada muestra en su pantalla superior el "banner" de cada app
cuando pasas el mouse por su icono. Este script convierte capturas normales en
imágenes de 200x120 con paleta reducida y tramado, que el CSS escala a 2x con
`image-rendering: pixelated`.

Uso (desde la carpeta del sitio):
    python tools/ds_banners.py

Para cambiar la imagen de una app, edita BANNERS y vuelve a correrlo.
Necesita Pillow: pip install pillow
"""
from pathlib import Path
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "img" / "3ds"

# app -> imagen de origen (relativa a la carpeta del sitio)
BANNERS = {
    "juegos": "img/shots/ffx.webp",
    "musica": "covers_src/glass-ecosystem.png",
    "cine": "img/shots/nms-saturn.webp",
    "galeria": "img/shots/cyber2077-cars.webp",
    "sobre-mi": "img/shots/outer-wilds.webp",
    "libro": "img/shots/hollow-night.webp",
}
ANCHO, ALTO = 200, 120   # la mitad de la pantalla superior de la 3DS (400x240)
COLORES = 40


def recortar(im, w, h):
    """Recorte centrado a la proporción w:h."""
    ratio = w / h
    iw, ih = im.size
    if iw / ih > ratio:
        nw = int(ih * ratio)
        x = (iw - nw) // 2
        return im.crop((x, 0, x + nw, ih))
    nh = int(iw / ratio)
    y = (ih - nh) // 2
    return im.crop((0, y, iw, y + nh))


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for app, origen in BANNERS.items():
        ruta = RAIZ / origen
        if not ruta.exists():
            print(f"  ! falta {origen} (banner de {app})")
            continue
        im = Image.open(ruta).convert("RGB")
        im = recortar(im, ANCHO, ALTO).resize((ANCHO, ALTO), Image.LANCZOS)
        im = im.quantize(colors=COLORES, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        salida = DESTINO / f"{app}.png"
        im.save(salida, optimize=True)
        print(f"  ✓ {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
