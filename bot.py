# -*- coding: utf-8 -*-
"""
@leovelabot — Bot Multi-Agente de Telegram para C8L Agency.
Abierto para todos, gratuito, con IA que aprende y evoluciona.
"""

import io
import os
import sys
import signal
import logging
import json
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Asegurar que el directorio del bot está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    TELEGRAM_BOT_TOKEN,
    ADMIN_CHAT_ID,
    BOT_NAME,
    HEALTH_PORT,
    validate_config,
)
from agents.orchestrator import AgentOrchestrator
from agents.chat_agent import ChatAgent
from agents.image_agent import ImageAgent
from agents.video_agent import VideoAgent
from agents.video_pipeline import VideoPipeline
from agents.code_agent import CodeAgent
from agents.design_agent import DesignAgent
from agents.memory import BotMemory

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("leovelabot")

# ---------------------------------------------------------------------------
# Validar configuración (solo si es ejecución directa, no importación)
# ---------------------------------------------------------------------------
_is_main = __name__ == "__main__"

if _is_main:
    if not validate_config():
        sys.exit(1)
elif not TELEGRAM_BOT_TOKEN:
    # Importado pero sin token — loguear aviso pero no crashear
    logger.warning("⚠️ bot.py importado sin TELEGRAM_BOT_TOKEN — funcionalidad Telegram limitada")

# ---------------------------------------------------------------------------
# Instancias globales
# ---------------------------------------------------------------------------
bot = TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown") if TELEGRAM_BOT_TOKEN else None
memory = BotMemory()
orchestrator = AgentOrchestrator()

# Registrar todos los agentes
chat_agent = ChatAgent()
image_agent = ImageAgent()
video_agent = VideoAgent()
video_pipeline = VideoPipeline()
code_agent = CodeAgent()
design_agent = DesignAgent()

orchestrator.register_agent("CHAT", chat_agent)
orchestrator.register_agent("IMAGE", image_agent)
orchestrator.register_agent("VIDEO_SHORT", video_agent)
orchestrator.register_agent("VIDEO_LONG", video_pipeline)
orchestrator.register_agent("CODE", code_agent)
orchestrator.register_agent("DESIGN", design_agent)

# Event loop para async
loop = asyncio.new_event_loop()


def run_async(coro):
    """Ejecuta una corutina async desde código sync."""
    return loop.run_until_complete(coro)


# ---------------------------------------------------------------------------
# Menú de bienvenida
# ---------------------------------------------------------------------------
WELCOME_MESSAGE = """🦁 *¡Bienvenido a C8L Agency, {name}!*

Soy *Leo*, tu asistente IA con superpoderes. Puedo hacer _cualquier cosa_ que me pidas:

🎨 *Crear imágenes* — "Dibuja un león cyberpunk"
🎬 *Generar vídeos* — "Haz un vídeo de 2 minutos sobre el espacio"
💻 *Programar* — "Crea un juego Snake en HTML"
🎯 *Diseñar* — "Diseña un logo para mi marca"
💬 *Conversar* — Pregúntame lo que quieras

*No necesitas código ni registro.* Solo escríbeme lo que necesites y me pongo a trabajar. 🚀

Escribe /help para ver todos los comandos."""

HELP_MESSAGE = """🦁 *Comandos de Leo Bot*

/start — Mensaje de bienvenida
/help — Este menú de ayuda
/stats — Mis estadísticas y aprendizaje
/evolve — Forzar una evolución (auto-mejora)
/clear — Limpiar mi memoria de tu conversación
/about — Información sobre C8L Agency

*O simplemente escríbeme lo que necesites:*
• _"Genera una imagen de un atardecer cyberpunk"_
• _"Crea un vídeo corto de un gato en el espacio"_
• _"Hazme un juego de naves espaciales"_
• _"Diseña un banner para YouTube"_
• _"Explícame cómo funciona la IA"_

¡Estoy aquí 24/7 para ayudarte! 🤖✨"""


