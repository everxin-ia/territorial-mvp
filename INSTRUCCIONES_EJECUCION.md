# Instrucciones de Ejecución - Plataforma Inteligencia Territorial

## Requisitos Previos

- **Docker Desktop** instalado y en ejecución
  - Windows: [Descargar Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Mac: [Descargar Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Linux: `sudo apt-get install docker.io docker-compose` (Ubuntu/Debian)

## Paso 1: Configurar Variables de Entorno

El sistema requiere una API key de OpenAI. Crea el archivo de configuración:

```bash
# Copia el archivo de ejemplo
cp backend/.env.example backend/.env

# Edita el archivo backend/.env y reemplaza con tu API key real
# OPENAI_API_KEY=sk-proj-TU_API_KEY_REAL_AQUI
```

**Nota:** Si no tienes una API key de OpenAI, puedes obtener una en https://platform.openai.com/api-keys

## Paso 2: Ejecutar el Sistema

### Opción A: Primera Vez (Construcción Completa)

```bash
# Construir y levantar todos los servicios
docker compose up --build
```

### Opción B: Ejecuciones Posteriores

```bash
# Levantar servicios sin reconstruir
docker compose up
```

### Opción C: Modo Detached (en segundo plano)

```bash
# Ejecutar en background
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f
```

## Paso 3: Acceder a la Aplicación

Una vez que los contenedores estén corriendo, espera unos segundos y accede a:

- **Frontend (Interfaz Web):** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **Backend API:** http://localhost:8000
- **Base de Datos PostgreSQL:** localhost:5432
  - Usuario: `postgres`
  - Contraseña: `postgres`
  - Base de datos: `territorial`

## Verificación de Funcionamiento

Deberías ver en los logs algo como:

```
backend-1  | Seeding Chile territories (16 regiones + 346 comunas)...
backend-1  | ✓ Seeded 362 territories
backend-1  | ✓ Seeded 3 RSS sources
backend-1  | ✓ Seeded alert rules
backend-1  | INFO:     Application startup complete.
```

## Comandos Útiles

### Ver logs en tiempo real
```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo frontend
docker compose logs -f frontend
```

### Detener los servicios
```bash
# Detener servicios (mantiene datos)
docker compose down

# Detener y eliminar volúmenes (limpia base de datos)
docker compose down -v
```

### Reiniciar un servicio específico
```bash
docker compose restart backend
docker compose restart frontend
```

### Reconstruir después de cambios en código
```bash
# Detener todo
docker compose down

# Reconstruir sin caché
docker compose build --no-cache

# Levantar de nuevo
docker compose up
```

### Acceder al contenedor backend
```bash
docker compose exec backend bash
```

### Ver estado de los contenedores
```bash
docker compose ps
```

## Solución de Problemas

### Error: "Cannot connect to the Docker daemon"
- **Solución:** Asegúrate de que Docker Desktop esté corriendo
- En Windows/Mac: Inicia Docker Desktop desde el menú de aplicaciones
- En Linux: `sudo systemctl start docker`

### Error: "Port is already allocated"
Otro servicio está usando los puertos 5173, 8000 o 5432.

```bash
# Linux/Mac - Ver qué está usando el puerto
lsof -i :8000
lsof -i :5173
lsof -i :5432

# Windows PowerShell
Get-NetTCPConnection -LocalPort 8000
```

### Error: "OPENAI_API_KEY not found"
- Asegúrate de haber creado el archivo `backend/.env`
- Verifica que contiene tu API key real de OpenAI

### La base de datos está corrupta o tiene errores
```bash
# Limpiar todo y empezar de cero
docker compose down -v
docker compose up --build
```

### Cambios en código no se reflejan
```bash
# Reconstruir las imágenes
docker compose down
docker compose build --no-cache
docker compose up
```

## Características del Sistema

Una vez ejecutándose, el sistema incluye:

- ✅ **362 territorios de Chile** (16 regiones + 346 comunas)
- ✅ **Análisis de sentimiento** con VADER
- ✅ **Detección de duplicados** con SimHash
- ✅ **Mapa interactivo** con Leaflet
- ✅ **Sistema de alertas** configurable
- ✅ **Ingesta automática RSS** cada 30 minutos
- ✅ **Cálculo de riesgo** cada 60 minutos
- ✅ **Evaluación de alertas** cada 15 minutos

## Pruebas Rápidas con cURL

```bash
# Verificar que el backend responde
curl http://localhost:8000/health

# Ver territorios cargados (debe devolver 362)
curl http://localhost:8000/territories?tenant_id=1 | jq '. | length'

# Ver todas las regiones
curl http://localhost:8000/territories?tenant_id=1 | jq '[.[] | select(.level=="región") | .name]'

# Ver señales recientes
curl http://localhost:8000/signals?tenant_id=1 | jq '.[0:5]'
```

## Desarrollo Local (Opcional)

Si prefieres ejecutar sin Docker:

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Recursos Adicionales

- **Documentación API Interactiva:** http://localhost:8000/docs
- **QUICKSTART.md:** Guía rápida de actualización
- **README.md:** Documentación completa del proyecto
- **AI_GEOSPARSING.md:** Detalles de geolocalización

## Soporte

Si encuentras problemas:
1. Revisa los logs: `docker compose logs -f`
2. Verifica que Docker esté corriendo
3. Asegúrate de tener el archivo `.env` configurado
4. Intenta reconstruir desde cero: `docker compose down -v && docker compose up --build`
