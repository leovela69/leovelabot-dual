"""Script: Importa todos los bots para registrarlos en el REGISTRY.
Ejecutar al inicio del sistema para cargar los 44 bots."""

from loguru import logger


def cargar_todos_los_bots():
    """Importa todos los módulos de bots para que se registren"""
    logger.info("🤖 Cargando bots iniciales...")

    # Principales
    import bots.architecto
    import bots.sabio
    import bots.memorion
    import bots.frontend
    import bots.backend

    # Creación
    import bots.css
    import bots.javascript
    import bots.react
    import bots.sql
    import bots.copywriting
    import bots.seo

    # Operaciones
    import bots.deployer
    import bots.centinela
    import bots.cronos
    import bots.linter
    import bots.security
    import bots.merger

    # Meta
    import bots.evolucion_bot
    import bots.herrero
    import bots.profeta
    import bots.archivista
    import bots.fantasma
    import bots.despertador
    import bots.espia

    # Especiales
    import bots.mercenario
    import bots.diplomatico
    import bots.guardian_bot
    import bots.frankenstein
    import bots.enjambre
    import bots.sindicato
    import bots.contrato

    # Extras
    import bots.musica_corrector
    import bots.videoclip
    import bots.tutor
    import bots.pair
    import bots.fabrica

    from bots.base import REGISTRY
    logger.info(f"✅ {len(REGISTRY)} bots cargados en el Registry")
    return REGISTRY


if __name__ == "__main__":
    cargar_todos_los_bots()
