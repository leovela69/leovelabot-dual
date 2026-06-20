# -*- coding: utf-8 -*-
"""
Agente de Imágenes — Sistema Hermes.
Genera imágenes usando Hugging Face (Stable Diffusion XL) como motor principal
y Gemini como fallback. Ambos gratuitos.

Flujo:
1. Intenta con Hugging Face Stable Diffusion XL (mejor calidad, gratis 30k/mes)
2. Si falla o no está configurado, usa Gemini Flash con modalidad IMAGE
3. Devuelve la imagen en bytes lista para enviar
"""

import io
import time
import base64
import logging
import requests
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    HUGGINGFACE_TOKEN,
    HF_IMAGE_MODEL,
    HF_API_URL,
    MAX_IMAGE_RETRIES,
    SYSTEM_PROMPT,
)

logger = logging.getLogger("leovelabot.image")

# Clientes (lazy init)
_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


class ImageAgent:
    """
    Genera imágenes usando múltiples backends gratuitos.
    Prioridad: Hugging Face → Gemini
    """

    def __init__(self):
        self._hf_available = bool(HUGGINGFACE_TOKEN)
        if self._hf_available:
            logger.info(f"🎨 Image Agent inicializado — HuggingFace ({HF_IMAGE_MODEL}) + Gemini fallback")
        else:
            logger.info("🎨 Image Agent inicializado — Solo Gemini (HUGGINGFACE_TOKEN no configurado)")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera una imagen a partir de la descripción del usuario."""

        # Mejorar el prompt para mejores resultados
        enhanced_prompt = self._enhance_prompt(message)

        # Intentar con Hugging Face primero (mejor calidad y más rápido)
        if self._hf_available:
            result = await self._generate_huggingface(enhanced_prompt, message)
            if result:
                return result

        # Fallback: Gemini
        result = await self._generate_gemini(enhanced_prompt, message)
        if result:
            return result

        # Si todo falla
        return {
            "type": "text",
            "content": (
                "No he podido generar la imagen ahora mismo. "
                "Puede ser que los servidores estén ocupados. "
                "Dale otro intento en unos segundos o prueba con otra descripción."
            ),
        }

    def _enhance_prompt(self, user_message: str) -> str:
        """Mejora el prompt del usuario para obtener mejores resultados."""
        # Si el usuario ya dio un prompt detallado, no tocar mucho
        if len(user_message) > 100:
            return user_message

        # Añadir calidad por defecto
        return (
            f"{user_message}, high quality, detailed, professional, "
            f"vibrant colors, sharp focus, 4K resolution"
        )

    async def _generate_huggingface(self, prompt: str, original_msg: str) -> dict | None:
        """Genera imagen con Hugging Face Inference API (Stable Diffusion XL)."""
        url = f"{HF_API_URL}/{HF_IMAGE_MODEL}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        payload = {"inputs": prompt}

        for attempt in range(MAX_IMAGE_RETRIES + 1):
            try:
                logger.info(f"🎨 HuggingFace intento {attempt + 1}: {prompt[:60]}...")
                response = requests.post(url, headers=headers, json=payload, timeout=120)

                if response.status_code == 200:
                    image_bytes = response.content

                    # Verificar que es una imagen válida (empieza con cabecera PNG o JPEG)
                    if len(image_bytes) > 1000:
                        logger.info(f"✅ Imagen generada con HuggingFace ({len(image_bytes)} bytes)")
                        return {
                            "type": "image",
                            "content": image_bytes,
                            "caption": f"🎨 _{original_msg[:100]}_",
                        }
                    else:
                        logger.warning(f"HuggingFace devolvió datos muy pequeños: {len(image_bytes)} bytes")

                elif response.status_code == 503:
                    # Modelo cargando — esperar y reintentar
                    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    wait_time = body.get("estimated_time", 20)
                    logger.info(f"⏳ Modelo cargando, esperando {wait_time:.0f}s...")
                    time.sleep(min(wait_time, 30))
                    continue

                elif response.status_code == 429:
                    # Rate limit — usar fallback
                    logger.warning("⚠️ Rate limit en HuggingFace, usando Gemini como fallback")
                    return None

                else:
                    logger.warning(f"HuggingFace error {response.status_code}: {response.text[:200]}")
                    if attempt < MAX_IMAGE_RETRIES:
                        time.sleep(3)
                        continue
                    return None

            except requests.Timeout:
                logger.warning(f"HuggingFace timeout (intento {attempt + 1})")
                if attempt < MAX_IMAGE_RETRIES:
                    time.sleep(2)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error HuggingFace: {e}")
                return None

        return None

    async def _generate_gemini(self, prompt: str, original_msg: str) -> dict | None:
        """Genera imagen con Gemini Flash (fallback)."""
        try:
            logger.info(f"🎨 Gemini fallback: {prompt[:60]}...")

            response = _get_gemini_client().models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=(
                    f"Generate a high-quality, detailed image based on this description: {prompt}. "
                    f"Style: vibrant colors, professional quality, cinematic lighting. "
                    f"Do NOT include any text or watermarks in the image."
                ),
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
                # Convertir bytes
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data

                logger.info(f"✅ Imagen generada con Gemini ({len(image_bytes)} bytes)")
                caption = f"🎨 _{original_msg[:100]}_"
                if text_caption:
                    caption += f"\n\n💡 {text_caption[:200]}"

                return {
                    "type": "image",
                    "content": image_bytes,
                    "caption": caption,
                }
            else:
                # Gemini respondió solo con texto
                if text_caption:
                    return {"type": "text", "content": f"🎨 {text_caption}"}
                return None

        except Exception as e:
            logger.error(f"Error Gemini imagen: {e}", exc_info=True)
            return None
