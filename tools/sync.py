"""Actualiza todo el sitio desde el vault de una sola vez.

Corre, en orden: now_sync (portada), shelf_sync (videojuegos), music_sync (música),
anime_sync (anime y manga) y cine_sync (cine, series y cómics).

Uso (desde la carpeta del sitio):
    python tools/sync.py            # actualiza todas las páginas
    python tools/sync.py --dry-run  # solo muestra los resúmenes
"""

import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCRIPTS = [
    ("Portada", "now_sync.py"),
    ("Videojuegos", "shelf_sync.py"),
    ("Música", "music_sync.py"),
    ("Anime y manga", "anime_sync.py"),
    ("Cine, series y cómics", "cine_sync.py"),
]


def main() -> None:
    extra = [a for a in sys.argv[1:] if a == "--dry-run"]
    fallos = []
    for nombre, script in SCRIPTS:
        print(f"\n=== {nombre} ({script}) ===")
        r = subprocess.run([sys.executable, str(AQUI / script), *extra])
        if r.returncode != 0:
            fallos.append(nombre)
    print("\n" + ("Todo listo." if not fallos else "Fallaron: " + ", ".join(fallos)))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
