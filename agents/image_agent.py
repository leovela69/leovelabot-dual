# -*- coding: utf-8 -*-
"""
Agente de Imágenes — Usa Hugging Face (gratis) para generar imágenes reales.
Fallback: si HF no está configurado, da descripción textual con Gemini/Groq.
"""

import os
import logging
import requests
from agents.provider_manager import get_provider_manager

logger = logging.getLogger("leovelabot.image")

HF_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


class ImageAgent:
    """Genera imágenes con Hugging Face (gratis) o descripción textual como fallback."""

    def __init__(self):
        if HF_TOKEN:
            logger.info("🎨 Image Agent inicializado (Hugging Face SDXL)")
        else:
            logger.warning("🎨 Image Agent: sin HUGGINGFACE_TOKEN — modo texto descriptivo")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        # Intentar con Hugging Face primero (imagen real)
        if HF_TOKEN:
            try:
                return await self._generate_with_hf(message)
            except Exception as e:
                logger.warning(f"HF falló: {e} — usando texto descriptivo")

        # Fallback: descripción textual con el provider manager
        try:
            return await self._generate_text_description(message)
        except Exception as e:
            logger.error(f"Error en Image Agent: {e}")
            return {
                "type": "text",
                "content": "❌ No pude generar la imagen. Intenta de nuevo.",
            }

    async def _generate_with_hf(self, message: str) -> dict:
        """Genera imagen real con Hugging Face Inference API."""
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        # Mejorar el prompt para SDXL
        enhanced_prompt = (
            f"{message}, high quality, detailed, vibrant colors, "
            f"professional, 4k, cyberpunk neon aesthetic"
        )

        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": enhanced_prompt},
            timeout=60,
        )

        if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
            return {
                "type": "image",
                "content": response.content,
                "caption": f"🎨 _{message[:100]}_\n🤖 Generado con Stable Diffusion XL",
            }
        else:
            raise Exception(f"HF status {response.status_code}: {response.text[:200]}")

    async def _generate_text_description(self, message: str) -> dict:
        """Genera una descripción visual detallada (sin imagen real)."""
        manager = get_provider_manager()
        description = await manager.generate_text(
            prompt=(
                f"El usuario quiere una imagen de: '{message}'. "
                f"Genera una descripción VISUAL ultra-detallada de cómo se vería esta imagen. "
                f"Describe colores, composición, iluminación, estilo artístico, detalles. "
                f"Hazlo como si fueras un director de arte describiendo a un ilustrador."
            ),
            system_prompt="Eres un director de arte experto. Describes imágenes con detalle cinematográfico.",
            temperature=0.9,
            max_output_tokens=1024,
        )

        return {
            "type": "text",
            "content": (
                f"🎨 *Concepto visual para:* _{message[:80]}_\n\n"
                f"{description}\n\n"
                f"💡 _Para generar imágenes reales, configura HUGGINGFACE\\_TOKEN en las variables de entorno._"
            ),
        }
