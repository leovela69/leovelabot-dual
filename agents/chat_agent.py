# -*- coding: utf-8 -*-
"""
Agente de Chat — Conversación general con personalidad C8L.
Usa Gemini Flash tier gratuito con historial de conversación.
"""

import logging
from collections import defaultdict
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    SYSTEM_PROMPT,
    MAX_HISTORY_PER_USER,
)

logger = logging.getLogger("leovelabot.chat")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class ChatAgent:
    """Agente de conversación general con memoria por usuario."""

    def __init__(self):
        # Historial de conversación por chat_id
        self._history: dict[int, list[dict]] = defaultdict(list)
        logger.info("💬 Chat Agent inicializado")

    def _get_history_text(self, chat_id: int) -> str:
        """Construye el contexto del historial para el prompt."""
        history = self._history[chat_id]
        if not history:
            return ""

        lines = []
        for msg in history[-MAX_HISTORY_PER_USER:]:
            role = "Usuario" if msg["role"] == "user" else "Leo"
            lines.append(f"{role}: {msg['text']}")

        return "\n".join(lines)

    def _add_to_history(self, chat_id: int, role: str, text: str) -> None:
        """Añade un mensaje al historial."""
        self._history[chat_id].append({"role": role, "text": text})
        # Limitar tamaño del historial
        if len(self._history[chat_id]) > MAX_HISTORY_PER_USER * 2:
            self._history[chat_id] = self._history[chat_id][-MAX_HISTORY_PER_USER:]

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera una respuesta conversacional."""
        try:
            # Construir el prompt con contexto
            history_text = self._get_history_text(chat_id)

            full_prompt = f"""{SYSTEM_PROMPT}

El usuario se llama {user_name}.

{"Historial de la conversación:" if history_text else ""}
{history_text}

Usuario: {message}

Leo:"""

            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    max_output_tokens=2048,
                ),
            )

            reply = response.text.strip()

            # Guardar en historial
            self._add_to_history(chat_id, "user", message)
            self._add_to_history(chat_id, "assistant", reply)

            return {"type": "text", "content": reply}

        except Exception as e:
            logger.error(f"Error en Chat Agent: {e}")
            return {
                "type": "text",
                "content": "🦁 Perdona, tuve un problema procesando tu mensaje. ¡Inténtalo otra vez!",
            }

    def clear_history(self, chat_id: int) -> None:
        """Limpia el historial de un chat."""
        self._history[chat_id].clear()
        logger.info(f"Historial limpiado para chat_id={chat_id}")
