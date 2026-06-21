"""Bot SQL: Bases de datos, schemas, queries, migraciones."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_sql = BotBase(
    id="bot_sql",
    nombre="SQL Database",
    especialidad="PostgreSQL, schemas, queries, índices, migraciones, Supabase",
    keywords=["sql", "database", "base de datos", "tabla", "query", "postgres", "supabase", "schema"],
    prompt_compiled=(
        "Genera SQL para PostgreSQL/Supabase. CREATE TABLE con tipos correctos, "
        "índices, constraints, foreign keys. Queries optimizadas. "
        "Incluye comentarios explicativos. Solo SQL funcional."
    ),
    modelo="groq",
    herramientas=["generar_sql", "validar_sql"],
    estado="activo",
    score=4.0,
)

registrar_bot_en_memoria(bot_sql)
