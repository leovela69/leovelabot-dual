# 🦁 @leovelabot — Bot Multi-Agente IA con Aprendizaje Evolutivo

Bot de Telegram para C8L Agency con **6 agentes IA especializados** y un sistema de **memoria y aprendizaje evolutivo** inspirado en Hermes Agent.

## ✨ Características

- 🔓 **Abierto para todos** — Sin códigos, sin registro, sin restricciones
- 💬 **Chat IA** — Conversación con personalidad C8L cyberpunk
- 🎨 **Generación de imágenes** — Crea cualquier imagen desde texto
- 🎬 **Vídeos cortos** — Genera clips de ~20 segundos
- 📹 **Vídeos largos** — Pipeline completo de hasta 20 minutos
- 💻 **Programador** — Crea juegos HTML5, scripts, aplicaciones
- 🎯 **Diseñador** — Logos, banners, UI con estilo C8L
- 🧠 **Aprendizaje evolutivo** — Aprende de cada tarea y mejora solo
- 📊 **Memoria persistente** — Recuerda usuarios, preferencias y habilidades
- 🔔 **Notificación de admin** — Te avisa por Telegram cuando arranca

## 🏗️ Arquitectura

```
bot.py                      ← Gateway de Telegram
├── config.py               ← Configuración centralizada
└── agents/
    ├── orchestrator.py     ← 🧠 Router de intenciones (Gemini)
    ├── chat_agent.py       ← 💬 Conversación con memoria
    ├── image_agent.py      ← 🎨 Generación de imágenes
    ├── video_agent.py      ← 🎬 Vídeos cortos (imágenes + FFmpeg)
    ├── video_pipeline.py   ← 📹 Vídeos largos (guión → escenas → composición)
    ├── code_agent.py       ← 💻 Programación y videojuegos
    ├── design_agent.py     ← 🎯 Diseños C8L
    └── memory.py           ← 🧠 Memoria + aprendizaje evolutivo
```

## 🚀 Ejecución local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Instalar FFmpeg (necesario para vídeos)
# Windows: winget install FFmpeg
# macOS:   brew install ffmpeg
# Linux:   apt install ffmpeg

# 3. Configurar variables de entorno
export TELEGRAM_BOT_TOKEN="tu_token_de_botfather"
export GEMINI_API_KEY="tu_api_key_de_google_ai_studio"
export ADMIN_CHAT_ID="tu_chat_id_de_telegram"

# 4. Arrancar el bot
python bot.py
```

## 🔑 Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token de [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | ✅ | API key de [Google AI Studio](https://aistudio.google.com/) (gratis) |
| `ADMIN_CHAT_ID` | Recomendado | Tu chat ID para recibir notificaciones |
| `HEALTH_PORT` | No | Puerto del health-check (default: 8080) |
| `TEMP_DIR` | No | Directorio temporal para vídeos |

### ¿Cómo obtener tu ADMIN_CHAT_ID?

1. Abre Telegram y busca `@userinfobot`
2. Envíale `/start`
3. Te responderá con tu **ID** — ese es tu chat ID

## 🧠 Sistema de Aprendizaje

El bot tiene 3 tipos de memoria:

1. **Episódica** — Recuerda cada tarea que completa (éxito/error)
2. **Semántica** — Extrae lecciones de cada tarea para mejorar
3. **Perfil de usuario** — Aprende tus preferencias y patrones

Cada 100 tareas, el bot ejecuta una **evolución automática**: analiza todos sus datos y genera mejoras concretas.

Puedes forzar una evolución manual con `/evolve` y ver las estadísticas con `/stats`.

## 🐳 Despliegue en Render (gratis)

1. Sube todo a un repositorio de GitHub
2. En [Render.com](https://render.com), crea un nuevo **Blueprint**
3. Conecta tu repositorio
4. Configura los secretos (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `ADMIN_CHAT_ID`)
5. ¡Deploy! El bot se ejecutará 24/7 como worker

## 💰 Costes

| Componente | Coste |
|------------|-------|
| Telegram Bot API | **Gratis** |
| Gemini Flash (chat, routing, código) | **Gratis** (tier gratuito) |
| Gemini Image Generation | **Gratis** (tier gratuito, con límites diarios) |
| FFmpeg (composición de vídeo) | **Gratis** (open source) |
| Render (hosting) | **Gratis** (tier worker) |
