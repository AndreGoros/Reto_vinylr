# Vinylr Content Engine

> Motor de automatización para la detección de tendencias musicales en LatAm y generación automática de contenido estático (imágenes) y dinámico (Reels 9:16) para redes sociales.

---

## Descripción general

El **Vinylr Content Engine** es el componente core encargado de:

1. **Detección de tendencias (Etapa 1):** Rastrea semanalmente los álbumes más populares en Latinoamérica utilizando la API oficial de Spotify y Last.fm.
2. **Generación de piezas estáticas (Etapa 2):** Renderiza plantillas HTML/CSS en imágenes de alta calidad (formatos tipo "Álbum A vs B" y "Top 10").
3. **Generación de video (Reels/TikTok):** Compila animaciones en formato vertical (9:16) listas para publicación utilizando **Remotion**.

---

## Demo rápido (100% resiliente)

Puedes probar el motor inmediatamente sin configurar credenciales ni tener conexión a internet. El script de demo detecta la configuración disponible y conmuta automáticamente a datos o renderizado local según sea necesario.

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar demo
cd src
python demo.py

```

Las imágenes generadas se guardarán en `data/demo_output/<fecha>/`.

### Opciones y flags de ejecución

| Comando | Descripción |
| --- | --- |
| `python demo.py` | Ejecución estándar (usa Spotify/APITemplate si existen; si no, usa fallback local/sample). |
| `python demo.py --force-sample` | Fuerza el modo 100% offline utilizando únicamente archivos de prueba local. |
| `python demo.py --with-reels` | Genera tanto las imágenes estáticas como los videos (.mp4). Requiere setup de Remotion. |
| `python demo.py --posts-only` | Genera exclusivamente imágenes estáticas (comportamiento por defecto). |
| `python demo.py --reels-only` | Genera exclusivamente videos .mp4. Aborta si el entorno Node.js no está disponible. |
| `python demo.py --quick` | Prueba express: procesa únicamente 1 post y su respectivo reel. |

---

## Instalación y configuración

Elige uno de los tres métodos de entorno de desarrollo según tu preferencia:

### Opción A — VS Code Dev Containers (Recomendado)

**Requisitos:** Docker Desktop corriendo y la extensión *Dev Containers* (`ms-vscode-remote.remote-containers`).

1. Copia el archivo de variables de entorno:
```bash
cp .env.example .env

```


2. Abre la carpeta del proyecto en VS Code.
3. Cuando aparezca el aviso *"Reopen in Container"*, haz clic en él (o presiona `Cmd/Ctrl + Shift + P` y selecciona `Dev Containers: Reopen in Container`).
4. La terminal integrada de VS Code se abrirá dentro del contenedor en `/app`.

---

### Opción B — Docker Compose (Terminal)

Útil para ejecuciones puntuales desde la consola sin abrir un IDE dentro del contenedor.

```bash
# 1. Configura variables de entorno
cp .env.example .env

# 2. Construye la imagen
docker compose build

# 3. Ejecuta el script (el contenedor se elimina automáticamente al finalizar)
docker compose run --rm vinylr python fetch_trending.py --top 8 --countries MX AR CO CL

```

Si prefieres mantener el contenedor en segundo plano:

```bash
docker compose up -d
docker compose exec vinylr bash

```

---

### Opción C — Entorno virtual local (venv)

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

```

*Nota:* Si utilizas esta opción, asegúrate de cargar las variables de entorno en tus scripts mediante `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()

```

---

## Uso del Pipeline

### 1. Extracción de tendencias (Etapa 1)

Ejecuta la recolección de álbumes populares para los países objetivo:

```bash
cd src
python fetch_trending.py --top 8 --countries MX AR CO CL

```

Este comando genera una estructura JSON en `data/trending_albums_<fecha>.json` con la siguiente forma:

