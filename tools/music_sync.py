"""Genera las listas de la página Música desde el vault.

- Records.md: "Escuchando ahora" y "Discos" (los ⭐ salen como estuches de CD).
- Bands.md: el top de bandas (lista numerada, en orden).

Reescribe en musica.html lo que hay entre <!-- music:ahora/discos/bandas:start/end -->.

Uso (desde la carpeta del sitio):
    python tools/music_sync.py            # actualiza musica.html
    python tools/music_sync.py --dry-run  # solo muestra el resumen
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
e = html.escape
PALETA = [("#1f5fb0", "#5fe0ff"), ("#7b3fa8", "#d6337a"), ("#2f8f4e", "#c9e27a"), ("#c2862a", "#3a2a57"),
          ("#0e7d6e", "#bff3ff"), ("#b83a3a", "#f2c230"), ("#3a3f9a", "#7b5cff"), ("#5a5a66", "#d9d9e0")]


def celdas(fila: str) -> list[str]:
    fila = fila.strip().strip("|").replace("\\|", "\0")
    return [c.strip().replace("\0", "|") for c in fila.split("|")]


def leer_tablas(ruta: Path) -> dict[str, list[dict]]:
    """Devuelve {seccion: [filas como dict]} para cada '## seccion' con tabla."""
    tablas: dict[str, list[dict]] = {}
    seccion, encabezado = None, None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion, encabezado = linea[3:].strip(), None
            tablas.setdefault(seccion, [])
        elif linea.strip().startswith("|") and seccion:
            c = celdas(linea)
            if encabezado is None:
                encabezado = [x.lower() for x in c]
                continue
            if all(set(x) <= set("-: ") for x in c) or not c[0]:
                continue
            fila = dict(zip(encabezado, c))
            fila["_fav"] = "⭐" in "".join(c)
            tablas[seccion].append(fila)
    return tablas


def leer_bandas(ruta: Path) -> list[str]:
    bandas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*\d+\.\s+(.+?)\s*$", linea)
        if m:
            bandas.append(re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", m.group(1)))
    return bandas


def colores(titulo: str, cfg: dict) -> str:
    if titulo in cfg.get("discos", {}):
        return cfg["discos"][titulo]
    a, b = PALETA[int(hashlib.md5(titulo.encode("utf-8")).hexdigest(), 16) % len(PALETA)]
    return f"--cover:{a};--cover2:{b}"


def html_ahora(filas: list[dict]) -> str:
    out = []
    for f in filas:
        que, artista, nota = f.get("qué", f.get("que", "")), f.get("artista", ""), f.get("nota", "")
        detalle = artista + (f" ({nota})" if nota else "")
        out.append(f"              <dt>{e(que)}</dt>")
        out.append(f"              <dd>{e(detalle)}</dd>")
    return "\n".join(out) + "\n"


def html_discos(filas: list[dict], cfg: dict) -> str:
    favs = [f for f in filas if f["_fav"]]
    favs.sort(key=lambda f: (f.get("año", "") or "9999", f.get("disco", "").lower()))
    out = []
    for f in favs:
        titulo = f.get("disco", "")
        out.append(f'              <li class="cd" style="{e(colores(titulo, cfg))}">')
        out.append('                <span class="cd__case" aria-hidden="true"></span>')
        out.append(f'                <span class="cd__title">{e(titulo)}</span>')
        out.append(f'                <span class="cd__artist">{e(f.get("artista", ""))}</span>')
        if f.get("año"):
            out.append(f'                <span class="cd__year">{e(f["año"])}</span>')
        if f.get("nota"):
            out.append(f'                <span class="cd__note">{e(f["nota"])}</span>')
        out.append("              </li>")
    return "\n".join(out) + "\n"


def html_bandas(bandas: list[str], top: int) -> str:
    I = "            "
    out = [f'{I}<ol class="top10">']
    out += [f"{I}  <li>{e(b)}</li>" for b in bandas[:top]]
    out.append(f"{I}</ol>")
    if len(bandas) > top:
        out.append(f'{I}<ol class="rest" start="{top + 1}">')
        out += [f"{I}  <li>{e(b)}</li>" for b in bandas[top:]]
        out.append(f"{I}</ol>")
    return "\n".join(out) + "\n"


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(rf"(<!-- music:{nombre}:start -->\n?)(.*?)([ \t]*<!-- music:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        sys.exit(f"Falta el marcador music:{nombre} en la página")
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="no escribe, solo muestra el resumen")
    ap.add_argument("--records", help="ruta a Records.md")
    ap.add_argument("--bands", help="ruta a Bands.md")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "music.json").read_text(encoding="utf-8"))
    tablas = leer_tablas(Path(args.records or cfg["vault_records"]))
    bandas = leer_bandas(Path(args.bands or cfg["vault_bands"]))
    ahora, discos = tablas.get("Escuchando ahora", []), tablas.get("Discos", [])
    pagina = (AQUI / cfg["pagina"]).resolve()

    print(f"Escuchando ahora: {len(ahora)}  ·  Discos: {len(discos)} ({sum(d['_fav'] for d in discos)} ⭐)  ·  Bandas: {len(bandas)}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "ahora", html_ahora(ahora))
    doc = reemplazar(doc, "discos", html_discos(discos, cfg))
    doc = reemplazar(doc, "bandas", html_bandas(bandas, cfg.get("top", 10)))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
