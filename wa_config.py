# -*- coding: utf-8 -*-
"""
Configuracion del bot de WhatsApp para C8L Agency.
"""

import os
import logging

logger = logging.getLogger("leovelabot.wa_config")

# ---------------------------------------------------------------------------
# WhatsApp Cloud API (Meta)
# ---------------------------------------------------------------------------
# Token de acceso permanente (se obtiene de Meta for Developers)
WHATSAPP_TOKEN: str = os.environ.get("WHATSAPP_TOKEN", "")

# Phone Number ID (ID del numero de telefono del bot en Meta)
WHATSAPP_PHONE_ID: str = os.environ.get("WHATSAPP_PHONE_ID", "")

# Token de verificacion del webhook (lo defines tu, cualquier string seguro)
VERIFY_TOKEN: str = os.environ.get("WA_VERIFY_TOKEN", "c8l_leovela_2026")

# Numero del admin (tu numero con codigo de pais, sin + ni espacios)
ADMIN_PHONE: str = os.environ.get("ADMIN_PHONE", "34611636294")

# ---------------------------------------------------------------------------
# Puerto del servidor web (unificado con el health-check de Telegram)
# Render.com inyecta PORT automáticamente. Usamos el mismo puerto para todo.
# ---------------------------------------------------------------------------
WEBHOOK_PORT: int = int(os.environ.get("PORT", "8080"))

# ---------------------------------------------------------------------------
# Gemini API (compartida con el bot de Telegram)
# ---------------------------------------------------------------------------
# Se hereda de la config del bot de Telegram via sys.path


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------
def validate_wa_config() -> bool:
    """Valida que las variables criticas esten configuradas. Retorna False si faltan (no crashea)."""
    missing = []

    if not WHATSAPP_TOKEN:
        missing.append("WHATSAPP_TOKEN")

    if not WHATSAPP_PHONE_ID:
        missing.append("WHATSAPP_PHONE_ID")

    if missing:
        logger.warning(f"⚠️ WhatsApp desactivado — faltan: {', '.join(missing)}")
        return False

    logger.info("✅ Configuracion de WhatsApp validada correctamente")
    return True
