# CLAUDE.md — LeOS (sitio personal de Leo)

> Contexto para retomar el trabajo en un chat nuevo. Léeme antes de tocar nada. Responde en **español**, directo y por pasos.

## Qué es
- Sitio personal estilo Old Internet: **https://leo-os.neocities.org** (Neocities, plan gratis).
- Código: `D:\LeOS\Dev\Website` · repo GitHub `korearn/leo-os` (rama `main`).
- Se publica **a mano**: Leo arrastra los archivos al panel de Neocities. No hay deploy automático (por decisión suya, mientras el sitio cambia mucho).
- Propósito: mostrar sus gustos (juegos, música, anime, cine…) y encontrar gente con gustos afines. Tono: nada cursi, nada demasiado personal.

## Estética: "Aero de medianoche"
Frutiger Aero de noche + menú de GameCube + plástico de Game Boy Color + los 4 colores del control de N64 como acento.
- Tokens en `style.css` (`:root`): `--noche #120f2e`, `--indigo #2a2463`, `--aqua #5fe0ff`, `--uva #7b5cff`, `--hielo #e8f4ff`, `--niebla #9aa6d6`, N64 rojo/verde/amarillo/azul.
- Fuentes: **Pixelify Sans** (títulos, etiquetas) y **Trebuchet MS** (texto). Ojo: en Pixelify los números 5/8/S se confunden; años y cifras van en Trebuchet.
- Cada página tiene **una** pieza memorable y lo demás son "ventanas" (`.window`): portada = memory card; juegos = estante de cartuchos; música = reproductor tipo Winamp; anime = tele CRT + cintas VHS + tomos; cine = boletos + guía de canales + cómics embolsados; sobre mí = ficha del jugador con medallas.
- Cartuchos/discos son **formas estilizadas sin logos ni arte de etiquetas** (no copiar diseños/arte oficiales).

## Páginas, fuentes y scripts
Todo se genera desde el vault de Obsidian (`D:\LeOS\Vault\Brain\Leo_OS`). Los scripts solo reescriben lo que hay entre marcadores `<!-- xxx:start -->` / `<!-- xxx:end -->`.

| Página | Nota(s) del vault | Script | Config |
|---|---|---|---|
| `index.html` (Ahora mismo, barra de estado, fecha, contador de visitas) | `Knowledge/Lore/Now.md` | `tools/now_sync.py` | `tools/now.json` |
| `juegos.html` (estante + "Todos mis juegos") | `Knowledge/Games/Shelf.md` | `tools/shelf_sync.py` | `tools/shelf.json` (colores por juego, nombres cortos) |
| `musica.html` | `Knowledge/Lore/Music/Records.md` + `Bands.md` | `tools/music_sync.py` | `tools/music.json` |
| `anime.html` | `Lore/Anime/Anime.md`, `Lore/Manga/Manga.md`, filas 📺 de `Now.md` | `tools/anime_sync.py` | `tools/anime.json` |
| `cine.html` | `Lore/Movies/Movies.md`, `Lore/Series/Series.md`, `Lore/Comics/Comics.md`, filas 🎞️/📔 de `Now.md` | `tools/cine_sync.py` | `tools/cine.json` |
| `galeria.html`, `sobre-mi.html`, `construccion.html`, `not_found.html` | — (HTML a mano) | — | — |

- **Todo de una vez:** `python tools/sync.py` (o `--dry-run`). Python 3 en Windows, solo librería estándar.
- **⭐** en cualquier tabla = destacado en la web (cartucho, CD, boleto, VHS, tomo…). Sin ⭐ = solo en las listas.
- **Columna "Nota"** = descripción breve que se muestra en la web (p. ej. "Retrofuturismo y líneas temporales"). Todos los títulos deben tener una.
- **Calificaciones** (`9/10`) viven solo en el vault; la web no las muestra (`"mostrar_calificacion": false` en `cine.json`).
- `Knowledge/Lore/Canon.md` = registro con fechas + "por qué me marcó" por medio (películas, series live action/animación, anime, cómics, libros). **Mantener siempre las razones personales de Leo**; las sinopsis van en español, 1–2 líneas, sin spoilers.
- Contador de visitas: `now_sync.py` lo lee de `https://neocities.org/api/info?sitename=leo-os` al correr; `index.html` intenta leerlo en vivo (puede fallar por CORS, entonces queda el del último sync).

## Flujo de Leo
1. Edita las notas en Obsidian.
2. `python tools/sync.py` en `D:\LeOS\Dev\Website`.
3. `git add . ; git commit -m "..." ; git push`.
4. Sube a Neocities solo los `.html`/`.css`/imágenes que cambiaron.

**Nunca se suben a Neocities:** `tools/`, `README.md`, `CLAUDE.md`, `gameshots/` (originales pesados; las versiones web están en `img/shots/` como WebP).

## Reglas para Claude
- **Lee siempre la versión actual del disco antes de editar** (Leo edita a mano y su editor formatea el HTML). Nunca reescribas desde una copia vieja; al guardar, usa la protección de "archivo cambiado" y si hay conflicto vuelve a leer y fusiona.
- Cambios en notas del vault: completar datos (año, autor, descripción) está bien; **no borrar ni reescribir sus razones personales**. Si hay ambigüedad (dos versiones de una obra), preguntar.
- Antes de cambios grandes de estructura, proponer y confirmar.
- No uses datos sensibles en la web (nombre legal, UPC/ISRC del EP, ciudad exacta, empresa).

## Pendientes (ronda de revisiones)
- [ ] **Now.md:** mejorar el formato para automatizar mejor lo que pasa a la web (siguiente tarea).
- [ ] Música: que *Glass Ecosystem* (Aero Memory, 4 pistas) suene: embed de Spotify/YouTube o MP3 si el plan gratis los acepta. No vender ni promocionar (reglas de Neocities).
- [ ] Música: lista completa desplegable de discos (hoy solo salen los ⭐).
- [ ] Página propia de Pokémon (equipos por juego desde `Knowledge/Games/Pokemon/Teams.md`).
- [ ] Medalla "Código" en Sobre mí: ¿link a GitHub o solo adorno?
- [ ] Revisar todas las páginas en celular.
- [ ] Evitar doble captura: que el registro de `Canon.md` alimente las listas (hoy lo terminado se anota en Canon y en la nota del medio).
- [ ] Actualizar `README.md` con `tools/sync.py`.
