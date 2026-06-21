"""Bot React: Componentes React, hooks, estado."""

from bots.base import BotBase, registrar_bot_en_memoria

bot_react = BotBase(
    id="bot_react",
    nombre="React",
    especialidad="Componentes React, hooks, estado, Next.js, TypeScript",
    keywords=["react", "componente", "hook", "useState", "nextjs", "next", "tsx", "jsx"],
    prompt_compiled=(
        "Genera componentes React modernos con hooks. TypeScript preferido. "
        "Functional components, custom hooks, proper state management. "
        "Next.js App Router si se pide. Solo código. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_react", "lint_tsx"],
    estado="activo",
    score=4.0,
)

bot_vue = BotBase(
    id="bot_vue",
    nombre="Vue",
    especialidad="Componentes Vue 3, Composition API, Nuxt, TypeScript",
    keywords=["vue", "nuxt", "composición", "setup", "ref", "computed"],
    prompt_compiled=(
        "Genera componentes Vue 3 con Composition API. "
        "script setup, TypeScript, Pinia si necesita estado global. "
        "Solo código. Sin explicaciones."
    ),
    modelo="groq",
    herramientas=["generar_vue"],
    estado="activo",
    score=3.5,
)

registrar_bot_en_memoria(bot_react)
registrar_bot_en_memoria(bot_vue)
