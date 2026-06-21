# -*- coding: utf-8 -*-
"""
Agente de Imágenes — Generación de imágenes con Gemini.
Usa el tier gratuito de Gemini para generar imágenes desde texto.
"""

import io
import base64
import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL

from agents.model_manager import smart_generate

logger = logging.getLogger("leovelabot.image")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class ImageAgent:
    """Genera imágenes usando Gemini con modalidad IMAGE."""

    def __init__(self):
        logger.info("🎨 Image Agent inicializado")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera una imagen a partir de la descripción del usuario."""
        try:
            # Mejorar el prompt para mejores resultados
            enhanced_prompt = (
                f"Generate a high-quality, detailed image based on this description: {message}. "
                f"Style: vibrant colors, professional quality, cinematic lighting."
            )

            response = await smart_generate(_get_client(), GEMINI_IMAGE_MODEL,
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    temperature=1.0,
                ),
            )

            # Buscar la parte de imagen en la respuesta
            image_data = None
            text_caption = ""

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                    elif hasattr(part, "text") and part.text:
                        text_caption = part.text

            if image_data:
                # Convertir bytes de imagen para envío
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data

                caption = text_caption if text_caption else f"🎨 Imagen generada: _{message[:100]}_"

                return {
                    "type": "image",
                    "content": image_bytes,
                    "caption": caption,
                }
            else:
                # Gemini respondió solo con texto (sin imagen)
                fallback = text_caption or "No pude generar la imagen. Intenta con otra descripción más detallada."
                return {"type": "text", "content": f"🎨 {fallback}"}

        except Exception as e:
            logger.error(f"Error en Image Agent: {e}", exc_info=True)
            return {
                "type": "text",
                "content": (
                    f"❌ Error generando la imagen: {str(e)}\n\n"
                    "💡 Intenta con una descripción más simple o diferente."
                ),
            }
