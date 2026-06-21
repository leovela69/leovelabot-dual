-- =============================================
-- C8L AGENT v15.4 — Schema Principal (9 tablas)
-- =============================================

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id TEXT UNIQUE NOT NULL,
    nombre TEXT,
    nivel INT DEFAULT 1,
    xp INT DEFAULT 0,
    preferencias JSONB DEFAULT '{}',
    idioma TEXT DEFAULT 'es',
    autonomia TEXT DEFAULT 'media',
    modo TEXT DEFAULT 'normal',
    creado_en TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bots (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    especialidad TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    prompt_compiled TEXT NOT NULL,
    modelo TEXT DEFAULT 'groq',
    herramientas TEXT[] DEFAULT '{}',
    score FLOAT DEFAULT 3.0,
    tareas_completadas INT DEFAULT 0,
    fallos INT DEFAULT 0,
    estado TEXT DEFAULT 'novato',
    padre_id TEXT REFERENCES bots(id),
    fusionado_de TEXT[] DEFAULT '{}',
    costo_promedio_tokens INT DEFAULT 0,
    config JSONB DEFAULT '{}',
    creado_por TEXT DEFAULT 'genesis',
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE TABLE proyectos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id TEXT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    archivos JSONB DEFAULT '[]',
    version_actual INT DEFAULT 1,
    contexto_thread JSONB DEFAULT '{}',
    centinela_activo BOOLEAN DEFAULT false,
    deploy_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE versiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID REFERENCES proyectos(id),
    numero INT NOT NULL,
    snapshot JSONB NOT NULL,
    es_fork BOOLEAN DEFAULT false,
    fork_nombre TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tareas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id TEXT NOT NULL,
    proyecto_id UUID REFERENCES proyectos(id),
    bot_id TEXT REFERENCES bots(id),
    equipo_bots TEXT[] DEFAULT '{}',
    tipo TEXT NOT NULL,
    orden_raw TEXT NOT NULL,
    orden_clean TEXT,
    plan JSONB,
    resultado TEXT,
    tokens_usados INT DEFAULT 0,
    tokens_ahorrados INT DEFAULT 0,
    calidad FLOAT DEFAULT 0,
    es_entrenamiento BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE arquetipos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    best_output TEXT,
    score_promedio FLOAT DEFAULT 0,
    veces_usado INT DEFAULT 0,
    source_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE errores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id TEXT REFERENCES bots(id),
    tarea_id UUID REFERENCES tareas(id),
    tipo TEXT NOT NULL,
    mensaje TEXT,
    solucion TEXT,
    veces_visto INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reglas_destiladas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categoria TEXT NOT NULL,
    regla TEXT NOT NULL,
    veces_aplicada INT DEFAULT 0,
    tasa_exito FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE intentos_bloqueados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id TEXT NOT NULL,
    orden TEXT NOT NULL,
    motivo TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_bots_estado ON bots(estado);
CREATE INDEX idx_bots_score ON bots(score DESC);
CREATE INDEX idx_tareas_usuario ON tareas(usuario_id);
CREATE INDEX idx_tareas_proyecto ON tareas(proyecto_id);
CREATE INDEX idx_proyectos_usuario ON proyectos(usuario_id);
