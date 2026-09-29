"""
demo.py
-------
Comando único para DEMOSTRAR el concepto de Vinylr Content Engine en
cualquier momento: genera los duelos "Álbum A vs B" y los posts
"Top 10 LatAm" sin importar si ya tienes las credenciales de
Last.fm configuradas, ni si hay conexión a internet en ese momento.
 
Estrategia de "nunca falla" (importante para poder hacer la demo en vivo
frente a jueces sin depender de que todo esté perfectamente configurado):
 
    Datos (álbumes y top 10):
        1) Intenta Last.fm API real (si hay credenciales) → PLAN A
        2) Si falla o no hay credenciales → usa data/sample/... → PLAN B
 
    Imagen (duelo y top 10):
        1) Intenta el render local (Playwright + HTML/CSS, mismo motor de
           generate_duels.py / generate_top10.py) → PLAN A
        2) Si Playwright no está instalado/no puede lanzar Chromium →
           genera la imagen con Pillow (más simple visualmente, pero
           funcional) → PLAN B, red de seguridad final
 
Uso:
    python src/demo.py
    python src/demo.py --with-reels        # Genera posts y reels
    python src/demo.py --posts-only        # Genera solo posts (default explícito)
    python src/demo.py --reels-only        # Genera solo reels (sin imágenes)
    python src/demo.py --quick             # Genera 1 post y 1 reel (prueba express)
 
--with-reels añade un PLAN C opcional (nunca sustituye a la imagen, solo se
suma): usa remotion-reels/ (ver ese README) para renderizar un video 9:16 de
cada duelo y del Top 10, a partir de los MISMOS dicts que ya arma este script.
Si Node.js o `npm install` no están listos, lo avisa y sigue sin los videos —
el demo de imágenes nunca se ve afectado por esto.
"""
 
import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional
 
import requests
from dotenv import load_dotenv
 
load_dotenv()  # Carga variables de .env sin depender de que el terminal/IDE lo haga por su cuenta.
 
# Import de los módulos ya construidos en iteraciones anteriores.
from generate_duels import build_duels, _load_albums  # reutilizamos su lógica de emparejamiento
 
SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "sample", "trending_albums_sample.json"
)
SAMPLE_TOP10_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "sample", "top10_sample.json"
)
 
# Respaldo del Top 10 LatAm EMBEBIDO en el código (no depende de que exista
# data/sample/top10_sample.json en disco). Es la última red de seguridad de
# la promesa "nunca falla" de esta demo: aunque no se haya creado/actualizado
# ese archivo de ejemplo, la demo igual puede mostrar un Top 10 LatAm.
FALLBACK_TOP10_LATAM = {
    "country_param": "latam",
    "country_name": "LatAm",
    "accent_primary": "#4263FF",
    "accent_secondary": "#FF3B7A",
    "featured_cover_url": "",
    "items": [
        {"rank": 1, "artist": "Bad Bunny", "title": "DTMF"},
        {"rank": 2, "artist": "KAROL G", "title": "Si Antes Te Hubiera Conocido"},
        {"rank": 3, "artist": "Feid", "title": "Luna"},
        {"rank": 4, "artist": "Rauw Alejandro", "title": "Touching the Sky"},
        {"rank": 5, "artist": "Shakira", "title": "Soltera"},
        {"rank": 6, "artist": "Peso Pluma", "title": "Lady Gaga"},
        {"rank": 7, "artist": "Grupo Frontera", "title": "un x100to"},
        {"rank": 8, "artist": "Young Miko", "title": "Classy 101"},
        {"rank": 9, "artist": "Tini", "title": "Muñecas"},
        {"rank": 10, "artist": "Fuerza Regida", "title": "Bebe Dame"},
    ],
}
 
