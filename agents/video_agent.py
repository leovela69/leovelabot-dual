# -*- coding: utf-8 -*-
"""
Agente de Vídeo — Sistema Hermes.
Genera vídeos cortos usando múltiples backends gratuitos:

Flujo para vídeos cortos (< 1 min):
1. Intenta con Hugging Face text-to-video (damo-vilab) — genera vídeo directo
2. Si falla, genera imágenes con HF/Gemini + las compone con FFmpeg (Ken Burns)
3. Devuelve el vídeo en bytes listo para enviar

Para vídeos largos (> 1 min), se delega al VideoPipeline.
"""

import os
import time
import uuid
import base64
import logging
import subprocess
import asyncio
import requests
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    GEMINI_CHAT_MODEL,
    HUGGINGFACE_TOKEN,
    HF_VIDEO_MODEL,
    HF_IMAGE_MODEL,
    HF_API_URL,
    FFMPEG_PATH,
    TEMP_DIR,
    SCENE_DURATION_SECONDS,
    MAX_VIDEO_RETRIES,
)

logger = logging.getLogger("leovelabot.video")

_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


class VideoAgent:
    """
    Genera vídeos cortos (~15-30 segundos) usando:
    - Hugging Face text-to-video (directo)
    - O composición de imágenes IA + FFmpeg (fallback fiable)
    """

    def __init__(self):
        os.makedirs(TEMP_DIR, exist_ok=True)
        self._hf_available = bool(HUGGINGFACE_TOKEN)
        if self._hf_available:
            logger.info(f"🎬 Video Agent inicializado — HuggingFace ({HF_VIDEO_MODEL}) + FFmpeg fallback")
        else:
            logger.info("🎬 Video Agent inicializado — Solo Gemini+FFmpeg (HUGGINGFACE_TOKEN no configurado)")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera un vídeo corto (~15-30 segundos)."""
        try:
            # Intentar generación directa con HuggingFace text-to-video
            if self._hf_available:
                result = await self._generate_hf_video(message)
                if result:
                    return result

            # Fallback: generar imágenes + componer con FFmpeg
            return await self._generate_image_composition(message, chat_id, user_name)

        except Exception as e:
            logger.error(f"Error en Video Agent: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"No he podido generar el vídeo: {str(e)}\n\nPrueba con otra descripción.",
            }

    async def _generate_hf_video(self, prompt: str) -> dict | None:
        """Genera vídeo directamente con Hugging Face text-to-video."""
        url = f"{HF_API_URL}/{HF_VIDEO_MODEL}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        payload = {"inputs": prompt}

        for attempt in range(MAX_VIDEO_RETRIES + 1):
            try:
                logger.info(f"🎬 HuggingFace video intento {attempt + 1}: {prompt[:50]}...")
                response = requests.post(url, headers=headers, json=payload, timeout=180)

                if response.status_code == 200:
                    video_bytes = response.content

                    # Verificar que tiene un tamaño razonable para ser un vídeo
                    if len(video_bytes) > 10000:
                        logger.info(f"✅ Vídeo generado con HuggingFace ({len(video_bytes)} bytes)")
                        return {
                            "type": "video",
                            "content": video_bytes,
                            "caption": f"🎬 _{prompt[:80]}_\n🤖 Generado con IA",
                        }
                    else:
                        logger.warning(f"HuggingFace video muy pequeño: {len(video_bytes)} bytes")
                        return None

                elif response.status_code == 503:
                    # Modelo cargando
                    body = response.json() if "json" in response.headers.get("content-type", "") else {}
                    wait_time = body.get("estimated_time", 30)
                    logger.info(f"⏳ Modelo de vídeo cargando, esperando {wait_time:.0f}s...")
                    await asyncio.sleep(min(wait_time, 45))
                    continue

                elif response.status_code == 429:
                    logger.warning("⚠️ Rate limit en HuggingFace video, usando fallback")
                    return None

                else:
                    logger.warning(f"HuggingFace video error {response.status_code}: {response.text[:200]}")
                    return None

            except requests.Timeout:
                logger.warning(f"HuggingFace video timeout (intento {attempt + 1})")
                return None
            except Exception as e:
                logger.error(f"Error HuggingFace video: {e}")
                return None

        return None

    async def _generate_image_composition(self, message: str, chat_id: int, user_name: str) -> dict:
        """
        Fallback fiable: genera varias imágenes + compone vídeo con FFmpeg.
        Siempre funciona mientras tenga al menos Gemini o HuggingFace.
        """
        num_scenes = 4  # 4 escenas × 5s = 20s de vídeo

        # 1. Generar descripciones de escenas
        logger.info(f"📝 Generando {num_scenes} escenas para: {message[:50]}...")
        scene_descriptions = await self._generate_scene_descriptions(message, num_scenes)

        # 2. Generar imagen para cada escena
        image_paths = []
        for i, desc in enumerate(scene_descriptions):
            logger.info(f"🖼️ Escena {i+1}/{len(scene_descriptions)}: {desc[:40]}...")
            img_data = await self._generate_scene_image(desc)

            if img_data:
                img_path = os.path.join(TEMP_DIR, f"scene_{uuid.uuid4().hex}.png")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                image_paths.append(img_path)

            # Pausa para no saturar APIs
            await asyncio.sleep(1)

        if not image_paths:
            return {
                "type": "text",
                "content": "No pude generar las imágenes para el vídeo. Prueba con otra descripción.",
            }

        # 3. Crear vídeo con FFmpeg
        output_path = os.path.join(TEMP_DIR, f"video_{uuid.uuid4().hex}.mp4")
        logger.info(f"🎬 Componiendo vídeo con {len(image_paths)} escenas...")

        success = self._create_video_from_images(image_paths, output_path)

        # 4. Limpiar imágenes temporales
        for p in image_paths:
            try:
                os.remove(p)
            except OSError:
                pass

        if success and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            os.remove(output_path)

            duration = len(image_paths) * SCENE_DURATION_SECONDS
            return {
                "type": "video",
                "content": video_bytes,
                "caption": (
                    f"🎬 _{message[:80]}_\n"
                    f"📐 {len(image_paths)} escenas × {SCENE_DURATION_SECONDS}s = {duration}s"
                ),
            }
        else:
            return {
                "type": "text",
                "content": "Error al componer el vídeo con FFmpeg. Puede que el servidor tenga un problema temporal.",
            }

    async def _generate_scene_descriptions(self, prompt: str, num_scenes: int) -> list[str]:
        """Usa Gemini para generar descripciones visuales de cada escena."""
        try:
            response = _get_gemini_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=(
                    f"Genera exactamente {num_scenes} descripciones de escenas visuales para un vídeo corto sobre: "
                    f"'{prompt}'. Cada descripción debe ser una línea que describa la imagen visual de esa escena. "
                    f"Solo escribe las descripciones, una por línea, sin números ni viñetas. "
                    f"Cada descripción debe ser detallada y cinematográfica (en inglés para mejor generación)."
                ),
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=512,
                ),
            )

            lines = [l.strip() for l in response.text.strip().split("\n") if l.strip()]
            return lines[:num_scenes]

        except Exception as e:
            logger.error(f"Error generando descripciones de escenas: {e}")
            # Fallback: usar el prompt original para todas las escenas con variaciones
            return [
                f"{prompt}, establishing shot, wide angle",
                f"{prompt}, close-up detail, dramatic lighting",
                f"{prompt}, different perspective, dynamic composition",
                f"{prompt}, finale shot, epic wide angle",
            ][:num_scenes]

    async def _generate_scene_image(self, description: str) -> bytes | None:
        """Genera una imagen para una escena — intenta HF primero, luego Gemini."""
        # Intentar con HuggingFace
        if self._hf_available:
            img = await self._hf_scene_image(description)
            if img:
                return img

        # Fallback: Gemini
        return await self._gemini_scene_image(description)

    async def _hf_scene_image(self, description: str) -> bytes | None:
        """Genera imagen de escena con HuggingFace."""
        url = f"{HF_API_URL}/{HF_IMAGE_MODEL}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        prompt = f"{description}, cinematic, widescreen 16:9, film quality, 4K"
        payload = {"inputs": prompt}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200 and len(response.content) > 1000:
                return response.content
            elif response.status_code == 503:
                # Esperar un poco y reintentar una vez
                await asyncio.sleep(15)
                response = requests.post(url, headers=headers, json=payload, timeout=90)
                if response.status_code == 200 and len(response.content) > 1000:
                    return response.content
        except Exception as e:
            logger.warning(f"HF escena fallida: {e}")

        return None

    async def _gemini_scene_image(self, description: str) -> bytes | None:
        """Genera imagen de escena con Gemini."""
        try:
            response = _get_gemini_client().models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=(
                    f"Generate a cinematic, high-quality, widescreen (16:9) image: "
                    f"{description}. Style: cinematic, vivid colors, 4K film quality, no text."
                ),
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    temperature=1.0,
                ),
            )

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        data = part.inline_data.data
                        if isinstance(data, str):
                            return base64.b64decode(data)
                        return data

        except Exception as e:
            logger.warning(f"Gemini escena fallida: {e}")

        return None

    def _create_video_from_images(self, image_paths: list[str], output_path: str) -> bool:
        """Crea un vídeo a partir de imágenes usando FFmpeg con efecto Ken Burns."""
        try:
            # Crear fichero de lista para FFmpeg
            list_file = os.path.join(TEMP_DIR, f"list_{uuid.uuid4().hex}.txt")
            with open(list_file, "w") as f:
                for img_path in image_paths:
                    f.write(f"file '{img_path}'\n")
                    f.write(f"duration {SCENE_DURATION_SECONDS}\n")
                # Repetir última imagen para que FFmpeg no la corte
                if image_paths:
                    f.write(f"file '{image_paths[-1]}'\n")

            # FFmpeg: crear vídeo con zoom suave (Ken Burns)
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-vf", (
                    "scale=1280:720:force_original_aspect_ratio=decrease,"
                    "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
                    "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1280x720"
                ),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-preset", "fast",
                "-movflags", "+faststart",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.warning(f"FFmpeg con zoompan falló, intentando sin efecto: {result.stderr[:200]}")
                # Fallback sin zoompan (más compatible)
                cmd_simple = [
                    FFMPEG_PATH, "-y",
                    "-f", "concat", "-safe", "0", "-i", list_file,
                    "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", "25",
                    "-preset", "fast",
                    "-movflags", "+faststart",
                    output_path,
                ]
                result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)

            # Limpiar archivo de lista
            try:
                os.remove(list_file)
            except OSError:
                pass

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout (300s)")
            return False
        except Exception as e:
            logger.error(f"Error creando vídeo con FFmpeg: {e}")
            return False
