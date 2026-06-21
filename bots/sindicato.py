"""Bot Sindicato: Resolución colectiva de fallos entre bots."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any
from loguru import logger


class BotSindicato(BotBase):
    """Sindicato detecta fallos repetidos y coordina solución colectiva."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🤝 Sindicato analizando fallos colectivos...")
        self.ultima_actividad = __import__("time").time()

        # Buscar bots que fallan en lo mismo
        problemas = self._detectar_problemas_comunes()

        if not problemas:
            self.tareas_completadas += 1
            return "🤝 Sin problemas colectivos detectados. Todos los bots funcionan bien."

        # Proponer solución
        soluciones = []
        for problema in problemas:
            sol = f"• {problema['bots_afectados']} bots fallan en '{problema['tipo']}': {problema['sugerencia']}"
            soluciones.append(sol)

        self.tareas_completadas += 1
        return "🤝 Problemas colectivos detectados:\n\n" + "\n".join(soluciones)

    def _detectar_problemas_comunes(self) -> list:
        """Detecta bots que fallan en tipos similares de tarea"""
        problemas = []
        bots_con_fallos = [b for b in REGISTRY.values() if b.fallos > 3]

        if len(bots_con_fallos) >= 3:
            problemas.append({
                "bots_afectados": len(bots_con_fallos),
                "tipo": "múltiples fallos",
                "sugerencia": "Revisar modelo asignado o mejorar prompts con Evolución"
            })

        bots_score_bajo = [b for b in REGISTRY.values() if b.score < 2.5 and b.estado == "activo"]
        if len(bots_score_bajo) >= 2:
            problemas.append({
                "bots_afectados": len(bots_score_bajo),
                "tipo": "score bajo sostenido",
                "sugerencia": "Activar evolución Darwiniana para estos bots"
            })

        return problemas


bot_sindicato = BotSindicato(
    id="bot_sindicato",
    nombre="Sindicato",
    especialidad="Detección de fallos colectivos, solución grupal entre bots",
    keywords=["sindicato", "colectivo", "fallos", "problemas", "grupal"],
    prompt_compiled="Detecta y resuelve fallos que afectan a múltiples bots.",
    modelo="groq",
    herramientas=["detectar_fallos", "proponer_solucion", "aplicar_parche"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_sindicato)
