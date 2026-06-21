# -*- coding: utf-8 -*-
"""
Agente de Chat — Conversación con failover automático multi-proveedor.
"""

import logging
from collections import defaultdict
from agents.provider_manager import get_provider_manager
from config import SYSTEM_PROMPT, MAX_HISTORY_PER_USER

logger = logging.getLogger("leovelabot.chat")


class ChatAgent:
    """Agente de conversación con memoria por usuario y failover."""

    def __init__(self):
        self._history: dict[int, list[dict]] = defaultdict(list)
        logger.info("💬 Chat Agent inicializado")

    def _get_history_text(self, chat_id: int) -> str:
        history = self._history[chat_id]
        if not history:
            return ""
        lines = []
        for msg in history[-MAX_HISTORY_PER_USER:]:
            role = "Usuario" if msg["role"] == "user" else "Leo"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def _add_to_history(self, chat_id: int, role: str, text: str) -> None:
        self._history[chat_id].append({"role": role, "text": text})
        if len(self._history[chat_id]) > MAX_HISTORY_PER_USER * 2:
            self._history[chat_id] = self._history[chat_id][-MAX_HISTORY_PER_USER:]

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        try:
            history_text = self._get_history_text(chat_id)

            prompt = f"""El usuario se llama {user_name}.

{"Historial de la conversación:" if history_text else ""}
{history_text}

Usuario: {message}

Leo:"""

            manager = get_provider_manager()
            reply = await manager.generate_text(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.85,
                max_output_tokens=2048,
            )

            # Guardar en historial
            self._add_to_history(chat_id, "user", message)
            self._add_to_history(chat_id, "assistant", reply)

            return {"type": "text", "content": reply}

        except Exception as e:
            logger.error(f"Error en Chat Agent: {e}")
            return {
                "type": "text",
                "content": "🦁 Perdona, todos mis cerebros están descansando ahora. ¡Inténtalo en unos segundos!",
            }

    def clear_history(self, chat_id: int) -> None:
        self._history[chat_id].clear()
