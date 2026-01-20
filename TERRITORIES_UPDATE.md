# Actualización: Base de Datos de Territorios de Chile

## 📊 Resumen de Cambios

Se ha extendido la base de datos de territorios para incluir **TODAS** las divisiones administrativas de Chile:

- ✅ **16 Regiones** con coordenadas y aliases
- ✅ **346 Comunas** organizadas jerárquicamente
- ✅ **Relaciones padre-hijo** (Región → Comuna)
- ✅ **Aliases y abreviaciones** para mejor matching

---

## 🗺️ Cobertura Completa

### Regiones de Chile

| Región | Código | Comunas | Coordenadas Capital |
|--------|--------|---------|---------------------|
| **Arica y Parinacota** | XV | 4 | -18.4746, -70.2979 |
| **Tarapacá** | I | 7 | -20.2307, -70.1355 |
| **Antofagasta** | II | 9 | -23.6509, -70.3975 |
| **Atacama** | III | 9 | -27.3664, -70.3314 |
| **Coquimbo** | IV | 15 | -29.9533, -71.3395 |
| **Valparaíso** | V | 38 | -33.0472, -71.6127 |
| **Metropolitana** | RM | 52 | -33.4489, -70.6693 |
| **O'Higgins** | VI | 33 | -34.5755, -71.0022 |
| **Maule** | VII | 30 | -35.4264, -71.6554 |
| **Ñuble** | XVI | 21 | -36.6064, -72.1036 |
| **Biobío** | VIII | 33 | -36.8270, -73.0498 |
| **Araucanía** | IX | 32 | -38.7359, -72.5904 |
| **Los Ríos** | XIV | 12 | -39.8142, -73.2458 |
| **Los Lagos** | X | 30 | -41.4693, -72.9424 |
| **Aysén** | XI | 10 | -45.4014, -72.6936 |
| **Magallanes** | XII | 11 | -53.1638, -70.9171 |

**Total: 346 comunas en 16 regiones**

---

## 🔄 Cómo Actualizar la Base de Datos

Dado que ya tienes una base de datos con territorios antiguos, necesitas recrearla:

### **Opción 1: Recrear Base de Datos (Recomendado para desarrollo)**

```bash
# Detener contenedores
docker compose down

# Eliminar volúmenes (BORRA TODOS LOS DATOS)
docker compose down -v

# Levantar con nuevos territorios
docker compose up --build
```

**Resultado esperado en los logs:**
```
backend-1  | Seeding Chile territories (16 regiones + 346 comunas)...
backend-1  | ✓ Seeded 362 territories
backend-1  | ✓ Seeded 3 RSS sources
backend-1  | ✓ Seeded alert rules
```

---

### **Opción 2: Migración Manual (Si necesitas preservar datos)**

Si tienes datos importantes que no quieres perder:

#### 1. Conectarse a la base de datos

```bash
docker exec -it territorial-mvp-db-1 psql -U territorial_user -d territorial_db
```

#### 2. Eliminar territorios antiguos

```sql
-- Eliminar territorios antiguos (conserva señales y alertas)
DELETE FROM signal_territories;
DELETE FROM territories WHERE tenant_id = 1;
```

#### 3. Reiniciar el backend

```bash
docker compose restart backend
```

El backend detectará que no hay territorios y ejecutará automáticamente el seed con los 362 nuevos territorios.

---

## 🎯 Ejemplos de Aliases Incluidos

### Región Metropolitana
```json
{
  "name": "Metropolitana de Santiago",
  "aliases": ["RM", "Región Metropolitana", "Santiago", "Metro", "Stgo"]
}
```

### Comunas de Santiago
- **Santiago Centro**: ["Stgo", "Santiago Centro"]
- **Providencia**: ["Provi"]
- **Pedro Aguirre Cerda**: ["PAC"]
- **Las Condes**: []
- **Puente Alto**: []

### Otras Regiones
- **Valparaíso**: ["V Región", "Región V", "Quinta Región", "V", "Valpo"]
- **Biobío**: ["VIII Región", "Región VIII", "Octava Región", "VIII", "Bío-Bío"]
- **Araucanía**: ["IX Región", "Región IX", "Novena Región", "IX", "La Araucanía"]

---

## 📂 Estructura de Datos

### Base de Datos

```sql
territories
├── id (serial)
├── tenant_id (int)
├── name (varchar) -- "Santiago", "Valparaíso", etc.
├── level (varchar) -- "región" o "comuna"
├── parent_id (int) -- NULL para regiones, region.id para comunas
├── latitude (float)
├── longitude (float)
├── aliases_json (text) -- JSON array de aliases
└── enabled (boolean)
```

