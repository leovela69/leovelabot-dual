FROM python:3.11-slim

LABEL maintainer="C8L Agency"
LABEL description="@leovelabot — Bot Multi-Agente IA con Aprendizaje Evolutivo"

# Instalar FFmpeg para el pipeline de vídeo
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python (capa cacheada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p /tmp/leovelabot_videos
RUN mkdir -p /app/agents/memory_data

# Puerto del health-check
EXPOSE 8080

# Variables de entorno por defecto
ENV HEALTH_PORT=8080
ENV TEMP_DIR=/tmp/leovelabot_videos
ENV PYTHONUNBUFFERED=1

CMD ["python", "whatsapp_bot.py"]
