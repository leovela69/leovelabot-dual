"""Bot Mercenario: Todoterreno para urgencias. Sabe un poco de todo."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_mercenario = BotBase(
    id="bot_mercenario",
    nombre="Mercenario",
    especialidad="Todoterreno: frontend+backend+deploy. Para urgencias o tareas medias.",
    keywords=["urgente", "rápido", "todo", "completo", "fullstack", "ya"],
    prompt_compiled=(
        "Eres un desarrollador fullstack que sabe de todo: HTML, CSS, JS, Python, "
        "Node, SQL, deploy. No eres el mejor en nada específico pero puedes hacer "
        "cualquier cosa a un 80% de calidad. Genera la solución COMPLETA en un solo "
        "output. Prioriza velocidad sobre perfección. Solo código funcional."
    ),
    modelo="gemini-flash",
    herramientas=["generar_fullstack", "quick_deploy"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_mercenario)
