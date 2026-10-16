"""Genera la página Cine, series y cómics desde el vault.

- Movies.md (⭐ = boleto), Series.md (⭐ = guía de canales), Comics.md (⭐ = cómic embolsado).
- Now.md: "En cartelera" (filas Movie, Series y Comic de Activo y Rotación; las de Siguiente como "próxima función").

Reescribe en cine.html lo que hay entre los marcadores <!-- cine:... -->.

Uso (desde la carpeta del sitio):
    python tools/cine_sync.py            # actualiza cine.html
    python tools/cine_sync.py --dry-run  # solo muestra el resumen
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

from now_lib import leer_now

AQUI = Path(__file__).resolve().parent
e = html.escape
TINTAS = ["#c8302a", "#1f5fb0", "#2f8f4e", "#7b3fa8", "#d6802f", "#0e7d6e"]


def celdas(fila: str) -> list[str]:
    fila = fila.strip().strip("|").replace("\\|", "\0")
    return [c.strip().replace("\0", "|") for c in fila.split("|")]


def leer_tablas(ruta: Path) -> dict[str, list[dict]]:
    tablas: dict[str, list[dict]] = {}
    seccion, encabezado = None, None
    if not ruta.exists():
        print(f"(no encontré {ruta}, la sección queda vacía)")
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
            fila["_t"] = c[0]
            fila["_fav"] = "⭐" in "".join(c)
            tablas[seccion].append(fila)
    return tablas


def anio(f: dict) -> str:
    m = re.match(r"^(\d{4})", f.get("año", ""))
    return m.group(1) if m else ""


def orden(f: dict):
    return (anio(f) or "9999", f["_t"].lower())


def colores(t: str, cfg: dict) -> list[str]:
    c = cfg.get("colores", {}).get(t)
    if c:
        return [x.strip() for x in c.split(",")]
    return [TINTAS[int(hashlib.md5(t.encode()).hexdigest(), 16) % len(TINTAS)]]


def limpiar(s: str) -> str:
    m = re.fullmatch(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", s.strip())
    return (m.group(2) or m.group(1)).strip() if m else s.strip()


# ---------- bloques ----------

def con_nota(cfg: dict) -> bool:
    """Las calificaciones viven en el vault; en la web solo salen si "mostrar_calificacion" es true."""
    return bool(cfg.get("mostrar_calificacion", False))


def boletos(pelis: list[dict], cfg: dict) -> str:
    I = "              "
    favs = sorted([f for f in pelis if f["_fav"]], key=orden)
    if not favs:
        return f'{I}<li class="empty-note">Todavía no hay boletos.</li>\n'
    out = []
    for f in favs:
        t = f["_t"]
        out.append(f'{I}<li class="ticket" style="--ink:{e(colores(t, cfg)[0])}">')
        out.append(f'{I}  <div class="ticket__main">')
        out.append(f'{I}    <span class="ticket__admit">Admite uno</span>')
        out.append(f'{I}    <span class="ticket__title">{e(t)}</span>')
        if f.get("nota"):
            out.append(f'{I}    <span class="ticket__note">{e(f["nota"])}</span>')
        out.append(f"{I}  </div>")
        out.append(f'{I}  <div class="ticket__stub"><span class="ticket__year">{anio(f) or "—"}</span>'
                   + (f'<span class="ticket__score">{e(f["calificación"])}</span>' if con_nota(cfg) and f.get("calificación") else "")
                   + "</div>")
        out.append(f"{I}</li>")
    return "\n".join(out) + "\n"


def canales(series: list[dict], cfg: dict) -> str:
    I = "              "
    favs = sorted([f for f in series if f["_fav"]], key=orden)
    if not favs:
        return f'{I}<li class="empty-note">Sin programación.</li>\n'
    out = []
    for n, f in enumerate(favs, start=1):
        meta = ", ".join(x for x in [f.get("calificación", "") if con_nota(cfg) else "", f.get("nota", "")] if x)
        out.append(f'{I}<li><span class="guide__ch">CH {n:02d}</span>'
                   f'<span class="guide__show">{e(f["_t"])}<small>{anio(f)}</small></span>'
                   f'<span class="guide__meta">{e(meta)}</span></li>')
    return "\n".join(out) + "\n"


def comics(lista: list[dict], cfg: dict) -> str:
    I = "              "
    favs = sorted([f for f in lista if f["_fav"]], key=orden)
    if not favs:
        return f'{I}<li class="empty-note">La caja está vacía.</li>\n'
    out = []
    for f in favs:
        t = f["_t"]
        c = colores(t, cfg)
        estilo = f"--cov:{c[0]}" + (f";--cov2:{c[1]}" if len(c) > 1 else "")
        meta = ", ".join(x for x in [f.get("autor", ""), anio(f)] if x)
        out.append(f'{I}<li class="comic" style="{e(estilo)}">')
        out.append(f'{I}  <span class="comic__bag" aria-hidden="true"></span>')
        out.append(f'{I}  <span class="comic__name">{e(t)}</span>')
        if meta:
            out.append(f'{I}  <span class="comic__meta">{e(meta)}</span>')
        if f.get("nota"):
            out.append(f'{I}  <span class="comic__note">{e(f["nota"])}</span>')
        out.append(f"{I}</li>")
    return "\n".join(out) + "\n"


def bloque_lista(titulo: str, filas: list[dict], abierta: bool, con_anio: bool, I: str, notas: bool = False) -> list[str]:
    if not filas:
        return []
    filas = sorted(filas, key=orden if con_anio else (lambda f: f["_t"].lower()))
    out = [f'{I}<details class="gamelist"{" open" if abierta else ""}>',
           f'{I}  <summary>{titulo} <span class="gamelist__count">{len(filas)}</span></summary>']
    clase = "gamelist__items" if con_anio else "gamelist__items gamelist__items--plain"
    out.append(f'{I}  <ul class="{clase}">')
    for f in filas:
        if con_anio:
            score = f' <span class="gl__score">{e(f["calificación"])}</span>' if notas and f.get("calificación") else " <span></span>"
            fav = ' <span class="gl__fav" title="Favorito">⭐</span>' if f["_fav"] else ""
            out.append(f'{I}    <li><span class="gl__year">{anio(f) or "—"}</span> <span class="gl__name">{e(f["_t"])}</span>{score}{fav}</li>')
        else:
            out.append(f'{I}    <li><span class="gl__name">{e(f["_t"])}</span></li>')
    out += [f"{I}  </ul>", f"{I}</details>"]
    return out


def lista(m: dict, s: dict, c: dict, cfg: dict) -> str:
    I = "            "
    n = con_nota(cfg)
    out = []
    out += bloque_lista("Películas", m.get("Vistas", []), True, True, I, n)
    out += bloque_lista("Series", s.get("Vistas", []), False, True, I, n)
    out += bloque_lista("Cómics", c.get("Leídos", []), False, True, I, n)
    por_ver = [dict(f, _t=f["_t"]) for f in m.get("Por ver", []) + s.get("Por ver", [])]
    out += bloque_lista("Por ver", por_ver, False, False, I)
    out += bloque_lista("Por leer", c.get("Por leer", []), False, False, I)
    return ("\n".join(out) if out else f'{I}<p class="empty-note">Lista en construcción.</p>') + "\n"


def cartelera(now: dict, cfg: dict) -> str:
    I = "              "
    medios = cfg.get("cartelera_medios", ["movie", "series", "comic"])
    out = []
    for f in now["activo"] + now["rotacion"]:
        if f["medio"] not in medios:
            continue
        av = f["avance"]
        if av["nuevo"]:
            detalle = f"{e(f['etiqueta'])}, por empezar"
        elif av["es_codigo"]:
            detalle = f'{e(f["etiqueta"])} · <code class="mono" title="{e(av["texto"])}">{e(av["codigo"])}</code>'
        else:
            detalle = e(f["etiqueta"]) + (f", {e(av['codigo'])}" if av["codigo"] else "")
        out += [f"{I}<dt>{e(f['obra'])}</dt>", f"{I}<dd>{detalle}</dd>"]
    for f in now["siguiente"]:
        if f["medio"] in medios:
            out += [f"{I}<dt>{e(f['obra'])}</dt>", f"{I}<dd>{e(f['etiqueta'])}, próxima función</dd>"]
    if not out:
        return f"{I}<dt>Sin función</dt>\n{I}<dd>Nada en cartelera por ahora.</dd>\n"
    return "\n".join(out) + "\n"


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(rf"(<!-- cine:{nombre}:start -->\n?)(.*?)([ \t]*<!-- cine:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        sys.exit(f"Falta el marcador cine:{nombre} en la página")
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    for k in ("movies", "series", "comics", "now"):
        ap.add_argument(f"--{k}")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "cine.json").read_text(encoding="utf-8"))
    m = leer_tablas(Path(args.movies or cfg["vault_movies"]))
    s = leer_tablas(Path(args.series or cfg["vault_series"]))
    c = leer_tablas(Path(args.comics or cfg["vault_comics"]))
    now, _ = leer_now(Path(args.now or cfg["vault_now"]))
    pagina = (AQUI / cfg["pagina"]).resolve()

    def cuenta(lst):
        return f"{len(lst)} ({sum(f['_fav'] for f in lst)} ⭐)"
    print(f"Películas: {cuenta(m.get('Vistas', []))}  ·  Series: {cuenta(s.get('Vistas', []))}  ·  Cómics: {cuenta(c.get('Leídos', []))}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "boletos", boletos(m.get("Vistas", []), cfg))
    doc = reemplazar(doc, "canales", canales(s.get("Vistas", []), cfg))
    doc = reemplazar(doc, "comics", comics(c.get("Leídos", []), cfg))
    doc = reemplazar(doc, "lista", lista(m, s, c, cfg))
    doc = reemplazar(doc, "cartelera", cartelera(now, cfg))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
