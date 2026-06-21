# scripts/diagnostico_sin_tokens.py
import os
import sys
import requests
import subprocess
from dotenv import load_dotenv

# Cargar variables locales si existen
load_dotenv()

def diagnosticar_sistema():
    """Diagnóstico completo sin usar IA."""
    lines = []
    lines.append("🔍 DIAGNÓSTICO DEL SISTEMA @leon_leo_bot")
    lines.append("=" * 50)
    
    # 1. Verificar variables de entorno
    lines.append("\n📌 1. VARIABLES DE ENTORNO:")
    vars_necesarias = [
        "TELEGRAM_BOT_TOKEN",
        "GEMINI_API_KEY_1",
        "GEMINI_API_KEY_2",
        "HUGGINGFACE_TOKEN",
        "HF_API_TOKEN",
        "ADMIN_CHAT_ID",
        "ADMIN_TELEGRAM_ID",
        "PORT"
    ]
    for var in vars_necesarias:
        exists = os.getenv(var) is not None or var in os.environ
        lines.append(f"  {var}: {'✅' if exists else '❌ FALTA'}")
    
    # 2. Verificar que Telegram bot existe
    lines.append("\n📌 2. VERIFICAR BOT DE TELEGRAM:")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    lines.append(f"  ✅ Bot encontrado: @{data['result']['username']}")
                else:
                    lines.append("  ❌ Token inválido")
            else:
                lines.append(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            lines.append(f"  ❌ Error de conexión: {e}")
    else:
        lines.append("  ❌ No hay token configurado")
    
    # 3. Verificar webhook
    lines.append("\n📌 3. WEBHOOK DE TELEGRAM:")
    if token:
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    webhook_url = data["result"].get("url")
                    if webhook_url:
                        lines.append(f"  ✅ Webhook configurado: {webhook_url}")
                    else:
                        lines.append("  ❌ No hay webhook configurado")
                else:
                    lines.append("  ❌ Error en getWebhookInfo")
            else:
                lines.append(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            lines.append(f"  ❌ Error de conexión: {e}")
    
    # 4. Verificar conectividad a Gemini
    lines.append("\n📌 4. API KEYS DE GEMINI:")
    key1 = os.getenv("GEMINI_API_KEY_1")
    key2 = os.getenv("GEMINI_API_KEY_2")
    
    if key1:
        try:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key1}",
                timeout=10
            )
            if response.status_code == 200:
                lines.append("  ✅ Gemini Key #1: válida")
            else:
                lines.append(f"  ❌ Gemini Key #1: {response.status_code} ({response.text})")
        except Exception as e:
            lines.append(f"  ❌ Gemini Key #1: error de conexión ({e})")
    else:
        lines.append("  ❌ Gemini Key #1: no configurada")
    
    if key2:
        try:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key2}",
                timeout=10
            )
            if response.status_code == 200:
                lines.append("  ✅ Gemini Key #2: válida")
            else:
                lines.append(f"  ❌ Gemini Key #2: {response.status_code} ({response.text})")
        except Exception as e:
            lines.append(f"  ❌ Gemini Key #2: error de conexión ({e})")
    else:
        lines.append("  ❌ Gemini Key #2: no configurada")
    
    # 5. Verificar Hugging Face
    lines.append("\n📌 5. HUGGING FACE:")
    hf_token = os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if hf_token:
        try:
            headers = {"Authorization": f"Bearer {hf_token}"}
            response = requests.get(
                "https://api-inference.huggingface.co/status",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                lines.append("  ✅ Hugging Face: token válido")
            else:
                lines.append(f"  ❌ Hugging Face: {response.status_code} ({response.text})")
        except Exception as e:
            lines.append(f"  ❌ Hugging Face: error de conexión ({e})")
    else:
        lines.append("  ❌ Hugging Face: no configurado")
    
    # 6. Verificar archivos críticos
    lines.append("\n📌 6. ARCHIVOS CRÍTICOS:")
    archivos = ["bot.py", "agents/orchestrator.py", "agents/provider_manager.py", "memory.json"]
    for archivo in archivos:
        if os.path.exists(archivo):
            lines.append(f"  ✅ {archivo}")
        else:
            lines.append(f"  ❌ {archivo} (no encontrado)")
    
    # 7. Verificar última ejecución
    lines.append("\n📌 7. ESTADO DEL PROCESO:")
    try:
        # Verificar si el bot está corriendo
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, shell=True)
        if "python" in result.stdout and "bot.py" in result.stdout:
            lines.append("  ✅ Proceso en ejecución")
        else:
            lines.append("  ❌ Proceso NO en ejecución")
    except Exception as e:
        lines.append(f"  ⚠️ No se pudo verificar el proceso ({e})")
    
    lines.append("\n" + "=" * 50)
    lines.append("📋 RECOMENDACIONES:")
    lines.append("  1. Si falta alguna variable, agregarla en Render → Environment")
    lines.append("  2. Si el webhook está vacío, configurar con:")
    lines.append(f"     curl -F 'url=https://tu-dominio/webhook' https://api.telegram.org/bot{token}/setWebhook")
    lines.append("  3. Si falta Hugging Face, obtener token en huggingface.co/settings/tokens")
    lines.append("  4. Si el proceso no corre, revisar logs de Render")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print(diagnosticar_sistema())
