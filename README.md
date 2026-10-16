# LeOS

Mi rincón en la web: videojuegos, anime, música y todo lo que me gusta. Hecho a mano, sin frameworks.

**En vivo:** https://leo-os.neocities.org

## Estética
"Aero de medianoche": Frutiger Aero de noche, el menú de la GameCube, el plástico de la Game Boy Color y los colores del control del N64. La navegación es una Memory Card.

## Estructura
| Archivo / carpeta | Qué es |
| --- | --- |
| `index.html` | Portada (memory card, "Ahora mismo", galería corta, favoritos) |
| `galeria.html` | Todas las capturas |
| `construccion.html` | Página para secciones que aún no existen |
| `not_found.html` | Error 404 (Neocities la usa automáticamente) |
| `style.css` | Todos los estilos |
| `img/shots/` | Capturas en WebP (`nombre.webp` grande, `nombre-mini.webp` miniatura) |
| `favicon.*`, `apple-touch-icon.png` | Íconos de la pestaña |

`gameshots/` (las capturas originales) no se sube al repo ni a Neocities.

## "Ahora mismo" desde Obsidian
La sección "Ahora mismo" de la portada (y la barra de estado y la fecha) se genera desde la nota `Now.md` del vault:

```powershell
python tools/now_sync.py --dry-run   # ver qué va a poner
python tools/now_sync.py             # escribir en index.html
```

Las plantillas de texto ("E9 / 12" → "Ep. 9 de 12", etc.) están en `tools/now.json`. El script solo toca lo que hay entre los marcadores `<!-- now:... -->` de `index.html`.

## Videojuegos desde Obsidian
El estante y la lista "Todos mis juegos" de `juegos.html` se generan desde `Knowledge/Games/Shelf.md` del vault:

```powershell
python tools/shelf_sync.py --dry-run   # resumen por consola, juegos sin fecha
python tools/shelf_sync.py             # escribir en juegos.html
```

Colores de cada cartucho y nombres cortos del estante: `tools/shelf.json` (sección `juegos`, por título exacto).

## Música desde Obsidian
`musica.html` toma "Escuchando ahora" y "Discos" de `Knowledge/Lore/Music/Records.md`, y el top de bandas de `Bands.md`:

```powershell
python tools/music_sync.py --dry-run
python tools/music_sync.py
```

Colores de cada estuche de CD: `tools/music.json`. Si subes la portada del EP como `img/glass-ecosystem.webp`, aparece sola en el reproductor.

## Anime y manga desde Obsidian
`anime.html` usa `Now.md` (filas 📺, la tele de "Viendo ahora"), `Knowledge/Lore/Anime/Anime.md` y `Knowledge/Lore/Manga/Manga.md`:

```powershell
python tools/anime_sync.py --dry-run
python tools/anime_sync.py
```

Colores de cintas VHS y lomos de manga: `tools/anime.json`.

## Cine, series y cómics desde Obsidian
`cine.html` usa `Knowledge/Lore/Movies/Movies.md`, `Series/Series.md`, `Comics/Comics.md` y "En cartelera" desde `Now.md` (filas 🎞️ y 📔):

```powershell
python tools/cine_sync.py --dry-run
python tools/cine_sync.py
```

Colores de boletos y portadas: `tools/cine.json`.

## Publicar
Por ahora, subiendo los archivos a mano al panel de Neocities. `tools/`, `README.md` y `gameshots/` no se suben.
