"""Bot Herrero: Crea herramientas nuevas para otros bots."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotHerrero(BotBase):
    """Herrero fabrica herramientas (funciones Python) para otros bots."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🔨 Herrero fabricando herramienta...")
        self.ultima_actividad = __import__("time").time()

        # Generar herramienta con IA
        resultado = await self._llamar_modelo(
            f"Genera una función Python reutilizable para: {texto}. "
            "Solo la función, con docstring, type hints, manejo de errores. "
            "Debe ser independiente (sin dependencias externas pesadas)."
        )

        # Guardar herramienta en DB
        await self._guardar_herramienta(texto, resultado)

        self.tareas_completadas += 1
        return f"🔨 Herramienta creada:\n\n```python\n{resultado}\n```"

    async def _guardar_herramienta(self, nombre: str, codigo: str):
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if client:
                client.table("herramientas").insert({
                    "nombre": nombre[:100],
                    "descripcion": f"Herramienta para: {nombre[:200]}",
                    "codigo": codigo[:5000],
                    "creado_por": self.id,
                }).execute()
        except Exception as e:
            logger.error(f"Error guardando herramienta: {e}")


bot_herrero = BotHerrero(
    id="bot_herrero",
    nombre="Herrero",
    especialidad="Crear herramientas Python reutilizables para otros bots",
    keywords=["herramienta", "tool", "función", "utilidad", "crear tool"],
    prompt_compiled="Crea funciones Python reutilizables. Type hints, docstring, error handling.",
    modelo="gemini-pro",
    herramientas=["generar_funcion", "registrar_herramienta"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_herrero)
