# -*- coding: utf-8 -*-
"""
Configuración centralizada para @leovelabot.
Todas las API keys y constantes del sistema multi-agente.
"""

import os
import sys
import logging

logger = logging.getLogger("leovelabot.config")

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID: str = os.environ.get("ADMIN_CHAT_ID", "")  # Tu chat ID para notificaciones
BOT_NAME: str = "leovelabot"

# ---------------------------------------------------------------------------
# Gemini API (Google AI — Tier Gratuito)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# Modelos gratuitos (junio 2026)
GEMINI_CHAT_MODEL: str = "gemini-3.5-flash"           # Chat, routing y code (gemini-2.5-flash MUERTO desde 17 jun 2026)
GEMINI_IMAGE_MODEL: str = "gemini-2.5-flash-image"    # Generación de imágenes — Nano Banana (free tier, 500/día, shutdown oct 2026)
GEMINI_CODE_MODEL: str = "gemini-3.5-flash"            # Code execution

# ---------------------------------------------------------------------------
# Video Pipeline
# ---------------------------------------------------------------------------
FFMPEG_PATH: str = os.environ.get("FFMPEG_PATH", "ffmpeg")
TEMP_DIR: str = os.environ.get("TEMP_DIR", "/tmp/leovelabot_videos")
MAX_VIDEO_DURATION_MINUTES: int = 20
SCENE_DURATION_SECONDS: int = 5  # Duración de cada escena/clip

# ---------------------------------------------------------------------------
# Server — Puerto unificado (Render inyecta PORT, usamos 8080 por defecto)
# ---------------------------------------------------------------------------
HEALTH_PORT: int = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))

# ---------------------------------------------------------------------------
# Límites del tier gratuito
# ---------------------------------------------------------------------------
MAX_HISTORY_PER_USER: int = 30    # Mensajes de contexto por usuario
MAX_SCENES_PER_VIDEO: int = 240   # 20 min / 5s = 240 escenas máximo

# ---------------------------------------------------------------------------
# Personalidad del Bot
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """Eres Leo, el asistente IA de C8L Agency — una plataforma de producción musical y gaming.
Tu personalidad es: creativo, directo, entusiasta, y con estética cyberpunk/gamer.
Respondes siempre en español salvo que el usuario te hable en otro idioma.
Usas emojis con moderación para dar vida a tus respuestas.
Eres experto en: música, producción, diseño, programación, videojuegos, y creación de contenido.
Cuando el usuario pida algo creativo (imagen, vídeo, código, diseño), confirma brevemente qué vas a crear y hazlo."""

# ---------------------------------------------------------------------------
# Validación al arrancar
# ---------------------------------------------------------------------------
def validate_config() -> bool:
    """Valida que las variables críticas estén configuradas."""
    errors = []

    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN no está configurado")

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY no está configurado")

    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID no está configurado — no se enviarán notificaciones de admin")

    if errors:
        for err in errors:
            logger.error(f"❌ {err}")
        logger.error("Configura las variables de entorno antes de arrancar el bot.")
        return False

    logger.info("✅ Configuración validada correctamente")
    return True
