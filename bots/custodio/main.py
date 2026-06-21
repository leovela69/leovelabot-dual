"""Custodio Main: Orquestador de comandos /custodio."""

from loguru import logger
from telegram.handlers import enviar_mensaje
import config


async def procesar_comando_custodio(chat_id: str, texto: str):
    """Procesa comandos /custodio [subcomando]"""

    # Solo el admin puede usar comandos del custodio
    if chat_id != config.ADMIN_TELEGRAM_ID:
        await enviar_mensaje(chat_id, "🚫 Solo Leo Vela puede usar los comandos del Custodio.")
        return

    partes = texto.split(maxsplit=2)
    subcomando = partes[1] if len(partes) > 1 else "estado"
    argumento = partes[2] if len(partes) > 2 else ""

    logger.info(f"🏢 Custodio: comando '{subcomando}' de {chat_id}")

    if subcomando == "estado":
        from bots.custodio.vigia import obtener_estado_web
        resultado = await obtener_estado_web()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "reparar":
        from bots.custodio.medico import diagnosticar_y_reparar
        resultado = await diagnosticar_y_reparar()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "contenido":
        from bots.custodio.creador import listar_contenido_pendiente
        resultado = await listar_contenido_pendiente()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "musica":
        from bots.custodio.creador import generar_musica_bundle
        resultado = await generar_musica_bundle()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "publicar":
        from bots.custodio.creador import publicar_contenido
        resultado = await publicar_contenido(argumento)
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "metricas":
        from bots.custodio.analista import obtener_metricas
        resultado = await obtener_metricas()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "diagnosticar":
        from bots.custodio.analista import diagnosticar_sistema
        resultado = await diagnosticar_sistema()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "modo":
        modo = argumento.lower() if argumento else "manual"
        resultado = f"⚙️ Custodio cambiado a modo: *{modo}*"
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "historial":
        from bots.custodio.aprendiz import obtener_historial
        resultado = await obtener_historial()
        await enviar_mensaje(chat_id, resultado)

    elif subcomando == "optimizar":
        from bots.custodio.aprendiz import optimizar_prompt
        resultado = await optimizar_prompt(argumento)
        await enviar_mensaje(chat_id, resultado)

    else:
        ayuda = (
            "🏢 *Comandos del Custodio:*\n\n"
            "• `/custodio estado` — Estado de la web\n"
            "• `/custodio reparar` — Diagnosticar y reparar fallos\n"
            "• `/custodio contenido` — Contenido pendiente\n"
            "• `/custodio musica` — Generar bundle Bolero-House\n"
            "• `/custodio publicar [id]` — Publicar contenido\n"
            "• `/custodio metricas` — Métricas de la web\n"
            "• `/custodio diagnosticar` — Diagnóstico profundo\n"
            "• `/custodio modo auto|manual` — Cambiar modo\n"
            "• `/custodio historial` — Últimas acciones\n"
            "• `/custodio optimizar [id]` — Optimizar prompt"
        )
        await enviar_mensaje(chat_id, ayuda)
