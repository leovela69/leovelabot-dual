"""Bot Tutor: Explica código paso a paso (modo tutor).

Descompone conceptos de programación y fragmentos de código en explicaciones
claras, paso a paso, adaptadas al nivel del usuario. Ideal para aprendizaje
y comprensión profunda de lógica y patrones.
"""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotTutor(BotBase):
    """Explica código y conceptos de programación paso a paso.

    Especializado en:
    - Descomposición de código en pasos comprensibles
    - Adaptación al nivel del usuario (principiante/intermedio/avanzado)
    - Explicación de patrones de diseño y arquitectura
    - Analogías y ejemplos prácticos
    - Detección de conceptos previos necesarios
    """

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Ejecuta explicación tutorial paso a paso."""
        logger.info("📚 Tutor preparando explicación paso a paso...")
        self.ultima_actividad = __import__("time").time()

        # Detectar nivel y tipo de explicación
        nivel = self._detectar_nivel(texto, contexto)
        tipo = self._detectar_tipo_explicacion(texto, contexto)

        # Construir prompt pedagógico
        prompt = self._construir_prompt_tutor(texto, contexto, nivel, tipo, retry)

        try:
            resultado = await self._llamar_modelo(prompt)
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)
            return resultado

        except Exception as e:
            logger.error(f"Error en Tutor: {e}")
            self.fallos += 1
            self._actualizar_score(exito=False)
            return f"Error generando explicación: {str(e)}"

    def _detectar_nivel(self, texto: str, contexto: Dict[str, Any]) -> str:
        """Detecta el nivel del usuario basándose en el texto y contexto."""
        texto_lower = texto.lower()

        # Indicadores de principiante
        if any(w in texto_lower for w in [
            "no entiendo", "qué es", "básico", "principiante",
            "primera vez", "nunca he", "simple"
        ]):
            return "principiante"

        # Indicadores de avanzado
        if any(w in texto_lower for w in [
            "internals", "bajo nivel", "optimizar", "complejidad",
            "architecture", "trade-off", "avanzado"
        ]):
            return "avanzado"

        # Default: intermedio
        return "intermedio"

    def _detectar_tipo_explicacion(self, texto: str, contexto: Dict[str, Any]) -> str:
        """Detecta qué tipo de explicación necesita."""
        texto_lower = texto.lower()

        # Código existente para explicar
        if contexto.get("ultimo_output") and any(
            w in texto_lower for w in ["explica", "qué hace", "cómo funciona"]
        ):
            return "explicar_codigo"

        # Concepto teórico
        if any(w in texto_lower for w in [
            "qué es", "concepto", "patrón", "principio", "teoría"
        ]):
            return "concepto"

        # Paso a paso de implementación
        if any(w in texto_lower for w in [
            "cómo hago", "cómo se hace", "implementar", "crear"
        ]):
            return "implementacion"

        # Debugging/comprensión de error
        if any(w in texto_lower for w in [
            "error", "falla", "por qué no", "bug", "problema"
        ]):
            return "debugging"

        return "general"

    def _construir_prompt_tutor(
        self, texto: str, contexto: Dict[str, Any], nivel: str, tipo: str, retry: bool
    ) -> str:
        """Construye prompt pedagógico adaptado."""
        parts = [self.prompt_compiled]

        # Nivel de explicación
        instrucciones_nivel = {
            "principiante": (
                "\nNivel: PRINCIPIANTE. Usa analogías simples, evita jerga técnica. "
                "Explica cada término nuevo. Pasos muy pequeños."
            ),
            "intermedio": (
                "\nNivel: INTERMEDIO. Asume conocimientos básicos de programación. "
                "Enfócate en el 'por qué' además del 'cómo'."
            ),
            "avanzado": (
                "\nNivel: AVANZADO. Profundiza en internals, complejidad, trade-offs. "
                "Compara con alternativas. Menciona edge cases."
            ),
        }
        parts.append(instrucciones_nivel[nivel])

        # Formato según tipo
        instrucciones_tipo = {
            "explicar_codigo": (
                "\nExplica este código línea por línea. "
                "Numera cada paso. Indica qué hace y POR QUÉ."
            ),
            "concepto": (
                "\nExplica el concepto con: "
                "1) Definición simple, 2) Analogía, 3) Ejemplo en código, "
                "4) Cuándo usarlo, 5) Errores comunes."
            ),
            "implementacion": (
                "\nGuía paso a paso para implementar. "
                "Cada paso con: qué hacer, por qué, y código ejemplo."
            ),
            "debugging": (
                "\nExplica: 1) Qué significa el error, 2) Por qué ocurre, "
                "3) Cómo solucionarlo paso a paso, 4) Cómo prevenirlo."
            ),
            "general": (
                "\nExplica de forma clara y estructurada. "
                "Usa pasos numerados. Incluye ejemplos."
            ),
        }
        parts.append(instrucciones_tipo[tipo])

        # Código a explicar (si existe en contexto)
        if contexto.get("ultimo_output") and tipo == "explicar_codigo":
            parts.append(f"\nCódigo a explicar:\n```\n{contexto['ultimo_output'][:1500]}\n```")

        parts.append(f"\nPregunta del usuario: {texto}")

        if retry:
            parts.append(
                "\n[La explicación anterior no fue clara. "
                "Simplifica más, usa más analogías y ejemplos concretos.]"
            )

        return "\n".join(parts)


bot_tutor = BotTutor(
    id="bot_tutor",
    nombre="Tutor",
    especialidad="Explicación paso a paso de código y conceptos de programación",
    keywords=["explicar", "enseñar", "aprender", "paso", "tutor", "entender", "concepto", "cómo funciona"],
    prompt_compiled=(
        "Eres un tutor de programación paciente y claro. "
        "Explicas código y conceptos paso a paso, adaptándote al nivel del usuario. "
        "Usas analogías, ejemplos prácticos y numeración. "
        "Nunca asumes que algo es 'obvio'. "
        "Formato: pasos numerados, código con comentarios, resumen al final."
    ),
    modelo="gemini-flash",
    herramientas=["explicar_codigo", "descomponer_concepto", "generar_ejemplo"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_tutor)