# ---------------------------------------------------------------------------
# Handlers de comandos
# ---------------------------------------------------------------------------
@bot.message_handler(commands=["start"])
def cmd_start(message: Message) -> None:
    """Saludo de bienvenida — abierto para todos."""
    name = message.from_user.first_name or "amigo"
    logger.info(f"🆕 /start de {name} (chat_id={message.chat.id})")

    # Rastrear usuario en la memoria
    memory.track_user_interaction(message.chat.id, name, "START")

    # Botones inline de acciones rápidas
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎨 Crear Imagen", callback_data="quick_image"),
        InlineKeyboardButton("🎬 Crear Vídeo", callback_data="quick_video"),
        InlineKeyboardButton("💻 Programar Algo", callback_data="quick_code"),
        InlineKeyboardButton("🎯 Diseñar", callback_data="quick_design"),
    )

    bot.reply_to(message, WELCOME_MESSAGE.format(name=name), reply_markup=markup)


@bot.message_handler(commands=["help"])
def cmd_help(message: Message) -> None:
    """Menú de ayuda."""
    bot.reply_to(message, HELP_MESSAGE)


@bot.message_handler(commands=["stats"])
def cmd_stats(message: Message) -> None:
    """Muestra las estadísticas de aprendizaje del bot."""
    stats = memory.get_stats_summary()
    user_ctx = memory.get_user_context(message.chat.id)
    bot.reply_to(message, f"{stats}\n{user_ctx}")


@bot.message_handler(commands=["evolve"])
def cmd_evolve(message: Message) -> None:
    """Fuerza una reflexión evolutiva del bot."""
    bot.reply_to(message, "🧬 Analizando mi evolución... dame un momento.")
    try:
        result = run_async(memory.evolve())
        bot.send_message(message.chat.id, f"🧬 *Evolución completada:*\n\n{result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error durante la evolución: {e}")


@bot.message_handler(commands=["clear"])
def cmd_clear(message: Message) -> None:
    """Limpia el historial de conversación del usuario."""
    chat_agent.clear_history(message.chat.id)
    bot.reply_to(message, "🧹 Historial de conversación limpiado. ¡Empezamos de cero!")


@bot.message_handler(commands=["about"])
def cmd_about(message: Message) -> None:
    """Información sobre C8L Agency."""
    bot.reply_to(
        message,
        (
            "🦁 *C8L Agency*\n\n"
            "Plataforma de producción musical y gaming con IA.\n\n"
            "🎵 Beats y producción musical cuántica\n"
            "🎰 Casino virtual con C8L Coins\n"
            "🎮 Gaming y streaming en vivo\n"
            "🤖 Asistentes IA que evolucionan\n\n"
            "🌐 c8lagency.com"
        ),
    )


# ---------------------------------------------------------------------------
# Handlers de callbacks (botones inline)
# ---------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("quick_"))
def handle_quick_action(call: CallbackQuery) -> None:
    """Maneja los botones de acción rápida."""
    action = call.data.replace("quick_", "")
    prompts = {
        "image": "¿Qué imagen quieres que cree? Describe lo que imaginas:",
        "video": "¿Qué vídeo quieres? Describe la escena y la duración:",
        "code": "¿Qué quieres que programe? Describe tu idea (juego, app, script...):",
        "design": "¿Qué quieres que diseñe? (logo, banner, UI, miniatura...):",
    }
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"✨ {prompts.get(action, '¿Qué necesitas?')}")


