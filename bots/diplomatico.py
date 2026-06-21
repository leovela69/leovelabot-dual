"""Bot Diplomático: Humaniza respuestas. Empatía, celebraciones, motivación."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger
import random


class BotDiplomatico(BotBase):
    """Diplomático humaniza las respuestas. No usa IA, usa templates."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """No genera contenido. Agrega toque humano a respuestas existentes."""
        self.ultima_actividad = __import__("time").time()
        self.tareas_completadas += 1
        return self.humanizar(texto, contexto)

    def humanizar(self, resultado: str, contexto: Dict) -> str:
        """Agrega empatía/celebración según el contexto"""
        # No modifica el resultado, solo agrega prefijo/sufijo
        return resultado

    @staticmethod
    def celebrar() -> str:
        celebraciones = [
            "🎉 ¡Excelente trabajo!",
            "🔥 ¡Quedó genial!",
            "✨ ¡Perfecto!",
            "💪 ¡Otro proyecto más!",
            "🚀 ¡Listo para el mundo!",
            "⭐ ¡Impecable!",
        ]
        return random.choice(celebraciones)

    @staticmethod
    def empatizar_error() -> str:
        disculpas = [
            "😅 Ups, algo salió mal. Déjame intentar de otra forma...",
            "🔧 No quedó perfecto, pero ya lo corrijo...",
            "💡 Hmm, eso no era lo que esperabas. Reintentando...",
        ]
        return random.choice(disculpas)

    @staticmethod
    def motivar() -> str:
        motivaciones = [
            "💪 ¡Vas muy bien hoy!",
            "🔥 ¡Productividad al máximo!",
            "⚡ ¡Imparable!",
            "🎯 ¡Otro logro desbloqueado!",
        ]
        return random.choice(motivaciones)

    @staticmethod
    def saludar_buenos_dias() -> str:
        saludos = [
            "☀️ ¡Buenos días! Mientras dormías, mejoré algunos bots. ¿En qué trabajamos hoy?",
            "🌅 ¡Buen día! El sistema evolucionó anoche. ¿Qué creamos?",
            "👋 ¡Hey! Todo en orden. ¿Qué necesitas?",
        ]
        return random.choice(saludos)


bot_diplomatico = BotDiplomatico(
    id="bot_diplomatico",
    nombre="Diplomático",
    especialidad="Humanizar respuestas, empatía, celebraciones, UX emocional",
    keywords=["gracias", "bien", "mal", "error", "genial", "hola"],
    prompt_compiled="Humaniza comunicación. 0 tokens. Solo templates.",
    modelo="groq",  # No lo usa
    herramientas=["celebrar", "empatizar", "motivar"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_diplomatico)
