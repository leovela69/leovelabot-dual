"""Juez: Evalúa calidad del resultado SIN usar IA. 0 tokens."""

from loguru import logger
from typing import Dict, Any


async def evaluar_resultado(resultado: str, clasificacion: Dict[str, Any]) -> int:
    """Evalúa la calidad del resultado con métricas reales.
    Score 0-100. No usa IA."""

    if not resultado or len(resultado.strip()) < 10:
        return 0

    score = 50  # Base
    tipo = clasificacion.get("tipo", "crear")

    # Completitud: ¿tiene contenido sustancial?
    if len(resultado) > 100:
        score += 10
    if len(resultado) > 500:
        score += 5

    # Coherencia: ¿tiene estructura?
    if any(marker in resultado for marker in ["```", "def ", "class ", "<", "{"]):
        score += 10

    # Si es código, validar sintaxis básica
    if tipo in ["crear", "modificar"]:
        score += _validar_codigo(resultado)

    # Penalizar errores obvios
    if "error" in resultado.lower() and "traceback" in resultado.lower():
        score -= 30
    if "undefined" in resultado.lower() or "null" in resultado.lower():
        score -= 5

    # Limitar rango
    return max(0, min(100, score))


def _validar_codigo(codigo: str) -> int:
    """Validación básica de código. Retorna bonus/penalización."""
    bonus = 0

    # HTML: tags cerrados
    if "<html" in codigo.lower() or "<div" in codigo.lower():
        opens = codigo.count("<") - codigo.count("</") - codigo.count("/>")
        if abs(opens) < 3:
            bonus += 5
        else:
            bonus -= 10

    # Python: indentación consistente
    if "def " in codigo or "class " in codigo:
        lines = codigo.split("\n")
        has_indent = any(l.startswith("    ") or l.startswith("\t") for l in lines)
        if has_indent:
            bonus += 5

    # JS: brackets balanceados
    if "function" in codigo or "const " in codigo:
        opens = codigo.count("{")
        closes = codigo.count("}")
        if abs(opens - closes) <= 1:
            bonus += 5
        else:
            bonus -= 10

    return bonus
