# -*- coding: utf-8 -*-
"""
@LeoVelaBot — Bot Multi-Agente de WhatsApp para C8L Agency.
Usa la WhatsApp Cloud API (Meta) con los mismos agentes que Telegram.
Servidor webhook Flask que recibe mensajes y responde via los agentes IA.
"""

import io
import os
import sys
import json
import logging
import asyncio
import hashlib
import hmac
import base64
import tempfile
import requests
import threading
from flask import Flask, request, jsonify

# Asegurar que el directorio actual está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wa_config import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_ID,
    VERIFY_TOKEN,
    ADMIN_PHONE,
    WEBHOOK_PORT,
    validate_wa_config,
)

# Importar agentes compartidos
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
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("leovelabot.whatsapp")

# ---------------------------------------------------------------------------
# Validar configuracion
# ---------------------------------------------------------------------------
if not validate_wa_config():
    logger.error("Configuracion de WhatsApp incompleta. Revisa las variables de entorno.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Instancias globales (compartidas entre Telegram y WhatsApp en RAM)
# ---------------------------------------------------------------------------
memory = BotMemory()
orchestrator = AgentOrchestrator()

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

# Conectar memoria al orquestador para contexto enriquecido
orchestrator.set_memory(memory)

# Event loop para async — en un hilo dedicado para evitar deadlocks con Flask
import concurrent.futures

_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_loop_thread.start()


def run_async(coro):
    """Ejecuta una corutina async desde código sync de Flask sin bloquear el event loop."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=120)  # Timeout de 2 min para tareas pesadas (vídeo)


# ---------------------------------------------------------------------------
# WhatsApp Cloud API helpers
# ---------------------------------------------------------------------------
API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"
MEDIA_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/media"
HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}


def send_text(to: str, text: str) -> dict:
    """Envia un mensaje de texto por WhatsApp."""
    chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
    result = None
    for chunk in chunks:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": chunk},
        }
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        result = r.json()
        logger.info(f"Texto enviado a {to}: {r.status_code}")
    return result


def send_image(to: str, image_bytes: bytes, caption: str = "") -> dict:
    """Envia una imagen por WhatsApp."""
    media_headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {
        "file": ("image.png", io.BytesIO(image_bytes), "image/png"),
        "messaging_product": (None, "whatsapp"),
        "type": (None, "image/png"),
    }
    r = requests.post(MEDIA_URL, headers=media_headers, files=files, timeout=60)
    media_result = r.json()
    media_id = media_result.get("id")

    if not media_id:
        logger.error(f"Error subiendo imagen: {media_result}")
        return send_text(to, f"No pude enviar la imagen. {caption}")

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"id": media_id, "caption": caption[:1024]},
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    return r.json()


def send_document(to: str, doc_bytes: bytes, filename: str, caption: str = "") -> dict:
    """Envia un documento/archivo por WhatsApp."""
    media_headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    mime = "text/html" if filename.endswith(".html") else "application/octet-stream"
    files = {
        "file": (filename, io.BytesIO(doc_bytes), mime),
        "messaging_product": (None, "whatsapp"),
        "type": (None, mime),
    }
    r = requests.post(MEDIA_URL, headers=media_headers, files=files, timeout=60)
    media_result = r.json()
    media_id = media_result.get("id")

    if not media_id:
        return send_text(to, f"No pude enviar el archivo. {caption}")

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {"id": media_id, "caption": caption[:1024], "filename": filename},
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    return r.json()


def send_video(to: str, video_bytes: bytes, caption: str = "") -> dict:
    """Envia un video por WhatsApp (max 16MB)."""
    size_mb = len(video_bytes) / (1024 * 1024)
    if size_mb > 16:
        return send_text(to, f"El video pesa {size_mb:.1f} MB (max 16 MB para WhatsApp). {caption}")

    media_headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {
        "file": ("video.mp4", io.BytesIO(video_bytes), "video/mp4"),
        "messaging_product": (None, "whatsapp"),
        "type": (None, "video/mp4"),
    }
    r = requests.post(MEDIA_URL, headers=media_headers, files=files, timeout=120)
    media_result = r.json()
    media_id = media_result.get("id")

    if not media_id:
        return send_text(to, f"No pude enviar el video. {caption}")

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": {"id": media_id, "caption": caption[:1024]},
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    return r.json()


def mark_as_read(message_id: str) -> None:
    """Marca un mensaje como leido."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)


def _download_wa_media(media_id: str) -> bytes | None:
    """Descarga un archivo multimedia de WhatsApp Cloud API."""
    try:
        # Paso 1: obtener la URL del media
        media_url = f"https://graph.facebook.com/v21.0/{media_id}"
        r = requests.get(media_url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}, timeout=15)
        media_info = r.json()
        download_url = media_info.get("url")

        if not download_url:
            logger.error(f"No se pudo obtener URL de media: {media_info}")
            return None

        # Paso 2: descargar el archivo
        r = requests.get(download_url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}, timeout=30)
        if r.status_code == 200:
            return r.content
        else:
            logger.error(f"Error descargando media: {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error descargando media de WhatsApp: {e}")
        return None


