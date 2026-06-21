"""Gestión de Proyectos: Organiza trabajo por proyecto.
Soporta versionado, fork, rollback."""

from loguru import logger
from typing import Optional, Dict, List


async def crear_proyecto(usuario_id: str, nombre: str) -> Optional[Dict]:
    """Crea un nuevo proyecto para el usuario"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return None

        result = client.table("proyectos").insert({
            "usuario_id": usuario_id,
            "nombre": nombre,
            "version_actual": 1,
        }).execute()

        if result.data:
            logger.info(f"📁 Proyecto creado: {nombre}")
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Error creando proyecto: {e}")
        return None


async def obtener_proyectos(usuario_id: str) -> List[Dict]:
    """Lista los proyectos del usuario"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return []

        result = client.table("proyectos").select("*").eq(
            "usuario_id", usuario_id
        ).order("updated_at", desc=True).execute()

        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error obteniendo proyectos: {e}")
        return []


async def guardar_version(proyecto_id: str, snapshot: Dict):
    """Guarda una nueva versión del proyecto"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return

        import json

        # Obtener versión actual
        proyecto = client.table("proyectos").select("version_actual").eq(
            "id", proyecto_id
        ).single().execute()

        if not proyecto.data:
            return

        nueva_version = proyecto.data["version_actual"] + 1

        # Guardar snapshot
        client.table("versiones").insert({
            "proyecto_id": proyecto_id,
            "numero": nueva_version,
            "snapshot": json.dumps(snapshot, ensure_ascii=False),
        }).execute()

        # Actualizar versión actual
        client.table("proyectos").update({
            "version_actual": nueva_version
        }).eq("id", proyecto_id).execute()

        logger.debug(f"Versión {nueva_version} guardada para proyecto {proyecto_id}")
    except Exception as e:
        logger.error(f"Error guardando versión: {e}")


async def rollback_version(proyecto_id: str, numero: int) -> Optional[Dict]:
    """Vuelve a una versión anterior del proyecto"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return None

        result = client.table("versiones").select("*").eq(
            "proyecto_id", proyecto_id
        ).eq("numero", numero).single().execute()

        if result.data:
            import json
            snapshot = json.loads(result.data["snapshot"])
            # Actualizar versión actual
            client.table("proyectos").update({
                "version_actual": numero
            }).eq("id", proyecto_id).execute()
            logger.info(f"⏪ Rollback a versión {numero}")
            return snapshot
        return None
    except Exception as e:
        logger.error(f"Error en rollback: {e}")
        return None


async def crear_fork(proyecto_id: str, nombre_fork: str) -> Optional[Dict]:
    """Crea un fork (rama alternativa) del proyecto"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return None

        # Obtener versión actual como base del fork
        proyecto = client.table("proyectos").select("*").eq(
            "id", proyecto_id
        ).single().execute()

        if not proyecto.data:
            return None

        # Crear versión tipo fork
        result = client.table("versiones").insert({
            "proyecto_id": proyecto_id,
            "numero": proyecto.data["version_actual"],
            "snapshot": "{}",
            "es_fork": True,
            "fork_nombre": nombre_fork,
        }).execute()

        logger.info(f"🔀 Fork creado: {nombre_fork}")
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creando fork: {e}")
        return None
