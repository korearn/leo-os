"""Publica el Diario: lee las notas de la carpeta Posts del vault y reescribe diario.html.

Una nota = una entrada. Solo salen las que tienen `publicar: true` en el frontmatter:

    ---
    fecha: 2026-11-04
    titulo: Rediseño Y2K
    publicar: true
    animo: con sueño          (opcional, sale como "Ánimo:")
    escuchando: Loveless      (opcional, sale como "Escuchando:")
    etiquetas: [sitio, y2k]   (opcional)
    entry: 3                  (opcional; si no, se numeran solas por fecha: la más vieja es Entry #1)
    ---
    El texto en Markdown sencillo: párrafos, **negritas**, *cursivas*, [enlaces](https://...),
    listas con "- ", subtítulos con "## " e imágenes ![texto](img/diario/foto.webp).
    Los [[enlaces de Obsidian]] salen como texto normal (el vault no se publica).

Cada entrada sale como "Entry #N" (como los videos de Marble Hornets) y el título va debajo.
Los archivos que empiezan con "_" se ignoran (plantillas, borradores aparte).
También pone la entrada más reciente en la portada (marcador diario:ultima de index.html).

Uso (desde la carpeta del sitio):
    python tools/diario_sync.py            # actualiza diario.html e index.html
    python tools/diario_sync.py --dry-run  # solo muestra qué entradas saldrían
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from now_lib import resolver  # noqa: E402

e = html.escape
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def slug(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "entrada"


def frontmatter(texto: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", texto, re.S)
    if not m:
        return {}, texto
    datos, ultima = {}, None
    for linea in m.group(1).splitlines():
        lista = re.match(r"^\s+-\s+(.+)$", linea)          # listas de YAML (como las guarda Obsidian)
        if lista and ultima:
            if not isinstance(datos.get(ultima), list):
                datos[ultima] = []
            datos[ultima].append(lista.group(1).strip().strip("\"'"))
            continue
        if ":" not in linea or linea.strip().startswith("#"):
            continue
        ultima = linea.split(":", 1)[0].strip().lower()
        k, v = linea.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("true", "false"):
            v = v.lower() == "true"
        else:
            v = v.strip("\"'")
        datos[k.strip().lower()] = v
    return datos, m.group(2)


def en_linea(t: str) -> str:
    t = e(t, quote=False)
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)          # [[nota|alias]] -> alias
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)                      # [[nota]] -> nota
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def markdown(md: str) -> str:
    out, parrafo, lista = [], [], []

    def cerrar():
        if parrafo:
            out.append("<p>" + en_linea(" ".join(parrafo)) + "</p>")
            parrafo.clear()
        if lista:
            out.append("<ul>" + "".join(f"<li>{en_linea(x)}</li>" for x in lista) + "</ul>")
            lista.clear()

    for linea in md.splitlines():
        s = linea.strip()
        if not s:
            cerrar()
        elif s.startswith("#"):
            cerrar()
            nivel = min(4, max(3, len(s) - len(s.lstrip("#")) + 1))
            out.append(f"<h{nivel}>{en_linea(s.lstrip('#').strip())}</h{nivel}>")
        elif re.match(r"^[-*] ", s):
            if parrafo:
                cerrar()
            lista.append(s[2:])
        else:
            if lista:
                cerrar()
            parrafo.append(s)
    cerrar()
    return "\n".join(out)


def fecha_larga(d: dt.date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def leer_entradas(carpeta: Path) -> tuple[list[dict], list[str]]:
    entradas, avisos = [], []
    if not carpeta or not carpeta.exists():
        return [], [f"No encontré la carpeta del diario: {carpeta}"]
    for ruta in sorted(carpeta.rglob("*.md")):
        if ruta.name.startswith("_"):
            continue
        datos, cuerpo = frontmatter(ruta.read_text(encoding="utf-8"))
        if datos.get("publicar") is not True:
            continue
        try:
            fecha = dt.date.fromisoformat(str(datos.get("fecha", ""))[:10])
        except ValueError:
            avisos.append(f"{ruta.name}: falta 'fecha' (AAAA-MM-DD); no se publica")
            continue
        titulo = str(datos.get("titulo") or ruta.stem)
        etiquetas = datos.get("etiquetas") or []
        if isinstance(etiquetas, str):
            etiquetas = [x.strip() for x in etiquetas.split(",") if x.strip()]
        entradas.append({"fecha": fecha, "titulo": titulo, "cuerpo": markdown(cuerpo),
                         "animo": datos.get("animo", ""), "escuchando": datos.get("escuchando", ""),
                         "etiquetas": etiquetas, "fijo": str(datos.get("entry", "")).strip().lstrip("#")})
    entradas.sort(key=lambda x: (x["fecha"], x["titulo"]))
    usados = {int(x["fijo"]) for x in entradas if x["fijo"].isdigit()}
    n = 0
    for x in entradas:
        if x["fijo"].isdigit():
            x["n"] = int(x["fijo"])
        else:
            n += 1
            while n in usados:
                n += 1
            x["n"] = n
        x["id"] = f"entry-{x['n']}"
    entradas.sort(key=lambda x: (x["fecha"], x["n"]), reverse=True)
    return entradas, avisos


def html_entradas(entradas: list[dict]) -> str:
    I = "          "
    if not entradas:
        return f'{I}<p class="diario__vacio">Todavía no hay entradas. Vuelve pronto.</p>\n'
    out = []
    for x in entradas:
        out.append(f'{I}<article class="entrada" id="{x["id"]}">')
        out.append(f'{I}  <p class="entrada__entry"><a href="#{x["id"]}">Entry #{x["n"]}</a></p>')
        out.append(f'{I}  <p class="entrada__fecha"><time datetime="{x["fecha"].isoformat()}">{fecha_larga(x["fecha"])}</time></p>')
        out.append(f'{I}  <h2 class="entrada__titulo">{e(x["titulo"])}</h2>')
        out.append(f'{I}  <div class="entrada__cuerpo">\n{x["cuerpo"]}\n{I}  </div>')
        pie = []
        if x["animo"]:
            pie.append(f'<span><b>Ánimo:</b> {e(x["animo"])}</span>')
        if x["escuchando"]:
            pie.append(f'<span><b>Escuchando:</b> {e(x["escuchando"])}</span>')
        if x["etiquetas"]:
            pie.append('<span><b>Etiquetas:</b> ' + ", ".join(
                f'<a href="#tag-{slug(t)}">{e(t)}</a>' for t in x["etiquetas"]) + "</span>")
        pie.append('<span><a href="libro.html">Comentar en el libro de visitas</a></span>')
        out.append(f'{I}  <p class="entrada__pie">' + " · ".join(pie) + "</p>")
        out.append(f"{I}</article>")
    return "\n".join(out) + "\n"


def html_archivo(entradas: list[dict]) -> str:
    I = "            "
    if not entradas:
        return f"{I}<p class=\"window__note\">Vacío por ahora.</p>\n"
    out = []
    anios = {}
    for x in entradas:
        anios.setdefault(x["fecha"].year, {}).setdefault(x["fecha"].month, []).append(x)
    for i, (anio, meses) in enumerate(sorted(anios.items(), reverse=True)):
        total = sum(len(v) for v in meses.values())
        out.append(f'{I}<details class="archivo"{" open" if i == 0 else ""}><summary>{anio} ({total})</summary>')
        for mes, lista in sorted(meses.items(), reverse=True):
            out.append(f'{I}  <p class="archivo__mes">{MESES[mes - 1]} ({len(lista)})</p><ul>')
            out += [f'{I}    <li><a href="#{x["id"]}">Entry #{x["n"]}</a> · {e(x["titulo"])}</li>' for x in lista]
            out.append(f"{I}  </ul>")
        out.append(f"{I}</details>")
    tags = {}
    for x in entradas:
        for t in x["etiquetas"]:
            tags[t] = tags.get(t, 0) + 1
    if tags:
        out.append(f'{I}<p class="archivo__mes">etiquetas</p><p class="etiquetas">' + " ".join(
            f'<span id="tag-{slug(t)}">{e(t)} ({n})</span>' for t, n in sorted(tags.items())) + "</p>")
    return "\n".join(out) + "\n"


def html_ultima(entradas: list[dict]) -> str:
    if not entradas:
        return '<p class="window__note">Todavía no hay entradas.</p>'
    x = entradas[0]
    resumen = re.sub(r"<[^>]+>", "", x["cuerpo"]).strip()
    if len(resumen) > 140:
        resumen = resumen[:140].rsplit(" ", 1)[0] + "…"
    return (f'<p class="ultima__fecha">{x["fecha"].strftime("%d/%m/%Y")}</p>'
            f'<p class="ultima__titulo"><a href="diario.html#{x["id"]}">Entry #{x["n"]}</a> · {e(x["titulo"])}</p>'
            f'<p class="window__note">{e(resumen)}</p>')


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(rf"(<!-- diario:{nombre}:start -->\n?)(.*?)([ \t]*<!-- diario:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        return doc
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--posts", help="carpeta de entradas (si no, la de diario.json)")
    args = ap.parse_args()
    cfg = json.loads((AQUI / "diario.json").read_text(encoding="utf-8"))
    entradas, avisos = leer_entradas(resolver(args.posts or cfg["vault_posts"]))
    for a in avisos:
        print(f"  ⚠ {a}")
    print(f"Entradas publicadas: {len(entradas)}")
    for x in entradas[:10]:
        print(f"  Entry #{x['n']:<3} {x['fecha']}  {x['titulo']}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return
    raiz = AQUI.parent
    diario = raiz / cfg.get("pagina", "diario.html")
    doc = diario.read_text(encoding="utf-8")
    doc = reemplazar(doc, "entradas", html_entradas(entradas))
    doc = reemplazar(doc, "archivo", html_archivo(entradas))
    diario.write_text(doc, encoding="utf-8", newline="\n")
    index = raiz / "index.html"
    if index.exists():
        d2 = index.read_text(encoding="utf-8")
        nuevo = reemplazar(d2, "ultima", html_ultima(entradas))
        if nuevo != d2:
            index.write_text(nuevo, encoding="utf-8", newline="\n")
    print(f"\nListo: {diario.name} ({len(entradas)} entradas).")


if __name__ == "__main__":
    main()