CANVAS_SIZE = (1080, 1440)
BG_COLOR = (18, 18, 22)          # negro/gris muy oscuro, estilo "vinilo"
ACCENT_COLOR = (255, 87, 87)     # rojo/coral para el "VS" y el CTA
TEXT_COLOR = (245, 245, 245)
 
 
# ------------------------------------------------------------------ #
# PLAN A / PLAN B para los DATOS
# ------------------------------------------------------------------ #
def get_albums(force_sample: bool) -> List[Dict[str, Any]]:
    if not force_sample:
        try:
            from lastfm_client import LastfmClient
            from fetch_trending import collect_trending_albums
 
            print("[datos] Intentando obtener álbumes en tendencia vía Last.fm API...")
            client = LastfmClient()  # lanza LastfmAPIError si falta LASTFM_API_KEY
            albums = collect_trending_albums(client, ["Mexico", "Argentina", "Colombia", "Chile"], top_n=2)
            if albums:
                print(f"[datos] OK — {len(albums)} álbumes obtenidos de Last.fm en vivo.")
                return albums
            print("[datos] Last.fm no devolvió álbumes, se usa el respaldo de ejemplo.")
        except Exception as exc:  # noqa: BLE001 - cualquier falla cae al plan B
            print(f"[datos] No se pudo usar Last.fm en vivo ({exc}). Se usa el respaldo de ejemplo.")
 
    print("[datos] Usando datos de EJEMPLO (data/sample/trending_albums_sample.json).")
    return _load_albums(SAMPLE_DATA_PATH)
 
 
