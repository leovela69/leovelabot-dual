"""Bot Fábrica: Crea nuevos bots bajo demanda usando lógica genesis.

Bot Factory helper que genera nuevos bots dinámicamente según las
necesidades del usuario. Utiliza el módulo core.genesis para crear
bots con prompts, keywords y configuraciones optimizadas.
"""

from bots.base import BotBase, registrar_bot_en_memoria
from typing import Dict, Any
from loguru import logger


class BotFabrica(BotBase):
    """Fábrica de bots: crea nuevos bots bajo demanda.

    Especializado en:
    - Análisis de necesidades para determinar qué bot crear
    - Generación de prompts compilados optimizados
    - Asignación de modelo adecuado según tarea
    - Selección de keywords relevantes
    - Registro automático del nuevo bot en el sistema
    """


    async def ejecutar(self, texto: str, contexto: Dict[str, Any], retry: bool = False) -> str:
        """Ejecuta creación de un nuevo bot."""
        logger.info("🏭 Fábrica: analizando solicitud de nuevo bot...")
        self.ultima_actividad = __import__("time").time()

        # Paso 1: Obtener especificación del nuevo bot via IA
        prompt_spec = self._construir_prompt_especificacion(texto, contexto, retry)

        try:
            especificacion = await self._llamar_modelo(prompt_spec)

            # Paso 2: Parsear especificación y crear bot
            nuevo_bot = self._crear_bot_desde_spec(especificacion, texto)

            if nuevo_bot:
                # Paso 3: Registrar en genesis y memoria
                await self._registrar_nuevo_bot(nuevo_bot)
                self.tareas_completadas += 1
                self._actualizar_score(exito=True)
                return self._formatear_resultado(nuevo_bot, especificacion)
            else:
                # Si no se pudo parsear, devolver la especificación raw
                self.tareas_completadas += 1
                return f"📋 Especificación generada:\n\n{especificacion}"

        except Exception as e:
            logger.error(f"Error en Fábrica: {e}")
            self.fallos += 1
            self._actualizar_score(exito=False)
            return f"Error creando bot: {str(e)}"


    def _construir_prompt_especificacion(
        self, texto: str, contexto: Dict[str, Any], retry: bool
    ) -> str:
        """Construye prompt para generar la especificación del nuevo bot."""
        parts = [self.prompt_compiled]

        parts.append(
            "\nGenera la especificación de un nuevo bot con este formato EXACTO:"
            "\nNOMBRE: [nombre del bot]"
            "\nID: bot_[id_snake_case]"
            "\nESPECIALIDAD: [descripción de una línea]"
            "\nKEYWORDS: [palabra1, palabra2, palabra3, ...]"
            "\nMODELO: [groq|gemini-flash|gemini-pro|huggingface]"
            "\nPROMPT: [prompt compilado de ~60 tokens, directo y accionable]"
            "\nHERRAMIENTAS: [herramienta1, herramienta2, ...]"
        )

        if contexto.get("proyecto_activo"):
            parts.append(f"\nProyecto activo: {contexto['proyecto_activo']}")

        parts.append(f"\nSolicitud del usuario: {texto}")

        if retry:
            parts.append(
                "\n[El bot anterior no fue útil. Crea uno más especializado "
                "y con mejor prompt.]"
            )

        return "\n".join(parts)


    def _crear_bot_desde_spec(self, especificacion: str, texto_original: str):
        """Parsea la especificación y crea un BotBase."""
        try:
            lines = especificacion.strip().split("\n")
            spec = {}

            for line in lines:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    spec[key.strip().upper()] = value.strip()

            # Validar campos mínimos
            nombre = spec.get("NOMBRE", "").strip()
            bot_id = spec.get("ID", "").strip()
            especialidad = spec.get("ESPECIALIDAD", "").strip()

            if not all([nombre, bot_id, especialidad]):
                logger.warning("Fábrica: Especificación incompleta")
                return None

            # Parsear keywords
            keywords_raw = spec.get("KEYWORDS", "")
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

            # Parsear herramientas
            herramientas_raw = spec.get("HERRAMIENTAS", "")
            herramientas = [
                h.strip() for h in herramientas_raw.split(",") if h.strip()
            ]

            # Modelo
            modelo = spec.get("MODELO", "groq").strip().lower()
            if modelo not in ["groq", "gemini-flash", "gemini-pro", "huggingface"]:
                modelo = "groq"

            # Prompt
            prompt = spec.get("PROMPT", f"Bot especializado en {especialidad}.")

            nuevo_bot = BotBase(
                id=bot_id,
                nombre=nombre,
                especialidad=especialidad,
                keywords=keywords,
                prompt_compiled=prompt,
                modelo=modelo,
                herramientas=herramientas,
                estado="novato",
                score=3.0,
                padre_id=self.id,
            )

            return nuevo_bot

        except Exception as e:
            logger.error(f"Error parseando especificación: {e}")
            return None


    async def _registrar_nuevo_bot(self, nuevo_bot: BotBase):
        """Registra el nuevo bot en memoria y en genesis."""
        # Registrar en memoria local
        registrar_bot_en_memoria(nuevo_bot)

        # Intentar registrar en genesis (persistencia)
        try:
            from core.genesis import registrar_bot_genesis
            await registrar_bot_genesis(nuevo_bot)
            logger.info(f"🏭 Bot '{nuevo_bot.id}' registrado en Genesis")
        except ImportError:
            logger.debug("Genesis no disponible, bot solo en memoria")
        except Exception as e:
            logger.warning(f"No se pudo registrar en genesis: {e}")

    def _formatear_resultado(self, bot: BotBase, especificacion: str) -> str:
        """Formatea el resultado de creación exitosa."""
        return (
            f"✅ Bot creado exitosamente:\n\n"
            f"🤖 **{bot.nombre}** (`{bot.id}`)\n"
            f"📋 Especialidad: {bot.especialidad}\n"
            f"🏷️ Keywords: {', '.join(bot.keywords)}\n"
            f"🧠 Modelo: {bot.modelo}\n"
            f"📊 Estado: {bot.estado} (score: {bot.score})\n"
            f"👨‍👦 Creado por: {self.id}\n\n"
            f"El bot ya está registrado y puede recibir tareas."
        )


bot_fabrica = BotFabrica(
    id="bot_fabrica",
    nombre="Fábrica",
    especialidad="Crea nuevos bots bajo demanda usando lógica genesis",
    keywords=["crear bot", "nuevo bot", "fabricar", "generar bot", "necesito bot", "fábrica"],
    prompt_compiled=(
        "Eres la Fábrica de Bots. Creas nuevos bots especializados bajo demanda. "
        "Analizas qué necesita el usuario y generas un bot optimizado: "
        "prompt compilado corto (~60 tokens), keywords precisas, modelo adecuado. "
        "Cada bot que creas nace como 'novato' y debe demostrar su valor. "
        "Prioriza bots específicos sobre genéricos."
    ),
    modelo="gemini-pro",
    herramientas=["crear_bot", "generar_prompt", "asignar_modelo", "registrar_genesis"],
    estado="elite",
    score=4.5,
)

registrar_bot_en_memoria(bot_fabrica)
