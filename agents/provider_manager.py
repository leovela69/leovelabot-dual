# -*- coding: utf-8 -*-
"""
🔧 Provider Manager — Failover automático multi-proveedor.

Si Gemini falla → Groq. Si Groq falla → OpenRouter. Nunca se queda mudo.
Rotación de API keys. Auto-recuperación. Notificación al admin.
"""

import os
import time
import logging
import requests
from google import genai
from google.genai import types

logger = logging.getLogger("leovelabot.providers")


class ProviderManager:
    """Gestiona múltiples proveedores de IA con failover automático."""

    def __init__(self):
        self._providers = []
        self._setup_providers()
        self._last_switch_time = 0
        logger.info(f"🔧 ProviderManager: {len(self._providers)} proveedores configurados")

    def _setup_providers(self):
        """Configura todos los proveedores disponibles según variables de entorno."""
        # Gemini Key 1
        key1 = os.environ.get("GEMINI_API_KEY", "")
        if key1:
            self._providers.append({
                "name": "gemini_1",
                "type": "gemini",
                "model": "gemini-3.5-flash",
                "key": key1,
                "priority": 1,
                "failures": 0,
                "max_failures": 3,
                "last_fail": 0,
            })

        # Gemini Key 2
        key2 = os.environ.get("GEMINI_API_KEY_2", "")
        if key2:
            self._providers.append({
                "name": "gemini_2",
                "type": "gemini",
                "model": "gemini-3.5-flash",
                "key": key2,
                "priority": 2,
                "failures": 0,
                "max_failures": 3,
                "last_fail": 0,
            })

        # Groq (gratis, muy rápido)
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            self._providers.append({
                "name": "groq",
                "type": "groq",
                "model": "llama-3.3-70b-versatile",
                "key": groq_key,
                "priority": 3,
                "failures": 0,
                "max_failures": 3,
                "last_fail": 0,
            })

        # OpenRouter (muchos modelos gratis)
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
        if or_key:
            self._providers.append({
                "name": "openrouter",
                "type": "openrouter",
                "model": "google/gemini-2.5-flash-preview",
                "key": or_key,
                "priority": 4,
                "failures": 0,
                "max_failures": 3,
                "last_fail": 0,
            })

        if not self._providers:
            logger.error("❌ No hay proveedores configurados. Necesitas al menos GEMINI_API_KEY.")

    def _get_best_provider(self) -> dict | None:
        """Retorna el mejor proveedor disponible (menor prioridad + menos fallos)."""
        available = [
            p for p in self._providers
            if p["failures"] < p["max_failures"]
        ]

        if not available:
            # Reset todos los contadores si todo está caído
            logger.warning("⚠️ Todos los proveedores fallaron. Reseteando contadores...")
            for p in self._providers:
                p["failures"] = 0
            available = self._providers

        return sorted(available, key=lambda x: (x["failures"], x["priority"]))[0] if available else None

    def _call_gemini(self, provider: dict, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Llama a Gemini API."""
        client = genai.Client(api_key=provider["key"])

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        config_kwargs = {
            "temperature": kwargs.get("temperature", 0.85),
            "max_output_tokens": kwargs.get("max_output_tokens", 2048),
        }

        response = client.models.generate_content(
            model=provider["model"],
            contents=full_prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        return response.text.strip()

    def _call_groq(self, provider: dict, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Llama a Groq API (compatible con OpenAI)."""
        headers = {
            "Authorization": f"Bearer {provider['key']}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.85),
            "max_tokens": kwargs.get("max_output_tokens", 2048),
        }

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def _call_openrouter(self, provider: dict, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Llama a OpenRouter API (compatible con OpenAI)."""
        headers = {
            "Authorization": f"Bearer {provider['key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://c8lagency.com",
            "X-Title": "C8L Agency Bot",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.85),
            "max_tokens": kwargs.get("max_output_tokens", 2048),
        }

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    async def generate_text(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        Genera texto con failover automático.
        Prueba cada proveedor hasta que uno funcione.
        """
        max_attempts = len(self._providers) + 1
        last_error = None

        for attempt in range(max_attempts):
            provider = self._get_best_provider()
            if not provider:
                break

            try:
                if provider["type"] == "gemini":
                    result = self._call_gemini(provider, prompt, system_prompt, **kwargs)
                elif provider["type"] == "groq":
                    result = self._call_groq(provider, prompt, system_prompt, **kwargs)
                elif provider["type"] == "openrouter":
                    result = self._call_openrouter(provider, prompt, system_prompt, **kwargs)
                else:
                    continue

                # Éxito — resetear fallos
                if provider["failures"] > 0:
                    logger.info(f"✅ {provider['name']} recuperado")
                    provider["failures"] = 0

                return result

            except Exception as e:
                provider["failures"] += 1
                provider["last_fail"] = time.time()
                last_error = e
                logger.warning(
                    f"⚠️ {provider['name']} falló ({provider['failures']}/{provider['max_failures']}): {str(e)[:100]}"
                )
                continue

        # Todo falló
        error_msg = f"Todos los proveedores fallaron. Último error: {last_error}"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)

    def get_status(self) -> str:
        """Estado de los proveedores para /stats."""
        lines = ["🔧 *Proveedores:*"]
        for p in self._providers:
            status = "✅" if p["failures"] == 0 else f"⚠️({p['failures']})"
            lines.append(f"  {status} {p['name']}: {p['model']}")
        return "\n".join(lines)


# Singleton global
_manager = None


def get_provider_manager() -> ProviderManager:
    """Obtiene la instancia singleton del ProviderManager."""
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager
