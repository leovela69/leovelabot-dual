-- =============================================
-- C8L AGENT v15.4 — Schema Custodio (5 tablas)
-- =============================================

CREATE TABLE web_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo TEXT NOT NULL,
    score_performance INT,
    score_seo INT,
    score_accessibility INT,
    score_security INT,
    problemas_detectados JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE web_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    estado TEXT DEFAULT 'borrador',
    aprobado_por TEXT,
    publicado_en TIMESTAMP,
    url_publicada TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE web_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uptime_percent FLOAT,
    velocidad_ms INT,
    visitas INT DEFAULT 0,
    paginas_vistas INT DEFAULT 0,
    score_lighthouse INT DEFAULT 0,
    score_seo INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE herramientas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    descripcion TEXT,
    codigo TEXT NOT NULL,
    creado_por TEXT,
    veces_usada INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tareas_programadas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id TEXT NOT NULL,
    cron_expr TEXT NOT NULL,
    tarea_template TEXT NOT NULL,
    activa BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_audits_tipo ON web_audits(tipo);
CREATE INDEX idx_content_estado ON web_content(estado);
CREATE INDEX idx_metrics_fecha ON web_metrics(created_at DESC);
