"""
local_render_client.py
-----------------------
Reemplaza a template_client.py (APITemplate.io). Genera las imágenes de
Vinylr renderizando los templates HTML/CSS de `src/templates/` con
Playwright (Chromium headless) — sin cuotas, sin API externa, sin
dependencia de red en tiempo de generación.
 
Por qué esto y no APITemplate.io:
- APITemplate.io Free se acabó (limitado a 3 plantillas). Con HTML/CSS
  propio no hay límite de plantillas ni de generaciones.
- Un solo template de "duelo" sirve para CUALQUIER país o par de países
  (antes se necesitaba un template_id de APITemplate distinto por cada
  uno). El color/identidad de cada país, si aplica, se pasa como variable
  Jinja2, no como una plantilla nueva.
 
Uso típico:
    with LocalRenderClient() as client:
        client.render_duel_image(album_a, album_b, "salida.png")
        client.render_top10_image("México", "#E63946", "#16855B",
                                   featured_cover_url, items, "top10_mx.png")
 
Requisitos (ver requirements.txt):
    pip install playwright jinja2
    python -m playwright install --with-deps chromium   # una sola vez
"""
 
import os
from typing import Any, Dict, List, Optional
 
from jinja2 import Environment, FileSystemLoader
 
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1440
 
 
class LocalRenderError(Exception):
    """Error genérico al renderizar una imagen localmente."""
 
 
class LocalRenderClient:
    """
    Envuelve Playwright + Jinja2. Se recomienda usarlo como context manager
    (`with LocalRenderClient() as client:`) para abrir el navegador UNA sola
    vez y reusarlo en todos los duelos/top10 de una corrida — abrir Chromium
    por imagen sería mucho más lento.
    """
 
    def __init__(self):
        self._env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        self._playwright = None
        self._browser = None
        self._page = None
 
    def __enter__(self) -> "LocalRenderClient":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise LocalRenderError(
                "Falta 'playwright' instalado. Corre: pip install playwright "
                "&& python -m playwright install --with-deps chromium"
            ) from exc
 
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch()
        except Exception as exc:  # noqa: BLE001
            self._playwright.stop()
            raise LocalRenderError(
                "No se pudo lanzar Chromium. Si es la primera vez, corre: "
                "python -m playwright install --with-deps chromium"
            ) from exc
        self._page = self._browser.new_page(
            viewport={"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT}
        )
        return self
 
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
 
    def _render_html_to_png(
        self, html: str, dest_path: str, width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT
    ) -> None:
        if self._page is None:
            raise LocalRenderError(
                "LocalRenderClient debe usarse como context manager: "
                "'with LocalRenderClient() as client: ...'"
            )
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        # El viewport se fija en CADA llamada (no solo al abrir el navegador),
        # porque no todos los templates miden lo mismo (ej. si el Top 10
        # cambia de tamaño respecto a los duelos) — evita capturas cortadas
        # o con espacio negro de más si algún template no coincide con el
        # tamaño por defecto.
        self._page.set_viewport_size({"width": width, "height": height})
        # set_content + esperar a que las fuentes/imagenes carguen antes del screenshot
        self._page.set_content(html, wait_until="networkidle")
        self._page.screenshot(path=dest_path)
 
    def render_duel_image(
        self,
        album_a: Dict[str, Any],
        album_b: Dict[str, Any],
        dest_path: str,
        year: Optional[str] = None,
        template_name: str = "duelo_template.html.j2",
    ) -> None:
        """
        Genera la imagen 'Álbum A vs B'. `template_name` elige CUÁL de los
        templates de duelo en src/templates/ usar (por defecto el
        original). Ahora mismo hay 3 disponibles con layouts distintos:
        duelo_template.html.j2 (carátula + vinilo), duelo_template_split.html.j2
        (carátulas a pantalla completa, corte diagonal) y
        duelo_template_stacked.html.j2 (mitades apiladas). Quien llama
        (generate_duels.py, demo.py) decide cuál usar en cada duelo, para
        que una misma corrida no genere las 6 imágenes con el mismo layout.
        """
        template = self._env.get_template(template_name)
        html = template.render(album_a=album_a, album_b=album_b, year=year or "2026")
        self._render_html_to_png(html, dest_path)
 
    def render_top10_image(
        self,
        country_name: str,
        accent_primary: str,
        accent_secondary: str,
        featured_cover_url: str,
        items: List[Dict[str, Any]],
        dest_path: str,
        year: Optional[str] = None,
    ) -> None:
        """Genera la imagen 'Top 10 País' usando top10_template.html.j2.
 
        items: lista de dicts {"rank": int, "artist": str, "title": str}
        """
        template = self._env.get_template("top10_template.html.j2")
        html = template.render(
            country_name=country_name,
            accent_primary=accent_primary,
            accent_secondary=accent_secondary,
            featured_cover_url=featured_cover_url,
            items=items,
            year=year or "2026",
        )
        self._render_html_to_png(html, dest_path, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
