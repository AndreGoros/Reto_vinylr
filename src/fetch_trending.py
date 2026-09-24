"""
fetch_trending.py
------------------
Script principal de la Etapa 1 (Detección de tendencias) del motor de
contenido de Vinylr.

Qué hace:
1. Recorre las playlists editoriales "Top 50" de varios países de LatAm.
2. Recorre "new releases" de esos mismos países.
3. Combina todo, deduplica por álbum, y calcula un score de tendencia simple:
      score = (apariciones en distintas playlists Top 50 del país)
              + (posición dentro de cada playlist, ponderada)
              + bonus si es lanzamiento reciente (últimos 30 días)
4. Guarda el top N resultante en data/trending_albums_<fecha>.json

Uso:
    python src/fetch_trending.py --top 8 --countries MX AR CO CL

Pensado para correrse 1 vez por semana (ej. lunes en la madrugada vía cron /
GitHub Actions) y alimentar la Etapa 2 (generación de brief creativo).
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from spotify_client import SpotifyClient

# ---------------------------------------------------------------------- #
# Playlists editoriales "Top 50" oficiales de Spotify por país (LatAm).
#
# NOTA IMPORTANTE: Spotify a veces cambia o retira IDs de playlists
# editoriales. Estos son los IDs públicos conocidos al momento de escribir
# este script. Si alguno da 404, hay que buscar el ID actualizado en
# open.spotify.com/playlist/<id> desde la playlist oficial "Top 50 - <país>".
# ---------------------------------------------------------------------- #
TOP50_PLAYLISTS = {
    "MX": "37i9dQZEVXbO3qyFxbkOE1",  # Top 50 - Mexico
    "AR": "37i9dQZEVXbMMy2roB9myp",  # Top 50 - Argentina
    "CO": "37i9dQZEVXbOa2lmxNORXQ",  # Top 50 - Colombia
    "CL": "37i9dQZEVXbL0GavIqMTeb",  # Top 50 - Chile
    "GLOBAL": "37i9dQZEVXbMDoHDwVN2tF",  # Top 50 - Global
}

RECENT_RELEASE_BONUS_DAYS = 30
RECENT_RELEASE_BONUS_POINTS = 2.0


def _album_key(album: Dict[str, Any]) -> str:
    """Usamos el ID de Spotify como llave única del álbum."""
    return album["id"]


def _normalize_album(album: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae solo los campos que nos importan para el brief creativo."""
    images = album.get("images", [])
    cover_url = images[0]["url"] if images else None
    return {
        "spotify_id": album["id"],
        "name": album["name"],
        "artists": [a["name"] for a in album.get("artists", [])],
        "release_date": album.get("release_date"),
        "cover_url": cover_url,
        "spotify_url": album.get("external_urls", {}).get("spotify"),
    }


def _is_recent(release_date: str, days: int) -> bool:
    """Spotify a veces da release_date con precisión de año o año-mes."""
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(release_date, fmt)
            return parsed >= datetime.now() - timedelta(days=days)
        except (ValueError, TypeError):
            continue
    return False


def collect_trending_albums(
    client: SpotifyClient, countries: List[str], top_n: int
) -> List[Dict[str, Any]]:
    scores: Dict[str, float] = {}
    album_data: Dict[str, Dict[str, Any]] = {}
    sources: Dict[str, List[str]] = {}

    # --- 1. Top 50 playlists: posición alta = más puntos --- #
    for country in countries:
        playlist_id = TOP50_PLAYLISTS.get(country.upper())
        if not playlist_id:
            print(f"[aviso] No tengo playlist Top 50 configurada para '{country}', se omite.")
            continue

        print(f"Descargando Top 50 de {country}...")
        try:
            items = client.get_playlist_tracks(playlist_id, market=country.upper())
        except Exception as exc:  # noqa: BLE001 - queremos seguir con los demás países
            print(f"[error] Falló Top 50 de {country}: {exc}")
            continue

        for position, item in enumerate(items):
            track = item.get("track")
            if not track or not track.get("album"):
                continue
            album = track["album"]
            key = _album_key(album)

            # Posición 0 (primer lugar) vale más que posición 49.
            position_score = max(0.0, (50 - position) / 50 * 3.0)
            scores[key] = scores.get(key, 0.0) + position_score

            if key not in album_data:
                album_data[key] = _normalize_album(album)
            sources.setdefault(key, []).append(f"top50_{country.lower()}")

    # --- 2. New releases: bonus si es lanzamiento muy reciente --- #
    for country in countries:
        print(f"Descargando new releases de {country}...")
        try:
            new_releases = client.get_new_releases(country=country.upper(), limit=20)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] Falló new-releases de {country}: {exc}")
            continue

        for album in new_releases:
            key = _album_key(album)
            if key not in album_data:
                album_data[key] = _normalize_album(album)

            if _is_recent(album.get("release_date", ""), RECENT_RELEASE_BONUS_DAYS):
                scores[key] = scores.get(key, 0.0) + RECENT_RELEASE_BONUS_POINTS
                sources.setdefault(key, []).append(f"new_release_{country.lower()}")

    # --- 3. Rankear y devolver top N --- #
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
        "count": len(results),
        "albums": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Obtiene álbumes en tendencia en LatAm vía Spotify API."
    )
    parser.add_argument(
        "--top", type=int, default=5, help="Cuántos álbumes top devolver (default: 5, según el MVP)."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=["MX", "AR", "CO", "CL"],
        help="Códigos de país a considerar (default: MX AR CO CL).",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data"),
        help="Carpeta donde guardar el JSON resultante.",
    )
    args = parser.parse_args()

    client = SpotifyClient()
    results = collect_trending_albums(client, args.countries, args.top)

    if not results:
        print("No se obtuvo ningún álbum. Revisa credenciales/IDs de playlist.")
        return

    filepath = save_results(results, args.output_dir)
    print(f"\nListo. {len(results)} álbumes guardados en: {filepath}\n")
    for i, album in enumerate(results, start=1):
        artists = ", ".join(album["artists"])
        print(f"{i}. {album['name']} — {artists} (score: {album['trend_score']})")


if __name__ == "__main__":
    main()
