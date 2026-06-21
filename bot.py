"""C8L AGENT v15.4 — CUSTODIO DEFINITIVO
Entry point principal: FastAPI + Webhook Telegram + Scheduler
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from core.gateway import procesar_mensaje
from core.guardian import verificar_etica
from core.reflejo import buscar_en_cache
from core.contexto import cargar_contexto
from bots.custodio.vigia import ciclo_vigia
from bots.custodio.analista import ciclo_analista
from bots.custodio.creador import ciclo_creador
from bots.custodio.aprendiz import ciclo_aprendiz

# Configurar logger
logger.add("logs/c8l_agent.log", rotation="10 MB", level=config.LOG_LEVEL)

# Scheduler para ciclos automaticos del Custodio
scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa y cierra recursos del sistema"""
    logger.info("🚀 C8L AGENT v15.4 CUSTODIO DEFINITIVO iniciando...")

    # Programar ciclos del Custodio
    scheduler.add_job(ciclo_vigia, "interval", minutes=config.PING_INTERVAL_MINUTES, id="vigia")
    scheduler.add_job(ciclo_analista, "interval", hours=1, id="analista")
    scheduler.add_job(ciclo_creador, "interval", hours=config.AUDIT_INTERVAL_HOURS, id="creador")
    scheduler.add_job(ciclo_aprendiz, "cron", hour=3, id="aprendiz")  # 3am cada dia

    scheduler.start()
    logger.info("⏰ Scheduler iniciado con ciclos del Custodio")

    yield

    # Cleanup
    scheduler.shutdown()
    logger.info("🛑 C8L AGENT apagado correctamente")


app = FastAPI(
    title="C8L AGENT v15.4",
    description="Sistema de agentes de IA autonomo para C8L Agency",
    version="15.4",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Endpoint de salud para Railway y Bot Despertador"""
    return {"status": "alive", "version": "15.4", "name": "CUSTODIO DEFINITIVO"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Recibe mensajes de Telegram y los procesa"""
    try:
        data = await request.json()
        logger.debug(f"Webhook recibido: {data}")

        # Extraer mensaje
        message = data.get("message", {})
        if not message:
            return JSONResponse({"ok": True})

        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        user_name = message.get("from", {}).get("first_name", "Usuario")

        if not text or not chat_id:
            return JSONResponse({"ok": True})

        # Sanitizar input
        if len(text) > config.MAX_MESSAGE_LENGTH:
            text = text[:config.MAX_MESSAGE_LENGTH]

        # CAPA 0: Guardian etico (verifica ANTES de procesar)
        es_seguro, motivo = await verificar_etica(text, chat_id)
        if not es_seguro:
            from telegram.handlers import enviar_mensaje
            await enviar_mensaje(chat_id, f"🚫 No puedo hacer eso: {motivo}")
            logger.warning(f"Orden bloqueada de {chat_id}: {motivo}")
            return JSONResponse({"ok": True})

        # CAPA 1: Reflejo (busca en cache primero)
        respuesta_cache = await buscar_en_cache(text, chat_id)
        if respuesta_cache:
            from telegram.handlers import enviar_mensaje
            await enviar_mensaje(chat_id, respuesta_cache)
            return JSONResponse({"ok": True})

        # CAPA 1.5: Cargar contexto del hilo activo
        contexto = await cargar_contexto(chat_id)

        # CAPA 2+: Procesar con el sistema completo
        await procesar_mensaje(chat_id, text, user_name, contexto)

        return JSONResponse({"ok": True})

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return JSONResponse({"ok": True})


@app.get("/")
async def root():
    """Pagina principal"""
    return {
        "nombre": "C8L AGENT v15.4 — CUSTODIO DEFINITIVO",
        "estado": "activo",
        "bots_registrados": 44,
        "creador": "Leo Vela — C8L Agency"
    }
