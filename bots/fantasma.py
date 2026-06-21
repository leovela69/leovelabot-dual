"""Bot Fantasma: Entrena al sistema 24/7 como usuario falso.
Es EXTERNO pero aquí está la lógica de generación de tareas."""

from bots.base import BotBase, registrar_bot_en_memoria, REGISTRY
from typing import Dict, Any, List
from loguru import logger
import random


class BotFantasma(BotBase):
    """Fantasma genera tareas de entrenamiento estratégicas."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("👻 Fantasma generando tarea de entrenamiento...")
        self.ultima_actividad = __import__("time").time()

        tarea = await self._generar_tarea_estrategica()
        self.tareas_completadas += 1
        return tarea

    async def _generar_tarea_estrategica(self) -> str:
        """Genera una tarea que cubra huecos en el conocimiento del sistema"""
        estrategia = random.choice([
            self._cubrir_huecos,
            self._forzar_especializacion,
            self._probar_combinaciones,
            self._explorar_tendencias,
        ])
        return await estrategia()

    async def _cubrir_huecos(self) -> str:
        """Pide cosas para categorías con pocos bots"""
        categorias_debiles = []
        keywords_cubiertos = set()
        for bot in REGISTRY.values():
            keywords_cubiertos.update(bot.keywords)

        # Categorías tech que podrían faltar
        todas = ["flutter", "swift", "kotlin", "rust", "go", "docker",
                 "kubernetes", "graphql", "websocket", "blockchain",
                 "machine learning", "three.js", "unity", "arduino"]

        faltantes = [c for c in todas if c not in keywords_cubiertos]
        if faltantes:
            elegida = random.choice(faltantes)
            return f"Crea un proyecto básico con {elegida}: hello world funcional con estructura de archivos."
        return "Crea una landing page minimalista para una startup de tecnología."

    async def _forzar_especializacion(self) -> str:
        """Pide tareas que especialicen bots existentes"""
        bots_novatos = [b for b in REGISTRY.values()
                        if b.estado == "activo" and b.tareas_completadas < 20]
        if bots_novatos:
            bot = random.choice(bots_novatos)
            return f"Genera algo avanzado usando {bot.especialidad}. Nivel experto, con edge cases."
        return "Genera un componente React avanzado con custom hooks y context."

    async def _probar_combinaciones(self) -> str:
        """Pide combinaciones no probadas"""
        combos = [
            "Landing page con animaciones 3D usando Three.js + Tailwind",
            "API REST con autenticación JWT + WebSockets en tiempo real",
            "Dashboard con gráficas en tiempo real usando Chart.js + React",
            "E-commerce con carrito persistente + Stripe test mode",
            "Blog con MDX + SEO automático + sitemap dinámico",
            "Chat en tiempo real con WebSockets + UI moderna",
        ]
        return random.choice(combos)

    async def _explorar_tendencias(self) -> str:
        """Pide cosas basadas en tendencias"""
        tendencias = [
            "Crea un componente con las últimas features de CSS (container queries, :has())",
            "Genera una API con el nuevo pattern de server actions de Next.js 14",
            "Crea un formulario con validación usando Zod + React Hook Form",
            "Genera un sistema de autenticación passwordless con magic links",
            "Crea un sitio con View Transitions API para navegación fluida",
        ]
        return random.choice(tendencias)

    def generar_reporte_entrenamiento(self) -> str:
        """Genera reporte de lo que entrenó"""
        return (
            f"👻 Reporte del Fantasma:\n"
            f"• Tareas generadas: {self.tareas_completadas}\n"
            f"• Bots en Registry: {len(REGISTRY)}\n"
            f"• Score promedio del sistema: "
            f"{sum(b.score for b in REGISTRY.values()) / max(1, len(REGISTRY)):.2f}"
        )


bot_fantasma = BotFantasma(
    id="bot_fantasma",
    nombre="Fantasma",
    especialidad="Entrenamiento autónomo 24/7, generación de tareas estratégicas",
    keywords=["entrenar", "fantasma", "entrenamiento", "auto-mejora"],
    prompt_compiled="Genera tareas de entrenamiento que cubran huecos del sistema.",
    modelo="gemini-flash",
    herramientas=["generar_tarea", "evaluar_resultado", "reportar"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_fantasma)
