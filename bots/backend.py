"""Bot Backend: Genera APIs Python (FastAPI) y Node.js."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_backend_python = BotBase(
    id="bot_backend_python",
    nombre="Backend Python",
    especialidad="APIs FastAPI/Flask, lógica de servidor, autenticación, CRUD",
    keywords=["api", "backend", "python", "fastapi", "flask", "servidor", "endpoint", "rest"],
    prompt_compiled=(
        "Genera APIs REST con FastAPI. Incluye: type hints, Pydantic models, "
        "manejo de errores, docstrings. Estructura limpia. "
        "Solo output código funcional. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_python", "lint_python"],
    estado="activo",
    score=4.0,
)

bot_backend_node = BotBase(
    id="bot_backend_node",
    nombre="Backend Node",
    especialidad="APIs Express/Fastify, Node.js, middleware, autenticación",
    keywords=["node", "express", "javascript", "backend", "api", "middleware"],
    prompt_compiled=(
        "Genera APIs REST con Express.js o Fastify. "
        "ES modules, async/await, validación, error handling. "
        "Solo output código funcional. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_node", "lint_js"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_backend_python)
registrar_bot_en_memoria(bot_backend_node)
