# Imagen ligera de Python. 3.11-slim es suficiente para requests + dotenv.
FROM python:3.11-slim

# Evita que Python genere .pyc y fuerza logs sin buffer (mejor para ver
# el output del script en tiempo real dentro del contenedor).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos primero solo requirements.txt para aprovechar la cache de Docker:
# si no cambian las dependencias, no se reinstala nada en builds futuros.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto.
COPY . .

WORKDIR /app/src

# Comando por default: muestra ayuda. El uso real se hace pasando argumentos,
# ej: docker compose run --rm vinylr python fetch_trending.py --top 10
CMD ["python", "fetch_trending.py", "--help"]
