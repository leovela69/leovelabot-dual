"""Bot Profeta: Predice lo que el usuario va a pedir."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotProfeta(BotBase):
    """Profeta analiza patrones del usuario para anticipar necesidades."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🔮 Profeta analizando patrones...")
        self.ultima_actividad = __import__("time").time()

        predicciones = await self._analizar_patrones(contexto)
        self.tareas_completadas += 1
        return predicciones

    async def _analizar_patrones(self, contexto: Dict) -> str:
        """Analiza historial para predecir próxima acción"""
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if not client:
                return "🔮 Sin datos suficientes para predicción."

            chat_id = contexto.get("chat_id", "")
            result = client.table("tareas").select("tipo, orden_raw").eq(
                "usuario_id", chat_id
            ).order("created_at", desc=True).limit(20).execute()

            if not result.data or len(result.data) < 5:
                return "🔮 Necesito más historial para predecir (mín. 5 tareas)."

            # Analizar secuencias frecuentes
            tipos = [t["tipo"] for t in result.data]
            ultimo_tipo = tipos[0] if tipos else "crear"

            secuencias_comunes = {
                "crear": "Probablemente querrás testear o desplegar lo creado.",
                "modificar": "Quizá quieras ver una preview o publicar.",
                "consultar": "Tal vez quieras crear algo basado en lo que investigaste.",
                "desplegar": "Probablemente querrás monitorear el deploy.",
            }

            prediccion = secuencias_comunes.get(ultimo_tipo,
                         "Basado en tu historial, parece que trabajas en proyectos web.")

            return f"🔮 Predicción:\n{prediccion}\n\nÚltimos tipos: {', '.join(tipos[:5])}"

        except Exception as e:
            return f"🔮 Error analizando patrones: {str(e)}"


bot_profeta = BotProfeta(
    id="bot_profeta",
    nombre="Profeta",
    especialidad="Predicción de necesidades del usuario basado en patrones",
    keywords=["predecir", "anticipar", "patrón", "siguiente", "prever"],
    prompt_compiled="Analiza patrones de uso para predecir próximas acciones.",
    modelo="groq",
    herramientas=["analizar_patrones", "pre_generar"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_profeta)
