"""Genera las listas de la página Música desde el vault.

- Now.md (filas Music): "Escuchando ahora" (el artista se toma de Discos).
- Records.md: "Discos" (los ⭐ salen como estuches de CD). "Mi nota" solo vive en el vault.
- Canon.md: solo avisos (obras del Registro sin ficha).
- Bands.md: "Top reciente" (numerada, de Spotify) y "De siempre" (las que han pasado por el top; salen plegadas).

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

from now_lib import _clave, leer_now, revisar_registro
from pixel_covers import slug

AQUI = Path(__file__).resolve().parent
SITIO = AQUI.parent
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


def leer_bandas(ruta: Path) -> tuple[list[str], list[str]]:
    """Devuelve (top reciente numerado, 'De siempre'). Sin secciones, toda lista numerada es el top."""
    top, siempre, seccion = [], [], ""
    limpio = lambda s: re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", s)
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion = linea[3:].strip().lower()
            continue
        m = re.match(r"^\s*\d+\.\s+(.+?)\s*$", linea)
        if m and seccion != "de siempre":
            top.append(limpio(m.group(1)))
            continue
        m = re.match(r"^\s*[-*]\s+(.+?)\s*$", linea)
        if m and seccion == "de siempre":
            siempre.append(limpio(m.group(1)))
    return top, siempre


def colores(titulo: str, cfg: dict) -> str:
    if titulo in cfg.get("discos", {}):
        return cfg["discos"][titulo]
    a, b = PALETA[int(hashlib.md5(titulo.encode("utf-8")).hexdigest(), 16) % len(PALETA)]
    return f"--cover:{a};--cover2:{b}"


def html_ahora(escuchando: list[dict], discos: list[dict]) -> str:
    """Filas Music de Now.md; el artista sale de la tabla Discos si el título coincide."""
    I = "              "
    if not escuchando:
        return f"{I}<dt>Silencio</dt>\n{I}<dd>Nada en repeat por ahora.</dd>\n"
    por_titulo = {_clave(d.get("disco", "")): d for d in discos}
    out = []
    for f in escuchando:
        d = por_titulo.get(_clave(f["obra"]), {})
        detalle = ", ".join(x for x in [d.get("artista", ""), f.get("sobre", "")] if x)
        out.append(f"{I}<dt>{e(f['obra'])}</dt>")
        out.append(f"{I}<dd>{e(detalle)}</dd>")
    return "\n".join(out) + "\n"


def html_discos(filas: list[dict], cfg: dict) -> str:
    favs = [f for f in filas if f["_fav"]]
    favs.sort(key=lambda f: (f.get("año", "") or "9999", f.get("disco", "").lower()))
    out = []
    for f in favs:
        titulo = f.get("disco", "")
        out.append(f'              <li class="cd" style="{e(colores(titulo, cfg))}">')
        portada = SITIO / "img" / "covers" / f"{slug(titulo)}.png"
        if portada.exists():
            out.append('                <span class="cd__case cd__case--art" aria-hidden="true">'
                       f'<img src="img/covers/{portada.name}" alt="" width="32" height="32" loading="lazy"></span>')
        else:
            out.append('                <span class="cd__case" aria-hidden="true"></span>')
        out.append(f'                <span class="cd__title">{e(titulo)}</span>')
        out.append(f'                <span class="cd__artist">{e(f.get("artista", ""))}</span>')
        if f.get("año"):
            out.append(f'                <span class="cd__year">{e(f["año"])}</span>')
        if f.get("nota"):
            out.append(f'                <span class="cd__note">{e(f["nota"])}</span>')
        out.append("              </li>")
    return "\n".join(out) + "\n"


def _seg(d: str) -> int:
    m, _, s = d.partition(":")
    return int(m or 0) * 60 + int(s or 0) if d else 0


def html_aero(a: dict) -> str:
    """Lista de pistas, pie con enlaces y datos para el reproductor (lee música real desde 'base')."""
    I = "          "
    pistas = a.get("pistas", [])
    out = [f'{I}<ol class="playlist" id="playlist">']
    for i, p in enumerate(pistas):
        actual = ' aria-current="true"' if i == 0 else ""
        out.append(f'{I}  <li><button type="button" data-i="{i}"{actual}><span>{e(p["titulo"])}</span>'
                   f'<span>{e(p.get("duracion", ""))}</span></button></li>')
    out.append(f"{I}</ol>")
    total = sum(_seg(p.get("duracion", "")) for p in pistas)
    enlaces = []
    if a.get("spotify"):
        enlaces.append(f'<a class="player__link player__link--spotify" href="{e(a["spotify"])}" rel="noopener" target="_blank">Spotify</a>')
    if a.get("bandcamp"):
        enlaces.append(f'<a class="player__link player__link--bandcamp" href="{e(a["bandcamp"])}" rel="noopener" target="_blank">Bandcamp</a>')
    pie = f"{len(pistas)} pistas, {total // 60}:{total % 60:02d}. Salió el {e(a.get('lanzamiento', ''))}."
    if enlaces:
        pie += " También está en " + " y ".join(enlaces) + "."
    out.append(f'{I}<p class="player__foot">{pie}</p>')
    datos = {"base": a.get("base", ""), "spotify": a.get("spotify", ""),
             "pistas": [{"t": p["titulo"], "f": p["archivo"], "d": p.get("duracion", "")} for p in pistas]}
    js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    out.append(f'{I}<script type="application/json" id="aero-data">{js}</script>')
    return "\n".join(out) + "\n"


def html_bandas(bandas: list[str], top: int, siempre: list[str] | None = None) -> str:
    I = "            "
    out = [f'{I}<ol class="top10">']
    out += [f"{I}  <li>{e(b)}</li>" for b in bandas[:top]]
    out.append(f"{I}</ol>")
    if len(bandas) > top:
        out.append(f'{I}<ol class="rest" start="{top + 1}">')
        out += [f"{I}  <li>{e(b)}</li>" for b in bandas[top:]]
        out.append(f"{I}</ol>")
    en_top = {b.lower() for b in bandas}
    resto = sorted((b for b in (siempre or []) if b.lower() not in en_top), key=str.lower)
    if resto:
        out.append(f'{I}<details class="gamelist bands-ever">')
        out.append(f'{I}  <summary>También de siempre <span class="gamelist__count">{len(resto)}</span></summary>')
        out.append(f'{I}  <ul class="bands-ever__list">')
        out += [f"{I}    <li>{e(b)}</li>" for b in resto]
        out += [f"{I}  </ul>", f"{I}</details>"]
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
    ap.add_argument("--now", help="ruta a Now.md")
    ap.add_argument("--canon", help="ruta a Canon.md")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "music.json").read_text(encoding="utf-8"))
    tablas = leer_tablas(Path(args.records or cfg["vault_records"]))
    bandas, siempre = leer_bandas(Path(args.bands or cfg["vault_bands"]))
    discos = tablas.get("Discos", [])
    ahora = []
    ruta_now = Path(args.now or cfg.get("vault_now", ""))
    if ruta_now.is_file():
        now, _ = leer_now(ruta_now)
        ahora = [f for f in now["activo"] + now["rotacion"] if f["medio"] == "music"]
    avisos = [f"{d.get('disco')} (⭐) no tiene Nota para la web" for d in discos if d["_fav"] and not d.get("nota")]
    titulos = {_clave(d.get("disco", "")) for d in discos}
    avisos += [f"'{f['obra']}' está en Now pero no tiene fila en Discos" for f in ahora if _clave(f["obra"]) not in titulos]
    avisos += revisar_registro(args.canon or cfg.get("vault_canon"), {"music": ("Records", [d.get("disco", "") for d in discos])})
    for a in avisos:
        print(f"  ⚠ {a}")
    pagina = (AQUI / cfg["pagina"]).resolve()

    print(f"Escuchando ahora: {len(ahora)}  ·  Discos: {len(discos)} ({sum(d['_fav'] for d in discos)} ⭐)  ·  Bandas: {len(bandas)}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "ahora", html_ahora(ahora, discos))
    doc = reemplazar(doc, "discos", html_discos(discos, cfg))
    doc = reemplazar(doc, "bandas", html_bandas(bandas, cfg.get("top", 10), siempre))
    if cfg.get("aero"):
        doc = reemplazar(doc, "aero", html_aero(cfg["aero"]))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
