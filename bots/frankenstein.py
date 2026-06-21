"""Bot Frankenstein: Fusiona 2 bots en uno nuevo con habilidades combinadas."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any
from loguru import logger


class BotFrankenstein(BotBase):
    """Frankenstein fusiona dos bots existentes en uno nuevo."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🧬 Frankenstein fusionando bots...")
        self.ultima_actividad = __import__("time").time()

        # Extraer IDs de bots a fusionar
        bot_ids = self._extraer_bots(texto)
        if len(bot_ids) < 2:
            return "Necesito 2 bots para fusionar. Ejemplo: 'fusiona bot_react con bot_sql'"

        bot_a = REGISTRY.get(bot_ids[0])
        bot_b = REGISTRY.get(bot_ids[1])

        if not bot_a or not bot_b:
            return f"No encontré uno de los bots: {bot_ids}"

        # Fusionar
        nuevo = self._fusionar(bot_a, bot_b)
        REGISTRY[nuevo.id] = nuevo

        self.tareas_completadas += 1
        return (
            f"🧬 ¡Bot fusionado creado!\n"
            f"• Nombre: {nuevo.nombre}\n"
            f"• Especialidad: {nuevo.especialidad}\n"
            f"• Padres: {bot_a.id} + {bot_b.id}\n"
            f"• Estado: novato (se probará en próximas tareas)"
        )

    def _extraer_bots(self, texto: str) -> list:
        """Extrae IDs de bots del texto"""
        ids = []
        for bot_id in REGISTRY.keys():
            if bot_id in texto.lower():
                ids.append(bot_id)
        return ids[:2]

    def _fusionar(self, bot_a: BotBase, bot_b: BotBase) -> BotBase:
        """Crea un bot nuevo combinando 2 existentes"""
        nuevo_id = f"bot_{bot_a.id.replace('bot_', '')}_{bot_b.id.replace('bot_', '')}"
        nuevo_nombre = f"{bot_a.nombre} + {bot_b.nombre}"
        nueva_especialidad = f"{bot_a.especialidad} + {bot_b.especialidad}"
        nuevo_prompt = f"{bot_a.prompt_compiled} Además: {bot_b.prompt_compiled}"
        nuevas_keywords = list(set(bot_a.keywords + bot_b.keywords))

        nuevo = BotBase(
            id=nuevo_id[:30],
            nombre=nuevo_nombre[:50],
            especialidad=nueva_especialidad[:200],
            keywords=nuevas_keywords[:15],
            prompt_compiled=nuevo_prompt[:500],
            modelo=bot_a.modelo,  # Hereda modelo del primero
            herramientas=list(set(bot_a.herramientas + bot_b.herramientas)),
            estado="novato",
            score=min(bot_a.score, bot_b.score),
            padre_id=bot_a.id,
        )

        logger.info(f"🧬 Frankenstein creó: {nuevo.id}")
        return nuevo


bot_frankenstein = BotFrankenstein(
    id="bot_frankenstein",
    nombre="Frankenstein",
    especialidad="Fusionar 2 bots en uno nuevo con habilidades combinadas",
    keywords=["fusionar", "combinar", "mezclar", "frankenstein", "unir bots"],
    prompt_compiled="Fusiona 2 bots en uno nuevo combinando sus prompts y keywords.",
    modelo="gemini-flash",
    herramientas=["fusionar_bots", "registrar_fusion"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_frankenstein)
