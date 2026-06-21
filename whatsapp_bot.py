# -*- coding: utf-8 -*-
"""
@leovelabot — Servidor unificado Flask para C8L Agency.
Arranca el bot de Telegram en modo WEBHOOK (no polling).
Webhook = solo ESTE servicio recibe mensajes, mata al bot fantasma.
"""

import io
import os
import sys
import json
import logging
import asyncio
import threading
import requests
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    TELEGRAM_BOT_TOKEN,
    GEMINI_API_KEY,
    ADMIN_CHAT_ID,
    BOT_NAME,
    SYSTEM_PROMPT,
    MAX_HISTORY_PER_USER,
)

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
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Puerto (Render inyecta PORT)
# ---------------------------------------------------------------------------
PORT = int(os.environ.get("PORT", "8080"))

# ---------------------------------------------------------------------------
# Async loop (thread-safe)
# ---------------------------------------------------------------------------
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True, name="async-loop").start()


def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=120)


# ---------------------------------------------------------------------------
# Gemini client (simple, directo)
# ---------------------------------------------------------------------------
from google import genai
from google.genai import types

_gemini_client = None


def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


# ---------------------------------------------------------------------------
# Historial de chat por usuario
# ---------------------------------------------------------------------------
_chat_history = {}


def get_history(chat_id):
    if chat_id not in _chat_history:
        _chat_history[chat_id] = []
    return _chat_history[chat_id]


def add_to_history(chat_id, role, text):
    history = get_history(chat_id)
    history.append({"role": role, "text": text})
    if len(history) > MAX_HISTORY_PER_USER * 2:
        _chat_history[chat_id] = history[-MAX_HISTORY_PER_USER:]


# ---------------------------------------------------------------------------
# Telegram API helpers
# ---------------------------------------------------------------------------
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def tg_send(chat_id, text, parse_mode=None):
    """Envía texto a Telegram. Si Markdown falla, envía plano."""
    payload = {"chat_id": chat_id, "text": text[:4096]}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)

    # Si Markdown falla, reintentar sin formato
    if not r.ok and parse_mode:
        payload.pop("parse_mode")
        r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)

    return r.ok


def tg_send_photo(chat_id, photo_bytes, caption=""):
    """Envía imagen a Telegram."""
    files = {"photo": ("image.png", io.BytesIO(photo_bytes), "image/png")}
    data = {"chat_id": chat_id, "caption": caption[:1024]}
    r = requests.post(f"{TG_API}/sendPhoto", data=data, files=files, timeout=30)
    return r.ok


def tg_send_document(chat_id, doc_bytes, filename, caption=""):
    """Envía documento a Telegram."""
    files = {"document": (filename, io.BytesIO(doc_bytes), "application/octet-stream")}
    data = {"chat_id": chat_id, "caption": caption[:1024]}
    r = requests.post(f"{TG_API}/sendDocument", data=data, files=files, timeout=30)
    return r.ok


def tg_send_action(chat_id, action="typing"):
    requests.post(f"{TG_API}/sendChatAction", json={"chat_id": chat_id, "action": action}, timeout=5)


# ---------------------------------------------------------------------------
# Procesar mensaje con Gemini
# ---------------------------------------------------------------------------
async def process_message(text, chat_id, user_name):
    """Procesa un mensaje con Gemini 3.5 Flash."""
    history = get_history(chat_id)
    history_text = "\n".join(
        f"{'Usuario' if m['role'] == 'user' else 'Leo'}: {m['text']}"
        for m in history[-MAX_HISTORY_PER_USER:]
    )

    prompt = f"""{SYSTEM_PROMPT}

El usuario se llama {user_name}.

{f"Historial:" if history_text else ""}
{history_text}

Usuario: {text}

Leo:"""

    try:
        response = get_gemini().models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.85,
                max_output_tokens=2048,
            ),
        )
        reply = response.text.strip()

        # Guardar en historial
        add_to_history(chat_id, "user", text)
        add_to_history(chat_id, "assistant", reply)

        return reply

    except Exception as e:
        logger.error(f"Gemini error: {e}")

        # Intentar con segunda key
        key2 = os.environ.get("GEMINI_API_KEY_2", "")
        if key2:
            try:
                client2 = genai.Client(api_key=key2)
                response = client2.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        max_output_tokens=2048,
                    ),
                )
                reply = response.text.strip()
                add_to_history(chat_id, "user", text)
                add_to_history(chat_id, "assistant", reply)
                return reply
            except Exception as e2:
                logger.error(f"Gemini key2 error: {e2}")

        return None


# ---------------------------------------------------------------------------
# Generar imagen con HuggingFace
# ---------------------------------------------------------------------------
async def generate_image(prompt):
    """Genera imagen con HuggingFace SDXL (gratis)."""
    hf_token = os.environ.get("HUGGINGFACE_TOKEN", "")
    if not hf_token:
        return None

    try:
        headers = {"Authorization": f"Bearer {hf_token}"}
        payload = {"inputs": f"{prompt}, high quality, detailed, vibrant colors, 4k"}

        r = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers=headers,
            json=payload,
            timeout=60,
        )

        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return r.content
    except Exception as e:
        logger.error(f"HuggingFace error: {e}")

    return None


