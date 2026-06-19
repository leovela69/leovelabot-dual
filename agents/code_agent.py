# -*- coding: utf-8 -*-
"""
Agente de Código — Programador y creador de videojuegos.
Usa Gemini con Code Execution para generar, ejecutar y enviar código.
"""

import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_CODE_MODEL, SYSTEM_PROMPT

logger = logging.getLogger("leovelabot.code")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class CodeAgent:
    """Genera código, crea videojuegos, y ejecuta scripts."""

    def __init__(self):
        logger.info("💻 Code Agent inicializado")

    async def process(self, message: str, chat_id: int, user_name: str) -> dict:
        """Genera código basado en la petición del usuario."""
        try:
            # Detectar si pide un videojuego (responder con HTML jugable)
            game_keywords = ["juego", "game", "videojuego", "snake", "tetris", "pong",
                             "plataformas", "arcade", "rpg", "shooter", "puzzle"]
            is_game = any(kw in message.lower() for kw in game_keywords)

            if is_game:
                return await self._create_game(message, user_name)
            else:
                return await self._create_code(message, user_name)

        except Exception as e:
            logger.error(f"Error en Code Agent: {e}", exc_info=True)
            return {
                "type": "text",
                "content": f"❌ Error generando código: {str(e)}",
            }

    async def _create_game(self, message: str, user_name: str) -> dict:
        """Genera un videojuego completo en HTML5 jugable en el navegador."""
        response = _get_client().models.generate_content(
            model=GEMINI_CODE_MODEL,
            contents=(
                f"Eres un desarrollador de videojuegos experto. Crea un juego web completo "
                f"basado en esta petición: '{message}'.\n\n"
                f"REGLAS ESTRICTAS:\n"
                f"1. El juego debe ser un ÚNICO archivo HTML que funcione al abrirlo en un navegador\n"
                f"2. Incluye todo el CSS y JavaScript inline (no dependencias externas)\n"
                f"3. El juego debe ser funcional, jugable y divertido\n"
                f"4. Usa Canvas 2D o DOM para los gráficos\n"
                f"5. Incluye: puntuación, controles (teclado/touch), game over, y reinicio\n"
                f"6. Diseño visual: estilo neon cyberpunk (fondo oscuro, colores brillantes)\n"
                f"7. Añade un título con el nombre del juego\n"
                f"8. Responsive para móvil y desktop\n\n"
                f"Responde SOLO con el código HTML completo, sin explicaciones. "
                f"Empieza con <!DOCTYPE html> y termina con </html>."
            ),
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )

        code = response.text.strip()
        # Limpiar marcadores de código markdown
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
            "caption": (
                f"🎮 *¡Juego creado!*\n\n"
                f"📝 _{message[:80]}_\n\n"
                f"📥 Descarga el archivo y ábrelo en tu navegador para jugar.\n"
                f"📱 Compatible con móvil y desktop."
            ),
        }

    async def _create_code(self, message: str, user_name: str) -> dict:
        """Genera código con ejecución opcional."""
        # Intentar con code execution si es algo que se puede ejecutar
        try:
            response = _get_client().models.generate_content(
                model=GEMINI_CODE_MODEL,
                contents=(
                    f"El usuario {user_name} pide: {message}\n\n"
                    f"Si la petición requiere generar código, genera código limpio, "
                    f"documentado y funcional. Si puedes ejecutar el código para mostrar "
                    f"el resultado, hazlo. Explica brevemente qué hace el código."
                ),
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)],
                    temperature=0.5,
                    max_output_tokens=8192,
                ),
            )
        except Exception:
            # Fallback sin code execution si no está disponible
            response = _get_client().models.generate_content(
                model=GEMINI_CODE_MODEL,
                contents=(
                    f"El usuario {user_name} pide: {message}\n\n"
                    f"Genera código limpio, documentado y funcional. "
                    f"Explica brevemente qué hace el código."
                ),
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=8192,
                ),
            )

        # Extraer contenido de la respuesta
        reply_parts = []
        code_blocks = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "executable_code") and part.executable_code:
                    code_blocks.append(f"```python\n{part.executable_code.code}\n```")
                elif hasattr(part, "code_execution_result") and part.code_execution_result:
                    reply_parts.append(f"📊 *Resultado:*\n```\n{part.code_execution_result.output}\n```")
                elif hasattr(part, "text") and part.text:
                    reply_parts.append(part.text)

        full_reply = "\n\n".join(reply_parts)
        if code_blocks:
            full_reply = "\n\n".join(code_blocks) + "\n\n" + full_reply

        # Si la respuesta es muy larga, enviarla como archivo
        if len(full_reply) > 4000:
            return {
                "type": "file",
                "content": full_reply.encode("utf-8"),
                "filename": "codigo_generado.txt",
                "caption": "💻 El código era muy largo, te lo envío como archivo.",
            }

        return {"type": "text", "content": f"💻 {full_reply}"}
