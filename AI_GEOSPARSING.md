# Sistema de Geosparsing con IA
## Detección Inteligente de Territorios en Noticias y Redes Sociales

Este documento explica el nuevo sistema de geosparsing con inteligencia artificial implementado en el MVP de Inteligencia Territorial.

---

## 📋 Tabla de Contenidos

1. [¿Qué es el Geosparsing con IA?](#qué-es-el-geosparsing-con-ia)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Cómo Funciona](#cómo-funciona)
4. [Configuración](#configuración)
5. [Trazabilidad y Explicabilidad](#trazabilidad-y-explicabilidad)
6. [API Endpoints](#api-endpoints)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Costos Estimados](#costos-estimados)

---

## ¿Qué es el Geosparsing con IA?

El **geosparsing** es el proceso de:
1. **Detectar topónimos** (nombres de lugares) en textos
2. **Resolver geográficamente** cada topónimo a un territorio concreto
3. **Desambiguar homónimos** (lugares con el mismo nombre)
4. **Asignar relevancia** basada en múltiples señales

### Ejemplo

**Texto de entrada:**
```
"Vecinos de Rancagua protestan contra minera. El conflicto afecta a la Región
de O'Higgins y podría extenderse a comunas cercanas como San Fernando."
```

**Salida del sistema:**
```json
{
  "territories": [
    {
      "territory_name": "Rancagua",
      "territory_level": "comuna",
      "relevance_score": 0.95,
      "detected_toponym": "Rancagua",
      "disambiguation_reason": "Detectado 'Rancagua' usando ai_ner_openai; match exacto con 'Rancagua'; aparece en título; contexto: \"...Vecinos de Rancagua protestan contra...\""
    },
    {
      "territory_name": "Región de O'Higgins",
      "territory_level": "región",
      "relevance_score": 0.88,
      "detected_toponym": "Región de O'Higgins",
      "disambiguation_reason": "Detectado 'Región de O'Higgins' usando ai_ner_openai; match exacto; alta frecuencia en texto"
    }
  ]
}
```

---

## Componentes del Sistema

### 1. **NER (Named Entity Recognition) con IA**

Detecta topónimos en español usando:
- **OpenAI GPT-4/GPT-3.5**: Máxima precisión, entiende contexto
- **Anthropic Claude**: Alternativa de alta calidad
- **spaCy NER**: Fallback sin costo (requiere modelo español)
- **Regex + Gazetteer**: Fallback básico

### 2. **Gazetteer (Catálogo de Territorios)**

Base de datos de 16 regiones + 346 comunas de Chile con:
- Nombres oficiales
- Aliases (ej: "Santiago" → "Región Metropolitana", "RM", "R.M.")
- Coordenadas geográficas (lat/lon)
- Jerarquía (región > comuna > localidad)

Fuente: `backend/app/data/chile_territories.py`

### 3. **Sistema de Scoring Multi-Señal**

Combina 6 señales para calcular relevancia:

| Señal | Peso | Descripción |
|-------|------|-------------|
| **Posición** | 25% | Título > Contenido |
| **Método detección** | 15% | IA > spaCy > Regex |
| **Confianza detección** | 15% | Confianza del NER |
| **Frecuencia** | 20% | Cuántas veces aparece |
| **Fuente regional** | 15% | Si coincide con región de la fuente |
| **Nivel territorial** | 10% | Región > Comuna > Localidad |

### 4. **Desambiguación Contextual**

Maneja homónimos usando:
- Contexto del texto (qué otros lugares se mencionan)
- Fuente de la noticia (medios regionales vs nacionales)
- Frecuencia de mención
- Proximidad a otros topónimos conocidos

### 5. **Trazabilidad Completa**

Para cada territorio detectado, el sistema guarda:
- ✅ Qué topónimo se detectó
- ✅ Dónde estaba en el texto (posición)
- ✅ Contexto (±50 caracteres alrededor)
- ✅ Por qué se mapeó a ese territorio
- ✅ Desglose de scoring
- ✅ Método de detección usado
- ✅ Proveedor de IA usado

---

## Cómo Funciona

### Pipeline Completo

```
┌─────────────────┐
│  Noticia nueva  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  1. DETECCIÓN DE TOPÓNIMOS  │
│     (NER con IA)            │
└────────┬────────────────────┘
         │
         │  ["Rancagua", "O'Higgins", "San Fernando"]
         ▼
┌─────────────────────────────┐
│  2. RESOLUCIÓN GEOGRÁFICA   │
│     (Gazetteer + Fuzzy)     │
└────────┬────────────────────┘
         │
         │  Candidatos por topónimo
         ▼
┌─────────────────────────────┐
│  3. SCORING & DESAMBIGUACIÓN│
│     (Multi-señal)           │
└────────┬────────────────────┘
         │
         │  Top 3 territorios con scores
         ▼
┌─────────────────────────────┐
│  4. ALMACENAMIENTO          │
│     (DB con trazabilidad)   │
└─────────────────────────────┘
```

### Código del Pipeline

**Archivo:** `backend/app/services/nlp/ai_geosparsing.py`

```python
from app.services.nlp.ai_geosparsing import geoparse_with_ai

# Uso básico
matches = await geoparse_with_ai(
    title="Vecinos de Rancagua protestan",
    content="El conflicto afecta a la Región de O'Higgins...",
    source_region="O'Higgins"  # Opcional, ayuda a desambiguar
)

# Retorna lista de territorios con trazabilidad completa
for match in matches:
    print(f"{match['territory_name']}: {match['relevance_score']}")
    print(f"  Detectado como: {match['detected_toponym']}")
    print(f"  Razón: {match['disambiguation_reason']}")
```

---

## Configuración

### Paso 1: Instalar Dependencias de IA

Edita `backend/requirements.txt` y descomenta:

```txt
# Descomentar la que necesites:
openai>=1.12.0       # Para OpenAI
anthropic>=0.18.0    # Para Anthropic
```

Luego instala:
```bash
cd backend
pip install -r requirements.txt
```

O reconstruye el contenedor Docker:
```bash
docker-compose up -d --build backend
```

### Paso 2: Obtener API Key

#### Opción A: OpenAI (Recomendado para empezar)

1. Crea cuenta en https://platform.openai.com
2. Ve a **API Keys**: https://platform.openai.com/api-keys
3. Crea una nueva API key
4. Copia el valor (comienza con `sk-proj-...`)

**Costo estimado:** $0.01-0.05 USD por noticia procesada con GPT-4o-mini

#### Opción B: Anthropic Claude

1. Crea cuenta en https://console.anthropic.com
2. Ve a **API Keys**: https://console.anthropic.com/settings/keys
3. Crea una nueva API key
4. Copia el valor (comienza con `sk-ant-...`)

**Costo estimado:** Similar a OpenAI

### Paso 3: Configurar Variables de Entorno

Edita `backend/.env`:

```bash
# Para OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-TU_API_KEY_AQUI
OPENAI_MODEL=gpt-4o-mini  # Más barato, rápido y suficientemente bueno

# O para Anthropic
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-TU_API_KEY_AQUI
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Paso 4: Reiniciar Backend

```bash
docker-compose restart backend

# O reiniciar todo
docker-compose down
docker-compose up -d
```

### Paso 5: Verificar que Funciona

Revisa los logs:
```bash
docker-compose logs -f backend
```

Deberías ver:
```
✅ Geosparsing con IA habilitado (openai)
```

---

## Trazabilidad y Explicabilidad

### ¿Por qué es importante?

El sistema guarda **explicaciones completas** de por qué cada territorio fue detectado. Esto permite:

✅ **Auditoría**: Revisar decisiones del sistema
✅ **Debugging**: Encontrar errores de detección
✅ **Mejora continua**: Analizar qué funciona y qué no
✅ **Transparencia**: Explicar al usuario por qué se asignó un territorio
✅ **Cumplimiento**: Requisitos legales/éticos de IA explicable

### Datos de Trazabilidad Guardados

Para cada territorio detectado, se guarda:

```python
{
  "territory_name": "Rancagua",              # Territorio oficial
  "territory_level": "comuna",               # región|comuna|localidad
  "latitude": -34.1704,                      # Coordenadas
  "longitude": -70.7408,

  # TRAZABILIDAD
  "detected_toponym": "Rancagua",            # Topónimo original detectado
  "toponym_position": 12,                    # Posición en el texto (caracteres)
  "toponym_context": "...Vecinos de Rancagua protestan...",  # Contexto

  # SCORING
  "relevance_score": 0.95,                   # Score final
  "scoring_breakdown": {                     # Desglose completo
    "position_score": 1.0,                   # Aparece en título
    "detection_method_score": 0.95,          # Detectado con IA
    "detection_confidence": 0.9,
    "frequency_score": 0.4,                  # Aparece 2 veces
    "source_region_score": 1.0,              # Fuente es de O'Higgins
    "level_score": 0.7,                      # Es una comuna
    "final_score": 0.95
  },

  # EXPLICABILIDAD
  "mapping_method": "exact_match",           # exact_match|alias_match|fuzzy_match
  "disambiguation_reason": "Detectado 'Rancagua' usando ai_ner_openai; match exacto con 'Rancagua'; aparece en título; fuente regional coincide (O'Higgins); contexto: \"...Vecinos de Rancagua protestan...\"",
  "ai_provider": "openai",                   # openai|anthropic|spacy|none
  "matched_at": "2024-01-20T15:30:00Z"       # Timestamp
}
```

### Ejemplo de Consulta de Trazabilidad

```bash
# Obtener trazabilidad de una señal específica
curl http://localhost:8000/signals/123/geosparsing-trace
```

Respuesta:
```json
{
  "signal_id": 123,
  "signal_title": "Vecinos de Rancagua protestan contra minera",
  "territories_detected": [
    {
      "territory_name": "Rancagua",
      "detection": {
        "detected_toponym": "Rancagua",
        "position_in_text": 12,
        "context": "...Vecinos de Rancagua protestan..."
      },
      "relevance_score": 0.95,
      "scoring_breakdown": { ... },
      "disambiguation_reason": "Detectado 'Rancagua' usando ai_ner_openai...",
      "ai_provider": "openai"
    }
  ],
  "ai_enabled": true,
  "metadata": {
    "total_territories": 2,
    "ai_detected_count": 2,
    "legacy_detected_count": 0
  }
}
```

---

## API Endpoints

### 1. **Listar Señales**

```http
GET /signals?tenant_id=1&limit=100&territory=Rancagua
```

Retorna señales con territorios básicos (sin trazabilidad completa).

### 2. **Obtener Señal Individual**

```http
GET /signals/{signal_id}
```

Retorna señal con territorios y tópicos.

### 3. **Obtener Trazabilidad de Geosparsing** ⭐ NUEVO

```http
GET /signals/{signal_id}/geosparsing-trace
```

Retorna trazabilidad completa del geosparsing para esa señal.

**Respuesta:**
```json
{
  "signal_id": 123,
  "signal_title": "Título de la noticia",
  "territories_detected": [
    {
      "territory_name": "Rancagua",
      "detection": { ... },
      "scoring_breakdown": { ... },
      "disambiguation_reason": "...",
      "ai_provider": "openai"
    }
  ],
  "ai_enabled": true
}
```

---

## Ejemplos de Uso

### Ejemplo 1: Noticia Simple

**Input:**
```
Título: "Protesta en Valparaíso por alza de tarifas"
Contenido: "Cientos de manifestantes tomaron la Plaza Sotomayor..."
```

**Output:**
```json
{
  "territories": [
    {
      "territory_name": "Valparaíso",
      "territory_level": "región",
      "relevance_score": 0.95,
      "detected_toponym": "Valparaíso",
      "disambiguation_reason": "Aparece en título; match exacto; alta confianza"
    }
  ]
}
```

### Ejemplo 2: Homónimos (Desambiguación)

**Input:**
```
Título: "La Unión reporta aumento de casos COVID"
Contenido: "La comuna de La Unión, en la Región de Los Ríos, registró 30 nuevos casos..."
```

**Output:**
```json
{
  "territories": [
    {
      "territory_name": "La Unión",
      "territory_level": "comuna",
      "relevance_score": 0.92,
      "detected_toponym": "La Unión",
      "disambiguation_reason": "Contexto menciona 'Región de Los Ríos'; descarta homónimo en Los Lagos"
    },
    {
      "territory_name": "Los Ríos",
      "territory_level": "región",
      "relevance_score": 0.85
    }
  ]
}
```

### Ejemplo 3: Múltiples Territorios

**Input:**
```
Título: "Incendios afectan a Valparaíso, Viña del Mar y Quilpué"
Contenido: "Las comunas de la Región de Valparaíso enfrentan emergencia por incendios forestales..."
```

**Output:**
```json
{
  "territories": [
    {
      "territory_name": "Valparaíso",
      "relevance_score": 0.95,
      "detected_toponym": "Valparaíso"
    },
    {
      "territory_name": "Viña del Mar",
      "relevance_score": 0.93,
      "detected_toponym": "Viña del Mar"
    },
    {
      "territory_name": "Quilpué",
      "relevance_score": 0.90,
      "detected_toponym": "Quilpué"
    }
  ]
}
```

---

## Costos Estimados

### OpenAI (GPT-4o-mini)

**Precios (enero 2024):**
- Input: $0.15 por 1M tokens
- Output: $0.60 por 1M tokens

**Estimación por noticia:**
- Input: ~1,500 tokens (título + contenido)
- Output: ~200 tokens (JSON de topónimos)
- **Costo: ~$0.0003 - $0.001 USD por noticia**

**Volumen mensual:**
- 1,000 noticias/mes: ~$0.30 - $1 USD
- 10,000 noticias/mes: ~$3 - $10 USD
- 100,000 noticias/mes: ~$30 - $100 USD

### Anthropic Claude (Claude 3.5 Sonnet)

Similar a OpenAI, ligeramente más caro pero mejor calidad.

### spaCy (Gratis)

Sin costo, pero menor precisión (~70% vs ~90% con IA).

### Recomendación

- **Desarrollo/Pruebas**: Usar spaCy (gratis)
- **Producción (bajo volumen)**: OpenAI GPT-4o-mini
- **Producción (alto volumen)**: Evaluar costos, considerar modelo local

---

## Migraciones de Base de Datos

Si ya tienes datos en producción, necesitas ejecutar migraciones para agregar los nuevos campos.

**Archivo de migración:** `backend/migrations/add_geosparsing_traceability.sql`

```sql
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
```

Ejecutar migración:
```bash
docker-compose exec db psql -U postgres -d territorial -f /migrations/add_geosparsing_traceability.sql
```

---

## Troubleshooting

### Error: "No se pudo cargar modelo spaCy"

**Solución:** Instalar modelo español:
```bash
docker-compose exec backend python -m spacy download es_core_news_sm
```

### Error: "OpenAI API error 401"

**Problema:** API key inválida
**Solución:** Verifica que `OPENAI_API_KEY` esté bien configurada en `.env`

### Los territorios detectados no tienen trazabilidad

**Problema:** Sistema usando fallback sin IA
**Solución:**
1. Verifica que `OPENAI_API_KEY` o `ANTHROPIC_API_KEY` esté configurada
2. Verifica que las dependencias estén instaladas (`pip list | grep openai`)
3. Reinicia el backend

### Costos muy altos

**Solución:**
1. Usa `gpt-4o-mini` en lugar de `gpt-4o` (10x más barato)
2. Limita el contenido procesado (max 3000 caracteres)
3. Considera usar spaCy para noticias de baja prioridad

---

## Roadmap Futuro

- [ ] **Cache de topónimos**: Evitar re-procesar noticias similares
- [ ] **Fine-tuning**: Entrenar modelo específico para Chile
- [ ] **Embeddings**: Usar embeddings para mejorar desambiguación
- [ ] **Feedback loop**: Aprender de correcciones manuales
- [ ] **Dashboard de trazabilidad**: UI para revisar detecciones
- [ ] **A/B testing**: Comparar IA vs spaCy en producción
- [ ] **Soporte multiidioma**: Inglés, mapudungun, etc.

---

## Soporte

Si tienes dudas o problemas:

1. Revisa esta documentación
2. Revisa los logs: `docker-compose logs -f backend`
3. Revisa el código: `backend/app/services/nlp/ai_geosparsing.py`
4. Abre un issue en GitHub

---

## Licencia

Este sistema es parte del MVP de Inteligencia Territorial y sigue la misma licencia del proyecto principal.

---

**Última actualización:** 2024-01-21
**Versión:** 2.0.0
