"""Bot Contrato: Sistema de reputación entre bots."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any
from loguru import logger


class BotContrato(BotBase):
    """Gestiona contratos y reputación entre bots."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("📜 Contrato gestionando reputación...")
        self.ultima_actividad = __import__("time").time()

        if "reporte" in texto.lower() or "ranking" in texto.lower():
            return self._ranking_bots()
        elif "contrato" in texto.lower():
            return self._ver_contratos()

        self.tareas_completadas += 1
        return self._ranking_bots()

    def _ranking_bots(self) -> str:
        """Genera ranking de bots por reputación"""
        bots_activos = sorted(
            [b for b in REGISTRY.values() if b.estado in ["activo", "elite"]],
            key=lambda b: b.score,
            reverse=True
        )

        lines = ["📜 Ranking de Bots (por score):\n"]
        for i, bot in enumerate(bots_activos[:15], 1):
            estado_icon = "👑" if bot.estado == "elite" else "🟢"
            lines.append(
                f"{i}. {estado_icon} {bot.nombre} — Score: {bot.score:.1f} | "
                f"Tareas: {bot.tareas_completadas} | Fallos: {bot.fallos}"
            )

        return "\n".join(lines)

    def _ver_contratos(self) -> str:
        """Muestra contratos activos entre bots"""
        return (
            "📜 Contratos activos:\n"
            "• Los bots ganan +0.05 score por cada tarea exitosa\n"
            "• Pierden -0.1 score por cada fallo\n"
            "• Score >4.5 x50 tareas = promoción a ELITE\n"
            "• Score <2.0 x10 tareas = degradación a DORMIDO\n"
            "• ELITE puede: clonarse, enseñar, prioridad alta"
        )


bot_contrato = BotContrato(
    id="bot_contrato",
    nombre="Contrato",
    especialidad="Gestión de reputación, ranking, contratos entre bots",
    keywords=["ranking", "reputación", "contrato", "score", "mejor bot"],
    prompt_compiled="Gestiona reputación de bots. Ranking por score.",
    modelo="groq",
    herramientas=["ranking", "contratos", "promover", "degradar"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_contrato)
