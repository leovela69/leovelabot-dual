# -*- coding: utf-8 -*-
"""
@LeoVelaBot — Bot Multi-Agente de WhatsApp (Sistema Hermes).
Usa la WhatsApp Cloud API (Meta) con los mismos agentes que Telegram.
Servidor webhook Flask que recibe mensajes y responde via los agentes IA.

Punto de entrada principal en Render: arranca Flask (WhatsApp) + Telegram polling.
"""

import io
import os
import re
import sys
import json
import logging
import asyncio
import hmac
import base64
import requests
import threading
from flask import Flask, request, jsonify, Response

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
# Instancias globales (compartidas entre Telegram y WhatsApp)
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

# ---------------------------------------------------------------------------
# Event loop para async — hilo dedicado para evitar deadlocks con Flask
# ---------------------------------------------------------------------------
_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_loop_thread.start()


def run_async(coro):
    """Ejecuta una corutina async desde código sync de Flask sin bloquear."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=180)  # 3 min timeout para vídeos largos


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
    """Envia un mensaje de texto por WhatsApp (auto-split si > 4096 chars)."""
    if not text:
        text = "..."
    # Limpiar markdown que WhatsApp no soporta bien
    text = text.replace("**", "*").replace("__", "_")

    chunks = [text[i:i + 4096] for i in range(0, len(text), 4096)]
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
        if r.status_code != 200:
            logger.error(f"Error enviando texto: {result}")
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
        "image": {"id": media_id, "caption": caption[:1024] if caption else ""},
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
        "document": {"id": media_id, "caption": caption[:1024] if caption else "", "filename": filename},
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
        "video": {"id": media_id, "caption": caption[:1024] if caption else ""},
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
    try:
        requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
    except Exception:
        pass  # No crítico


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
    """Procesa una imagen recibida con Gemini Vision."""
    from google import genai
    from google.genai import types
    from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL, SYSTEM_PROMPT

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
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
                "caption": result_text[:1024] if result_text else f"Aquí tienes, {user_name}",
            }
        else:
            return {
                "type": "text",
                "content": result_text or "He visto tu imagen pero no he podido generar nada visual. Dime qué quieres que haga con ella.",
            }

    except Exception as e:
        logger.error(f"Error procesando imagen: {e}", exc_info=True)
        return {
            "type": "text",
            "content": f"No he podido procesar la imagen: {str(e)}. ¿Me dices qué querías?",
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
# Comandos de WhatsApp (empiezan con /)
# ---------------------------------------------------------------------------
def _handle_command(phone: str, text: str, user_name: str, chat_id: int) -> bool:
    """Procesa comandos específicos. Devuelve True si era un comando."""
    cmd = text.lower().strip()

    if cmd in ["/start", "hola", "hi", "menu"]:
        welcome = (
            f"Qué pasa {user_name}! Soy Leo, el bot de C8L Agency.\n\n"
            "Escríbeme lo que necesites y me pongo a currar:\n\n"
            "🎨 Crear imágenes — \"Dibuja un león cyberpunk\"\n"
            "🎬 Generar vídeos — \"Haz un vídeo corto del espacio\"\n"
            "💻 Programar — \"Crea un juego Snake en HTML\"\n"
            "🎯 Diseñar — \"Diseña un logo para mi marca\"\n"
            "🎵 Cover musical — \"/cover portada trap oscura\"\n"
            "💬 Conversar — Pregúntame lo que quieras\n\n"
            "Solo escribe. Sin comandos raros ni historias. 🔥"
        )
        send_text(phone, welcome)
        return True

    if cmd == "/stats":
        stats = memory.get_stats_summary()
        ctx = memory.get_user_context(chat_id)
        send_text(phone, f"{stats}\n{ctx}")
        return True

    if cmd == "/clear":
        chat_agent.clear_history(chat_id)
        send_text(phone, "Historial limpiado. Empezamos de cero, tío!")
        return True

    if cmd == "/help":
        help_msg = (
            "🦁 *Comandos disponibles:*\n\n"
            "/stats — Mis estadísticas\n"
            "/clear — Limpiar historial\n"
            "/cover [descripción] — Crear portada musical\n"
            "/video [descripción] — Crear vídeo\n"
            "/estado — Estado del sistema\n"
            "/ranking — Top usuarios\n\n"
            "O simplemente escribe lo que necesites. Sin comandos."
        )
        send_text(phone, help_msg)
        return True

    if cmd == "/estado":
        send_text(phone, (
            "🌐 Estado de Hermes:\n\n"
            "🤖 Bot: ✅ Online\n"
            "📱 WhatsApp: ✅ Activo\n"
            "💬 Telegram: ✅ Activo\n"
            "🧠 Agentes: Todos operativos\n"
            "💾 Memoria: SQLite persistente\n\n"
            "⚡ Todo funcionando."
        ))
        return True

    if cmd == "/ranking":
        profiles = memory.profiles
        if not profiles:
            send_text(phone, "Aún no hay ranking. ¡Sé el primero!")
            return True

        sorted_users = sorted(
            profiles.items(),
            key=lambda x: x[1].get("total_messages", 0) if isinstance(x[1], dict) else 0,
            reverse=True,
        )[:10]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []
        for i, (uid, profile) in enumerate(sorted_users):
            if isinstance(profile, dict):
                name = profile.get("user_name", "Anónimo")
                msgs = profile.get("total_messages", 0)
                if msgs > 0:
                    lines.append(f"{medals[i]} {name} — {msgs} msgs")

        if lines:
            send_text(phone, f"🏆 *Top Usuarios C8L*\n\n" + "\n".join(lines))
        else:
            send_text(phone, "Aún no hay suficientes datos para el ranking.")
        return True

    # /cover [prompt]
    if cmd.startswith("/cover"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_text(phone, "Dime qué quieres en la portada. Ejemplo:\n/cover portada trap oscura con calavera neon")
            return True

        prompt = parts[1]
        cover_prompt = (
            f"Diseña una portada/cover de música profesional: {prompt}. "
            f"Cuadrada (1:1), tipografía impactante, calidad Spotify/Apple Music."
        )
        result = run_async(design_agent.process(cover_prompt, chat_id, user_name))
        send_result(phone, result)
        memory.record_episode(chat_id=chat_id, user_name=user_name, intent="COVER",
                              user_message=prompt, result_type=result.get("type"), success=True)
        return True

    # /video [prompt]
    if cmd.startswith("/video"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_text(phone, "Dime qué vídeo quieres. Ejemplo:\n/video clip cyberpunk con coches y neones")
            return True

        prompt = parts[1]
        send_text(phone, "🎬 Generando tu vídeo... tarda un poco, espera.")
        duration_match = re.search(r"(\d+)\s*min", prompt)
        if duration_match and int(duration_match.group(1)) > 1:
            result = run_async(video_pipeline.process(prompt, chat_id, user_name))
        else:
            result = run_async(video_agent.process(prompt, chat_id, user_name))
        send_result(phone, result)
        memory.record_episode(chat_id=chat_id, user_name=user_name, intent="VIDEO_CREATE",
                              user_message=prompt, result_type=result.get("type"), success=True)
        return True

    return False  # No era un comando


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verificación del webhook por Meta (challenge)."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token and hmac.compare_digest(token, VERIFY_TOKEN):
        logger.info("✅ Webhook verificado correctamente")
        return Response(challenge, mimetype="text/plain"), 200
    else:
        logger.warning(f"❌ Verificación fallida: mode={mode}")
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

        logger.info(f"📩 Mensaje de {user_name} ({phone}): tipo={msg_type}")
        mark_as_read(msg_id)

        # Calcular chat_id consistente desde el número de teléfono
        chat_id = int(phone[-10:]) if len(phone) >= 10 else hash(phone) % 10**9

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
            logger.info(f"   Texto: {text[:80]}...")

            # Intentar procesar como comando
            if _handle_command(phone, text, user_name, chat_id):
                return jsonify({"status": "ok"}), 200

            # Procesar con el orquestador (mensaje normal)
            memory.track_user_interaction(chat_id, user_name, "MESSAGE")

            result = run_async(orchestrator.process(text, chat_id, user_name))
            send_result(phone, result)

            # Registrar episodio (no bloquear la respuesta)
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

            # Aprender de la tarea (background)
            try:
                intent = run_async(orchestrator.classify_intent(text))
                run_async(memory.learn_from_task(
                    user_message=text,
                    intent=intent,
                    result=str(result.get("content", ""))[:300],
                    success=True,
                ))
            except Exception:
                pass

        elif msg_type == "image":
            # Descargar y procesar imagen
            image_id = msg.get("image", {}).get("id")
            caption = msg.get("image", {}).get("caption", "")

            if image_id:
                memory.track_user_interaction(chat_id, user_name, "IMAGE_RECEIVED")
                image_bytes = _download_wa_media(image_id)

                if image_bytes:
                    user_instruction = caption if caption else "Analiza esta imagen y dime qué ves."
                    result = run_async(
                        _process_image_with_context(image_bytes, user_instruction, chat_id, user_name)
                    )
                    send_result(phone, result)
                else:
                    send_text(phone, "No pude descargar tu imagen. ¿Me la envías de nuevo?")
            else:
                send_text(phone, "No pude recibir la imagen. Inténtalo otra vez.")

        elif msg_type in ["audio", "voice"]:
            send_text(phone, (
                "He recibido tu audio, pero por ahora solo proceso texto e imágenes. "
                "Escríbeme lo que necesites y me pongo con ello."
            ))

        elif msg_type == "document":
            send_text(phone, (
                "He recibido tu documento. Por ahora no puedo procesar archivos directamente, "
                "pero puedo crear código, diseños, y mucho más. Dime qué necesitas."
            ))

        else:
            send_text(phone, "Escríbeme en texto o envíame una imagen. Me pongo a currar con ello.")

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}", exc_info=True)
        # Intentar notificar al usuario del error
        try:
            if phone:
                send_text(phone, "Uf, me ha dado un error. Dale otra vez en unos segundos.")
        except Exception:
            pass

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint para Render."""
    return jsonify({
        "status": "healthy",
        "bot": "LeoVelaBot Hermes",
        "version": "2.0",
        "agents": ["chat", "image", "video", "video_pipeline", "code", "design"],
        "memory": {
            "episodes": memory.episode_count,
            "skills": memory.skill_count,
            "users": memory.profile_count,
        },
    })


