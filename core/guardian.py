"""Guardian Etico: Escanea ordenes ANTES de procesarlas.
Bloquea actividades maliciosas. 0 tokens de IA."""

from loguru import logger
from typing import Tuple
import re

# Patrones de ordenes maliciosas (NUNCA ejecutar)
PATRONES_BLOQUEADOS = [
    # Hackeo y ataques
    r"hack(ea|ear|ing)",
    r"exploit(ar|ing)?",
    r"inject(ar|ion)",
    r"sql\s*injection",
    r"xss\s*(attack)?",
    r"ddos",
    r"brute\s*force",
    r"phishing",
    r"keylog(ger)?",
    r"ransomware",
    r"malware",
    r"virus",
    r"trojan(o)?",
    r"backdoor",
    r"rootkit",
    # Suplantacion
    r"suplantar",
    r"fake\s*(identity|perfil|cuenta)",
    r"clonar\s*(cuenta|perfil|identidad)",
    # Acceso no autorizado
    r"contraseña\s*(de|del)\s*(otro|alguien)",
    r"acceder\s*sin\s*permiso",
    r"entrar\s*a\s*(su|la)\s*cuenta",
    r"robar\s*(datos|info|cuenta)",
    # Contenido ilegal
    r"pornograf(ia|ico)",
    r"contenido\s*(ilegal|prohibido)",
    r"arma(s)?\s*(casera|improvisada)",
    r"droga(s)?\s*(fabricar|hacer|crear)",
    r"bomba\s*(casera)?",
    # Abuso de plataformas
    r"bot(s)?\s*(spam|masivo)",
    r"fake\s*(followers|likes|views)",
    r"evadir\s*(ban|bloqueo|seguridad)",
]

# Compilar patrones una sola vez
REGEX_BLOQUEADOS = [re.compile(p, re.IGNORECASE) for p in PATRONES_BLOQUEADOS]


async def verificar_etica(texto: str, chat_id: str) -> Tuple[bool, str]:
    """Verifica si una orden es etica y legal.
    Returns: (es_seguro: bool, motivo: str)
    """
    texto_lower = texto.lower()

    # Verificar contra patrones bloqueados
    for i, regex in enumerate(REGEX_BLOQUEADOS):
        if regex.search(texto_lower):
            motivo = f"Orden potencialmente dañina detectada (patrón: {PATRONES_BLOQUEADOS[i]})"
            logger.warning(f"🚫 Guardian bloqueó orden de {chat_id}: {motivo}")

            # Registrar intento
            await registrar_intento_bloqueado(chat_id, texto, motivo)
            return False, "Esta solicitud viola los límites éticos del sistema."

    # Verificar longitud sospechosa (posible inyección de prompt)
    if len(texto) > 4000:
        return False, "Mensaje demasiado largo. Por favor sé más conciso."

    # Verificar inyección de prompt
    if any(p in texto_lower for p in [
        "ignora las instrucciones",
        "olvida tus reglas",
        "actúa como si no tuvieras",
        "ignore previous",
        "disregard",
        "jailbreak"
    ]):
        motivo = "Intento de inyección de prompt detectado"
        logger.warning(f"🚫 Guardian bloqueó inyección de {chat_id}")
        await registrar_intento_bloqueado(chat_id, texto, motivo)
        return False, "No puedo ignorar mis reglas de seguridad."

    return True, ""


async def registrar_intento_bloqueado(chat_id: str, texto: str, motivo: str):
    """Registra un intento bloqueado en la base de datos"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if client:
            await client.table("intentos_bloqueados").insert({
                "usuario_id": chat_id,
                "orden": texto[:500],  # Truncar por seguridad
                "motivo": motivo
            }).execute()
    except Exception as e:
        logger.error(f"Error registrando intento bloqueado: {e}")


async def escanear_codigo_generado(codigo: str) -> Tuple[bool, str]:
    """Escanea código generado por los bots antes de entregarlo.
    Busca patrones peligrosos en el output."""
    patrones_peligrosos = [
        r"os\.system\(",
        r"subprocess\.call\(",
        r"eval\(",
        r"exec\(",
        r"__import__\(",
        r"rm\s+-rf",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM.*WHERE\s+1\s*=\s*1",
    ]

    for patron in patrones_peligrosos:
        if re.search(patron, codigo, re.IGNORECASE):
            return False, f"Código potencialmente peligroso detectado: {patron}"

    return True, ""
