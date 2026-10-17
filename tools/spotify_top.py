"""Actualiza el top de bandas (Bands.md del vault) con tus datos reales de Spotify.

Reescribe '## Top reciente' y suma las bandas nuevas a '## De siempre' (nunca borra de ahí).

Dos fuentes, elige una:

1) API de Spotify (inmediato, aprox. el último año):
       python tools/spotify_top.py --api
   Requiere una app propia en https://developer.spotify.com/dashboard (gratis, pero Spotify
   exige Premium al dueño de la app). Redirect URI de la app: http://127.0.0.1:8765/callback
   El Client ID va en tools/spotify.local.json  ->  {"client_id": "..."}
   (ese archivo está en .gitignore: no se sube a GitHub ni a Neocities). No se guarda ningún token.

2) Historial descargado de Spotify (todo el tiempo, tarda días en llegar):
       python tools/spotify_top.py --historial "C:/ruta/a/la/carpeta/descomprimida"
   Lee Streaming_History_Audio_*.json (historial extendido) o StreamingHistory_music_*.json
   (datos de cuenta). Cuenta minutos escuchados por artista e ignora reproducciones < 30 s.

   Con --anio 2026 cuenta solo lo escuchado ese año (la API no puede filtrar por año).

Opciones: --top 50 (cuántos), --rango long_term|medium_term|short_term (solo API),
          --dry-run (solo muestra la lista y qué cambió, no escribe).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import http.server
import json
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections import defaultdict
from pathlib import Path

# Certificados: en Windows, Python a veces no ve la cadena completa que el navegador sí ve
# ("CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate"). Si está instalado
# `truststore` (pip install truststore), se usa el almacén de certificados del sistema, igual que el navegador.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    truststore = None

AQUI = Path(__file__).resolve().parent
REDIRECT = "http://127.0.0.1:8765/callback"
RANGOS = {"long_term": "último año aprox.", "medium_term": "últimos 6 meses", "short_term": "últimas 4 semanas"}


# ---------- fuente 1: API (OAuth con PKCE, sin client secret) ----------

def token_por_pkce(client_id: str) -> str:
    verificador = secrets.token_urlsafe(64)
    reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).rstrip(b"=").decode()
    estado = secrets.token_urlsafe(16)
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT,
        "scope": "user-top-read", "code_challenge_method": "S256", "code_challenge": reto, "state": estado,
    })
    recibido: dict = {}

    class Manejador(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            recibido.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<p>Listo. Ya puedes cerrar esta pestaña y volver a la terminal.</p>".encode())

        def log_message(self, *a):
            pass

    servidor = http.server.HTTPServer(("127.0.0.1", 8765), Manejador)
    print("Abriendo el navegador para que autorices el acceso (solo lectura de tu top)...")
    webbrowser.open(url)
    while "code" not in recibido and "error" not in recibido:
        servidor.handle_request()
    servidor.server_close()
    if recibido.get("error") or recibido.get("state") != estado:
        sys.exit(f"Spotify no autorizó el acceso: {recibido.get('error', 'estado inválido')}")

    datos = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": recibido["code"], "redirect_uri": REDIRECT,
        "client_id": client_id, "code_verifier": verificador,
    }).encode()
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=datos,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with _abrir(req) as r:
        return json.loads(r.read())["access_token"]


def top_api(top: int, rango: str) -> list[str]:
    ruta = AQUI / "spotify.local.json"
    if not ruta.exists():
        sys.exit(f"Falta {ruta.name} con tu Client ID: {{\"client_id\": \"...\"}}")
    token = token_por_pkce(json.loads(ruta.read_text(encoding="utf-8"))["client_id"])
    nombres: list[str] = []
    offset = 0
    while len(nombres) < top:
        url = (f"https://api.spotify.com/v1/me/top/artists?time_range={rango}"
               f"&limit={min(50, top - len(nombres))}&offset={offset}")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with _abrir(req) as r:
            items = json.loads(r.read()).get("items", [])
        if not items:
            break
        nombres += [a["name"] for a in items]
        offset += len(items)
    return nombres[:top]


# ---------- fuente 2: historial descargado ----------

def top_historial(carpeta: Path, top: int, anio: str | None = None) -> tuple[list[str], str]:
    archivos = sorted(carpeta.rglob("Streaming_History_Audio_*.json")) or \
        sorted(carpeta.rglob("StreamingHistory_music_*.json")) or sorted(carpeta.rglob("StreamingHistory*.json"))
    if not archivos:
        sys.exit(f"No encontré archivos de historial en {carpeta}")
    ms = defaultdict(int)
    fechas = []
    for f in archivos:
        for p in json.loads(f.read_text(encoding="utf-8")):
            artista = p.get("master_metadata_album_artist_name") or p.get("artistName")
            dur = p.get("ms_played", p.get("msPlayed", 0)) or 0
            fecha = (p.get("ts") or p.get("endTime") or "")[:10]
            if not artista or dur < 30_000 or (anio and not fecha.startswith(anio)):
                continue
            ms[artista] += dur
            if fecha:
                fechas.append(fecha)
    orden = sorted(ms, key=lambda a: -ms[a])[:top]
    for i, a in enumerate(orden[:10], start=1):
        print(f"  {i:>2}. {a}  ({ms[a] // 60000} min)")
    periodo = f"{min(fechas)} a {max(fechas)}" if fechas else "historial"
    return orden, periodo


# ---------- escribir Bands.md ----------

def _seccion(lineas: list[str], nombre: str) -> tuple[int, int]:
    """Índices [inicio, fin) del cuerpo de '## nombre' (fin = siguiente '## ' o final)."""
    ini = next((i for i, l in enumerate(lineas) if l.strip().lower() == f"## {nombre}".lower()), None)
    if ini is None:
        return -1, -1
    fin = next((i for i in range(ini + 1, len(lineas)) if lineas[i].startswith("## ")), len(lineas))
    return ini + 1, fin


def escribir(bandas: list[str], fuente: str, ruta: Path, dry: bool) -> None:
    """Reescribe '## Top reciente' y SUMA las bandas nuevas al final de '## De siempre' (nunca borra)."""
    texto = ruta.read_text(encoding="utf-8")
    lineas = texto.splitlines()
    t0, t1 = _seccion(lineas, "Top reciente")
    s0, s1 = _seccion(lineas, "De siempre")
    if t0 < 0 or s0 < 0:
        sys.exit("Bands.md necesita las secciones '## Top reciente' y '## De siempre'.")

    viejas = [m.group(1).strip() for l in lineas[t0:t1] if (m := re.match(r"^\s*\d+\.\s+(.+?)\s*$", l))]
    siempre = [m.group(1).strip() for l in lineas[s0:s1] if (m := re.match(r"^\s*[-*]\s+(.+?)\s*$", l))]
    limpio = lambda b: re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", b).lower()
    en_siempre = {limpio(b) for b in siempre}
    nuevas_set = {b.lower() for b in bandas}
    entran = [b for b in bandas if b.lower() not in {limpio(v) for v in viejas}]
    salen = [b for b in viejas if limpio(b) not in nuevas_set]
    suman = [b for b in bandas if b.lower() not in en_siempre]
    print(f"\nTop {len(bandas)} ({fuente}).")
    print("Entran al top: " + (", ".join(entran) or "ninguna"))
    print("Salen del top: " + (", ".join(salen) or "ninguna") + "  (se quedan en 'De siempre')")
    print("Se suman a 'De siempre': " + (", ".join(suman) or "ninguna"))
    if dry:
        print("\n(dry-run: no se escribió nada)")
        return

    hoy = dt.date.today().isoformat()
    top = ["", f"Top {len(bandas)} según Spotify ({fuente}), actualizado {hoy}.", ""] + \
          [f"{i}. {b}" for i, b in enumerate(bandas, start=1)] + [""]
    cuerpo_s = lineas[s0:s1]
    while cuerpo_s and not cuerpo_s[-1].strip():
        cuerpo_s.pop()
    cuerpo_s += [f"- {b}" for b in suman] + [""]
    nuevo = lineas[:t0] + top + lineas[t1:s0] + cuerpo_s + lineas[s1:]
    if t0 > s0:  # por si las secciones están al revés
        nuevo = lineas[:s0] + cuerpo_s + lineas[s1:t0] + top + lineas[t1:]
    ruta.write_text("\n".join(nuevo).rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"\nListo: {ruta.name} actualizado. Corre tools/music_sync.py (o sync.py) para la web.")


def _abrir(req, timeout=15):
    """urlopen con un mensaje claro si falla la verificación del certificado (nunca se desactiva)."""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as err:
        if "CERTIFICATE_VERIFY_FAILED" in str(err):
            sys.exit("No pude verificar el certificado de Spotify.\n"
                     "  1) Instala truststore:  python -m pip install truststore   y vuelve a correr el script.\n"
                     "  2) Si sigue igual, tu antivirus puede estar inspeccionando HTTPS (p. ej. 'escaneo web/HTTPS');"
                     " desactívalo solo para Python o agrega una excepción.")
        raise


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--api", action="store_true", help="usar la API de Spotify")
    g.add_argument("--historial", help="carpeta con el historial descargado de Spotify")
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--rango", default="long_term", choices=list(RANGOS))
    ap.add_argument("--anio", help="solo historial: limita a un año, p. ej. 2026")
    ap.add_argument("--bands", help="ruta a Bands.md (si no, la de music.json)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.loads((AQUI / "music.json").read_text(encoding="utf-8"))
    ruta = Path(args.bands or cfg["vault_bands"])
    if args.api:
        bandas, fuente = top_api(args.top, args.rango), RANGOS[args.rango]
    else:
        bandas, periodo = top_historial(Path(args.historial), args.top, args.anio)
        fuente = f"año {args.anio}, historial {periodo}" if args.anio else f"historial {periodo}"
    if not bandas:
        sys.exit("Spotify no devolvió artistas.")
    escribir(bandas, fuente, ruta, args.dry_run)


if __name__ == "__main__":
    main()
