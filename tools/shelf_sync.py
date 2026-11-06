"""Genera la página Videojuegos desde Shelf.md del vault.

Lee las secciones de Shelf.md (Recomendados, Clásicos por consola, Modernos, Por jugar, Wishlist).
El estado "jugando" y la ventana "Jugando ahora" salen de Now.md (filas Game); Canon.md solo se revisa (avisos).
Reescribe en juegos.html lo que hay entre los marcadores <!-- shelf:NOMBRE:start/end -->:
  insert   -> "Inserta un cartucho" (tabla Recomendados, con el filtro ¿Qué te late hoy?)
  jugando  -> "Jugando ahora" (Now.md)
  estante  -> el estante completo (juegos con ⭐), dentro de La caja de cartuchos
  listas   -> todas las listas (Clásicos, Modernos, Wishlist)
  pila     -> La pila de pendientes (Por jugar)
Colores, nombres cortos y modos: tools/shelf.json.

Uso (desde la carpeta del sitio):
    python tools/shelf_sync.py            # actualiza juegos.html
    python tools/shelf_sync.py --dry-run  # solo muestra el resumen
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

AQUI = Path(__file__).resolve().parent
e = html.escape

# Etiquetas por defecto (si el juego no tiene colores en shelf.json)
PALETA = [("#d8382c", "#f2f2f2"), ("#1f5fb0", "#f2c230"), ("#2f8f4e", "#e8e0c8"),
          ("#7b3fa8", "#e0b23a"), ("#c2862a", "#2b2b31"), ("#167ec4", "#e8f4ff"),
          ("#b83a6a", "#f3d7a0"), ("#3a3f9a", "#5fe0ff"), ("#0e7d6e", "#f2e6b0")]


# ---------- lectura de Shelf.md ----------

def celdas(fila: str) -> list[str]:
    """Divide una fila de tabla respetando las barras escapadas (\\|)."""
    fila = fila.strip().strip("|").replace("\\|", "\0")
    return [c.strip().replace("\0", "|") for c in fila.split("|")]


def es_separador(c: list[str]) -> bool:
    return all(set(x) <= set("-: ") for x in c)


def leer_shelf(ruta: Path) -> dict:
    datos = {"Clásicos": {}, "Modernos": [], "Por jugar": [], "Wishlist": [], "Recomendados": []}
    seccion, consola, encabezado = None, None, None

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion, consola, encabezado = linea[3:].strip(), None, None
        elif linea.startswith("### "):
            consola, encabezado = linea[4:].strip(), None
        elif linea.strip().startswith("|") and seccion in datos:
            c = celdas(linea)
            if encabezado is None:
                encabezado = [x.lower() for x in c]
                continue
            if es_separador(c) or not c[0]:
                continue
            fila = dict(zip(encabezado, c))
            if seccion == "Recomendados":
                datos["Recomendados"].append({
                    "titulo": fila.get("juego", ""),
                    "modo": fila.get("modo", "").strip().lower(),
                    "porque": fila.get("recomiendo si", ""),
                    "prueba": fila.get("prueba", ""),
                })
                continue
            juego = {
                "titulo": fila.get("juego", ""),
                "fecha": fila.get("fecha", ""),
                "fav": "⭐" in fila.get("⭐", "") or "⭐" in "".join(c),
                "estado": fila.get("estado", "").lower(),
                "plataforma": fila.get("plataforma", ""),
                "nota": fila.get("nota", ""),
            }
            if seccion == "Clásicos":
                if consola:
                    juego["plataforma"] = consola
                    datos["Clásicos"].setdefault(consola, []).append(juego)
            else:
                datos[seccion].append(juego)
    return datos


def clave_fecha(j: dict):
    f = j["fecha"]
    return (0, f.ljust(10, "~"), j["titulo"].lower()) if re.match(r"^\d{4}", f) else (1, "", j["titulo"].lower())


def anio(j: dict) -> str:
    m = re.match(r"^(\d{4})", j["fecha"])
    return m.group(1) if m else ""


# ---------- HTML ----------

def estilo_por_defecto(titulo: str) -> str:
    i = int(hashlib.md5(titulo.encode("utf-8")).hexdigest(), 16) % len(PALETA)
    a, b = PALETA[i]
    return f"--label:{a};--label2:{b}"


def html_estante(datos: dict, cfg: dict) -> str:
    consolas = cfg["consolas"]
    orden = {c["nombre"]: i for i, c in enumerate(consolas)}
    info = {c["nombre"]: c for c in consolas}
    extra = cfg.get("juegos", {})

    favs: dict[str, list] = {}
    for consola, lista in datos["Clásicos"].items():
        for j in lista:
            if j["fav"]:
                favs.setdefault(consola, []).append(j)
    for j in datos["Modernos"]:
        if j["fav"]:
            favs.setdefault(j["plataforma"] or "PC", []).append(j)

    out = []
    for consola in sorted(favs, key=lambda c: (orden.get(c, 999), c)):
        c = info.get(consola, {"clase": "disc", "acento": "#9aa6d6"})
        rid = "sh-" + re.sub(r"[^a-z0-9]+", "-", consola.lower()).strip("-")
        out.append(f'              <section class="shelf__row" style="--accent:{c["acento"]}" aria-labelledby="{rid}">')
        out.append(f'                <h3 class="shelf__console" id="{rid}">{e(consola)}</h3>')
        out.append('                <ul class="shelf__games">')
        for j in sorted(favs[consola], key=clave_fecha):
            x = extra.get(j["titulo"], {})
            estilo = x.get("estilo") or estilo_por_defecto(j["titulo"])
            nombre = x.get("corto") or j["titulo"]
            out.append(f'                  <li class="game game--{c["clase"]}" style="{e(estilo)}">')
            out.append('                    <span class="game__box" aria-hidden="true"><span class="game__label"></span></span>')
            out.append(f'                    <span class="game__title">{e(nombre)}</span>')
            out.append(f'                    <span class="game__year">{anio(j)}</span>')
            out.append('                  </li>')
        out.append('                </ul>')
        out.append('              </section>')
    return "\n".join(out) + "\n"


def li_juego(j: dict, cfg: dict, con_plataforma: bool) -> str:
    partes = [f'<span class="gl__year">{anio(j) or "—"}</span>',
              f'<span class="gl__name">{e(j["titulo"])}</span>']
    if j["fav"]:
        partes.append('<span class="gl__fav" title="En el estante">⭐</span>')
    if con_plataforma and j["plataforma"]:
        partes.append(f'<span class="gl__plat">{e(j["plataforma"])}</span>')
    est = cfg["estados"].get(j["estado"])
    if est:
        partes.append(f'<span class="gl__state gl__state--{e(j["estado"])}">{e(est)}</span>')
    return "<li>" + " ".join(partes) + "</li>"


def html_listas(datos: dict, cfg: dict) -> str:
    orden = {c["nombre"]: i for i, c in enumerate(cfg["consolas"])}
    clasicos = datos["Clásicos"]
    n_clas = sum(len(v) for v in clasicos.values())
    n_mod = len(datos["Modernos"])
    n_wl = len(datos["Wishlist"])
    I = "          "

    out = [f'{I}<p class="window__note">He jugado {n_clas + n_mod} juegos'
           + '. Los de la ⭐ están en el estante completo.</p>']

    out.append(f'{I}<details class="gamelist">')
    out.append(f'{I}  <summary>Clásicos <span class="gamelist__count">{n_clas}</span></summary>')
    for consola in sorted(clasicos, key=lambda c: (orden.get(c, 999), c)):
        lista = sorted(clasicos[consola], key=clave_fecha)
        out.append(f'{I}  <h3 class="gamelist__console">{e(consola)} <small>{len(lista)}</small></h3>')
        out.append(f'{I}  <ul class="gamelist__items">')
        out += [f'{I}    {li_juego(j, cfg, False)}' for j in lista]
        out.append(f'{I}  </ul>')
    out.append(f'{I}</details>')

    out.append(f'{I}<details class="gamelist">')
    out.append(f'{I}  <summary>Modernos <span class="gamelist__count">{n_mod}</span></summary>')
    out.append(f'{I}  <ul class="gamelist__items">')
    out += [f'{I}    {li_juego(j, cfg, True)}' for j in sorted(datos["Modernos"], key=clave_fecha)]
    out.append(f'{I}  </ul>')
    out.append(f'{I}</details>')

    for clave, nombre, mostrar in [("Wishlist", "Wishlist", "wishlist")]:
        lista = datos[clave]
        if not lista or not cfg["mostrar"].get(mostrar, True):
            continue
        out.append(f'{I}<details class="gamelist">')
        out.append(f'{I}  <summary>{nombre} <span class="gamelist__count">{len(lista)}</span></summary>')
        out.append(f'{I}  <ul class="gamelist__items gamelist__items--plain">')
        for j in sorted(lista, key=lambda j: j["titulo"].lower()):
            plat = f' <span class="gl__plat">{e(j["plataforma"])}</span>' if j["plataforma"] else ""
            out.append(f'{I}    <li><span class="gl__name">{e(j["titulo"])}</span>{plat}</li>')
        out.append(f'{I}  </ul>')
        out.append(f'{I}</details>')
    return "\n".join(out) + "\n"


def _id(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _clave(t)).strip("-")


def html_insert(recs: list[dict], todos: list[dict], cfg: dict) -> tuple[str, list[str]]:
    """'Inserta un cartucho': filtro por modo + pantalla + cartuchos. Funciona sin JavaScript (radios + CSS)."""
    I = "            "
    modos = cfg.get("modos", {})
    info = {c["nombre"]: c for c in cfg["consolas"]}
    extra = cfg.get("juegos", {})
    por_clave = {}
    for j in todos:
        por_clave.setdefault(_clave(j["titulo"]), j)
    avisos, items = [], []
    for r in recs:
        j = por_clave.get(_clave(r["titulo"]))
        if not j:
            avisos.append(f"Recomendado '{r['titulo']}' no está en Clásicos ni Modernos (se omite)")
            continue
        if r["modo"] and r["modo"] not in modos:
            avisos.append(f"Modo '{r['modo']}' de '{r['titulo']}' no existe (usa: {', '.join(modos)})")
        items.append((r, j))
    ids = {_clave(r["titulo"]): "cart-" + _id(r["titulo"]) for r, _ in items}

    out = [f'{I}<div class="insert">']
    out.append(f'{I}  <input class="sr-only" type="radio" name="modo" id="modo-todos" checked>')
    for m in modos:
        out.append(f'{I}  <input class="sr-only" type="radio" name="modo" id="modo-{m}">')
    out.append(f'{I}  <div class="insert__modes">')
    out.append(f'{I}    <span class="insert__ask">{e(cfg.get("pregunta_modo", "¿En qué mood vienes?"))}</span>')
    out.append(f'{I}    <label for="modo-todos">Todo</label>')
    for m, d in modos.items():
        out.append(f'{I}    <label for="modo-{m}">{e(d["nombre"])}</label>')
    out.append(f'{I}  </div>')
    out.append(f'{I}  <p class="insert__desc">')
    out.append(f'{I}    <span data-m="todos">Mis recomendados de todas las épocas.</span>')
    for m, d in modos.items():
        out.append(f'{I}    <span data-m="{m}">{e(d["desc"])}</span>')
    out.append(f'{I}  </p>')

    out.append(f'{I}  <div class="insert__tv">')
    out.append(f'{I}    <div class="insert__screen" aria-live="polite">')
    out.append(f'{I}      <p class="insert__idle">INSERTA UN CARTUCHO<span class="blink" aria-hidden="true">_</span></p>')
    for r, j in items:
        cid = ids[_clave(r["titulo"])]
        modo = modos.get(r["modo"], {}).get("nombre", "")
        nombre = extra.get(j["titulo"], {}).get("corto") or j["titulo"]
        meta = " · ".join(x for x in [j["plataforma"], anio(j), modo] if x)
        out.append(f'{I}      <input class="sr-only" type="radio" name="cart" id="{cid}">')
        out.append(f'{I}      <article class="insert__panel">')
        out.append(f'{I}        <p class="insert__boot">CARGANDO... OK</p>')
        out.append(f'{I}        <h3 class="insert__title">{e(nombre)}</h3>')
        out.append(f'{I}        <p class="insert__meta">{e(meta)}</p>')
        if r["porque"]:
            out.append(f'{I}        <p class="insert__why"><span>Te lo recomiendo si</span> {e(r["porque"])}</p>')
        if r["prueba"]:
            destino = ids.get(_clave(r["prueba"]))
            jp = por_clave.get(_clave(r["prueba"]))
            txt = (extra.get(jp["titulo"], {}).get("corto") if jp else None) or r["prueba"]
            p = (f'<label class="insert__jump" for="{destino}">{e(txt)} ▸</label>' if destino
                 else f'<b>{e(txt)}</b>')
            out.append(f'{I}        <p class="insert__next">¿Te gustó? Prueba {p}</p>')
        out.append(f'{I}      </article>')
    out.append(f'{I}    </div>')
    out.append(f'{I}    <div class="insert__slot" aria-hidden="true"></div>')
    out.append(f'{I}  </div>')

    out.append(f'{I}  <ul class="insert__carts">')
    for r, j in items:
        cid = ids[_clave(r["titulo"])]
        c = info.get(j["plataforma"], {"clase": "disc"})
        x = extra.get(j["titulo"], {})
        estilo = x.get("estilo") or estilo_por_defecto(j["titulo"])
        nombre = x.get("corto") or j["titulo"]
        out.append(f'{I}    <li class="game game--{c["clase"]}" data-modo="{e(r["modo"])}" style="{e(estilo)}">')
        out.append(f'{I}      <label for="{cid}">')
        out.append(f'{I}        <span class="game__box" aria-hidden="true"><span class="game__label"></span></span>')
        out.append(f'{I}        <span class="game__title">{e(nombre)}</span>')
        out.append(f'{I}        <span class="game__year">{e(j["plataforma"])}</span>')
        out.append(f'{I}      </label>')
        out.append(f'{I}    </li>')
    out.append(f'{I}  </ul>')
    out.append(f'{I}</div>')
    return "\n".join(out) + "\n", avisos


def html_jugando(now: dict | None) -> str:
    """'Jugando ahora' desde Now.md: Activo y Rotación (Jugando) y Siguiente (Queue)."""
    I = "            "
    if not now:
        return f"{I}<p class=\"side-text\">Sin datos de Now.md.</p>\n"
    filas = [(f, "Jugando") for f in now["activo"] + now["rotacion"] if f["medio"] == "game"]
    filas += [(f, "Queue") for f in now.get("siguiente", []) if f["medio"] == "game"]
    if not filas:
        return f"{I}<p class=\"side-text\">Nada en la consola por ahora.</p>\n"
    out = [f'{I}<dl class="favs">']
    for f, estado in filas:
        detalle = f.get("sobre") or (f["avance"]["texto"] if f.get("voy") and f["voy"].upper() not in ("PLAY", "") else "")
        out.append(f'{I}  <dt>{e(estado)}</dt>')
        out.append(f'{I}  <dd>{e(f["obra"])}' + (f' <small>· {e(detalle)}</small>' if detalle else '') + '</dd>')
    out.append(f'{I}</dl>')
    return "\n".join(out) + "\n"


def html_pila(datos: dict) -> str:
    """La pila de pendientes (Por jugar), como lomos de cajas apiladas."""
    I = "          "
    lista = sorted(datos["Por jugar"], key=lambda j: j["titulo"].lower())
    out = [f'{I}<p class="pila__count"><b>{len(lista)}</b> juegos esperando turno.</p>']
    out.append(f'{I}<p class="window__note">Todos ya están en mi biblioteca. ¿Cuál empiezo? Vota en el libro de visitas y el más pedido pasa a la consola.</p>')
    out.append(f'{I}<a class="bigbtn pila__cta" href="libro.html">✎ Dime cuál empiezo</a>')
    out.append(f'{I}<details class="gamelist">')
    out.append(f'{I}  <summary>Ver la pila <span class="gamelist__count">{len(lista)}</span></summary>')
    out.append(f'{I}  <ul class="pila">')
    for j in lista:
        a = estilo_por_defecto(j["titulo"]).split(";")[0].split(":")[1]
        out.append(f'{I}    <li style="--lomo:{a}">{e(j["titulo"])}</li>')
    out.append(f'{I}  </ul>')
    out.append(f'{I}</details>')
    return "\n".join(out) + "\n"


def reemplazar(doc: str, nombre: str, nuevo: str) -> str:
    patron = re.compile(
        rf"(<!-- shelf:{nombre}:start -->\n?)(.*?)([ \t]*<!-- shelf:{nombre}:end -->)", re.S)
    if not patron.search(doc):
        sys.exit(f"Falta el marcador shelf:{nombre} en la página")
    return patron.sub(lambda m: m.group(1) + nuevo + m.group(3), doc, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="no escribe, solo muestra el resumen")
    ap.add_argument("--shelf", help="ruta a Shelf.md (si no, la de shelf.json)")
    ap.add_argument("--now", help="ruta a Now.md")
    ap.add_argument("--canon", help="ruta a Canon.md")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "shelf.json").read_text(encoding="utf-8"))
    datos = leer_shelf(resolver(args.shelf or cfg["vault_shelf"]))
    pagina = (AQUI / cfg["pagina"]).resolve()

    # "Jugando" sale de Now.md (filas Game de Activo y Rotación); no se escribe a mano en Shelf.
    avisos = []
    now = None
    todos = [j for v in datos["Clásicos"].values() for j in v] + datos["Modernos"]
    if args.now or cfg.get("vault_now"):
        ruta_now = resolver(args.now or cfg["vault_now"])
        if ruta_now.exists():
            now, _ = leer_now(ruta_now)
            jugando = {_clave(f["obra"]) for f in now["activo"] + now["rotacion"] if f["medio"] == "game"}
            por_clave = {_clave(j["titulo"]): j for j in todos}
            for j in todos:
                if j["estado"] == "jugando" and _clave(j["titulo"]) not in jugando:
                    avisos.append(f"{j['titulo']} dice 'jugando' en Shelf pero no está en Now (se ignora)")
                    j["estado"] = ""
            for k in jugando:
                if k in por_clave:
                    por_clave[k]["estado"] = "jugando"
                else:
                    avisos.append(f"'{k}' está en Now pero no tiene fila en Shelf (agrégalo a Modernos)")
    avisos += revisar_registro(args.canon or cfg.get("vault_canon"), {"game": ("Shelf", [j["titulo"] for j in todos])})
    for a in avisos:
        print(f"  ⚠ {a}")

    conocidas = {c["nombre"] for c in cfg["consolas"]}
    print("Clásicos:")
    for consola, lista in datos["Clásicos"].items():
        aviso = "" if consola in conocidas else "   (consola sin diseño: saldrá como disco)"
        print(f"  {consola:<18} {len(lista):>3} juegos, {sum(j['fav'] for j in lista)} ⭐{aviso}")
    print(f"Modernos: {len(datos['Modernos'])}  ·  Por jugar: {len(datos['Por jugar'])}  ·  Wishlist: {len(datos['Wishlist'])}")
    insert, av_rec = html_insert(datos["Recomendados"], todos, cfg)
    for a in av_rec:
        print(f"  ⚠ {a}")
    print(f"Recomendados: {len(datos['Recomendados'])}")
    avisar_tope("cartuchos", len(datos["Recomendados"]))
    avisar_tope("estante", sum(j["fav"] for j in todos))
    sin_fecha = [j["titulo"] for v in datos["Clásicos"].values() for j in v if not anio(j)] + \
                [j["titulo"] for j in datos["Modernos"] if not anio(j)]
    if sin_fecha:
        print(f"Sin fecha ({len(sin_fecha)}, van al final): " + ", ".join(sin_fecha[:8]) + (" ..." if len(sin_fecha) > 8 else ""))

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return

    doc = pagina.read_text(encoding="utf-8")
    doc = reemplazar(doc, "insert", insert)
    doc = reemplazar(doc, "jugando", html_jugando(now))
    doc = reemplazar(doc, "estante", html_estante(datos, cfg))
    doc = reemplazar(doc, "pila", html_pila(datos))
    doc = reemplazar(doc, "listas", html_listas(datos, cfg))
    pagina.write_text(doc, encoding="utf-8", newline="\n")
    print(f"\nListo: {pagina.name} actualizado.")


if __name__ == "__main__":
    main()
