"""
generate_duels.py
------------------
Etapa 2 del pipeline: arma 2 TIPOS de duelo a partir del JSON de
tendencias (que trae el top 2 de cada país, ver fetch_trending.py), y
genera sus imágenes con el motor de render local (Playwright + HTML/CSS,
ver local_render_client.py) en vez de APITemplate.io.
 
1. DUELO INTRA-PAÍS: el #1 vs el #2 en tendencia de CADA país.
2. DUELO CRUZADO: México(#1) vs Colombia(#1), y Argentina(#1) vs Chile(#1).
 
Antes se necesitaba un template_id de APITemplate.io distinto por cada país
y por cada par cruzado (6 en total). Con el render local, los 3 layouts de
duelo en src/templates/ (original, split, stacked) sirven para CUALQUIER
país o combinación — se rotan entre los 6 duelos de cada corrida para que
no salgan todos con el mismo diseño (ver TEMPLATE_ROTATION), en vez de
necesitar una plantilla nueva por cada país o par.
 
Como antes, el script NO publica nada — solo deja las imágenes + su
metadata en data/generated/<fecha>/ para la revisión humana.
 
Desde esta iteración, --type fija qué slot de la semana estás generando:
LUNES usa --type country, VIERNES usa --type cross (y además
generate_top10.py para el Top 10 LatAm — ver .github/workflows).
 
Uso:
    python src/generate_duels.py --type country   # slot Lunes
    python src/generate_duels.py --type cross      # slot Viernes
    python src/generate_duels.py                   # los 2 tipos (default "all")
"""
 
import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List
 
from dotenv import load_dotenv
 
from local_render_client import LocalRenderClient, LocalRenderError
 
load_dotenv()  # Carga variables de .env sin depender de que el terminal/IDE lo haga por su cuenta.
 
# Pares fijos para el duelo cruzado (país_a, país_b). Los nombres deben
# coincidir con el campo "country" que trae cada álbum en el JSON de
# tendencias (ver fetch_trending.py --countries).
CROSS_COUNTRY_PAIRS = [
    ("Mexico", "Colombia"),
    ("Argentina", "Chile"),
]
 
