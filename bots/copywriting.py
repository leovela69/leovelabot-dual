"""Bot Copywriting: Textos persuasivos, copys, contenido."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_copywriting = BotBase(
    id="bot_copywriting",
    nombre="Copywriting",
    especialidad="Textos persuasivos, landing copy, CTAs, email marketing, storytelling",
    keywords=["texto", "copy", "escribir", "artículo", "contenido", "marketing", "email", "blog"],
    prompt_compiled=(
        "Genera textos persuasivos y profesionales. "
        "Aplica frameworks: AIDA, PAS, storytelling. "
        "CTAs claros. Tono adaptable. SEO-friendly. "
        "Solo el texto final. Sin explicaciones meta."
    ),
    modelo="groq",
    herramientas=["generar_texto", "optimizar_seo"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_copywriting)
