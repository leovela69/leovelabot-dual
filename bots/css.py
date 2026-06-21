"""Bot CSS: Estilos avanzados, animaciones, responsive."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_css = BotBase(
    id="bot_css",
    nombre="CSS Advanced",
    especialidad="CSS avanzado, animaciones, Tailwind custom, responsive, dark mode",
    keywords=["css", "estilos", "animación", "hover", "responsive", "dark", "tailwind", "diseño"],
    prompt_compiled=(
        "Genera CSS moderno y avanzado. Animaciones suaves, transitions, "
        "responsive mobile-first, custom properties, dark mode. "
        "Tailwind o CSS puro según se pida. Solo código. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_css", "lint_css"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_css)
