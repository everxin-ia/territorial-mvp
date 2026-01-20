# Plataforma Inteligencia Territorial — MVP Enhanced v2.0

**Sistema avanzado de detección temprana de conflictos socio-territoriales** mediante análisis de señales públicas (RSS, noticias web) con NLP avanzado, scoring heurístico mejorado, y visualización ejecutiva.

## 🚀 Novedades v2.0

### Backend - Mejoras de Alta y Media Prioridad

#### ✅ NLP Avanzado
- **Sentiment Analysis**: VADER para detectar polaridad de noticias (positivo/negativo/neutral)
- **Deduplicación Mejorada**: SimHash para detección de near-duplicates (threshold configurable)
- **Territorios Dinámicos**: Base de datos de territorios con geocoding (lat/lon), jerarquía y aliases
- **Source Credibility**: Sistema de scoring de credibilidad de fuentes (0-1)

#### ✅ Análisis de Riesgo Mejorado
- **Time Series Analysis**: Detección de tendencias (rising/falling/stable) vs periodo anterior
- **Anomaly Detection**: Identificación de scores > 2 desviaciones estándar
- **Scoring Mejorado**: Incorpora sentiment y credibilidad de fuente
  ```
  score = source_weight × credibility + 2×topic + language + recurrence + official + sentiment_penalty
  ```

#### ✅ Sistema de Alertas
- **Alert Deduplication**: Previene alertas duplicadas (window de 1 hora)
- **Comentarios en Alertas**: Sistema colaborativo con historial de comentarios
- **Estados de Alerta**: new → acked → closed (workflow completo)

#### ✅ API REST Extendida
- `GET/POST/PUT/DELETE /territories` - CRUD de territorios
- `GET/POST/PUT/DELETE /alert-rules` - Gestión de reglas de alerta
- `POST /alert-rules/{id}/comments` - Comentarios en alertas
- `GET /territories/map` - GeoJSON para visualización de mapa
- `GET /signals?territory=X&topic=Y&days=Z` - Filtros avanzados

### Frontend - Mejoras UI/UX

#### ✅ Vista de Mapa Interactivo
- **Leaflet/OpenStreetMap**: Visualización geoespacial de territorios
- **Círculos de Riesgo**: Tamaño/color proporcional a probabilidad
- **Popups Informativos**: Detalles de riesgo, tendencia y anomalías
- **Detección Visual de Anomalías**: Indicadores de alerta especiales

#### ✅ Filtros Avanzados
- Filtrado por territorio (búsqueda parcial)
- Filtrado por tópico (8 categorías)
- Filtrado temporal (7/14/30 días)
- Resultados en tiempo real

#### ✅ Panel de Configuración
- **CRUD de Reglas de Alerta**: Crear/editar/eliminar reglas visualmente
- **Sliders de Umbrales**: Ajuste intuitivo de probabilidad/confianza
- **Habilitación/Deshabilitación**: Toggle de reglas sin eliminarlas

#### ✅ Dashboard Mejorado
- **Gráficos de Sentiment**: Distribución positivo/neutral/negativo
- **Top 5 Tópicos**: Visualización de temas más frecuentes
- **Badges de Sentiment**: Indicadores visuales en tabla de señales
- **Drill-Down en Alertas**: Click para ver comentarios y contexto

#### ✅ Sistema de Comentarios
- Modal interactivo para cada alerta
- Historial completo de comentarios con timestamps
- Identificación de usuario
- Colaboración en tiempo real

## 🔧 Requisitos

- Docker + Docker Compose
- Node 18+ (opcional, para desarrollo frontend local)
- Python 3.11+ (opcional, para desarrollo backend local)

## 🚦 Quickstart

