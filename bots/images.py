"""Bot Images: Genera imágenes con HuggingFace (FLUX.1 / Stable Diffusion)."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotImages(BotBase):
    """Genera imágenes usando modelos de HuggingFace."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🖼️ Images generando imagen...")
        self.ultima_actividad = __import__("time").time()

        try:
            from ejecutores.frio import generar_imagen
            resultado = await generar_imagen(texto)
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)
            return resultado
        except Exception as e:
            self.fallos += 1
            self._actualizar_score(exito=False)
            return f"❌ Error generando imagen: {str(e)}"


bot_images = BotImages(
    id="bot_images",
    nombre="Images",
    especialidad="Generación de imágenes con IA: logos, fotos, arte, diseños",
    keywords=["imagen", "foto", "logo", "diseño", "arte", "ilustración", "generar imagen", "visual"],
    prompt_compiled="Genera imágenes con Stable Diffusion / FLUX.1 via HuggingFace.",
    modelo="huggingface",
    herramientas=["generar_imagen", "editar_imagen"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_images)
