"""Gateway: Procesa mensajes y los rutea al bot correcto"""

from loguru import logger
from typing import Dict, Any

import config
from core.genesis import buscar_o_crear_bot
from core.contexto import actualizar_contexto
from telegram.handlers import enviar_mensaje, enviar_progreso


async def procesar_mensaje(chat_id: str, texto: str, user_name: str, contexto: Dict[str, Any]):
    """Punto central de procesamiento. Clasifica y rutea al bot correcto."""
    logger.info(f"Procesando mensaje de {user_name} ({chat_id}): {texto[:50]}...")

    # Verificar si es comando del custodio
    if texto.startswith("/custodio"):
        from bots.custodio.main import procesar_comando_custodio
        await procesar_comando_custodio(chat_id, texto)
        return

    # Verificar si es comando general
    if texto.startswith("/"):
        from telegram.comandos import procesar_comando
        await procesar_comando(chat_id, texto, user_name)
        return

    # Clasificar la tarea
    clasificacion = clasificar_tarea(texto, contexto)
    logger.debug(f"Clasificación: {clasificacion}")

    # Enviar progreso al usuario
    await enviar_progreso(chat_id, "⚡ Entendido. Trabajando...")

    # Buscar o crear bot para la tarea
    bot = await buscar_o_crear_bot(clasificacion, contexto)

    if not bot:
        await enviar_mensaje(chat_id, "❌ No pude encontrar ni crear un bot para esta tarea. Intenta reformular tu pedido.")
        return

    # Ejecutar tarea con el bot asignado
    try:
        resultado = await bot.ejecutar(texto, contexto)

        # Validar resultado con el Juez
        from core.juez import evaluar_resultado
        score = await evaluar_resultado(resultado, clasificacion)

        if score >= 70:
            # Actualizar contexto del hilo
            await actualizar_contexto(chat_id, texto, resultado)
            # Entregar al usuario
            from salida.formato import formatear_respuesta
            respuesta = await formatear_respuesta(resultado, chat_id)
            await enviar_mensaje(chat_id, respuesta)
        elif score >= 50:
            # Reintentar una vez
            logger.warning(f"Score {score}, reintentando...")
            resultado = await bot.ejecutar(texto, contexto, retry=True)
            await actualizar_contexto(chat_id, texto, resultado)
            from salida.formato import formatear_respuesta
            respuesta = await formatear_respuesta(resultado, chat_id)
            await enviar_mensaje(chat_id, f"⚠️ Resultado con advertencias:\n\n{respuesta}")
        else:
            await enviar_mensaje(chat_id, "❌ No logré generar un resultado de calidad. ¿Puedes dar más detalles?")

        # Guardar en memoria (async, no bloquea)
        from memoria.supabase import guardar_tarea
        await guardar_tarea(chat_id, texto, resultado, score, bot.id)

    except Exception as e:
        logger.error(f"Error ejecutando bot {bot.id}: {e}")
        await enviar_mensaje(chat_id, f"⚠️ Ocurrió un error. Lo registré para mejorar. Intenta de nuevo.")


def clasificar_tarea(texto: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
    """Clasifica la tarea usando heurísticas (0 tokens de IA)"""
    texto_lower = texto.lower()

    # Detectar tipo
    tipo = "crear"
    if any(p in texto_lower for p in ["cambia", "modifica", "arregla", "corrige", "actualiza"]):
        tipo = "modificar"
    elif any(p in texto_lower for p in ["otra vez", "repite", "igual que", "como el"]):
        tipo = "repetir"
    elif any(p in texto_lower for p in ["qué es", "explica", "dime", "cómo funciona", "busca"]):
        tipo = "consultar"
    elif any(p in texto_lower for p in ["y luego", "después", "y también", "primero", "segundo"]):
        tipo = "encadenar"
    elif any(p in texto_lower for p in ["publica", "despliega", "sube", "deploy"]):
        tipo = "desplegar"
    elif any(p in texto_lower for p in ["imagen", "foto", "logo", "diseño visual"]):
        tipo = "media"
    elif any(p in texto_lower for p in ["canción", "música", "bolero", "audio"]):
        tipo = "musica"

    # Detectar complejidad
    verbos_accion = sum(1 for p in ["crea", "hazme", "genera", "construye", "diseña", "programa"]
                        if p in texto_lower)
    complejidad = "baja"
    if verbos_accion >= 3 or len(texto.split()) > 30:
        complejidad = "alta"
    elif verbos_accion >= 2 or len(texto.split()) > 15:
        complejidad = "media"

    # Detectar urgencia
    urgencia = "normal"
    if any(p in texto_lower for p in ["urgente", "rápido", "ya", "apúrate"]):
        urgencia = "rapido"

    # Detectar si es continuación del hilo
    es_continuacion = False
    if contexto.get("proyecto_activo"):
        if any(p in texto_lower for p in ["agrégale", "ponle", "cámbialo", "eso", "así", "más"]):
            es_continuacion = True

    # Keywords para buscar bot especializado
    keywords = [w for w in texto_lower.split() if len(w) > 3 and w not in
                ["hazme", "crear", "quiero", "necesito", "para", "como", "algo", "esto"]]

    return {
        "tipo": tipo,
        "complejidad": complejidad,
        "urgencia": urgencia,
        "es_continuacion": es_continuacion,
        "keywords": keywords[:10],
        "texto_original": texto
    }
