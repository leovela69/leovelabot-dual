# -*- coding: utf-8 -*-
"""
🔧 Model Manager — Auto-reparación de modelos Gemini.

Cuando un modelo devuelve 404 (deprecado), automáticamente cambia al siguiente
modelo disponible de la lista de fallback. El bot NUNCA se queda muerto.
"""

import logging
import time
from google import genai
from google.genai import types

logger = logging.getLogger("leovelabot.model_manager")

# ---------------------------------------------------------------------------
# Fallback lists — ordenadas de más nueva a más vieja
# Si Google apaga un modelo, el siguiente de la lista toma su lugar
# ---------------------------------------------------------------------------
CHAT_FALLBACKS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

IMAGE_FALLBACKS = [
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-preview-image-generation",
]

# Modelos que ya sabemos que están muertos (se llena dinámicamente)
_dead_models: set = set()


def get_working_model(preferred: str, category: str = "chat") -> str:
    """
    Retorna el modelo preferido si no está muerto, o el siguiente fallback.
    """
    if preferred not in _dead_models:
        return preferred

    fallbacks = CHAT_FALLBACKS if category != "image" else IMAGE_FALLBACKS
    for model in fallbacks:
        if model not in _dead_models:
            return model

    # Si todo está muerto, intentar el preferido de todas formas
    return preferred


def mark_dead(model: str) -> str | None:
    """
    Marca un modelo como muerto y retorna el siguiente disponible.
    """
    _dead_models.add(model)
    logger.warning(f"☠️ Modelo '{model}' marcado como MUERTO (404)")

    # Buscar en ambas listas
    for fallback_list in [CHAT_FALLBACKS, IMAGE_FALLBACKS]:
        if model in fallback_list:
            for m in fallback_list:
                if m not in _dead_models:
                    logger.info(f"🔄 AUTO-SWITCH: {model} → {m}")
                    return m
    return None


async def smart_generate(client, model: str, contents, config=None, category: str = "chat"):
    """
    Wrapper inteligente para generate_content con auto-fallback.
    
    Si el modelo devuelve 404, automáticamente prueba el siguiente
    de la lista de fallback y reintenta.
    
    Args:
        client: google.genai.Client
        model: nombre del modelo preferido
        contents: prompt/contenido
        config: GenerateContentConfig
        category: "chat" o "image"
        
    Returns:
        response de Gemini
    """
    # Usar modelo que funcione
    current_model = get_working_model(model, category)
    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        attempts += 1
        try:
            kwargs = {"model": current_model, "contents": contents}
            if config:
                kwargs["config"] = config

            response = client.models.generate_content(**kwargs)
            return response

        except Exception as e:
            error_str = str(e).lower()

            # Detectar 404 (modelo no existe)
            if "404" in error_str or "not found" in error_str:
                next_model = mark_dead(current_model)
                if next_model:
                    current_model = next_model
                    logger.info(f"🔄 Reintentando con modelo: {current_model}")
                    continue
                else:
                    raise  # No hay más modelos

            # Detectar 429 (rate limit)
            elif "429" in error_str or "rate" in error_str or "quota" in error_str:
                import asyncio
                logger.warning(f"⏳ Rate limit en '{current_model}' — esperando 5s...")
                await asyncio.sleep(5)
                continue

            # Otro error — no reintentar
            else:
                raise

    raise Exception(f"Todos los intentos fallaron para '{model}'")


def get_status() -> str:
    """Resumen del estado para mostrar al admin."""
    if not _dead_models:
        return "✅ Todos los modelos funcionan correctamente."
    return f"⚠️ Modelos caídos: {', '.join(sorted(_dead_models))}"
