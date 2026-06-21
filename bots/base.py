"""Clase base de TODOS los bots del sistema.
Cada bot hereda de BotBase y tiene: id, prompt, modelo, score, estado."""

from loguru import logger
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time

# Registry global de bots (in-memory, se sincroniza con DB)
REGISTRY: Dict[str, "BotBase"] = {}


@dataclass
class BotBase:
    """Clase base para todos los bots del ecosistema"""
    id: str
    nombre: str
    especialidad: str
    keywords: List[str] = field(default_factory=list)
    prompt_compiled: str = ""
    modelo: str = "groq"  # groq, gemini-flash, gemini-pro, huggingface
    herramientas: List[str] = field(default_factory=list)
    score: float = 3.0
    tareas_completadas: int = 0
    fallos: int = 0
    estado: str = "activo"  # novato, activo, elite, dormido, muerto
    padre_id: Optional[str] = None
    costo_promedio_tokens: int = 0
    ultima_actividad: float = field(default_factory=time.time)

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Ejecuta una tarea. Método principal que cada bot puede sobrescribir."""
        logger.info(f"🤖 Bot '{self.id}' ejecutando tarea...")
        self.ultima_actividad = time.time()

        try:
            # Construir prompt completo
            prompt = self._construir_prompt(texto, contexto, retry)

            # Llamar al modelo de IA
            resultado = await self._llamar_modelo(prompt)

            # Actualizar estadísticas
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)

            # Verificar promoción
            await self._verificar_promocion()

            return resultado

        except Exception as e:
            logger.error(f"Error en bot '{self.id}': {e}")
            self.fallos += 1
            self._actualizar_score(exito=False)

            # Verificar degradación
            await self._verificar_degradacion()

            return f"Error: {str(e)}"

    def _construir_prompt(self, texto: str, contexto: Dict[str, Any], retry: bool) -> str:
        """Construye el prompt completo para el modelo"""
        parts = []

        # System prompt del bot (compilado, ~80 tokens)
        parts.append(self.prompt_compiled)

        # Contexto del proyecto activo
        if contexto.get("proyecto_activo"):
            parts.append(f"\nProyecto activo: {contexto['proyecto_activo']}")

        # Output anterior (para continuaciones)
        if contexto.get("ultimo_output") and contexto.get("ultimos_mensajes"):
            parts.append(f"\nÚltimo output generado:\n{contexto['ultimo_output'][:500]}")

        # Si es retry, pedir mejor calidad
        if retry:
            parts.append("\n[IMPORTANTE: El resultado anterior no fue suficiente. Mejora la calidad.]")

        # La orden del usuario
        parts.append(f"\nOrden del usuario: {texto}")
        parts.append("\nResponde SOLO con el resultado. Sin explicaciones.")

        return "\n".join(parts)

    async def _llamar_modelo(self, prompt: str) -> str:
        """Llama al modelo de IA asignado al bot"""
        if self.modelo == "groq":
            from ejecutores.caliente import llamar_groq
            return await llamar_groq(prompt)
        elif self.modelo == "gemini-flash":
            from ejecutores.caliente import llamar_gemini_flash
            return await llamar_gemini_flash(prompt)
        elif self.modelo == "gemini-pro":
            from ejecutores.caliente import llamar_gemini_pro
            return await llamar_gemini_pro(prompt)
        elif self.modelo == "huggingface":
            from ejecutores.frio import llamar_huggingface
            return await llamar_huggingface(prompt)
        else:
            # Fallback: Groq
            from ejecutores.caliente import llamar_groq
            return await llamar_groq(prompt)

    def _actualizar_score(self, exito: bool):
        """Actualiza score del bot basado en éxito/fracaso"""
        if exito:
            self.score = min(5.0, self.score + 0.05)
        else:
            self.score = max(0.0, self.score - 0.1)

    async def _verificar_promocion(self):
        """Verifica si el bot merece ser promovido"""
        if self.estado == "novato" and self.tareas_completadas >= 5:
            tasa_exito = self.tareas_completadas / max(1, self.tareas_completadas + self.fallos)
            if tasa_exito >= 0.8:
                self.estado = "activo"
                logger.info(f"⬆️ Bot '{self.id}' promovido a ACTIVO")

        elif self.estado == "activo" and self.tareas_completadas >= 50:
            if self.score >= 4.5:
                self.estado = "elite"
                logger.info(f"👑 Bot '{self.id}' promovido a ELITE")

    async def _verificar_degradacion(self):
        """Verifica si el bot debe ser degradado"""
        if self.fallos >= 10 and self.score < 2.0:
            if self.estado in ["activo", "elite"]:
                self.estado = "dormido"
                logger.warning(f"⬇️ Bot '{self.id}' degradado a DORMIDO")
            elif self.estado == "dormido":
                self.estado = "muerto"
                logger.warning(f"☠️ Bot '{self.id}' marcado como MUERTO")

    async def pedir_ayuda(self, mensaje: str, tipo: str = "REQUEST_HELP"):
        """Pide ayuda a otros bots via Redis"""
        from memoria.redis import publicar_mensaje_bot
        # Buscar bot que pueda ayudar
        for bot_id, bot in REGISTRY.items():
            if bot_id != self.id and bot.estado in ["activo", "elite"]:
                await publicar_mensaje_bot(self.id, bot_id, tipo, mensaje)
                break

    async def compartir_output(self, destino: str, output: str):
        """Comparte su output con otro bot"""
        from memoria.redis import publicar_mensaje_bot
        await publicar_mensaje_bot(self.id, destino, "SHARE_OUTPUT", output)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el bot a diccionario"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "especialidad": self.especialidad,
            "keywords": self.keywords,
            "prompt_compiled": self.prompt_compiled,
            "modelo": self.modelo,
            "score": self.score,
            "tareas_completadas": self.tareas_completadas,
            "fallos": self.fallos,
            "estado": self.estado,
        }


def registrar_bot_en_memoria(bot: BotBase):
    """Registra un bot en el Registry in-memory"""
    REGISTRY[bot.id] = bot
    logger.debug(f"Bot registrado: {bot.id} ({bot.especialidad})")


def obtener_bot(bot_id: str) -> Optional[BotBase]:
    """Obtiene un bot del Registry por ID"""
    return REGISTRY.get(bot_id)


def listar_bots_activos() -> List[BotBase]:
    """Lista todos los bots activos y elite"""
    return [b for b in REGISTRY.values() if b.estado in ["activo", "elite"]]