### Jerarquía

```
Metropolitana de Santiago (región, parent_id=NULL)
├── Santiago (comuna, parent_id=1)
├── Providencia (comuna, parent_id=1)
├── Las Condes (comuna, parent_id=1)
├── Maipú (comuna, parent_id=1)
└── ... (48 comunas más)

Valparaíso (región, parent_id=NULL)
├── Valparaíso (comuna, parent_id=2)
├── Viña del Mar (comuna, parent_id=2)
├── Quilpué (comuna, parent_id=2)
└── ... (35 comunas más)
```

---

## 🔍 Matching de Territorios Mejorado

### Antes (8 territorios hardcoded)
```python
# Solo tenías 8 ubicaciones
territorios = ["Santiago", "Valparaíso", "Antofagasta", ...]
```

### Ahora (362 territorios en BD)
```python
# Sistema inteligente con:
1. Matching exacto por nombre
2. Matching por aliases
3. Fuzzy matching (≥92% similitud)
4. Jerarquía región-comuna
```

### Ejemplos de Detección

**Texto de noticia:**
> "Protesta en la RM bloquea carretera..."

**Sistema detecta:**
- Territorio: "Metropolitana de Santiago"
- Nivel: región
- Confianza: 0.95 (match exacto por alias "RM")

**Texto de noticia:**
> "Conflicto ambiental en Conce afecta a comunidades..."

**Sistema detecta:**
- Territorio: "Concepción"
- Nivel: comuna
- Confianza: 0.9 (match por alias "Conce")

---

## 🗺️ Visualización en Mapa

Ahora el mapa mostrará:

✅ **16 marcadores regionales** con coordenadas precisas
✅ **346 marcadores comunales** (cuando hay señales)
✅ **Círculos de riesgo** proporcionales a probabilidad
✅ **Jerarquía visual** (zoom región → zoom comuna)

---

## 📊 Estadísticas

### Antes
- Territorios: 8
- Cobertura: ~5% de Chile
- Matching: Diccionario hardcoded

### Ahora
- Territorios: 362 (16 regiones + 346 comunas)
- Cobertura: 100% de Chile
- Matching: Base de datos + fuzzy + aliases
- Jerarquía: Sí (región → comuna)
- Geocoding: Sí (lat/lon para todos)

---

## 🧪 Verificación Post-Actualización

Después de actualizar, verifica:

### 1. Contar territorios

```bash
curl http://localhost:8000/territories?tenant_id=1 | jq '. | length'
```

**Esperado:** 362

### 2. Ver regiones

```bash
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.level=="región") | .name]'
```

**Esperado:** Array con 16 regiones

### 3. Ver comunas de Santiago

```bash
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.level=="comuna") | .name]' | grep -i santiago
```

**Esperado:** 52 comunas de la RM

### 4. Verificar jerarquía

```bash
# Ver una región y sus comunas
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.name=="Metropolitana de Santiago")]'
```

**Esperado:** Región con parent_id=null

---

## 🎯 Beneficios

1. **Precisión territorial**: Matching exacto de 346 comunas vs 8 ciudades
2. **Análisis jerárquico**: Puedes agregar riesgo por comuna → región
3. **Geocoding preciso**: Coordenadas para todas las ubicaciones
4. **Mejor UX**: Mapa completo de Chile con todas las comunas
5. **Escalabilidad**: Fácil agregar localidades rurales bajo cada comuna

---

## 🚀 Próximos Pasos Opcionales

1. **Agregar localidades rurales**: Puedes extender el catálogo con pueblos y aldeas
2. **Geocoding automático**: Integrar API de geocoding para ubicaciones no catalogadas
3. **Búsqueda avanzada**: Filtros por región, provincia, etc.
4. **Mapas de calor**: Visualización de riesgo agregado por región

---

## 📝 Archivo de Datos

Todos los territorios están definidos en:
```
backend/app/data/chile_territories.py
```

**Formato:**
```python
CHILE_TERRITORIES = [
    {
        "name": "Nombre Región",
        "level": "región",
        "lat": -XX.XXXX,
        "lon": -XX.XXXX,
        "aliases": ["Alias1", "Alias2"],
        "comunas": [
            {"name": "Comuna 1", "lat": -XX.XXXX, "lon": -XX.XXXX, "aliases": []},
            {"name": "Comuna 2", "lat": -XX.XXXX, "lon": -XX.XXXX, "aliases": []},
        ]
    },
    # ... 15 regiones más
]
```

---

¿Preguntas? Revisa los logs del backend para ver el seeding en acción. 🎉