def get_top10_posts(force_sample: bool) -> List[Dict[str, Any]]:
    """
    Devuelve una lista con UN solo post "Top 10 LatAm" (ranking combinado
    de varios países, ver generate_top10.build_top10_latam), en la forma
    que espera local_render_client.render_top10_image / generate_local_top10_image:
    {country_param, country_name, accent_primary, accent_secondary,
     featured_cover_url, items}. Se mantiene como lista (de 1 elemento) para
    no tener que tocar el resto del loop de main() que itera "posts".
    """
    if not force_sample:
        try:
            from lastfm_client import LastfmClient
            from generate_top10 import build_top10_latam
 
            print("[datos] Intentando obtener el Top 10 LatAm vía Last.fm API...")
            client = LastfmClient()
            post = build_top10_latam(client, ["Mexico", "Argentina", "Colombia", "Chile"], top_n=10)
            if post:
                print("[datos] OK — Top 10 LatAm obtenido de Last.fm en vivo.")
                return [post]
            print("[datos] Last.fm no devolvió el Top 10 LatAm, se usa el respaldo de ejemplo.")
        except Exception as exc:  # noqa: BLE001 - cualquier falla cae al plan B
            print(f"[datos] No se pudo usar Last.fm en vivo para el Top 10 LatAm ({exc}). Se usa el respaldo de ejemplo.")
 
    print("[datos] Usando Top 10 de EJEMPLO.")
    if os.path.exists(SAMPLE_TOP10_PATH):
        try:
            with open(SAMPLE_TOP10_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Soporta tanto el shape viejo ({"posts": [un post por país]})
            # como un JSON con el shape nuevo de un solo post LatAm — así
            # no truena ni si el archivo todavía no se actualizó.
            if isinstance(data, dict) and "posts" in data:
                return data["posts"]
            return [data]
        except Exception as exc:  # noqa: BLE001 - si el archivo está corrupto/desactualizado, cae al fallback embebido
            print(f"[datos] No se pudo leer {SAMPLE_TOP10_PATH} ({exc}); se usa el fallback embebido en el código.")
    else:
        print(f"[datos] No existe {SAMPLE_TOP10_PATH}; se usa el fallback embebido en el código.")
 
    return [FALLBACK_TOP10_LATAM]
 
 
# ------------------------------------------------------------------ #
# PLAN A / PLAN B para la IMAGEN
# ------------------------------------------------------------------ #
def _try_local_render(
    album_a: Dict[str, Any], album_b: Dict[str, Any], dest_path: str, template_name: Optional[str] = None
) -> bool:
    """Intenta generar la imagen con el motor HTML/CSS + Playwright. True si tuvo éxito."""
    try:
        from local_render_client import LocalRenderClient
 
        with LocalRenderClient() as client:
            if template_name:
                client.render_duel_image(album_a, album_b, dest_path, template_name=template_name)
            else:
                client.render_duel_image(album_a, album_b, dest_path)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [imagen] Render local no disponible ({exc}). Se usa el generador Pillow.")
        return False
 
 
def _try_local_render_top10(post: Dict[str, Any], dest_path: str) -> bool:
    """Igual que _try_local_render, pero para el post 'Top 10 LatAm'."""
    try:
        from local_render_client import LocalRenderClient
 
        with LocalRenderClient() as client:
            client.render_top10_image(
                country_name=post["country_name"],
                accent_primary=post["accent_primary"],
                accent_secondary=post["accent_secondary"],
                featured_cover_url=post["featured_cover_url"],
                items=post["items"],
                dest_path=dest_path,
            )
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [imagen] Render local no disponible ({exc}). Se usa el generador Pillow.")
        return False
 
 
def _load_font(size: int):
    """Busca una fuente TTF común en el sistema; si no encuentra ninguna, usa la default de Pillow."""
    from PIL import ImageFont
 
    candidate_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()
 
 
def _fetch_cover_image(url: str, size: int):
    """Descarga la carátula; si falla (sin internet, URL rota), devuelve un cuadro sólido de relleno."""
    from PIL import Image
    import io
 
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        return img.resize((size, size))
    except Exception:  # noqa: BLE001
        placeholder = Image.new("RGB", (size, size), (60, 60, 68))
        return placeholder
 
 
def _wrap_and_center_text(draw, text: str, font, max_width: int, x_center: int, y: int, fill):
    """Dibuja texto centrado, partiéndolo en varias líneas si es muy largo."""
    lines = textwrap.wrap(text, width=18) or [text]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        draw.text((x_center - line_width / 2, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + 10
    return y
 
 
def generate_local_duel_image(album_a: Dict[str, Any], album_b: Dict[str, Any], dest_path: str) -> None:
    """
    Genera localmente (sin ninguna API externa de diseño) una versión funcional
    de la imagen "Álbum A vs B", usando Pillow. Es el respaldo de última
    instancia del demo: SIEMPRE puede correr, incluso sin internet
    (usa cuadros de color si no logra descargar las carátulas).
    """
    from PIL import Image, ImageDraw
 
    width, height = CANVAS_SIZE
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
 
    cover_size = 420
    margin_top = 280
 
    cover_a = _fetch_cover_image(album_a["cover_url"], cover_size)
    cover_b = _fetch_cover_image(album_b["cover_url"], cover_size)
    img.paste(cover_a, (width // 2 - cover_size - 30, margin_top))
    img.paste(cover_b, (width // 2 + 30, margin_top))
 
    font_question = _load_font(58)
    font_vs = _load_font(90)
    font_name = _load_font(34)
    font_artist = _load_font(26)
    font_cta = _load_font(30)
 
    _wrap_and_center_text(
        draw, "¿CUÁL FUE MEJOR?", font_question, width - 100, width // 2, 100, TEXT_COLOR
    )
 
    vs_bbox = draw.textbbox((0, 0), "VS", font=font_vs)
    vs_w, vs_h = vs_bbox[2] - vs_bbox[0], vs_bbox[3] - vs_bbox[1]
    draw.text(
        (width // 2 - vs_w / 2, margin_top + cover_size / 2 - vs_h / 2),
        "VS",
        font=font_vs,
        fill=ACCENT_COLOR,
    )
 
    name_y = margin_top + cover_size + 40
    _wrap_and_center_text(
        draw, album_a["name"], font_name, cover_size, width // 2 - cover_size // 2 - 30, name_y, TEXT_COLOR
    )
    _wrap_and_center_text(
        draw, ", ".join(album_a["artists"]), font_artist, cover_size,
        width // 2 - cover_size // 2 - 30, name_y + 90, (200, 200, 200),
    )
    _wrap_and_center_text(
        draw, album_b["name"], font_name, cover_size, width // 2 + cover_size // 2 + 30, name_y, TEXT_COLOR
    )
    _wrap_and_center_text(
        draw, ", ".join(album_b["artists"]), font_artist, cover_size,
        width // 2 + cover_size // 2 + 30, name_y + 90, (200, 200, 200),
    )
 
    cta = "Vota tú en Vinylr — el Letterboxd de la música"
    cta_bbox = draw.textbbox((0, 0), cta, font=font_cta)
    draw.text(
        (width // 2 - (cta_bbox[2] - cta_bbox[0]) / 2, height - 160),
        cta,
        font=font_cta,
        fill=ACCENT_COLOR,
    )
 
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    img.save(dest_path, "PNG")
 
 
def generate_local_top10_image(post: Dict[str, Any], dest_path: str) -> None:
    """
    Respaldo con Pillow para el post 'Top 10 LatAm', equivalente en
    espíritu a generate_local_duel_image: nunca falla, aunque se vea más
    simple que el render HTML/CSS real.
    """
    from PIL import Image, ImageDraw
 
    width, height = CANVAS_SIZE
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
 
    font_title = _load_font(64)
    font_tag = _load_font(40)
    font_rank = _load_font(22)
    font_artist = _load_font(20)
    font_title_track = _load_font(17)
    font_cta = _load_font(24)
 
    accent = tuple(int(post.get("accent_primary", "#E63946").lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
 
    draw.text((72, 60), post["country_name"].upper(), font=font_title, fill=TEXT_COLOR)
    draw.text((72, 140), "TOP 10", font=font_tag, fill=(120, 120, 120))
    draw.rectangle([72, 210, 72 + 160, 214], fill=accent)
 
    cover_size = 200
    cover = _fetch_cover_image(post.get("featured_cover_url", ""), cover_size)
    img.paste(cover, (width - 72 - cover_size, 240))
 
    y = 260
    for item in post["items"]:
        line = f"{item['rank']:02d}  {item['artist'].upper()} — {item['title']}"
        draw.text((72, y), f"{item['rank']:02d}", font=font_rank, fill=(150, 150, 150))
        draw.text((120, y), item["artist"].upper(), font=font_artist, fill=TEXT_COLOR)
        draw.text((120, y + 26), item["title"], font=font_title_track, fill=(160, 160, 160))
        y += 62
        if y > height - 140:
            break  # no seguir dibujando si ya no cabe en el lienzo
 
    cta = "VINYLR — EL LETTERBOXD DE LA MÚSICA"
    draw.text((72, height - 60), cta, font=font_cta, fill=ACCENT_COLOR)
 
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    img.save(dest_path, "PNG")
 
 
# ------------------------------------------------------------------ #
# Orquestador principal
# ------------------------------------------------------------------ #
def main():
    parser = argparse.ArgumentParser(
        description="Demo on-demand: genera los 2 duelos VS (Lunes y Viernes) sin importar el estado de tus credenciales/internet."
    )
    parser.add_argument(
        "--force-sample",
        action="store_true",
        help="Ignora Spotify aunque haya credenciales configuradas; usa siempre los datos de ejemplo.",
    )
    parser.add_argument(
        "--with-reels",
        action="store_true",
        help="Además de las imágenes, genera el Reel (.mp4) de cada pieza con Remotion (ver remotion-reels/).",
    )
    parser.add_argument(
        "--posts-only",
        action="store_true",
        help="Genera SOLO las imágenes (posts), sin video — esto ya es el default; existe como alias explícito y gana si se combina con --with-reels/--reels-only por error.",
    )
    parser.add_argument(
        "--reels-only",
        action="store_true",
        help="Genera SOLO los videos (Reels), sin crear las imágenes. Implica --with-reels.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Prueba rápida para mostrar en el momento: genera SOLO 1 duelo (imagen + video), "
            "sin el resto de duelos ni el Top 10. Implica --with-reels."
        ),
    )
    args = parser.parse_args()
    if args.quick:
        args.with_reels = True
    if args.reels_only:
        args.with_reels = True
    if args.posts_only:
        args.with_reels = False  # gana al final: "solo posts" es explícito e inequívoco
 
    skip_images = args.reels_only and not args.posts_only
 
    reels_ready = False
    if args.with_reels:
        try:
            from render_reel import remotion_ready
 
            reels_ready = remotion_ready()
            if not reels_ready:
                print(
                    "[reels] Node.js/dependencias no están listos todavía. Setup: "
                    "cd remotion-reels && npm install\n"
                )
        except Exception as exc:  # noqa: BLE001 - --with-reels nunca debe tumbar el demo de imágenes
            print(f"[reels] No se pudo preparar el módulo de video ({exc}).\n")
 
    if skip_images and not reels_ready:
        print("--reels-only pedido, pero el módulo de video no está listo — no se generaría nada. Abortando.")
        sys.exit(1)
 
    print("=" * 60)
    print("  VINYLR CONTENT ENGINE — DEMO")
    print("=" * 60)
 
    albums = get_albums(force_sample=args.force_sample)
    duels = build_duels(albums)
 
    if not duels:
        print("No se pudieron armar duelos ni siquiera con los datos de ejemplo. Algo está mal.")
        sys.exit(1)
 
    if args.quick:
        duels = duels[:1]  # solo el primer duelo — nada de correr los demás ni el Top 10
 
    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "data", "demo_output", datetime.now().strftime("%Y-%m-%d_%H%M%S")
    )
 
    if args.quick:
        print(f"\n[quick] Generando SOLO 1 duelo (imagen + video) en: {output_dir}\n")
    else:
        print(f"\nSe generarán {len(duels)} duelo(s) + el Top 10 LatAm en: {output_dir}\n")
 
    for duel in duels:
        a, b = duel["album_a"], duel["album_b"]
        print(f"--- Duelo [{duel['type']}] {duel['label']}: {a['name']} vs {b['name']} ---")
 
        if not skip_images:
            dest_path = os.path.join(output_dir, f"duelo_{duel['label']}.png")
            used_local_render = _try_local_render(a, b, dest_path, template_name=duel.get("template"))
            if not used_local_render:
                print("  [imagen] Generando versión con Pillow (respaldo garantizado)...")
                generate_local_duel_image(a, b, dest_path)
            print(f"  -> Imagen lista: {dest_path}\n")
 
        if reels_ready:
            from render_reel import render_duel_video
 
            video_path = os.path.join(output_dir, f"reel_duelo_{duel['label']}.mp4")
            print("  [reel] Renderizando video con Remotion (puede tardar) ...")
            if render_duel_video(a, b, video_path, exit_on_missing_deps=False):
                print(f"  -> Reel listo: {video_path}\n")
            elif not skip_images:
                print("  -> No se generó el reel de este duelo (ver aviso arriba); la imagen sigue disponible.\n")
            else:
                print("  -> No se generó el reel de este duelo (ver aviso arriba).\n")
 
    if args.quick:
        top10_posts: List[Dict[str, Any]] = []
        print("[quick] Se omite el Top 10 (solo se pidió 1 duelo).\n")
    else:
        print("--- Generando el post 'Top 10 LatAm' ---\n")
        top10_posts = get_top10_posts(force_sample=args.force_sample)
    for post in top10_posts:
        print(f"--- Top 10 {post['country_name']} ({len(post['items'])} canciones) ---")
 
        if not skip_images:
            dest_path = os.path.join(output_dir, f"top10_{post['country_param'].lower()}.png")
            used_local_render = _try_local_render_top10(post, dest_path)
            if not used_local_render:
                print("  [imagen] Generando versión con Pillow (respaldo garantizado)...")
                generate_local_top10_image(post, dest_path)
            print(f"  -> Imagen lista: {dest_path}\n")
 
        if reels_ready:
            from render_reel import render_top10_video
 
            video_path = os.path.join(output_dir, f"reel_top10_{post['country_param'].lower()}.mp4")
            print("  [reel] Renderizando video con Remotion (puede tardar) ...")
            if render_top10_video(post, video_path, exit_on_missing_deps=False):
                print(f"  -> Reel listo: {video_path}\n")
            elif not skip_images:
                print("  -> No se generó el reel de este Top 10 (ver aviso arriba); la imagen sigue disponible.\n")
            else:
                print("  -> No se generó el reel de este Top 10 (ver aviso arriba).\n")
 
    total_pieces = len(duels) + len(top10_posts)
 
    print("=" * 60)
    if skip_images:
        print(f"LISTO. Abre la carpeta para ver los {total_pieces} Reel(s) generado(s):")
    elif args.with_reels:
        print(f"LISTO. Abre la carpeta para ver las {total_pieces} imágenes (+ Reels) generadas:")
    else:
        print(f"LISTO. Abre la carpeta para ver las {total_pieces} imágenes generadas:")
    print(f"  {os.path.abspath(output_dir)}")
    if args.with_reels and not reels_ready:
        print("  (sin Reels: falta 'cd remotion-reels && npm install')")
    print("=" * 60)
 
 
if __name__ == "__main__":
    main()
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 


