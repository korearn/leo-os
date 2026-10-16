"""Sincroniza la sección "Ahora mismo" del sitio con la nota Now.md del vault.

Lee la tabla de "## Activo" en Now.md y reescribe en index.html lo que hay entre
los marcadores <!-- now:list:start/end -->, <!-- now:ticker:start/end --> y
<!-- now:date:start/end -->. Las plantillas de texto viven en tools/now.json.

Uso (desde la carpeta del sitio):
    python tools/now_sync.py            # actualiza index.html
    python tools/now_sync.py --dry-run  # solo muestra lo que pondría
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SEP = " &nbsp;&nbsp;✦&nbsp;&nbsp; "


def sin_selector(s: str) -> str:
    """Quita el selector de variación de los emoji (🎞️ y 🎞 cuentan igual)."""
    return s.replace("️", "").strip()


def limpiar_obra(s: str) -> str:
    """[[Kuuchuu Buranko]] -> Kuuchuu Buranko ; [[nota|Alias]] -> Alias."""
    s = s.strip()
    m = re.fullmatch(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", s)
    if m:
        return (m.group(2) or m.group(1)).strip()
    return s


def leer_tabla(now_md: Path) -> list[dict]:
    texto = now_md.read_text(encoding="utf-8")
    m = re.search(r"^## Activo\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        sys.exit("No encontré la sección '## Activo' en Now.md")

    filas = [l for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(filas) < 3:
        sys.exit("La tabla de '## Activo' está vacía")

    items = []
    for fila in filas[2:]:  # salta encabezado y separador
        celdas = [c.strip() for c in fila.strip().strip("|").split("|")]
        if len(celdas) < 3 or not celdas[1]:
            continue  # filas vacías o sin obra
        items.append({
            "medio": sin_selector(celdas[0]),
            "obra": limpiar_obra(celdas[1]),
            "voy": celdas[2],
        })
    return items


def rellenar(plantilla: str, obra: str, voy: str, grupos: tuple) -> str:
    out = plantilla.replace("{obra}", obra).replace("{voy}", voy)
    for i, g in enumerate(grupos, start=1):
        out = out.replace("{" + str(i) + "}", g or "")
    return out


def formatear(item: dict, cfg: dict) -> dict:
    tipos = {sin_selector(k): v for k, v in cfg["tipos"].items()}
    tipo = tipos.get(item["medio"], item["medio"])
    obra, voy = item["obra"], item["voy"]

    for regla in cfg["formatos"]:
        m = re.match(regla["patron"], voy, re.I)
        if not m:
            continue
        g = m.groups()
        barra = None
        if "barra" in regla:
            num, den = (int(g[i - 1]) for i in regla["barra"])
            if den > 0:
                barra = (num, den, round(min(num / den, 1) * 100))
        return {
            "tipo": tipo, "obra": obra,
            "texto": rellenar(regla["texto"], obra, voy, g),
            "ticker": rellenar(regla.get("ticker", "{obra}"), obra, voy, g),
            "barra": barra,
        }

    d = cfg["por_defecto"]
    return {
        "tipo": tipo, "obra": obra,
        "texto": rellenar(d["texto"], obra, voy, ()),
        "ticker": rellenar(d["ticker"], obra, voy, ()),
        "barra": None,
    }


def html_lista(items: list[dict]) -> str:
    e = html.escape
    bloques = []
    for it in items:
        lineas = [
            '              <li class="now__item">',
            f'                <span class="now__kind">{e(it["tipo"])}</span>',
            f'                <span class="now__name">{e(it["obra"])}</span>',
            f'                <span class="now__where">{e(it["texto"])}</span>',
        ]
        if it["barra"]:
            num, den, pct = it["barra"]
            lineas.append(
                f'                <span class="bar" role="img" aria-label="{num} de {den}">'
                f'<span style="--p: {pct}%"></span></span>'
            )
        lineas.append("              </li>")
        bloques.append("\n".join(lineas))
    return "\n".join(bloques) + "\n"


def html_ticker(items: list[dict], tipos_ok: list[str]) -> str:
    partes = [html.escape(it["ticker"]) for it in items if it["tipo"] in tipos_ok]
    linea = SEP.join(partes) + SEP
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


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(
        rf"(<!-- now:{nombre}:start -->\n?)(.*?)([ \t]*<!-- now:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        sys.exit(f"Falta el marcador now:{nombre} en index.html")
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="no escribe, solo muestra")
    ap.add_argument("--now", help="ruta a Now.md (si no, la de now.json)")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "now.json").read_text(encoding="utf-8"))
    now_md = Path(args.now or cfg["vault_now"])
    index = (AQUI / cfg["index"]).resolve()

    items = [formatear(i, cfg) for i in leer_tabla(now_md)]

    for it in items:
        extra = f"  [{it['barra'][2]}%]" if it["barra"] else ""
        print(f"  {it['tipo']:<9} {it['obra']:<28} {it['texto']}{extra}")

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = index.read_text(encoding="utf-8")
    doc = reemplazar(doc, "list", html_lista(items))
    doc = reemplazar(doc, "ticker", html_ticker(items, cfg.get("ticker_tipos", [])))
    doc = reemplazar(doc, "date", fecha_hoy())
    if cfg.get("neocities_sitio") and "<!-- now:visitas:start -->" in doc:
        n = visitas(cfg["neocities_sitio"])
        if n is None:
            print("(sin conexión con Neocities: el contador se queda igual)")
        else:
            doc = reemplazar(doc, "visitas", html_contador(n))
            print(f"Visitas: {n}")
    index.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {index.name} actualizado con {len(items)} elementos.")


if __name__ == "__main__":
    main()
