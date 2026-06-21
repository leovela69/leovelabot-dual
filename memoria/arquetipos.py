"""Arquetipos: Compresión de tareas similares (10:1).
100 tareas de 'landing page' → 1 arquetipo con lo mejor."""

from loguru import logger
from typing import Optional, Dict


async def buscar_arquetipo(keywords: list) -> Optional[Dict]:
    """Busca un arquetipo que matchee las keywords"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return None

        # Buscar arquetipos por categoría
        for kw in keywords[:3]:
            result = client.table("arquetipos").select("*").ilike(
                "categoria", f"%{kw}%"
            ).order("score_promedio", desc=True).limit(1).execute()

            if result.data:
                arquetipo = result.data[0]
                # Incrementar uso
                client.table("arquetipos").update({
                    "veces_usado": arquetipo["veces_usado"] + 1
                }).eq("id", arquetipo["id"]).execute()
                return arquetipo

        return None
    except Exception as e:
        logger.error(f"Error buscando arquetipo: {e}")
        return None


async def crear_arquetipo(nombre: str, categoria: str, best_output: str, score: float):
    """Crea un nuevo arquetipo desde tareas exitosas"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return

        client.table("arquetipos").insert({
            "nombre": nombre,
            "categoria": categoria,
            "best_output": best_output[:5000],
            "score_promedio": score,
            "veces_usado": 1,
            "source_count": 1,
        }).execute()
        logger.info(f"📦 Arquetipo creado: {nombre}")
    except Exception as e:
        logger.error(f"Error creando arquetipo: {e}")


async def comprimir_tareas_en_arquetipos():
    """Comprime tareas similares en arquetipos (modo sueño)"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return

        # Buscar tareas con calidad alta no comprimidas
        result = client.table("tareas").select("*").gte(
            "calidad", 80
        ).limit(100).execute()

        if not result.data or len(result.data) < 10:
            return

        # TODO: Agrupar por similitud y crear arquetipos
        logger.debug(f"Compresión: {len(result.data)} tareas candidatas")
    except Exception as e:
        logger.error(f"Error en compresión: {e}")
