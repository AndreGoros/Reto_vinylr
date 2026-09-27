"""
generate_top10.py
------------------
Arma el post "Top 10 LatAm" (ver `src/templates/top10_template.html.j2`):
UN SOLO ranking combinado de canciones en tendencia across los países
pedidos, no uno separado por país.
 
Por qué un ranking combinado y no uno por país:
- El usuario decidió que el formato "Top 10" represente a LatAm como
  región (identidad "Latam-first" de Vinylr), no fragmentado país por
  país — eso ya lo cubren los duelos intra-país (generate_duels.py).
- Una canción que aparece en el top de VARIOS países pesa más en el
  ranking combinado que una que solo es fuerte en uno — es una señal más
  fiel de qué está sonando de verdad en toda la región, no solo en un
  mercado.
 
Cómo se combina (mismo patrón de scoring que fetch_trending.py usó para
álbumes en la Iteración 26-28, aplicado aquí a canciones):
    Para cada país, se pide su top 50 (geo.gettoptracks). Cada canción
    suma un puntaje según su posición (1er lugar pesa más que el puesto
    50). Los puntajes de una misma canción se SUMAN entre países, así que
    aparecer en el top de 2+ países la empuja hacia arriba en el ranking
    LatAm. Se toman las top `top_n` canciones por puntaje combinado.
 
Solo se resuelve el álbum/carátula de la canción #1 (una sola llamada
extra a `track.getinfo`), para tener una imagen destacada; las posiciones
2-10 se muestran como texto (artista + título), tal como espera
`top10_template.html.j2`.
 
Como en `generate_duels.py`, este script NO publica nada — solo deja la
imagen + su metadata en `data/generated/<fecha>/` para revisión humana.
 
Uso:
    python src/generate_top10.py
    python src/generate_top10.py --countries Mexico Argentina --top 10
"""
 
import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
 
from dotenv import load_dotenv
 
from lastfm_client import LastfmClient
from local_render_client import LocalRenderClient, LocalRenderError
 
load_dotenv()  # Carga variables de .env sin depender de que el terminal/IDE lo haga por su cuenta.
 
# Identidad visual del post LatAm (no es de un país en particular, así que
# no se usa la tabla de acentos por país de los duelos).
LATAM_ACCENT_PRIMARY = "#4263FF"
LATAM_ACCENT_SECONDARY = "#FF3B7A"
 
TRACKS_PER_COUNTRY = 50  # cuántas posiciones del top de cada país se consideran para el ranking combinado
 
 
def _track_key(artist: str, title: str) -> str:
    return f"{artist.strip().lower()}::{title.strip().lower()}"
 
 
def _resolve_featured_cover(client: LastfmClient, artist: str, track: str) -> str:
    """
    Intenta conseguir la carátula del álbum de la canción #1, para el
    recorte destacado de la imagen. Si Last.fm no tiene álbum registrado
    para esta canción, devuelve "" — el template ya oculta el <img> con
    onerror si la URL viene vacía o rota, así que nunca rompe el layout.
    """
    info = client.get_track_info(artist, track)
    if not info or not info.get("cover_url"):
        return ""
    return info["cover_url"]
 
 
def build_top10_latam(
    client: LastfmClient, countries: List[str], top_n: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Arma el ranking combinado LatAm. Devuelve None si NINGÚN país devolvió
    canciones utilizables (ej. sin conexión, API caída, etc.) — quien
    llama (demo.py, main() de este archivo) decide qué hacer en ese caso
    (típicamente caer al respaldo de ejemplo).
    """
    scores: Dict[str, float] = {}
    track_data: Dict[str, Dict[str, str]] = {}
 
    for country in countries:
        print(f"Descargando top tracks de {country} para el ranking LatAm...")
        try:
            tracks = client.get_geo_top_tracks(country, limit=TRACKS_PER_COUNTRY)
        except Exception as exc:  # noqa: BLE001 - seguimos con el siguiente país
            print(f"[error] Falló geo.gettoptracks de {country}: {exc}")
            continue
 
        for position, track in enumerate(tracks):
            artist_name = track.get("artist", {}).get("name") or track.get("artist", {}).get("#text")
            track_name = track.get("name")
            if not artist_name or not track_name:
                continue
 
            key = _track_key(artist_name, track_name)
            position_score = max(0.0, (TRACKS_PER_COUNTRY - position) / TRACKS_PER_COUNTRY * 3.0)
            scores[key] = scores.get(key, 0.0) + position_score
 
            if key not in track_data:
                track_data[key] = {"artist": artist_name, "title": track_name}
 
    if not scores:
        print("[aviso] Ningún país devolvió tracks utilizables, no se pudo armar el ranking LatAm.")
        return None
 
    ranked_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:top_n]
 
    items: List[Dict[str, Any]] = []
    for i, key in enumerate(ranked_keys, start=1):
        data = track_data[key]
        items.append({"rank": i, "artist": data["artist"], "title": data["title"]})
 
    if not items:
        print("[aviso] No se pudo armar el ranking LatAm (0 canciones tras el scoring).")
        return None
 
    featured_cover_url = _resolve_featured_cover(client, items[0]["artist"], items[0]["title"])
    if not featured_cover_url:
        print("  [aviso] Sin carátula resoluble para el #1 del ranking LatAm; la imagen sale sin cover destacado.")
 
    return {
        "country_param": "latam",
        "country_name": "LatAm",
        "items": items,
        "featured_cover_url": featured_cover_url,
        "accent_primary": LATAM_ACCENT_PRIMARY,
        "accent_secondary": LATAM_ACCENT_SECONDARY,
    }
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Genera la imagen 'Top 10 LatAm' a partir de las canciones en tendencia de varios países de Last.fm."
    )
    parser.add_argument(
        "--top", type=int, default=10, help="Cuántas canciones incluir en el ranking combinado (default: 10)."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=["Mexico", "Argentina", "Colombia", "Chile"],
        help="Países cuyo top se combina en el ranking LatAm (default: Mexico Argentina Colombia Chile).",
    )
    default_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    parser.add_argument("--data-dir", default=default_data_dir)
    args = parser.parse_args()
 
    client = LastfmClient()
    post = build_top10_latam(client, args.countries, args.top)
 
    if not post:
        print("No se pudo armar el ranking LatAm. Revisa tu LASTFM_API_KEY y los países pedidos.")
        return
 
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(args.data_dir, "generated", today)
    os.makedirs(output_dir, exist_ok=True)
 
    image_path = os.path.join(output_dir, "top10_latam.png")
    manifest = {"generated_at": datetime.now().isoformat(), "post": None}
 
    print(f"Generando Top 10 LatAm ({len(post['items'])} canciones)...")
    try:
        with LocalRenderClient() as render_client:
            render_client.render_top10_image(
                country_name=post["country_name"],
                accent_primary=post["accent_primary"],
                accent_secondary=post["accent_secondary"],
                featured_cover_url=post["featured_cover_url"],
                items=post["items"],
                dest_path=image_path,
            )
        status = "generado_pendiente_revision"
        print(f"  -> Guardado en {image_path}")
    except LocalRenderError as exc:
        image_path = None
        status = f"error: {exc}"
        print(f"  -> [ERROR] {exc}")
 
    manifest["post"] = {
        "country_name": post["country_name"],
        "items": post["items"],
        "image_path": image_path,
        "status": status,
    }
 
    manifest_path = os.path.join(output_dir, "manifest_top10.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
 
    print(f"\nListo. Revisa la imagen y el manifest en: {output_dir}")
    print("Recuerda: NADA se publica automáticamente — la revisión humana decide.")
 
 
if __name__ == "__main__":
    main()
 
