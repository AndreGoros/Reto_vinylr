# Vinylr Reels — plantillas de video (Remotion)

Plantillas de video 9:16 (1080×1920) con la identidad de Vinylr (`BRAND_GUIDE.md`),
pensadas para llenarse con los mismos datos que ya produce el pipeline de Python
(`fetch_trending.py` → `generate_duels.py` / `generate_top10.py`) y sacar un
`.mp4` listo para Reels/TikTok — con la misma revisión humana obligatoria que
el resto del proyecto (esto NO publica nada solo).

## Por qué esta combinación

| Pieza | Para qué se usó aquí |
|---|---|
| **Remotion** | Es el motor real: renderiza React a video frame por frame, determinista (a diferencia de una animación con `requestAnimationFrame`, que Remotion no puede capturar de forma confiable). Cada composición (`DueloReel`, `Top10Reel`) es un componente React normal que recibe *props* — ahí es donde se "rellena el hueco". |
| **ReactBits** | Es una librería de efectos de texto/UI (`BlurText`, `ShinyText`, etc.) pensada para apps normales, con GSAP/CSS-timing basado en reloj real. Eso **no sirve tal cual** dentro de Remotion (cada frame se renderiza aparte, hasta en paralelo). Por eso, en vez de importar el paquete, `src/components/reactbits.tsx` **reimplementa el mismo efecto visual pero impulsado por `useCurrentFrame()`**, para que el resultado sea 100% reproducible al exportar. |
| **21st.dev** | Es un directorio de componentes UI (React + Tailwind) pensado para inspiración/prototipado rápido de interfaces, no para video. Aquí se usa como **fuente de referencia visual** (tarjetas, badges, layouts) — si copias un bloque de ahí, pégalo en `src/components/` y aplícale el mismo criterio que a ReactBits: cualquier animación debe depender de `frame`, no de tiempo real, temporizadores o `IntersectionObserver`. Los componentes puramente estáticos (sin animación) sí se pueden usar directo. |

## Estructura

```
remotion-reels/
├── src/
│   ├── theme.ts               # colores/fuentes de BRAND_GUIDE.md, tamaños de canvas
│   ├── schema.ts               # forma de los props (zod) — el "contrato" del hueco a rellenar
│   ├── components/
│   │   ├── reactbits.tsx       # BlurText, ShinyText (frame-driven)
│   │   ├── ui.tsx               # Grain, Backdrop, Masthead, Vinyl (marca Vinylr)
│   │   └── Cover.tsx            # carátula tipo polaroid + vinilo, con entrada animada
│   ├── compositions/
│   │   ├── DueloReel.tsx        # "Álbum A vs B" en video (11s)
│   │   └── Top10Reel.tsx        # cuenta regresiva Top 10 (duración según nº de canciones)
│   └── Root.tsx                 # registra las composiciones + sus props de ejemplo
├── props/
│   ├── duelo.sample.json        # generado desde data/sample/trending_albums_sample.json
│   └── top10.sample.json        # generado desde data/sample/Top10sample.json
└── remotion.config.ts
```

## Setup (una sola vez)

Requiere Node.js 18+.

```bash
cd remotion-reels
npm install
```

## Ver/editar visualmente (Remotion Studio)

```bash
npm run studio
```

Abre un preview en vivo de `DueloReel` y `Top10Reel` con los props de ejemplo,
con timeline scrubbing — útil para ajustar tiempos/colores antes de exportar.

## Rellenar el hueco y exportar un MP4

### Opción A — desde Python (recomendado, mismo flujo que las imágenes)

`src/render_reel.py` es el puente: toma el JSON que ya arma `build_duels()` /
`build_top10_latam()`, lo mapea 1:1 a los props de la plantilla (mismos nombres
de campo: `cover_url`, `artists`, `country`) y llama a `npx remotion render`.

```bash
cd src
python render_reel.py --kind duelo --type country   # slot Lunes (#1 vs #2 por país)
python render_reel.py --kind duelo --type cross      # slot Viernes (país vs país)
python render_reel.py --kind top10                   # con data/sample/Top10sample.json
python render_reel.py --kind top10 --live             # arma el Top 10 con Last.fm real
```

Los `.mp4` quedan en `data/generated/<fecha>/reels/`, junto a un
`manifest_reels_*.json` — igual patrón que `generate_duels.py`. **Nada se
publica automáticamente.**

### Opción B — Remotion CLI directo, con un JSON de props a mano

```bash
npx remotion render DueloReel out/duelo.mp4 --props=props/duelo.sample.json
npx remotion render Top10Reel out/top10.mp4 --props=props/top10.sample.json
```

El JSON de props puede venir de cualquier lado (otra API, un CMS, etc.) siempre
que respete `src/schema.ts` — ahí es literalmente donde se define "el hueco".

## Notas

- **Imágenes rotas rompen el render.** Remotion cancela el render completo si
  un `<Img>` no carga (a propósito, para no exportar un video con huecos en
  silencio). `render_reel.py` valida cada `cover_url` con un `HEAD` antes de
  lanzar el render y omite ese duelo si falla — mismo criterio defensivo que
  ya usa `local_render_client.py` con `onerror` en las plantillas HTML.
- **Duración dinámica del Top 10**: `Top10Reel` usa `calculateMetadata` para
  ajustar automáticamente los frames totales al número real de canciones
  (3 a 10), así que nunca hay tiempo muerto ni corte.
- **Fuentes**: se cargan con `@remotion/google-fonts` (Archivo Black +
  Newsreader), las mismas que ya usan los templates HTML — no dependen de que
  el sistema tenga la fuente instalada, así el render es reproducible en
  cualquier máquina/CI.
- No pude correr `npm install` ni un render real en este entorno (sin acceso
  a red saliente), así que el código no quedó verificado en vivo — mismo
  aviso que ya tienen `fetch_trending.py`/`README.md` del proyecto: pruébalo
  una vez con `npm run studio` antes de conectarlo al pipeline automático.
