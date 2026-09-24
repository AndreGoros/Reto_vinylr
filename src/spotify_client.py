"""
spotify_client.py
------------------
Cliente mínimo para la Web API de Spotify usando el flujo "Client Credentials".

Este flujo NO requiere que un usuario inicie sesión: solo necesitas un
Client ID y un Client Secret de una app registrada en
https://developer.spotify.com/dashboard

Por qué Client Credentials y no Authorization Code:
- Solo vamos a leer datos públicos (playlists editoriales, new releases).
- No necesitamos acceder a datos privados de ningún usuario.
- Es el flujo más simple de automatizar en un cron semanal (sin refresh
  tokens de usuario que puedan expirar/revocarse).

Documentación oficial:
https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow
"""

import base64
import os
import time
from typing import Any, Dict, List, Optional

import requests

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


class SpotifyAuthError(Exception):
    """Error autenticando contra la API de Spotify."""


class SpotifyAPIError(Exception):
    """Error genérico al llamar a un endpoint de la API de Spotify."""


class SpotifyClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.environ.get("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("SPOTIFY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise SpotifyAuthError(
                "Faltan credenciales. Define SPOTIFY_CLIENT_ID y "
                "SPOTIFY_CLIENT_SECRET como variables de entorno (ver .env.example) "
                "o pásalas directamente al constructor."
            )

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------ #
    # Autenticación
    # ------------------------------------------------------------------ #
    def _fetch_new_token(self) -> None:
        """Pide un access token nuevo usando Client Credentials Flow."""
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=15)

        if response.status_code != 200:
            raise SpotifyAuthError(
                f"No se pudo obtener el token (status {response.status_code}): "
                f"{response.text}"
            )

        payload = response.json()
        self._access_token = payload["access_token"]
        # Restamos 60s de margen de seguridad antes de que expire de verdad.
        self._token_expires_at = time.time() + payload.get("expires_in", 3600) - 60

    def _get_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            self._fetch_new_token()
        return self._access_token  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Llamadas genéricas
    # ------------------------------------------------------------------ #
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET genérico contra la API con reintento simple si el token expiró (401)."""
        url = f"{API_BASE}{path}"
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 401:
            # Token pudo haber expirado justo en el borde; forzamos renovación una vez.
            self._access_token = None
            headers = {"Authorization": f"Bearer {self._get_token()}"}
            response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            time.sleep(retry_after)
            response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            raise SpotifyAPIError(
                f"Error en GET {path} (status {response.status_code}): {response.text}"
            )

        return response.json()

    # ------------------------------------------------------------------ #
    # Endpoints específicos que necesitamos
    # ------------------------------------------------------------------ #
    def get_playlist_tracks(self, playlist_id: str, market: str = "MX") -> List[Dict[str, Any]]:
        """
        Devuelve la lista de tracks (con su álbum embebido) de una playlist pública,
        ej. una playlist editorial "Top 50 - <país>".

        Maneja paginación (Spotify pagina de 100 en 100).
        """
        items: List[Dict[str, Any]] = []
        path = f"/playlists/{playlist_id}/tracks"
        params = {
            "market": market,
            "limit": 100,
            "fields": (
                "items(track(album(id,name,release_date,images,external_urls,"
                "artists(name)))),next"
            ),
        }

        while True:
            data = self._get(path, params=params)
            items.extend(data.get("items", []))

            next_url = data.get("next")
            if not next_url:
                break
            # `next` viene como URL completa; la convertimos a path relativo.
            path = next_url.replace(API_BASE, "")
            params = None  # los params ya van embebidos en next_url

        return items

    def get_new_releases(self, country: str = "MX", limit: int = 20) -> List[Dict[str, Any]]:
        """Devuelve álbumes de lanzamiento reciente para un mercado dado."""
        data = self._get(
            "/browse/new-releases",
            params={"country": country, "limit": limit},
        )
        return data.get("albums", {}).get("items", [])
