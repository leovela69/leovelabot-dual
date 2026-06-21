-- =============================================
-- C8L AGENT v15.4 — Schema Música (3 tablas)
-- =============================================

CREATE TABLE custodio_canciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    letra TEXT,
    prompt_positivo TEXT,
    prompt_negativo TEXT,
    url_audio TEXT,
    duracion INT,
    calidad INT DEFAULT 0,
    estado TEXT DEFAULT 'pendiente',
    fecha_generacion TIMESTAMP DEFAULT NOW(),
    fecha_aprobacion TIMESTAMP
);

CREATE TABLE custodio_videoclips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cancion_id UUID REFERENCES custodio_canciones(id),
    url_video TEXT,
    duracion INT,
    calidad INT DEFAULT 0,
    estado TEXT DEFAULT 'pendiente',
    fecha_generacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conocimiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categoria TEXT NOT NULL,
    dato TEXT NOT NULL,
    fuente TEXT,
    confianza FLOAT DEFAULT 1.0,
    veces_consultado INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tendencias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente TEXT NOT NULL,
    tecnologias TEXT[] DEFAULT '{}',
    resumen TEXT,
    fecha DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_canciones_estado ON custodio_canciones(estado);
CREATE INDEX idx_canciones_calidad ON custodio_canciones(calidad DESC);
CREATE INDEX idx_videoclips_cancion ON custodio_videoclips(cancion_id);
CREATE INDEX idx_conocimiento_cat ON conocimiento(categoria);
CREATE INDEX idx_tendencias_fecha ON tendencias(fecha DESC);
