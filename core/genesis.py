"""Genesis: El Creador de Bots.
Busca el bot adecuado o CREA uno nuevo si no existe."""

from loguru import logger
from typing import Dict, Any, Optional


async def buscar_o_crear_bot(clasificacion: Dict[str, Any], contexto: Dict[str, Any]) -> Optional[Any]:
    """Busca en el Registry un bot para la tarea. Si no existe, lo crea."""
    from bots.base import BotBase

    keywords = clasificacion.get("keywords", [])
    tipo = clasificacion.get("tipo", "crear")

    # 1. Buscar en Registry por keywords y tipo
    bot = await buscar_en_registry(keywords, tipo)
    if bot:
        logger.info(f"Genesis: asignó bot existente '{bot.id}'")
        return bot

    # 2. Si no hay match directo, buscar similar (>60%)
    bot_similar = await buscar_similar(keywords)
    if bot_similar:
        logger.info(f"Genesis: usando bot similar '{bot_similar.id}'")
        return bot_similar

    # 3. Si no hay nada → CREAR bot nuevo
    logger.info(f"Genesis: creando bot nuevo para keywords={keywords}")
    nuevo_bot = await crear_bot_nuevo(keywords, tipo, clasificacion)
    return nuevo_bot


async def buscar_en_registry(keywords: list, tipo: str) -> Optional[Any]:
    """Busca bot en el Registry por keywords y tipo"""
    from bots.base import REGISTRY

    mejor_match = None
    mejor_score = 0

    for bot_id, bot in REGISTRY.items():
        if bot.estado not in ["activo", "elite"]:
            continue

        # Calcular match por keywords
        bot_keywords = set(bot.keywords)
        input_keywords = set(keywords)
        coincidencias = len(bot_keywords & input_keywords)

        if coincidencias > mejor_score:
            mejor_score = coincidencias
            mejor_match = bot

    if mejor_score >= 2:
        return mejor_match
    return None


async def buscar_similar(keywords: list) -> Optional[Any]:
    """Busca bot con especialidad similar usando lógica simple"""
    from bots.base import REGISTRY

    tipo_mapping = {
        "html": "bot_frontend",
        "css": "bot_css",
        "tailwind": "bot_frontend",
        "react": "bot_react",
        "vue": "bot_vue",
        "next": "bot_nextjs",
        "python": "bot_backend_python",
        "api": "bot_backend_python",
        "node": "bot_backend_node",
        "sql": "bot_sql",
        "base de datos": "bot_sql",
        "imagen": "bot_images",
        "foto": "bot_images",
        "logo": "bot_images",
        "música": "bot_custodio_creador",
        "canción": "bot_custodio_creador",
        "bolero": "bot_custodio_creador",
        "video": "bot_videoclip",
        "deploy": "bot_deployer",
        "publica": "bot_deployer",
        "seo": "bot_seo",
        "texto": "bot_copywriting",
        "artículo": "bot_copywriting",
    }

    for kw in keywords:
        for pattern, bot_id in tipo_mapping.items():
            if pattern in kw:
                if bot_id in REGISTRY:
                    return REGISTRY[bot_id]

    return None


async def crear_bot_nuevo(keywords: list, tipo: str, clasificacion: Dict) -> Optional[Any]:
    """Crea un bot nuevo usando Genesis (Gemini Pro)"""
    from bots.base import BotBase, REGISTRY

    # Generar nombre basado en keywords
    nombre = f"bot_{'_'.join(keywords[:2])}" if keywords else f"bot_generico_{tipo}"
    nombre = nombre.replace(" ", "_").lower()[:30]

    # Si ya existe con ese nombre, usarlo
    if nombre in REGISTRY:
        return REGISTRY[nombre]

    # Crear bot nuevo con prompt genérico
    especialidad = " + ".join(keywords[:3]) if keywords else tipo
    prompt = f"Eres un experto en {especialidad}. Genera código/contenido de alta calidad. Solo output, sin explicaciones."

    nuevo_bot = BotBase(
        id=nombre,
        nombre=nombre.replace("_", " ").title(),
        especialidad=especialidad,
        keywords=keywords,
        prompt_compiled=prompt,
        modelo="groq",
        estado="novato"
    )

    # Registrar
    REGISTRY[nombre] = nuevo_bot
    logger.info(f"🆕 Genesis creó nuevo bot: {nombre} ({especialidad})")

    # Guardar en DB (async)
    try:
        from memoria.supabase import registrar_bot
        await registrar_bot(nuevo_bot)
    except Exception as e:
        logger.error(f"Error registrando bot en DB: {e}")

    return nuevo_bot


async def registrar_bot_genesis(bot) -> bool:
    """Registra un bot creado por la Fábrica en el sistema.
    Usado por bots/fabrica.py cuando crea bots nuevos."""
    from bots.base import REGISTRY

    try:
        # Registrar en memoria
        REGISTRY[bot.id] = bot
        logger.info(f"🏭 Bot registrado vía Genesis: {bot.id}")

        # Persistir en Supabase
        from memoria.supabase import registrar_bot
        await registrar_bot(bot)
        return True
    except Exception as e:
        logger.error(f"Error en registrar_bot_genesis: {e}")
        return False
