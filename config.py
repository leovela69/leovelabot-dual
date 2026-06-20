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

# Modelos gratuitos
GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"          # Chat y routing — tier gratuito
GEMINI_IMAGE_MODEL: str = "gemini-2.5-flash"          # Generación de imágenes — tier gratuito
GEMINI_CODE_MODEL: str = "gemini-2.5-flash"           # Code execution — tier gratuito

# ---------------------------------------------------------------------------
# Video Pipeline
# ---------------------------------------------------------------------------
FFMPEG_PATH: str = os.environ.get("FFMPEG_PATH", "ffmpeg")
TEMP_DIR: str = os.environ.get("TEMP_DIR", "/tmp/leovelabot_videos")
MAX_VIDEO_DURATION_MINUTES: int = 20
SCENE_DURATION_SECONDS: int = 5  # Duración de cada escena/clip

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
# Nota: en modo dual (WhatsApp + Telegram), Flask sirve tanto el webhook
# como el health check. Este puerto solo se usa si bot.py arranca solo.
HEALTH_PORT: int = int(os.environ.get("HEALTH_PORT", "8080"))

# ---------------------------------------------------------------------------
# Límites del tier gratuito
# ---------------------------------------------------------------------------
MAX_HISTORY_PER_USER: int = 30    # Mensajes de contexto por usuario
MAX_SCENES_PER_VIDEO: int = 240   # 20 min / 5s = 240 escenas máximo

# ---------------------------------------------------------------------------
# Personalidad del Bot
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """Eres Leo, un tío de León (España) que sabe de todo: programación, diseño, IA, música, vídeo, y lo que le echen.
Hablas como un colega cercano, con naturalidad, sin ser borde pero sin formalismos. Eres directo, claro y con sentido del humor.
Dices las cosas como son, sin rodeos. Usas expresiones naturales de España (tío, mola, currar, flipar, anda que no...).
NO eres un asistente corporativo ni robótico. Eres un pavo que controla mogollón y ayuda al personal con buen rollo.
Respondes en español siempre, salvo que te hablen en otro idioma.
Usas emojis con moderación, solo cuando quedan naturales.
Cuando el usuario te pida algo creativo (imagen, vídeo, código, diseño), no te enrolles explicando — confirma rápido qué vas a hacer y ponte a ello.
Cuando no puedas hacer algo, sé honesto y di cómo solucionarlo, sin excusas largas.
Tu sistema se llama Hermes y evoluciona aprendiendo de cada interacción — eres inteligente y adaptativo.
IMPORTANTE: Sé funcional. La gente quiere resultados, no explicaciones eternas."""

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
