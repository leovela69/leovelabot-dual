"""Bot Linter: Valida código sin IA (0 tokens)."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger
import re


class BotLinter(BotBase):
    """Linter valida código usando regex y lógica. 0 tokens de IA."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🔍 Linter validando código...")
        self.ultima_actividad = __import__("time").time()

        codigo = contexto.get("ultimo_output", texto)
        errores = []

        # Detectar tipo de código
        if "<html" in codigo.lower() or "<div" in codigo.lower():
            errores.extend(self._validar_html(codigo))
        if "def " in codigo or "import " in codigo:
            errores.extend(self._validar_python(codigo))
        if "function" in codigo or "const " in codigo:
            errores.extend(self._validar_js(codigo))

        if not errores:
            self.tareas_completadas += 1
            return "✅ Código válido. Sin errores detectados."

        self.tareas_completadas += 1
        return "⚠️ Errores encontrados:\n" + "\n".join(f"• {e}" for e in errores)

    def _validar_html(self, codigo: str) -> list:
        errores = []
        if "<html" in codigo and "</html>" not in codigo:
            errores.append("HTML: tag </html> faltante")
        if "<head" in codigo and "</head>" not in codigo:
            errores.append("HTML: tag </head> faltante")
        if "<body" in codigo and "</body>" not in codigo:
            errores.append("HTML: tag </body> faltante")
        imgs_sin_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', codigo)
        if imgs_sin_alt:
            errores.append(f"HTML: {len(imgs_sin_alt)} imágenes sin atributo alt")
        return errores

    def _validar_python(self, codigo: str) -> list:
        errores = []
        lines = codigo.split("\n")
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith("#"):
                if "\t" in line and "    " in line:
                    errores.append(f"Python L{i}: Mezcla de tabs y espacios")
                    break
        if "import *" in codigo:
            errores.append("Python: Wildcard import (import *) no recomendado")
        return errores

    def _validar_js(self, codigo: str) -> list:
        errores = []
        if "var " in codigo:
            errores.append("JS: Usar let/const en vez de var")
        opens = codigo.count("{")
        closes = codigo.count("}")
        if abs(opens - closes) > 1:
            errores.append(f"JS: Brackets desbalanceados ({opens} abiertos, {closes} cerrados)")
        return errores


bot_linter = BotLinter(
    id="bot_linter",
    nombre="Linter",
    especialidad="Validación de código sin IA. HTML, Python, JavaScript.",
    keywords=["validar", "lint", "errores", "sintaxis", "revisar", "código"],
    prompt_compiled="Valida código con regex y lógica. 0 tokens.",
    modelo="groq",  # No lo usa realmente
    herramientas=["lint_html", "lint_python", "lint_js"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_linter)
