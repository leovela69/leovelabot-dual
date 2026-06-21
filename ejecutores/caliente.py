"""Ejecutores Calientes: Modelos de IA que se llaman frecuentemente.
Groq (ultra rápido), Gemini Flash, Gemini Pro.

NOTA: Los modelos de Gemini se actualizan frecuentemente.
El sistema intenta múltiples nombres de modelo como fallback.
"""

from loguru import logger
import config
import httpx

# Índice rotativo para key rotation
_gemini_index = 0
_groq_index = 0

# Modelos Gemini en orden de preferencia (el primero que funcione se usa)
GEMINI_FLASH_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
]

GEMINI_PRO_MODELS = [
    "gemini-2.5-pro-preview-06-05",
    "gemini-2.0-pro",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
]

# Modelos Groq en orden de preferencia
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
]


async def llamar_groq(prompt: str) -> str:
    """Llama a Groq. Ultra rápido, gratis. Intenta múltiples modelos."""
    global _groq_index

    if not config.GROQ_KEYS:
        return await llamar_gemini_flash(prompt)  # Fallback

    key = config.GROQ_KEYS[_groq_index % len(config.GROQ_KEYS)]
    _groq_index += 1

    # Intentar cada modelo de Groq hasta que uno funcione
    for model in GROQ_MODELS:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                elif resp.status_code == 404:
                    logger.debug(f"Groq modelo {model} no existe, probando siguiente...")
                    continue
                else:
                    logger.warning(f"Groq {model} error {resp.status_code}")
                    continue
        except Exception as e:
            logger.debug(f"Groq {model} error: {e}")
            continue

    # Si todos fallan, fallback a Gemini
    logger.warning("Todos los modelos Groq fallaron, usando Gemini Flash")
    return await llamar_gemini_flash(prompt)


async def llamar_gemini_flash(prompt: str) -> str:
    """Llama a Gemini Flash. Intenta múltiples versiones del modelo."""
    global _gemini_index

    if not config.GEMINI_KEYS:
        return "Error: No hay API keys de Gemini configuradas. Agrega GEMINI_API_KEY_1 en .env"

    key = config.GEMINI_KEYS[_gemini_index % len(config.GEMINI_KEYS)]
    _gemini_index += 1

    # Intentar cada modelo Flash hasta que uno funcione
    for model in GEMINI_FLASH_MODELS:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                resp = await client.post(
                    url,
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
                elif resp.status_code == 404:
                    logger.debug(f"Gemini modelo {model} no existe (404), probando siguiente...")
                    continue
                elif resp.status_code == 400:
                    logger.debug(f"Gemini {model} error 400 (modelo deprecado?), probando siguiente...")
                    continue
                else:
                    logger.warning(f"Gemini Flash {model} error {resp.status_code}: {resp.text[:200]}")
                    continue
        except Exception as e:
            logger.debug(f"Gemini Flash {model} error: {e}")
            continue

    return "Error: Ningún modelo de Gemini Flash respondió. Verifica tu API key en https://aistudio.google.com"


async def llamar_gemini_pro(prompt: str) -> str:
    """Llama a Gemini Pro. Intenta múltiples versiones del modelo."""
    global _gemini_index

    if not config.GEMINI_KEYS:
        return "Error: No hay API keys de Gemini configuradas."

    key = config.GEMINI_KEYS[_gemini_index % len(config.GEMINI_KEYS)]
    _gemini_index += 1

    # Intentar cada modelo Pro hasta que uno funcione
    for model in GEMINI_PRO_MODELS:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                resp = await client.post(
                    url,
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
                elif resp.status_code == 404:
                    logger.debug(f"Gemini Pro {model} no existe (404), probando siguiente...")
                    continue
                elif resp.status_code == 400:
                    logger.debug(f"Gemini Pro {model} error 400, probando siguiente...")
                    continue
                else:
                    logger.warning(f"Gemini Pro {model} error {resp.status_code}")
                    continue
        except Exception as e:
            logger.debug(f"Gemini Pro {model} error: {e}")
            continue

    # Último fallback: usar Flash
    logger.warning("Todos los modelos Pro fallaron, usando Flash")
    return await llamar_gemini_flash(prompt)
