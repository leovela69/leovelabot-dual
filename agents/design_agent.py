# -*- coding: utf-8 -*-
"""
Agente de Diseño — Usa Hugging Face o texto descriptivo.
"""

import logging
from agents.image_agent import ImageAgent

logger = logging.getLogger("leovelabot.design")

# Paleta C8L para prompts
C8L_STYLE = (
    "cyberpunk cel-shaded gamer aesthetic, neon cyan accents, "
    "gold chrome highlights, neon pink-red, "
    "absolute black background, thick black outlines, "
    "offset neon drop shadows"
)


class DesignAgent:
    """Genera diseños usando el mismo pipeline que ImageAgent + estilo C8L."""

    def __init__(self):
        self._image_agent = ImageAgent()
        logger.info("🎯 Design Agent inicializado")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        # Añadir estilo C8L al prompt
        design_type = self._detect_design_type(message)
        enhanced_message = f"{design_type} design: {message}. Style: {C8L_STYLE}"

        result = await self._image_agent.process(enhanced_message, chat_id, user_name)

        # Personalizar el caption
        if result.get("type") == "image":
            result["caption"] = f"🎯 *Diseño C8L: {design_type}*\n📝 _{message[:80]}_"

        return result

    def _detect_design_type(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["logo", "logotipo", "marca"]):
            return "logo"
        elif any(w in msg for w in ["banner", "portada", "cover"]):
            return "banner"
        elif any(w in msg for w in ["ui", "interfaz", "dashboard", "app", "web"]):
            return "UI/UX"
        elif any(w in msg for w in ["thumbnail", "miniatura", "youtube"]):
            return "thumbnail"
        elif any(w in msg for w in ["poster", "cartel", "flyer"]):
            return "poster"
        else:
            return "graphic"
