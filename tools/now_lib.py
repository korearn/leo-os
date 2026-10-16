"""Lectura compartida de Now.md para now_sync, anime_sync y cine_sync.

- Medios: tools/medios.json (una palabra por medio, con alias).
- Formatos de "Voy en": tools/now.json (códigos tipo E6/11, P49/779, #4/9, C12, 45%, NEW).
- Secciones de Now.md: "## Activo", "## Rotación" y "## Siguiente". Las columnas se leen
  por su encabezado (Medio, Obra, Voy en, Sobre, Hueco), no por posición.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def _norm(s: str) -> str:
    """minúsculas, sin acentos ni selector de emoji: 'Rotación' -> 'rotacion'."""
    s = s.replace("️", "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def cargar_json(nombre: str) -> dict:
    return json.loads((AQUI / nombre).read_text(encoding="utf-8"))


def mapa_medios() -> tuple[dict, dict]:
    """Devuelve (alias normalizado -> clave, clave -> etiqueta)."""
    medios = cargar_json("medios.json")["medios"]
    alias, etiquetas = {}, {}
    for clave, d in medios.items():
        etiquetas[clave] = d["etiqueta"]
        for a in [clave, d["etiqueta"], *d.get("alias", [])]:
            alias[_norm(a)] = clave
    return alias, etiquetas


def limpiar_obra(s: str) -> str:
    """[[Kuuchuu Buranko]] -> Kuuchuu Buranko ; [[nota|Alias]] -> Alias."""
    m = re.fullmatch(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", s.strip())
    return (m.group(2) or m.group(1)).strip() if m else s.strip()


def _celdas(fila: str) -> list[str]:
    fila = fila.strip().strip("|").replace("\\|", "\0")
    return [c.strip().replace("\0", "|") for c in fila.split("|")]


def _rellenar(plantilla: str, grupos: tuple) -> str:
    def opcional(m):
        trozo = m.group(1)
        usados = [int(n) for n in re.findall(r"\{(\d+)\}", trozo)]
        return trozo if all(n <= len(grupos) and grupos[n - 1] for n in usados) else ""
    out = re.sub(r"\[([^\]]*)\]", opcional, plantilla)
    for i, g in enumerate(grupos, start=1):
        out = out.replace("{" + str(i) + "}", str(int(g)) if g and g.isdigit() else (g or ""))
    return out


def avance(voy: str, cfg: dict) -> dict:
    """'E6/11' -> {codigo:'E6/11', texto:'Ep. 6 de 11', num:6, den:11, pct:55, estado:'progreso', ...}.

    estado: 'progreso' (hay total → barra), 'nuevo' (NEW) o 'abierto' (sin medida: PLAY, horas, texto libre).
    """
    voy = voy.strip()
    if not voy and cfg.get("vacio"):
        v = cfg["vacio"]
        return {"codigo": v["codigo"], "texto": v["texto"], "num": None, "den": None, "pct": None,
                "es_codigo": True, "nuevo": False, "estado": v.get("estado", "abierto"), "regla": "vacío"}
    for regla in cfg["formatos"]:
        m = re.match(regla["patron"], voy, re.I)
        if not m:
            continue
        g = m.groups()
        num = den = pct = None
        if "barra" in regla:
            idx = regla["barra"]
            a = g[idx[0] - 1] if len(g) >= idx[0] else None
            b = regla.get("total_fijo") or (g[idx[1] - 1] if len(idx) > 1 and len(g) >= idx[1] else None)
            if a and b and int(b) > 0:
                num, den = int(a), int(b)
                pct = round(min(num / den, 1) * 100)
        return {"codigo": _rellenar(regla["codigo"], g), "texto": _rellenar(regla["texto"], g),
                "num": num, "den": den, "pct": pct, "es_codigo": True,
                "nuevo": regla.get("nombre") == "por empezar", "regla": regla.get("nombre"),
                "estado": "progreso" if pct is not None else ("nuevo" if regla.get("nombre") == "por empezar"
                                                              else regla.get("estado", "abierto"))}
    return {"codigo": voy, "texto": voy, "num": None, "den": None, "pct": None,
            "es_codigo": False, "nuevo": False, "estado": "abierto", "regla": None}


SECCIONES = {"activo": "activo", "rotacion": "rotacion", "siguiente": "siguiente"}


def leer_now(ruta: Path, cfg: dict | None = None) -> tuple[dict[str, list[dict]], list[str]]:
    """Lee Now.md. Devuelve ({'activo': [...], 'rotacion': [...], 'siguiente': [...]}, avisos)."""
    cfg = cfg or cargar_json("now.json")
    alias, etiquetas = mapa_medios()
    out = {k: [] for k in SECCIONES.values()}
    avisos: list[str] = []
    seccion, encabezado = None, None
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            seccion, encabezado = SECCIONES.get(_norm(linea[3:])), None
            continue
        if not seccion or not linea.strip().startswith("|"):
            continue
        c = _celdas(linea)
        if encabezado is None:
            encabezado = [_norm(x) for x in c]
            continue
        if all(set(x) <= set("-: ") for x in c):
            continue
        fila = dict(zip(encabezado, c))
        obra = limpiar_obra(fila.get("obra", ""))
        if not obra:
            continue
        crudo = fila.get("medio", "")
        clave = alias.get(_norm(crudo))
        if clave is None:
            avisos.append(f"Medio desconocido '{crudo}' en '{obra}' (agrégalo a tools/medios.json)")
        out[seccion].append({
            "medio": clave or _norm(crudo),
            "etiqueta": etiquetas.get(clave, crudo),
            "obra": obra,
            "voy": fila.get("voy en", ""),
            "sobre": fila.get("sobre", ""),
            "hueco": fila.get("hueco", ""),
            "avance": avance(fila.get("voy en", ""), cfg),
            "seccion": seccion,
        })
    if cfg.get("un_activo_por_medio", True):
        vistos: dict[str, str] = {}
        for it in out["activo"]:
            if it["medio"] in vistos:
                avisos.append(f"Dos obras de {it['etiqueta']} en Activo ({vistos[it['medio']]} y {it['obra']}): "
                              "deja una y pasa la otra a Rotación")
            vistos.setdefault(it["medio"], it["obra"])
    return out, avisos
