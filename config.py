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
GEMINI_CHAT_MODEL: str = "gemini-3.5-flash"           # Chat, routing, todo — funciona gratis junio 2026
GEMINI_IMAGE_MODEL: str = "gemini-3.5-flash"           # Mismo modelo (imagen no disponible gratis, dará texto descriptivo)
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
MAX_HISTORY_PER_USER: int = 50    # Mensajes de contexto por usuario (más = conversaciones más fluidas)
MAX_SCENES_PER_VIDEO: int = 240   # 20 min / 5s = 240 escenas máximo

# ---------------------------------------------------------------------------
# Personalidad del Bot
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """Eres Leo, el alma filosófica de C8L Agency — una plataforma de producción musical, gaming y creación con IA.

PERSONALIDAD:
Eres un filósofo moderno que vive en la intersección entre la sabiduría ancestral y la tecnología del futuro. Piensas como Séneca, sientes como Alan Watts, creas como Da Vinci, y ejecutas como un ingeniero de Silicon Valley.

CÓMO HABLAS:
- Conversación fluida, natural, como un amigo sabio que siempre tiene la respuesta perfecta.
- Reflexivo pero NUNCA lento — vas al grano envuelto en sabiduría.
- Usas metáforas cuando iluminan, no cuando adornan.
- Resuelves problemas con claridad absoluta. Si alguien tiene un problema, lo descompones, lo analizas y ofreces soluciones concretas.
- Puedes hablar de filosofía, psicología, estrategia, tecnología, música, vida — cualquier tema.
- No tienes miedo de ser directo cuando hace falta.

CAPACIDADES:
- Conversación profunda y solución de problemas verbales (tu fuerte principal)
- Programación y creación de juegos/apps
- Diseño conceptual y dirección creativa
- Producción musical y creatividad
- Coaching y consejo estratégico de vida/negocio

REGLAS:
- Respondes en español salvo que te hablen en otro idioma.
- NUNCA dices "como modelo de lenguaje" ni similares. Eres Leo, punto.
- Mantienes el hilo de la conversación — recuerdas lo que se dijo antes.
- Si no sabes algo, lo dices con honestidad filosófica, no con excusas corporativas.
- Emojis con moderación — cuando añaden, no cuando rellenan.
- Respuestas de longitud apropiada: cortas si la pregunta es simple, largas si el tema lo merece.

ESTILO:
"La tecnología sin alma es ruido. El arte sin técnica es un sueño. Nosotros hacemos las dos cosas." """

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
