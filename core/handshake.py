"""Handshake: Confirma con el usuario antes de tareas caras.
Si la tarea costará >2000 tokens, muestra plan y pide OK."""

from loguru import logger
from typing import Dict, Any


async def necesita_handshake(clasificacion: Dict[str, Any]) -> bool:
    """Determina si la tarea necesita confirmación"""
    complejidad = clasificacion.get("complejidad", "baja")
    tipo = clasificacion.get("tipo", "crear")

    # Tareas complejas siempre piden confirmación
    if complejidad == "alta":
        return True
    # Cadenas siempre piden confirmación
    if tipo == "encadenar":
        return True
    # Deploy siempre pide confirmación
    if tipo == "desplegar":
        return True

    return False


async def generar_plan(clasificacion: Dict[str, Any]) -> str:
    """Genera un plan resumido para mostrar al usuario"""
    tipo = clasificacion.get("tipo", "crear")
    keywords = clasificacion.get("keywords", [])
    complejidad = clasificacion.get("complejidad", "media")

    plan = f"📋 *Mi plan:*\n"
    plan += f"• Tipo: {tipo}\n"
    plan += f"• Complejidad: {complejidad}\n"
    plan += f"• Keywords: {', '.join(keywords[:5])}\n"
    plan += f"• Costo estimado: ~{'3000' if complejidad == 'alta' else '1500'} tokens\n"
    plan += f"\n¿Confirmas? (sí/no)"

    return plan
