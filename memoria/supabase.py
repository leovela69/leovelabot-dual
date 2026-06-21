"""Cliente Supabase: Base de datos principal + Storage"""

from loguru import logger
from typing import Optional, Dict, Any
import config

_client = None


async def get_client():
    """Obtiene el cliente de Supabase (singleton)"""
    global _client
    if _client is None:
        try:
            from supabase import create_client
            _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
            logger.info("✅ Supabase conectado")
        except Exception as e:
            logger.error(f"❌ Error conectando Supabase: {e}")
            return None
    return _client


async def guardar_tarea(chat_id: str, texto: str, resultado: str, score: int, bot_id: str):
    """Guarda una tarea completada en la base de datos"""
    try:
        client = await get_client()
        if not client:
            return

        data = {
            "usuario_id": chat_id,
            "bot_id": bot_id,
            "tipo": "crear",
            "orden_raw": texto[:1000],
            "resultado": resultado[:5000] if resultado else "",
            "calidad": score,
            "tokens_usados": len(texto.split()) * 3,
        }
        client.table("tareas").insert(data).execute()
        logger.debug(f"Tarea guardada: score={score}, bot={bot_id}")
    except Exception as e:
        logger.error(f"Error guardando tarea: {e}")


async def registrar_bot(bot):
    """Registra un bot nuevo en la base de datos"""
    try:
        client = await get_client()
        if not client:
            return

        data = {
            "id": bot.id,
            "nombre": bot.nombre,
            "especialidad": bot.especialidad,
            "keywords": bot.keywords,
            "prompt_compiled": bot.prompt_compiled,
            "modelo": bot.modelo,
            "estado": bot.estado,
        }
        client.table("bots").upsert(data).execute()
        logger.debug(f"Bot registrado en DB: {bot.id}")
    except Exception as e:
        logger.error(f"Error registrando bot: {e}")


async def buscar_tareas_similares(texto: str, limit: int = 5):
    """Busca tareas similares en el historial"""
    try:
        client = await get_client()
        if not client:
            return []

        result = client.table("tareas").select("*").ilike(
            "orden_raw", f"%{texto[:50]}%"
        ).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error buscando tareas: {e}")
        return []


async def obtener_bots_activos():
    """Obtiene todos los bots activos del Registry"""
    try:
        client = await get_client()
        if not client:
            return []

        result = client.table("bots").select("*").in_(
            "estado", ["activo", "elite"]
        ).order("score", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error obteniendo bots: {e}")
        return []


async def actualizar_score_bot(bot_id: str, nuevo_score: float):
    """Actualiza el score de un bot"""
    try:
        client = await get_client()
        if not client:
            return

        client.table("bots").update({
            "score": nuevo_score
        }).eq("id", bot_id).execute()
    except Exception as e:
        logger.error(f"Error actualizando score: {e}")


async def obtener_metricas_sistema():
    """Obtiene métricas generales del sistema"""
    try:
        client = await get_client()
        if not client:
            return {}

        bots = client.table("bots").select("id", count="exact").execute()
        tareas = client.table("tareas").select("id", count="exact").execute()

        return {
            "bots_total": bots.count if bots else 0,
            "tareas_total": tareas.count if tareas else 0,
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return {}
