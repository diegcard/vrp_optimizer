# 🚚 VRP Optimizer

## Sistema Inteligente de Optimización de Rutas para Logística de Última Milla

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1-EE4C2C.svg)](https://pytorch.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Sistema basado en la nube que utiliza **Deep Reinforcement Learning (DQN)** para resolver el problema de enrutamiento de vehículos (VRP) en la logística de última milla de Bogotá, Colombia.

---

## 📋 Información del Proyecto

| | |
|---|---|
| **Universidad** | Escuela Colombiana de Ingeniería Julio Garavito |
| **Materia** | Arquitectura Empresarial (AREP) |
| **Período** | 2025-2 |
| **Docente** | Luis Daniel Benavides |

### 👥 Integrantes

| Nombre | GitHub | Rol |
|--------|--------|-----|
| **Diego Alexander Cárdenas Beltrán** | [@diegcard](https://github.com/diegcard) | Desarrollador Full Stack & ML Engineer |
| **Alison Valderrama** | [@alisonvalderrama](https://github.com/alisonvalderrama) | Desarrolladora Backend & Data Engineer |

---

## 🎯 Planteamiento del Problema

### Contexto

La **logística de última milla** representa entre el **40% y 50%** del costo total de la cadena de suministro. En ciudades como Bogotá, con más de 8 millones de habitantes y una compleja infraestructura vial, la optimización de rutas de entrega se convierte en un desafío crítico.

### Problemática Identificada

1. **Crecimiento exponencial del e-commerce**: La pandemia aceleró la demanda de entregas a domicilio, aumentando la presión sobre las flotas de distribución.

2. **Congestión vehicular**: Bogotá presenta tiempos de desplazamiento hasta 3 veces mayores en horas pico, afectando directamente la eficiencia de las entregas.

3. **Costos operativos elevados**: Combustible, mantenimiento vehicular y tiempos improductivos representan pérdidas significativas.

4. **Impacto ambiental**: Rutas ineficientes generan mayor emisión de CO₂ y contribuyen al deterioro de la calidad del aire.

5. **Complejidad computacional**: El VRP es un problema **NP-hard**, lo que significa que encontrar la solución óptima para instancias grandes es computacionalmente intratable con métodos tradicionales.

### Preguntas de Investigación

- ¿Cómo puede el Reinforcement Learning adaptarse dinámicamente a las condiciones cambiantes del tráfico en Bogotá?
- ¿Qué mejoras en tiempo y distancia se pueden lograr comparado con métodos heurísticos tradicionales?
- ¿Es factible implementar un sistema de optimización en tiempo real basado en la nube?

---

## 💡 Solución Propuesta

### Enfoque

Desarrollamos un **sistema integral basado en la nube** que combina:

1. **Deep Q-Network (DQN)**: Agente de Reinforcement Learning que aprende políticas óptimas de enrutamiento mediante la interacción con un entorno simulado.

2. **Arquitectura de Microservicios**: Backend escalable con FastAPI que permite procesamiento asíncrono y alta disponibilidad.

3. **Integración con datos reales**: Uso de OpenStreetMap y OSRM para obtener rutas reales sobre la red vial de Bogotá.

4. **Interfaz intuitiva**: Dashboard en React con visualización en tiempo real de rutas sobre mapas interactivos.

### Características Principales

| Característica | Descripción |
|----------------|-------------|
| 🧠 **RL Training** | Entrenamiento de agentes DQN con replay buffer y target network |
| 🗺️ **Rutas Reales** | Integración con OSRM para seguir calles reales |
| 📊 **Dashboard** | Visualización en tiempo real con Leaflet |
| ⚡ **3 Métodos** | DQN, Greedy (vecino más cercano), OR-Tools |
| 🐳 **Containerizado** | Despliegue completo con Docker Compose |
| 📈 **Monitoreo** | Prometheus + Grafana para métricas |

### Algoritmo DQN

```
┌─────────────────────────────────────────────────────────────┐
│                    Deep Q-Network (DQN)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Estado (s)                    Red Neuronal                 │
│   ┌──────────────┐             ┌──────────────┐             │
│   │ • Posición   │             │   Input      │             │
│   │ • Visitados  │ ──────────► │   Layer      │             │
│   │ • Capacidad  │             │   (128)      │             │
│   │ • Demandas   │             └──────┬───────┘             │
│   │ • Distancias │                    │                     │
│   └──────────────┘             ┌──────▼───────┐             │
│                                │   Hidden     │             │
│                                │   (256)      │             │
│                                └──────┬───────┘             │
│                                       │                     │
│                                ┌──────▼───────┐             │
│   Acción (a)                   │   Output     │             │
│   ┌──────────────┐             │   Q-values   │             │
│   │ Cliente i    │ ◄────────── │   (n_clientes)             │
│   │ o Depot      │             └──────────────┘             │
│   └──────────────┘                                          │
│                                                              │
│   Recompensa: R = -distancia - penalización + bonus         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE                                    │
│                    ┌─────────────────────────┐                         │
│                    │   React 18 + TypeScript │                         │
│                    │   • Leaflet Maps        │                         │
│                    │   • TanStack Query      │                         │
│                    │   • Zustand State       │                         │
│                    │   • Tailwind CSS        │                         │
│                    └───────────┬─────────────┘                         │
│                                │ HTTP/REST                             │
└────────────────────────────────┼───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI + Python 3.11                       │   │
│  ├──────────────┬──────────────┬──────────────┬──────────────────┤   │
│  │  REST API    │  RL Engine   │  Optimization│   Services       │   │
│  │  /customers  │  DQN Agent   │  Greedy      │   GraphHopper    │   │
│  │  /vehicles   │  Environment │  OR-Tools    │   OSRM           │   │
│  │  /optimize   │  Training    │  Solver      │   Redis Cache    │   │
│  │  /training   │  PyTorch     │              │                  │   │
│  └──────────────┴──────────────┴──────────────┴──────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    OSRM      │  │  Prometheus  │
│   + PostGIS  │  │    Cache     │  │   Routing    │  │   + Grafana  │
│              │  │              │  │   (externo)  │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### Componentes

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Frontend** | React 18, TypeScript, Vite | Interfaz de usuario con mapas interactivos |
| **Backend** | FastAPI, Python 3.11 | API REST y lógica de negocio |
| **RL Engine** | PyTorch, Gymnasium | Entrenamiento y inferencia del agente DQN |
| **Base de Datos** | PostgreSQL 15 + PostGIS | Almacenamiento de datos geoespaciales |
| **Cache** | Redis 7 | Cache de sesiones y resultados de optimización |
| **Routing** | OSRM Public API | Cálculo de rutas sobre red vial real |
| **Monitoreo** | Prometheus + Grafana | Métricas y dashboards |

---

## 🚀 Guía de Instalación

### Requisitos Previos

- **Docker** y **Docker Compose** (v2.0+)
- **Git**
- **8 GB RAM** mínimo (16 GB recomendado para entrenamiento RL)
- **10 GB** de espacio en disco

### Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/diegcard/vrp_optimizer.git
cd vrp_optimizer

# 2. Iniciar todos los servicios
docker-compose up -d

# 3. Verificar que los servicios estén corriendo
docker-compose ps

# 4. Ver logs en tiempo real
docker-compose logs -f backend
```

### Acceso a los Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| 🖥️ **Frontend** | http://localhost:3000 | - |
| 🔌 **API Backend** | http://localhost:8000 | - |
| 📚 **API Docs (Swagger)** | http://localhost:8000/docs | - |
| 📊 **Grafana** | http://localhost:3001 | admin/admin |
| 📈 **Prometheus** | http://localhost:9090 | - |

---

## 📖 Manual de Usuario

### 1. Dashboard Principal

Vista general del sistema con:
- **Estadísticas**: Total de clientes, vehículos y rutas optimizadas
- **Mapa de Bogotá**: Visualización de puntos de entrega
- **Métricas del sistema**: CPU, memoria y latencia

### 2. Gestión de Clientes

| Acción | Descripción |
|--------|-------------|
| ➕ **Crear** | Añadir clientes con nombre, ubicación, demanda y prioridad |
| ✏️ **Editar** | Modificar información de clientes existentes |
| 🗑️ **Eliminar** | Remover clientes del sistema |
| 📍 **Mapa** | Click en el mapa para asignar coordenadas |

### 3. Gestión de Vehículos

Configurar la flota de distribución:
- **Capacidad**: Carga máxima en unidades
- **Velocidad**: Velocidad promedio en km/h
- **Costo por km**: Para cálculo de costos operativos

### 4. Optimización de Rutas

Tres métodos de optimización disponibles:

| Método | Descripción | Velocidad | Calidad |
|--------|-------------|-----------|---------|
| 🧠 **Reinforcement Learning** | Agente DQN entrenado | Media | Alta |
| ⚡ **Greedy** | Heurística del vecino más cercano | Rápida | Media |
| 🔧 **OR-Tools** | Solver de programación lineal de Google | Lenta | Óptima* |

**Opciones adicionales**:
- ✅ **Usar red de carreteras real**: Rutas siguen calles reales (OSRM)
- ❌ **Distancia euclidiana**: Líneas rectas (más rápido)

### 5. Entrenamiento del Agente RL

Entrenar el modelo DQN con configuración personalizada:

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `num_episodes` | 1000 | Número de episodios de entrenamiento |
| `learning_rate` | 0.001 | Tasa de aprendizaje del optimizador |
| `gamma` | 0.99 | Factor de descuento para recompensas futuras |
| `epsilon_start` | 1.0 | Exploración inicial (ε-greedy) |
| `epsilon_end` | 0.01 | Exploración final |
| `epsilon_decay` | 0.995 | Tasa de decaimiento de epsilon |
| `batch_size` | 64 | Tamaño del batch para entrenamiento |
| `buffer_size` | 10000 | Tamaño del replay buffer |

---

## 🔌 API Reference

### Endpoints Principales

#### Clientes
```http
GET    /api/v1/customers/          # Listar todos los clientes
POST   /api/v1/customers/          # Crear nuevo cliente
GET    /api/v1/customers/{id}/     # Obtener cliente por ID
PUT    /api/v1/customers/{id}/     # Actualizar cliente
DELETE /api/v1/customers/{id}/     # Eliminar cliente
```

#### Vehículos
```http
GET    /api/v1/vehicles/           # Listar todos los vehículos
POST   /api/v1/vehicles/           # Crear nuevo vehículo
PUT    /api/v1/vehicles/{id}/      # Actualizar vehículo
DELETE /api/v1/vehicles/{id}/      # Eliminar vehículo
```

#### Depósitos
```http
GET    /api/v1/depots/             # Listar depósitos
POST   /api/v1/depots/             # Crear depósito
```

#### Optimización
```http
POST   /api/v1/optimization/optimize/    # Ejecutar optimización
```

**Request Body:**
```json
{
  "depot_id": "uuid",
  "customer_ids": ["uuid1", "uuid2"],
  "vehicle_ids": ["uuid1"],
  "method": "rl",
  "use_real_roads": true
}
```

#### Entrenamiento
```http
POST   /api/v1/training/start/     # Iniciar entrenamiento
GET    /api/v1/training/status/    # Estado del entrenamiento
POST   /api/v1/training/stop/      # Detener entrenamiento
GET    /api/v1/training/models/    # Listar modelos guardados
GET    /api/v1/training/history/   # Historial de entrenamientos
```

---

## 📁 Estructura del Proyecto

```
vrp-optimizer/
├── 📂 backend/
│   ├── 📂 api/
│   │   └── 📂 routes/           # Endpoints REST
│   │       ├── customers.py
│   │       ├── vehicles.py
│   │       ├── depots.py
│   │       ├── optimization.py
│   │       └── training.py
│   ├── 📂 config/               # Configuración
│   ├── 📂 database/             # Modelos SQLAlchemy
│   ├── 📂 schemas/              # Schemas Pydantic
│   ├── 📂 services/             # Lógica de negocio
│   │   ├── optimization_service.py
│   │   └── training_service.py
│   ├── 📂 rl/                   # Reinforcement Learning
│   │   ├── dqn_agent.py         # Agente DQN
│   │   └── vrp_environment.py   # Entorno Gymnasium
│   ├── main.py                  # Entry point
│   ├── requirements.txt
│   └── Dockerfile
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/       # Componentes React
│   │   ├── 📂 pages/            # Páginas
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Customers.tsx
│   │   │   ├── Vehicles.tsx
│   │   │   ├── Optimization.tsx
│   │   │   └── Training.tsx
│   │   ├── 📂 hooks/            # Custom hooks
│   │   ├── 📂 store/            # Estado global (Zustand)
│   │   ├── 📂 api/              # Cliente API (Axios)
│   │   └── 📂 types/            # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── 📂 database/
│   └── init.sql                 # Schema inicial PostgreSQL
├── 📂 models/                   # Modelos DQN entrenados
│   └── vrp_dqn_v1.pt
├── 📂 monitoring/
│   ├── prometheus.yml
│   └── 📂 grafana/
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🐳 Comandos Docker

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver estado de los servicios
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs -f backend

# Reiniciar un servicio
docker-compose restart backend

# Reconstruir un servicio (después de cambios)
docker-compose up -d --build backend

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker-compose down -v
```

---

## 📊 Resultados Esperados

### Métricas de Rendimiento

| Métrica | Greedy | OR-Tools | DQN (entrenado) |
|---------|--------|----------|-----------------|
| Tiempo de cómputo | ~0.1s | ~5s | ~0.5s |
| Distancia total | Base | -15% vs Base | -10% vs Base |
| Escalabilidad | Alta | Baja | Alta |

### Casos de Uso Validados

- ✅ Optimización de 10-50 clientes con 3-5 vehículos
- ✅ Rutas reales sobre la red vial de Bogotá
- ✅ Entrenamiento de agentes DQN en < 30 minutos
- ✅ Visualización en tiempo real de rutas

---

## 🔬 Desarrollo Local

### Backend (sin Docker)

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (sin Docker)

```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.11** - Lenguaje principal
- **FastAPI** - Framework web asíncrono
- **PyTorch** - Deep Learning
- **Gymnasium** - Entorno RL
- **SQLAlchemy** - ORM
- **GeoAlchemy2** - Extensión geoespacial
- **aiohttp** - Cliente HTTP asíncrono

### Frontend
- **React 18** - UI Library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Leaflet** - Mapas interactivos
- **TanStack Query** - Data fetching
- **Zustand** - State management
- **Axios** - HTTP client

### Infraestructura
- **Docker & Docker Compose** - Containerización
- **PostgreSQL 15 + PostGIS** - Base de datos geoespacial
- **Redis 7** - Cache
- **OSRM** - Routing engine
- **Prometheus & Grafana** - Monitoreo

---

## 📚 Referencias

1. Mnih, V., et al. (2015). *Human-level control through deep reinforcement learning*. Nature.
2. Nazari, M., et al. (2018). *Reinforcement Learning for Solving the Vehicle Routing Problem*. NeurIPS.
3. Dantzig, G. B., & Ramser, J. H. (1959). *The Truck Dispatching Problem*. Management Science.
4. Google OR-Tools Documentation. https://developers.google.com/optimization
5. OpenStreetMap Contributors. https://www.openstreetmap.org

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- **Escuela Colombiana de Ingeniería Julio Garavito** por el apoyo académico
- **Prof. Luis Daniel Benavides** por la guía en arquitectura de software
- **OpenStreetMap** por los datos cartográficos de Colombia
- **OSRM** por el servicio público de routing

---

<div align="center">

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub ⭐**

Desarrollado con ❤️ por Diego Cárdenas & Alison Valderrama

Escuela Colombiana de Ingeniería Julio Garavito | 2025

</div>
