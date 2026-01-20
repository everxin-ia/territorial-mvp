#!/bin/bash

echo "=========================================="
echo "Actualización: Territorios de Chile v2.0"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paso 1: Detener contenedores
echo -e "${YELLOW}[1/4] Deteniendo contenedores actuales...${NC}"
docker compose down -v
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Contenedores detenidos${NC}"
else
    echo -e "${RED}✗ Error al detener contenedores${NC}"
    exit 1
fi
echo ""

# Paso 2: Reconstruir imágenes
echo -e "${YELLOW}[2/4] Reconstruyendo imágenes Docker (esto puede tardar unos minutos)...${NC}"
docker compose build --no-cache
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Imágenes reconstruidas${NC}"
else
    echo -e "${RED}✗ Error al reconstruir imágenes${NC}"
    exit 1
fi
echo ""

# Paso 3: Levantar servicios
echo -e "${YELLOW}[3/4] Levantando servicios...${NC}"
docker compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Servicios levantados${NC}"
else
    echo -e "${RED}✗ Error al levantar servicios${NC}"
    exit 1
fi
echo ""

# Esperar a que el backend esté listo
echo -e "${YELLOW}[4/4] Esperando a que el backend esté listo...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend está listo${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo -n "."
    sleep 2
done
echo ""

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}⚠ El backend está tardando en iniciar. Verifica los logs con: docker compose logs -f backend${NC}"
    echo ""
fi

# Verificar territorios
echo ""
echo -e "${YELLOW}Verificando territorios cargados...${NC}"
TERRITORY_COUNT=$(curl -s http://localhost:8000/territories?tenant_id=1 | jq '. | length' 2>/dev/null)

if [ ! -z "$TERRITORY_COUNT" ] && [ "$TERRITORY_COUNT" -eq 362 ]; then
    echo -e "${GREEN}✓ 362 territorios cargados correctamente${NC}"
else
    echo -e "${YELLOW}⚠ Se esperaban 362 territorios, se encontraron: $TERRITORY_COUNT${NC}"
    echo -e "${YELLOW}  Verifica los logs con: docker compose logs backend${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Actualización completada${NC}"
echo "=========================================="
echo ""
echo "Accesos:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Backend:   http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/docs"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs:           docker compose logs -f backend"
echo "  - Ver territorios:    curl http://localhost:8000/territories?tenant_id=1 | jq"
echo "  - Detener servicios:  docker compose down"
echo ""
