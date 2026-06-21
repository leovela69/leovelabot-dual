# -*- coding: utf-8 -*-
"""
Orquestador de Agentes — Router de intenciones con failover.
"""

import logging
from agents.provider_manager import get_provider_manager

logger = logging.getLogger("leovelabot.orchestrator")

CLASSIFICATION_PROMPT = """Eres un clasificador de intenciones. Analiza el mensaje del usuario y responde SOLO con una de estas categorías (una sola palabra):

- CHAT: conversación general, preguntas, saludos, opiniones
- IMAGE: crear, generar, dibujar, diseñar una imagen o foto
- VIDEO_SHORT: crear un vídeo corto (menos de 1 minuto)
- VIDEO_LONG: crear un vídeo largo (más de 1 minuto, película, cortometraje)
- CODE: programar, crear código, hacer un juego, una app, un script, arreglar código
- DESIGN: diseñar una UI, un logo, un banner, una interfaz, mockup, wireframe

Mensaje del usuario: "{message}"

Categoría:"""


class AgentOrchestrator:
    """Clasifica la intención del usuario y enruta al agente correcto."""

    def __init__(self):
        self._agents = {}
        logger.info("🧠 Orquestador de agentes inicializado")

    def register_agent(self, intent: str, agent) -> None:
        self._agents[intent] = agent

    async def classify_intent(self, message: str) -> str:
        try:
            manager = get_provider_manager()
            response = await manager.generate_text(
                prompt=CLASSIFICATION_PROMPT.format(message=message),
                temperature=0.1,
                max_output_tokens=20,
            )

            intent = response.strip().upper().replace(".", "").replace("*", "")

            valid_intents = {"CHAT", "IMAGE", "VIDEO_SHORT", "VIDEO_LONG", "CODE", "DESIGN"}
            if intent not in valid_intents:
                # Intentar extraer de la respuesta
                for vi in valid_intents:
                    if vi in intent:
                        return vi
                return "CHAT"

            return intent

        except Exception as e:
            logger.error(f"Error clasificando intención: {e}")
            return "CHAT"

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        intent = await self.classify_intent(message)

        agent = self._agents.get(intent) or self._agents.get("CHAT")

        if not agent:
            return {"type": "text", "content": "⚠️ No hay agentes configurados.", "intent": intent}

        try:
            result = await agent.process(message, chat_id, user_name)
            result["intent"] = intent
            return result
        except Exception as e:
            logger.error(f"Error en agente {intent}: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"❌ Error: {str(e)}\n\nInténtalo de nuevo.",
                "intent": intent,
            }
