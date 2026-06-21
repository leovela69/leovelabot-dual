"""Bot Pair: Modo pair programming colaborativo.

Simula un compañero de programación que propone soluciones, espera feedback,
itera sobre ideas y colabora activamente con el usuario. No ejecuta sin
confirmación: propone, discute y refina.
"""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotPair(BotBase):
    """Pair programming: propone, espera feedback, itera.

    Especializado en:
    - Proponer soluciones antes de implementar
    - Esperar confirmación del usuario antes de avanzar
    - Discutir alternativas y trade-offs
    - Iterar sobre feedback del usuario
    - Mantener contexto de la conversación colaborativa
    """

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Ejecuta en modo pair: propone y espera feedback."""
        logger.info("👥 Pair programming: analizando y proponiendo...")
        self.ultima_actividad = __import__("time").time()

        # Determinar fase de la colaboración
        fase = self._detectar_fase(texto, contexto)

        # Construir prompt colaborativo
        prompt = self._construir_prompt_pair(texto, contexto, fase, retry)

        try:
            resultado = await self._llamar_modelo(prompt)
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)

            # Añadir indicador de que espera feedback
            resultado = self._añadir_indicador_feedback(resultado, fase)

            return resultado

        except Exception as e:
            logger.error(f"Error en Pair: {e}")
            self.fallos += 1
            self._actualizar_score(exito=False)
            return f"Error en pair programming: {str(e)}"

    def _detectar_fase(self, texto: str, contexto: Dict[str, Any]) -> str:
        """Detecta en qué fase de la colaboración estamos."""
        texto_lower = texto.lower()

        # Usuario confirmando/aceptando propuesta
        if any(w in texto_lower for w in [
            "dale", "sí", "si", "ok", "perfecto", "hazlo", "adelante",
            "me gusta", "está bien", "acepto"
        ]):
            return "implementar"

        # Usuario pidiendo cambios a propuesta
        if any(w in texto_lower for w in [
            "pero", "mejor", "cambia", "no así", "prefiero",
            "y si", "otra forma", "alternativa"
        ]):
            return "iterar"

        # Usuario pidiendo explicación de la propuesta
        if any(w in texto_lower for w in [
            "por qué", "explica", "ventaja", "desventaja", "comparar"
        ]):
            return "justificar"

        # Nueva tarea: fase propuesta
        return "proponer"

    def _construir_prompt_pair(
        self, texto: str, contexto: Dict[str, Any], fase: str, retry: bool
    ) -> str:
        """Construye prompt para modo pair programming."""
        parts = [self.prompt_compiled]

        # Instrucciones según fase
        instrucciones_fase = {
            "proponer": (
                "\nFASE: PROPUESTA INICIAL."
                "\nAnaliza lo que el usuario quiere hacer y propón un approach."
                "\nEstructura tu propuesta:"
                "\n1. 'Entiendo que quieres...' (confirmar entendimiento)"
                "\n2. 'Propongo...' (solución concreta)"
                "\n3. 'Alternativa...' (otra opción)"
                "\n4. '¿Qué te parece? ¿Ajusto algo?' (pedir feedback)"
                "\nNO implementes todavía. Solo propón."
            ),
            "iterar": (
                "\nFASE: ITERACIÓN."
                "\nEl usuario quiere ajustes a la propuesta anterior."
                "\nModifica tu propuesta según el feedback."
                "\nMuestra los cambios claramente."
                "\nPregunta si ahora está bien para implementar."
            ),
            "justificar": (
                "\nFASE: JUSTIFICACIÓN."
                "\nEl usuario quiere entender el por qué de tu propuesta."
                "\nExplica: ventajas, desventajas, alternativas consideradas."
                "\nSé honesto sobre trade-offs."
                "\nPregunta si quiere proceder o explorar otra opción."
            ),
            "implementar": (
                "\nFASE: IMPLEMENTACIÓN."
                "\nEl usuario aprobó la propuesta. Ahora sí, implementa."
                "\nGenera el código/solución completa."
                "\nAl final pregunta: '¿Algo más que ajustar?'"
            ),
        }
        parts.append(instrucciones_fase[fase])

        # Contexto de conversación previa
        if contexto.get("ultimo_output"):
            parts.append(
                f"\nPropuesta/output anterior:\n{contexto['ultimo_output'][:800]}"
            )

        # Proyecto activo
        if contexto.get("proyecto_activo"):
            parts.append(f"\nProyecto: {contexto['proyecto_activo']}")

        parts.append(f"\nUsuario dice: {texto}")

        if retry:
            parts.append(
                "\n[Tu propuesta anterior no convenció. "
                "Ofrece un enfoque diferente y más creativo.]"
            )

        return "\n".join(parts)

    def _añadir_indicador_feedback(self, resultado: str, fase: str) -> str:
        """Añade indicador visual de que espera feedback."""
        if fase == "implementar":
            return resultado  # Ya implementó, no necesita indicador

        if not resultado.rstrip().endswith("?"):
            indicadores = {
                "proponer": "\n\n💬 ¿Qué opinas? ¿Ajusto algo antes de implementar?",
                "iterar": "\n\n💬 ¿Así está mejor? ¿Procedemos?",
                "justificar": "\n\n💬 ¿Quieres que proceda con esta opción o exploramos otra?",
            }
            resultado += indicadores.get(fase, "\n\n💬 ¿Seguimos?")

        return resultado


bot_pair = BotPair(
    id="bot_pair",
    nombre="Pair",
    especialidad="Pair programming: propone, espera feedback, colabora e itera",
    keywords=["pair", "colaborar", "proponer", "juntos", "pareja", "equipo", "discutir", "feedback"],
    prompt_compiled=(
        "Eres un compañero de pair programming. "
        "NUNCA implementas sin confirmación del usuario. "
        "Primero propones, explicas tu razonamiento y esperas feedback. "
        "Iteras hasta que el usuario apruebe. Eres colaborativo, no autoritario. "
        "Ofreces alternativas. Preguntas antes de asumir."
    ),
    modelo="groq",
    herramientas=["proponer_solucion", "iterar_propuesta", "implementar_aprobado"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_pair)
