"""
generate_duels.py
------------------
Etapa 2 del pipeline: toma el JSON de álbumes en tendencia (generado por
fetch_trending.py) y produce las imágenes de los duelos "Álbum A vs B" para
Lunes y Viernes, usando APITemplate.io.

Lógica de emparejamiento (simple a propósito, para poder ajustarla rápido
durante el hackathon si algún duelo no tiene sentido):
    - Álbum #1 vs Álbum #2 del ranking → duelo del LUNES
    - Álbum #3 vs Álbum #4 del ranking → duelo del VIERNES
    - Álbum #5 queda de reserva/comodín si algún duelo se rechaza en revisión.

Esta es la pieza que la propuesta llama "revisión humana obligatoria de
5 minutos": el script NO publica nada, solo deja las imágenes + su
metadata en data/generated/<fecha>/ listas para que una persona las revise
antes de programarlas en Instagram.

Uso:
    python src/generate_duels.py
    python src/generate_duels.py --input data/trending_albums_2026-09-22.json
"""

import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from template_client import TemplateClient


def _find_latest_trending_file(data_dir: str) -> str:
    pattern = os.path.join(data_dir, "trending_albums_*.json")
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No encontré ningún archivo trending_albums_*.json en {data_dir}. "
            "Corre primero fetch_trending.py."
        )
    return matches[-1]  # el más reciente por orden alfabético (fecha en el nombre)


def _load_albums(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload["albums"]


def build_duels(albums: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Empareja álbumes en duelos para Lunes y Viernes."""
    duels = []
    if len(albums) >= 2:
        duels.append({"day": "lunes", "album_a": albums[0], "album_b": albums[1]})
    if len(albums) >= 4:
        duels.append({"day": "viernes", "album_a": albums[2], "album_b": albums[3]})

    if len(duels) < 2:
        print(
            f"[aviso] Solo se armaron {len(duels)} duelo(s) porque el JSON trae "
            f"{len(albums)} álbum(es). Se necesitan al menos 4 para Lunes + Viernes."
        )
    return duels


def main():
    parser = argparse.ArgumentParser(
        description="Genera las imágenes de los duelos Álbum A vs B (Lunes y Viernes)."
    )
    default_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    parser.add_argument(
        "--input",
        default=None,
        help="Ruta al JSON de trending_albums a usar. Si se omite, usa el más reciente en data/.",
    )
    parser.add_argument("--data-dir", default=default_data_dir)
    args = parser.parse_args()

    input_path = args.input or _find_latest_trending_file(args.data_dir)
    print(f"Usando álbumes de: {input_path}")

    albums = _load_albums(input_path)
    duels = build_duels(albums)

    if not duels:
        print("No hay suficientes álbumes para armar ni un duelo. Abortando.")
        return

    client = TemplateClient()

    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(args.data_dir, "generated", today)
    os.makedirs(output_dir, exist_ok=True)

    manifest = {"generated_at": datetime.now().isoformat(), "source_file": input_path, "duels": []}

    for duel in duels:
        a, b = duel["album_a"], duel["album_b"]
        label = f"{a['name']} vs {b['name']}"
        print(f"Generando duelo de {duel['day'].upper()}: {label} ...")

        try:
            download_url = client.create_duel_image(a, b)
            image_filename = f"duelo_{duel['day']}.png"
            image_path = os.path.join(output_dir, image_filename)
            client.download_image(download_url, image_path)
            status = "generado_pendiente_revision"
            print(f"  -> Guardado en {image_path}")
        except Exception as exc:  # noqa: BLE001 - queremos seguir con el otro duelo si uno falla
            image_path = None
            status = f"error: {exc}"
            print(f"  -> [ERROR] {exc}")

        manifest["duels"].append(
            {
                "day": duel["day"],
                "album_a": {"name": a["name"], "artists": a["artists"]},
                "album_b": {"name": b["name"], "artists": b["artists"]},
                "image_path": image_path,
                "status": status,
            }
        )

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\nListo. Revisa las imágenes y el manifest en: {output_dir}")
    print("Recuerda: NADA se publica automáticamente. Esto es para la revisión humana.")


if __name__ == "__main__":
    main()
