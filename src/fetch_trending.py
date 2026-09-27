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
2. Para cada país, resuelve la canción mejor posicionada que tenga álbum
   registrado en Last.fm (vía `track.getinfo`) — Last.fm no da álbumes
   directamente por país, así que hay que llegar a ellos por canción.
3. Devuelve UN álbum representativo por país (no un ranking global
   mezclado), en el mismo orden en que se pasaron los países — para que
   cada país quede representado y los duelos no terminen dominados por
   un solo mercado.

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
    client: LastfmClient, countries: List[str], top_n: int = 2
) -> List[Dict[str, Any]]:
    """
    Devuelve hasta `top_n` álbumes por país (por defecto 2: el #1 y el #2 en
    tendencia), cada uno etiquetado con `country` y `rank`. Ya no arma un
    ranking global mezclado entre países — cada país se resuelve por
    separado, para poder armar tanto duelos intra-país (#1 vs #2 del mismo
    país) como duelos cruzados entre países específicos (ver
    generate_duels.py, Iteración 29).
    """
    results: List[Dict[str, Any]] = []

    for country in countries:
        print(f"Descargando top tracks de {country}...")
        try:
            tracks = client.get_geo_top_tracks(country, limit=50)
        except Exception as exc:  # noqa: BLE001 - seguimos con los demás países
            print(f"[error] Falló geo.gettoptracks de {country}: {exc}")
            continue

        found_for_country: List[Dict[str, Any]] = []
        seen_keys = set()

        for position, track in enumerate(tracks[:TRACKS_TO_RESOLVE_PER_COUNTRY]):
            if len(found_for_country) >= top_n:
                break

            artist_name = track.get("artist", {}).get("name") or track.get("artist", {}).get("#text")
            track_name = track.get("name")
            if not artist_name or not track_name:
                continue

            info = client.get_track_info(artist_name, track_name)
            if not info or not info.get("album_name"):
                continue  # esta canción no tiene álbum registrado en Last.fm

            key = _album_key(info["album_name"], info["artist"])
            if key in seen_keys:
                continue  # no repetir el mismo álbum dos veces para el mismo país
            seen_keys.add(key)

            position_score = max(0.0, (50 - position) / 50 * 3.0)
            found_for_country.append(
                {
                    "id": key,
                    "name": info["album_name"],
                    "artists": [info["artist"]],
                    "release_date": None,  # Last.fm no da esto en este flujo
                    "cover_url": info["cover_url"],
                    "source_url": info.get("url"),
                    "country": country,
                    "rank": len(found_for_country) + 1,
                    "trend_score": round(position_score, 2),
                    "sources": [f"lastfm_top_{country.lower()}"],
                }
            )

        if found_for_country:
            results.extend(found_for_country)
        else:
            print(f"[aviso] No se encontró ningún álbum resoluble para {country}, se omite.")

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
        "--top", type=int, default=2, help="Cuántos álbumes traer POR PAÍS (default: 2, para armar el duelo #1 vs #2)."
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
