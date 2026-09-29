# Vinylr Content Engine — Contexto del Proyecto

> Documento de referencia/presentación. Para el detalle técnico iteración por
> iteración, ver `PROGRESS.md`.

---

## 1. Contexto del proyecto

Este proyecto es parte del reto de innovación de **TREP CAMP y EPIC LAB
(ITAM)** para la startup real **Vinylr** — el "Letterboxd de la música",
orientado al mercado hispanohablante de Latinoamérica. Vinylr integra tres
pilares: (1) calificar y rankear álbumes mediante duelos de comparación
directa ("A vs B"), (2) diarios personales de conciertos/festivales, y (3)
un marketplace de vinilos.

### El problema de crecimiento
Vinylr tiene más de 11.2K seguidores en redes sociales, pero solo ~1,000
usuarios activos en la app — una brecha crítica de conversión. Una auditoría
de su Instagram (@vinylr.app) identificó tres causas:

1. **Percepción equivocada ("parece Spotify")** — el contenido actual (portadas
   estáticas, "This Week's Picks") transmite la idea de una plataforma pasiva
   de escucha, no una herramienta interactiva para construir tu identidad musical.
2. **Falta de claridad inmediata** — no se entiende a primera vista que Vinylr
   es un motor interactivo de votación "A vs B", ni que es "el Letterboxd de
   la música".
3. **Desconexión lingüística y cultural** — el mercado meta es LatAm/español,
   pero el 100% del contenido en redes está en inglés.

## 2. Objetivo deseado

Resolver el Track #1 del reto: **usar Inteligencia Artificial para convertir
el alcance de redes sociales en descargas virales y activación de usuarios**,
con un límite de tiempo real de **2 semanas** (duración del hackathon).

## 3. Idea / propuesta considerada hasta ahora

### Propuesta de valor
Transformar el alcance en redes en descargas efectivas mediante un flujo
semiautomatizado que convierte las tendencias musicales de LatAm en duelos
visuales "VS" en español, mostrando la mecánica real de Vinylr directamente
en el feed — con **revisión humana obligatoria** antes de publicar cualquier
pieza.

### Cadencia de contenido
- **Lunes y Viernes:** duelos "Álbum A vs B" — el contenido nuevo/automatizado
  que este proyecto construye.
- **Miércoles y Sábado:** formatos existentes de Vinylr (*Top-Ranked Picks*,
  *Critics' Picks*) — ya funcionan de forma independiente, **fuera del
  alcance** de este pipeline.

### Qué SÍ incluye el MVP
- Script de automatización ligera para extraer, 1 vez por semana, los
  álbumes con mayor tendencia en países clave de LatAm.
- Generación asistida por IA de la pieza visual "Álbum A vs B", con revisión
  humana obligatoria (~5 min) antes de programar la publicación.
- Enlace de atribución rastreable (UTM/Bitly) para medir conversión real a
  descargas — *pendiente de construir*.

### Qué NO incluye (decisión explícita)
- Publicación 100% autónoma sin revisión humana.
- Tocar los formatos existentes de Miércoles/Sábado.
- Bots conversacionales en DMs o integraciones de software avanzadas.

### Arquitectura técnica construida hasta ahora

```
1. DATOS — Spotify API (Client Credentials Flow, gratis)
   → Top 50 + New Releases por país (MX, AR, CO, CL, Global) → top 5 álbumes/semana

2. GENERACIÓN DE IMAGEN — APITemplate.io (plan gratuito, 50 imágenes/mes)
   → Plantilla "Álbum A vs B" (1080x1920) → 2 duelos/semana (Lunes, Viernes)
   (Se eligió sobre Canva porque Canva Free no tiene API de generación automática)

3. EMPAQUETADO — Docker + VS Code Dev Containers
   → Entorno reproducible; disponible como alternativa al venv local

4. AUTOMATIZACIÓN SEMANAL — GitHub Actions
   → Corre el pipeline cada lunes vía cron, sube resultados como artifact
     descargable para revisión humana (nunca publica solo)

5. DEMO ON-DEMAND — script con doble red de seguridad
   → Si no hay credenciales/internet, usa datos de ejemplo + genera la
     imagen localmente con Pillow. Pensado para mostrar el concepto en
     cualquier momento (ej. frente a jueces del hackathon) sin depender de
     que todo esté 100% configurado.

6. REVISIÓN HUMANA — manual, ~5 min, antes de programar cualquier publicación

7. (OPCIONAL) VIDEO — Remotion (remotion-reels/)
   → Mismos dicts de álbumes/Top 10 → Reel .mp4 (9:16), vía src/render_reel.py
   → Activable en el demo con --with-reels; solo local por ahora (el Dockerfile
     y GitHub Actions siguen siendo 100% Python, sin Node)
```

### Pendiente de construir
- Enlace de atribución (UTM/Bitly) para medir conversión Instagram → descarga.
- Brief creativo en español (texto/copy que acompaña cada post, no solo la imagen).
- Definir y validar las 3 hipótesis del proyecto: tasa de interacción, conversión
  a descargas, y eficiencia operativa (<15 min/semana de intervención humana).

---

*Última actualización: 2026-09-23. Ver `PROGRESS.md` para el detalle completo
de cada iteración y decisión técnica.*
