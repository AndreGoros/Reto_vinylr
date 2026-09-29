Readme · MD
Vinylr Content Engine — Etapa 1: Detección de tendencias
Módulo que obtiene los álbumes en tendencia en LatAm (semanalmente) usando la API oficial de Spotify. Es el primer paso del motor de contenido para Instagram descrito en PROGRESS.md.

🚀 Demo rápido (recomendado para empezar)
Antes de configurar nada, puedes ver el concepto funcionando ahora mismo:

bash
pip install -r requirements.txt
cd src
python demo.py
Esto genera las 2 imágenes "Álbum A vs B" (Lunes y Viernes) sin importar si ya tienes Spotify/APITemplate.io configurados:

Si detecta credenciales de Spotify, usa datos reales; si no, usa datos de ejemplo (data/sample/).
Si detecta credenciales de APITemplate.io, genera la imagen con la plantilla real; si no, la genera localmente con Pillow.
Nunca falla — es la versión que puedes correr en cualquier momento para mostrarle a alguien cómo funciona, incluso sin internet.
Las imágenes quedan en data/demo_output/<fecha>/.

Para forzar el modo 100% offline/ejemplo (sin siquiera intentar Spotify):

bash
python demo.py --force-sample
Para que además genere el Reel (.mp4) de cada pieza, junto a su imagen (requiere el setup de remotion-reels/ — ver más abajo):

bash
python demo.py --with-reels      # posts (imágenes) + reels (video)
python demo.py --posts-only      # solo imágenes — mismo resultado que sin flags, explícito
python demo.py --reels-only      # solo video, sin generar las imágenes
python demo.py --quick           # prueba express: 1 solo post + su reel, nada más
Si Node.js o npm install no están listos, el demo lo avisa; con --with-reels o --quick sigue generando las imágenes igual, pero --reels-only aborta (no tendría nada que mostrar si no puede hacer el video).

Setup
Hay dos formas de correr este proyecto: con Docker/VS Code (recomendado) o con un venv local de Python. Elige una.

Opción A — VS Code Dev Containers (recomendado)
Requisitos: Docker Desktop instalado y corriendo, y la extensión "Dev Containers" de VS Code (ms-vscode-remote.remote-containers).

Copia .env.example como .env y llena tus credenciales de Spotify:
bash
   cp .env.example .env
Abre la carpeta vinylr-content-engine en VS Code.
VS Code va a detectar la carpeta .devcontainer/ y te va a mostrar un aviso abajo a la derecha: "Reopen in Container". Dale clic. (Si no aparece: Cmd/Ctrl + Shift + P → "Dev Containers: Reopen in Container")
Espera a que construya la imagen la primera vez (tarda un par de minutos). VS Code se va a reconectar y su terminal integrada ya va a estar dentro del contenedor, en /app.
Corre el script normal, como si fuera local:
bash
   cd src
   python fetch_trending.py --top 8 --countries MX AR CO CL
Los archivos que genere en data/ van a aparecer también fuera del contenedor, en tu carpeta local data/ (está montada como volumen).
Opción B — Docker + terminal, sin abrir VS Code dentro del contenedor
Útil si solo quieres correr el script puntualmente desde tu terminal normal.

bash
cd vinylr-content-engine
cp .env.example .env   # y llena tus credenciales

# Construye la imagen la primera vez (o si cambias requirements.txt)
docker compose build

# Corre el script (se borra el contenedor al terminar, --rm)
docker compose run --rm vinylr python fetch_trending.py --top 8 --countries MX AR CO CL
Si prefieres dejar el contenedor corriendo y entrar con una shell:

bash
docker compose up -d
docker compose exec vinylr bash
# ya adentro:
cd src && python fetch_trending.py --top 8
Opción C — Venv local (sin Docker)
bash
cd vinylr-content-engine
python -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tu Client ID y Client Secret
Carga las variables de entorno antes de correr el script (o usa python-dotenv si prefieres cargarlas automáticamente agregando estas 2 líneas al inicio de fetch_trending.py):

python
from dotenv import load_dotenv
load_dotenv()
Uso
bash
cd src
python fetch_trending.py --top 8 --countries MX AR CO CL
Esto genera data/trending_albums_<fecha>.json con algo como:

json
{
  "generated_at": "2026-09-23T10:00:00",
  "count": 8,
  "albums": [
    {
      "spotify_id": "...",
      "name": "Nombre del álbum",
      "artists": ["Artista"],
      "release_date": "2026-09-12",
      "cover_url": "https://i.scdn.co/image/...",
      "spotify_url": "https://open.spotify.com/album/...",
      "trend_score": 12.4,
      "sources": ["top50_mx", "new_release_mx"]
    }
  ]
}
Este JSON es el input directo de la Etapa 2 (generación de brief creativo en español), que se construirá en la siguiente iteración.

