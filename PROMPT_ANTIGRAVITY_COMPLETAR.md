# PROMPT PARA ANTIGRAVITY — COMPLETAR C8L AGENT v15.4
# Copiar y pegar DIRECTO en Antigravity

---

Ya tengo el proyecto C8L AGENT v15.4 "CUSTODIO DEFINITIVO" parcialmente construido.
Son 80 archivos creados con código funcional. Necesito que COMPLETES lo que falta
y CONECTES todo para que funcione como un sistema unificado.

## LO QUE YA ESTÁ HECHO (no reescribir, solo completar lo que falta):

80 archivos ya creados en esta estructura:


```
c8l-agent/
├── bot.py                          ✅ FastAPI + webhook + scheduler
├── config.py                       ✅ Todas las variables de entorno
├── requirements.txt                ✅ Dependencias completas
├── Dockerfile                      ✅ Multi-stage build
├── railway.toml                    ✅ Config Railway + healthcheck
├── .env.example                    ✅ Todas las API keys necesarias
├── README.md                       ✅ Instrucciones de deploy
│
├── core/
│   ├── __init__.py                 ✅
│   ├── gateway.py                  ✅ Procesa mensajes, clasifica, rutea
│   ├── reflejo.py                  ✅ Cache L1/L2 + predefinidas
│   ├── contexto.py                 ✅ Context Thread (hilo conversacional)
│   ├── genesis.py                  ✅ Busca o crea bots
│   ├── guardian.py                 ✅ Ética + bloqueo de órdenes maliciosas
│   ├── juez.py                     ✅ Evaluador 0 tokens (métricas reales)
│   ├── handshake.py                ✅ Confirma antes si tarea es cara
│   └── evolucion.py                ✅ Ciclo de evolución (modo sueño)
│
├── memoria/
│   ├── __init__.py                 ✅
│   ├── supabase.py                 ✅ Cliente Supabase + CRUD
│   ├── redis.py                    ✅ Cliente Redis + mensajes entre bots
│   ├── arquetipos.py               ✅ Compresión de tareas
│   ├── olvido.py                   ✅ Limpieza de datos obsoletos
│   └── proyectos.py                ✅ Gestión de proyectos + versiones + fork
│
├── bots/
│   ├── __init__.py                 ✅
│   ├── base.py                     ✅ BotBase + REGISTRY + ciclo de vida
│   ├── architecto.py               ✅ Coordinador
│   ├── sabio.py                    ✅ Intérprete
│   ├── memorion.py                 ✅ Memoria (búsqueda por similitud)
│   ├── frontend.py                 ✅ HTML + Tailwind
│   ├── backend.py                  ✅ Python/Node APIs
│   ├── css.py                      ✅ CSS avanzado
│   ├── javascript.py               ✅ JS vanilla
│   ├── react.py                    ✅ React + Vue
│   ├── sql.py                      ✅ Bases de datos
│   ├── copywriting.py              ✅ Textos persuasivos
│   ├── seo.py                      ✅ SEO + meta tags
│   ├── deployer.py                 ✅ Deploy Vercel/Cloudflare/Railway
│   ├── centinela.py                ✅ Monitoreo URLs
│   ├── cronos.py                   ✅ Tareas programadas
│   ├── linter.py                   ✅ Validación de código (0 IA)
│   ├── security.py                 ✅ Escaneo vulnerabilidades (0 IA)
│   ├── merger.py                   ✅ Une resultados de equipos
│   ├── evolucion_bot.py            ✅ Evolución Darwiniana de prompts
│   ├── herrero.py                  ✅ Crea herramientas para otros bots
│   ├── profeta.py                  ✅ Predice necesidades del usuario
│   ├── archivista.py               ✅ Knowledge base estructurada
│   ├── fantasma.py                 ✅ Entrenamiento 24/7
│   ├── despertador.py              ✅ Health checking
│   ├── espia.py                    ✅ Tendencias tech
│   ├── mercenario.py               ✅ Todoterreno urgencias
│   ├── diplomatico.py              ✅ Humaniza respuestas
│   ├── guardian_bot.py             ✅ Bot de seguridad
│   ├── frankenstein.py             ✅ Fusión de bots
│   ├── enjambre.py                 ✅ Modo enjambre (clonación masiva)
│   ├── sindicato.py                ✅ Resolución colectiva de fallos
│   ├── contrato.py                 ✅ Reputación entre bots
│   ├── musica_corrector.py         ✅ Diagnóstico fallos Suno/Udio
│   ├── videoclip.py                ✅ Genera prompts de videoclip
│   ├── tutor.py                    ✅ Modo tutor (explica paso a paso)
│   ├── pair.py                     ✅ Pair programming
│   ├── fabrica.py                  ✅ Bot Factory (crea bots nuevos)
│   │
│   └── custodio/
│       ├── __init__.py             ✅
│       ├── main.py                 ✅ Orquestador de comandos /custodio
│       ├── vigia.py                ✅ Monitoreo web cada 5 min
│       ├── medico.py               ✅ Reparación + rollback
│       ├── creador.py              ✅ Genera contenido + música
│       ├── analista.py             ✅ Métricas + diagnóstico
│       ├── aprendiz.py             ✅ Aprendizaje + limpieza
│       ├── notificador.py          ✅ Reportes a Leo Vela
│       └── prompts.py              ✅ Prompts Bolero-House
│
├── ejecutores/
│   ├── __init__.py                 ✅
│   ├── caliente.py                 ✅ Groq + Gemini Flash + Gemini Pro
│   └── frio.py                     ✅ HuggingFace + OpenRouter + imágenes
│
├── salida/
│   ├── __init__.py                 ✅
│   ├── formato.py                  ✅ Formato Telegram Markdown
│   └── storage.py                  ✅ Supabase Storage upload
│
├── telegram/
│   ├── __init__.py                 ✅
│   ├── handlers.py                 ✅ Envío de mensajes
│   └── comandos.py                 ✅ 12 comandos (/start, /help, /bots...)
│
├── scripts/
│   ├── crear_bots_iniciales.py     ✅ Carga los 44 bots al arrancar
│   └── resetear_sistema.py         ✅ Reset cache + reload
│
├── sql/
│   ├── schema.sql                  ✅ 9 tablas principales
│   ├── schema_custodio.sql         ✅ 5 tablas del Custodio
│   └── schema_musica.sql           ✅ 4 tablas de música + tendencias
│
└── templates/
    ├── articulo_blog.md            ✅ Plantilla de artículo SEO
    ├── estructura_cancion.md       ✅ Estructura Bolero-House
    └── prompt_musica.txt           ✅ Prompts estándar Suno/Udio
```

