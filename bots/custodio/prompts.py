"""Prompts estándar para generación de música Bolero-House."""

# Prompt positivo para Suno/Udio
PROMPT_MUSICA_POSITIVO = (
    "Bolero-House style, 115 BPM, smooth and deep House kick, "
    "warm ukulele, upright-style bass, maracas, atmospheric synthesizer, "
    "elegant dance rhythm, playful ukulele strumming, bongo percussion, "
    "lofi filter, echoing voice, velvety smiling vocals, rich harmonies, "
    "groovy outro."
)

# Prompt negativo para Suno/Udio
PROMPT_MUSICA_NEGATIVO = (
    "aggressive, harsh vocals, high BPM (>130), techno, acoustic solo, "
    "distorted guitar, fast metal, rap, low quality, muffled, tinny, thin, "
    "muddy, distorted, clipping, overcompressed, auto-tune excessive, "
    "robotic vocals, off-key, out of time, genre mismatch."
)

# Estructura estándar de canción Bolero-House
ESTRUCTURA_CANCION = {
    "bpm": 115,
    "estructura": "Intro → Verso 1 → Coro → Verso 2 → Coro → Puente → Coro → Outro",
    "intro": "8 compases con ukelele",
    "instrumentos": ["ukulele", "house kick", "maracas", "bongo", "synth pad", "upright bass"],
    "voz": "Cálida, aterciopelada, con eco sutil",
    "coros": "3 capas armónicas",
    "outro": "Groove descendente, fade out con ukelele",
}

# Templates de títulos
TEMPLATES_TITULOS = [
    "Noches de {tema} (Bolero-House Mix)",
    "{tema} en la Arena (C8L Edit)",
    "Bailando {tema} (House Remix)",
    "{tema} Tropical (Leo Vela Sessions)",
    "Luna de {tema} (Bolero Groove)",
]
