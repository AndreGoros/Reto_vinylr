"""
lastfm_client.py
-----------------
Cliente para la API de Last.fm (https://www.last.fm/api), usado como
reemplazo de Spotify para detectar álbumes en tendencia por país.
 
Por qué el cambio (ver PROGRESS.md, Iteración 26-27): Spotify empezó a
devolver 403 Forbidden en los endpoints de contenido editorial
(playlists "Top 50", new-releases) para apps nuevas en "Development Mode" —
es una restricción de plataforma, no algo que dependa de nuestro código.
Last.fm no tiene ese tipo de restricción: solo pide una API key gratuita,
sin OAuth ni flujo de tokens.
 
Autenticación: se obtiene una API key gratis en
https://www.last.fm/api/account/create — no requiere Client Secret.
 
Documentación oficial de los métodos usados aquí:
https://www.last.fm/api/show/geo.getTopTracks
https://www.last.fm/api/show/track.getInfo
"""
 
import os
import time
from typing import Any, Dict, List, Optional
 
import requests
 
API_BASE = "https://ws.audioscrobbler.com/2.0/"
 
 
class LastfmAPIError(Exception):
    """Error genérico al llamar a la API de Last.fm."""
 
 
class LastfmClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LASTFM_API_KEY")
        if not self.api_key:
            raise LastfmAPIError(
                "Falta LASTFM_API_KEY como variable de entorno (ver .env.example). "
                "Se obtiene gratis en https://www.last.fm/api/account/create"
            )
 
    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "api_key": self.api_key, "format": "json"}
        response = requests.get(API_BASE, params=params, timeout=15)
 
        if response.status_code == 429:
            time.sleep(1)
            response = requests.get(API_BASE, params=params, timeout=15)
 
        if response.status_code != 200:
            raise LastfmAPIError(
                f"Error en Last.fm (status {response.status_code}): {response.text}"
            )
 
        data = response.json()
        if "error" in data:
            raise LastfmAPIError(f"Last.fm devolvió error: {data.get('message', data)}")
 
        return data
 
    def get_geo_top_tracks(self, country: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Top canciones por país (por scrobbles/escuchas), método `geo.gettoptracks`.
        `country` debe ser el nombre completo del país en inglés (ej. "Mexico",
        no "MX") — es como Last.fm espera este parámetro.
        """
        data = self._get(
            {"method": "geo.gettoptracks", "country": country, "limit": limit}
        )
        tracks = data.get("tracks", {}).get("track", [])
        return tracks if isinstance(tracks, list) else [tracks]
 
    def get_track_info(self, artist: str, track: str) -> Optional[Dict[str, Any]]:
        """
        Detalle de una canción, incluyendo el álbum al que pertenece (si Last.fm
        lo tiene registrado) — necesario porque `geo.gettoptracks` no incluye álbum.
        Devuelve None si Last.fm no tiene información de álbum para esta canción.
        """
        try:
            data = self._get({"method": "track.getinfo", "artist": artist, "track": track})
        except LastfmAPIError:
            return None
 
        track_data = data.get("track", {})
        album = track_data.get("album")
        if not album:
            return None
 
        images = album.get("image", [])
        # Last.fm devuelve varias resoluciones; tomamos la más grande disponible.
        cover_url = None
        for img in images:
            if img.get("#text"):
                cover_url = img["#text"]
        if not cover_url:
            return None  # sin carátula no nos sirve para el duelo visual
 
        try:
            listeners = int(track_data.get("listeners", 0))
        except (TypeError, ValueError):
            listeners = 0
 
        return {
            "album_name": album.get("title"),
            "artist": album.get("artist", artist),
            "cover_url": cover_url,
            "url": album.get("url"),
            "listeners": listeners,
        }
 
