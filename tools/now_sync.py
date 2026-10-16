"""Sincroniza la sección "Ahora mismo" del sitio con la nota Now.md del vault.

Lee "## Activo" y "## Rotación" de Now.md y reescribe en index.html lo que hay entre
los marcadores <!-- now:list -->, <!-- now:rotacion -->, <!-- now:ticker -->,
<!-- now:date --> y <!-- now:visitas -->. Formatos en tools/now.json; medios en tools/medios.json.

Además avisa (sin bloquear) si hay dos obras del mismo medio en Activo, si un medio no existe
o si algo de Activo lleva más de N días sin avanzar (lo recuerda en tools/now_state.json).

Uso (desde la carpeta del sitio):
    python tools/now_sync.py            # actualiza index.html
    python tools/now_sync.py --dry-run  # solo muestra lo que pondría
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
import urllib.request
from pathlib import Path

from now_lib import AQUI, cargar_json, leer_now

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SEP = " &nbsp;&nbsp;✦&nbsp;&nbsp; "
e = html.escape


def html_item(it: dict, I: str, compacto: bool = False) -> str:
    """Una fila tipo archivo de memory card: medio, título, ficha de avance y medidor (siempre presente)."""
    av = it["avance"]
    est = av["estado"]
    clase = "now__item" + (" now__item--compact" if compacto else "")
    if av["es_codigo"]:
        ficha = f'<code class="now__chip now__chip--{est} mono" title="{e(av["texto"])}">{e(av["codigo"])}</code>'
    else:
        ficha = f'<span class="now__chip now__chip--{est}">{e(av["codigo"])}</span>'
    pct = av["pct"] if est == "progreso" else (100 if est == "abierto" else 0)
    lineas = [
        f'{I}<li class="{clase}" style="--medio: var(--m-{e(it["medio"])}, var(--niebla))">',
        f'{I}  <span class="now__kind"><span class="now__swatch" aria-hidden="true"></span>{e(it["etiqueta"])}</span>',
        f'{I}  <span class="now__name">{e(it["obra"])}</span>',
        f'{I}  {ficha}',
    ]
    if it["sobre"] and not compacto:
        lineas.append(f'{I}  <span class="now__about">{e(it["sobre"])}</span>')
    lineas.append(f'{I}  <span class="meter meter--{est}" role="img" aria-label="{e(av["texto"])}">'
                  f'<span style="--p: {pct}%"></span></span>')
    lineas.append(f"{I}</li>")
    return "\n".join(lineas)


def html_lista(items: list[dict]) -> str:
    I = "              "
    if not items:
        return f'{I}<li class="now__empty">Nada en la consola por ahora.</li>\n'
    return "\n".join(html_item(it, I) for it in items) + "\n"


def html_rotacion(items: list[dict]) -> str:
    I = "            "
    if not items:
        return ""
    filas = "\n".join(html_item(it, I + "    ", compacto=True) for it in items)
    return (f'{I}<div class="now__rot">\n'
            f'{I}  <p class="now__rot-bar"><span class="now__rot-title">En rotación</span>'
            f'<span class="now__rot-note">Lo sigo, sin prisa</span></p>\n'
            f'{I}  <ul class="now now--compact">\n{filas}\n{I}  </ul>\n'
            f'{I}</div>\n')


def html_ticker(items: list[dict], medios_ok: list[str]) -> str:
    partes = [e(it["obra"]) for it in items if it["medio"] in medios_ok]
    linea = SEP.join(partes) + SEP if partes else "Sin juegos en la consola" + SEP
    span = f"        <span>{linea}</span>\n"
    return span + span  # dos copias para que el desplazamiento sea continuo


def fecha_hoy() -> str:
    hoy = dt.date.today()
    return f"Actualizado el {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}."


def visitas(sitio: str) -> int | None:
    """Lee las visitas del sitio en la API pública de Neocities. None si no hay red."""
    try:
        url = f"https://neocities.org/api/info?sitename={sitio}"
        with urllib.request.urlopen(url, timeout=6) as r:
            datos = json.loads(r.read().decode("utf-8"))
        return int(datos["info"]["views"])
    except Exception:
        return None


def html_contador(n: int) -> str:
    return "".join(f"<span>{d}</span>" for d in f"{n:06d}")


def reemplazar(doc: str, nombre: str, nuevo: str, obligatorio: bool = True) -> str:
    import re
    patron = re.compile(
        rf"(<!-- now:{nombre}:start -->\n?)(.*?)([ \t]*<!-- now:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        if obligatorio:
            sys.exit(f"Falta el marcador now:{nombre} en index.html")
        print(f"(no hay marcador now:{nombre} en index.html; se omite)")
        return doc
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def revisar_avance(todos: list[dict], cfg: dict, escribir: bool) -> list[str]:
    """Recuerda cuándo cambió por última vez 'Voy en' de cada obra y avisa si Activo se estancó."""
    ruta = AQUI / cfg.get("estado", "now_state.json")
    try:
        estado = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    hoy = dt.date.today()
    nuevo, avisos = {}, []
    limite = int(cfg.get("dias_sin_avance", 21))
    for it in todos:
        prev = estado.get(it["obra"], {})
        desde = prev.get("desde") if prev.get("voy") == it["voy"] else hoy.isoformat()
        nuevo[it["obra"]] = {"voy": it["voy"], "desde": desde, "inicio": prev.get("inicio", hoy.isoformat())}
        dias = (hoy - dt.date.fromisoformat(desde)).days
        if it["seccion"] == "activo" and dias > limite and it["avance"]["estado"] == "progreso":
            avisos.append(f"{it['obra']} lleva {dias} días sin avanzar: ¿pasarla a Rotación?")
    if escribir:
        ruta.write_text(json.dumps(nuevo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return avisos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="no escribe, solo muestra")
    ap.add_argument("--now", help="ruta a Now.md (si no, la de now.json)")
    args = ap.parse_args()

    cfg = cargar_json("now.json")
    now, avisos = leer_now(Path(args.now or cfg["vault_now"]), cfg)
    activo, rotacion = now["activo"], now["rotacion"]
    index = (AQUI / cfg["index"]).resolve()

    for titulo, lista in (("Activo", activo), ("Rotación", rotacion)):
        print(f"{titulo}:")
        for it in lista:
            av = it["avance"]
            extra = f"  [{av['pct']}%]" if av["pct"] is not None else ""
            print(f"  {it['etiqueta']:<9} {it['obra']:<28} {av['codigo']}{extra}")
    avisos += revisar_avance(activo + rotacion, cfg, escribir=not args.dry_run)
    for a in avisos:
        print(f"  ⚠ {a}")

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = index.read_text(encoding="utf-8")
    doc = reemplazar(doc, "list", html_lista(activo))
    doc = reemplazar(doc, "rotacion", html_rotacion(rotacion if cfg.get("rotacion_en_web", True) else []),
                     obligatorio=False)
    doc = reemplazar(doc, "ticker", html_ticker(activo, cfg.get("ticker_medios", [])))
    doc = reemplazar(doc, "date", fecha_hoy())
    if cfg.get("neocities_sitio") and "<!-- now:visitas:start -->" in doc:
        n = visitas(cfg["neocities_sitio"])
        if n is None:
            print("(sin conexión con Neocities: el contador se queda igual)")
        else:
            doc = reemplazar(doc, "visitas", html_contador(n))
            print(f"Visitas: {n}")
    index.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {index.name} actualizado ({len(activo)} activos, {len(rotacion)} en rotación).")


if __name__ == "__main__":
    main()
