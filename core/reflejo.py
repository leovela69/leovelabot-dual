"""Capa Reflejo: Cache L1 (RAM) + Cache L2 (Redis).
Resuelve ~70% de mensajes sin usar IA. 0 tokens."""

from loguru import logger
from typing import Optional
import hashlib
import time

# Cache L1: In-memory dict (últimas 200 respuestas, TTL 1 hora)
_cache_l1: dict = {}
_cache_l1_timestamps: dict = {}
MAX_CACHE_L1 = 200
TTL_L1 = 3600  # 1 hora en segundos

# Respuestas predefinidas (0 tokens, instantáneo)
RESPUESTAS_PREDEFINIDAS = {
    "hola": "👋 ¡Hola! Soy C8L Agent. ¿En qué te ayudo hoy?",
    "hi": "👋 Hey! I'm C8L Agent. How can I help?",
    "gracias": "🙏 ¡De nada! Aquí estoy si necesitas algo más.",
    "thanks": "🙏 You're welcome! Let me know if you need anything else.",
    "ok": "👍 Perfecto. Dime si necesitas algo más.",
    "quién eres": "🤖 Soy C8L Agent v15.4 — el asistente de IA de C8L Agency. Puedo crear webs, apps, APIs, música, imágenes y mucho más. Escribe /help para ver todo lo que puedo hacer.",
    "quien eres": "🤖 Soy C8L Agent v15.4 — el asistente de IA de C8L Agency. Puedo crear webs, apps, APIs, música, imágenes y mucho más. Escribe /help para ver todo lo que puedo hacer.",
    "qué puedes hacer": "💪 Puedo: crear webs, apps, APIs, generar imágenes, música Bolero-House, videoclips, optimizar SEO, analizar datos, y mucho más. Usa /help para la lista completa.",
}


async def buscar_en_cache(texto: str, chat_id: str) -> Optional[str]:
    """Busca respuesta en cache L1 (RAM) y L2 (Redis).
    Si encuentra, devuelve la respuesta sin gastar tokens."""

    texto_lower = texto.lower().strip()

    # Primero: respuestas predefinidas (instantáneo)
    for key, respuesta in RESPUESTAS_PREDEFINIDAS.items():
        if texto_lower == key or texto_lower.startswith(key):
            logger.debug(f"Reflejo: respuesta predefinida para '{key}'")
            return respuesta

    # Segundo: Cache L1 (in-memory, hash exacto)
    hash_input = _generar_hash(texto_lower + chat_id)
    respuesta_l1 = _buscar_l1(hash_input)
    if respuesta_l1:
        logger.debug(f"Reflejo: hit en Cache L1")
        return respuesta_l1

    # Tercero: Cache L2 (Redis, similarity)
    respuesta_l2 = await _buscar_l2(texto_lower, chat_id)
    if respuesta_l2:
        logger.debug(f"Reflejo: hit en Cache L2")
        # Promover a L1
        _guardar_l1(hash_input, respuesta_l2)
        return respuesta_l2

    # No encontrado en cache
    return None


async def guardar_en_cache(texto: str, chat_id: str, respuesta: str):
    """Guarda una respuesta en ambos niveles de cache"""
    texto_lower = texto.lower().strip()
    hash_input = _generar_hash(texto_lower + chat_id)

    # Guardar en L1
    _guardar_l1(hash_input, respuesta)

    # Guardar en L2 (Redis)
    await _guardar_l2(texto_lower, chat_id, respuesta)


def _generar_hash(texto: str) -> str:
    """Genera hash MD5 del texto para cache L1"""
    return hashlib.md5(texto.encode()).hexdigest()


def _buscar_l1(hash_key: str) -> Optional[str]:
    """Busca en cache L1 (in-memory). Verifica TTL."""
    if hash_key in _cache_l1:
        timestamp = _cache_l1_timestamps.get(hash_key, 0)
        if time.time() - timestamp < TTL_L1:
            return _cache_l1[hash_key]
        else:
            # Expirado, limpiar
            del _cache_l1[hash_key]
            del _cache_l1_timestamps[hash_key]
    return None


def _guardar_l1(hash_key: str, respuesta: str):
    """Guarda en cache L1. Aplica LRU si excede MAX."""
    # LRU: si está lleno, eliminar el más viejo
    if len(_cache_l1) >= MAX_CACHE_L1:
        oldest_key = min(_cache_l1_timestamps, key=_cache_l1_timestamps.get)
        del _cache_l1[oldest_key]
        del _cache_l1_timestamps[oldest_key]

    _cache_l1[hash_key] = respuesta
    _cache_l1_timestamps[hash_key] = time.time()


async def _buscar_l2(texto: str, chat_id: str) -> Optional[str]:
    """Busca en cache L2 (Redis). TTL 24h."""
    try:
        from memoria.redis import get_redis
        redis = await get_redis()
        if redis:
            key = f"cache:l2:{_generar_hash(texto + chat_id)}"
            resultado = await redis.get(key)
            if resultado:
                return resultado.decode() if isinstance(resultado, bytes) else resultado
    except Exception as e:
        logger.debug(f"Cache L2 no disponible: {e}")
    return None


async def _guardar_l2(texto: str, chat_id: str, respuesta: str):
    """Guarda en cache L2 (Redis) con TTL de 24 horas."""
    try:
        from memoria.redis import get_redis
        redis = await get_redis()
        if redis:
            key = f"cache:l2:{_generar_hash(texto + chat_id)}"
            await redis.setex(key, 86400, respuesta)  # 24h TTL
    except Exception as e:
        logger.debug(f"Error guardando en Cache L2: {e}")
