#!/bin/bash

# ===========================================
# Script para construir y subir imágenes a DockerHub
# VRP Optimizer - Vehicle Routing Problem
# ===========================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-tuusuario}"
VERSION="${VERSION:-latest}"
PUSH_TO_HUB="${PUSH_TO_HUB:-true}"

# Nombres de las imágenes
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/vrp-backend"
FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/vrp-frontend"

echo -e "${BLUE}==========================================="
echo -e "   VRP Optimizer - Build & Push to DockerHub"
echo -e "===========================================${NC}"
echo ""

# Verificar si el usuario está logueado en DockerHub
echo -e "${YELLOW}Verificando login en DockerHub...${NC}"
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo -e "${RED}No estás logueado en DockerHub. Ejecutando docker login...${NC}"
    docker login
fi

# ===========================================
# Build Backend
# ===========================================
echo ""
echo -e "${BLUE}[1/4] Construyendo imagen del Backend...${NC}"
echo -e "      Imagen: ${BACKEND_IMAGE}:${VERSION}"
docker build -t "${BACKEND_IMAGE}:${VERSION}" ./backend
docker tag "${BACKEND_IMAGE}:${VERSION}" "${BACKEND_IMAGE}:latest"
echo -e "${GREEN}✓ Backend construido exitosamente${NC}"

# ===========================================
# Build Frontend
# ===========================================
echo ""
echo -e "${BLUE}[2/4] Construyendo imagen del Frontend...${NC}"
echo -e "      Imagen: ${FRONTEND_IMAGE}:${VERSION}"
docker build -t "${FRONTEND_IMAGE}:${VERSION}" ./frontend
docker tag "${FRONTEND_IMAGE}:${VERSION}" "${FRONTEND_IMAGE}:latest"
echo -e "${GREEN}✓ Frontend construido exitosamente${NC}"

# ===========================================
# Push to DockerHub
# ===========================================
if [ "$PUSH_TO_HUB" = "true" ]; then
    echo ""
    echo -e "${BLUE}[3/4] Subiendo Backend a DockerHub...${NC}"
    docker push "${BACKEND_IMAGE}:${VERSION}"
    docker push "${BACKEND_IMAGE}:latest"
    echo -e "${GREEN}✓ Backend subido a DockerHub${NC}"

    echo ""
    echo -e "${BLUE}[4/4] Subiendo Frontend a DockerHub...${NC}"
    docker push "${FRONTEND_IMAGE}:${VERSION}"
    docker push "${FRONTEND_IMAGE}:latest"
    echo -e "${GREEN}✓ Frontend subido a DockerHub${NC}"
else
    echo ""
    echo -e "${YELLOW}[3/4] Saltando push a DockerHub (PUSH_TO_HUB=false)${NC}"
    echo -e "${YELLOW}[4/4] Saltando push a DockerHub (PUSH_TO_HUB=false)${NC}"
fi

# ===========================================
# Resumen
# ===========================================
echo ""
echo -e "${GREEN}==========================================="
echo -e "   ✓ Build completado exitosamente!"
echo -e "===========================================${NC}"
echo ""
echo -e "Imágenes creadas:"
echo -e "  - ${BACKEND_IMAGE}:${VERSION}"
echo -e "  - ${BACKEND_IMAGE}:latest"
echo -e "  - ${FRONTEND_IMAGE}:${VERSION}"
echo -e "  - ${FRONTEND_IMAGE}:latest"
echo ""
echo -e "${YELLOW}Para ejecutar el proyecto:${NC}"
echo -e "  1. Copia .env.example a .env"
echo -e "  2. Edita .env con tu usuario de DockerHub"
echo -e "  3. Ejecuta: docker-compose -f docker-compose.prod.yml up -d"
echo ""
