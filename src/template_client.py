"""
template_client.py
-------------------
Cliente para APITemplate.io (https://apitemplate.io), usado para generar
automáticamente la imagen del duelo "Álbum A vs B" a partir de una plantilla
visual diseñada una sola vez en su editor.

Por qué esta herramienta y no Canva:
- Canva Free no tiene API pública de generación automática (eso solo existe
  en Canva Enterprise). APITemplate.io sí tiene un plan gratuito real
  (50 imágenes/mes) con API REST simple.

Requisito previo (manual, se hace una sola vez en el dashboard de
apitemplate.io): diseñar la plantilla "Álbum A vs B" y nombrar sus capas
dinámicas exactamente como se documenta en PROGRESS.md / README.md:
    album_a_cover, album_a_name, album_a_artist,
    album_b_cover, album_b_name, album_b_artist

Documentación oficial:
https://docs.apitemplate.io/api/index.html
"""

import os
from typing import Any, Dict, Optional

import requests

API_BASE = "https://rest.apitemplate.io"


class TemplateAPIError(Exception):
    """Error genérico al llamar a la API de APITemplate.io."""


class TemplateClient:
    def __init__(self, api_key: Optional[str] = None, template_id: Optional[str] = None):
        self.api_key = api_key or os.environ.get("APITEMPLATE_API_KEY")
        self.template_id = template_id or os.environ.get("APITEMPLATE_TEMPLATE_ID")

        if not self.api_key or not self.template_id:
            raise TemplateAPIError(
                "Faltan APITEMPLATE_API_KEY y/o APITEMPLATE_TEMPLATE_ID como "
                "variables de entorno (ver .env.example)."
            )

    def create_duel_image(self, album_a: Dict[str, Any], album_b: Dict[str, Any]) -> str:
        """
        Genera la imagen del duelo "Álbum A vs B" y devuelve la URL de descarga.

        album_a / album_b: dicts con al menos las llaves "name", "artists"
        (lista) y "cover_url", tal como los produce fetch_trending.py.
        """
        overrides = [
            {"name": "album_a_cover", "src": album_a["cover_url"]},
            {"name": "album_a_name", "text": album_a["name"]},
            {"name": "album_a_artist", "text": ", ".join(album_a["artists"])},
            {"name": "album_b_cover", "src": album_b["cover_url"]},
            {"name": "album_b_name", "text": album_b["name"]},
            {"name": "album_b_artist", "text": ", ".join(album_b["artists"])},
        ]

        url = f"{API_BASE}/v2/create-image"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        params = {"template_id": self.template_id}
        body = {"overrides": overrides}

        response = requests.post(url, headers=headers, params=params, json=body, timeout=30)

        if response.status_code != 200:
            raise TemplateAPIError(
                f"Error generando imagen (status {response.status_code}): {response.text}"
            )

        data = response.json()
        download_url = data.get("download_url") or data.get("download_url_png")
        if not download_url:
            raise TemplateAPIError(f"La respuesta no trae download_url: {data}")

        return download_url

    @staticmethod
    def download_image(url: str, dest_path: str) -> None:
        """Descarga la imagen generada a disco, para la cola de revisión humana."""
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise TemplateAPIError(
                f"No se pudo descargar la imagen (status {response.status_code}): {url}"
            )
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(response.content)