# ---------------------------------------------------------------------------
# Handler principal — Procesa TODOS los mensajes de texto
# ---------------------------------------------------------------------------
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_message(message: Message) -> None:
    """Procesa cualquier mensaje de texto a través del orquestador."""
    user_name = message.from_user.first_name or "Usuario"
    chat_id = message.chat.id
    text = message.text

    logger.info(f"📩 [{user_name}] ({chat_id}): {text[:80]}...")

    # Indicador de "escribiendo..."
    bot.send_chat_action(chat_id, "typing")

    # Rastrear interacción
    memory.track_user_interaction(chat_id, user_name, "MESSAGE")

    try:
        # Procesar con el orquestador
        result = run_async(orchestrator.process(text, chat_id, user_name))

        # Enviar la respuesta según el tipo
        _send_result(chat_id, result, message.message_id)

        # Registrar episodio y aprender
        intent = run_async(orchestrator.classify_intent(text))
        memory.record_episode(
            chat_id=chat_id,
            user_name=user_name,
            intent=intent,
            user_message=text,
            result_type=result.get("type", "text"),
            success=True,
        )

        # Aprender de la tarea (async, en background)
        try:
            run_async(memory.learn_from_task(
                user_message=text,
                intent=intent,
                result=str(result.get("content", ""))[:300],
                success=True,
            ))
        except Exception:
            pass  # El aprendizaje no debe bloquear la respuesta

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Error inesperado: {str(e)}\n\nInténtalo de nuevo.")

        # Registrar el error para aprender
        memory.record_episode(
            chat_id=chat_id,
            user_name=user_name,
            intent="ERROR",
            user_message=text,
            result_type="error",
            success=False,
            notes=str(e),
        )


# ---------------------------------------------------------------------------
# Handler de fotos — El usuario puede enviar fotos para editar/analizar
# ---------------------------------------------------------------------------
@bot.message_handler(content_types=["photo"])
def handle_photo(message: Message) -> None:
    """Procesa fotos enviadas por el usuario."""
    user_name = message.from_user.first_name or "Usuario"
    caption = message.caption or "Analiza esta imagen"

    bot.send_chat_action(message.chat.id, "typing")

    bot.reply_to(
        message,
        (
            "📸 ¡Recibí tu imagen! Por ahora puedo:\n\n"
            "• Generar imágenes nuevas desde texto\n"
            "• Crear diseños con estilo C8L\n\n"
            "Descríbeme qué quieres hacer con la imagen o qué quieres crear."
        ),
    )


# ---------------------------------------------------------------------------
# Enviar resultados al chat
# ---------------------------------------------------------------------------
def _send_result(chat_id: int, result: dict, reply_to: int = None) -> None:
    """Envía el resultado del agente al chat de Telegram."""
    result_type = result.get("type", "text")
    content = result.get("content", "")
    caption = result.get("caption", "")

    try:
        if result_type == "text":
            # Dividir mensajes largos (Telegram limita a 4096 chars)
            text = str(content)
            while text:
                chunk = text[:4096]
                bot.send_message(chat_id, chunk)
                text = text[4096:]

        elif result_type == "image":
            bot.send_chat_action(chat_id, "upload_photo")
            photo = io.BytesIO(content)
            photo.name = "image.png"
            bot.send_photo(chat_id, photo, caption=caption[:1024])

        elif result_type == "video":
            bot.send_chat_action(chat_id, "upload_video")
            video = io.BytesIO(content)
            video.name = "video.mp4"
            bot.send_video(chat_id, video, caption=caption[:1024], timeout=120)

        elif result_type == "video_parts":
            # Vídeo largo dividido en partes
            parts = content
            bot.send_message(chat_id, f"📹 Enviando vídeo en {len(parts)} partes...")
            for i, part_bytes in enumerate(parts):
                bot.send_chat_action(chat_id, "upload_video")
                video = io.BytesIO(part_bytes)
                video.name = f"video_parte_{i+1}.mp4"
                bot.send_video(
                    chat_id, video,
                    caption=f"📹 Parte {i+1}/{len(parts)}",
                    timeout=120,
                )

        elif result_type == "file":
            bot.send_chat_action(chat_id, "upload_document")
            doc = io.BytesIO(content)
            doc.name = result.get("filename", "archivo.txt")
            bot.send_document(chat_id, doc, caption=caption[:1024])

        # Enviar actualizaciones de progreso si las hay
        progress = result.get("progress", [])
        for update in progress:
            bot.send_message(chat_id, update)

    except Exception as e:
        logger.error(f"Error enviando resultado: {e}")
        bot.send_message(chat_id, f"❌ Error enviando el resultado: {str(e)}")


