"""Bot Frontend: Genera HTML + Tailwind + responsive."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_frontend = BotBase(
    id="bot_frontend",
    nombre="Frontend",
    especialidad="HTML semántico + Tailwind CSS + responsive + accesible",
    keywords=["html", "web", "página", "landing", "tailwind", "responsive", "sitio"],
    prompt_compiled=(
        "Genera HTML semántico con Tailwind CSS. Responsive mobile-first. "
        "Accesible (alt, aria, semántica). Moderno (2026). "
        "Solo output código. Sin explicaciones. "
        "Incluye: meta viewport, lang, charset."
    ),
    modelo="groq",
    herramientas=["generar_html", "lint_html"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_frontend)
