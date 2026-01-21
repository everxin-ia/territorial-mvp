# Migraciones de Base de Datos

Este directorio contiene scripts SQL para migraciones de la base de datos.

## Ejecutar Migraciones

### Opción 1: Desde contenedor Docker

```bash
# Copiar archivo de migración al contenedor
docker cp backend/migrations/add_geosparsing_traceability.sql $(docker-compose ps -q db):/tmp/migration.sql

# Ejecutar migración
docker-compose exec db psql -U postgres -d territorial -f /tmp/migration.sql
```

### Opción 2: Directamente con psql

```bash
# Si tienes psql instalado localmente
psql -h localhost -U postgres -d territorial -f backend/migrations/add_geosparsing_traceability.sql
```

### Opción 3: Usar docker-compose exec

```bash
docker-compose exec db psql -U postgres -d territorial << EOF
$(cat backend/migrations/add_geosparsing_traceability.sql)
EOF
```

## Migraciones Disponibles

### `add_geosparsing_traceability.sql`

**Versión:** 2.0.0
**Fecha:** 2024-01-21

Agrega campos de trazabilidad al sistema de geosparsing con IA:
- `detected_toponym`: Topónimo original detectado
- `toponym_position`: Posición en el texto
- `toponym_context`: Contexto del topónimo
- `relevance_score`: Score de relevancia
- `scoring_breakdown_json`: Desglose de scores
- `mapping_method`: Método de mapeo
- `disambiguation_reason`: Explicación de desambiguación
- `ai_provider`: Proveedor de IA usado
- `latitude/longitude`: Coordenadas geográficas

**Ejecutar:**
```bash
docker cp backend/migrations/add_geosparsing_traceability.sql $(docker-compose ps -q db):/tmp/migration.sql
docker-compose exec db psql -U postgres -d territorial -f /tmp/migration.sql
```

**Verificar:**
```sql
-- Ver estructura de la tabla
\d signal_territories

-- Contar registros con/sin IA
SELECT ai_provider, COUNT(*) FROM signal_territories GROUP BY ai_provider;
```

## Rollback

Si necesitas revertir la migración:

```sql
ALTER TABLE signal_territories
DROP COLUMN IF EXISTS detected_toponym,
DROP COLUMN IF EXISTS toponym_position,
DROP COLUMN IF EXISTS toponym_context,
DROP COLUMN IF EXISTS relevance_score,
DROP COLUMN IF EXISTS scoring_breakdown_json,
DROP COLUMN IF EXISTS mapping_method,
DROP COLUMN IF EXISTS disambiguation_reason,
DROP COLUMN IF EXISTS ai_provider,
DROP COLUMN IF EXISTS latitude,
DROP COLUMN IF EXISTS longitude;
```

## Notas

- ⚠️ Las migraciones son idempotentes (usan `IF NOT EXISTS`)
- ⚠️ Los registros existentes se actualizan con `ai_provider='legacy'`
- ✅ Se agregan índices para optimizar consultas
- ✅ Se agregan comentarios descriptivos a las columnas
