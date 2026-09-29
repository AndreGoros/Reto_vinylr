"""
render_reel.py
---------------
Puente Python -> Remotion. Toma los MISMOS datos que ya produce el pipeline
(fetch_trending.py / generate_duels.build_duels / generate_top10) y rellena el
"hueco" de las plantillas de video en remotion-reels/ para sacar MP4 (Reels 9:16).

Uso (desde la raíz del repo o desde src/):
    python src/render_reel.py --kind duelo --type country     # Lunes  (#1 vs #2 por país)
    python src/render_reel.py --kind duelo --type cross       # Viernes (país vs país)
    python src/render_reel.py --kind top10                    # Top 10 (sample o --top10-json)
    python src/render_reel.py --kind top10 --live             # arma el Top 10 con Last.fm

Requisitos: Node 18+ y `npm install` dentro de remotion-reels/ (una sola vez).
Igual que el resto del pipeline: NO publica nada, solo deja los MP4 para revisión humana.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from generate_duels import _find_latest_trending_file, _load_albums, build_duels

load_dotenv()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REMOTION_DIR = os.path.join(ROOT, "remotion-reels")
DATA_DIR = os.path.join(ROOT, "data")
SAMPLE_TRENDING = os.path.join(DATA_DIR, "sample", "trending_albums_sample.json")
SAMPLE_TOP10 = os.path.join(DATA_DIR, "sample", "Top10sample.json")


def _cover_ok(url: str) -> bool:
    """Remotion <Img> cancela TODO el render si una imagen no carga; mejor descartar el duelo antes."""
    if not url:
        return False
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        if r.status_code == 405:  # algunos CDNs no aceptan HEAD
            r = requests.get(url, timeout=10, stream=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _album_props(a: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": a["name"],
        "artists": a["artists"],
        "cover_url": a["cover_url"],
        "country": a.get("country", ""),
    }


def remotion_ready() -> bool:
    """
    True si se puede intentar un render de video (Node + `npm install` ya
    corrido en remotion-reels/). demo.py usa esto para decidir en silencio si
    ofrece el reel o no, sin necesidad de que el usuario configure nada para
    seguir usando el demo de imágenes como siempre.
    """
    return bool(shutil.which("npx")) and os.path.isdir(os.path.join(REMOTION_DIR, "node_modules"))


def _render(composition: str, props: Dict[str, Any], out_path: str, exit_on_missing_deps: bool = True) -> bool:
    npx = shutil.which("npx")
    if not npx or not os.path.isdir(os.path.join(REMOTION_DIR, "node_modules")):
        msg = (
            f"Falta Node.js y/o dependencias instaladas. Corre: cd {REMOTION_DIR} && npm install "
            "(ver remotion-reels/README.md)."
        )
        if exit_on_missing_deps:
            sys.exit(msg)
        print(f"  [reel] {msg}")
        return False

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    props_path = out_path.replace(".mp4", ".props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    cmd = [npx, "remotion", "render", composition, out_path, f"--props={props_path}"]
    print("  $", " ".join(cmd))
    try:
        result = subprocess.run(cmd, cwd=REMOTION_DIR)
    except Exception as exc:  # noqa: BLE001 - un reel fallido nunca debe tumbar al llamador (ej. demo.py)
        print(f"  [reel] Error al invocar Remotion: {exc}")
        return False
    return result.returncode == 0


def render_duel_video(
    album_a: Dict[str, Any], album_b: Dict[str, Any], dest_path: str, exit_on_missing_deps: bool = True
) -> bool:
    """
    Reel individual "Álbum A vs B" -> dest_path (.mp4). Reutilizable desde
    generate_duels.py o demo.py, no solo desde el CLI de este archivo.
    Devuelve False (sin tronar) si falta una carátula o Remotion no está listo.
    """
    if not (_cover_ok(album_a["cover_url"]) and _cover_ok(album_b["cover_url"])):
        print("  [reel] Carátula inaccesible, se omite el video (la imagen estática no se ve afectada).")
        return False
    props = {
        "albumA": _album_props(album_a),
        "albumB": _album_props(album_b),
        "kicker": "Nuevo duelo",
        "headline": "¿Cuál fue mejor?",
        "turnHeadline": "Tu turno",
        "cta": "VOTA EN VINYLR",
        "year": str(datetime.now().year),
    }
    return _render("DueloReel", props, dest_path, exit_on_missing_deps=exit_on_missing_deps)


def render_top10_video(post: Dict[str, Any], dest_path: str, exit_on_missing_deps: bool = True) -> bool:
    """Reel del post 'Top 10 [País/Región]' -> dest_path (.mp4). Mismo criterio que render_duel_video."""
    props = {
        "countryName": post["country_name"],
        "accentPrimary": post["accent_primary"],
        "accentSecondary": post["accent_secondary"],
        "featuredCoverUrl": post["featured_cover_url"],
        "items": post["items"],
        "secondsPerItem": 1.3,
        "cta": "¿COINCIDES? VOTA EN VINYLR",
        "year": str(datetime.now().year),
    }
    return _render("Top10Reel", props, dest_path, exit_on_missing_deps=exit_on_missing_deps)


def render_duels(input_path: Optional[str], duel_type: str, out_dir: str) -> list:
    path = input_path or (
        _find_latest_trending_file(DATA_DIR)
        if any(n.startswith("trending_albums_") for n in os.listdir(DATA_DIR))
        else SAMPLE_TRENDING
    )
    print(f"Usando álbumes de: {path}")
    duels = build_duels(_load_albums(path), duel_type=duel_type)
    results = []
    for d in duels:
        a, b = d["album_a"], d["album_b"]
        out = os.path.join(out_dir, f"reel_duelo_{d['label']}.mp4")
        print(f"Renderizando reel [{d['type']}] {d['label']} ...")
        ok = render_duel_video(a, b, out)
        results.append({"label": d["label"], "type": d["type"], "video": out if ok else None,
                        "status": "generado_pendiente_revision" if ok else "error"})
    return results


def render_top10(live: bool, top10_json: str, out_dir: str) -> list:
    if live:
        from generate_top10 import build_top10_latam
        from lastfm_client import LastfmClient

        post = build_top10_latam(LastfmClient(), ["Mexico", "Argentina", "Colombia", "Chile"], 10)
        if not post:
            sys.exit("No se pudo armar el Top 10 con Last.fm (revisa LASTFM_API_KEY).")
    else:
        with open(top10_json, "r", encoding="utf-8") as f:
            post = json.load(f)["posts"][0]

    out = os.path.join(out_dir, f"reel_top10_{post['country_param']}.mp4")
    print("Renderizando reel Top 10 ...")
    ok = render_top10_video(post, out)
    return [{"label": f"top10_{post['country_param']}", "video": out if ok else None,
             "status": "generado_pendiente_revision" if ok else "error"}]


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera Reels (MP4) de Vinylr con Remotion.")
    ap.add_argument("--kind", choices=["duelo", "top10"], required=True)
    ap.add_argument("--type", choices=["all", "country", "cross"], default="all", help="Solo para --kind duelo")
    ap.add_argument("--input", default=None, help="trending_albums_*.json (default: el más reciente o el sample)")
    ap.add_argument("--live", action="store_true", help="Top 10: consultar Last.fm en vivo")
    ap.add_argument("--top10-json", default=SAMPLE_TOP10)
    args = ap.parse_args()

    out_dir = os.path.join(DATA_DIR, "generated", datetime.now().strftime("%Y-%m-%d"), "reels")
    results = (
        render_duels(args.input, args.type, out_dir)
        if args.kind == "duelo"
        else render_top10(args.live, args.top10_json, out_dir)
    )
    with open(os.path.join(out_dir, f"manifest_reels_{args.kind}.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "reels": results}, f, ensure_ascii=False, indent=2)
    print(f"\nListo. Revisa los MP4 en: {out_dir}\nNADA se publica automáticamente — la revisión humana decide.")


if __name__ == "__main__":
    main()
