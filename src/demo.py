"""
demo.py
-------
Comando único para DEMOSTRAR el concepto de Vinylr Content Engine en
cualquier momento: genera las 2 imágenes "Álbum A vs B" (Lunes y Viernes)
sin importar si ya tienes las credenciales de Spotify/APITemplate.io
configuradas, ni si hay conexión a internet en ese momento.

Estrategia de "nunca falla" (importante para poder hacer la demo en vivo
frente a jueces sin depender de que todo esté perfectamente configurado):

    Datos de álbumes:
        1) Intenta Spotify API real (si hay credenciales) → PLAN A
        2) Si falla o no hay credenciales → usa data/sample/... → PLAN B

    Imagen del duelo:
        1) Intenta APITemplate.io real (si hay credenciales/plantilla) → PLAN A
        2) Si falla o no hay credenciales → genera la imagen localmente
           con Pillow (más simple visualmente, pero funcional) → PLAN B

Uso:
    python src/demo.py
    python src/demo.py --force-sample      # fuerza el modo 100% offline/ejemplo
"""

import argparse
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

CANVAS_SIZE = (1080, 1920)
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


# ------------------------------------------------------------------ #
# PLAN A / PLAN B para la IMAGEN
# ------------------------------------------------------------------ #
def _try_real_template(
    album_a: Dict[str, Any], album_b: Dict[str, Any], dest_path: str, template_env_var: str
) -> bool:
    """Intenta generar la imagen con APITemplate.io. Devuelve True si tuvo éxito."""
    try:
        from template_client import TemplateClient

        client = TemplateClient()  # lanza TemplateAPIError si falta la API key
        template_id = os.environ.get(template_env_var)
        if not template_id:
            print(f"  [imagen] Falta {template_env_var} en .env. Se usa el generador local.")
            return False
        url = client.create_duel_image(album_a, album_b, template_id=template_id)
        client.download_image(url, dest_path)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [imagen] APITemplate.io no disponible ({exc}). Se usa el generador local.")
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
    margin_top = 260

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
    args = parser.parse_args()

    print("=" * 60)
    print("  VINYLR CONTENT ENGINE — DEMO")
    print("=" * 60)

    albums = get_albums(force_sample=args.force_sample)
    duels = build_duels(albums)

    if not duels:
        print("No se pudieron armar duelos ni siquiera con los datos de ejemplo. Algo está mal.")
        sys.exit(1)

    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "data", "demo_output", datetime.now().strftime("%Y-%m-%d_%H%M%S")
    )

    print(f"\nSe generarán {len(duels)} duelo(s) en: {output_dir}\n")

    for duel in duels:
        a, b = duel["album_a"], duel["album_b"]
        print(f"--- Duelo [{duel['type']}] {duel['label']}: {a['name']} vs {b['name']} ---")
        dest_path = os.path.join(output_dir, f"duelo_{duel['label']}.png")

        used_real_api = _try_real_template(a, b, dest_path, duel["template_env_var"])
        if not used_real_api:
            print("  [imagen] Generando versión local con Pillow (respaldo garantizado)...")
            generate_local_duel_image(a, b, dest_path)

        print(f"  -> Imagen lista: {dest_path}\n")

    print("=" * 60)
    print(f"LISTO. Abre la carpeta para ver las {len(duels)} imágenes generadas:")
    print(f"  {os.path.abspath(output_dir)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
