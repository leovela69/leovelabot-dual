"""Comandos de Telegram: /start, /help, /stats, /bots, etc."""

from loguru import logger
from telegram.handlers import enviar_mensaje


async def procesar_comando(chat_id: str, texto: str, user_name: str):
    """Procesa comandos /slash"""
    comando = texto.split()[0].lower().replace("@", "").split("@")[0]

    if comando == "/start":
        await cmd_start(chat_id, user_name)
    elif comando == "/help":
        await cmd_help(chat_id)
    elif comando == "/stats":
        await cmd_stats(chat_id)
    elif comando == "/bots":
        await cmd_bots(chat_id)
    elif comando == "/salud":
        await cmd_salud(chat_id)
    elif comando == "/proyecto":
        nombre = texto.replace("/proyecto", "").strip()
        await cmd_proyecto(chat_id, nombre)
    elif comando == "/proyectos":
        await cmd_proyectos(chat_id)
    elif comando == "/nuevo":
        await cmd_nuevo(chat_id)
    elif comando == "/entrenamiento":
        await cmd_entrenamiento(chat_id)
    elif comando == "/diagnostico":
        await cmd_diagnostico(chat_id)
    else:
        await enviar_mensaje(chat_id, f"Comando `{comando}` no reconocido. Usa /help.")


async def cmd_start(chat_id: str, user_name: str):
    await enviar_mensaje(chat_id, (
        f"🚀 *¡Hola {user_name}!*\n\n"
        "Soy *C8L Agent v15.4* — el sistema de IA de C8L Agency.\n\n"
        "Puedo crear:\n"
        "• 🌐 Webs, landing pages, apps\n"
        "• ⚙️ APIs, backends, bases de datos\n"
        "• 🎨 Imágenes, logos, diseños\n"
        "• 🎵 Música Bolero-House\n"
        "• 🎬 Videoclips y animaciones\n"
        "• 📝 Contenido, artículos, SEO\n"
        "• 🚀 Deploy automático en la nube\n\n"
        "Tengo *44 bots especializados* trabajando para ti.\n\n"
        "Escribe lo que necesitas o usa /help para ver comandos."
    ))


async def cmd_help(chat_id: str):
    await enviar_mensaje(chat_id, (
        "📋 *Comandos disponibles:*\n\n"
        "*Generales:*\n"
        "• /start — Bienvenida\n"
        "• /help — Esta ayuda\n"
        "• /stats — Estadísticas del sistema\n"
        "• /bots — Lista de bots activos\n"
        "• /salud — Estado de salud\n\n"
        "*Proyectos:*\n"
        "• /proyecto [nombre] — Activar proyecto\n"
        "• /proyectos — Ver mis proyectos\n"
        "• /nuevo — Proyecto limpio\n\n"
        "*Custodio (admin):*\n"
        "• /custodio estado — Estado web\n"
        "• /custodio musica — Generar Bolero-House\n"
        "• /custodio contenido — Pendientes\n"
        "• /custodio metricas — Métricas web\n"
        "• /custodio reparar — Diagnosticar\n"
        "• /custodio diagnosticar — Check profundo\n"
        "• /diagnostico — Diagnóstico sin tokens (admin)\n\n"
        "*O simplemente escribe lo que necesitas:*\n"
        "_'Hazme una landing de zapatos'_\n"
        "_'Crea una API REST con auth'_\n"
        "_'Genera un logo minimalista'_"
    ))


async def cmd_stats(chat_id: str):
    from bots.base import REGISTRY
    from memoria.supabase import obtener_metricas_sistema

    metricas = await obtener_metricas_sistema()
    activos = len([b for b in REGISTRY.values() if b.estado in ["activo", "elite"]])
    elites = len([b for b in REGISTRY.values() if b.estado == "elite"])

    await enviar_mensaje(chat_id, (
        "📊 *Estadísticas del sistema:*\n\n"
        f"🤖 Bots registrados: {len(REGISTRY)}\n"
        f"🟢 Activos: {activos}\n"
        f"👑 Elite: {elites}\n"
        f"📝 Tareas totales: {metricas.get('tareas_total', 0)}\n"
        f"💾 Bots en DB: {metricas.get('bots_total', 0)}\n"
    ))


async def cmd_bots(chat_id: str):
    from bots.base import REGISTRY

    lines = ["🤖 *Bots del sistema:*\n"]
    for bot in sorted(REGISTRY.values(), key=lambda b: b.score, reverse=True)[:20]:
        icon = "👑" if bot.estado == "elite" else "🟢" if bot.estado == "activo" else "💤"
        lines.append(f"{icon} `{bot.id}` — {bot.especialidad[:40]} (⭐{bot.score:.1f})")

    if len(REGISTRY) > 20:
        lines.append(f"\n... y {len(REGISTRY)-20} más")

    await enviar_mensaje(chat_id, "\n".join(lines))


async def cmd_salud(chat_id: str):
    from bots.despertador import bot_despertador
    resultado = await bot_despertador.ejecutar("health check", {})
    await enviar_mensaje(chat_id, resultado)


async def cmd_proyecto(chat_id: str, nombre: str):
    if not nombre:
        await enviar_mensaje(chat_id, "Usa: `/proyecto MiProyecto`")
        return
    from core.contexto import cambiar_proyecto
    await cambiar_proyecto(chat_id, nombre)
    await enviar_mensaje(chat_id, f"📁 Proyecto activo: *{nombre}*")


async def cmd_proyectos(chat_id: str):
    from memoria.proyectos import obtener_proyectos
    proyectos = await obtener_proyectos(chat_id)
    if not proyectos:
        await enviar_mensaje(chat_id, "📁 No tienes proyectos. Usa `/proyecto NombreNuevo`")
        return
    lines = ["📁 *Tus proyectos:*\n"]
    for p in proyectos[:10]:
        lines.append(f"• {p['nombre']} (v{p.get('version_actual', 1)})")
    await enviar_mensaje(chat_id, "\n".join(lines))


async def cmd_nuevo(chat_id: str):
    from core.contexto import limpiar_contexto
    await limpiar_contexto(chat_id)
    await enviar_mensaje(chat_id, "🆕 Contexto limpio. Listo para un nuevo proyecto.")


async def cmd_entrenamiento(chat_id: str):
    from bots.fantasma import bot_fantasma
    reporte = bot_fantasma.generar_reporte_entrenamiento()
    await enviar_mensaje(chat_id, reporte)


async def cmd_diagnostico(chat_id: str):
    import config
    if not config.ADMIN_TELEGRAM_ID or str(chat_id) != str(config.ADMIN_TELEGRAM_ID):
        await enviar_mensaje(chat_id, "⛔ Comando solo para administradores.")
        return

    from scripts.diagnostico_sin_tokens import diagnosticar_sistema
    resultado = diagnosticar_sistema()
    # Puesto que es markdown, envolvemos en un bloque de código para que se lea alineado
    await enviar_mensaje(chat_id, f"📋 *Resultado del diagnóstico:*\n```text\n{resultado}\n```")
