@echo off
REM ===========================================
REM Script para construir y subir imágenes a DockerHub
REM VRP Optimizer - Vehicle Routing Problem
REM Windows PowerShell / CMD Version
REM ===========================================

setlocal enabledelayedexpansion

REM Configuración por defecto
if "%DOCKERHUB_USERNAME%"=="" set DOCKERHUB_USERNAME=tuusuario
if "%VERSION%"=="" set VERSION=latest
if "%PUSH_TO_HUB%"=="" set PUSH_TO_HUB=true

REM Nombres de las imágenes
set BACKEND_IMAGE=%DOCKERHUB_USERNAME%/vrp-backend
set FRONTEND_IMAGE=%DOCKERHUB_USERNAME%/vrp-frontend

echo ===========================================
echo    VRP Optimizer - Build ^& Push to DockerHub
echo ===========================================
echo.

REM ===========================================
REM Build Backend
REM ===========================================
echo [1/4] Construyendo imagen del Backend...
echo       Imagen: %BACKEND_IMAGE%:%VERSION%
docker build -t "%BACKEND_IMAGE%:%VERSION%" ./backend
if errorlevel 1 (
    echo ERROR: Fallo al construir el backend
    exit /b 1
)
docker tag "%BACKEND_IMAGE%:%VERSION%" "%BACKEND_IMAGE%:latest"
echo [OK] Backend construido exitosamente
echo.

REM ===========================================
REM Build Frontend
REM ===========================================
echo [2/4] Construyendo imagen del Frontend...
echo       Imagen: %FRONTEND_IMAGE%:%VERSION%
docker build -t "%FRONTEND_IMAGE%:%VERSION%" ./frontend
if errorlevel 1 (
    echo ERROR: Fallo al construir el frontend
    exit /b 1
)
docker tag "%FRONTEND_IMAGE%:%VERSION%" "%FRONTEND_IMAGE%:latest"
echo [OK] Frontend construido exitosamente
echo.

REM ===========================================
REM Push to DockerHub
REM ===========================================
if "%PUSH_TO_HUB%"=="true" (
    echo [3/4] Subiendo Backend a DockerHub...
    docker push "%BACKEND_IMAGE%:%VERSION%"
    docker push "%BACKEND_IMAGE%:latest"
    echo [OK] Backend subido a DockerHub
    echo.

    echo [4/4] Subiendo Frontend a DockerHub...
    docker push "%FRONTEND_IMAGE%:%VERSION%"
    docker push "%FRONTEND_IMAGE%:latest"
    echo [OK] Frontend subido a DockerHub
) else (
    echo [3/4] Saltando push a DockerHub (PUSH_TO_HUB=false)
    echo [4/4] Saltando push a DockerHub (PUSH_TO_HUB=false)
)

echo.
echo ===========================================
echo    Build completado exitosamente!
echo ===========================================
echo.
echo Imagenes creadas:
echo   - %BACKEND_IMAGE%:%VERSION%
echo   - %BACKEND_IMAGE%:latest
echo   - %FRONTEND_IMAGE%:%VERSION%
echo   - %FRONTEND_IMAGE%:latest
echo.
echo Para ejecutar el proyecto:
echo   1. Copia .env.example a .env
echo   2. Edita .env con tu usuario de DockerHub
echo   3. Ejecuta: docker-compose -f docker-compose.prod.yml up -d
echo.

endlocal
