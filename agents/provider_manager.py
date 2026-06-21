# agents/provider_manager.py
import os
import time
import threading
from typing import Optional, Dict, List
import google.generativeai as genai
from groq import Groq
import requests

class ProviderManager:
    """Gestor multi-proveedor con failover automático y autoreparación."""
    
    def __init__(self):
        self.providers = self._init_providers()
        self.current_provider = None
        self.failure_counts = {}
        self.lock = threading.Lock()
        self._load_state()
        self._start_health_check()
    
    def _init_providers(self):
        return [
            {
                "name": "gemini_1",
                "type": "gemini",
                "model": "gemini-1.5-flash",
                "key": os.getenv("GEMINI_API_KEY_1"),
                "priority": 1,
                "failures": 0,
                "max_failures": 3,
                "cooldown": 0,
                "healthy": True
            },
            {
                "name": "gemini_2",
                "type": "gemini",
                "model": "gemini-1.5-flash",
                "key": os.getenv("GEMINI_API_KEY_2"),
                "priority": 2,
                "failures": 0,
                "max_failures": 3,
                "cooldown": 0,
                "healthy": True
            },
            {
                "name": "groq",
                "type": "groq",
                "model": "llama-3.1-70b-versatile",
                "key": os.getenv("GROQ_API_KEY"),
                "priority": 3,
                "failures": 0,
                "max_failures": 3,
                "cooldown": 0,
                "healthy": True
            },
            {
                "name": "openrouter",
                "type": "openrouter",
                "model": "google/gemini-1.5-flash",
                "key": os.getenv("OPENROUTER_API_KEY"),
                "priority": 4,
                "failures": 0,
                "max_failures": 3,
                "cooldown": 0,
                "healthy": True
            }
        ]
    
    def get_provider(self):
        """Retorna el mejor proveedor disponible."""
        with self.lock:
            # Filtrar proveedores saludables y en cooldown
            available = [p for p in self.providers 
                        if p["healthy"] and p["cooldown"] <= time.time()]
            
            if not available:
                # Resetear todos los fallos si todos están caídos
                for p in self.providers:
                    p["failures"] = 0
                    p["healthy"] = True
                    p["cooldown"] = 0
                available = self.providers
            
            # Elegir el de mayor prioridad
            provider = sorted(available, key=lambda x: x["priority"])[0]
            self.current_provider = provider
            return provider
    
    def report_failure(self, provider_name: str):
        """Reporta un fallo y cambia de proveedor automáticamente."""
        with self.lock:
            for p in self.providers:
                if p["name"] == provider_name:
                    p["failures"] += 1
                    p["healthy"] = p["failures"] < p["max_failures"]
                    if not p["healthy"]:
                        p["cooldown"] = time.time() + 300  # 5 min de cooldown
                        self._notify_admin(f"⚠️ {p['name']} ha fallado {p['failures']} veces. Cambiando a otro proveedor.")
                    break
    
    def _start_health_check(self):
        """Hilo que verifica la salud de los proveedores cada 2 minutos."""
        def check_loop():
            while True:
                time.sleep(120)
                self._check_all_providers()
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
    
    def _check_all_providers(self):
        """Verifica que los proveedores están vivos."""
        for p in self.providers:
            if not p.get("key"):
                continue
            if p["cooldown"] <= time.time():
                try:
                    # Ping simple al proveedor
                    if p["type"] == "gemini":
                        genai.configure(api_key=p["key"])
                        model = genai.GenerativeModel(p["model"])
                        response = model.generate_content("ping")
                        if response:
                            p["healthy"] = True
                            p["failures"] = 0
                except Exception as e:
                    p["failures"] += 1
                    if p["failures"] >= p["max_failures"]:
                        p["healthy"] = False
                        p["cooldown"] = time.time() + 300
    
    def _notify_admin(self, message: str):
        """Envía notificación al admin via Telegram."""
        try:
            import requests
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("ADMIN_CHAT_ID") or os.getenv("ADMIN_TELEGRAM_ID")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message})
        except:
            pass
    
    def _load_state(self):
        """Carga el estado desde disco."""
        # Para persistencia entre reinicios
        pass

    def _save_state(self):
        """Guarda el estado en disco."""
        # Para persistencia entre reinicios
        pass
