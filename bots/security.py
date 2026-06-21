"""Bot Security: Escanea vulnerabilidades (0 tokens, regex)."""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger
import re


class BotSecurity(BotBase):
    """Security escanea código por vulnerabilidades usando patterns."""

    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        logger.info("🔒 Security escaneando...")
        self.ultima_actividad = __import__("time").time()

        codigo = contexto.get("ultimo_output", texto)
        vulnerabilidades = self._escanear(codigo)

        if not vulnerabilidades:
            return "🔒 Seguro. No se detectaron vulnerabilidades."

        resultado = "🚨 Vulnerabilidades detectadas:\n\n"
        for v in vulnerabilidades:
            resultado += f"• [{v['severidad']}] {v['tipo']}: {v['descripcion']}\n"

        return resultado

    def _escanear(self, codigo: str) -> list:
        vulns = []
        patterns = [
            (r"eval\(", "Code Injection", "eval() permite ejecución de código arbitrario", "ALTA"),
            (r"innerHTML\s*=", "XSS", "innerHTML puede inyectar scripts maliciosos", "ALTA"),
            (r"document\.write\(", "XSS", "document.write() es vulnerable a XSS", "MEDIA"),
            (r"SELECT\s+.*\s+FROM.*\+.*input", "SQL Injection", "Concatenación directa en query SQL", "ALTA"),
            (r"password\s*=\s*['\"]", "Hardcoded Secret", "Contraseña hardcodeada en el código", "ALTA"),
            (r"api[_-]?key\s*=\s*['\"]", "Exposed API Key", "API key expuesta en código", "ALTA"),
            (r"http://", "Insecure HTTP", "Usar HTTPS en vez de HTTP", "BAJA"),
            (r"cors\(.*origin.*\*", "Open CORS", "CORS abierto a todos los orígenes", "MEDIA"),
            (r"exec\(", "Code Execution", "exec() permite ejecución arbitraria", "ALTA"),
            (r"pickle\.loads?\(", "Deserialization", "pickle es inseguro con datos no confiables", "ALTA"),
        ]

        for pattern, tipo, desc, sev in patterns:
            if re.search(pattern, codigo, re.IGNORECASE):
                vulns.append({"tipo": tipo, "descripcion": desc, "severidad": sev})

        return vulns


bot_security = BotSecurity(
    id="bot_security",
    nombre="Security Scanner",
    especialidad="Escaneo de vulnerabilidades: XSS, SQLi, secrets, CORS",
    keywords=["seguridad", "vulnerabilidad", "xss", "sql injection", "escanear", "security"],
    prompt_compiled="Escanea código por vulnerabilidades con regex. 0 tokens.",
    modelo="groq",
    herramientas=["scan_xss", "scan_sqli", "scan_secrets"],
    estado="elite",
    score=5.0,
)

registrar_bot_en_memoria(bot_security)
