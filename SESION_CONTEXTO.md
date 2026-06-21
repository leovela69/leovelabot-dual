# CONTEXTO DE SESIÓN — C8L AGENT / @leovelabot
## Fecha: 21 junio 2026

## RESUMEN DEL PROYECTO
- **Repo:** https://github.com/leovela69/leovelabot-dual
- **Propietario:** leovela69 (Leo Vela)
- **Bot Telegram token:** 8557275735:AAFfSXMaxjnSOSJmu-QtN00sZUAwSwIK6Uo
- **Tipo:** Bot multi-agente para C8L Agency (producción musical + gaming + IA)
- **Stack:** Python + pyTelegramBotAPI + google-genai (Gemini) + Flask + FFmpeg
- **Deploy:** Render.com con Docker

## ARQUITECTURA
- `whatsapp_bot.py` — Punto de entrada principal (Flask + Telegram en hilo)
- `bot.py` — Bot Telegram standalone (también importable)
- `agents/orchestrator.py` — Clasifica intención y enruta al agente correcto
- `agents/chat_agent.py` — Conversación general con Gemini Flash
- `agents/image_agent.py` — Generación de imágenes con Gemini
- `agents/video_agent.py` — Vídeos cortos (imágenes + FFmpeg)
- `agents/video_pipeline.py` — Vídeos largos (hasta 20 min)
- `agents/code_agent.py` — Programación y juegos HTML5
- `agents/design_agent.py` — Diseños con estética C8L
- `agents/memory.py` — Sistema de memoria/aprendizaje evolutivo

## FIXES APLICADOS (PR #3)
1. No crash sin WhatsApp vars → flag WHATSAPP_ENABLED
2. Puerto unificado a PORT=8080
3. bot.py no crashea al ser importado (guard _is_main)
4. Dockerfile y render.yaml actualizados

## LO QUE FALTA POR HACER
- [ ] Probar bot en vivo con Telegram API
- [ ] Verificar generación de imágenes
- [ ] Verificar generación de vídeos
- [ ] Verificar code agent (juegos HTML)
- [ ] Verificar design agent
- [ ] Verificar chat conversacional
- [ ] Verificar sistema de memoria
- [ ] Fix de cualquier error encontrado en pruebas

## VARIABLES DE ENTORNO NECESARIAS
- TELEGRAM_BOT_TOKEN=8557275735:AAFfSXMaxjnSOSJmu-QtN00sZUAwSwIK6Uo
- GEMINI_API_KEY=(necesaria — Google AI Studio gratuita)
- ADMIN_CHAT_ID=(chat ID de Leo)

## NOTAS
- El sandbox de Kiro tiene modo INTEGRATIONS_ONLY (sin internet externa)
- Para probar el bot en vivo necesito acceso a api.telegram.org
- El bot usa Gemini 2.5 Flash (tier gratuito) para todo
