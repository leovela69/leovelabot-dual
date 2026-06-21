"""Custodio Notificador: Envía reportes y alertas a Leo Vela."""

from loguru import logger
import config


async def reporte_diario():
    """Genera y envía reporte diario (8am)"""
    from bots.custodio.vigia import obtener_estado_web
    from bots.custodio.analista import obtener_metricas

    estado = await obtener_estado_web()
    metricas = await obtener_metricas()

    reporte = (
        f"☀️ *Reporte Diario C8L Agency*\n"
        f"{'='*30}\n\n"
        f"{estado}\n\n"
        f"{metricas}\n\n"
        f"💡 Usa `/custodio contenido` para ver pendientes."
    )

    from telegram.handlers import enviar_mensaje
    await enviar_mensaje(config.ADMIN_TELEGRAM_ID, reporte)
    logger.info("📊 Reporte diario enviado a Leo")


async def alerta_urgente(mensaje: str):
    """Envía alerta urgente inmediata"""
    from telegram.handlers import enviar_mensaje
    await enviar_mensaje(config.ADMIN_TELEGRAM_ID, f"🚨 *ALERTA URGENTE:*\n\n{mensaje}")
