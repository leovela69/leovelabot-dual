"""Bot Espía: Scrapea tendencias tech cada 6h."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotEspia(BotBase):
    """Espía monitorea tendencias externas para mantener el sistema actualizado."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🕵️ Espía investigando tendencias...")
        self.ultima_actividad = __import__("time").time()

        tendencias = await self._buscar_tendencias()
        self.tareas_completadas += 1
        return tendencias

    async def _buscar_tendencias(self) -> str:
        """Busca tendencias tech usando Serper API"""
        try:
            import config
            import httpx

            if not config.SERPER_API_KEY:
                return "🕵️ Sin API key de búsqueda. Usando tendencias predefinidas."

            queries = [
                "trending web development frameworks 2026",
                "popular programming technologies this week",
                "latest frontend trends"
            ]

            import random
            query = random.choice(queries)

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": config.SERPER_API_KEY},
                    json={"q": query, "num": 5}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("organic", [])[:5]
                    lines = ["🕵️ Tendencias detectadas:\n"]
                    for r in results:
                        lines.append(f"• {r.get('title', 'N/A')}")

                    # Guardar en DB
                    await self._guardar_tendencias(lines)
                    return "\n".join(lines)

            return "🕵️ No pude obtener tendencias. Reintentaré después."
        except Exception as e:
            logger.error(f"Error buscando tendencias: {e}")
            return f"🕵️ Error: {str(e)}"

    async def _guardar_tendencias(self, tendencias: list):
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if client:
                client.table("tendencias").insert({
                    "fuente": "serper",
                    "tecnologias": tendencias[:10],
                    "resumen": "\n".join(tendencias[:5]),
                }).execute()
        except Exception as e:
            logger.error(f"Error guardando tendencias: {e}")


bot_espia = BotEspia(
    id="bot_espia",
    nombre="Espía",
    especialidad="Monitoreo de tendencias tech, scraping ético, inteligencia competitiva",
    keywords=["tendencia", "trending", "popular", "nuevo", "competencia", "mercado"],
    prompt_compiled="Busca tendencias en web. Scrapea GitHub, HN, ProductHunt.",
    modelo="gemini-pro",
    herramientas=["web_search", "scrape_trends", "guardar_tendencias"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_espia)
