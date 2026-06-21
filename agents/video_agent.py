# -*- coding: utf-8 -*-
"""
Agente de Vídeo — Generación de vídeos cortos y largos.
Vídeos cortos: genera imágenes con Gemini + las anima con FFmpeg.
Vídeos largos: delega al VideoPipeline.
"""

import io
import os
import base64
import logging
import subprocess
import tempfile
import uuid
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    GEMINI_CHAT_MODEL,
    FFMPEG_PATH,
    TEMP_DIR,
    SCENE_DURATION_SECONDS,
)

from agents.model_manager import smart_generate

logger = logging.getLogger("leovelabot.video")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class VideoAgent:
    """Genera vídeos cortos (hasta ~30s) usando imágenes IA + FFmpeg."""

    def __init__(self):
        os.makedirs(TEMP_DIR, exist_ok=True)
        logger.info("🎬 Video Agent inicializado")

    async def _generate_scene_image(self, description: str) -> bytes | None:
        """Genera una imagen para una escena del vídeo."""
        try:
            prompt = (
                f"Generate a cinematic, high-quality, widescreen (16:9) image for a video scene: "
                f"{description}. Style: cinematic, vivid colors, professional film quality, 4K look."
            )

            response = await smart_generate(_get_client(), GEMINI_IMAGE_MODEL,
                contents=prompt,
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
            logger.error(f"Error generando imagen de escena: {e}")

        return None

    async def _generate_scene_descriptions(self, prompt: str, num_scenes: int) -> list[str]:
        """Usa Gemini para generar descripciones visuales de cada escena."""
        try:
            response = await smart_generate(_get_client(), GEMINI_CHAT_MODEL,
                contents=(
                    f"Genera exactamente {num_scenes} descripciones de escenas visuales para un vídeo corto sobre: "
                    f"'{prompt}'. Cada descripción debe ser una línea que describa la imagen visual de esa escena. "
                    f"Solo escribe las descripciones, una por línea, sin números ni viñetas. "
                    f"Cada descripción debe ser detallada y cinematográfica."
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
            return [prompt] * num_scenes

    def _create_video_from_images(self, image_paths: list[str], output_path: str) -> bool:
        """Crea un vídeo a partir de imágenes usando FFmpeg con efecto Ken Burns."""
        try:
            # Crear un fichero de lista para FFmpeg
            list_file = os.path.join(TEMP_DIR, f"list_{uuid.uuid4().hex}.txt")
            with open(list_file, "w") as f:
                for img_path in image_paths:
                    f.write(f"file '{img_path}'\n")
                    f.write(f"duration {SCENE_DURATION_SECONDS}\n")
                # Repetir la última imagen para que FFmpeg no la corte
                if image_paths:
                    f.write(f"file '{image_paths[-1]}'\n")

            # FFmpeg: crear vídeo con transiciones suaves
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.001,1.3)':d=125:s=1280x720",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-preset", "fast",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                # Intentar sin zoompan como fallback
                cmd_simple = [
                    FFMPEG_PATH,
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", "25",
                    "-preset", "fast",
                    output_path,
                ]
                result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)

            # Limpiar archivo de lista
            os.remove(list_file)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error creando vídeo con FFmpeg: {e}")
            return False

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera un vídeo corto (~15-30 segundos)."""
        try:
            num_scenes = 4  # 4 escenas × 5s = 20s de vídeo

            # 1. Generar descripciones de escenas
            logger.info(f"📝 Generando {num_scenes} escenas para: {message[:50]}...")
            scene_descriptions = await self._generate_scene_descriptions(message, num_scenes)

            # 2. Generar imagen para cada escena
            image_paths = []
            for i, desc in enumerate(scene_descriptions):
                logger.info(f"🖼️ Generando imagen {i+1}/{len(scene_descriptions)}: {desc[:40]}...")
                img_data = await self._generate_scene_image(desc)

                if img_data:
                    img_path = os.path.join(TEMP_DIR, f"scene_{uuid.uuid4().hex}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    image_paths.append(img_path)

            if not image_paths:
                return {
                    "type": "text",
                    "content": "❌ No pude generar las imágenes para el vídeo. Intenta con otra descripción.",
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

                # Limpiar vídeo temporal
                os.remove(output_path)

                return {
                    "type": "video",
                    "content": video_bytes,
                    "caption": f"🎬 Vídeo generado: _{message[:80]}_\n📐 {len(image_paths)} escenas × {SCENE_DURATION_SECONDS}s",
                }
            else:
                return {
                    "type": "text",
                    "content": "❌ Error al componer el vídeo con FFmpeg. Verifica que FFmpeg está instalado.",
                }

        except Exception as e:
            logger.error(f"Error en Video Agent: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"❌ Error generando el vídeo: {str(e)}",
            }
