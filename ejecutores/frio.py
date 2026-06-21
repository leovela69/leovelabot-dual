"""Ejecutores Fríos: Se activan bajo demanda. HuggingFace, OpenRouter."""

from loguru import logger
import config
import httpx


async def llamar_huggingface(prompt: str, model: str = "meta-llama/Llama-3.1-70B-Instruct") -> str:
    """Llama a HuggingFace Inference API. Gratis, más lento."""
    if not config.HF_API_TOKEN:
        from ejecutores.caliente import llamar_groq
        return await llamar_groq(prompt)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {config.HF_API_TOKEN}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 2048}}
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0].get("generated_text", "").replace(prompt, "").strip()
                return str(data)
            else:
                logger.warning(f"HuggingFace error {resp.status_code}")
                from ejecutores.caliente import llamar_groq
                return await llamar_groq(prompt)
    except Exception as e:
        logger.error(f"Error HuggingFace: {e}")
        from ejecutores.caliente import llamar_groq
        return await llamar_groq(prompt)


async def llamar_openrouter(prompt: str) -> str:
    """Llama a OpenRouter. Último recurso / fallback."""
    if not config.OPENROUTER_API_KEY:
        from ejecutores.caliente import llamar_gemini_flash
        return await llamar_gemini_flash(prompt)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://c8lagency.com",
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                from ejecutores.caliente import llamar_gemini_flash
                return await llamar_gemini_flash(prompt)
    except Exception as e:
        logger.error(f"Error OpenRouter: {e}")
        from ejecutores.caliente import llamar_gemini_flash
        return await llamar_gemini_flash(prompt)


async def generar_imagen(prompt: str) -> str:
    """Genera imagen con HuggingFace (FLUX.1 o Stable Diffusion)."""
    if not config.HF_API_TOKEN:
        return "❌ Sin token de HuggingFace para imágenes."

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {config.HF_API_TOKEN}"},
                json={"inputs": prompt}
            )
            if resp.status_code == 200:
                # En producción: guardar en Supabase Storage y devolver URL
                return "🖼️ Imagen generada. En producción se guardaría en Storage."
            else:
                return f"❌ Error generando imagen: {resp.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