Reels de video (opcional)
Además de la imagen estática ("Álbum A vs B", "Top 10"), el proyecto puede generar la misma pieza como video 9:16 listo para Reels/TikTok, usando Remotion. Vive en remotion-reels/ (ver su propio README.md para el detalle de arquitectura: por qué Remotion, cómo se portaron los efectos de ReactBits, y dónde encaja 21st.dev). El puente entre Python y esa carpeta es src/render_reel.py.

Setup (una sola vez, requiere Node.js 18+):

bash
cd remotion-reels
npm install
Uso:

bash
python demo.py --with-reels                              # video de cada pieza del demo
python src/render_reel.py --kind duelo --type country     # solo el slot Lunes
python src/render_reel.py --kind duelo --type cross       # solo el slot Viernes
python src/render_reel.py --kind top10 --live              # Top 10 con Last.fm real
Como el resto del pipeline: nada se publica automáticamente, los .mp4 quedan junto a las imágenes para la misma revisión humana de ~5 min.

Pendiente de construir: automatizar esto en weekly_content.yml (GitHub Actions) y en el Dockerfile — ambos son hoy 100% Python y no tienen Node instalado, así que por ahora los Reels solo se generan en local.

Notas importantes
No probado en vivo todavía: el entorno donde se escribió este código no tiene acceso a internet, así que la lógica está verificada por revisión pero falta correrlo una vez con credenciales reales para confirmar que los IDs de playlist siguen vigentes (Spotify los rota de vez en cuando).
Primer paso al correrlo por primera vez: ejecútalo con --top 20 y revisa manualmente que los álbumes tengan sentido para tu mercado antes de conectarlo a la generación automática de contenido.
Pensado para correr como cron job semanal (lunes temprano) vía GitHub Actions, para que el JSON esté listo antes de generar los posts del lunes.
Docker: si cambias requirements.txt, corre docker compose build de nuevo (o, dentro de VS Code Dev Containers, Cmd/Ctrl+Shift+P → "Dev Containers: Rebuild Container") para que se reinstalen las dependencias.
El archivo .env nunca se copia a la imagen de Docker (está en .dockerignore); se inyecta en tiempo de ejecución vía env_file en docker-compose.yml. Así tus credenciales no quedan hardcodeadas en la imagen.
Automatización semanal con GitHub Actions
El workflow .github/workflows/weekly_content.yml corre el pipeline real (Spotify → APITemplate.io) todos los lunes a las 08:00 UTC, y sube las imágenes generadas como un "artifact" descargable desde la pestaña Actions del repositorio — listo para la revisión humana de 5 minutos.

Setup (una sola vez):

Sube este proyecto a un repositorio de GitHub.
Ve a Settings → Secrets and variables → Actions → New repository secret y crea estos 4 secrets:
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
APITEMPLATE_API_KEY
APITEMPLATE_TEMPLATE_ID
Listo. También puedes correrlo manualmente sin esperar al lunes: pestaña Actions → "Generar duelos semanales (Vinylr)" → Run workflow.
Estructura del proyecto

vinylr-content-engine/

├── PROGRESS.md                  # registro de avance (leer primero)
├── README.md
├── Dockerfile / docker-compose.yml / .devcontainer/
├── .github/workflows/weekly_content.yml
├── requirements.txt
├── .env.example
├── data/
│   ├── sample/                  # datos de ejemplo para el demo
│   ├── generated/                # salida del pipeline real (producción) — incluye reels/ si se usó --with-reels o render_reel.py
│   └── demo_output/              # salida de demo.py — incluye los .mp4 si se usó --with-reels
├── src/
│   ├── lastfm_client.py          # Etapa 1: cliente de Last.fm
│   ├── fetch_trending.py         # Etapa 1: rankea álbumes trending
│   ├── local_render_client.py    # Etapa 2: renderiza los templates HTML/CSS a imagen (Playwright)
│   ├── generate_duels.py         # Etapa 2: arma duelos Lun/Vie + genera imágenes
│   ├── generate_top10.py         # Etapa 2: arma y genera el Top 10 LatAm
│   ├── render_reel.py            # Puente Python -> Remotion: mismos dicts, ahora como .mp4
│   ├── templates/                # *.html.j2 — plantillas HTML/CSS de las imágenes
│   └── demo.py                   # Demo on-demand, siempre funcional (--with-reels opcional)
└── remotion-reels/               # Plantillas de VIDEO (9:16) con Remotion — ver su README.md
    ├── src/compositions/          # DueloReel.tsx, Top10Reel.tsx
    ├── src/components/            # UI de marca + efectos tipo ReactBits (portados a Remotion)
    └── props/                     # ejemplos del "hueco" que rellena render_reel.py