# ---------------------------------------------------------------------------
# Health-check HTTP server
# ---------------------------------------------------------------------------
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = {
            "status": "healthy",
            "bot": BOT_NAME,
            "agents": ["chat", "image", "video", "video_pipeline", "code", "design"],
            "memory": {
                "episodes": len(memory.episodes),
                "skills": len(memory.skills),
                "users": len(memory.profiles),
            },
        }
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, fmt, *args):
        return


def _run_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), _HealthHandler)
    logger.info(f"🏥 Health-check en puerto {HEALTH_PORT}")
    server.serve_forever()


# ---------------------------------------------------------------------------
# Notificación de admin al arrancar
# ---------------------------------------------------------------------------
def _notify_admin_startup() -> None:
    """Envía un mensaje al admin cuando el bot arranca."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID no configurado — no se enviará notificación de arranque")
        return

    try:
        bot.send_message(
            int(ADMIN_CHAT_ID),
            (
                "🦁✅ *@leovelabot está ACTIVO*\n\n"
                "Todos los agentes están preparados y listos:\n\n"
                "💬 Chat Agent — Conversación IA\n"
                "🎨 Image Agent — Generación de imágenes\n"
                "🎬 Video Agent — Vídeos cortos\n"
                "📹 Video Pipeline — Vídeos largos (hasta 20 min)\n"
                "💻 Code Agent — Programación y videojuegos\n"
                "🎯 Design Agent — Diseños C8L\n"
                "🧠 Memory System — Aprendizaje activo\n\n"
                f"📊 Memoria: {len(memory.episodes)} episodios, "
                f"{len(memory.skills)} habilidades\n\n"
                "🚀 *Todo listo. Escríbeme lo que necesites.*"
            ),
        )
        logger.info(f"📨 Notificación de arranque enviada a admin (chat_id={ADMIN_CHAT_ID})")
    except Exception as e:
        logger.error(f"Error enviando notificación al admin: {e}")


# ---------------------------------------------------------------------------
# Evolución periódica automática
# ---------------------------------------------------------------------------
def _auto_evolve_loop():
    """Ejecuta evolución automática cada 100 episodios."""
    import time
    last_count = len(memory.episodes)
    while True:
        time.sleep(300)  # Revisar cada 5 minutos
        current_count = len(memory.episodes)
        if current_count - last_count >= 100:
            logger.info("🧬 Evolución automática activada (100 nuevos episodios)")
            try:
                asyncio.run(memory.evolve())
            except Exception as e:
                logger.error(f"Error en evolución automática: {e}")
            last_count = current_count


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
def _handle_signal(signum, _frame):
    logger.info(f"Señal {signum} recibida — guardando memoria y apagando...")
    memory.save_all()
    bot.stop_polling()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Health-check server (daemon)
    threading.Thread(target=_run_health_server, daemon=True).start()

    # Evolución automática (daemon)
    threading.Thread(target=_auto_evolve_loop, daemon=True).start()

    # Notificar al admin
    _notify_admin_startup()

    # Arrancar el bot
    logger.info(f"🚀 @{BOT_NAME} arrancado — Modo polling — Abierto para todos")
    logger.info(f"🧠 Agentes: chat, image, video, video_pipeline, code, design")
    logger.info(f"📚 Memoria: {len(memory.episodes)} episodios, {len(memory.skills)} habilidades")

    bot.infinity_polling(timeout=30, long_polling_timeout=25)


if __name__ == "__main__":
    main()
