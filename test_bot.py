# -*- coding: utf-8 -*-
"""
🧪 Script de pruebas para @leovelabot — Ejecutar localmente.

Envía mensajes reales al bot vía Telegram API y muestra los resultados.
Requiere: TELEGRAM_BOT_TOKEN y GEMINI_API_KEY en variables de entorno.

Uso:
    export TELEGRAM_BOT_TOKEN="tu_token"
    export GEMINI_API_KEY="tu_key"
    export TEST_CHAT_ID="tu_chat_id"   # Tu chat ID personal
    python test_bot.py
"""

import os
import sys
import asyncio
import time
import json

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Validar configuración
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TEST_CHAT_ID = os.environ.get("TEST_CHAT_ID", "")

if not all([TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, TEST_CHAT_ID]):
    print("❌ Faltan variables de entorno:")
    if not TELEGRAM_BOT_TOKEN:
        print("   - TELEGRAM_BOT_TOKEN")
    if not GEMINI_API_KEY:
        print("   - GEMINI_API_KEY")
    if not TEST_CHAT_ID:
        print("   - TEST_CHAT_ID (tu chat ID, obtenlo con @userinfobot)")
    print("\nConfigura las variables y ejecuta de nuevo.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Importar agentes
# ---------------------------------------------------------------------------
from agents.orchestrator import AgentOrchestrator
from agents.chat_agent import ChatAgent
from agents.image_agent import ImageAgent
from agents.video_agent import VideoAgent
from agents.video_pipeline import VideoPipeline
from agents.code_agent import CodeAgent
from agents.design_agent import DesignAgent
from agents.memory import BotMemory

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
print("=" * 60)
print("🧪 TEST SUITE — @leovelabot")
print("=" * 60)

memory = BotMemory()
orchestrator = AgentOrchestrator()

chat_agent = ChatAgent()
image_agent = ImageAgent()
video_agent = VideoAgent()
video_pipeline = VideoPipeline()
code_agent = CodeAgent()
design_agent = DesignAgent()

orchestrator.register_agent("CHAT", chat_agent)
orchestrator.register_agent("IMAGE", image_agent)
orchestrator.register_agent("VIDEO_SHORT", video_agent)
orchestrator.register_agent("VIDEO_LONG", video_pipeline)
orchestrator.register_agent("CODE", code_agent)
orchestrator.register_agent("DESIGN", design_agent)

chat_id = int(TEST_CHAT_ID)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
TESTS = [
    {
        "name": "1. CHAT — Conversación general",
        "message": "¿Qué es C8L Agency? Explícamelo en 2 frases.",
        "expected_type": "text",
        "expected_intent": "CHAT",
    },
    {
        "name": "2. IMAGE — Generación de imagen",
        "message": "Genera una imagen de un león cyberpunk con luces neón",
        "expected_type": "image",
        "expected_intent": "IMAGE",
    },
    {
        "name": "3. CODE — Crear un juego",
        "message": "Crea un juego de Snake en HTML5 jugable en el navegador",
        "expected_type": "file",
        "expected_intent": "CODE",
    },
    {
        "name": "4. DESIGN — Diseñar logo",
        "message": "Diseña un logo para una marca de ropa urbana llamada StreetVibe",
        "expected_type": "image",
        "expected_intent": "DESIGN",
    },
    {
        "name": "5. VIDEO_SHORT — Vídeo corto",
        "message": "Haz un vídeo corto de 15 segundos de un amanecer en la playa",
        "expected_type": "video",
        "expected_intent": "VIDEO_SHORT",
    },
    {
        "name": "6. CLASIFICACIÓN — Detectar código",
        "message": "Escríbeme un script en Python que ordene una lista",
        "expected_type": "text",
        "expected_intent": "CODE",
    },
    {
        "name": "7. CLASIFICACIÓN — Detectar chat",
        "message": "¿Cuál es tu color favorito?",
        "expected_type": "text",
        "expected_intent": "CHAT",
    },
]

results = []


async def run_test(test: dict) -> dict:
    """Ejecuta un test individual."""
    name = test["name"]
    message = test["message"]
    expected_type = test["expected_type"]
    expected_intent = test["expected_intent"]

    print(f"\n{'─' * 50}")
    print(f"🧪 {name}")
    print(f"   📩 \"{message}\"")

    start = time.time()
    try:
        result = await orchestrator.process(message, chat_id, "TestUser")
        elapsed = time.time() - start

        actual_type = result.get("type", "unknown")
        actual_intent = result.get("intent", "unknown")
        content = result.get("content", "")

        # Evaluar resultado
        type_ok = actual_type == expected_type
        intent_ok = actual_intent == expected_intent

        status = "✅ PASS" if (type_ok and intent_ok) else "⚠️ PARTIAL" if intent_ok else "❌ FAIL"

        print(f"   ⏱️ {elapsed:.1f}s")
        print(f"   🎯 Intent: {actual_intent} (esperado: {expected_intent}) {'✅' if intent_ok else '❌'}")
        print(f"   📦 Tipo: {actual_type} (esperado: {expected_type}) {'✅' if type_ok else '❌'}")

        if actual_type == "text":
            preview = str(content)[:150].replace("\n", " ")
            print(f"   💬 Respuesta: \"{preview}...\"")
        elif actual_type == "image":
            print(f"   🖼️ Imagen generada: {len(content)} bytes")
        elif actual_type == "video":
            print(f"   🎬 Vídeo generado: {len(content)} bytes ({len(content)/(1024*1024):.1f} MB)")
        elif actual_type == "file":
            filename = result.get("filename", "?")
            print(f"   📄 Archivo: {filename} ({len(content)} bytes)")

        print(f"   {status}")

        return {
            "name": name,
            "status": status,
            "elapsed": elapsed,
            "intent_ok": intent_ok,
            "type_ok": type_ok,
            "actual_intent": actual_intent,
            "actual_type": actual_type,
        }

    except Exception as e:
        elapsed = time.time() - start
        print(f"   ⏱️ {elapsed:.1f}s")
        print(f"   ❌ ERROR: {e}")
        return {
            "name": name,
            "status": "❌ ERROR",
            "elapsed": elapsed,
            "intent_ok": False,
            "type_ok": False,
            "error": str(e),
        }


async def run_all_tests():
    """Ejecuta todos los tests y muestra un resumen."""
    print(f"\n🚀 Ejecutando {len(TESTS)} tests...\n")

    for test in TESTS:
        result = await run_test(test)
        results.append(result)
        # Pausa entre tests para no saturar la API gratuita
        await asyncio.sleep(2)

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)

    passed = sum(1 for r in results if "PASS" in r["status"])
    partial = sum(1 for r in results if "PARTIAL" in r["status"])
    failed = sum(1 for r in results if "FAIL" in r["status"] or "ERROR" in r["status"])
    total_time = sum(r["elapsed"] for r in results)

    for r in results:
        print(f"  {r['status']} {r['name']} ({r['elapsed']:.1f}s)")

    print(f"\n  Total: {len(results)} tests")
    print(f"  ✅ Passed: {passed}")
    print(f"  ⚠️ Partial: {partial}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏱️ Tiempo total: {total_time:.1f}s")

    # Guardar resultados
    report_path = "test_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 Resultados guardados en: {report_path}")

    if failed > 0:
        print(f"\n  ⚠️ {failed} test(s) fallaron — revisa los errores arriba.")
        sys.exit(1)
    else:
        print(f"\n  🎉 ¡Todos los tests pasaron!")


