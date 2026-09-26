"""
fetch_trending.py
------------------
Etapa 1 del pipeline: obtiene álbumes en tendencia en LatAm.

NOTA (Iteración 27): este script usaba Spotify API, pero Spotify empezó a
devolver 403 Forbidden en los endpoints de contenido editorial para apps
nuevas en "Development Mode" (ver PROGRESS.md, Iteración 26). Se migró a
Last.fm API, que no tiene esa restricción. El esquema del JSON de salida
se mantuvo igual a propósito, para que `generate_duels.py` y `demo.py`
sigan funcionando sin cambios.

Qué hace:
1. Para cada país de LatAm, pide las canciones más escuchadas (`geo.gettoptracks`).
2. Para cada canción (hasta un límite, para no saturar la API), resuelve su
   álbum vía `track.getinfo` — Last.fm no da álbumes directamente por país.
3. Agrega por álbum (cuenta cuántas canciones distintas de ese álbum aparecen
   en el top, ponderado por posición), deduplica, y guarda el top N.

Uso:
    python src/fetch_trending.py --top 5 --countries Mexico Argentina Colombia Chile
"""

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

from lastfm_client import LastfmClient

load_dotenv()  # Carga variables de .env sin depender de que el terminal/IDE lo haga por su cuenta.

# Cuántas canciones del top de cada país se intentan resolver a álbum.
# Cada una es una llamada extra a la API (track.getinfo), así que se limita
# para no hacer decenas de requests innecesarios por país.
TRACKS_TO_RESOLVE_PER_COUNTRY = 20


def _album_key(album_name: str, artist: str) -> str:
    return f"{artist.strip().lower()}::{album_name.strip().lower()}"


def collect_trending_albums(
    client: LastfmClient, countries: List[str], top_n: int
) -> List[Dict[str, Any]]:
    scores: Dict[str, float] = {}
    album_data: Dict[str, Dict[str, Any]] = {}
    sources: Dict[str, List[str]] = {}

    for country in countries:
        print(f"Descargando top tracks de {country}...")
        try:
            tracks = client.get_geo_top_tracks(country, limit=50)
        except Exception as exc:  # noqa: BLE001 - seguimos con los demás países
            print(f"[error] Falló geo.gettoptracks de {country}: {exc}")
            continue

        for position, track in enumerate(tracks[:TRACKS_TO_RESOLVE_PER_COUNTRY]):
            artist_name = track.get("artist", {}).get("name") or track.get("artist", {}).get("#text")
            track_name = track.get("name")
            if not artist_name or not track_name:
                continue

            info = client.get_track_info(artist_name, track_name)
            if not info or not info.get("album_name"):
                continue  # esta canción no tiene álbum registrado en Last.fm

            key = _album_key(info["album_name"], info["artist"])
            position_score = max(0.0, (50 - position) / 50 * 3.0)
            scores[key] = scores.get(key, 0.0) + position_score

            if key not in album_data:
                album_data[key] = {
                    "id": key,
                    "name": info["album_name"],
                    "artists": [info["artist"]],
                    "release_date": None,  # Last.fm no da esto en este flujo
                    "cover_url": info["cover_url"],
                    "source_url": info.get("url"),
                }
            sources.setdefault(key, []).append(f"lastfm_top_{country.lower()}")

    ranked_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    results = []
    for key in ranked_keys[:top_n]:
        entry = dict(album_data[key])
        entry["trend_score"] = round(scores[key], 2)
        entry["sources"] = sorted(set(sources.get(key, [])))
        results.append(entry)

    return results


def save_results(results: List[Dict[str, Any]], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"trending_albums_{datetime.now().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(output_dir, filename)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "source": "lastfm",
        "count": len(results),
        "albums": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Obtiene álbumes en tendencia en LatAm vía Last.fm API."
    )
    parser.add_argument(
        "--top", type=int, default=5, help="Cuántos álbumes top devolver (default: 5)."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=["Mexico", "Argentina", "Colombia", "Chile"],
        help="Nombres de país en inglés, como los espera Last.fm (default: Mexico Argentina Colombia Chile).",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data"),
        help="Carpeta donde guardar el JSON resultante.",
    )
    args = parser.parse_args()

    client = LastfmClient()
    results = collect_trending_albums(client, args.countries, args.top)

    if not results:
        print("No se obtuvo ningún álbum. Revisa tu LASTFM_API_KEY.")
        return

    filepath = save_results(results, args.output_dir)
    print(f"\nListo. {len(results)} álbumes guardados en: {filepath}\n")
    for i, album in enumerate(results, start=1):
        artists = ", ".join(album["artists"])
        print(f"{i}. {album['name']} — {artists} (score: {album['trend_score']})")


if __name__ == "__main__":
    main()
