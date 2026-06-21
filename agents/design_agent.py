# -*- coding: utf-8 -*-
"""
Agente de Diseño — Crea diseños, logos, mockups, banners.
Usa Gemini con la paleta de colores C8L Agency.
"""

import base64
import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL

logger = logging.getLogger("leovelabot.design")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

# Paleta C8L para inyectar en los prompts
C8L_STYLE = (
    "cyberpunk cel-shaded gamer aesthetic, neon cyan (#00F3FF) accents, "
    "gold chrome (#D4AF37) highlights, neon pink-red (#FF0055), "
    "absolute black (#000000) background, thick black outlines, "
    "offset neon drop shadows, Space Grotesk typography style"
)


class DesignAgent:
    """Genera diseños con la estética C8L Agency."""

    def __init__(self):
        logger.info("🎯 Design Agent inicializado")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera un diseño basado en la petición del usuario."""
        try:
            # Detectar tipo de diseño
            design_type = self._detect_design_type(message)

            prompt = (
                f"Create a professional {design_type} design based on: {message}. "
                f"Visual style: {C8L_STYLE}. "
                f"The design must look premium, modern, and production-ready. "
                f"No placeholder text — use real, relevant content. "
                f"High resolution, clean composition, visually striking."
            )

            response = _get_client().models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    temperature=1.0,
                ),
            )

            image_data = None
            text_caption = ""

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        data = part.inline_data.data
                        image_data = base64.b64decode(data) if isinstance(data, str) else data
                    elif hasattr(part, "text") and part.text:
                        text_caption = part.text

            if image_data:
                caption = (
                    f"🎯 *Diseño generado: {design_type}*\n\n"
                    f"📝 _{message[:80]}_\n"
                    f"🎨 Estilo: C8L Cyberpunk"
                )
                if text_caption:
                    caption += f"\n\n💡 {text_caption[:200]}"

                return {
                    "type": "image",
                    "content": image_data,
                    "caption": caption,
                }
            else:
                return {
                    "type": "text",
                    "content": f"🎯 {text_caption or 'No pude generar el diseño. Intenta con más detalles.'}",
                }

        except Exception as e:
            logger.error(f"Error en Design Agent: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"❌ Error generando el diseño: {str(e)}",
            }

    def _detect_design_type(self, message: str) -> str:
        """Detecta el tipo de diseño solicitado."""
        msg = message.lower()
        if any(w in msg for w in ["logo", "logotipo", "marca"]):
            return "logo"
        elif any(w in msg for w in ["banner", "portada", "cover", "cabecera"]):
            return "banner"
        elif any(w in msg for w in ["ui", "interfaz", "dashboard", "app", "web", "pantalla"]):
            return "UI/UX interface"
        elif any(w in msg for w in ["thumbnail", "miniatura", "youtube"]):
            return "YouTube thumbnail"
        elif any(w in msg for w in ["poster", "cartel", "flyer"]):
            return "poster"
        elif any(w in msg for w in ["icono", "icon", "avatar"]):
            return "icon"
        else:
            return "graphic design"