# ---------------------------------------------------------------------------
# Ejecutar
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test rápido de clasificación (sin llamar a Gemini para cada agente)
    print("\n🔍 Test rápido de clasificación de intenciones...")
    quick_tests = [
        ("Hola, ¿cómo estás?", "CHAT"),
        ("Genera una imagen de un gato", "IMAGE"),
        ("Crea un vídeo de 30 segundos", "VIDEO_SHORT"),
        ("Haz una película de 5 minutos", "VIDEO_LONG"),
        ("Programa un juego de Tetris", "CODE"),
        ("Diseña un banner para YouTube", "DESIGN"),
    ]

    async def quick_classify():
        print()
        for msg, expected in quick_tests:
            intent = await orchestrator.classify_intent(msg)
            ok = "✅" if intent == expected else "❌"
            print(f"  {ok} \"{msg[:40]}\" → {intent} (esperado: {expected})")
        print()

    asyncio.run(quick_classify())

    # Preguntar si ejecutar tests completos (usan API de Gemini)
    print("─" * 60)
    print("⚠️  Los tests completos llaman a la API de Gemini (tier gratuito).")
    print("    Cada test gasta tokens. ¿Continuar?")
    print()
    answer = input("    Ejecutar tests completos? [s/N]: ").strip().lower()

    if answer in ("s", "si", "sí", "y", "yes"):
        asyncio.run(run_all_tests())
    else:
        print("\n  ℹ️ Solo se ejecutó la clasificación rápida. Para tests completos: responde 's'.")
