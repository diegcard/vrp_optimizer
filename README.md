    # VRP Optimizer - Sistema de Optimización de Rutas con Reinforcement Learning

Sistema inteligente de optimización de rutas para logística de última milla en Bogotá, Colombia. Utiliza Deep Q-Learning (DQN) para resolver el Vehicle Routing Problem (VRP) con restricciones de capacidad y ventanas de tiempo.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Leaflet)                   │
│   Dashboard │ Clientes │ Vehículos │ Optimización │ Entrenamiento   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  REST API    │  │  RL Engine   │  │  Services    │               │
│  │  Endpoints   │  │  (PyTorch)   │  │  (Async)     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │  GraphHopper │    │    Redis     │
│   + PostGIS  │    │   Routing    │    │    Cache     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 🚀 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose
- Git
- 8GB RAM mínimo (recomendado 16GB para entrenamiento RL)

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd vrp-optimizer
```

2. **Descargar el mapa de Colombia para GraphHopper**
```bash
# Crear directorio de datos
mkdir -p graphhopper/data

# Descargar el mapa de Colombia (OpenStreetMap)
wget -O graphhopper/data/colombia-latest.osm.pbf \
  https://download.geofabrik.de/south-america/colombia-latest.osm.pbf
```

3. **Iniciar los servicios**
```bash
docker-compose up -d
```

4. **Verificar que todos los servicios estén corriendo**
```bash
docker-compose ps
```

### Acceso a la Aplicación

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Interfaz de usuario |
| API Backend | http://localhost:8000 | API REST |
| API Docs | http://localhost:8000/docs | Documentación Swagger |
| GraphHopper | http://localhost:8989 | Motor de rutas |
| Grafana | http://localhost:3001 | Monitoreo |
| Prometheus | http://localhost:9090 | Métricas |

## 📖 Guía de Uso

### 1. Dashboard

Vista general del sistema con:
- Estadísticas de clientes, vehículos y rutas
- Mapa de Bogotá con puntos de entrega
- Métricas de rendimiento del sistema

### 2. Gestión de Clientes

- **Agregar clientes**: Click en el mapa o formulario manual
- **Propiedades**: Nombre, ubicación, demanda, prioridad
- **Selección**: Elegir clientes para optimización

### 3. Gestión de Vehículos

- **Crear vehículos**: Definir capacidad, velocidad, costo
- **Estados**: Disponible, En ruta, Mantenimiento
- **Selección**: Elegir flota para optimización

### 4. Optimización de Rutas

Tres métodos disponibles:

1. **Reinforcement Learning (DQN)**: Modelo entrenado con aprendizaje profundo
2. **Greedy (Vecino más cercano)**: Heurística rápida
3. **OR-Tools**: Solver de Google para optimización lineal

**Opciones**:
- Usar red de carreteras real (GraphHopper)
- Distancia euclidiana (más rápido)

### 5. Entrenamiento RL

Entrenar el agente DQN:

- **Configuración**: Episodios, learning rate, gamma, epsilon
- **Visualización**: Curva de aprendizaje en tiempo real
- **Modelos**: Guardar y cargar modelos entrenados

## 🧠 Algoritmo de Reinforcement Learning

### Arquitectura DQN

```
Estado (s) ──► Red Neuronal ──► Q-values para cada acción
    │              │
    │         ┌────┴────┐
    │         │ Dueling │
    │         │   DQN   │
    │         └────┬────┘
    │              │
    └──────────────┴──► Acción (cliente a visitar)
```

### Espacio de Estados

- Posición actual del vehículo
- Clientes visitados (máscara binaria)
- Capacidad restante
- Demandas de clientes
- Distancias al depot

### Espacio de Acciones

- Visitar cliente i (0 ≤ i < n_clientes)
- Regresar al depot

### Función de Recompensa

```
R = -distancia_recorrida - penalizacion_capacidad + bonus_entrega
```

## 🔧 Configuración

### Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/vrp_optimizer

# Redis
REDIS_URL=redis://redis:6379

# GraphHopper
GRAPHHOPPER_URL=http://graphhopper:8989

# RL
RL_MODEL_PATH=/app/models
```

### Configuración de Entrenamiento

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| num_episodes | 1000 | Número de episodios |
| learning_rate | 0.001 | Tasa de aprendizaje |
| gamma | 0.99 | Factor de descuento |
| epsilon_start | 1.0 | Epsilon inicial |
| epsilon_end | 0.01 | Epsilon final |
| epsilon_decay | 0.995 | Decaimiento de epsilon |
| batch_size | 64 | Tamaño del batch |
| buffer_size | 10000 | Tamaño del replay buffer |

## 📊 API Endpoints

### Clientes
- `GET /api/customers` - Listar clientes
- `POST /api/customers` - Crear cliente
- `GET /api/customers/{id}` - Obtener cliente
- `PUT /api/customers/{id}` - Actualizar cliente
- `DELETE /api/customers/{id}` - Eliminar cliente

### Vehículos
- `GET /api/vehicles` - Listar vehículos
- `POST /api/vehicles` - Crear vehículo
- `PUT /api/vehicles/{id}` - Actualizar vehículo
- `DELETE /api/vehicles/{id}` - Eliminar vehículo

### Optimización
- `POST /api/optimization/optimize` - Optimizar rutas

### Entrenamiento
- `POST /api/training/start` - Iniciar entrenamiento
- `GET /api/training/status` - Estado del entrenamiento
- `POST /api/training/stop` - Detener entrenamiento
- `GET /api/training/models` - Listar modelos

## 🐳 Docker Commands

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Reiniciar servicio específico
docker-compose restart backend

# Detener todo
docker-compose down

# Limpiar todo (incluyendo volúmenes)
docker-compose down -v
```

## 📁 Estructura del Proyecto

```
vrp-optimizer/
├── backend/
│   ├── api/
│   │   └── routes/          # Endpoints REST
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Lógica de negocio
│   ├── rl/                  # Reinforcement Learning
│   │   ├── vrp_environment.py
│   │   └── dqn_agent.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/           # Páginas
│   │   ├── hooks/           # Custom hooks
│   │   ├── store/           # Estado (Zustand)
│   │   ├── api/             # Cliente API
│   │   └── types/           # TypeScript types
│   └── package.json
├── database/
│   └── init.sql             # Schema inicial
├── graphhopper/
│   ├── config.yml           # Configuración
│   └── data/                # Mapas OSM
├── monitoring/
│   └── prometheus.yml
└── docker-compose.yml
```

## 🔬 Desarrollo

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

## 📈 Métricas y Monitoreo

### Grafana Dashboards

1. **Sistema**: CPU, memoria, latencia
2. **Optimización**: Tiempo de cómputo, distancias
3. **RL Training**: Rewards, loss, epsilon

### Prometheus Metrics

- `vrp_optimization_duration_seconds`
- `vrp_total_distance_km`
- `vrp_training_episode`
- `vrp_training_reward`

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE

## 👥 Autores

- Proyecto de grado - Universidad
- Arquitectura de Software en la Nube (AREP)

---

**Nota**: Este sistema está diseñado para propósitos educativos y de investigación. Para uso en producción, considere ajustes de seguridad y escalabilidad adicionales.
