-- ============================================================
-- Migración: Agregar Trazabilidad de Geosparsing con IA
-- Versión: 2.0.0
-- Fecha: 2024-01-21
-- ============================================================
--
-- Esta migración agrega campos de trazabilidad y explicabilidad
-- al sistema de geosparsing para cumplir con requisitos de IA
-- responsable y auditable.
--
-- Campos agregados:
-- - detected_toponym: Topónimo original detectado en el texto
-- - toponym_position: Posición del topónimo en el texto
-- - toponym_context: Contexto alrededor del topónimo
-- - relevance_score: Score de relevancia calculado
-- - scoring_breakdown_json: Desglose detallado de scores
-- - mapping_method: Método usado para mapear (exact_match, fuzzy, etc)
-- - disambiguation_reason: Explicación de por qué se eligió este territorio
-- - ai_provider: Proveedor de IA usado (openai, anthropic, spacy, none)
-- - latitude/longitude: Coordenadas geográficas del territorio
--
-- ============================================================

BEGIN;

-- Agregar campos de trazabilidad a signal_territories
ALTER TABLE signal_territories
ADD COLUMN IF NOT EXISTS detected_toponym VARCHAR(200),
ADD COLUMN IF NOT EXISTS toponym_position INTEGER,
ADD COLUMN IF NOT EXISTS toponym_context TEXT,
ADD COLUMN IF NOT EXISTS relevance_score FLOAT,
ADD COLUMN IF NOT EXISTS scoring_breakdown_json TEXT,
ADD COLUMN IF NOT EXISTS mapping_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS disambiguation_reason TEXT,
ADD COLUMN IF NOT EXISTS ai_provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS latitude FLOAT,
ADD COLUMN IF NOT EXISTS longitude FLOAT;

-- Agregar índices para consultas eficientes
CREATE INDEX IF NOT EXISTS idx_signal_territories_ai_provider
ON signal_territories(ai_provider);

CREATE INDEX IF NOT EXISTS idx_signal_territories_mapping_method
ON signal_territories(mapping_method);

-- Agregar comentarios descriptivos a las columnas
COMMENT ON COLUMN signal_territories.detected_toponym IS 'Topónimo original detectado en el texto (ej: "Rancagua")';
COMMENT ON COLUMN signal_territories.toponym_position IS 'Posición del topónimo en el texto (en caracteres)';
COMMENT ON COLUMN signal_territories.toponym_context IS 'Contexto alrededor del topónimo (±50 caracteres)';
COMMENT ON COLUMN signal_territories.relevance_score IS 'Score de relevancia calculado (0-1)';
COMMENT ON COLUMN signal_territories.scoring_breakdown_json IS 'Desglose JSON de scores por señal';
COMMENT ON COLUMN signal_territories.mapping_method IS 'Método de mapeo: exact_match, alias_match, fuzzy_match, ai_disambiguation';
COMMENT ON COLUMN signal_territories.disambiguation_reason IS 'Explicación legible de por qué se eligió este territorio';
COMMENT ON COLUMN signal_territories.ai_provider IS 'Proveedor de IA: openai, anthropic, spacy, none';
COMMENT ON COLUMN signal_territories.latitude IS 'Latitud del territorio';
COMMENT ON COLUMN signal_territories.longitude IS 'Longitud del territorio';

-- Actualizar registros existentes con valores por defecto
UPDATE signal_territories
SET
    ai_provider = 'legacy',
    mapping_method = 'legacy'
WHERE ai_provider IS NULL;

COMMIT;

-- ============================================================
-- Verificación
-- ============================================================
-- Ejecutar estas queries para verificar la migración:
--
-- 1. Ver estructura de la tabla:
--    \d signal_territories
--
-- 2. Contar registros con/sin IA:
--    SELECT ai_provider, COUNT(*) FROM signal_territories GROUP BY ai_provider;
--
-- 3. Ver ejemplo de trazabilidad:
--    SELECT territory, detected_toponym, mapping_method, ai_provider
--    FROM signal_territories LIMIT 10;
--
-- ============================================================
