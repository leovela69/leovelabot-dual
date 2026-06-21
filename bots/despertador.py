"""Bot Despertador: Vigila que el sistema esté vivo (externo).
Aquí está la lógica de health checking."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger
import httpx


class BotDespertador(BotBase):
    """Despertador verifica salud del sistema principal."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("⏰ Despertador verificando salud...")
        self.ultima_actividad = __import__("time").time()
        return await self._health_check()

    async def _health_check(self) -> str:
        """Verifica todos los componentes del sistema"""
        import config
        resultados = []

        # Check 1: API principal
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{config.TELEGRAM_WEBHOOK_URL.replace('/webhook', '/health')}")
                if resp.status_code == 200:
                    resultados.append("✅ API principal: OK")
                else:
                    resultados.append(f"⚠️ API principal: {resp.status_code}")
        except Exception as e:
            resultados.append(f"❌ API principal: CAÍDA ({e})")

        # Check 2: Supabase
        try:
            from memoria.supabase import get_client
            client = await get_client()
            if client:
                resultados.append("✅ Supabase: OK")
            else:
                resultados.append("⚠️ Supabase: No conectado")
        except Exception:
            resultados.append("❌ Supabase: Error")

        # Check 3: Redis
        try:
            from memoria.redis import get_redis
            r = await get_redis()
            if r:
                await r.ping()
                resultados.append("✅ Redis: OK")
            else:
                resultados.append("⚠️ Redis: No conectado")
        except Exception:
            resultados.append("❌ Redis: Error")

        self.tareas_completadas += 1
        return "⏰ Health Check:\n" + "\n".join(resultados)


bot_despertador = BotDespertador(
    id="bot_despertador",
    nombre="Despertador",
    especialidad="Health checking del sistema, reinicio si cae, alertas",
    keywords=["salud", "health", "status", "reiniciar", "despertar"],
    prompt_compiled="Verifica salud de API, DB, Redis. Alerta si algo falla.",
    modelo="groq",
    herramientas=["ping", "health_check", "restart"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_despertador)
