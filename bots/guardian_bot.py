"""Bot Guardián: Supervisa ética y seguridad del sistema."""

from bots.base import BotBase, registrar_bot_en_memoria

# El guardián real está en core/guardian.py
# Este bot es la interfaz para consultarlo desde Telegram

bot_guardian = BotBase(
    id="bot_guardian",
    nombre="Guardián",
    especialidad="Ética, seguridad, bloqueo de acciones maliciosas, auditoría",
    keywords=["seguridad", "ética", "bloquear", "permitir", "auditoría"],
    prompt_compiled=(
        "Supervisas la ética del sistema. Reportas intentos bloqueados. "
        "Escaneas código generado por vulnerabilidades. "
        "0 tokens: usas patterns y regex."
    ),
    modelo="groq",
    herramientas=["escanear_etica", "reportar_bloqueo", "auditar"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_guardian)
