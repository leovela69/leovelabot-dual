"""Ejecutores Calientes: Modelos de IA que se llaman frecuentemente.
Groq (ultra rápido), Gemini Flash, Gemini Pro."""

from loguru import logger
import config
import httpx

# Índice rotativo para key rotation
_gemini_index = 0
_groq_index = 0


async def llamar_groq(prompt: str) -> str:
    """Llama a Groq (Llama 3.1 70B). Ultra rápido, gratis."""
    global _groq_index

    if not config.GROQ_KEYS:
        return await llamar_gemini_flash(prompt)  # Fallback

    key = config.GROQ_KEYS[_groq_index % len(config.GROQ_KEYS)]
    _groq_index += 1

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.7,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"Groq error {resp.status_code}, fallback a Gemini")
                return await llamar_gemini_flash(prompt)
    except Exception as e:
        logger.error(f"Error Groq: {e}")
        return await llamar_gemini_flash(prompt)


async def llamar_gemini_flash(prompt: str) -> str:
    """Llama a Gemini 1.5 Flash. Rápido y gratis."""
    global _gemini_index

    if not config.GEMINI_KEYS:
        return "Error: No hay API keys de Gemini configuradas."

    key = config.GEMINI_KEYS[_gemini_index % len(config.GEMINI_KEYS)]
    _gemini_index += 1

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.7}
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return "Sin respuesta del modelo."
            else:
                logger.warning(f"Gemini Flash error {resp.status_code}")
                return f"Error del modelo (status {resp.status_code})"
    except Exception as e:
        logger.error(f"Error Gemini Flash: {e}")
        return f"Error: {str(e)}"


async def llamar_gemini_pro(prompt: str) -> str:
    """Llama a Gemini 1.5 Pro. Potente, para tareas complejas."""
    global _gemini_index

    if not config.GEMINI_KEYS:
        return "Error: No hay API keys de Gemini configuradas."

    key = config.GEMINI_KEYS[_gemini_index % len(config.GEMINI_KEYS)]
    _gemini_index += 1

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.7}
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return "Sin respuesta del modelo."
            else:
                logger.warning(f"Gemini Pro error {resp.status_code}, fallback a Flash")
                return await llamar_gemini_flash(prompt)
    except Exception as e:
        logger.error(f"Error Gemini Pro: {e}")
        return await llamar_gemini_flash(prompt)
