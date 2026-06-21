"""Script: Resetea el sistema (mantiene datos en DB, limpia cache)."""

import asyncio
from loguru import logger


async def resetear():
    """Resetea cache y estado en memoria sin borrar DB"""
    logger.info("🔄 Reseteando sistema...")

    # Limpiar cache L1
    from core.reflejo import _cache_l1, _cache_l1_timestamps
    _cache_l1.clear()
    _cache_l1_timestamps.clear()
    logger.info("✅ Cache L1 limpiado")

    # Limpiar Redis cache
    try:
        from memoria.redis import get_redis
        r = await get_redis()
        if r:
            await r.flushdb()
            logger.info("✅ Redis limpiado")
    except Exception as e:
        logger.warning(f"Redis no disponible: {e}")

    # Recargar bots
    from scripts.crear_bots_iniciales import cargar_todos_los_bots
    registry = cargar_todos_los_bots()
    logger.info(f"✅ {len(registry)} bots recargados")

    logger.info("🔄 Reset completo")


if __name__ == "__main__":
    asyncio.run(resetear())
