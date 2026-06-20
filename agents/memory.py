# -*- coding: utf-8 -*-
"""
Sistema de Memoria y Aprendizaje — Hermes Evolution Engine.
Usa SQLite para persistencia real entre reinicios.

Tres tipos de memoria:
1. EPISÓDICA — Recuerda tareas pasadas y sus resultados
2. SEMÁNTICA — Conocimientos y habilidades aprendidas
3. PERFIL — Preferencias de cada usuario

Evolución autónoma: analiza patrones, aprende de errores, mejora con el tiempo.
"""

import os
import json
import time
import sqlite3
import logging
import threading
from contextlib import contextmanager
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL, DATABASE_PATH

logger = logging.getLogger("leovelabot.memory")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class BotMemory:
    """
    Sistema de memoria persistente con SQLite y aprendizaje evolutivo.

    Sobrevive a reinicios del servidor. Cada interacción se guarda.
    El bot aprende de sus éxitos y errores.
    """

    def __init__(self):
        # Crear directorio si no existe
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._db_path = DATABASE_PATH
        self._lock = threading.Lock()

        # Inicializar la base de datos
        self._init_db()

        # Cargar conteos para acceso rápido
        self._update_counts()

        logger.info(
            f"🧠 Memoria SQLite cargada: {self.episode_count} episodios, "
            f"{self.skill_count} habilidades, {self.profile_count} perfiles"
        )

    # ------------------------------------------------------------------
    # Propiedades para compatibilidad con el código existente
    # ------------------------------------------------------------------
    @property
    def episodes(self) -> list:
        """Devuelve lista de episodios (para compatibilidad con health check)."""
        return self._get_recent_episodes(100)

    @property
    def skills(self) -> list:
        """Devuelve lista de habilidades (para compatibilidad)."""
        return self._get_all_skills()

    @property
    def profiles(self) -> dict:
        """Devuelve diccionario de perfiles (para compatibilidad)."""
        return self._get_all_profiles()

    # ------------------------------------------------------------------
    # Conexión SQLite (thread-safe)
    # ------------------------------------------------------------------
    @contextmanager
    def _get_conn(self):
        """Context manager para conexiones SQLite thread-safe."""
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Mejor rendimiento concurrente
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Crea las tablas si no existen."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_name TEXT DEFAULT 'Usuario',
                    intent TEXT NOT NULL,
                    message TEXT NOT NULL,
                    result_type TEXT DEFAULT 'text',
                    success INTEGER DEFAULT 1,
                    notes TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    type TEXT DEFAULT 'skill',
                    intent TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    trigger_message TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_profiles (
                    chat_id INTEGER PRIMARY KEY,
                    user_name TEXT DEFAULT 'Usuario',
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    preferences TEXT DEFAULT '{}',
                    favorite_intents TEXT DEFAULT '{}',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    stats TEXT NOT NULL,
                    improvements TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_episodes_chat_id ON episodes(chat_id);
                CREATE INDEX IF NOT EXISTS idx_episodes_intent ON episodes(intent);
                CREATE INDEX IF NOT EXISTS idx_episodes_timestamp ON episodes(timestamp);
                CREATE INDEX IF NOT EXISTS idx_skills_intent ON skills(intent);
            """)

    def _update_counts(self):
        """Actualiza los conteos en memoria para acceso rápido."""
        with self._get_conn() as conn:
            self.episode_count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            self.skill_count = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
            self.profile_count = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]

    # ------------------------------------------------------------------
    # PERSISTENCIA — No necesita save_all (SQLite auto-persiste)
    # ------------------------------------------------------------------
    def save_all(self) -> None:
        """Compatibilidad — SQLite ya persiste automáticamente."""
        self._update_counts()
        logger.info("💾 Memoria sincronizada (SQLite)")

    # ------------------------------------------------------------------
    # 1. MEMORIA EPISÓDICA — Recordar tareas pasadas
    # ------------------------------------------------------------------
    def record_episode(
        self,
        chat_id: int,
        user_name: str,
        intent: str,
        user_message: str,
        result_type: str,
        success: bool,
        notes: str = "",
    ) -> None:
        """Registra un episodio (tarea completada) en la memoria."""
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """INSERT INTO episodes (timestamp, chat_id, user_name, intent, message, result_type, success, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (time.time(), chat_id, user_name, intent, user_message[:500], result_type, int(success), notes),
                )
            self.episode_count += 1

    def get_similar_episodes(self, intent: str, limit: int = 5) -> list[dict]:
        """Recupera episodios similares pasados para aprender de ellos."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM episodes WHERE intent = ? ORDER BY timestamp DESC LIMIT ?",
                (intent, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def _get_recent_episodes(self, limit: int = 100) -> list[dict]:
        """Obtiene los episodios más recientes."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # 2. MEMORIA SEMÁNTICA — Habilidades aprendidas
    # ------------------------------------------------------------------
    async def learn_from_task(self, user_message: str, intent: str, result: str, success: bool) -> None:
        """
        Analiza una tarea completada y extrae una lección aprendida.
        Usa Gemini para reflexionar sobre la tarea.
        """
        lesson_type = "error_pattern" if not success else "skill"

        try:
            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=(
                    f"Eres un sistema de aprendizaje autónomo. Analiza esta tarea y extrae "
                    f"UNA lección concisa (máximo 2 frases) para mejorar en el futuro.\n\n"
                    f"Tipo: {intent}\n"
                    f"Petición: {user_message[:300]}\n"
                    f"Éxito: {'Sí' if success else 'No'}\n"
                    f"Resultado: {result[:300]}\n\n"
                    f"Lección:"
                ),
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=150,
                ),
            )

            lesson = response.text.strip()

            with self._lock:
                with self._get_conn() as conn:
                    conn.execute(
                        """INSERT INTO skills (timestamp, type, intent, lesson, trigger_message)
                           VALUES (?, ?, ?, ?, ?)""",
                        (time.time(), lesson_type, intent, lesson, user_message[:200]),
                    )
                self.skill_count += 1

            logger.info(f"📚 Nueva habilidad [{intent}]: {lesson[:80]}...")

        except Exception as e:
            logger.error(f"Error aprendiendo de tarea: {e}")

    def get_relevant_skills(self, intent: str) -> str:
        """Obtiene habilidades relevantes para un tipo de tarea."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT lesson FROM skills WHERE intent = ? ORDER BY timestamp DESC LIMIT 5",
                (intent,),
            ).fetchall()

        if not rows:
            return ""

        lessons = "\n".join([f"- {row['lesson']}" for row in rows])
        return f"\nLecciones aprendidas de tareas similares:\n{lessons}\n"

    def _get_all_skills(self) -> list[dict]:
        """Obtiene todas las habilidades."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM skills ORDER BY timestamp DESC LIMIT 200").fetchall()
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # 3. PERFIL DE USUARIO — Preferencias aprendidas
    # ------------------------------------------------------------------
    def update_user_profile(self, chat_id: int, user_name: str, key: str, value: str) -> None:
        """Actualiza una preferencia del usuario."""
        with self._lock:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT preferences FROM user_profiles WHERE chat_id = ?", (chat_id,)
                ).fetchone()

                if row:
                    prefs = json.loads(row["preferences"])
                    prefs[key] = value
                    conn.execute(
                        "UPDATE user_profiles SET preferences = ?, user_name = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                        (json.dumps(prefs, ensure_ascii=False), user_name, chat_id),
                    )
                else:
                    prefs = {key: value}
                    conn.execute(
                        """INSERT INTO user_profiles (chat_id, user_name, first_seen, last_seen, total_messages, preferences, favorite_intents)
                           VALUES (?, ?, ?, ?, 0, ?, '{}')""",
                        (chat_id, user_name, time.time(), time.time(), json.dumps(prefs, ensure_ascii=False)),
                    )

    def track_user_interaction(self, chat_id: int, user_name: str, intent: str) -> None:
        """Registra una interacción para aprender patrones del usuario."""
        with self._lock:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT total_messages, favorite_intents FROM user_profiles WHERE chat_id = ?",
                    (chat_id,),
                ).fetchone()

                if row:
                    total = row["total_messages"] + 1
                    intents = json.loads(row["favorite_intents"])
                    intents[intent] = intents.get(intent, 0) + 1
                    conn.execute(
                        """UPDATE user_profiles 
                           SET total_messages = ?, last_seen = ?, user_name = ?, 
                               favorite_intents = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE chat_id = ?""",
                        (total, time.time(), user_name, json.dumps(intents), chat_id),
                    )
                else:
                    intents = {intent: 1}
                    conn.execute(
                        """INSERT INTO user_profiles (chat_id, user_name, first_seen, last_seen, total_messages, preferences, favorite_intents)
                           VALUES (?, ?, ?, ?, 1, '{}', ?)""",
                        (chat_id, user_name, time.time(), time.time(), json.dumps(intents)),
                    )
                    self.profile_count += 1

    def get_user_context(self, chat_id: int) -> str:
        """Genera contexto personalizado basado en el perfil del usuario."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM user_profiles WHERE chat_id = ?", (chat_id,)
            ).fetchone()

        if not row:
            return ""

        total = row["total_messages"]
        name = row["user_name"]
        prefs = json.loads(row["preferences"])
        fav_intents = json.loads(row["favorite_intents"])

        context_parts = [f"\n👤 Contexto de {name}:"]
        context_parts.append(f"- Mensajes totales: {total}")

        if fav_intents:
            top_intent = max(fav_intents, key=fav_intents.get)
            context_parts.append(f"- Actividad favorita: {top_intent}")

        if prefs:
            for k, v in list(prefs.items())[:5]:
                context_parts.append(f"- Preferencia '{k}': {v}")

        return "\n".join(context_parts)

    def _get_all_profiles(self) -> dict:
        """Obtiene todos los perfiles como diccionario."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM user_profiles").fetchall()
            return {str(row["chat_id"]): dict(row) for row in rows}

    # ------------------------------------------------------------------
    # 4. EVOLUCIÓN — Auto-mejora periódica
    # ------------------------------------------------------------------
    async def evolve(self) -> str:
        """
        Reflexión evolutiva: analiza datos acumulados y genera insights.
        Llamar periódicamente o con /evolve.
        """
        try:
            # Recopilar estadísticas
            with self._get_conn() as conn:
                total_eps = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
                success_count = conn.execute("SELECT COUNT(*) FROM episodes WHERE success = 1").fetchone()[0]
                total_skills = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
                total_users = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]
                error_patterns = conn.execute("SELECT COUNT(*) FROM skills WHERE type = 'error_pattern'").fetchone()[0]

                # Errores recientes
                recent_errors = conn.execute(
                    "SELECT intent, message FROM episodes WHERE success = 0 ORDER BY timestamp DESC LIMIT 10"
                ).fetchall()

                # Habilidades recientes
                recent_skills = conn.execute(
                    "SELECT lesson FROM skills ORDER BY timestamp DESC LIMIT 10"
                ).fetchall()

            stats = {
                "total_episodes": total_eps,
                "total_skills": total_skills,
                "total_users": total_users,
                "success_rate": (success_count / max(total_eps, 1)) * 100,
                "error_patterns": error_patterns,
            }

            errors_text = "\n".join(
                [f"- [{dict(e)['intent']}] {dict(e)['message'][:100]}" for e in recent_errors]
            )
            skills_text = "\n".join([f"- {dict(s)['lesson']}" for s in recent_skills])

            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=(
                    f"Eres un sistema de auto-mejora para un bot IA llamado Hermes. "
                    f"Analiza estas estadísticas y sugiere 3 mejoras concretas y accionables.\n\n"
                    f"Estadísticas:\n{json.dumps(stats, indent=2)}\n\n"
                    f"Errores recientes:\n{errors_text}\n\n"
                    f"Habilidades aprendidas:\n{skills_text}\n\n"
                    f"Sugiere 3 mejoras concretas (en español, estilo directo):"
                ),
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=500,
                ),
            )

            improvements = response.text.strip()

            # Guardar la evolución
            with self._lock:
                with self._get_conn() as conn:
                    conn.execute(
                        "INSERT INTO evolution_log (timestamp, stats, improvements) VALUES (?, ?, ?)",
                        (time.time(), json.dumps(stats), improvements),
                    )

            logger.info(f"🧬 Evolución completada: {improvements[:100]}...")
            self._update_counts()
            return improvements

        except Exception as e:
            logger.error(f"Error en evolución: {e}")
            return f"Error durante la evolución: {e}"

    def get_stats_summary(self) -> str:
        """Resumen de estadísticas para mostrar al usuario."""
        with self._get_conn() as conn:
            total_eps = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            success = conn.execute("SELECT COUNT(*) FROM episodes WHERE success = 1").fetchone()[0]
            total_skills = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
            total_users = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]
            evolutions = conn.execute("SELECT COUNT(*) FROM evolution_log").fetchone()[0]

        rate = (success / max(total_eps, 1)) * 100

        return (
            f"📊 *Estadísticas de Hermes*\n\n"
            f"🧠 Episodios registrados: {total_eps}\n"
            f"📚 Habilidades aprendidas: {total_skills}\n"
            f"👥 Usuarios conocidos: {total_users}\n"
            f"✅ Tasa de éxito: {rate:.1f}%\n"
            f"🧬 Evoluciones realizadas: {evolutions}\n"
            f"💾 Base de datos: SQLite (persistente)"
        )
