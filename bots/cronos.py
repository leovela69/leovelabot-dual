"""Bot Cronos: Tareas programadas (cron inteligente)."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotCronos(BotBase):
    """Cronos gestiona tareas programadas del usuario."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("⏰ Cronos procesando tarea programada...")
        self.ultima_actividad = __import__("time").time()

        if "listar" in texto.lower() or "ver" in texto.lower():
            return await self._listar_programadas(contexto)
        elif "cancelar" in texto.lower():
            return "Para cancelar, especifica el ID de la tarea: /programar cancelar [id]"
        else:
            return await self._programar_tarea(texto, contexto)

    async def _programar_tarea(self, texto: str, contexto: Dict) -> str:
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if not client:
                return "❌ No pude conectar con la base de datos."

            chat_id = contexto.get("chat_id", "unknown")
            client.table("tareas_programadas").insert({
                "usuario_id": chat_id,
                "cron_expr": "0 9 * * 1",  # Default: lunes 9am
                "tarea_template": texto,
                "activa": True,
            }).execute()

            return (
                "⏰ Tarea programada guardada:\n"
                f"• Tarea: {texto[:100]}\n"
                "• Frecuencia: Cada lunes 9am (ajustable)\n"
                "• Estado: Activa\n"
                "Usa /programar listar para ver todas."
            )
        except Exception as e:
            return f"❌ Error programando tarea: {str(e)}"

    async def _listar_programadas(self, contexto: Dict) -> str:
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if not client:
                return "Sin conexión a DB."

            chat_id = contexto.get("chat_id", "unknown")
            result = client.table("tareas_programadas").select("*").eq(
                "usuario_id", chat_id
            ).eq("activa", True).execute()

            if not result.data:
                return "📋 No tienes tareas programadas activas."

            lines = ["⏰ Tareas programadas activas:\n"]
            for t in result.data[:10]:
                lines.append(f"• {t['tarea_template'][:50]} ({t['cron_expr']})")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {str(e)}"


bot_cronos = BotCronos(
    id="bot_cronos",
    nombre="Cronos",
    especialidad="Tareas programadas, automatización temporal, cron jobs",
    keywords=["programar", "cada", "lunes", "diario", "semanal", "automático", "cron", "recordar"],
    prompt_compiled="Gestiona tareas programadas. CRUD de cron jobs.",
    modelo="groq",
    herramientas=["crear_cron", "listar_cron", "cancelar_cron"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_cronos)
