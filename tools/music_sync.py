"""Genera las listas de la página Música desde el vault.

- Now.md (filas Music): "Escuchando ahora" (el artista se toma de Discos).
- Records.md: "Discos" (los ⭐ salen como estuches de CD). "Mi nota" solo vive en el vault.
- Canon.md: solo avisos (obras del Registro sin ficha).
- music.json, bloques "obi" y "generos_jp": la franja obi (帯) de cada CD ⭐, como los discos japoneses.
- Records.md, columna Género: los géneros de los ⭐ forman "Lo que más escucho" (botones que iluminan discos y bandas).
- Bands.md: "Favoritas" = el cartel de festival de "Mis bandas". El top de Spotify ("Top reciente" y
  "De siempre") ya no sale en la web; se queda en el vault como registro.

Reescribe en musica.html lo que hay entre <!-- music:ahora/discos/bandas/generos:start/end -->.

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

from now_lib import avisar_tope, _clave, leer_now, revisar_registro, resolver
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


def leer_bandas(ruta: Path) -> list[str]:
    """Lista '## Favoritas' de Bands.md (en orden; es el orden del cartel)."""
    favs, seccion = [], ""
    limpio = lambda t: re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", t)
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion = linea[3:].strip().lower()
            continue
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+?)\s*$", linea)
        if m and seccion == "favoritas":
            favs.append(limpio(m.group(1)))
    return favs


def generos(fila: dict) -> list[str]:
    return [g.strip() for g in (fila.get("género") or fila.get("genero") or "").split(",") if g.strip()]


def _attr(lista: list[str]) -> str:
    return "|".join(x.lower() for x in lista)


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


def html_obi(f: dict, cfg: dict) -> str:
    """Franja obi (帯) como en los discos japoneses: artista en katakana y el primer género, de music.json."""
    obis = {k.lower(): v for k, v in cfg.get("obi", {}).items() if not k.startswith("_")}
    nombre = obis.get(f.get("artista", "").lower())
    if not nombre:
        return ""
    gjp = {k.lower(): v for k, v in cfg.get("generos_jp", {}).items() if not k.startswith("_")}
    gen = next((gjp[g.lower()] for g in generos(f) if g.lower() in gjp), "")
    pie = f'<span class="obi__gen">{e(gen)}</span>' if gen else ""
    return (f'<span class="obi" lang="ja"><span class="obi__cd">CD</span>'
            f'<span class="obi__texto"><span class="obi__art">{e(nombre)}</span>{pie}</span></span>')


def html_discos(filas: list[dict], cfg: dict) -> str:
    favs = [f for f in filas if f["_fav"]]
    favs.sort(key=lambda f: (f.get("año", "") or "9999", f.get("disco", "").lower()))
    out = []
    for f in favs:
        titulo = f.get("disco", "")
        datos = f' id="cd-{slug(titulo)}" data-artista="{e(f.get("artista", "").lower())}" data-generos="{e(_attr(generos(f)))}"'
        out.append(f'              <li class="cd"{datos} style="{e(colores(titulo, cfg))}">')
        portada = SITIO / "img" / "covers" / f"{slug(titulo)}.png"
        obi = html_obi(f, cfg)
        if portada.exists():
            out.append('                <span class="cd__case cd__case--art" aria-hidden="true">'
                       f'<img src="img/covers/{portada.name}" alt="" width="32" height="32" loading="lazy">{obi}</span>')
        else:
            out.append(f'                <span class="cd__case" aria-hidden="true">{obi}</span>')
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


def html_cartel(bandas: list[str], discos: list[dict]) -> str:
    """Cartel de festival: 3 cabezas de cartel, 4 medianas y el resto chicas.
    Si la banda tiene disco ⭐, su nombre es un enlace a ese CD (con JS además lo abre)."""
    I = "            "
    if not bandas:
        return f'{I}<p class="window__note">Agrega bandas en la sección Favoritas de Bands.md.</p>\n'
    por_artista: dict[str, list[dict]] = {}
    for d in discos:
        if d["_fav"]:
            por_artista.setdefault(d.get("artista", "").lower(), []).append(d)
    filas = [bandas[:3], bandas[3:7], bandas[7:]]
    out = [f'{I}<div class="cartel">',
           f'{I}  <p class="cartel__presenta">LeOS presenta</p>',
           f'{I}  <p class="cartel__nombre">LeOS Fest</p>',
           f'{I}  <p class="cartel__sub">Line-up de siempre · una sola noche · entrada libre</p>']
    for n, fila in enumerate(filas, 1):
        if not fila:
            continue
        out.append(f'{I}  <ul class="cartel__fila cartel__fila--{n}">')
        for b in fila:
            suyos = por_artista.get(b.lower(), [])
            gen = _attr(sorted({g for d in suyos for g in generos(d)}))
            datos = f' data-artista="{e(b.lower())}" data-generos="{e(gen)}"'
            if suyos:
                out.append(f'{I}    <li class="banda"{datos}><a href="#cd-{slug(suyos[0].get("disco", ""))}">{e(b)}</a></li>')
            else:
                out.append(f'{I}    <li class="banda"{datos}><span>{e(b)}</span></li>')
        out.append(f"{I}  </ul>")
    out += [f'{I}  <p class="cartel__pie">Puertas 20:00 · Escenario principal · Haz clic en una banda para sacar su disco</p>',
            f"{I}</div>"]
    return "\n".join(out) + "\n"


def html_generos(discos: list[dict]) -> str:
    """Géneros de los discos ⭐, del que más discos tiene al que menos."""
    I = "              "
    cuenta: dict[str, list[str]] = {}
    for d in discos:
        if d["_fav"]:
            for g in generos(d):
                cuenta.setdefault(g.lower(), []).append(g)
    if not cuenta:
        return f"{I}<li>Llena la columna Género en Records.md</li>\n"
    orden = sorted(cuenta.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return "\n".join(f'{I}<li><button type="button" class="chip" data-genero="{e(k)}" aria-pressed="false">'
                     f'{e(v[0])} <span class="chip__n">{len(v)}</span></button></li>' for k, v in orden) + "\n"


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
    tablas = leer_tablas(resolver(args.records or cfg["vault_records"]))
    bandas = leer_bandas(resolver(args.bands or cfg["vault_bands"]))
    discos = tablas.get("Discos", [])
    ahora = []
    ruta_now = resolver(args.now or cfg.get("vault_now", ""))
    if ruta_now and ruta_now.is_file():
        now, _ = leer_now(ruta_now)
        ahora = [f for f in now["activo"] + now["rotacion"] if f["medio"] == "music"]
    avisos = [f"{d.get('disco')} (⭐) no tiene Nota para la web" for d in discos if d["_fav"] and not d.get("nota")]
    avisos += [f"{d.get('disco')} (⭐) no tiene Género" for d in discos if d["_fav"] and not generos(d)]
    if not bandas:
        avisos.append("Bands.md no tiene la sección '## Favoritas' (el cartel sale vacío)")
    titulos = {_clave(d.get("disco", "")) for d in discos}
    avisos += [f"'{f['obra']}' está en Now pero no tiene fila en Discos" for f in ahora if _clave(f["obra"]) not in titulos]
    avisos += revisar_registro(args.canon or cfg.get("vault_canon"), {"music": ("Records", [d.get("disco", "") for d in discos])})
    for a in avisos:
        print(f"  ⚠ {a}")
    pagina = (AQUI / cfg["pagina"]).resolve()

    print(f"Escuchando ahora: {len(ahora)}  ·  Discos: {len(discos)} ({sum(d['_fav'] for d in discos)} ⭐)  ·  Bandas en el cartel: {len(bandas)}")
    avisar_tope("cds", sum(d["_fav"] for d in discos))
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "ahora", html_ahora(ahora, discos))
    doc = reemplazar(doc, "discos", html_discos(discos, cfg))
    doc = reemplazar(doc, "bandas", html_cartel(bandas, discos))
    doc = reemplazar(doc, "generos", html_generos(discos))
    if cfg.get("aero"):
        doc = reemplazar(doc, "aero", html_aero(cfg["aero"]))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
