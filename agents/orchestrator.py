# -*- coding: utf-8 -*-
"""
Orquestador de Agentes — Router de Intenciones.
Usa Gemini Flash (gratuito) para clasificar qué quiere el usuario
y enrutar al agente especializado correcto.
"""

import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL

from agents.model_manager import smart_generate

logger = logging.getLogger("leovelabot.orchestrator")

# Cliente Gemini (lazy init)
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

# Prompt de clasificación
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
        """Registra un agente para una intención específica."""
        self._agents[intent] = agent
        logger.info(f"   → Agente registrado: {intent} → {agent.__class__.__name__}")

    async def classify_intent(self, message: str) -> str:
        """Clasifica la intención del mensaje usando Gemini."""
        try:
            response = await smart_generate(_get_client(), GEMINI_CHAT_MODEL,
                contents=CLASSIFICATION_PROMPT.format(message=message),
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=20,
                ),
            )
            intent = response.text.strip().upper().replace(".", "")

            # Validar que es una intención conocida
            valid_intents = {"CHAT", "IMAGE", "VIDEO_SHORT", "VIDEO_LONG", "CODE", "DESIGN"}
            if intent not in valid_intents:
                logger.warning(f"Intención no reconocida '{intent}', usando CHAT")
                return "CHAT"

            logger.info(f"🎯 Intención clasificada: '{message[:50]}...' → {intent}")
            return intent

        except Exception as e:
            logger.error(f"Error clasificando intención: {e}")
            return "CHAT"  # Fallback seguro

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """
        Procesa un mensaje: clasifica la intención y lo envía al agente correcto.
        
        Returns:
            dict con keys: 'type', 'content', 'intent', y opcionalmente 'caption'
        """
        intent = await self.classify_intent(message)

        agent = self._agents.get(intent)
        if not agent:
            agent = self._agents.get("CHAT")

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
                "content": f"❌ Error procesando tu solicitud: {str(e)}\n\nInténtalo de nuevo o escribe /help.",
                "intent": intent,
            }
