"""Bot Enjambre: Clona un bot N veces para tareas masivas."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any, List
from loguru import logger
import asyncio
import copy


class BotEnjambre(BotBase):
    """Enjambre clona bots para procesamiento masivo en paralelo."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🐝 Enjambre activado...")
        self.ultima_actividad = __import__("time").time()

        # Determinar qué bot clonar y cuántas veces
        bot_base, cantidad, subtareas = self._analizar_tarea(texto)
        if not bot_base:
            return "No pude determinar qué bot clonar para esta tarea masiva."

        # Ejecutar en paralelo
        resultados = await self._ejecutar_enjambre(bot_base, subtareas, contexto)

        self.tareas_completadas += 1
        return (
            f"🐝 Enjambre completado:\n"
            f"• Bot clonado: {bot_base.id}\n"
            f"• Clones usados: {len(subtareas)}\n"
            f"• Resultados: {len(resultados)} outputs generados\n\n"
            + "\n---\n".join(resultados[:5])
            + (f"\n\n... y {len(resultados)-5} más" if len(resultados) > 5 else "")
        )

    def _analizar_tarea(self, texto: str):
        """Determina bot a clonar y divide en subtareas"""
        # Buscar el bot más adecuado
        bot_base = None
        for bot in REGISTRY.values():
            if bot.estado in ["activo", "elite"] and bot.id != self.id:
                for kw in bot.keywords:
                    if kw in texto.lower():
                        bot_base = bot
                        break
                if bot_base:
                    break

        if not bot_base:
            bot_base = REGISTRY.get("bot_frontend")

        # Crear subtareas (simplificado)
        import re
        nums = re.findall(r'\d+', texto)
        cantidad = int(nums[0]) if nums else 5
        cantidad = min(cantidad, 20)  # Max 20 clones

        subtareas = [f"{texto} (variación {i+1})" for i in range(cantidad)]
        return bot_base, cantidad, subtareas

    async def _ejecutar_enjambre(self, bot_base: BotBase, subtareas: list, contexto: Dict) -> List[str]:
        """Ejecuta subtareas en paralelo con clones"""
        async def ejecutar_clon(tarea: str) -> str:
            clon = copy.copy(bot_base)
            try:
                return await clon.ejecutar(tarea, contexto)
            except Exception as e:
                return f"Error en clon: {str(e)}"

        # Ejecutar hasta 5 en paralelo (límite de rate)
        resultados = []
        for batch in [subtareas[i:i+5] for i in range(0, len(subtareas), 5)]:
            batch_results = await asyncio.gather(
                *[ejecutar_clon(t) for t in batch],
                return_exceptions=True
            )
            for r in batch_results:
                if isinstance(r, Exception):
                    resultados.append(f"Error: {str(r)}")
                else:
                    resultados.append(str(r))

        return resultados


bot_enjambre = BotEnjambre(
    id="bot_enjambre",
    nombre="Enjambre",
    especialidad="Procesamiento masivo en paralelo, clonación de bots",
    keywords=["masivo", "múltiples", "100", "50", "genera muchos", "variaciones", "batch"],
    prompt_compiled="Clona bots y ejecuta tareas masivas en paralelo.",
    modelo="gemini-flash",
    herramientas=["clonar_bot", "ejecutar_paralelo", "ensamblar_resultados"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_enjambre)