async def _process_image_with_context(image_bytes: bytes, instruction: str, chat_id: int, user_name: str) -> dict:
    """Procesa una imagen recibida con Gemini Vision — analiza, edita, o genera variaciones."""
    from google import genai
    from google.genai import types
    from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL, SYSTEM_PROMPT
    import base64

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Construir el prompt con la imagen
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        prompt_text = (
            f"{SYSTEM_PROMPT}\n\n"
            f"El usuario {user_name} te ha enviado una imagen con esta instrucción: '{instruction}'\n\n"
            f"Si te pide modificarla, generar una versión nueva, o algo creativo con ella, hazlo.\n"
            f"Si solo quiere saber qué es, descríbela con detalle.\n"
            f"Si te pide cambiar su cara, crear un avatar, o algo así, genera una imagen nueva basada en lo que ves.\n"
            f"Responde de forma natural como Leo (tío de León, cercano)."
        )

        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[image_part, prompt_text],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                temperature=0.8,
            ),
        )

        # Extraer resultado
        result_image = None
        result_text = ""

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    data = part.inline_data.data
                    result_image = base64.b64decode(data) if isinstance(data, str) else data
                elif hasattr(part, "text") and part.text:
                    result_text += part.text

        if result_image:
            return {
                "type": "image",
                "content": result_image,
                "caption": result_text[:1024] if result_text else f"Aquí tienes lo que me pediste, {user_name}",
            }
        else:
            return {
                "type": "text",
                "content": result_text or "He visto tu imagen pero no he podido generar una respuesta visual. Dime qué quieres que haga con ella.",
            }

    except Exception as e:
        logger.error(f"Error procesando imagen con Gemini: {e}", exc_info=True)
        return {
            "type": "text",
            "content": f"Uf, no he podido procesar la imagen: {str(e)}. ¿Me dices qué querías que hiciera?",
        }


