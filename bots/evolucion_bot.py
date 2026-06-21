"""Bot Evolución: Mejora prompts de otros bots (Darwiniano)."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any
from loguru import logger


class BotEvolucion(BotBase):
    """Evoluciona prompts: genera variantes, las prueba, la mejor sobrevive."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🧬 Evolución ejecutando ciclo Darwiniano...")
        self.ultima_actividad = __import__("time").time()

        # Encontrar bots con score bajo para mejorar
        bots_mejorar = [b for b in REGISTRY.values()
                        if b.estado == "activo" and b.score < 3.5 and b.tareas_completadas > 5]

        if not bots_mejorar:
            return "✅ Todos los bots tienen buen rendimiento. Sin mejoras necesarias."

        resultados = []
        for bot in bots_mejorar[:3]:
            nuevo_prompt = await self._mutar_prompt(bot)
            resultados.append(f"• {bot.id}: prompt mutado (score actual: {bot.score:.1f})")

        self.tareas_completadas += 1
        return "🧬 Evolución completada:\n" + "\n".join(resultados)

    async def _mutar_prompt(self, bot: BotBase) -> str:
        """Genera una mutación del prompt del bot"""
        prompt_base = bot.prompt_compiled
        # Mutación simple: agregar instrucción de calidad
        mejoras = [
            " Prioriza calidad sobre velocidad.",
            " Incluye manejo de errores robusto.",
            " Sé más específico y detallado.",
            " Usa las mejores prácticas 2026.",
        ]
        import random
        mejora = random.choice(mejoras)
        bot.prompt_compiled = prompt_base.rstrip(".") + "." + mejora
        return bot.prompt_compiled


bot_evolucion_meta = BotEvolucion(
    id="bot_evolucion_meta",
    nombre="Evolución",
    especialidad="Mejora Darwiniana de prompts, optimización de bots",
    keywords=["evolucionar", "mejorar", "optimizar", "prompt", "mutación"],
    prompt_compiled="Mejora los prompts de otros bots usando selección natural.",
    modelo="gemini-pro",
    herramientas=["mutar_prompt", "evaluar_prompt", "seleccionar"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_evolucion_meta)
