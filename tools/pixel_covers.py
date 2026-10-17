"""Convierte portadas en versiones pixeladas para la página de música.

Pon las imágenes originales en covers_src/ (carpeta del sitio, ignorada por git) con el nombre
del disco en minúsculas y guiones: loveless.jpg, ok-computer.png, glass-ecosystem.png...
El script las recorta al centro en cuadrado, las reduce a N×N píxeles, limita la paleta y las
guarda como PNG diminutos en img/covers/. La web las agranda con `image-rendering: pixelated`.

Uso (desde la carpeta del sitio):
    python -m pip install pillow          # una sola vez
    python tools/pixel_covers.py          # procesa todo lo que haya en covers_src/
    python tools/pixel_covers.py --lista  # dice qué nombres espera para los discos con ⭐
Ajustes en music.json -> "portadas": {"pixeles": 32, "colores": 24}.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITIO = AQUI.parent
EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def slug(texto: str) -> str:
    """'OK Computer' -> 'ok-computer' ; 'Tranquility Base Hotel & Casino' -> 'tranquility-base-hotel-casino'."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if not t:  # títulos sin letras latinas (p. ej. マジックディスク): nombre estable a partir del texto
        t = "disco-" + hashlib.md5(texto.encode("utf-8")).hexdigest()[:6]
    return t


def discos_favoritos(records: Path) -> list[str]:
    """Títulos de la tabla Discos con ⭐ (para --lista)."""
    titulos, en_tabla, encabezado = [], False, None
    for linea in records.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            en_tabla, encabezado = linea[3:].strip().lower() == "discos", None
            continue
        if en_tabla and linea.strip().startswith("|"):
            c = [x.strip() for x in linea.strip().strip("|").split("|")]
            if encabezado is None:
                encabezado = c
                continue
            if c and c[0] and "⭐" in "".join(c) and not set(c[0]) <= set("-: "):
                titulos.append(c[0])
    return titulos


def pixelar(origen: Path, destino: Path, n: int, colores: int) -> None:
    from PIL import Image  # pip install pillow

    img = Image.open(origen).convert("RGB")
    lado = min(img.size)
    x, y = (img.width - lado) // 2, (img.height - lado) // 2
    img = img.crop((x, y, x + lado, y + lado))
    img = img.resize((n, n), Image.Resampling.BOX)  # promedio por bloque: píxel limpio
    img = img.quantize(colors=colores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lista", action="store_true", help="muestra qué archivos espera y cuáles faltan")
    ap.add_argument("--records", help="ruta a Records.md (si no, la de music.json)")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "music.json").read_text(encoding="utf-8"))
    pc = cfg.get("portadas", {})
    origen_dir = SITIO / pc.get("origen", "covers_src")
    destino_dir = SITIO / pc.get("destino", "img/covers")
    n, colores = int(pc.get("pixeles", 32)), int(pc.get("colores", 24))

    if args.lista:
        ruta = Path(args.records or cfg["vault_records"])
        esperados = [slug(t) for t in discos_favoritos(ruta)] + [slug(cfg.get("aero", {}).get("titulo", "glass-ecosystem"))]
        hechos = {p.stem for p in destino_dir.glob("*.png")}
        fuentes = {p.stem for p in origen_dir.glob("*") if p.suffix.lower() in EXT}
        for s in esperados:
            estado = "listo" if s in hechos else ("falta procesar" if s in fuentes else "falta imagen")
            print(f"  {s:<36} {estado}")
        print(f"\nPon las imágenes en {origen_dir} con esos nombres (cualquier extensión: jpg, png, webp).")
        return

    if not origen_dir.exists():
        origen_dir.mkdir(parents=True)
        sys.exit(f"Creé {origen_dir}. Pon ahí las portadas y vuelve a correr el script.")
    archivos = [p for p in sorted(origen_dir.iterdir()) if p.suffix.lower() in EXT]
    if not archivos:
        sys.exit(f"No hay imágenes en {origen_dir}.")
    for p in archivos:
        destino = destino_dir / f"{slug(p.stem)}.png"
        pixelar(p, destino, n, colores)
        print(f"  {p.name:<36} -> img/covers/{destino.name} ({destino.stat().st_size // 1024 or 1} KB)")
    print("\nListo. Corre tools/music_sync.py (o sync.py) para ponerlas en la página.")


if __name__ == "__main__":
    main()
