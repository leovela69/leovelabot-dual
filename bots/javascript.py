"""Bot JavaScript: Lógica vanilla JS, interactividad."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_javascript = BotBase(
    id="bot_javascript",
    nombre="JavaScript",
    especialidad="JavaScript vanilla, DOM, eventos, async/await, fetch, lógica",
    keywords=["javascript", "js", "dom", "evento", "función", "lógica", "interactivo", "vanilla"],
    prompt_compiled=(
        "Genera JavaScript moderno (ES2022+). Async/await, modules, "
        "DOM manipulation eficiente, event delegation, error handling. "
        "Código limpio y funcional. Solo output. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_js", "lint_js"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_javascript)
