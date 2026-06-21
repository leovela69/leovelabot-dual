"""Bot SEO: Optimización para buscadores, meta tags, schema."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_seo = BotBase(
    id="bot_seo",
    nombre="SEO",
    especialidad="SEO técnico, meta tags, schema JSON-LD, keywords, sitemap, robots.txt",
    keywords=["seo", "meta", "google", "posicionamiento", "keywords", "schema", "sitemap"],
    prompt_compiled=(
        "Genera contenido y código optimizado para SEO. "
        "Meta titles (<60 chars), descriptions (<160 chars), "
        "schema JSON-LD, Open Graph, keywords naturales. "
        "Solo output optimizado. Sin explicaciones."
    ),
    modelo="gemini-flash",
    herramientas=["generar_meta", "generar_schema", "analizar_seo"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_seo)
