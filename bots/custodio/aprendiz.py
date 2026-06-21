"""Custodio Aprendiz: Memoria evolutiva, aprende de cada acción."""

from loguru import logger


async def ciclo_aprendiz():
    """Ciclo diario (3am): aprende, optimiza, limpia"""
    logger.info("🧠 Aprendiz: ciclo de aprendizaje nocturno...")

    await _refrescar_conocimiento()
    await _autoevaluar_prompts()
    await _limpiar_logs_antiguos()

    logger.info("🧠 Aprendiz: ciclo completado")


async def obtener_historial() -> str:
    """Muestra últimas 10 acciones del Custodio"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return "❌ Sin conexión."

        result = client.table("web_audits").select("*").order(
            "created_at", desc=True
        ).limit(10).execute()

        if not result.data:
            return "📋 Sin historial de acciones aún."

        lines = ["📋 *Últimas acciones del Custodio:*\n"]
        for a in result.data:
            lines.append(f"• [{a['tipo']}] {a.get('created_at', '')[:16]}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"


async def optimizar_prompt(prompt_id: str) -> str:
    """Optimiza un prompt de música o contenido"""
    if not prompt_id:
        return "Especifica el ID del prompt a optimizar."

    try:
        from ejecutores.caliente import llamar_gemini_pro

        resultado = await llamar_gemini_pro(
            f"Optimiza este prompt para generar mejor música Bolero-House. "
            f"Hazlo más específico, con mejores descriptores de audio. "
            f"ID original: {prompt_id}"
        )

        return f"🧠 Prompt optimizado:\n\n{resultado[:1500]}"
    except Exception as e:
        return f"Error optimizando: {str(e)}"


async def _refrescar_conocimiento():
    """Actualiza embeddings y conocimiento"""
    logger.debug("Refrescando conocimiento...")


async def _autoevaluar_prompts():
    """Evalúa prompts de música por rendimiento"""
    logger.debug("Autoevaluando prompts...")


async def _limpiar_logs_antiguos():
    """Limpia logs de más de 30 días"""
    try:
        from memoria.supabase import get_client
        from datetime import datetime, timedelta

        client = await get_client()
        if not client:
            return

        fecha_limite = (datetime.now() - timedelta(days=30)).isoformat()
        client.table("web_audits").delete().lt("created_at", fecha_limite).execute()
        logger.info("🧹 Logs antiguos limpiados")
    except Exception as e:
        logger.debug(f"Error limpiando logs: {e}")
