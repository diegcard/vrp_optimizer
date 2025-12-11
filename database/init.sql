-- ===========================================
-- Inicialización de Base de Datos VRP Optimizer
-- PostgreSQL + PostGIS
-- ===========================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- Tabla: clientes (nodos de entrega)
-- ===========================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    demand INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    time_window_start TIME,
    time_window_end TIME,
    service_time_minutes INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice espacial para búsquedas geográficas
CREATE INDEX idx_customers_location ON customers USING GIST (location);

-- ===========================================
-- Tabla: vehículos (flota)
-- ===========================================
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 100,
    vehicle_type VARCHAR(50) DEFAULT 'van',
    current_location GEOGRAPHY(POINT, 4326),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'in_route', 'maintenance', 'offline')),
    driver_name VARCHAR(255),
    driver_phone VARCHAR(20),
    fuel_efficiency DECIMAL(5, 2), -- km/litro
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_location ON vehicles USING GIST (current_location);
CREATE INDEX idx_vehicles_status ON vehicles (status);

-- ===========================================
-- Tabla: depósitos (centros de distribución)
-- ===========================================
CREATE TABLE IF NOT EXISTS depots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    capacity INTEGER,
    operating_hours_start TIME DEFAULT '06:00:00',
    operating_hours_end TIME DEFAULT '22:00:00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_depots_location ON depots USING GIST (location);

-- ===========================================
-- Tabla: pedidos (órdenes de entrega)
-- ===========================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    depot_id UUID REFERENCES depots(id),
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_transit', 'delivered', 'failed', 'cancelled')),
    demand INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 1,
    required_delivery_date DATE,
    time_window_start TIME,
    time_window_end TIME,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_delivery_date ON orders (required_delivery_date);

-- ===========================================
-- Tabla: rutas (soluciones de optimización)
-- ===========================================
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID REFERENCES vehicles(id),
    depot_id UUID REFERENCES depots(id),
    optimization_method VARCHAR(50) NOT NULL, -- 'rl', 'greedy', 'genetic', 'ortools'
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    total_distance_km DECIMAL(10, 2),
    total_time_minutes INTEGER,
    total_demand INTEGER,
    route_geometry GEOGRAPHY(LINESTRING, 4326),
    sequence JSONB, -- Array ordenado de paradas
    metrics JSONB, -- Métricas adicionales
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_routes_vehicle ON routes (vehicle_id);
CREATE INDEX idx_routes_status ON routes (status);
CREATE INDEX idx_routes_geometry ON routes USING GIST (route_geometry);

-- ===========================================
-- Tabla: paradas de ruta (detalle de cada visita)
-- ===========================================
CREATE TABLE IF NOT EXISTS route_stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id),
    customer_id UUID REFERENCES customers(id),
    stop_sequence INTEGER NOT NULL,
    arrival_time_estimated TIMESTAMP WITH TIME ZONE,
    arrival_time_actual TIMESTAMP WITH TIME ZONE,
    departure_time_actual TIMESTAMP WITH TIME ZONE,
    distance_from_previous_km DECIMAL(10, 2),
    time_from_previous_minutes INTEGER,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'arrived', 'completed', 'skipped')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_route_stops_route ON route_stops (route_id);
CREATE INDEX idx_route_stops_sequence ON route_stops (route_id, stop_sequence);

-- ===========================================
-- Tabla: historial de entrenamiento RL
-- ===========================================
CREATE TABLE IF NOT EXISTS rl_training_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    episode INTEGER NOT NULL,
    total_reward DECIMAL(15, 4),
    avg_distance DECIMAL(10, 2),
    avg_deliveries INTEGER,
    epsilon DECIMAL(5, 4),
    loss DECIMAL(15, 6),
    training_time_seconds DECIMAL(10, 2),
    hyperparameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rl_training_model ON rl_training_history (model_name);
CREATE INDEX idx_rl_training_episode ON rl_training_history (model_name, episode);

-- ===========================================
-- Tabla: modelos RL guardados
-- ===========================================
CREATE TABLE IF NOT EXISTS rl_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20),
    model_type VARCHAR(50), -- 'dqn', 'ppo', 'a2c'
    file_path VARCHAR(500),
    is_active BOOLEAN DEFAULT false,
    metrics JSONB, -- métricas de rendimiento
    hyperparameters JSONB,
    trained_episodes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- Tabla: logs de tráfico en tiempo real
-- ===========================================
CREATE TABLE IF NOT EXISTS traffic_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    segment_start GEOGRAPHY(POINT, 4326),
    segment_end GEOGRAPHY(POINT, 4326),
    traffic_factor DECIMAL(3, 2), -- 1.0 = normal, >1 = congestionado
    speed_kmh DECIMAL(6, 2),
    source VARCHAR(50), -- 'graphhopper', 'google', 'waze'
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_traffic_logs_time ON traffic_logs (recorded_at);

-- ===========================================
-- Tabla: métricas de rendimiento del sistema
-- ===========================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4),
    metric_type VARCHAR(50), -- 'performance', 'business', 'ml'
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_metrics_name ON system_metrics (metric_name);
CREATE INDEX idx_system_metrics_time ON system_metrics (recorded_at);

-- ===========================================
-- Funciones de utilidad
-- ===========================================

-- Función para calcular distancia entre dos puntos
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DOUBLE PRECISION, 
    lon1 DOUBLE PRECISION, 
    lat2 DOUBLE PRECISION, 
    lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN ST_Distance(
        ST_SetSRID(ST_MakePoint(lon1, lat1), 4326)::geography,
        ST_SetSRID(ST_MakePoint(lon2, lat2), 4326)::geography
    ) / 1000; -- Retorna en kilómetros
