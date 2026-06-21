"""Bot Merger: Une resultados de múltiples bots en uno coherente."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_merger = BotBase(
    id="bot_merger",
    nombre="Merger",
    especialidad="Unir resultados de equipos de bots en un output coherente",
    keywords=["unir", "merge", "combinar", "ensamblar", "juntar", "integrar"],
    prompt_compiled=(
        "Recibes outputs de múltiples bots. Únelos en un resultado coherente. "
        "Resuelve conflictos (nombres de variables, imports duplicados, estilos). "
        "El resultado final debe funcionar como una unidad. Solo output final."
    ),
    modelo="gemini-flash",
    herramientas=["merge_outputs", "resolver_conflictos"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_merger)
