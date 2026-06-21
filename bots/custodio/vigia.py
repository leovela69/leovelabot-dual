"""Custodio Vigía: Monitoreo asíncrono de la web C8L Agency.
Pinguea cada 5 minutos. Detecta caídas, lentitud, errores."""

from loguru import logger
import httpx
import config


# Endpoints a monitorear
ENDPOINTS = [
    {"url": config.WEB_URL, "nombre": "Home"},
    {"url": f"{config.WEB_URL}/servicios", "nombre": "Servicios"},
    {"url": f"{config.WEB_URL}/portafolio", "nombre": "Portafolio"},
    {"url": f"{config.WEB_URL}/contacto", "nombre": "Contacto"},
]

# Umbral de latencia (ms)
UMBRAL_LATENCIA = 5000
# Contadores de fallos consecutivos
_fallos_consecutivos: dict = {}


async def ciclo_vigia():
    """Ciclo principal del Vigía (se ejecuta cada 5 minutos)"""
    logger.debug("👁️ Vigía: ping a la web...")

    resultados = []
    alertas = []

    async with httpx.AsyncClient(timeout=10) as client:
        for endpoint in ENDPOINTS:
            try:
                resp = await client.get(endpoint["url"])
                latencia = int(resp.elapsed.total_seconds() * 1000)

                if resp.status_code >= 500:
                    alertas.append(f"🚨 {endpoint['nombre']}: Error {resp.status_code}")
                    _fallos_consecutivos[endpoint["url"]] = _fallos_consecutivos.get(endpoint["url"], 0) + 1
                elif latencia > UMBRAL_LATENCIA:
                    alertas.append(f"⚠️ {endpoint['nombre']}: Lento ({latencia}ms)")
                else:
                    _fallos_consecutivos[endpoint["url"]] = 0
                    resultados.append(f"✅ {endpoint['nombre']}: {latencia}ms")

            except httpx.TimeoutException:
                alertas.append(f"🚨 {endpoint['nombre']}: TIMEOUT")
                _fallos_consecutivos[endpoint["url"]] = _fallos_consecutivos.get(endpoint["url"], 0) + 1
            except Exception as e:
                alertas.append(f"❌ {endpoint['nombre']}: {str(e)[:50]}")
                _fallos_consecutivos[endpoint["url"]] = _fallos_consecutivos.get(endpoint["url"], 0) + 1

    # Si hay 3+ fallos consecutivos en algún endpoint → alertar a Leo
    for url, count in _fallos_consecutivos.items():
        if count >= 3:
            await _alertar_leo(f"🚨 URGENTE: {url} ha fallado {count} veces consecutivas")
            # Activar médico
            from bots.custodio.medico import auto_reparar
            await auto_reparar(url)

    # Guardar métricas en DB
    await _guardar_monitoreo(resultados, alertas)

    if alertas:
        logger.warning(f"Vigía: {len(alertas)} alertas detectadas")


async def obtener_estado_web() -> str:
    """Obtiene estado actual de la web para mostrar al usuario"""
    lines = ["🌐 *Estado de la web C8L Agency:*\n"]

    async with httpx.AsyncClient(timeout=10) as client:
        for endpoint in ENDPOINTS:
            try:
                resp = await client.get(endpoint["url"])
                latencia = int(resp.elapsed.total_seconds() * 1000)

                if resp.status_code == 200:
                    icon = "✅" if latencia < 2000 else "⚡"
                    lines.append(f"{icon} {endpoint['nombre']}: {resp.status_code} ({latencia}ms)")
                else:
                    lines.append(f"⚠️ {endpoint['nombre']}: {resp.status_code} ({latencia}ms)")

            except httpx.TimeoutException:
                lines.append(f"🚨 {endpoint['nombre']}: TIMEOUT")
            except Exception as e:
                lines.append(f"❌ {endpoint['nombre']}: Error ({str(e)[:30]})")

    lines.append(f"\n🔗 URL: {config.WEB_URL}")
    return "\n".join(lines)


async def _alertar_leo(mensaje: str):
    """Envía alerta urgente a Leo Vela por Telegram"""
    try:
        from telegram.handlers import enviar_mensaje
        await enviar_mensaje(config.ADMIN_TELEGRAM_ID, mensaje)
    except Exception as e:
        logger.error(f"Error alertando a Leo: {e}")


async def _guardar_monitoreo(resultados: list, alertas: list):
    """Guarda resultado del monitoreo en Supabase"""
    try:
        from memoria.supabase import get_client
        client = await get_client()
        if client:
            import json
            client.table("web_audits").insert({
                "tipo": "ping",
                "problemas_detectados": json.dumps(alertas),
            }).execute()
    except Exception as e:
        logger.debug(f"Error guardando monitoreo: {e}")