@app.route("/", methods=["GET"])
def root():
    """Root endpoint — info básica."""
    return jsonify({
        "name": "LeoVelaBot Hermes",
        "status": "running",
        "endpoints": ["/webhook", "/health"],
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("🦁 Leo Vela Bot (Hermes) arrancando...")
    logger.info(f"   🧠 Agentes: chat, image, video, video_pipeline, code, design")
    logger.info(f"   💾 Memoria: {memory.episode_count} episodios, {memory.skill_count} habilidades")
    logger.info(f"   🌐 Webhook en puerto {WEBHOOK_PORT}")

    # Arrancar el bot de Telegram en segundo plano si el token está configurado
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if telegram_token:
        logger.info("   📱 Iniciando Telegram en segundo plano...")
        try:
            import bot as tg_bot
            # Compartir las mismas instancias
            tg_bot.memory = memory
            tg_bot.orchestrator = orchestrator
            tg_bot._DUAL_MODE = True
            # Lanzar polling en un hilo daemon
            threading.Thread(
                target=tg_bot.bot.infinity_polling,
                kwargs={"timeout": 30, "long_polling_timeout": 25},
                daemon=True,
            ).start()
            logger.info("   ✅ Telegram activo en segundo plano")
        except Exception as tg_err:
            logger.error(f"   ❌ Error iniciando Telegram: {tg_err}", exc_info=True)
    else:
        logger.warning("   ⚠️ TELEGRAM_BOT_TOKEN no configurado — solo WhatsApp activo")

    logger.info("🚀 Bot listo. Esperando mensajes...")
    app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=False)
