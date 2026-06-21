# scripts/auto_reparar.py
import os
import sys
import subprocess
import requests
from dotenv import load_dotenv

# Cargar variables locales si existen
load_dotenv()

def auto_reparar():
    """Intenta reparar problemas comunes automáticamente."""
    print("🔧 AUTO-REPARACIÓN DEL SISTEMA")
    print("=" * 50)
    
    # 1. Configurar webhook si está vacío
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL", "https://tu-dominio/webhook")
    
    if token and webhook_url:
        print("\n📌 Configurando webhook...")
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{token}/setWebhook",
                params={"url": webhook_url}
            )
            if response.status_code == 200 and response.json().get("ok"):
                print("  ✅ Webhook configurado correctamente")
            else:
                print(f"  ❌ Error configurando webhook: {response.text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # 2. Verificar memory.json
    if not os.path.exists("memory.json"):
        print("\n📌 Creando memory.json...")
        with open("memory.json", "w") as f:
            f.write('{"conversations": {}, "current_provider": "gemini_1"}')
        print("  ✅ memory.json creado")
    
    print("\n✅ Auto-reparación completada.")

if __name__ == "__main__":
    auto_reparar()
