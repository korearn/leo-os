"""Genera la página Anime y manga desde el vault.

- Now.md (filas Anime de Activo y Rotación): la tele de "Viendo ahora".
- Anime.md: Vistos (⭐ = cinta VHS) y Por ver.
- Manga.md: Leídos (⭐ = tomo en la repisa) y Por leer. Lo que leo ahora sale de Now.md (filas Manga).
- "Mi nota" = calificación (solo vault); "en curso" oculta la ficha de las vistas. Canon.md: avisos del Registro.

Reescribe en anime.html lo que hay entre los marcadores <!-- anime:... --> y <!-- manga:... -->.

Uso (desde la carpeta del sitio):
    python tools/anime_sync.py            # actualiza anime.html
    python tools/anime_sync.py --dry-run  # solo muestra el resumen
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

from now_lib import leer_now as leer_now_md, revisar_registro

AQUI = Path(__file__).resolve().parent
e = html.escape
PALETA = ["#1f5fb0", "#c8302a", "#2f8f4e", "#7b3fa8", "#c2862a", "#0e7d6e", "#b83a6a", "#3a3f9a"]


def celdas(fila: str) -> list[str]:
    fila = fila.strip().strip("|").replace("\\|", "\0")
    return [c.strip().replace("\0", "|") for c in fila.split("|")]


def leer_tablas(ruta: Path) -> dict[str, list[dict]]:
    tablas: dict[str, list[dict]] = {}
    seccion, encabezado = None, None
    if not ruta.exists():
        return tablas
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
            fila["_en_curso"] = fila.get("mi nota", "").strip().lower() == "en curso"
            tablas[seccion].append(fila)
    return tablas


def limpiar(s: str) -> str:
    m = re.fullmatch(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", s.strip())
    return (m.group(2) or m.group(1)).strip() if m else s.strip()


def color(titulo: str, cfg: dict) -> str:
    return cfg.get("colores", {}).get(titulo) or PALETA[int(hashlib.md5(titulo.encode()).hexdigest(), 16) % len(PALETA)]


def anio(f: dict) -> str:
    m = re.match(r"^(\d{4})", f.get("año", ""))
    return m.group(1) if m else ""


# ---------- bloques ----------

def html_tv(viendo: list[dict]) -> str:
    I = "              "
    if not viendo:
        return f'{I}<li class="tv__empty">Sin señal. No estoy viendo nada ahora.</li>\n'
    out = []
    for n, f in enumerate(viendo, start=1):
        av = f["avance"]
        if av["regla"] in ("episodio", "temporada + episodio"):
            m = re.search(r"E(\d+)(?:/(\d+))?$", av["codigo"])
            ep = f"EP {int(m.group(1)):02d}" + (f"/{int(m.group(2)):02d}" if m.group(2) else "")
            if av["codigo"].startswith("S"):
                ep = av["codigo"].split("E")[0] + " " + ep
        else:
            ep = av["codigo"]
        out.append(f'{I}<li class="tv__item">')
        out.append(f'{I}  <span class="tv__ch">CH {n:02d}</span>')
        out.append(f'{I}  <span class="tv__name">{e(f["obra"])}</span>')
        out.append(f'{I}  <span class="tv__ep" title="{e(av["texto"])}">{e(ep)}</span>')
        if av["pct"] is not None:
            out.append(f'{I}  <span class="tv__bar" role="img" aria-label="{e(av["texto"])}"><span style="--p: {av["pct"]}%"></span></span>')
        out.append(f"{I}</li>")
    return "\n".join(out) + "\n"


def html_vhs(vistos: list[dict], cfg: dict) -> str:
    I = "              "
    favs = sorted([f for f in vistos if f["_fav"]], key=lambda f: (anio(f) or "9999", f.get("anime", "").lower()))
    if not favs:
        return f'{I}<li class="empty-note">Todavía no marco favoritos.</li>\n'
    out = []
    for f in favs:
        t = f.get("anime", "")
        out.append(f'{I}<li class="tape" style="--tape:{e(color(t, cfg))}">')
        out.append(f'{I}  <span class="tape__label">{e(t)} <span class="tape__year">{anio(f)}</span></span>')
        nota = f.get("nota", "")
        out.append(f'{I}  <span class="tape__note">{e(nota)}</span>' if nota and "?" not in nota else f'{I}  <span class="tape__note"></span>')
        out.append(f"{I}</li>")
    return "\n".join(out) + "\n"


def lista(titulo: str, filas: list[dict], clave: str, abierta: bool, I: str, con_anio: bool = True) -> list[str]:
    filas = [f for f in filas if f.get(clave)]
    if not filas:
        return []
    filas.sort(key=lambda f: ((anio(f) or "9999") if con_anio else "", f.get(clave, "").lower()))
    out = [f'{I}<details class="gamelist"{" open" if abierta else ""}>',
           f'{I}  <summary>{titulo} <span class="gamelist__count">{len(filas)}</span></summary>']
    if con_anio:
        out.append(f'{I}  <ul class="gamelist__items">')
        for f in filas:
            fav = ' <span class="gl__fav" title="Favorito">⭐</span>' if f["_fav"] else ""
            out.append(f'{I}    <li><span class="gl__year">{anio(f) or "—"}</span> <span class="gl__name">{e(f[clave])}</span>{fav}</li>')
    else:
        out.append(f'{I}  <ul class="gamelist__items gamelist__items--plain">')
        for f in filas:
            out.append(f'{I}    <li><span class="gl__name">{e(f[clave])}</span></li>')
    out += [f"{I}  </ul>", f"{I}</details>"]
    return out


def html_lista_anime(anime: dict) -> str:
    I = "            "
    out = lista("Vistos", anime.get("Vistos", []), "anime", True, I)
    out += lista("Por ver", anime.get("Por ver", []), "anime", False, I, con_anio=False)
    return ("\n".join(out) if out else f'{I}<p class="empty-note">Lista en construcción.</p>') + "\n"


def html_leyendo(leyendo: list[dict]) -> str:
    """Manga que leo ahora: filas `Manga` de Now.md (Activo y Rotación)."""
    I = "              "
    if not leyendo:
        return f"{I}<dt>Nada por ahora</dt>\n{I}<dd>Pronto vuelvo a abrir un tomo.</dd>\n"
    out = []
    for f in leyendo:
        av = f["avance"]
        detalle = av["texto"] if av["codigo"] and not av["nuevo"] else ("Por empezar" if av["nuevo"] else "")
        out += [f"{I}<dt>{e(f['obra'])}</dt>", f"{I}<dd>{e(detalle)}</dd>"]
    return "\n".join(out) + "\n"


def html_tomos(manga: dict, cfg: dict) -> str:
    I = "              "
    favs = [f for f in manga.get("Leídos", []) if f["_fav"] and f.get("manga")]
    if not favs:
        return f'{I}<li class="empty-note">La repisa espera su primer tomo.</li>\n'
    out = []
    for f in sorted(favs, key=lambda f: (anio(f) or "9999", f["manga"].lower())):
        vol = f.get("tomos", "")
        out.append(f'{I}<li class="tomo" style="--spine:{e(color(f["manga"], cfg))}" title="{e(f["manga"])}">')
        out.append(f'{I}  <span class="tomo__title">{e(f["manga"])}</span>')
        out.append(f'{I}  <span class="tomo__vol">{e(vol)}</span>' if vol else f"{I}  <span></span>")
        out.append(f"{I}</li>")
    return "\n".join(out) + "\n"


def html_lista_manga(manga: dict) -> str:
    I = "            "
    out = lista("Leídos", manga.get("Leídos", []), "manga", True, I)
    out += lista("Por leer", manga.get("Por leer", []), "manga", False, I, con_anio=False)
    return ("\n".join(out) if out else f'{I}<p class="empty-note">Lista en construcción.</p>') + "\n"


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(rf"(<!-- {nombre}:start -->\n?)(.*?)([ \t]*<!-- {nombre}:end -->)", re.S)
    if not patron.search(doc):
        sys.exit(f"Falta el marcador {nombre} en la página")
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--anime"); ap.add_argument("--manga"); ap.add_argument("--now"); ap.add_argument("--canon")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "anime.json").read_text(encoding="utf-8"))
    anime = leer_tablas(Path(args.anime or cfg["vault_anime"]))
    manga = leer_tablas(Path(args.manga or cfg["vault_manga"]))
    now, avisos = leer_now_md(Path(args.now or cfg["vault_now"]))
    pagina = (AQUI / cfg["pagina"]).resolve()

    viendo = [f for f in now["activo"] + now["rotacion"] if f["medio"] == cfg.get("medio_tv", "anime")]
    leyendo = [f for f in now["activo"] + now["rotacion"] if f["medio"] == "manga"]
    # Fichas "en curso": existen en el catálogo pero no se muestran como vistas/leídas.
    anime["Vistos"] = [f for f in anime.get("Vistos", []) if not f["_en_curso"]]
    manga["Leídos"] = [f for f in manga.get("Leídos", []) if not f["_en_curso"]]
    for nombre, filas, clave in (("Anime", anime["Vistos"], "anime"), ("Manga", manga["Leídos"], "manga")):
        for f in filas:
            if f.get(clave) and not f.get("nota"):
                avisos.append(f"{f[clave]} ({nombre}) no tiene Nota para la web")
    todos_a = [f.get("anime", "") for f in leer_tablas(Path(args.anime or cfg["vault_anime"])).get("Vistos", [])]
    todos_m = [f.get("manga", "") for f in leer_tablas(Path(args.manga or cfg["vault_manga"])).get("Leídos", [])]
    avisos += revisar_registro(args.canon or cfg.get("vault_canon"),
                               {"anime": ("Anime", todos_a), "manga": ("Manga", todos_m)})
    for a in avisos:
        print(f"  ⚠ {a}")
    vistos = [f for f in anime.get("Vistos", []) if f.get("anime")]
    print(f"Viendo (desde Now): {len(viendo)}  ·  Vistos: {len(vistos)} ({sum(f['_fav'] for f in vistos)} ⭐)  ·  "
          f"Por ver: {len([f for f in anime.get('Por ver', []) if f.get('anime')])}")
    print(f"Manga: leyendo {len(leyendo)} (desde Now)  ·  "
          f"leídos {len([f for f in manga.get('Leídos', []) if f.get('manga')])}  ·  "
          f"por leer {len([f for f in manga.get('Por leer', []) if f.get('manga')])}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "anime:tv", html_tv(viendo))
    doc = reemplazar(doc, "anime:vhs", html_vhs(anime.get("Vistos", []), cfg))
    doc = reemplazar(doc, "anime:lista", html_lista_anime(anime))
    doc = reemplazar(doc, "manga:leyendo", html_leyendo(leyendo))
    doc = reemplazar(doc, "manga:tomos", html_tomos(manga, cfg))
    doc = reemplazar(doc, "manga:lista", html_lista_manga(manga))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
