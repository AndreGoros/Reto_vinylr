"""
test_single_image.py
---------------------
Genera SOLO UNA imagen (un duelo específico), para probar que una plantilla
de APITemplate.io se ve bien sin gastar de golpe las 6 imágenes que produce
`generate_duels.py` — útil para cuidar la cuota gratis de 50 imágenes/mes.

Por defecto usa los datos de EJEMPLO (data/sample/trending_albums_sample.json),
para tampoco gastar llamadas reales a Last.fm mientras solo se está
probando el diseño visual. Usa --live si quieres datos reales.

Uso:
    python src/test_single_image.py --template mexico
    python src/test_single_image.py --template mexico_colombia
    python src/test_single_image.py --template argentina --live
"""

import argparse
import os
from datetime import datetime

from dotenv import load_dotenv

from generate_duels import build_duels, _load_albums
from template_client import TemplateClient

load_dotenv()

SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "sample", "trending_albums_sample.json"
)

# Mapea el valor corto de --template al "label" real que produce build_duels().
TEMPLATE_CHOICES = {
    "mexico": "mexico_1_vs_2",
    "argentina": "argentina_1_vs_2",
    "colombia": "colombia_1_vs_2",
    "chile": "chile_1_vs_2",
    "mexico_colombia": "mexico_vs_colombia",
    "argentina_chile": "argentina_vs_chile",
}


def main():
    parser = argparse.ArgumentParser(
        description="Genera UNA sola imagen de un duelo específico, para probar una plantilla sin gastar cuota."
    )
    parser.add_argument(
        "--template",
        required=True,
        choices=sorted(TEMPLATE_CHOICES.keys()),
        help="Qué duelo/plantilla probar.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Usa datos reales de Last.fm (el JSON más reciente en data/) en vez de los de ejemplo.",
    )
    args = parser.parse_args()

    if args.live:
        import glob

        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        matches = sorted(glob.glob(os.path.join(data_dir, "trending_albums_*.json")))
        if not matches:
            print("No hay ningún trending_albums_*.json en data/. Corre fetch_trending.py primero, o quita --live.")
            return
        albums = _load_albums(matches[-1])
        print(f"Usando datos reales de: {matches[-1]}")
    else:
        albums = _load_albums(SAMPLE_DATA_PATH)
        print("Usando datos de EJEMPLO (no gasta llamadas a Last.fm).")

    duels = build_duels(albums)
    target_label = TEMPLATE_CHOICES[args.template]
    duel = next((d for d in duels if d["label"] == target_label), None)

    if not duel:
        print(
            f"No se pudo armar el duelo '{target_label}' con los datos disponibles "
            "(probablemente falta el país correspondiente en el JSON)."
        )
        return

    template_id = os.environ.get(duel["template_env_var"])
    if not template_id:
        print(f"Falta {duel['template_env_var']} en tu .env — agrégala antes de probar esta plantilla.")
        return

    a, b = duel["album_a"], duel["album_b"]
    print(f"Generando 1 imagen: [{duel['type']}] {a['name']} vs {b['name']} usando {duel['template_env_var']}...")

    client = TemplateClient()
    url = client.create_duel_image(a, b, template_id=template_id)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "test_output")
    os.makedirs(output_dir, exist_ok=True)
    dest_path = os.path.join(
        output_dir, f"test_{duel['label']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    client.download_image(url, dest_path)

    print(f"\nListo — 1 sola imagen generada (cuota usada: 1). Ábrela en:\n  {os.path.abspath(dest_path)}")


if __name__ == "__main__":
    main()
