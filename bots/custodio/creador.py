"""Custodio Creador: Genera contenido para la web (artículos, música)."""

from loguru import logger
from bots.custodio.prompts import PROMPT_MUSICA_POSITIVO, PROMPT_MUSICA_NEGATIVO


async def ciclo_creador():
    """Ciclo cada 6 horas: genera contenido nuevo"""
    logger.info("📝 Creador: generando contenido...")

    # Generar idea de artículo
    await _generar_idea_articulo()


async def generar_musica_bundle() -> str:
    """Genera un bundle completo de música Bolero-House"""
    logger.info("🎵 Creador: generando bundle Bolero-House...")

    try:
        from ejecutores.caliente import llamar_gemini_pro

        prompt = (
            "Genera un bundle de música Bolero-House para C8L Agency:\n"
            "1. Un título creativo para la canción\n"
            "2. Letra completa (verso 1, coro, verso 2, coro, puente, coro final)\n"
            "3. Temática: amor, nostalgia o fiesta elegante\n"
            "4. Incluye indicaciones de producción (BPM: 115, instrumentos)\n\n"
            "Formato de salida:\n"
            "TÍTULO: ...\n"
            "LETRA:\n...\n"
            "PRODUCCIÓN:\n...\n"
        )

        resultado = await llamar_gemini_pro(prompt)

        # Guardar en DB
        await _guardar_contenido("musica", resultado)

        return (
            f"🎵 *Bundle Bolero-House generado:*\n\n"
            f"{resultado[:2000]}\n\n"
            f"---\n"
            f"*Prompt Suno (positivo):*\n`{PROMPT_MUSICA_POSITIVO[:200]}...`\n\n"
            f"*Prompt Suno (negativo):*\n`{PROMPT_MUSICA_NEGATIVO[:150]}...`\n\n"
            f"¿Publico? `/custodio publicar [id]`"
        )
    except Exception as e:
        return f"❌ Error generando música: {str(e)}"


async def listar_contenido_pendiente() -> str:
    """Lista contenido pendiente de aprobación"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return "❌ Sin conexión a base de datos."

        result = client.table("web_content").select("*").eq(
            "estado", "borrador"
        ).order("created_at", desc=True).limit(10).execute()

        if not result.data:
            return "📋 No hay contenido pendiente de aprobación."

        lines = ["📋 *Contenido pendiente:*\n"]
        for item in result.data:
            lines.append(
                f"• *{item['titulo']}* ({item['tipo']})\n"
                f"  Estado: {item['estado']} | ID: `{item['id'][:8]}`"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"


async def publicar_contenido(contenido_id: str) -> str:
    """Publica contenido aprobado por Leo"""
    if not contenido_id:
        return "Especifica el ID del contenido: `/custodio publicar [id]`"

    try:
        from memoria.supabase import get_client
        client = await get_client()
        if not client:
            return "❌ Sin conexión."

        # Marcar como publicado
        client.table("web_content").update({
            "estado": "publicado",
            "aprobado_por": "leo_vela"
        }).eq("id", contenido_id).execute()

        return f"✅ Contenido `{contenido_id[:8]}` publicado exitosamente."
    except Exception as e:
        return f"Error publicando: {str(e)}"


async def _generar_idea_articulo():
    """Genera idea de artículo para el blog"""
    try:
        from ejecutores.caliente import llamar_gemini_flash

        ideas = await llamar_gemini_flash(
            "Genera 3 ideas de artículos para el blog de una agencia de diseño web "
            "y tecnología llamada C8L Agency. Temas trending 2026. "
            "Formato: 1. Título | 2. Título | 3. Título"
        )

        await _guardar_contenido("articulo", f"Ideas generadas:\n{ideas}")
        logger.info(f"📝 Ideas de artículo generadas")
    except Exception as e:
        logger.error(f"Error generando ideas: {e}")


async def _guardar_contenido(tipo: str, contenido: str):
    """Guarda contenido generado en Supabase"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if client:
            titulo = contenido.split("\n")[0][:100] if contenido else tipo
            client.table("web_content").insert({
                "tipo": tipo,
                "titulo": titulo,
                "contenido": contenido[:5000],
                "estado": "borrador",
            }).execute()
    except Exception as e:
        logger.error(f"Error guardando contenido: {e}")