def send_result(phone: str, result: dict) -> None:
    """Envia el resultado del agente al usuario de WhatsApp."""
    result_type = result.get("type", "text")
    content = result.get("content", "")
    caption = result.get("caption", "")

    try:
        if result_type == "text":
            send_text(phone, str(content))
        elif result_type == "image":
            send_image(phone, content, caption)
        elif result_type == "video":
            send_video(phone, content, caption)
        elif result_type == "file":
            filename = result.get("filename", "archivo.txt")
            send_document(phone, content, filename, caption)
        elif result_type == "video_parts":
            parts = content
            send_text(phone, f"Enviando video en {len(parts)} partes...")
            for i, part_bytes in enumerate(parts):
                send_video(phone, part_bytes, f"Parte {i+1}/{len(parts)}")
    except Exception as e:
        logger.error(f"Error enviando resultado: {e}")
        send_text(phone, f"Error enviando el resultado: {str(e)}")


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verificacion del webhook por Meta (challenge) - Versión unificada limpia para Render."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token and hmac.compare_digest(token, VERIFY_TOKEN):
        logger.info("Webhook verificado correctamente")
        from flask import Response
        return Response(challenge, mimetype="text/plain"), 200
    else:
        logger.warning(f"Verificacion fallida: mode={mode}")
        return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    """Recibe mensajes de WhatsApp y los procesa con los agentes."""
    data = request.get_json()

    if not data:
        return jsonify({"status": "no data"}), 200

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "no messages"}), 200

        msg = messages[0]
        msg_type = msg.get("type")
        msg_id = msg.get("id")
        phone = msg.get("from")

        contacts = value.get("contacts", [{}])
        user_name = contacts[0].get("profile", {}).get("name", "Usuario") if contacts else "Usuario"

        logger.info(f"Mensaje de {user_name} ({phone}): tipo={msg_type}")
        mark_as_read(msg_id)

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
            logger.info(f"Texto: {text[:80]}...")

            if text.lower() in ["/start", "hola", "hi", "menu"]:
                welcome = (
                    "Hola {name}! Soy Leo, tu asistente IA de C8L Agency.\n\n"
                    "Puedo hacer cualquier cosa que me pidas:\n\n"
                    "- Crear imagenes: \"Dibuja un leon cyberpunk\"\n"
                    "- Generar videos: \"Haz un video corto del espacio\"\n"
                    "- Programar: \"Crea un juego Snake en HTML\"\n"
                    "- Disenar: \"Disena un logo para mi marca\"\n"
                    "- Conversar: Preguntame lo que quieras\n\n"
                    "Solo escribeme lo que necesites!"
                ).format(name=user_name)
                send_text(phone, welcome)
                return jsonify({"status": "ok"}), 200

            if text.lower() == "/stats":
                stats = memory.get_stats_summary()
                ctx = memory.get_user_context(int(phone[-10:]))
                send_text(phone, f"{stats}\n{ctx}")
                return jsonify({"status": "ok"}), 200

            if text.lower() == "/clear":
                chat_agent.clear_history(int(phone[-10:]))
                send_text(phone, "Historial limpiado. Empezamos de cero!")
                return jsonify({"status": "ok"}), 200

            chat_id = int(phone[-10:])
            memory.track_user_interaction(chat_id, user_name, "MESSAGE")

            result = run_async(orchestrator.process(text, chat_id, user_name))
            send_result(phone, result)

            try:
                intent = run_async(orchestrator.classify_intent(text))
                memory.record_episode(
                    chat_id=chat_id,
                    user_name=user_name,
                    intent=intent,
                    user_message=text,
                    result_type=result.get("type", "text"),
                    success=True,
                )
            except Exception:
                pass

        elif msg_type == "image":
            # Descargar la imagen enviada por el usuario
            image_id = msg.get("image", {}).get("id")
            caption = msg.get("image", {}).get("caption", "")

            if image_id:
                chat_id = int(phone[-10:])
                memory.track_user_interaction(chat_id, user_name, "IMAGE_RECEIVED")

                # Descargar la imagen de WhatsApp
                image_bytes = _download_wa_media(image_id)

                if image_bytes:
                    # Procesar con el agente de imágenes
                    user_instruction = caption if caption else "Analiza esta imagen y dime qué ves. Si quiero que hagas algo con ella, te lo diré."
                    result = run_async(
                        _process_image_with_context(image_bytes, user_instruction, chat_id, user_name)
                    )
                    send_result(phone, result)
                else:
                    send_text(phone, "No pude descargar tu imagen. ¿Me la envías de nuevo?")
            else:
                send_text(phone, "No pude recibir la imagen correctamente. Inténtalo otra vez.")
        else:
            send_text(phone, "Por ahora solo proceso mensajes de texto e imagenes. Escribeme lo que necesites!")

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}", exc_info=True)

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "bot": "LeoVelaBot WhatsApp",
        "agents": ["chat", "image", "video", "video_pipeline", "code", "design"],
        "memory": {
            "episodes": len(memory.episodes),
            "skills": len(memory.skills),
            "users": len(memory.profiles),
        },
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Leo Vela WhatsApp Bot arrancando...")
    logger.info(f"Agentes: chat, image, video, video_pipeline, code, design")
    logger.info(f"Memoria: {len(memory.episodes)} episodios, {len(memory.skills)} habilidades")
    logger.info(f"Webhook escuchando en puerto {WEBHOOK_PORT}")

    # Arrancar el bot de Telegram en segundo plano si el token está configurado
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if telegram_token:
        logger.info("Iniciando Bot de Telegram en segundo plano...")
        try:
            import bot as tg_bot
            # Compartir las mismas instancias de memoria y orquestador
            tg_bot.memory = memory
            tg_bot.orchestrator = orchestrator
            # Indicar que NO arranque su propio health server (ya lo sirve Flask)
            tg_bot._DUAL_MODE = True
            # Lanzar el polling en un hilo
            threading.Thread(
                target=tg_bot.bot.infinity_polling,
                kwargs={"timeout": 30, "long_polling_timeout": 25},
                daemon=True,
            ).start()
            logger.info("Bot de Telegram iniciado con éxito en segundo plano.")
        except Exception as tg_err:
            logger.error(f"Error al iniciar el Bot de Telegram en segundo plano: {tg_err}", exc_info=True)

    app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=False)
