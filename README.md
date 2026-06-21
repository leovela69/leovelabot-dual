# C8L AGENT v15.4 — "CUSTODIO DEFINITIVO"

Sistema de agentes de IA autonomo para C8L Agency.
44 bots especializados, vigilancia 24/7, musica Bolero-House, auto-reparacion.

## Despliegue rapido (Railway)

1. Fork este repo
2. Crea proyecto en Railway y conecta el repo
3. Agrega las variables de entorno (ver .env.example)
4. Railway despliega automaticamente con el Dockerfile

## Configuracion

1. Crear bot en Telegram con @BotFather
2. Crear proyecto en Supabase y ejecutar sql/schema.sql
3. Obtener API keys gratuitas:
   - Google AI Studio (Gemini): https://aistudio.google.com
   - Groq: https://console.groq.com
   - Jina AI: https://jina.ai
   - Serper: https://serper.dev
   - HuggingFace: https://huggingface.co/settings/tokens
4. Configurar webhook de Telegram al URL de Railway

## Comandos disponibles

- /start - Bienvenida
- /help - Ayuda
- /stats - Estadisticas
- /bots - Lista de bots activos
- /custodio estado - Estado de la web
- /custodio musica - Generar musica Bolero-House
- /custodio contenido - Ver contenido pendiente
- /custodio metricas - Metricas de la web

## Costo: $0.00/mes (100% servicios gratuitos)
