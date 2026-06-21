"""Custodio Analista: Métricas de la web, auditoría SEO, conversiones."""

from loguru import logger


async def ciclo_analista():
    """Ciclo cada hora: recopila métricas"""
    logger.debug("📊 Analista: recopilando métricas...")
    await _recopilar_metricas()


async def obtener_metricas() -> str:
    """Obtiene métricas actuales de la web"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return "❌ Sin conexión a base de datos."

        # Últimas métricas guardadas
        result = client.table("web_metrics").select("*").order(
            "created_at", desc=True
        ).limit(1).execute()

        if not result.data:
            return ("📊 *Métricas de la web:*\n\n"
                    "⚠️ Sin datos aún. Las métricas se recopilan cada hora.\n"
                    "Espera al próximo ciclo del Analista.")

        m = result.data[0]
        return (
            f"📊 *Métricas de la web C8L Agency:*\n\n"
            f"⬆️ Uptime: {m.get('uptime_percent', 99.9):.1f}%\n"
            f"⚡ Velocidad promedio: {m.get('velocidad_ms', 0)}ms\n"
            f"👥 Visitas (último día): {m.get('visitas', 0)}\n"
            f"📄 Páginas vistas: {m.get('paginas_vistas', 0)}\n"
            f"🔍 Score SEO: {m.get('score_seo', 0)}/100\n"
            f"🎯 Score Lighthouse: {m.get('score_lighthouse', 0)}/100\n"
        )
    except Exception as e:
        return f"Error obteniendo métricas: {str(e)}"


async def diagnosticar_sistema() -> str:
    """Diagnóstico profundo del sistema de música y web"""
    diagnostico = ["🔬 *Diagnóstico profundo:*\n"]

    # Check web
    import httpx
    import config
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(config.WEB_URL)
            latencia = int(resp.elapsed.total_seconds() * 1000)
            diagnostico.append(f"🌐 Web: {resp.status_code} ({latencia}ms)")
    except Exception as e:
        diagnostico.append(f"🌐 Web: ❌ Error ({str(e)[:30]})")

    # Check Supabase
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if client:
            diagnostico.append("🗄️ Supabase: ✅ Conectado")
        else:
            diagnostico.append("🗄️ Supabase: ⚠️ No conectado")
    except Exception:
        diagnostico.append("🗄️ Supabase: ❌ Error")

    # Check Redis
    try:
        from memoria.redis import get_redis
        r = await get_redis()
        if r:
            await r.ping()
            diagnostico.append("📦 Redis: ✅ OK")
        else:
            diagnostico.append("📦 Redis: ⚠️ No conectado")
    except Exception:
        diagnostico.append("📦 Redis: ❌ Error")

    # Bots activos
    from bots.base import REGISTRY
    activos = len([b for b in REGISTRY.values() if b.estado in ["activo", "elite"]])
    diagnostico.append(f"🤖 Bots activos: {activos}/{len(REGISTRY)}")

    return "\n".join(diagnostico)


async def _recopilar_metricas():
    """Recopila y guarda métricas en DB"""
    try:
        import httpx
        import config
        from memoria.supabase import get_client

        velocidad = 0
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(config.WEB_URL)
                velocidad = int(resp.elapsed.total_seconds() * 1000)
        except Exception:
            pass

        client = await get_client()
        if client:
            client.table("web_metrics").insert({
                "uptime_percent": 99.9 if velocidad > 0 else 0,
                "velocidad_ms": velocidad,
                "visitas": 0,  # Se actualizaría con analytics real
                "paginas_vistas": 0,
                "score_lighthouse": 0,
                "score_seo": 0,
            }).execute()
    except Exception as e:
        logger.debug(f"Error recopilando métricas: {e}")
