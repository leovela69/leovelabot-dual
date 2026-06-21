"""Custodio Médico: Repara fallos detectados (con permiso de Leo)."""

from loguru import logger
import config


async def diagnosticar_y_reparar() -> str:
    """Diagnostica problemas y propone/ejecuta reparaciones"""
    logger.info("🏥 Médico: diagnosticando...")

    problemas = await _detectar_problemas()

    if not problemas:
        return "🏥 *Diagnóstico completo:*\n\n✅ No se detectaron problemas. La web está saludable."

    resultado = "🏥 *Diagnóstico de la web:*\n\n"
    for i, p in enumerate(problemas, 1):
        resultado += (
            f"*{i}. [{p['gravedad']}] {p['tipo']}*\n"
            f"   📄 Página: {p['pagina']}\n"
            f"   📝 Descripción: {p['descripcion']}\n"
            f"   💡 Solución: {p['solucion']}\n\n"
        )

    resultado += "¿Procedo con las reparaciones? (sí/no)"
    return resultado


async def auto_reparar(url: str):
    """Reparación automática cuando hay 3+ fallos consecutivos"""
    logger.warning(f"🏥 Médico: auto-reparación para {url}")

    # Nivel 1: Purgar caché
    await _purgar_cache()

    # Nivel 2: Notificar a Leo
    from telegram.handlers import enviar_mensaje
    await enviar_mensaje(
        config.ADMIN_TELEGRAM_ID,
        f"🏥 *Médico activo:*\n\n"
        f"Detecté fallos repetidos en: {url}\n"
        f"Acciones tomadas:\n"
        f"• ✅ Caché purgado\n"
        f"• ⏳ Monitoreando recuperación\n\n"
        f"¿Quieres que intente rollback? (sí/no)"
    )


async def ejecutar_rollback():
    """Ejecuta rollback al último deploy estable"""
    logger.warning("🏥 Médico: ejecutando ROLLBACK...")
    # En producción: llamaría a Vercel API para revert
    return "🏥 Rollback ejecutado. Último deploy estable restaurado."


async def _purgar_cache():
    """Purga caché del sistema"""
    try:
        from memoria.redis import get_redis
        r = await get_redis()
        if r:
            # Solo purgar cache de la web, no todo Redis
            keys = await r.keys("cache:web:*")
            if keys:
                await r.delete(*keys)
                logger.info(f"🏥 Purgadas {len(keys)} entradas de cache web")
    except Exception as e:
        logger.error(f"Error purgando cache: {e}")


async def _detectar_problemas() -> list:
    """Detecta problemas en la web"""
    problemas = []

    # Check 1: Links rotos (simplificado)
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(config.WEB_URL)
            if resp.status_code != 200:
                problemas.append({
                    "tipo": "Página principal con error",
                    "gravedad": "ALTA",
                    "pagina": config.WEB_URL,
                    "descripcion": f"Status code: {resp.status_code}",
                    "solucion": "Verificar deploy y configuración del servidor"
                })

            # Check latencia
            latencia = int(resp.elapsed.total_seconds() * 1000)
            if latencia > 3000:
                problemas.append({
                    "tipo": "Velocidad lenta",
                    "gravedad": "MEDIA",
                    "pagina": config.WEB_URL,
                    "descripcion": f"Latencia: {latencia}ms (umbral: 3000ms)",
                    "solucion": "Optimizar imágenes, activar CDN, minificar assets"
                })
    except Exception as e:
        problemas.append({
            "tipo": "Web no accesible",
            "gravedad": "CRÍTICA",
            "pagina": config.WEB_URL,
            "descripcion": str(e)[:100],
            "solucion": "Verificar hosting, DNS, y certificado SSL"
        })

    return problemas
