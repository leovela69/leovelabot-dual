"""Bot Centinela: Vigila proyectos desplegados 24/7."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger
import httpx


class BotCentinela(BotBase):
    """Centinela vigila URLs desplegadas. No usa IA, solo ping."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("👁️ Centinela verificando URLs...")
        self.ultima_actividad = __import__("time").time()

        # Verificar URL específica o todas las conocidas
        url = self._extraer_url(texto)
        if url:
            return await self._verificar_url(url)
        return "Especifica una URL para verificar o usa /custodio estado para la web principal."

    def _extraer_url(self, texto: str) -> str:
        import re
        urls = re.findall(r'https?://\S+', texto)
        return urls[0] if urls else ""

    async def _verificar_url(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                latencia = resp.elapsed.total_seconds() * 1000

                if resp.status_code == 200:
                    estado = "✅ OK"
                elif resp.status_code < 400:
                    estado = f"⚠️ Redirect ({resp.status_code})"
                else:
                    estado = f"❌ Error ({resp.status_code})"

                return (
                    f"📡 Estado de {url}:\n"
                    f"• Status: {estado}\n"
                    f"• Latencia: {latencia:.0f}ms\n"
                    f"• {'Saludable' if resp.status_code == 200 else 'Requiere atención'}"
                )
        except httpx.TimeoutException:
            return f"🚨 TIMEOUT: {url} no respondió en 10 segundos"
        except Exception as e:
            return f"❌ Error verificando {url}: {str(e)}"


bot_centinela = BotCentinela(
    id="bot_centinela",
    nombre="Centinela",
    especialidad="Monitoreo de uptime, latencia, disponibilidad de URLs",
    keywords=["monitorear", "vigilar", "uptime", "ping", "caída", "status"],
    prompt_compiled="Vigila URLs. Reporta estado, latencia, errores.",
    modelo="groq",
    herramientas=["ping_url", "check_ssl", "check_latencia"],
    estado="activo",
    score=4.5,
)

registrar_bot_en_memoria(bot_centinela)
