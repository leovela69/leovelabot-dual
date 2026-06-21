"""Bot Videoclip: Genera prompts para videoclips y animaciones visuales.

Crea prompts detallados y creativos para generación de videoclips,
animaciones y contenido visual usando modelos de IA generativa de video.
Especializado en storytelling visual, composición de escenas y dirección artística.
"""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotVideoclip(BotBase):
    """Genera prompts profesionales para videoclips y animaciones.

    Especializado en:
    - Creación de prompts para generación de video (Runway, Pika, Sora)
    - Composición de escenas y storyboarding textual
    - Dirección artística y estilos visuales
    - Sincronización visual-musical para videoclips
    - Animación de conceptos abstractos y narrativas
    """

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Genera prompt de videoclip."""
        logger.info("🎬 Videoclip generando prompt visual...")
        self.ultima_actividad = __import__("time").time()

        # Determinar tipo de contenido visual
        tipo = self._detectar_tipo_visual(texto)

        # Construir prompt especializado
        prompt = self._construir_prompt_visual(texto, contexto, tipo, retry)

        try:
            resultado = await self._llamar_modelo(prompt)
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)

            # Formatear resultado como storyboard si es videoclip completo
            if tipo == "videoclip_completo":
                resultado = self._formatear_storyboard(resultado)

            return resultado

        except Exception as e:
            logger.error(f"Error en Videoclip: {e}")
            self.fallos += 1
            self._actualizar_score(exito=False)
            return f"Error generando prompt visual: {str(e)}"

    def _detectar_tipo_visual(self, texto: str) -> str:
        """Detecta el tipo de contenido visual solicitado."""
        texto_lower = texto.lower()

        if any(w in texto_lower for w in ["videoclip", "video musical", "clip musical"]):
            return "videoclip_completo"
        elif any(w in texto_lower for w in ["animación", "animar", "motion"]):
            return "animacion"
        elif any(w in texto_lower for w in ["escena", "shot", "plano"]):
            return "escena_individual"
        elif any(w in texto_lower for w in ["loop", "bucle", "gif"]):
            return "loop_visual"
        elif any(w in texto_lower for w in ["transición", "transicion", "morph"]):
            return "transicion"
        else:
            return "prompt_general"

    def _construir_prompt_visual(
        self, texto: str, contexto: Dict[str, Any], tipo: str, retry: bool
    ) -> str:
        """Construye prompt especializado para generación visual."""
        parts = [self.prompt_compiled]

        # Instrucciones según tipo
        instrucciones_tipo = {
            "videoclip_completo": (
                "\nGenera un storyboard completo con 4-8 escenas. "
                "Para cada escena incluye: descripción visual, movimiento de cámara, "
                "iluminación, duración estimada y transición."
            ),
            "animacion": (
                "\nGenera un prompt de animación detallado. "
                "Incluye: estilo (2D/3D/stop-motion), paleta de colores, "
                "movimiento principal y ritmo visual."
            ),
            "escena_individual": (
                "\nGenera un prompt para una escena/shot individual. "
                "Incluye: composición, punto focal, profundidad de campo, iluminación."
            ),
            "loop_visual": (
                "\nGenera un prompt para un loop/bucle visual perfecto. "
                "El inicio y final deben conectar fluidamente."
            ),
            "transicion": (
                "\nGenera un prompt para transición entre escenas. "
                "Describe el morph/movimiento entre estado A y estado B."
            ),
            "prompt_general": (
                "\nGenera un prompt visual creativo y detallado "
                "optimizado para modelos de generación de video."
            ),
        }

        parts.append(instrucciones_tipo.get(tipo, instrucciones_tipo["prompt_general"]))

        # Contexto musical si existe
        if contexto.get("ultimo_output") and any(
            w in contexto.get("ultimo_output", "").lower()
            for w in ["letra", "verse", "chorus", "canción"]
        ):
            parts.append(
                f"\nContexto musical (sincronizar visual con esto):\n"
                f"{contexto['ultimo_output'][:500]}"
            )

        parts.append(f"\nSolicitud del usuario: {texto}")
        parts.append("\nResponde SOLO con el/los prompt(s) listos para usar.")

        if retry:
            parts.append("\n[Sé más creativo y detallado. Añade referencias artísticas.]")

        return "\n".join(parts)

    def _formatear_storyboard(self, resultado: str) -> str:
        """Formatea resultado como storyboard visual."""
        if "Escena" not in resultado and "Scene" not in resultado:
            # Añadir formato de storyboard si el modelo no lo hizo
            return f"🎬 STORYBOARD GENERADO:\n\n{resultado}"
        return f"🎬 STORYBOARD:\n\n{resultado}"


bot_videoclip = BotVideoclip(
    id="bot_videoclip",
    nombre="Videoclip",
    especialidad="Generación de prompts para videoclips, animaciones y contenido visual",
    keywords=["video", "clip", "animación", "visual", "videoclip", "escena", "storyboard", "motion"],
    prompt_compiled=(
        "Eres un director creativo de videoclips y animaciones. "
        "Generas prompts detallados para modelos de video IA (Runway, Pika, Sora). "
        "Dominas composición visual, dirección de fotografía, color grading y storytelling visual. "
        "Cada prompt debe incluir: sujeto, acción, entorno, iluminación, estilo artístico, "
        "movimiento de cámara. Formato listo para copiar y usar."
    ),
    modelo="huggingface",
    herramientas=["generar_storyboard", "crear_escena", "sugerir_estilos_visuales"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_videoclip)