```json
{
  "generated_at": "2026-09-23T10:00:00",
  "count": 8,
  "albums": [
    {
      "spotify_id": "4aawyAB9vmqN3u3R432M29",
      "name": "Nombre del Álbum",
      "artists": ["Artista Principal"],
      "release_date": "2026-09-12",
      "cover_url": "https://i.scdn.co/image/...",
      "spotify_url": "https://open.spotify.com/album/...",
      "trend_score": 12.4,
      "sources": ["top50_mx", "new_release_mx"]
    }
  ]
}

```

---

### 2. Generación de Reels en Video (Remotion)

Las piezas en video 9:16 utilizan **Remotion** (React) ubicadas en la carpeta `remotion-reels/`. El puente de integración desde Python es `src/render_reel.py`.

#### Setup inicial de Remotion (requiere Node.js 18+):

```bash
cd remotion-reels
npm install
cd ..

```

#### Comandos de renderizado de video:

```bash
# Renderizar mediante demo.py
python demo.py --with-reels

# Renderizar slots individuales
python src/render_reel.py --kind duelo --type country   # Slot Lunes
python src/render_reel.py --kind duelo --type cross     # Slot Viernes
python src/render_reel.py --kind top10 --live            # Top 10 con datos de Last.fm en vivo

```

---

## Automatización con GitHub Actions

El flujo automatizado `.github/workflows/weekly_content.yml` ejecuta el pipeline todos los **lunes a las 08:00 UTC**. Genera las piezas gráficas y las sube como un *Artifact* descargable listo para la revisión humana (~5 min).

### Configuración de Secrets en GitHub

En tu repositorio de GitHub, ve a **Settings → Secrets and variables → Actions** y añade las siguientes llaves:

* `SPOTIFY_CLIENT_ID`
* `SPOTIFY_CLIENT_SECRET`
* `APITEMPLATE_API_KEY`
* `APITEMPLATE_TEMPLATE_ID`

*Nota:* Para ejecutar manualmente la automatización, ve a la pestaña **Actions → Generar duelos semanales (Vinylr) → Run workflow**.

---

## Estructura del proyecto

```text
vinylr-content-engine/
├── PROGRESS.md                    # Bitácora de desarrollo y roadmap
├── README.md                      # Documentación principal
├── Dockerfile                     # Configuración de imagen Docker
├── docker-compose.yml             # Orquestación de servicios Docker
├── .devcontainer/                 # Configuración de Dev Containers (VS Code)
├── .github/workflows/
│   └── weekly_content.yml         # GitHub Actions Workflow (Cron semanal)
├── requirements.txt               # Dependencias de Python
├── .env.example                   # Plantilla de variables de entorno
├── data/
│   ├── sample/                    # Datos estáticos para ejecuciones de prueba/offline
│   ├── generated/                 # Archivos finales en producción (JSON, JPG, MP4)
│   └── demo_output/               # Salida temporal generada por demo.py
├── src/
│   ├── fetch_trending.py          # Etapa 1: Cliente Spotify & ranking de tendencias
│   ├── lastfm_client.py           # Etapa 1: Cliente Last.fm
│   ├── local_render_client.py     # Etapa 2: Motor de renderizado HTML a Imagen (Playwright)
│   ├── generate_duels.py          # Etapa 2: Generador de enfrentamientos (Lun/Vie)
│   ├── generate_top10.py          # Etapa 2: Generador del Top 10 LatAm
│   ├── render_reel.py             # Puente Python -> Remotion para render de video .mp4
│   ├── demo.py                    # Script de demostración interactivo/offline
│   └── templates/                 # Plantillas HTML/CSS (Jinja2) para imágenes estáticas
└── remotion-reels/                # Proyecto Node.js / React Remotion para video
    ├── src/compositions/          # Composiciones (DueloReel.tsx, Top10Reel.tsx)
    ├── src/components/            # UI de marca y efectos visuales
    └── props/                     # Archivos de prueba para renderizado de Reels

```

---
