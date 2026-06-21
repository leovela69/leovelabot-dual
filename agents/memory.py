# -*- coding: utf-8 -*-
"""
Sistema de Memoria y Aprendizaje — Evolución Autónoma.
Permite al bot aprender de cada tarea, recordar preferencias,
y mejorar sus respuestas con el tiempo (estilo Hermes Agent).
"""

import os
import json
import time
import logging
import threading
from collections import defaultdict
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL, TEMP_DIR

logger = logging.getLogger("leovelabot.memory")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_data")


class BotMemory:
    """
    Sistema de memoria persistente y aprendizaje evolutivo.
    
    Tres tipos de memoria:
    1. EPISÓDICA — Recuerda tareas pasadas y sus resultados
    2. SEMÁNTICA — Conocimientos y habilidades aprendidas
    3. PERFIL — Preferencias de cada usuario
    """

    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self._lock = threading.Lock()  # Protege escrituras concurrentes (Telegram + WhatsApp)
        self._episodes_path = os.path.join(MEMORY_DIR, "episodes.json")
        self._skills_path = os.path.join(MEMORY_DIR, "learned_skills.json")
        self._profiles_path = os.path.join(MEMORY_DIR, "user_profiles.json")
        self._evolution_path = os.path.join(MEMORY_DIR, "evolution_log.json")

        self.episodes: list[dict] = self._load(self._episodes_path, [])
        self.skills: list[dict] = self._load(self._skills_path, [])
        self.profiles: dict[str, dict] = self._load(self._profiles_path, {})
        self.evolution_log: list[dict] = self._load(self._evolution_path, [])

        logger.info(
            f"🧠 Memoria cargada: {len(self.episodes)} episodios, "
            f"{len(self.skills)} habilidades, {len(self.profiles)} perfiles"
        )

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _load(self, path: str, default):
        """Carga datos de un archivo JSON."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error cargando {path}: {e}")
        return default

    def _save(self, path: str, data) -> None:
        """Guarda datos en un archivo JSON (thread-safe)."""
        with self._lock:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except IOError as e:
                logger.error(f"Error guardando {path}: {e}")

    def save_all(self) -> None:
        """Persiste toda la memoria a disco (thread-safe)."""
        with self._lock:
            try:
                with open(self._episodes_path, "w", encoding="utf-8") as f:
                    json.dump(self.episodes, f, ensure_ascii=False, indent=2)
                with open(self._skills_path, "w", encoding="utf-8") as f:
                    json.dump(self.skills, f, ensure_ascii=False, indent=2)
                with open(self._profiles_path, "w", encoding="utf-8") as f:
                    json.dump(self.profiles, f, ensure_ascii=False, indent=2)
                with open(self._evolution_path, "w", encoding="utf-8") as f:
                    json.dump(self.evolution_log, f, ensure_ascii=False, indent=2)
            except IOError as e:
                logger.error(f"Error en save_all: {e}")

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
        episode = {
            "timestamp": time.time(),
            "chat_id": chat_id,
            "user_name": user_name,
            "intent": intent,
            "message": user_message[:500],
            "result_type": result_type,
            "success": success,
            "notes": notes,
        }
        self.episodes.append(episode)

        # Mantener máximo 1000 episodios (FIFO)
        if len(self.episodes) > 1000:
            self.episodes = self.episodes[-1000:]

        self._save(self._episodes_path, self.episodes)

    def get_similar_episodes(self, intent: str, limit: int = 5) -> list[dict]:
        """Recupera episodios similares pasados para aprender de ellos."""
        matching = [ep for ep in self.episodes if ep.get("intent") == intent]
        return matching[-limit:]

    # ------------------------------------------------------------------
    # 2. MEMORIA SEMÁNTICA — Habilidades aprendidas
    # ------------------------------------------------------------------
    async def learn_from_task(self, user_message: str, intent: str, result: str, success: bool) -> None:
        """
        Analiza una tarea completada y extrae una habilidad/lección aprendida.
        Usa Gemini para reflexionar sobre la tarea.
        """
        if not success:
            # Aprender de los errores también
            lesson_type = "error_pattern"
        else:
            lesson_type = "skill"

        try:
            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=(
                    f"Eres un sistema de aprendizaje autónomo. Analiza esta tarea completada y extrae "
                    f"UNA lección concisa (máximo 2 frases) que puedas usar para mejorar en el futuro.\n\n"
                    f"Tipo de tarea: {intent}\n"
                    f"Petición del usuario: {user_message[:300]}\n"
                    f"Éxito: {'Sí' if success else 'No'}\n"
                    f"Resultado: {result[:300]}\n\n"
                    f"Lección aprendida:"
                ),
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=150,
                ),
            )

            lesson = response.text.strip()

            skill_entry = {
                "timestamp": time.time(),
                "type": lesson_type,
                "intent": intent,
                "lesson": lesson,
                "trigger_message": user_message[:200],
            }
            self.skills.append(skill_entry)

            # Mantener máximo 200 habilidades
            if len(self.skills) > 200:
                self.skills = self.skills[-200:]

            self._save(self._skills_path, self.skills)
            logger.info(f"📚 Nueva habilidad aprendida [{intent}]: {lesson[:80]}...")

        except Exception as e:
            logger.error(f"Error aprendiendo de tarea: {e}")

    def get_relevant_skills(self, intent: str) -> str:
        """Obtiene habilidades relevantes para un tipo de tarea."""
        relevant = [s for s in self.skills if s.get("intent") == intent]
        if not relevant:
            return ""

        # Tomar las últimas 5 lecciones relevantes
        recent = relevant[-5:]
        lessons = "\n".join([f"- {s['lesson']}" for s in recent])
        return f"\n\nLecciones aprendidas de tareas anteriores similares:\n{lessons}\n"

    # ------------------------------------------------------------------
    # 3. PERFIL DE USUARIO — Preferencias aprendidas
    # ------------------------------------------------------------------
    def update_user_profile(self, chat_id: int, user_name: str, key: str, value: str) -> None:
        """Actualiza una preferencia del usuario."""
        uid = str(chat_id)
        if uid not in self.profiles:
            self.profiles[uid] = {
                "user_name": user_name,
                "first_seen": time.time(),
                "preferences": {},
                "total_messages": 0,
                "favorite_intents": {},
            }

        self.profiles[uid]["preferences"][key] = value
        self.profiles[uid]["user_name"] = user_name
        self._save(self._profiles_path, self.profiles)

    def track_user_interaction(self, chat_id: int, user_name: str, intent: str) -> None:
        """Registra una interacción para aprender patrones del usuario."""
        uid = str(chat_id)
        if uid not in self.profiles:
            self.profiles[uid] = {
                "user_name": user_name,
                "first_seen": time.time(),
                "preferences": {},
                "total_messages": 0,
                "favorite_intents": {},
            }

        profile = self.profiles[uid]
        profile["total_messages"] = profile.get("total_messages", 0) + 1
        profile["last_seen"] = time.time()
        profile["user_name"] = user_name

        intents = profile.get("favorite_intents", {})
        intents[intent] = intents.get(intent, 0) + 1
        profile["favorite_intents"] = intents

        self._save(self._profiles_path, self.profiles)

    def get_user_context(self, chat_id: int) -> str:
        """Genera contexto personalizado basado en el perfil del usuario."""
        uid = str(chat_id)
        profile = self.profiles.get(uid)
        if not profile:
            return ""

        total = profile.get("total_messages", 0)
        name = profile.get("user_name", "Usuario")
        prefs = profile.get("preferences", {})
        fav_intents = profile.get("favorite_intents", {})

        context_parts = [f"\nContexto del usuario {name}:"]
        context_parts.append(f"- Mensajes totales: {total}")

        if fav_intents:
            top_intent = max(fav_intents, key=fav_intents.get)
            context_parts.append(f"- Actividad favorita: {top_intent}")

        if prefs:
            for k, v in list(prefs.items())[:5]:
                context_parts.append(f"- Preferencia '{k}': {v}")

        return "\n".join(context_parts)

    # ------------------------------------------------------------------
    # 4. EVOLUCIÓN — Auto-mejora periódica
    # ------------------------------------------------------------------
    async def evolve(self) -> str:
        """
        Reflexión evolutiva: analiza todos los datos acumulados
        y genera insights de mejora. Llamar periódicamente.
        """
        try:
            stats = {
                "total_episodes": len(self.episodes),
                "total_skills": len(self.skills),
                "total_users": len(self.profiles),
                "success_rate": (
                    sum(1 for ep in self.episodes if ep.get("success"))
                    / max(len(self.episodes), 1)
                    * 100
                ),
                "error_patterns": len([s for s in self.skills if s.get("type") == "error_pattern"]),
            }

            recent_errors = [
                ep for ep in self.episodes[-50:]
                if not ep.get("success")
            ]

            response = _get_client().models.generate_content(
                model=GEMINI_CHAT_MODEL,
                contents=(
                    f"Eres un sistema de auto-mejora para un bot IA. Analiza estas estadísticas "
                    f"y sugiere 3 mejoras concretas y accionables.\n\n"
                    f"Estadísticas:\n{json.dumps(stats, indent=2)}\n\n"
                    f"Errores recientes:\n"
                    + "\n".join([f"- [{e.get('intent')}] {e.get('message', '')[:100]}" for e in recent_errors[:10]])
                    + "\n\nHabilidades aprendidas:\n"
                    + "\n".join([f"- {s['lesson']}" for s in self.skills[-10:]])
                    + "\n\nSugiere 3 mejoras concretas:"
                ),
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=500,
                ),
            )

            evolution_entry = {
                "timestamp": time.time(),
                "stats": stats,
                "improvements": response.text.strip(),
            }
            self.evolution_log.append(evolution_entry)
            self._save(self._evolution_path, self.evolution_log)

            logger.info(f"🧬 Evolución completada: {response.text[:100]}...")
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error en evolución: {e}")
            return f"Error durante la evolución: {e}"

    def get_stats_summary(self) -> str:
        """Resumen de estadísticas para mostrar al admin."""
        total_eps = len(self.episodes)
        success = sum(1 for ep in self.episodes if ep.get("success"))
        rate = (success / max(total_eps, 1)) * 100

        return (
            f"📊 *Estadísticas del Bot*\n\n"
            f"🧠 Episodios registrados: {total_eps}\n"
            f"📚 Habilidades aprendidas: {len(self.skills)}\n"
            f"👥 Usuarios conocidos: {len(self.profiles)}\n"
            f"✅ Tasa de éxito: {rate:.1f}%\n"
            f"🧬 Evoluciones realizadas: {len(self.evolution_log)}"
        )
