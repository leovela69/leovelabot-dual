# -*- coding: utf-8 -*-
"""
Pipeline de Vídeos Largos — Composición de vídeos de hasta 20 minutos.
Genera guión → escenas → imágenes → clips → vídeo final con FFmpeg.
Envía actualizaciones de progreso al usuario vía Telegram.
"""

import os
import uuid
import logging
import subprocess
import asyncio
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_IMAGE_MODEL,
    FFMPEG_PATH,
    TEMP_DIR,
    SCENE_DURATION_SECONDS,
    MAX_VIDEO_DURATION_MINUTES,
    MAX_SCENES_PER_VIDEO,
)

from agents.model_manager import smart_generate

logger = logging.getLogger("leovelabot.video_pipeline")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class VideoPipeline:
    """Pipeline completo para generar vídeos largos (hasta 20 min)."""

    def __init__(self):
        os.makedirs(TEMP_DIR, exist_ok=True)
        logger.info("📹 Video Pipeline inicializado")

    async def _generate_script(self, prompt: str, duration_minutes: int) -> dict:
        """Genera un guión completo con escenas, diálogos y descripciones visuales."""
        num_scenes = min(
            (duration_minutes * 60) // SCENE_DURATION_SECONDS,
            MAX_SCENES_PER_VIDEO,
        )

        response = await smart_generate(_get_client(), GEMINI_CHAT_MODEL,
            contents=(
                f"Eres un guionista profesional de cine. Crea un guión detallado para un vídeo "
                f"de {duration_minutes} minutos sobre: '{prompt}'.\n\n"
                f"El vídeo tendrá exactamente {num_scenes} escenas de {SCENE_DURATION_SECONDS} segundos cada una.\n\n"
                f"Para CADA escena, escribe en formato JSON:\n"
                f'{{"scenes": [\n'
                f'  {{"scene_number": 1, "visual": "Descripción visual detallada de lo que se ve", '
                f'"narration": "Texto de narración o diálogo para esta escena", '
                f'"mood": "Estado de ánimo: épico/tranquilo/tenso/alegre/etc"}},\n'
                f"  ...\n"
                f"]}}\n\n"
                f"Responde SOLO con el JSON, sin explicaciones adicionales."
            ),
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=8192,
            ),
        )

        # Parsear el JSON del guión
        import json
        text = response.text.strip()
        # Limpiar posibles marcadores de código
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            script = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: crear escenas simples
            logger.warning("No se pudo parsear el guión JSON, usando fallback")
            script = {
                "scenes": [
                    {
                        "scene_number": i + 1,
                        "visual": f"Escena {i+1} de un vídeo sobre {prompt}",
                        "narration": "",
                        "mood": "neutral",
                    }
                    for i in range(num_scenes)
                ]
            }

        return script

    async def _generate_scene_image(self, visual_description: str, mood: str) -> bytes | None:
        """Genera una imagen cinematográfica para una escena."""
        import base64

        try:
            style_map = {
                "épico": "epic, dramatic lighting, wide angle, cinematic",
                "tranquilo": "calm, soft lighting, peaceful, serene",
                "tenso": "tense, dark shadows, high contrast, dramatic",
                "alegre": "joyful, bright colors, warm lighting, happy",
                "misterioso": "mysterious, fog, dark, enigmatic",
                "acción": "action, dynamic, motion blur, intense",
            }
            style = style_map.get(mood, "cinematic, professional, high quality")

            response = await smart_generate(_get_client(), GEMINI_IMAGE_MODEL,
                contents=(
                    f"Generate a cinematic widescreen (16:9) image: {visual_description}. "
                    f"Style: {style}, 4K film quality, no text or watermarks."
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
            logger.error(f"Error generando imagen de escena: {e}")

        return None

    def _stitch_video(self, image_paths: list[str], output_path: str) -> bool:
        """Une todas las imágenes en un vídeo final con FFmpeg."""
        try:
            list_file = os.path.join(TEMP_DIR, f"pipeline_list_{uuid.uuid4().hex}.txt")
            with open(list_file, "w") as f:
                for img_path in image_paths:
                    f.write(f"file '{img_path}'\n")
                    f.write(f"duration {SCENE_DURATION_SECONDS}\n")
                if image_paths:
                    f.write(f"file '{image_paths[-1]}'\n")

            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                       "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", "25", "-preset", "fast",
                "-movflags", "+faststart",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            os.remove(list_file)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error en FFmpeg stitching: {e}")
            return False

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """
        Genera un vídeo largo completo. Retorna el resultado por partes
        para que el bot pueda enviar actualizaciones de progreso.
        """
        try:
            # Determinar duración deseada
            import re
            duration_match = re.search(r"(\d+)\s*min", message)
            duration = int(duration_match.group(1)) if duration_match else 2
            duration = min(duration, MAX_VIDEO_DURATION_MINUTES)

            num_scenes = (duration * 60) // SCENE_DURATION_SECONDS

            # Paso 1: Guión
            logger.info(f"📝 Generando guión para {duration} min ({num_scenes} escenas)...")
            script = await self._generate_script(message, duration)
            scenes = script.get("scenes", [])[:num_scenes]

            if not scenes:
                return {"type": "text", "content": "❌ No pude generar el guión. Intenta de nuevo."}

            # Paso 2: Generar imágenes
            image_paths = []
            progress_updates = []

            for i, scene in enumerate(scenes):
                visual = scene.get("visual", f"Escena {i+1}")
                mood = scene.get("mood", "neutral")

                logger.info(f"🖼️ Escena {i+1}/{len(scenes)}: {visual[:50]}...")
                img_data = await self._generate_scene_image(visual, mood)

                if img_data:
                    img_path = os.path.join(TEMP_DIR, f"pipeline_{uuid.uuid4().hex}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    image_paths.append(img_path)

                # Reportar progreso cada 10 escenas
                if (i + 1) % 10 == 0:
                    pct = int(((i + 1) / len(scenes)) * 100)
                    progress_updates.append(f"🎬 Progreso: {pct}% ({i+1}/{len(scenes)} escenas)")

                # Pequeña pausa para no saturar la API
                await asyncio.sleep(0.5)

            if not image_paths:
                return {"type": "text", "content": "❌ No se pudieron generar las imágenes."}

            # Paso 3: Componer vídeo
            output_path = os.path.join(TEMP_DIR, f"long_video_{uuid.uuid4().hex}.mp4")
            logger.info(f"🎬 Componiendo vídeo final con {len(image_paths)} escenas...")

            success = self._stitch_video(image_paths, output_path)

            # Limpiar imágenes temporales
            for p in image_paths:
                try:
                    os.remove(p)
                except OSError:
                    pass

            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)

                # Telegram limita a 50MB para vídeos
                if file_size > 50 * 1024 * 1024:
                    # Dividir en partes
                    return await self._split_and_return(output_path, message)

                with open(output_path, "rb") as f:
                    video_bytes = f.read()
                os.remove(output_path)

                return {
                    "type": "video",
                    "content": video_bytes,
                    "caption": (
                        f"🎬 *Vídeo largo generado*\n"
                        f"📝 _{message[:80]}_\n"
                        f"⏱️ {len(image_paths) * SCENE_DURATION_SECONDS}s "
                        f"({len(image_paths)} escenas)\n"
                        f"📦 {file_size / (1024*1024):.1f} MB"
                    ),
                    "progress": progress_updates,
                }
            else:
                return {"type": "text", "content": "❌ Error al componer el vídeo final."}

        except Exception as e:
            logger.error(f"Error en Video Pipeline: {e}", exc_info=True)
            return {"type": "text", "content": f"❌ Error en el pipeline de vídeo: {str(e)}"}

    async def _split_and_return(self, video_path: str, original_prompt: str) -> dict:
        """Divide un vídeo grande en partes de <50MB para Telegram."""
        try:
            parts = []
            part_num = 1
            part_path = os.path.join(TEMP_DIR, f"part_{part_num}_{uuid.uuid4().hex}.mp4")

            # Dividir en segmentos de 3 minutos
            cmd = [
                FFMPEG_PATH, "-y", "-i", video_path,
                "-c", "copy", "-map", "0",
                "-segment_time", "180",
                "-f", "segment",
                "-reset_timestamps", "1",
                os.path.join(TEMP_DIR, f"split_%03d_{uuid.uuid4().hex}.mp4"),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)

            # Recoger las partes
            import glob
            split_files = sorted(glob.glob(os.path.join(TEMP_DIR, "split_*.mp4")))

            video_parts = []
            for sp in split_files:
                with open(sp, "rb") as f:
                    video_parts.append(f.read())
                os.remove(sp)

            os.remove(video_path)

            return {
                "type": "video_parts",
                "content": video_parts,
                "caption": f"🎬 Vídeo largo: _{original_prompt[:60]}_ (dividido en {len(video_parts)} partes)",
            }

        except Exception as e:
            logger.error(f"Error dividiendo vídeo: {e}")
            return {"type": "text", "content": "❌ El vídeo es demasiado grande para Telegram."}
