"""Bot Memorión: Memoria del sistema.
Guarda y recupera tareas previas usando embeddings."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any, Optional
from loguru import logger


class BotMemorion(BotBase):
    """Memorión tiene lógica especial: busca por similitud, no genera con IA."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Busca en memoria tareas similares"""
        logger.info("🗄️ Memorión buscando tareas similares...")

        # Buscar en Supabase por texto similar
        from memoria.supabase import buscar_tareas_similares
        similares = await buscar_tareas_similares(texto)

        if similares:
            mejor = similares[0]
            return (
                f"📋 Encontré tarea similar (score: {mejor.get('calidad', 0)}):\n"
                f"Orden original: {mejor.get('orden_raw', '')}\n"
                f"Resultado: {mejor.get('resultado', '')[:1000]}"
            )

        # Buscar en arquetipos
        from memoria.arquetipos import buscar_arquetipo
        keywords = texto.lower().split()[:5]
        arquetipo = await buscar_arquetipo(keywords)

        if arquetipo:
            return (
                f"📦 Encontré arquetipo: {arquetipo.get('nombre', '')}\n"
                f"Output base: {arquetipo.get('best_output', '')[:1000]}"
            )

        return "No encontré tareas similares en memoria."


bot_memorion = BotMemorion(
    id="bot_memorion",
    nombre="Memorión",
    especialidad="Búsqueda y recuperación de tareas previas, arquetipos",
    keywords=["memoria", "historial", "anterior", "parecido", "similar", "recuerda"],
    prompt_compiled="Busca tareas similares en la memoria del sistema.",
    modelo="groq",  # No usa IA realmente, solo búsqueda
    herramientas=["buscar_embeddings", "buscar_arquetipos"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_memorion)
