"""Bot Archivista: Knowledge base estructurada del sistema."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotArchivista(BotBase):
    """Archivista mantiene conocimiento estructurado (no tareas, SABER)."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("📚 Archivista consultando base de conocimiento...")
        self.ultima_actividad = __import__("time").time()

        if "guardar" in texto.lower() or "recuerda" in texto.lower():
            return await self._guardar_conocimiento(texto)
        else:
            return await self._consultar_conocimiento(texto)

    async def _consultar_conocimiento(self, consulta: str) -> str:
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if not client:
                return "📚 Base de conocimiento no disponible."

            result = client.table("conocimiento").select("*").ilike(
                "dato", f"%{consulta[:50]}%"
            ).order("veces_consultado", desc=True).limit(5).execute()

            if not result.data:
                return "📚 No encontré información sobre eso en la base de conocimiento."

            lines = ["📚 Conocimiento encontrado:\n"]
            for item in result.data:
                lines.append(f"• [{item['categoria']}] {item['dato']}")
                # Incrementar contador
                client.table("conocimiento").update({
                    "veces_consultado": item["veces_consultado"] + 1
                }).eq("id", item["id"]).execute()

            return "\n".join(lines)
        except Exception as e:
            return f"Error consultando: {str(e)}"

    async def _guardar_conocimiento(self, texto: str) -> str:
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if not client:
                return "❌ No pude guardar."

            # Extraer el dato (todo después de "guardar" o "recuerda")
            import re
            dato = re.sub(r"^(guardar?|recuerda)\s+", "", texto, flags=re.IGNORECASE).strip()

            client.table("conocimiento").insert({
                "categoria": "general",
                "dato": dato[:500],
                "fuente": "usuario",
                "confianza": 1.0,
            }).execute()

            return f"📚 Guardado en base de conocimiento:\n• {dato[:200]}"
        except Exception as e:
            return f"Error guardando: {str(e)}"


bot_archivista = BotArchivista(
    id="bot_archivista",
    nombre="Archivista",
    especialidad="Base de conocimiento estructurada, hechos, preferencias, reglas",
    keywords=["conocimiento", "saber", "recuerda", "guardar", "wiki", "dato", "hecho"],
    prompt_compiled="Gestiona la base de conocimiento. Guarda y recupera hechos.",
    modelo="groq",
    herramientas=["guardar_hecho", "consultar_hecho"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_archivista)
