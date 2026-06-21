"""Cliente Redis (Upstash): Cache rápido + colas de mensajes"""

from loguru import logger
from typing import Optional
import config

_redis_client = None


async def get_redis():
    """Obtiene cliente Redis (singleton)"""
    global _redis_client
    if _redis_client is None:
        try:
            if not config.UPSTASH_REDIS_URL:
                logger.debug("Redis no configurado")
                return None

            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                config.UPSTASH_REDIS_URL,
                password=config.UPSTASH_REDIS_TOKEN,
                decode_responses=True
            )
            await _redis_client.ping()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible: {e}")
            return None
    return _redis_client


async def publicar_mensaje_bot(from_bot: str, to_bot: str, tipo: str, payload: str):
    """Publica mensaje en la cola de un bot (comunicación entre bots)"""
    try:
        r = await get_redis()
        if not r:
            return

        import json
        mensaje = json.dumps({
            "from": from_bot,
            "to": to_bot,
            "tipo": tipo,
            "payload": payload
        })
        await r.rpush(f"bot_queue:{to_bot}", mensaje)
        await r.expire(f"bot_queue:{to_bot}", 3600)
    except Exception as e:
        logger.error(f"Error publicando mensaje: {e}")


async def leer_mensajes_bot(bot_id: str, max_msgs: int = 10) -> list:
    """Lee mensajes pendientes de la cola de un bot"""
    try:
        r = await get_redis()
        if not r:
            return []

        import json
        mensajes = []
        for _ in range(max_msgs):
            msg = await r.lpop(f"bot_queue:{bot_id}")
            if msg:
                mensajes.append(json.loads(msg))
            else:
                break
        return mensajes
    except Exception as e:
        logger.error(f"Error leyendo mensajes: {e}")
        return []


async def incrementar_contador(key: str, ttl: int = 3600) -> int:
    """Incrementa contador (para rate limiting)"""
    try:
        r = await get_redis()
        if not r:
            return 0

        count = await r.incr(key)
        if count == 1:
            await r.expire(key, ttl)
        return count
    except Exception:
        return 0
