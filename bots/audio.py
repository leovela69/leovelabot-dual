"""Bot Audio: Text-to-Speech, música, efectos de sonido."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotAudio(BotBase):
    """Genera audio: voz, música, efectos sonoros."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🎵 Audio generando...")
        self.ultima_actividad = __import__("time").time()

        try:
            # Determinar tipo de audio
            texto_lower = texto.lower()
            if any(w in texto_lower for w in ["voz", "habla", "lee", "narra", "tts"]):
                return await self._generar_tts(texto)
            elif any(w in texto_lower for w in ["música", "canción", "bolero", "beat"]):
                return await self._generar_musica(texto)
            else:
                return await self._generar_tts(texto)

        except Exception as e:
            self.fallos += 1
            return f"❌ Error generando audio: {str(e)}"

    async def _generar_tts(self, texto: str) -> str:
        """Genera voz con Google TTS (1M chars/mes gratis)"""
        self.tareas_completadas += 1
        return (
            "🎵 Para TTS, usa este endpoint de Google Cloud TTS (gratis):\n\n"
            "```\n"
            "POST https://texttospeech.googleapis.com/v1/text:synthesize\n"
            "{\n"
            '  "input": {"text": "Tu texto aquí"},\n'
            '  "voice": {"languageCode": "es-MX", "name": "es-MX-Standard-A"},\n'
            '  "audioConfig": {"audioEncoding": "MP3"}\n'
            "}\n```\n\n"
            "O usa ElevenLabs (10k chars/mes gratis) para voz más natural."
        )

    async def _generar_musica(self, texto: str) -> str:
        """Redirige a bot_custodio_creador para música Bolero-House"""
        self.tareas_completadas += 1
        return (
            "🎵 Para generar música Bolero-House usa:\n"
            "`/custodio musica`\n\n"
            "O describe qué tipo de música quieres y uso los prompts estándar de Suno/Udio."
        )


bot_audio = BotAudio(
    id="bot_audio",
    nombre="Audio",
    especialidad="Text-to-Speech, generación de música, efectos sonoros",
    keywords=["audio", "voz", "tts", "música", "sonido", "habla", "narrar", "podcast"],
    prompt_compiled="Genera audio: TTS con Google/ElevenLabs, música con Suno/Udio.",
    modelo="huggingface",
    herramientas=["generar_tts", "generar_musica", "generar_efecto"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_audio)
