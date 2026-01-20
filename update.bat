@echo off
echo ==========================================
echo Actualizacion: Territorios de Chile v2.0
echo ==========================================
echo.

REM Paso 1: Detener contenedores
echo [1/4] Deteniendo contenedores actuales...
docker compose down -v
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron detener los contenedores
    pause
    exit /b 1
)
echo OK: Contenedores detenidos
echo.

REM Paso 2: Reconstruir imagenes
echo [2/4] Reconstruyendo imagenes Docker (esto puede tardar unos minutos)...
docker compose build --no-cache
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron reconstruir las imagenes
    pause
    exit /b 1
)
echo OK: Imagenes reconstruidas
echo.

REM Paso 3: Levantar servicios
echo [3/4] Levantando servicios...
docker compose up -d
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron levantar los servicios
    pause
    exit /b 1
)
echo OK: Servicios levantados
echo.

REM Paso 4: Esperar a que el backend este listo
echo [4/4] Esperando a que el backend este listo...
timeout /t 10 /nobreak > nul
echo OK: Esperando completado
echo.

echo ==========================================
echo Actualizacion completada
echo ==========================================
echo.
echo Accesos:
echo   - Frontend:  http://localhost:3000
echo   - Backend:   http://localhost:8000
echo   - API Docs:  http://localhost:8000/docs
echo.
echo Comandos utiles:
echo   - Ver logs:           docker compose logs -f backend
echo   - Detener servicios:  docker compose down
echo.
pause