# Los 3 layouts de duelo disponibles en src/templates/ (ver sus propios
# comentarios). Se rotan entre los duelos de una misma corrida para que no
# los 6 salgan con el mismo diseño — mismo criterio que ya usa demo.py.
TEMPLATE_ROTATION = [
    "duelo_template.html.j2",
    "duelo_template_split.html.j2",
    "duelo_template_stacked.html.j2",
]
 
 
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
 
 
def build_duels(albums: List[Dict[str, Any]], duel_type: str = "all") -> List[Dict[str, Any]]:
    """
    Arma los duelos a partir de la lista de álbumes (que trae "country" y
    "rank" en cada uno, gracias a fetch_trending.py).
 
    duel_type controla CUÁLES de los 2 tipos se arman:
      - "country": solo intra-país (#1 vs #2 de cada país)  -> slot Lunes
      - "cross":   solo cruzado (país A #1 vs país B #1)      -> slot Viernes
      - "all":     ambos (comportamiento por default, usado por demo.py)
 
    Devuelve una lista de dicts: {"label", "type", "album_a", "album_b"}.
    """
    if duel_type not in ("all", "country", "cross"):
        raise ValueError(f"duel_type inválido: {duel_type!r} (debe ser 'all', 'country' o 'cross')")
 
    # Indexamos por país y rank para poder armar ambos tipos de duelo.
    by_country: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for album in albums:
        country = album.get("country")
        rank = album.get("rank")
        if not country or not rank:
            continue
        by_country.setdefault(country, {})[rank] = album
 
    duels: List[Dict[str, Any]] = []
 
    # --- Duelo intra-país: #1 vs #2 de cada país --- #
    if duel_type in ("all", "country"):
        for country, ranks in by_country.items():
            if 1 in ranks and 2 in ranks:
                duels.append(
                    {
                        "label": f"{country.lower()}_1_vs_2",
                        "type": "country",
                        "album_a": ranks[1],
                        "album_b": ranks[2],
                    }
                )
            else:
                print(f"[aviso] {country} no tiene #1 y #2 resueltos, se omite su duelo intra-país.")
 
    # --- Duelo cruzado: pares fijos de países, usando el #1 de cada uno --- #
    if duel_type in ("all", "cross"):
        for country_a, country_b in CROSS_COUNTRY_PAIRS:
            album_a = by_country.get(country_a, {}).get(1)
            album_b = by_country.get(country_b, {}).get(1)
            if album_a and album_b:
                duels.append(
                    {
                        "label": f"{country_a.lower()}_vs_{country_b.lower()}",
                        "type": "cross",
                        "album_a": album_a,
                        "album_b": album_b,
                    }
                )
            else:
                print(
                    f"[aviso] Falta el #1 de {country_a} o {country_b}, "
                    "se omite ese duelo cruzado."
                )
 
    # Se asigna la plantilla AL FINAL, después de armar todos los duelos,
    # para que la rotación sea sobre la lista completa (y no se repita el
    # mismo layout dos veces seguidas solo por coincidir con el resto entre
    # duelos intra-país y cruzados).
    for i, duel in enumerate(duels):
        duel["template"] = TEMPLATE_ROTATION[i % len(TEMPLATE_ROTATION)]
 
    return duels
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Genera las imágenes de los duelos: intra-país (#1 vs #2) y cruzados entre países."
    )
    default_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    parser.add_argument(
        "--input",
        default=None,
        help="Ruta al JSON de trending_albums a usar. Si se omite, usa el más reciente en data/.",
    )
    parser.add_argument("--data-dir", default=default_data_dir)
    parser.add_argument(
        "--type",
        choices=["all", "country", "cross"],
        default="all",
        help=(
            "Qué tipo de duelo generar: 'country' (intra-país, slot Lunes), "
            "'cross' (entre países, slot Viernes) o 'all' (ambos, default)."
        ),
    )
    args = parser.parse_args()
 
    input_path = args.input or _find_latest_trending_file(args.data_dir)
    print(f"Usando álbumes de: {input_path}")
 
    albums = _load_albums(input_path)
    duels = build_duels(albums, duel_type=args.type)
 
    if not duels:
        print("No hay suficientes álbumes/países resueltos para armar ni un duelo. Abortando.")
        return
 
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(args.data_dir, "generated", today)
    os.makedirs(output_dir, exist_ok=True)
 
    manifest = {"generated_at": datetime.now().isoformat(), "source_file": input_path, "duels": []}
 
    # Un solo Chromium para TODOS los duelos de la corrida (abrirlo por duelo
    # sería mucho más lento). Si Playwright no está instalado o falla al
    # lanzar el navegador, LocalRenderError se levanta aquí mismo, antes de
    # gastar tiempo armando los duelos.
    with LocalRenderClient() as render_client:
        for duel in duels:
            a, b = duel["album_a"], duel["album_b"]
            label_display = f"{a['name']} vs {b['name']}"
            print(f"Generando duelo [{duel['type']}] {duel['label']} (plantilla: {duel['template']}): {label_display} ...")
 
            image_filename = f"duelo_{duel['label']}.png"
            image_path = os.path.join(output_dir, image_filename)
 
            try:
                render_client.render_duel_image(a, b, image_path, template_name=duel["template"])
                status = "generado_pendiente_revision"
                print(f"  -> Guardado en {image_path}")
            except LocalRenderError as exc:  # noqa: BLE001 - seguimos con el siguiente duelo si uno falla
                image_path = None
                status = f"error: {exc}"
                print(f"  -> [ERROR] {exc}")
 
            manifest["duels"].append(
                {
                    "label": duel["label"],
                    "type": duel["type"],
                    "template": duel["template"],
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
    print("Recuerda: NADA se publica automáticamente, y NADA asigna un día fijo.")
    print("La revisión humana decide qué duelos publicar y en qué día.")
 
 
if __name__ == "__main__":
    main()
 