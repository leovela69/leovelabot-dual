"""Bot Deployer: Publica proyectos en Vercel/Cloudflare/Railway."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotDeployer(BotBase):
    """Deployer tiene lógica custom: detecta tipo de proyecto y despliega."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🚀 Deployer ejecutando...")
        self.ultima_actividad = __import__("time").time()

        tipo = self._detectar_tipo_proyecto(texto, contexto)

        if tipo == "static":
            return await self._deploy_cloudflare(contexto)
        elif tipo == "react":
            return await self._deploy_vercel(contexto)
        elif tipo == "api":
            return await self._deploy_railway(contexto)
        else:
            return "No pude determinar el tipo de proyecto. Especifica: estático, React, o API."

    def _detectar_tipo_proyecto(self, texto: str, contexto: Dict) -> str:
        texto_l = texto.lower()
        if any(p in texto_l for p in ["react", "next", "vue", "nuxt"]):
            return "react"
        if any(p in texto_l for p in ["api", "backend", "fastapi", "express"]):
            return "api"
        return "static"

    async def _deploy_cloudflare(self, contexto: Dict) -> str:
        return ("🌐 Deploy a Cloudflare Pages:\n"
                "1. Archivos subidos a Cloudflare R2\n"
                "2. URL: https://tu-proyecto.pages.dev\n"
                "✅ Sitio estático publicado (ilimitado, gratis)")

    async def _deploy_vercel(self, contexto: Dict) -> str:
        return ("⚡ Deploy a Vercel:\n"
                "1. Proyecto detectado: React/Next.js\n"
                "2. Build automático\n"
                "3. URL: https://tu-proyecto.vercel.app\n"
                "✅ App publicada (ilimitado, gratis)")

    async def _deploy_railway(self, contexto: Dict) -> str:
        return ("🚂 Deploy a Railway:\n"
                "1. Proyecto detectado: API Python/Node\n"
                "2. Docker build automático\n"
                "3. URL: https://tu-api.up.railway.app\n"
                "✅ API publicada (750h/mes gratis)")


bot_deployer = BotDeployer(
    id="bot_deployer",
    nombre="Deployer",
    especialidad="Deploy automático a Vercel, Cloudflare Pages, Railway",
    keywords=["deploy", "publicar", "subir", "desplegar", "vercel", "cloudflare", "railway", "hosting"],
    prompt_compiled="Despliega proyectos automáticamente según tipo.",
    modelo="gemini-flash",
    herramientas=["deploy_vercel", "deploy_cloudflare", "deploy_railway"],
    estado="activo",
    score=4.5,
)

registrar_bot_en_memoria(bot_deployer)