# ---------------------------------------------------------------------------
# Webhook de Telegram
# ---------------------------------------------------------------------------
@app.route(f"/webhook/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Recibe mensajes de Telegram via webhook."""
    data = request.get_json()
    if not data:
        return jsonify({"ok": True}), 200

    try:
        # Extraer mensaje
        message = data.get("message") or data.get("callback_query", {}).get("message")
        if not message:
            return jsonify({"ok": True}), 200

        chat_id = message["chat"]["id"]
        user_name = message.get("from", {}).get("first_name", "Usuario")

        # Callback query (botones)
        if "callback_query" in data:
            callback = data["callback_query"]
            action = callback.get("data", "")
            prompts = {
                "quick_image": "¿Qué imagen quieres? Descríbela:",
                "quick_video": "¿Qué vídeo quieres? Describe escena y duración:",
                "quick_code": "¿Qué quieres que programe? (juego, app, script...):",
                "quick_design": "¿Qué quieres que diseñe? (logo, banner, UI...):",
            }
            tg_send(chat_id, f"✨ {prompts.get(action, '¿Qué necesitas?')}")
            return jsonify({"ok": True}), 200

        # Texto
        text = message.get("text", "")
        if not text:
            return jsonify({"ok": True}), 200

        # Comandos
        if text.startswith("/start"):
            welcome = (
                f"🦁 *¡Bienvenido a C8L Agency, {user_name}!*\n\n"
                f"Soy *Leo*, tu asistente IA. Puedo:\n\n"
                f"🎨 Crear imágenes — \"dibuja un león\"\n"
                f"💻 Programar — \"crea un juego Snake\"\n"
                f"💬 Conversar — pregúntame lo que quieras\n\n"
                f"Solo escríbeme. 🚀"
            )
            tg_send(chat_id, welcome, parse_mode="Markdown")
            return jsonify({"ok": True}), 200

        if text.startswith("/help"):
            tg_send(chat_id, (
                "🦁 *Comandos:*\n/start — Bienvenida\n/help — Ayuda\n/clear — Limpiar historial\n\n"
                "O simplemente escríbeme lo que necesites."
            ), parse_mode="Markdown")
            return jsonify({"ok": True}), 200

        if text.startswith("/clear"):
            _chat_history.pop(chat_id, None)
            tg_send(chat_id, "🧹 Historial limpiado.")
            return jsonify({"ok": True}), 200

        # Detectar si pide imagen
        image_keywords = ["dibuja", "genera imagen", "genera una imagen", "crea imagen", "diseña", "logo", "banner"]
        wants_image = any(kw in text.lower() for kw in image_keywords)

        tg_send_action(chat_id, "typing")

        if wants_image:
            # Intentar generar imagen real con HF
            image_data = run_async(generate_image(text))
            if image_data:
                tg_send_photo(chat_id, image_data, caption=f"🎨 _{text[:100]}_")
                return jsonify({"ok": True}), 200
            # Fallback: descripción textual con Gemini
            reply = run_async(process_message(
                f"Describe visualmente con todo detalle cómo se vería esta imagen: {text}. "
                f"Sé creativo y cinematográfico.",
                chat_id, user_name
            ))
        else:
            # Chat normal
            reply = run_async(process_message(text, chat_id, user_name))

        if reply:
            tg_send(chat_id, reply)
        else:
            tg_send(chat_id, "❌ Todos mis cerebros están descansando. Inténtalo en 30 segundos.")

    except Exception as e:
        logger.error(f"Error en webhook: {e}", exc_info=True)

    return jsonify({"ok": True}), 200


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "bot": BOT_NAME}), 200


# ---------------------------------------------------------------------------
# Configurar webhook al arrancar
# ---------------------------------------------------------------------------
def setup_webhook():
    """Configura el webhook de Telegram apuntando a este servicio."""
    # Obtener URL del servicio en Render
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")

    if not render_url:
        # Intentar construirla desde el nombre del servicio
        service_name = os.environ.get("RENDER_SERVICE_NAME", "leovelabot-dual")
        render_url = f"https://{service_name}.onrender.com"

    webhook_url = f"{render_url}/webhook/{TELEGRAM_BOT_TOKEN}"

    # Eliminar webhook antiguo
    requests.post(f"{TG_API}/deleteWebhook", timeout=10)

    # Configurar nuevo webhook
    r = requests.post(
        f"{TG_API}/setWebhook",
        json={"url": webhook_url, "drop_pending_updates": True},
        timeout=10,
    )

    if r.ok:
        result = r.json()
        if result.get("ok"):
            logger.info(f"✅ Webhook configurado: {webhook_url}")
            # Notificar admin
            if ADMIN_CHAT_ID:
                tg_send(
                    int(ADMIN_CHAT_ID),
                    f"🦁✅ Bot ACTIVO (webhook)\n🔗 {webhook_url}",
                )
            return True

    logger.error(f"❌ Error configurando webhook: {r.text}")
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
        logger.error("❌ Faltan TELEGRAM_BOT_TOKEN o GEMINI_API_KEY")
        sys.exit(1)

    # Configurar webhook (mata al bot fantasma automáticamente)
    logger.info("🔧 Configurando webhook de Telegram...")
    setup_webhook()

    # Arrancar Flask
    logger.info(f"🚀 @{BOT_NAME} arrancado — Modo WEBHOOK — Puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
