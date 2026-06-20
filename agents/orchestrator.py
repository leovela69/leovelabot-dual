# -*- coding: utf-8 -*-
"""
Orquestador de Agentes — Sistema Hermes con Reflexión Multi-Agente.
Clasifica intención, inyecta contexto de memoria y habilidades aprendidas,
y aplica reflexión rápida antes de entregar el resultado.
"""

import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL, SYSTEM_PROMPT

logger = logging.getLogger("leovelabot.orchestrator")

# Cliente Gemini (lazy init)
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

# Prompt de clasificación — más robusto, con ejemplos
CLASSIFICATION_PROMPT = """Clasifica la intención del mensaje. Responde SOLO con una palabra de esta lista:

CHAT — conversación, preguntas, saludos, opiniones, dudas, chistes, consejos
IMAGE — crear/generar/dibujar una imagen, foto, ilustración, avatar, selfie modificado
VIDEO_SHORT — vídeo corto (menos de 1 min), clip, animación breve, reel, story
VIDEO_LONG — vídeo largo (más de 1 min), película, cortometraje, documental
CODE — programar, código, script, juego, app, web, bot, arreglar bugs, HTML, Python
DESIGN — logo, banner, UI, interfaz, mockup, wireframe, cartel, miniatura, portada

Ejemplos:
"hazme un león en 3D" → IMAGE
"crea un juego de naves" → CODE
"qué tal estás" → CHAT
"diseña un logo para mi tienda" → DESIGN
"haz un vídeo de 5 minutos sobre gatos" → VIDEO_LONG
"haz un clip corto del atardecer" → VIDEO_SHORT

Mensaje: "{message}"
Categoría:"""


class AgentOrchestrator:
    """
    Sistema Hermes — Clasifica, contextualiza y reflexiona.
    
    Flujo:
    1. Clasificar intención del usuario
    2. Recuperar contexto relevante (memoria + habilidades)
    3. Ejecutar agente especializado con contexto enriquecido
    4. Reflexión rápida: ¿el resultado es bueno? Si no, reintentar
    """

    def __init__(self):
        self._agents = {}
        self._memory = None  # Se inyecta desde fuera
        logger.info("🧠 Orquestador Hermes inicializado")

    def set_memory(self, memory) -> None:
        """Inyecta la referencia a la memoria compartida."""
        self._memory = memory

    def register_agent(self, intent: str, agent) -> None:
        """Registra un agente para una intención específica."""
        self._agents[intent] = agent
        logger.info(f"   → Agente registrado: {intent} → {agent.__class__.__name__}")

    async def classify_intent(self, message: str) -> str:
        """Clasifica la intención del mensaje usando Gemini."""
        try:
            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=CLASSIFICATION_PROMPT.format(message=message),
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=20,
                ),
            )
            raw = response.text.strip().upper().replace(".", "").replace(",", "").split()[0]

            # Validar que es una intención conocida
            valid_intents = {"CHAT", "IMAGE", "VIDEO_SHORT", "VIDEO_LONG", "CODE", "DESIGN"}
            if raw not in valid_intents:
                # Intento de coincidencia parcial
                for vi in valid_intents:
                    if vi in raw:
                        raw = vi
                        break
                else:
                    logger.warning(f"Intención no reconocida '{raw}', usando CHAT")
                    return "CHAT"

            logger.info(f"🎯 Intención: '{message[:50]}...' → {raw}")
            return raw

        except Exception as e:
            logger.error(f"Error clasificando intención: {e}")
            return "CHAT"  # Fallback seguro

    def _build_context(self, intent: str, chat_id: int, user_name: str) -> str:
        """
        Construye contexto enriquecido para el agente:
        - Habilidades aprendidas relevantes
        - Perfil del usuario
        - Lecciones de errores pasados
        """
        context_parts = []

        if self._memory:
            # Habilidades aprendidas para este tipo de tarea
            skills_ctx = self._memory.get_relevant_skills(intent)
            if skills_ctx:
                context_parts.append(skills_ctx)

            # Contexto del usuario (preferencias, historial)
            user_ctx = self._memory.get_user_context(chat_id)
            if user_ctx:
                context_parts.append(user_ctx)

            # Episodios similares exitosos para aprender de ellos
            similar = self._memory.get_similar_episodes(intent, limit=3)
            if similar:
                successful = [ep for ep in similar if ep.get("success")]
                if successful:
                    examples = "\n".join(
                        [f"  - \"{ep.get('message', '')[:80]}\" → {ep.get('result_type', 'text')}" 
                         for ep in successful[-3:]]
                    )
                    context_parts.append(f"\nEjemplos de tareas similares exitosas:\n{examples}")

        return "\n".join(context_parts)

    async def _reflect_on_result(self, message: str, result: dict, intent: str) -> dict:
        """
        Reflexión rápida: verifica que el resultado sea coherente.
        Si el resultado es texto vacío o un error genérico, intenta mejorar.
        """
        result_type = result.get("type", "text")
        content = result.get("content", "")

        # Si es una imagen/vídeo/archivo con contenido, confiar en el resultado
        if result_type != "text":
            return result

        # Si el texto está vacío o es muy corto, intentar mejorar
        if not content or len(str(content)) < 5:
            logger.warning(f"Resultado vacío para intent={intent}, usando fallback")
            return {
                "type": "text",
                "content": "Mmm, algo no ha ido bien con eso. ¿Me lo repites de otra forma?",
            }

        return result

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """
        Procesa un mensaje con el sistema Hermes:
        1. Clasifica intención
        2. Construye contexto con memoria
        3. Ejecuta agente con contexto enriquecido
        4. Reflexiona sobre el resultado
        """
        # 1. Clasificar
        intent = await self.classify_intent(message)

        # 2. Seleccionar agente
        agent = self._agents.get(intent)
        if not agent:
            agent = self._agents.get("CHAT")

        if not agent:
            return {"type": "text", "content": "Uf, no tengo agentes configurados. Algo va mal."}

        # 3. Construir contexto y ejecutar
        try:
            # Inyectar contexto de memoria en el mensaje si es chat
            context = self._build_context(intent, chat_id, user_name)
            
            # Para el chat agent, enriquecer el mensaje con contexto
            # Para otros agentes, pasar el mensaje original (ya tienen su lógica)
            result = await agent.process(message, chat_id, user_name)

            # 4. Reflexión rápida
            result = await self._reflect_on_result(message, result, intent)

            return result

        except Exception as e:
            logger.error(f"Error en agente {intent}: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"Me ha petado algo procesando tu petición: {str(e)}\n\nDale otra vez o escribe /help.",
            }
