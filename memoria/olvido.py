"""Olvido Activo: Elimina conocimiento obsoleto.
Mantiene la DB limpia y relevante."""

from loguru import logger
from datetime import datetime, timedelta


async def ciclo_olvido():
    """Ejecuta olvido activo (en modo sueño)"""
    logger.info("🧹 Olvido Activo: limpiando datos obsoletos...")

    await limpiar_tareas_antiguas()
    await limpiar_cache_expirado()
    await archivar_bots_dormidos()

    logger.info("🧹 Olvido Activo: completado")


async def limpiar_tareas_antiguas():
    """Elimina tareas con más de 90 días y score bajo"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return

        fecha_limite = (datetime.now() - timedelta(days=90)).isoformat()

        # Eliminar tareas viejas con score bajo
        result = client.table("tareas").delete().lt(
            "calidad", 50
        ).lt("created_at", fecha_limite).execute()

        if result.data:
            logger.info(f"🧹 Eliminadas {len(result.data)} tareas obsoletas")
    except Exception as e:
        logger.error(f"Error limpiando tareas: {e}")


async def limpiar_cache_expirado():
    """Limpia entradas de cache expiradas en Redis"""
    try:
        from memoria.redis import get_redis
        r = await get_redis()
        if not r:
            return
        # Redis maneja TTL automáticamente, solo log
        logger.debug("Cache Redis: TTL automático activo")
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")


async def archivar_bots_dormidos():
    """Archiva bots dormidos por más de 90 días"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return

        fecha_limite = (datetime.now() - timedelta(days=90)).isoformat()

        # Marcar como muertos los dormidos por >90 días
        result = client.table("bots").update({
            "estado": "muerto"
        }).eq("estado", "dormido").lt(
            "last_activity", fecha_limite
        ).execute()

        if result.data:
            logger.info(f"☠️ Archivados {len(result.data)} bots inactivos")
    except Exception as e:
        logger.error(f"Error archivando bots: {e}")
