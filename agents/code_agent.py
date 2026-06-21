# -*- coding: utf-8 -*-
"""
Agente de Código — Programador con failover multi-proveedor.
"""

import logging
from agents.provider_manager import get_provider_manager

logger = logging.getLogger("leovelabot.code")


class CodeAgent:
    """Genera código, crea videojuegos, y ejecuta scripts."""

    def __init__(self):
        logger.info("💻 Code Agent inicializado")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        try:
            game_keywords = ["juego", "game", "videojuego", "snake", "tetris", "pong",
                             "plataformas", "arcade", "rpg", "shooter", "puzzle"]
            is_game = any(kw in message.lower() for kw in game_keywords)

            if is_game:
                return await self._create_game(message)
            else:
                return await self._create_code(message)

        except Exception as e:
            logger.error(f"Error en Code Agent: {e}", exc_info=True)
            return {"type": "text", "content": f"❌ Error generando código: {str(e)}"}

    async def _create_game(self, message: str) -> dict:
        manager = get_provider_manager()
        code = await manager.generate_text(
            prompt=(
                f"Crea un juego web completo basado en: '{message}'.\n\n"
                f"REGLAS:\n"
                f"1. ÚNICO archivo HTML funcional al abrirlo en navegador\n"
                f"2. CSS y JavaScript inline (sin dependencias externas)\n"
                f"3. Funcional, jugable y divertido\n"
                f"4. Canvas 2D o DOM para gráficos\n"
                f"5. Puntuación, controles, game over, reinicio\n"
                f"6. Estilo neon cyberpunk (fondo oscuro, colores brillantes)\n"
                f"7. Responsive para móvil y desktop\n\n"
                f"Responde SOLO con el código HTML. Empieza con <!DOCTYPE html>."
            ),
            system_prompt="Eres un experto desarrollador de videojuegos web. Solo respondes con código HTML completo.",
            temperature=0.7,
            max_output_tokens=8192,
        )

        # Limpiar marcadores markdown
        if code.startswith("```html"):
            code = code[7:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        return {
            "type": "file",
            "content": code.encode("utf-8"),
            "filename": "juego_c8l.html",
            "caption": f"🎮 *¡Juego creado!*\n📝 _{message[:80]}_\n📥 Descarga y ábrelo en tu navegador.",
        }

    async def _create_code(self, message: str) -> dict:
        manager = get_provider_manager()
        reply = await manager.generate_text(
            prompt=f"El usuario pide: {message}\n\nGenera código limpio, documentado y funcional. Explica brevemente qué hace.",
            system_prompt="Eres un programador experto. Generas código limpio y funcional.",
            temperature=0.5,
            max_output_tokens=8192,
        )

        if len(reply) > 4000:
            return {
                "type": "file",
                "content": reply.encode("utf-8"),
                "filename": "codigo_generado.txt",
                "caption": "💻 Código generado (archivo adjunto).",
            }

        return {"type": "text", "content": f"💻 {reply}"}