END;
$$ LANGUAGE plpgsql;

-- Función para obtener clientes cercanos a un punto
CREATE OR REPLACE FUNCTION get_nearby_customers(
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    radius_km DOUBLE PRECISION
) RETURNS TABLE (
    customer_id UUID,
    customer_name VARCHAR,
    distance_km DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        ST_Distance(
            c.location,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) / 1000 as dist
    FROM customers c
    WHERE ST_DWithin(
        c.location,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_km * 1000
    )
    ORDER BY dist;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Datos de ejemplo para Bogotá
-- ===========================================

-- Insertar depósito principal (Centro de distribución en Bogotá)
INSERT INTO depots (name, address, location) VALUES
('Centro de Distribución Norte', 'Autopista Norte Km 7, Bogotá', ST_SetSRID(ST_MakePoint(-74.0456, 4.7566), 4326)),
('Centro de Distribución Sur', 'Av. Boyacá con Calle 80 Sur, Bogotá', ST_SetSRID(ST_MakePoint(-74.1143, 4.5981), 4326));

-- Insertar clientes de ejemplo en diferentes zonas de Bogotá
INSERT INTO customers (name, address, location, demand, priority, time_window_start, time_window_end) VALUES
('Cliente Chapinero', 'Calle 72 #10-25, Chapinero', ST_SetSRID(ST_MakePoint(-74.0553, 4.6577), 4326), 5, 3, '08:00', '12:00'),
('Cliente Usaquén', 'Calle 116 #15-30, Usaquén', ST_SetSRID(ST_MakePoint(-74.0307, 4.6947), 4326), 3, 2, '09:00', '14:00'),
('Cliente Suba', 'Av. Suba #115-50, Suba', ST_SetSRID(ST_MakePoint(-74.0830, 4.7419), 4326), 4, 4, '07:00', '11:00'),
('Cliente Kennedy', 'Av. 1 de Mayo #68-15, Kennedy', ST_SetSRID(ST_MakePoint(-74.1583, 4.6181), 4326), 6, 1, '10:00', '16:00'),
('Cliente Fontibón', 'Calle 17 #96-50, Fontibón', ST_SetSRID(ST_MakePoint(-74.1458, 4.6733), 4326), 2, 3, '08:00', '13:00'),
('Cliente Engativá', 'Calle 80 #90-20, Engativá', ST_SetSRID(ST_MakePoint(-74.1108, 4.7058), 4326), 4, 2, '09:00', '15:00'),
('Cliente Centro', 'Carrera 7 #32-15, Centro', ST_SetSRID(ST_MakePoint(-74.0720, 4.6229), 4326), 8, 5, '07:00', '10:00'),
('Cliente Teusaquillo', 'Calle 45 #13-50, Teusaquillo', ST_SetSRID(ST_MakePoint(-74.0680, 4.6398), 4326), 3, 2, '11:00', '17:00'),
('Cliente Barrios Unidos', 'Calle 63 #24-30, Barrios Unidos', ST_SetSRID(ST_MakePoint(-74.0733, 4.6653), 4326), 5, 3, '08:00', '14:00'),
('Cliente Puente Aranda', 'Carrera 50 #6-20, Puente Aranda', ST_SetSRID(ST_MakePoint(-74.1180, 4.6275), 4326), 7, 4, '06:00', '12:00');

-- Insertar vehículos de ejemplo
INSERT INTO vehicles (plate_number, capacity, vehicle_type, current_location, status, driver_name, driver_phone, fuel_efficiency) VALUES
('ABC123', 100, 'van', ST_SetSRID(ST_MakePoint(-74.0456, 4.7566), 4326), 'available', 'Juan Pérez', '3001234567', 12.5),
('DEF456', 80, 'van', ST_SetSRID(ST_MakePoint(-74.0456, 4.7566), 4326), 'available', 'María García', '3009876543', 14.0),
('GHI789', 120, 'truck', ST_SetSRID(ST_MakePoint(-74.1143, 4.5981), 4326), 'available', 'Carlos López', '3005551234', 8.5),
('JKL012', 60, 'motorcycle', ST_SetSRID(ST_MakePoint(-74.0456, 4.7566), 4326), 'available', 'Ana Rodríguez', '3007778888', 35.0);

-- Vista para obtener resumen de rutas activas
CREATE OR REPLACE VIEW active_routes_summary AS
SELECT 
    r.id as route_id,
    v.plate_number,
    v.driver_name,
    r.optimization_method,
    r.total_distance_km,
    r.total_time_minutes,
    COUNT(rs.id) as total_stops,
    COUNT(CASE WHEN rs.status = 'completed' THEN 1 END) as completed_stops,
    r.created_at,
    r.started_at
FROM routes r
JOIN vehicles v ON r.vehicle_id = v.id
LEFT JOIN route_stops rs ON r.id = rs.route_id
WHERE r.status IN ('planned', 'active')
GROUP BY r.id, v.plate_number, v.driver_name;

-- Trigger para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_vehicles_updated_at
    BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_rl_models_updated_at
    BEFORE UPDATE ON rl_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos VRP Optimizer inicializada correctamente';
    RAISE NOTICE 'Extensiones: PostGIS habilitado';
    RAISE NOTICE 'Tablas creadas: customers, vehicles, depots, orders, routes, route_stops, rl_training_history, rl_models, traffic_logs, system_metrics';
    RAISE NOTICE 'Datos de ejemplo insertados para Bogotá';
END $$;
