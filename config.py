"""Configuracion central del sistema C8L AGENT v15.4"""

import os
from dotenv import load_dotenv

load_dotenv()


# === TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")

# === GEMINI (rotacion de keys) ===
GEMINI_KEYS = [
    os.getenv(f"GEMINI_API_KEY_{i}", "") for i in range(1, 6)
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]  # Filtrar vacias
GEMINI_API_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else os.getenv("GEMINI_API_KEY", "")

# === GROQ (rotacion de keys) ===
GROQ_KEYS = [
    os.getenv(f"GROQ_API_KEY_{i}", "") for i in range(1, 4)
]
GROQ_KEYS = [k for k in GROQ_KEYS if k]

# === SUPABASE ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# === REDIS ===
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")

# === BUSQUEDA WEB ===
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
BRAVE_SEARCH_KEY = os.getenv("BRAVE_SEARCH_KEY", "")

# === HUGGING FACE ===
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# === EMBEDDINGS ===
JINA_API_KEY = os.getenv("JINA_API_KEY", "")

# === DEPLOY ===
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
WEB_REPO = os.getenv("WEB_REPO", "leovela69/c8lagency-web")

# === OPENROUTER ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# === WEB C8L ===
WEB_URL = os.getenv("WEB_URL", "https://c8lagency.com")
WEB_SITEMAP = os.getenv("WEB_SITEMAP", "https://c8lagency.com/sitemap.xml")

# === CONFIG GENERAL ===
TIMEZONE = os.getenv("TIMEZONE", "America/Mexico_City")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "8"))
AUDIT_INTERVAL_HOURS = int(os.getenv("AUDIT_INTERVAL_HOURS", "6"))
PING_INTERVAL_MINUTES = int(os.getenv("PING_INTERVAL_MINUTES", "5"))

# === RATE LIMITS ===
MAX_REQUESTS_PER_HOUR = 60
MAX_MESSAGE_LENGTH = 5000

# === MODELOS POR DEFECTO ===
MODELO_COORDINACION = "gemini-flash"
MODELO_COMPLEJO = "gemini-pro"
MODELO_EJECUCION = "groq"
MODELO_FALLBACK = "openrouter"

# === AGENT CONFIGURATION ===
TEMP_DIR = os.getenv("TEMP_DIR", "temp")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002")
GEMINI_CODE_MODEL = os.getenv("GEMINI_CODE_MODEL", "gemini-1.5-pro")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Eres Leo, el asistente oficial de C8L Agency.")
MAX_HISTORY_PER_USER = int(os.getenv("MAX_HISTORY_PER_USER", "10"))
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
SCENE_DURATION_SECONDS = int(os.getenv("SCENE_DURATION_SECONDS", "5"))
MAX_VIDEO_DURATION_MINUTES = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "20"))
MAX_SCENES_PER_VIDEO = int(os.getenv("MAX_SCENES_PER_VIDEO", "240"))
