"""
===========================================
Servicio de Optimización de Rutas
Integra RL, heurísticos y OR-Tools
===========================================
"""

import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio
import os

from rl.vrp_environment import VRPEnvironment, VRPEnvironmentWithRealData
from rl.dqn_agent import DQNAgent
from config.settings import settings


class OptimizationService:
    """
    Servicio principal de optimización de rutas.
    
    Proporciona múltiples métodos de optimización:
    - Reinforcement Learning (DQN)
    - Greedy (Vecino más cercano)
    - OR-Tools
    - Algoritmos genéticos
    """
    
    def __init__(self):
        self.agent: Optional[DQNAgent] = None
        self.model_loaded = False
        self.model_path = settings.MODEL_PATH
    
    async def load_model(self, model_name: str = None):
        """Cargar modelo RL entrenado"""
        if model_name is None:
            # Buscar modelo activo en BD o usar default
            try:
                from database.connection import get_db
                from sqlalchemy import text
                async for db in get_db():
                    query = text("""
                        SELECT name, file_path, hyperparameters
                        FROM rl_models
                        WHERE is_active = true
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """)
                    result = await db.execute(query)
                    row = result.fetchone()
                    if row:
                        model_name = row.name
                        model_path_from_db = row.file_path
                        if model_path_from_db and os.path.exists(model_path_from_db):
                            model_file = model_path_from_db
                        else:
                            model_file = os.path.join(self.model_path, f"{model_name}.pt")
                    else:
                        # Usar default
                        model_name = getattr(settings, 'DEFAULT_MODEL_NAME', 'vrp_dqn_v1')
                        model_file = os.path.join(self.model_path, f"{model_name}.pt")
                    break
            except Exception as e:
                logger.warning(f"Error buscando modelo activo: {e}")
                model_name = getattr(settings, 'DEFAULT_MODEL_NAME', 'vrp_dqn_v1')
                model_file = os.path.join(self.model_path, f"{model_name}.pt")
        else:
            model_file = os.path.join(self.model_path, f"{model_name}.pt")
        
        if not os.path.exists(model_file):
            logger.warning(f"Modelo no encontrado: {model_file}")
            self.model_loaded = False
            return False
        
        try:
            import torch
            # Cargar checkpoint para obtener config
            checkpoint = torch.load(model_file, map_location='cpu')
            config = checkpoint.get('config', {})
            
            # Crear agente con config del modelo
            self.agent = DQNAgent(
                state_dim=config.get('state_dim', 104),
                action_dim=config.get('action_dim', 21),
                learning_rate=config.get('learning_rate', 0.001),
                gamma=config.get('gamma', 0.99),
                epsilon_end=config.get('epsilon_end', 0.01),
                epsilon_decay=config.get('epsilon_decay', 0.995),
                batch_size=config.get('batch_size', 64),
            )
            self.agent.load(model_file)
            self.model_loaded = True
            logger.info(f"Modelo cargado exitosamente: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            self.model_loaded = False
            return False
    
    async def optimize_with_rl(
        self,
        depot: Dict,
        customers: List[Dict],
        vehicles: List[Dict],
        consider_traffic: bool = True,
        use_real_roads: bool = False
    ) -> Dict[str, Any]:
        """
        Optimizar rutas usando el agente de RL.
        
        Args:
            depot: {"id", "lat", "lon"}
            customers: [{"id", "lat", "lon", "demand", "priority"}, ...]
            vehicles: [{"id", "capacity"}, ...]
            consider_traffic: Considerar tráfico (ajusta rewards)
        
        Returns:
            Diccionario con rutas optimizadas y métricas
        """
        # Crear entorno con datos reales
        env = VRPEnvironmentWithRealData(
            customers_data=customers,
            vehicles_data=vehicles,
            depot_data=depot
        )
        
        # Si no hay modelo cargado, usar greedy como fallback
        if not self.model_loaded or self.agent is None:
            logger.warning("Modelo RL no disponible, usando greedy")
            return await self.optimize_greedy(depot, customers, vehicles, use_real_roads)
        
        # Ejecutar optimización con el agente
        state, info = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action_mask = env.get_action_mask()
            action = self.agent.select_action(state, action_mask, training=False)
            state, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        
        # Construir resultado
        routes = self._build_routes_from_env(env, customers, vehicles)
        
        return {
            "success": True,
            "routes": routes,
            "total_distance_km": info["total_distance"] * 100,  # Escalar
            "total_time_minutes": int(info["total_distance"] * 100 * 2),  # Estimación
            "customers_served": info["customers_visited"],
            "customers_unserved": info["customers_remaining"],
            "metrics": {
                "rl_reward": total_reward,
                "efficiency": env.get_solution_quality()
            }
        }
    
    async def optimize_greedy(
        self,
        depot: Dict,
        customers: List[Dict],
        vehicles: List[Dict],
        use_real_roads: bool = False
    ) -> Dict[str, Any]:
        """
        Optimización greedy (vecino más cercano).
        
        Asigna clientes al vehículo más cercano que tenga capacidad.
        """
        routes = []
        unassigned = list(range(len(customers)))
        
        for vehicle in vehicles:
            route_points = []
            current_lat = depot["lat"]
            current_lon = depot["lon"]
            current_load = 0
            capacity = vehicle.get("capacity", 100)
            total_distance = 0
            
            while unassigned:
                # Encontrar cliente más cercano con capacidad disponible
                best_idx = None
                best_dist = float('inf')
                
                for idx in unassigned:
                    c = customers[idx]
                    if current_load + c.get("demand", 1) <= capacity:
                        dist = self._haversine_distance(
                            current_lat, current_lon,
                            c["lat"], c["lon"]
                        )
                        if dist < best_dist:
                            best_dist = dist
                            best_idx = idx
                
                if best_idx is None:
                    break
                
                # Agregar cliente a la ruta
                c = customers[best_idx]
                route_points.append({
                    "customer_id": c["id"],
                    "location": {"lat": c["lat"], "lon": c["lon"]},
                    "demand": c.get("demand", 1),
                    "sequence": len(route_points)
                })
                
                total_distance += best_dist
                current_lat = c["lat"]
                current_lon = c["lon"]
                current_load += c.get("demand", 1)
                unassigned.remove(best_idx)
            
            # Agregar retorno al depósito
            if route_points:
                total_distance += self._haversine_distance(
                    current_lat, current_lon,
                    depot["lat"], depot["lon"]
                )
                
                # Obtener geometría (con calles reales si está habilitado)
                if use_real_roads:
                    geometry, road_distance, road_time = await self._build_geometry_with_roads(depot, route_points)
                    routes.append({
                        "vehicle_id": vehicle["id"],
                        "points": route_points,
                        "total_distance_km": round(road_distance, 2),
                        "total_time_minutes": int(road_time),
                        "total_demand": current_load,
                        "geometry": geometry
                    })
                else:
                    routes.append({
                        "vehicle_id": vehicle["id"],
                        "points": route_points,
                        "total_distance_km": round(total_distance, 2),
                        "total_time_minutes": int(total_distance * 2),  # ~30 km/h avg
                        "total_demand": current_load,
                        "geometry": self._build_geometry(depot, route_points)
                    })
        
        total_dist = sum(r["total_distance_km"] for r in routes)
        served = sum(len(r["points"]) for r in routes)
        
        return {
            "success": True,
            "routes": routes,
            "total_distance_km": round(total_dist, 2),
            "total_time_minutes": int(total_dist * 2),
            "customers_served": served,
            "customers_unserved": len(unassigned),
            "metrics": {"method": "greedy"}
        }
    
    async def optimize_with_ortools(
        self,
        depot: Dict,
        customers: List[Dict],
        vehicles: List[Dict],
        use_real_roads: bool = False
    ) -> Dict[str, Any]:
        """
        Optimización usando Google OR-Tools.
        
        Utiliza el solver de VRP de OR-Tools para soluciones óptimas.
        """
        try:
            from ortools.constraint_solver import routing_enums_pb2
            from ortools.constraint_solver import pywrapcp
        except ImportError:
            logger.warning("OR-Tools no disponible, usando greedy")
            return await self.optimize_greedy(depot, customers, vehicles, use_real_roads)
        
        # Crear matriz de distancias
        locations = [depot] + customers
        n = len(locations)
        distance_matrix = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_matrix[i][j] = int(self._haversine_distance(
                        locations[i]["lat"], locations[i]["lon"],
                        locations[j]["lat"], locations[j]["lon"]
                    ) * 1000)  # Metros
        
        # Crear modelo
        manager = pywrapcp.RoutingIndexManager(n, len(vehicles), 0)
        routing = pywrapcp.RoutingModel(manager)
        
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Restricciones de capacidad
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:
                return 0
            return customers[from_node - 1].get("demand", 1)
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            [v.get("capacity", 100) for v in vehicles],
            True,
            "Capacity"
        )
        
        # Parámetros de búsqueda
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        
        # Resolver
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            logger.warning("OR-Tools no encontró solución, usando greedy")
            return await self.optimize_greedy(depot, customers, vehicles)
        
        # Extraer rutas
        routes = []
        total_distance = 0
        
        for vehicle_idx in range(len(vehicles)):
            route_points = []
            route_distance = 0
            route_demand = 0
            index = routing.Start(vehicle_idx)
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node > 0:
                    c = customers[node - 1]
                    route_points.append({
                        "customer_id": c["id"],
                        "location": {"lat": c["lat"], "lon": c["lon"]},
                        "demand": c.get("demand", 1),
                        "sequence": len(route_points)
                    })
                    route_demand += c.get("demand", 1)
                
                next_index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(index, next_index, vehicle_idx)
                index = next_index
            
            if route_points:
                distance_km = route_distance / 1000
                # Obtener geometría (con calles reales si está habilitado)
                if use_real_roads:
                    geometry, road_distance, road_time = await self._build_geometry_with_roads(depot, route_points)
                    routes.append({
                        "vehicle_id": vehicles[vehicle_idx]["id"],
                        "points": route_points,
                        "total_distance_km": round(road_distance, 2),
                        "total_time_minutes": int(road_time),
                        "total_demand": route_demand,
                        "geometry": geometry
                    })
                else:
                    routes.append({
                        "vehicle_id": vehicles[vehicle_idx]["id"],
                        "points": route_points,
                        "total_distance_km": round(distance_km, 2),
                        "total_time_minutes": int(distance_km * 2),
                        "total_demand": route_demand,
                        "geometry": self._build_geometry(depot, route_points)
                    })
                total_distance += distance_km
        
        served = sum(len(r["points"]) for r in routes)
        
        return {
            "success": True,
            "routes": routes,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": int(total_distance * 2),
            "customers_served": served,
            "customers_unserved": len(customers) - served,
            "metrics": {"method": "ortools", "solver_status": "optimal"}
        }
    
    def _build_routes_from_env(
        self,
        env: VRPEnvironment,
        customers: List[Dict],
        vehicles: List[Dict]
    ) -> List[Dict]:
        """Construir estructura de rutas desde el entorno"""
        routes = []
        
        for i, vehicle in enumerate(env.vehicles):
            if not vehicle.route:
                continue
            
            route_points = []
            for seq, customer_idx in enumerate(vehicle.route):
                c = customers[customer_idx]
                route_points.append({
                    "customer_id": c["id"],
                    "location": {"lat": c["lat"], "lon": c["lon"]},
                    "demand": c.get("demand", 1),
                    "sequence": seq
                })
            
            if route_points:
                routes.append({
                    "vehicle_id": vehicles[i]["id"],
                    "points": route_points,
                    "total_distance_km": round(vehicle.total_distance * 100, 2),
                    "total_time_minutes": int(vehicle.total_distance * 100 * 2),
                    "total_demand": vehicle.current_load,
                    "geometry": []
                })
        
        return routes
    
    async def _get_road_geometry(self, points: List[Dict]) -> tuple:
        """
        Obtener geometría real de calles usando OSRM público.
        
        Args:
            points: Lista de puntos [{lat, lon}, ...]
        
        Returns:
            (geometry, distance_km, duration_min)
        """
        import aiohttp
        
        if len(points) < 2:
            return points, 0, 0
        
        # Construir coordenadas para OSRM (lon,lat)
        coords = ";".join([f"{p['lon']},{p['lat']}" for p in points])
        url = f"https://router.project-osrm.org/route/v1/driving/{coords}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "Ok" and data.get("routes"):
                            route = data["routes"][0]
                            geometry = [
                                {"lat": coord[1], "lon": coord[0]}
                                for coord in route["geometry"]["coordinates"]
                            ]
                            distance_km = route["distance"] / 1000
                            duration_min = route["duration"] / 60
                            return geometry, distance_km, duration_min
        except Exception as e:
            logger.warning(f"Error obteniendo ruta OSRM: {e}")
        
        # Fallback a línea recta
        return points, self._calculate_total_distance(points), len(points) * 5
    
    def _calculate_total_distance(self, points: List[Dict]) -> float:
        """Calcular distancia total entre puntos"""
        total = 0
        for i in range(len(points) - 1):
            total += self._haversine_distance(
                points[i]["lat"], points[i]["lon"],
                points[i+1]["lat"], points[i+1]["lon"]
            )
        return total
    
    async def _build_geometry_with_roads(self, depot: Dict, points: List[Dict]) -> tuple:
        """Construir geometría siguiendo calles reales"""
        all_points = [{"lat": depot["lat"], "lon": depot["lon"]}]
        for p in points:
            all_points.append(p["location"])
        all_points.append({"lat": depot["lat"], "lon": depot["lon"]})
        
        return await self._get_road_geometry(all_points)
    
    def _build_geometry(self, depot: Dict, points: List[Dict]) -> List[Dict]:
        """Construir geometría de la ruta para visualización (línea recta)"""
        geometry = [{"lat": depot["lat"], "lon": depot["lon"]}]
        for p in points:
            geometry.append(p["location"])
        geometry.append({"lat": depot["lat"], "lon": depot["lon"]})
        return geometry
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calcular distancia haversine en km"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