```bash
cd territorial-mvp

# Levantar servicios
docker compose up --build

# Backend: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

El sistema se auto-seedea con:
- 1 tenant demo
- 8 territorios de Chile (Santiago, Valparaíso, etc.) con coordenadas
- 3 fuentes RSS (Google News)
- 1 regla de alerta demo

**Jobs automáticos:**
- Ingesta RSS: cada 30 min
- Cálculo de riesgo: cada 60 min
- Evaluación de alertas: cada 15 min

## 📊 Nuevas Tablas de Base de Datos

### `territories`
```sql
CREATE TABLE territories (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  name VARCHAR(200) NOT NULL,
  level VARCHAR(40),              -- país|región|comuna|ciudad
  parent_id INT REFERENCES territories(id),
  latitude FLOAT,
  longitude FLOAT,
  aliases_json TEXT,              -- Lista JSON de nombres alternativos
  enabled BOOLEAN DEFAULT TRUE
);
```

### `alert_comments`
```sql
CREATE TABLE alert_comments (
  id SERIAL PRIMARY KEY,
  alert_id INT REFERENCES alert_events(id),
  user_name VARCHAR(200) DEFAULT 'Usuario',
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🎯 Nuevos Endpoints

### Territorios
```bash
# Listar territorios
GET /territories?tenant_id=1

# Crear territorio
POST /territories?tenant_id=1
{
  "name": "Santiago",
  "level": "región",
  "latitude": -33.4489,
  "longitude": -70.6693,
  "aliases": ["RM", "Región Metropolitana"]
}

# Actualizar territorio
PUT /territories/{id}

# Eliminar territorio
DELETE /territories/{id}

# Obtener GeoJSON para mapa
GET /territories/map?tenant_id=1
```

### Reglas de Alerta
```bash
# Listar reglas
GET /alert-rules?tenant_id=1

# Crear regla
POST /alert-rules?tenant_id=1
{
  "name": "Riesgo Alto Santiago",
  "territory_filter": "Santiago",
  "min_prob": 0.7,
  "min_confidence": 0.5,
  "enabled": true
}

# Actualizar regla
PUT /alert-rules/{id}

# Eliminar regla
DELETE /alert-rules/{id}

# Agregar comentario a alerta
POST /alert-rules/{alert_id}/comments
{
  "user_name": "Ana García",
  "comment": "Revisado. Escalar a equipo de crisis."
}

# Listar comentarios
GET /alert-rules/{alert_id}/comments

# Actualizar status de alerta
PATCH /alert-rules/{alert_id}/status?status=acked
```

### Señales (filtros extendidos)
```bash
# Filtrar por territorio, tópico y días
GET /signals?tenant_id=1&territory=Santiago&topic=socioambiental&days=7
```

## 🧪 Testing

Ejecutar tests:
```bash
cd backend
pytest tests/ -v
```

Tests incluidos:
- ✅ `test_scoring.py`: Scoring, sentiment, credibilidad
- ✅ `test_sentiment.py`: VADER sentiment analysis
- ✅ `test_simhash.py`: Near-duplicate detection

## 📈 Flujo de Datos v2.0

```
1. INGESTA (cada 30 min)
   RSS → Normalize HTML → SimHash dedup check → Sentiment analysis
   → DB Insert → NLP Topics → Territories (DB matching) → Commit

2. ANÁLISIS DE RIESGO (cada 60 min)
   Señales (7 días) → Scoring (+ sentiment + credibility)
   → Agregación por territorio → Time series comparison
   → Anomaly detection → RiskSnapshot con trend

3. ALERTAS (cada 15 min)
   RiskSnapshot → Evaluar reglas → Deduplication check
   → Insert AlertEvent → Webhook POST (con trend/anomaly)

4. VISUALIZACIÓN (Real-time)
   Frontend → API REST → Dashboard/Mapa/Señales/Alertas/Config
```

## 🔐 Notas de Ética y Compliance

**⚠️ IMPORTANTE:**
- Este sistema **NO predice** eventos futuros
- Estima **probabilidad de riesgo** basada en señales públicas
- Requiere **validación humana** antes de tomar acciones
- **NO usar** para decisiones automatizadas
- Cumplir con regulaciones de privacidad (GDPR/CCPA)
- Realizar **auditorías de sesgo** periódicas
- Implementar **transparencia** en scoring (drivers JSON)

## 🔄 Próximos Pasos Sugeridos

1. **ML Model**: Entrenar clasificador supervisado (si hay datos etiquetados)
2. **Multi-channel Ingestion**: Twitter API, Telegram, WhatsApp
3. **Predictive Forecasting**: ARIMA/LSTM para proyecciones temporales
4. **Advanced NER**: spaCy modelo en español (es_core_news_lg)
5. **Graph Analysis**: NetworkX para detectar clusters de tópicos
6. **User Management**: Autenticación JWT + roles (admin/analyst/viewer)
7. **Real-time Notifications**: WebSockets para alertas push
8. **Export PDF**: Generación de reportes ejecutivos

## 📝 Changelog v2.0

### Added
- ✅ Sentiment analysis (VADER)
- ✅ SimHash near-duplicate detection
- ✅ Dynamic territories (DB + geocoding)
- ✅ Source credibility scoring
- ✅ Time series trend analysis
- ✅ Anomaly detection
- ✅ Alert deduplication
- ✅ Comment system for alerts
- ✅ Interactive map (Leaflet)
- ✅ Advanced filters (territory/topic/days)
- ✅ CRUD panel for alert rules
- ✅ Unit tests (pytest)

### Changed
- ⚙️ Scoring formula: incorporates sentiment + credibility
- ⚙️ Alert explanations: include trend + anomaly indicators
- ⚙️ API: CORS enabled for development
- ⚙️ Frontend: 5 tabs (Resumen/Mapa/Señales/Alertas/Configuración)

### Fixed
- 🐛 Duplicate alerts (deduplication window)
- 🐛 Missing territories (DB-based system)
- 🐛 Inconsistent sentiment handling

---

**v2.0.0 Enhanced** - Plataforma de Inteligencia Territorial
Para soporte consulta la [documentación de API](http://localhost:8000/docs)
