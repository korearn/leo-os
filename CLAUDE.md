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
| `index.html` (Ahora mismo + "En rotación", barra de estado, fecha, contador de visitas) | `Knowledge/Lore/Now.md` (Activo y Rotación) | `tools/now_sync.py` | `tools/now.json` (formatos de "Voy en", avisos) |
| `juegos.html` (estante + "Todos mis juegos") | `Knowledge/Games/Shelf.md` (+ "Jugando" desde filas `Game` de `Now.md`) | `tools/shelf_sync.py` | `tools/shelf.json` (colores por juego, nombres cortos) |
| `musica.html` (reproductor de Glass Ecosystem, discos, bandas, "Escuchando ahora") | `Knowledge/Lore/Music/Records.md` + `Bands.md` + filas `Music` de `Now.md` | `tools/music_sync.py` | `tools/music.json` (bloque `aero`: pistas, `base` del audio, enlaces Spotify/Bandcamp) |
| `anime.html` | `Lore/Anime/Anime.md`, `Lore/Manga/Manga.md`, filas `Anime` y `Manga` de `Now.md` | `tools/anime_sync.py` | `tools/anime.json` |
| `cine.html` | `Lore/Movies/Movies.md`, `Lore/Series/Series.md`, `Lore/Comics/Comics.md`, filas `Movie`/`Series`/`Comic` de `Now.md` | `tools/cine_sync.py` | `tools/cine.json` |
| `galeria.html`, `sobre-mi.html`, `construccion.html`, `not_found.html` | — (HTML a mano) | — | — |

- **Now.md** se lee con `tools/now_lib.py` (compartido por todos los scripts). Medios en `tools/medios.json` (una palabra: `Game`, `Anime`, `Series`, `Manga`, `Book`, `Comic`, `Movie`, `Music`). Juegos sin meta: `PLAY` o celda vacía; `12h` horas. "Voy en" en formato código: `E6/11`, `S2E3/10`, `C12/200`, `V3/23`, `P49/779`, `#4/9`, `45%`, `NEW` (con `/total` sale barra). Columnas por encabezado: Medio, Obra, Voy en, Sobre (sale en la web), Hueco (solo vault). Secciones: Activo (1 por medio), Rotación (bloque compacto en la web), Siguiente (no sale en portada; cine lo muestra como "próxima función"). `tools/now_state.json` guarda cuándo avanzó cada obra para avisar a los 21 días.
- **Todo de una vez:** `python tools/sync.py` (o `--dry-run`). Python 3 en Windows, solo librería estándar.
- **⭐** en cualquier tabla = destacado en la web (cartucho, CD, boleto, VHS, tomo…). Sin ⭐ = solo en las listas.
- **Columna "Nota"** = descripción breve que se muestra en la web (p. ej. "Retrofuturismo y líneas temporales"). Todos los títulos deben tener una.
- **Calificaciones** (`9/10`) viven solo en el vault; la web no las muestra (`"mostrar_calificacion": false` en `cine.json`).
- **Una ficha por obra.** `Movies.md`, `Series.md`, `Comics.md`, `Anime.md`, `Manga.md`, `Books.md` (solo vault) y `Records.md` son la ficha completa: Año, creador, Género, ⭐, **Nota** (web), **Mi nota** (calificación, solo vault; `en curso` la oculta de las vistas), **De qué trata** y **Por qué me marcó** (razones personales de Leo: no borrar ni reescribir). Comics tiene además `## Personajes` (solo vault).
- `Knowledge/Lore/Canon.md` = **Registro** con fecha de lo terminado (Fecha · Obra · Medio · Análisis, medios con las palabras de Now) + Patrones. Ya no guarda fichas. Cada script avisa si una obra del Registro no tiene ficha en su catálogo o si una ficha publicada no tiene Nota (`now_lib.revisar_registro`).
- **Estados derivados de Now:** "Jugando" en Shelf, "Escuchando ahora" en música y "Leyendo" de manga salen de Now.md; no se escriben a mano en los catálogos.
- **Audio de Aero Memory:** Neocities gratis no acepta MP3. Los MP3 van en `audio/aero-memory/` (nombres en `music.json`), se suben a GitHub y se sirven con **GitHub Pages** (`https://korearn.github.io/leo-os/audio/aero-memory/`). Si no cargan, el reproductor muestra "Sin señal" y, si hay enlace de Spotify, el botón ⏏ abre el álbum.
- Contador de visitas: `now_sync.py` lo lee de `https://neocities.org/api/info?sitename=leo-os` al correr; `index.html` intenta leerlo en vivo (puede fallar por CORS, entonces queda el del último sync).

## Flujo de Leo
1. Edita las notas en Obsidian.
2. `python tools/sync.py` en `D:\LeOS\Dev\Website`.
3. `git add . ; git commit -m "..." ; git push`.
4. Sube a Neocities solo los `.html`/`.css`/imágenes que cambiaron.

**Nunca se suben a Neocities:** `tools/`, `audio/` (Neocities gratis no acepta MP3), `README.md`, `CLAUDE.md`, `gameshots/` (originales pesados; las versiones web están en `img/shots/` como WebP).

## Reglas para Claude
- **Lee siempre la versión actual del disco antes de editar** (Leo edita a mano y su editor formatea el HTML). Nunca reescribas desde una copia vieja; al guardar, usa la protección de "archivo cambiado" y si hay conflicto vuelve a leer y fusiona.
- Cambios en notas del vault: completar datos (año, autor, descripción) está bien; **no borrar ni reescribir sus razones personales**. Si hay ambigüedad (dos versiones de una obra), preguntar.
- Antes de cambios grandes de estructura, proponer y confirmar.
- No uses datos sensibles en la web (nombre legal, UPC/ISRC del EP, ciudad exacta, empresa).

## Pendientes (ronda de revisiones)
- [x] **Now.md:** formato nuevo (medios por palabra, códigos de avance, Activo/Rotación/Siguiente) — 2026-10-16. Falta que Leo lo revise en vivo.
- [x] Música: reproductor real de *Glass Ecosystem* (2026-10-16). Falta: copiar los MP3 a `audio/aero-memory/`, activar GitHub Pages en el repo y poner el enlace de Spotify en `music.json`.
- [ ] Música: lista completa desplegable de discos (hoy solo salen los ⭐).
- [ ] Página propia de Pokémon (equipos por juego desde `Knowledge/Games/Pokemon/Teams.md`).
- [ ] Medalla "Código" en Sobre mí: ¿link a GitHub o solo adorno?
- [ ] Revisar todas las páginas en celular.
- [x] Doble captura resuelta para cine (2026-10-16): fichas en Movies/Series/Comics, Canon solo registro. Anime, Manga, Libros y Records también (2026-10-16); Shelf toma "jugando" de Now.
- [ ] Actualizar `README.md` con `tools/sync.py`.
