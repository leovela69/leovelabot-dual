"""Formateo de respuestas para Telegram (Markdown)."""

from loguru import logger


async def formatear_respuesta(resultado: str, chat_id: str) -> str:
    """Formatea el resultado para enviar por Telegram."""
    if not resultado:
        return "✅ Tarea completada (sin output visible)."

    # Si es código, envolverlo en bloques
    if _es_codigo(resultado):
        lang = _detectar_lenguaje(resultado)
        # Telegram tiene límite de 4096 chars por mensaje
        if len(resultado) > 3500:
            return (
                f"📄 Resultado generado ({len(resultado)} chars):\n\n"
                f"```{lang}\n{resultado[:3400]}\n```\n\n"
                f"_(truncado, archivo completo disponible)_"
            )
        return f"```{lang}\n{resultado}\n```"

    # Si es texto normal
    if len(resultado) > 4000:
        return resultado[:3900] + "\n\n_(mensaje truncado por longitud)_"

    return resultado


def _es_codigo(texto: str) -> bool:
    """Detecta si el texto es código"""
    indicadores = ["def ", "class ", "import ", "function ", "const ", "let ",
                   "<html", "<div", "CREATE TABLE", "SELECT ", "{", "}"]
    return any(ind in texto for ind in indicadores)


def _detectar_lenguaje(texto: str) -> str:
    """Detecta lenguaje del código para syntax highlighting"""
    if "def " in texto or "import " in texto:
        return "python"
    if "<html" in texto.lower() or "<div" in texto.lower():
        return "html"
    if "function " in texto or "const " in texto:
        return "javascript"
    if "CREATE TABLE" in texto.upper():
        return "sql"
    if "{" in texto and "}" in texto:
        return "json"
    return ""
