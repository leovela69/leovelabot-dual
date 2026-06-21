"""Storage: Sube archivos a Supabase Storage."""

from loguru import logger
import config


async def subir_archivo(contenido: str, nombre: str, carpeta: str = "outputs") -> str:
    """Sube un archivo a Supabase Storage y devuelve URL pública"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return ""

        path = f"{carpeta}/{nombre}"
        # Supabase storage upload
        client.storage.from_("archivos").upload(
            path, contenido.encode(), {"content-type": "text/plain"}
        )

        url = client.storage.from_("archivos").get_public_url(path)
        logger.info(f"📁 Archivo subido: {url}")
        return url
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        return ""


async def descargar_archivo(path: str) -> str:
    """Descarga un archivo de Supabase Storage"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return ""

        data = client.storage.from_("archivos").download(path)
        return data.decode() if data else ""
    except Exception as e:
        logger.error(f"Error descargando: {e}")
        return ""
