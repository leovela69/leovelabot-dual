"""Context Thread: Mantiene el hilo de conversación activo.
Recuerda en qué proyecto está trabajando el usuario."""

from loguru import logger
from typing import Dict, Any, Optional


# Cache local de contextos activos (se sincroniza con Redis)
_contextos: Dict[str, Dict[str, Any]] = {}


async def cargar_contexto(chat_id: str) -> Dict[str, Any]:
    """Carga el contexto activo del usuario (proyecto, últimos mensajes, outputs)"""

    # Primero buscar en memoria local
    if chat_id in _contextos:
        return _contextos[chat_id]

    # Buscar en Redis
    try:
        from memoria.redis import get_redis
        redis = await get_redis()
        if redis:
            import json
            data = await redis.get(f"contexto:{chat_id}")
            if data:
                contexto = json.loads(data)
                _contextos[chat_id] = contexto
                return contexto
    except Exception as e:
        logger.debug(f"Error cargando contexto de Redis: {e}")

    # Contexto vacío si no existe
    contexto_nuevo = {
        "proyecto_activo": None,
        "ultimos_mensajes": [],
        "ultimo_output": None,
        "ultimo_bot_usado": None,
        "idioma": "es"
    }
    _contextos[chat_id] = contexto_nuevo
    return contexto_nuevo


async def actualizar_contexto(chat_id: str, mensaje: str, output: str):
    """Actualiza el contexto con el nuevo mensaje y output"""
    contexto = _contextos.get(chat_id, {
        "proyecto_activo": None,
        "ultimos_mensajes": [],
        "ultimo_output": None,
        "ultimo_bot_usado": None,
        "idioma": "es"
    })

    # Agregar mensaje al historial (máx 5)
    contexto["ultimos_mensajes"].append(mensaje)
    if len(contexto["ultimos_mensajes"]) > 5:
        contexto["ultimos_mensajes"] = contexto["ultimos_mensajes"][-5:]

    # Guardar último output (truncado para no saturar memoria)
    contexto["ultimo_output"] = output[:2000] if output else None

    _contextos[chat_id] = contexto

    # Sincronizar con Redis (async, no bloquea)
    try:
        from memoria.redis import get_redis
        redis = await get_redis()
        if redis:
            import json
            await redis.setex(
                f"contexto:{chat_id}",
                1800,  # TTL 30 min (se renueva con cada mensaje)
                json.dumps(contexto, ensure_ascii=False)
            )
    except Exception as e:
        logger.debug(f"Error guardando contexto en Redis: {e}")


async def cambiar_proyecto(chat_id: str, nombre_proyecto: str):
    """Cambia el proyecto activo del usuario"""
    contexto = await cargar_contexto(chat_id)
    contexto["proyecto_activo"] = nombre_proyecto
    contexto["ultimos_mensajes"] = []
    contexto["ultimo_output"] = None
    _contextos[chat_id] = contexto
    await actualizar_contexto(chat_id, f"/proyecto {nombre_proyecto}", "")
    logger.info(f"Usuario {chat_id} cambió a proyecto: {nombre_proyecto}")


async def limpiar_contexto(chat_id: str):
    """Limpia el contexto del usuario (nuevo proyecto)"""
    _contextos[chat_id] = {
        "proyecto_activo": None,
        "ultimos_mensajes": [],
        "ultimo_output": None,
        "ultimo_bot_usado": None,
        "idioma": "es"
    }
    try:
        from memoria.redis import get_redis
        redis = await get_redis()
        if redis:
            await redis.delete(f"contexto:{chat_id}")
    except Exception:
        pass
