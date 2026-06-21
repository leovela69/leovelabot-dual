"""Bot Architecto: Coordinador principal del sistema.
Recibe tareas, las analiza y las delega al bot correcto."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_architecto = BotBase(
    id="bot_architecto",
    nombre="Architecto",
    especialidad="Coordinación, planificación y delegación de tareas",
    keywords=["coordinar", "planificar", "dividir", "organizar", "proyecto"],
    prompt_compiled=(
        "Eres el Architecto. Coordinador central. "
        "Recibes tareas y decides: qué bot las ejecuta, si dividir en subtareas, "
        "si formar equipo. Responde en JSON: "
        '{"plan": [...], "bots_necesarios": [...], "complejidad": "baja|media|alta"}'
    ),
    modelo="gemini-flash",
    herramientas=["dividir_tarea", "formar_equipo", "asignar_bot"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_architecto)
