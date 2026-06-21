"""Bot Música Corrector: Diagnostica fallos en generación musical (Suno/Udio).

Analiza prompts de generación de música, identifica problemas comunes
(estructura incorrecta, tags mal formados, estilos incompatibles),
y propone correcciones para obtener mejores resultados en plataformas
como Suno y Udio.
"""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotMusicaCorrector(BotBase):
    """Diagnostica y corrige fallos en generación de música con IA.

    Especializado en:
    - Análisis de prompts fallidos para Suno/Udio
    - Corrección de estructura de letras (intro, verso, coro, bridge, outro)
    - Detección de tags incompatibles o mal formados
    - Sugerencias de estilo y género para mejorar resultados
    - Diagnóstico de problemas de audio (cortes, distorsión, voz robótica)
    """

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Ejecuta diagnóstico de fallo musical."""
        logger.info("🎵 MúsicaCorrector analizando fallo de generación...")
        self.ultima_actividad = __import__("time").time()

        # Detectar tipo de problema
        problemas_detectados = self._detectar_problemas(texto, contexto)

        if problemas_detectados:
            # Construir prompt específico para diagnóstico musical
            prompt_diagnostico = self._construir_prompt_diagnostico(
                texto, contexto, problemas_detectados, retry
            )
            resultado = await self._llamar_modelo(prompt_diagnostico)
            self.tareas_completadas += 1
            self._actualizar_score(exito=True)
            return resultado
        else:
            # Diagnóstico general via modelo
            return await super().ejecutar(texto, contexto, retry)

    def _detectar_problemas(self, texto: str, contexto: Dict[str, Any]) -> list:
        """Detecta problemas comunes en prompts musicales."""
        problemas = []
        texto_lower = texto.lower()

        # Problemas de estructura
        if any(tag in texto_lower for tag in ["[intro]", "[verse]", "[chorus]"]):
            if "[chorus]" not in texto_lower and "[coro]" not in texto_lower:
                problemas.append("sin_coro")
            if texto_lower.count("[") != texto_lower.count("]"):
                problemas.append("tags_desbalanceados")

        # Problemas de longitud
        if len(texto) > 3000:
            problemas.append("prompt_muy_largo")

        # Problemas de estilo conflictivo
        estilos_conflictivos = [
            (["death metal", "heavy"], ["jazz suave", "bossa nova", "lo-fi"]),
            (["rap", "trap"], ["ópera", "clásica", "gregoriano"]),
        ]
        for grupo_a, grupo_b in estilos_conflictivos:
            tiene_a = any(e in texto_lower for e in grupo_a)
            tiene_b = any(e in texto_lower for e in grupo_b)
            if tiene_a and tiene_b:
                problemas.append("estilos_conflictivos")

        # Problemas reportados por el usuario
        if any(word in texto_lower for word in ["corte", "cortado", "se corta"]):
            problemas.append("audio_cortado")
        if any(word in texto_lower for word in ["robótic", "robot", "distorsion"]):
            problemas.append("voz_robotica")
        if any(word in texto_lower for word in ["no suena", "silencio", "vacío"]):
            problemas.append("sin_audio")

        return problemas

    def _construir_prompt_diagnostico(
        self, texto: str, contexto: Dict[str, Any], problemas: list, retry: bool
    ) -> str:
        """Construye prompt especializado para diagnóstico musical."""
        parts = [self.prompt_compiled]

        parts.append(f"\nProblemas detectados automáticamente: {', '.join(problemas)}")
        parts.append(f"\nPrompt/descripción del usuario: {texto}")

        if contexto.get("ultimo_output"):
            parts.append(f"\nOutput previo (posible prompt musical fallido):\n{contexto['ultimo_output'][:800]}")

        parts.append(
            "\nDiagnostica el problema y proporciona:"
            "\n1. Causa probable del fallo"
            "\n2. Prompt corregido listo para usar"
            "\n3. Tips para evitar el problema en el futuro"
        )

        if retry:
            parts.append("\n[IMPORTANTE: Sé más detallado y ofrece alternativas múltiples.]")

        return "\n".join(parts)


bot_musica_corrector = BotMusicaCorrector(
    id="bot_musica_corrector",
    nombre="Música Corrector",
    especialidad="Diagnóstico y corrección de fallos en generación musical (Suno, Udio)",
    keywords=["musica", "corregir", "suno", "fallo", "audio", "udio", "canción", "letra", "generar música"],
    prompt_compiled=(
        "Eres un experto en generación de música con IA (Suno, Udio). "
        "Diagnosticas por qué un prompt musical falla y propones correcciones. "
        "Conoces la estructura correcta: [Intro], [Verse], [Chorus], [Bridge], [Outro]. "
        "Sabes qué estilos combinan bien y cuáles generan conflictos. "
        "Responde con el diagnóstico y el prompt corregido listo para copiar."
    ),
    modelo="gemini-flash",
    herramientas=["diagnosticar_prompt_musical", "corregir_estructura", "sugerir_estilos"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_musica_corrector)
