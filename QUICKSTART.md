# Guía Rápida - Actualización con Territorios de Chile

## Problema Común: ImportError

Si ves este error:
```
ImportError: cannot import name 'match_territories' from 'app.services.nlp.territories'
```

O este otro:
```
ModuleNotFoundError: No module named 'rapidfuzz'
```

**Solución:** Debes reconstruir los contenedores Docker para instalar las nuevas dependencias.

## Pasos para Actualizar

### 1. Detener y limpiar contenedores actuales
```bash
docker compose down -v
```

**Nota:** La opción `-v` eliminará los volúmenes (incluida la base de datos). Si deseas preservar datos, omite `-v` pero ten en cuenta que necesitarás ejecutar migraciones SQL manualmente.

### 2. Reconstruir las imágenes Docker
```bash
docker compose build --no-cache
```

La opción `--no-cache` asegura que se reconstruya todo desde cero, incluyendo la instalación de nuevas dependencias Python:
- rapidfuzz==3.9.6
- spacy==3.7.2
- vaderSentiment==3.3.2
- simhash==2.1.2
- numpy==1.26.4

### 3. Levantar los servicios
```bash
docker compose up
```

O en modo detached:
```bash
docker compose up -d
```

### 4. Verificar que todo funciona

Deberías ver en los logs:
```
backend-1  | Seeding Chile territories (16 regiones + 346 comunas)...
backend-1  | ✓ Seeded 362 territories
backend-1  | ✓ Seeded 3 RSS sources
backend-1  | ✓ Seeded alert rules
backend-1  | INFO:     Application startup complete.
```

### 5. Probar el sistema

```bash
# Ver territorios cargados (debe devolver 362)
curl http://localhost:8000/territories?tenant_id=1 | jq '. | length'

# Ver todas las regiones
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.level=="región") | .name]'

# Ver comunas de la Región Metropolitana
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.level=="comuna" and .parent_id!=null) | .name] | .[0:10]'
```

## Comandos Útiles

### Ver logs en tiempo real
```bash
docker compose logs -f backend
```

### Entrar al contenedor backend
```bash
docker compose exec backend bash
```

### Verificar dependencias instaladas
```bash
docker compose exec backend pip list | grep -E "rapidfuzz|spacy|vader|simhash"
```

Deberías ver:
```
rapidfuzz                  3.9.6
simhash                    2.1.2
spacy                      3.7.2
vaderSentiment             3.3.2
```

### Reiniciar solo un servicio
```bash
docker compose restart backend
```

## Solución de Problemas

### Error: "column does not exist"
Si ves errores sobre columnas faltantes, necesitas recrear la base de datos:
```bash
docker compose down -v
docker compose up --build
```

### Error: "Docker daemon not running"
En Windows, asegúrate de que Docker Desktop esté iniciado y corriendo.

### Error de permisos en Linux
```bash
sudo docker compose down -v
sudo docker compose up --build
```

### Verificar que los puertos estén libres
```bash
# En Linux/Mac
lsof -i :8000
lsof -i :5432

# En Windows (PowerShell)
Get-NetTCPConnection -LocalPort 8000
Get-NetTCPConnection -LocalPort 5432
```

## Acceder a la Aplicación

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432 (usuario: `postgres`, password: `postgres`)

## Resumen de la Actualización

✅ **362 territorios** (16 regiones + 346 comunas)
✅ **Cobertura 100%** de Chile
✅ **Matching inteligente** con aliases y fuzzy search
✅ **Jerarquía** región → comuna
✅ **Geocoding** completo para mapas
✅ **Análisis de sentimiento** con VADER
✅ **Deduplicación** con SimHash
✅ **Time series** y detección de anomalías
