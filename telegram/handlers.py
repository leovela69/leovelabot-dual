"""Handlers de Telegram: Envío de mensajes."""

from loguru import logger
import httpx
import config


async def enviar_mensaje(chat_id: str, texto: str):
    """Envía un mensaje de texto por Telegram"""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("Sin token de Telegram configurado")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram tiene límite de 4096 chars
    if len(texto) > 4096:
        # Dividir en partes
        partes = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
        for parte in partes:
            await _enviar(url, chat_id, parte)
    else:
        await _enviar(url, chat_id, texto)


async def enviar_progreso(chat_id: str, texto: str):
    """Envía mensaje de progreso (no espera respuesta)"""
    await enviar_mensaje(chat_id, texto)


async def _enviar(url: str, chat_id: str, texto: str):
    """Envía un mensaje individual"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": texto,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
    except Exception as e:
        # Reintentar sin Markdown si falla
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json={
                    "chat_id": chat_id,
                    "text": texto,
                })
        except Exception as e2:
            logger.error(f"Error enviando mensaje: {e2}")
