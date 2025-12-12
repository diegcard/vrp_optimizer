# 🚚 VRP Optimizer - DockerHub Deployment Guide

## 📋 Descripción

Sistema de optimización de rutas de vehículos (VRP) usando Reinforcement Learning, con PostgreSQL/PostGIS, GraphHopper, Redis, y monitoreo con Prometheus/Grafana.

## 🐳 Imágenes en DockerHub

| Servicio | Imagen | Descripción |
|----------|--------|-------------|
| Backend | [`diegcard/vrp-backend`](https://hub.docker.com/r/diegcard/vrp-backend) | FastAPI + DQN Agent |
| Frontend | [`diegcard/vrp-frontend`](https://hub.docker.com/r/diegcard/vrp-frontend) | React + Nginx |

---

## ☁️ Despliegue en AWS EC2

### 1. Conectarse a la instancia EC2

```bash
ssh -i "tu-llave.pem" ec2-user@tu-ip-publica
# o para Ubuntu:
ssh -i "tu-llave.pem" ubuntu@tu-ip-publica
```

### 2. Instalar Docker y Docker Compose

```bash
# Para Amazon Linux 2 / Amazon Linux 2023
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Cerrar sesión y volver a conectarse para aplicar el grupo docker
exit
```

```bash
# Para Ubuntu
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
exit
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/diegcard/vrp-optimizer.git
cd vrp-optimizer
```

### 4. Descargar el mapa OSM (GraphHopper)

```bash
mkdir -p graphhopper/data
cd graphhopper/data
wget https://download.geofabrik.de/south-america/colombia-latest.osm.pbf
cd ../..
```

### 5. Hacer Pull de las imágenes desde DockerHub

```bash
# Descargar las imágenes
docker pull diegcard/vrp-backend:latest
docker pull diegcard/vrp-frontend:latest

# O usar docker-compose para descargar todas
docker-compose -f docker-compose.prod.yml pull
```

### 6. (RECOMENDADO) Crear memoria swap para EC2

```bash
# Crear archivo de swap de 2GB (ayuda a evitar OOM kills)
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Verificar que el swap esté activo
free -h

# Para que el swap persista después de reiniciar
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 7. Iniciar los servicios

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 8. Verificar que todo esté corriendo

```bash
# Ver estado de todos los servicios
docker-compose -f docker-compose.prod.yml ps

# Ver logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs solo de GraphHopper (buscar "Started server")
docker logs -f vrp-graphhopper

# Esperar hasta ver este mensaje en GraphHopper:
# "Started server at HTTP 0.0.0.0:8989"
```

**Nota:** GraphHopper puede tardar 2-3 minutos en cargar el mapa OSM en la primera ejecución.

**Verificación de servicios healthy:**
```bash
# Todos deben mostrar (healthy) excepto Prometheus y Grafana
docker-compose -f docker-compose.prod.yml ps

# Verificar que el backend responde
curl http://localhost:8000/api/v1/health/

# Verificar GraphHopper
curl http://localhost:8989/health
```

### 9. Configurar Security Groups en AWS

Asegúrate de abrir los siguientes puertos en tu Security Group:

| Puerto | Servicio | Acceso |
|--------|----------|--------|
| 22 | SSH | Tu IP |
| 80 | Frontend | 0.0.0.0/0 |
| 8000 | Backend API | 0.0.0.0/0 |
| 8989 | GraphHopper | 0.0.0.0/0 (opcional) |
| 3001 | Grafana | Tu IP |
| 9090 | Prometheus | Tu IP |

### 10. Acceder a la aplicación

Una vez configurados los Security Groups:

- **Frontend**: `http://tu-ip-publica`
- **Backend API**: `http://tu-ip-publica:8000`
- **Swagger Docs**: `http://tu-ip-publica:8000/docs`
- **Grafana**: `http://tu-ip-publica:3001` (admin / admin123)
- **Prometheus**: `http://tu-ip-publica:9090`

**Ejemplo con tu EC2:**
- Frontend: `http://44.222.217.128`
- API Docs: `http://44.222.217.128:8000/docs`

---

## 🚀 Inicio Rápido (Local)

### 1. Clonar y configurar

```bash
# Clonar repositorio (solo necesitas los archivos de configuración)
git clone https://github.com/tuusuario/vrp-optimizer.git
cd vrp-optimizer

# Crear archivo de configuración
cp .env.example .env

# Editar .env con tu usuario de DockerHub
# DOCKERHUB_USERNAME=tuusuario
```

### 2. Configurar datos de GraphHopper

Asegúrate de tener el archivo OSM en `graphhopper/data/`:
```bash
# Descargar mapa de Colombia (o tu región)
mkdir -p graphhopper/data
cd graphhopper/data
wget https://download.geofabrik.de/south-america/colombia-latest.osm.pbf
```

### 3. Ejecutar todo con un solo comando

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verificar servicios

```bash
# Ver estado de los contenedores
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🌐 URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend | http://localhost | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| GraphHopper | http://localhost:8989 | - |
| Grafana | http://localhost:3001 | admin / admin123 |
| Prometheus | http://localhost:9090 | - |

## 🔧 Para Desarrolladores

### Construir y subir imágenes a DockerHub

**Windows:**
```powershell
# Configurar variables
$env:DOCKERHUB_USERNAME="tu-usuario-dockerhub"
$env:VERSION="1.0.0"

# Login en DockerHub
docker login

# Ejecutar script de build
.\build-and-push.bat
```

**Linux/Mac:**
```bash
# Configurar variables
export DOCKERHUB_USERNAME="tu-usuario-dockerhub"
export VERSION="1.0.0"

# Login en DockerHub
docker login

# Ejecutar script de build
chmod +x build-and-push.sh
./build-and-push.sh
```

### Solo construir (sin push)

```bash
# Windows
set PUSH_TO_HUB=false
.\build-and-push.bat

# Linux/Mac
PUSH_TO_HUB=false ./build-and-push.sh
```

## 📁 Estructura de Archivos Necesarios

Para que el proyecto funcione, necesitas estos archivos locales:

```
vrp-optimizer/
├── .env                         # Variables de entorno
├── docker-compose.prod.yml      # Compose de producción
├── database/
│   └── init.sql                 # Script de inicialización DB
├── graphhopper/
│   ├── config.yml               # Configuración GraphHopper
│   └── data/
│       └── colombia-latest.osm.pbf  # Mapa OSM
├── models/                      # Modelos RL entrenados
│   └── vrp_dqn_v1.pt
└── monitoring/
    ├── prometheus.yml           # Config Prometheus
    └── grafana/
        └── dashboards/          # Dashboards Grafana
```

## 🔒 Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DOCKERHUB_USERNAME` | Usuario de DockerHub | `tuusuario` |
| `VERSION` | Versión de las imágenes | `latest` |
| `POSTGRES_USER` | Usuario PostgreSQL | `vrp_user` |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | `vrp_password_123` |
| `POSTGRES_DB` | Nombre de la base de datos | `vrp_routes` |
| `GRAFANA_USER` | Usuario Grafana | `admin` |
| `GRAFANA_PASSWORD` | Contraseña Grafana | `admin123` |

## 🛑 Detener Servicios

```bash
# Detener todos los servicios
docker-compose -f docker-compose.prod.yml down

# Detener y eliminar volúmenes (¡CUIDADO! Elimina datos)
docker-compose -f docker-compose.prod.yml down -v
```

## 🔄 Actualizar Imágenes

```bash
# Descargar últimas versiones
docker-compose -f docker-compose.prod.yml pull

# Reiniciar con nuevas imágenes
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Healthchecks

Todos los servicios tienen healthchecks configurados:

- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **GraphHopper**: HTTP `/health`
- **Backend**: HTTP `/api/v1/health/`
- **Frontend**: HTTP `/`

## ⚠️ Solución de Problemas

### GraphHopper no inicia o se reinicia continuamente
```bash
# Verificar que el archivo OSM existe y tiene el tamaño correcto (~294MB para Colombia)
ls -lh graphhopper/data/colombia-latest.osm.pbf

# Ver logs para identificar el problema
docker logs -f vrp-graphhopper

# Si ves "graph.flag_encoders is deprecated":
# - Asegúrate de tener la última versión del config.yml
# - El archivo debe usar graph.vehicles en lugar de graph.flag_encoders

# Si GraphHopper se reinicia antes de completar la carga:
# - La primera carga puede tardar 2-3 minutos
# - Espera a ver el mensaje "Started server at HTTP 0.0.0.0:8989"
# - El healthcheck está configurado con 180s de período inicial

# Reiniciar solo GraphHopper
docker-compose -f docker-compose.prod.yml restart graphhopper
```

### Base de datos no conecta
```bash
# Verificar que PostgreSQL está healthy
docker-compose -f docker-compose.prod.yml ps postgres

# Reiniciar solo PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

### Frontend no carga API
```bash
# Verificar que el backend está corriendo
curl http://localhost:8000/api/v1/health/

# Ver logs del frontend
docker-compose -f docker-compose.prod.yml logs frontend
```

## 📝 Licencia

Este proyecto está bajo la licencia MIT.