## LO QUE FALTA COMPLETAR:

1. **Conectar `bot.py` con `scripts/crear_bots_iniciales.py`**
   - Al arrancar (en lifespan), debe llamar a `cargar_todos_los_bots()`
   - Esto registra los 44 bots en el REGISTRY en memoria

2. **Agregar función `registrar_bot_genesis` en `core/genesis.py`**
   - `bots/fabrica.py` importa `from core.genesis import registrar_bot_genesis`
   - Necesita existir esa función (guardar bot nuevo en Supabase)

3. **Agregar estas líneas al inicio de `bot.py` (después de imports):**
   ```python
   from scripts.crear_bots_iniciales import cargar_todos_los_bots
   cargar_todos_los_bots()
   ```

4. **Completar los archivos `__init__.py` faltantes:**
   - `scripts/__init__.py`
   - `templates/__init__.py` (no necesario pero limpio)

5. **Agregar al `bot.py` un import del reporte diario:**
   ```python
   from bots.custodio.notificador import reporte_diario
   scheduler.add_job(reporte_diario, "cron", hour=config.DAILY_REPORT_HOUR, id="reporte_diario")
   ```

6. **Agregar al `bot.py` el job del Fantasma:**
   ```python
   from bots.fantasma import bot_fantasma
   async def ciclo_fantasma():
       # Solo si no hay usuarios activos (simplificado: ejecutar de 0-6am)
       resultado = await bot_fantasma.ejecutar("entrenamiento", {})
   scheduler.add_job(ciclo_fantasma, "interval", minutes=30, id="fantasma")
   ```

7. **Crear archivos faltantes que otros importan pero no existen:**
   - `bots/images.py` (bot_images para generación de imágenes con HuggingFace)
   - `bots/audio.py` (bot_audio para TTS)

## LO QUE DEBES HACER ADICIONAL:

8. **Tests básicos** — Crear `tests/test_bot.py` con:
   - Test de que todos los bots se cargan sin error
   - Test de que el clasificador funciona
   - Test de que el Guardian bloquea órdenes maliciosas
   - Test de que el cache L1 funciona

9. **Verificar imports circulares** — Revisar que no haya imports circulares entre módulos.

10. **Agregar manejo de errores global** en `bot.py`:
    ```python
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Error global: {exc}")
        return JSONResponse({"ok": True})
    ```

## CONTEXTO TÉCNICO:

- Lenguaje: Python 3.11+
- Framework: FastAPI + uvicorn
- Async: asyncio + httpx para todas las llamadas HTTP
- DB: Supabase (PostgreSQL) + Upstash Redis
- IA: Gemini Flash/Pro + Groq (Llama 3.1) + HuggingFace + OpenRouter
- Deploy: Railway (Dockerfile)
- Comunicación: Telegram Bot API (webhook)
- Scheduler: APScheduler (async)
- Logging: loguru

## INSTRUCCIONES FINALES:

1. Lee todos los archivos existentes para entender la estructura.
2. Completa los puntos 1-10 listados arriba.
3. Verifica que todo compile sin errores (python -c "import bot").
4. Asegúrate de que `uvicorn bot:app` arranque sin crash.
5. Genera el archivo `tests/test_bot.py` con tests básicos.
6. NO reescribas archivos que ya funcionan. Solo completa lo que falta.

COMPLETA EL PROYECTO. HAZLO FUNCIONAL AL 100%.
