"""
===========================================
VRP Environment - Gymnasium para Reinforcement Learning
Entorno de simulación del problema de ruteo vehicular
===========================================
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import random
from dataclasses import dataclass
from loguru import logger


@dataclass
class Customer:
    """Representación de un cliente/nodo de entrega"""
    id: int
    x: float  # Coordenada normalizada [0, 1]
    y: float
    demand: int
    priority: int = 1
    time_window_start: Optional[float] = None
    time_window_end: Optional[float] = None
    visited: bool = False


@dataclass
class Vehicle:
    """Representación de un vehículo"""
    id: int
    capacity: int
    current_load: int = 0
    current_x: float = 0.5  # Inicia en depósito
    current_y: float = 0.5
    route: List[int] = None
    total_distance: float = 0.0
    
    def __post_init__(self):
        if self.route is None:
            self.route = []


class VRPEnvironment(gym.Env):
    """
    Entorno Gymnasium para el problema de ruteo vehicular (VRP).
    
    El agente debe asignar clientes a vehículos y determinar el orden
    de visita para minimizar la distancia total mientras respeta
    las restricciones de capacidad.
    
    Estado: Vector con información de clientes, vehículos y distancias
    Acción: Seleccionar el siguiente cliente a visitar
    Recompensa: Negativa de la distancia recorrida + bonificaciones
    """
    
    metadata = {"render_modes": ["human", "rgb_array"]}
    
    def __init__(
        self,
        num_customers: int = 20,
        num_vehicles: int = 3,
        vehicle_capacity: int = 100,
        grid_size: float = 100.0,
        max_demand: int = 20,
        use_time_windows: bool = False,
        seed: Optional[int] = None
    ):
        super().__init__()
        
        self.num_customers = num_customers
        self.num_vehicles = num_vehicles
        self.vehicle_capacity = vehicle_capacity
        self.grid_size = grid_size
        self.max_demand = max_demand
        self.use_time_windows = use_time_windows
        
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        # Depósito en el centro
        self.depot_x = 0.5
        self.depot_y = 0.5
        
        # Espacio de observación
        # Para cada cliente: x, y, demand, visited, distance_to_current
        # Para vehículo actual: current_load, remaining_capacity
        # Global: num_unvisited, current_vehicle_id
        obs_dim = num_customers * 5 + 4
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # Espacio de acciones: seleccionar cliente (0 a num_customers-1)
        # Acción num_customers = volver al depósito
        self.action_space = spaces.Discrete(num_customers + 1)
        
        # Estado interno
        self.customers: List[Customer] = []
        self.vehicles: List[Vehicle] = []
        self.current_vehicle_idx: int = 0
        self.current_time: float = 0.0
        self.total_reward: float = 0.0
        self.steps: int = 0
        self.max_steps: int = num_customers * 3
        
        # Para renderizado
        self.render_mode = None
        
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Reiniciar el entorno con nuevos clientes aleatorios.
        """
        super().reset(seed=seed)
        
        if seed is not None:
            np.random.seed(seed)
        
        # Generar clientes aleatorios
        self.customers = []
        for i in range(self.num_customers):
            customer = Customer(
                id=i,
                x=np.random.uniform(0.1, 0.9),
                y=np.random.uniform(0.1, 0.9),
                demand=np.random.randint(1, self.max_demand + 1),
                priority=np.random.randint(1, 6),
                visited=False
            )
            
            if self.use_time_windows:
                start = np.random.uniform(0, 0.5)
                customer.time_window_start = start
                customer.time_window_end = start + np.random.uniform(0.2, 0.5)
            
            self.customers.append(customer)
        
        # Inicializar vehículos
        self.vehicles = []
        for i in range(self.num_vehicles):
            self.vehicles.append(Vehicle(
                id=i,
                capacity=self.vehicle_capacity,
                current_x=self.depot_x,
                current_y=self.depot_y
            ))
        
        self.current_vehicle_idx = 0
        self.current_time = 0.0
        self.total_reward = 0.0
        self.steps = 0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Ejecutar una acción en el entorno.
        
        Args:
            action: Índice del cliente a visitar (0 a num_customers-1)
                   o num_customers para volver al depósito
        
        Returns:
            observation: Nuevo estado
            reward: Recompensa obtenida
            terminated: Si el episodio terminó
            truncated: Si se truncó por límite de pasos
            info: Información adicional
        """
        self.steps += 1
        reward = 0.0
        terminated = False
        truncated = False
        
        vehicle = self.vehicles[self.current_vehicle_idx]
        
        # Acción: volver al depósito
        if action == self.num_customers:
            distance = self._calculate_distance(
                vehicle.current_x, vehicle.current_y,
                self.depot_x, self.depot_y
            )
            vehicle.total_distance += distance
            vehicle.current_x = self.depot_x
            vehicle.current_y = self.depot_y
            vehicle.current_load = 0
            
            reward = -distance * 0.1  # Penalización por distancia
            
            # Cambiar al siguiente vehículo
            self.current_vehicle_idx = (self.current_vehicle_idx + 1) % self.num_vehicles
            
        # Acción: visitar cliente
        elif 0 <= action < self.num_customers:
            customer = self.customers[action]
            
            # Verificar si es acción válida
            if customer.visited:
                reward = -1.0  # Penalización por acción inválida
            elif vehicle.current_load + customer.demand > vehicle.capacity:
                reward = -0.5  # Penalización por exceder capacidad
                # Forzar regreso al depósito
                distance = self._calculate_distance(
                    vehicle.current_x, vehicle.current_y,
                    self.depot_x, self.depot_y
                )
                vehicle.total_distance += distance
                vehicle.current_x = self.depot_x
                vehicle.current_y = self.depot_y
                vehicle.current_load = 0
                reward -= distance * 0.1
            else:
                # Visitar cliente válido
                distance = self._calculate_distance(
                    vehicle.current_x, vehicle.current_y,
                    customer.x, customer.y
                )
                
                vehicle.total_distance += distance
                vehicle.current_x = customer.x
                vehicle.current_y = customer.y
                vehicle.current_load += customer.demand
                vehicle.route.append(customer.id)
                customer.visited = True
                
                # Recompensa basada en distancia y prioridad
                reward = -distance * 0.1  # Penalización por distancia
                reward += 0.5 * customer.priority  # Bonificación por prioridad
                
                # Bonificación por eficiencia de carga
                load_efficiency = vehicle.current_load / vehicle.capacity
                if load_efficiency > 0.7:
                    reward += 0.2
        else:
            reward = -1.0  # Acción fuera de rango
        
        self.total_reward += reward
        
        # Verificar terminación
        all_visited = all(c.visited for c in self.customers)
        if all_visited:
            # Todos los vehículos deben volver al depósito
            for v in self.vehicles:
                if v.current_x != self.depot_x or v.current_y != self.depot_y:
                    dist = self._calculate_distance(
                        v.current_x, v.current_y,
                        self.depot_x, self.depot_y
                    )
                    v.total_distance += dist
                    reward -= dist * 0.1
            
            # Bonificación por completar todas las entregas
            reward += 10.0
            terminated = True
        
        # Truncar si se excede el límite de pasos
        if self.steps >= self.max_steps:
            truncated = True
            # Penalización por no completar
            unvisited = sum(1 for c in self.customers if not c.visited)
            reward -= unvisited * 2.0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """Construir vector de observación"""
        vehicle = self.vehicles[self.current_vehicle_idx]
        
        obs = []
        
        # Información de cada cliente
        for customer in self.customers:
            obs.extend([
                customer.x,
                customer.y,
                customer.demand / self.max_demand,  # Normalizado
                1.0 if customer.visited else 0.0,
                self._calculate_distance(
                    vehicle.current_x, vehicle.current_y,
                    customer.x, customer.y
                )
            ])
        
        # Información del vehículo actual
        obs.extend([
            vehicle.current_load / vehicle.capacity,
            (vehicle.capacity - vehicle.current_load) / vehicle.capacity,
            self.current_vehicle_idx / self.num_vehicles,
            sum(1 for c in self.customers if not c.visited) / self.num_customers
        ])
        
        return np.array(obs, dtype=np.float32)
    
    def _get_info(self) -> Dict[str, Any]:
        """Información adicional del estado"""
        return {
            "total_distance": sum(v.total_distance for v in self.vehicles),
            "customers_visited": sum(1 for c in self.customers if c.visited),
            "customers_remaining": sum(1 for c in self.customers if not c.visited),
            "current_vehicle": self.current_vehicle_idx,
            "steps": self.steps,
            "total_reward": self.total_reward
        }
    
    def _calculate_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcular distancia euclidiana normalizada"""
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def get_valid_actions(self) -> List[int]:
        """Obtener lista de acciones válidas"""
        vehicle = self.vehicles[self.current_vehicle_idx]
        valid = []
        
        for i, customer in enumerate(self.customers):
            if not customer.visited:
                if vehicle.current_load + customer.demand <= vehicle.capacity:
                    valid.append(i)
        
        # Siempre puede volver al depósito
        valid.append(self.num_customers)
        
        return valid
    
    def get_action_mask(self) -> np.ndarray:
        """
        Obtener máscara de acciones válidas.
        1 = válida, 0 = inválida
        """
        mask = np.zeros(self.action_space.n, dtype=np.float32)
        for action in self.get_valid_actions():
            mask[action] = 1.0
        return mask
    
    def render(self):
        """Renderizar el estado actual (para debugging)"""
        if self.render_mode == "human":
            self._render_text()
    
    def _render_text(self):
        """Renderizado en texto"""
        print("\n" + "=" * 50)
        print(f"Step: {self.steps} | Vehículo actual: {self.current_vehicle_idx}")
        print(f"Clientes visitados: {sum(1 for c in self.customers if c.visited)}/{self.num_customers}")
        
        for i, v in enumerate(self.vehicles):
            marker = ">>> " if i == self.current_vehicle_idx else "    "
            print(f"{marker}Vehículo {i}: Carga={v.current_load}/{v.capacity}, Distancia={v.total_distance:.2f}")
        
        print(f"Recompensa total: {self.total_reward:.2f}")
        print("=" * 50)
    
    def get_solution_quality(self) -> Dict[str, float]:
        """Obtener métricas de calidad de la solución actual"""
        total_distance = sum(v.total_distance for v in self.vehicles)
        customers_served = sum(1 for c in self.customers if c.visited)
        
        # Calcular distancia óptima aproximada (TSP simple)
        # usando nearest neighbor como referencia
        ref_distance = self._calculate_reference_distance()
        
        return {
            "total_distance": total_distance,
            "customers_served": customers_served,
            "service_rate": customers_served / self.num_customers,
            "efficiency_ratio": ref_distance / max(total_distance, 0.001),
            "avg_distance_per_customer": total_distance / max(customers_served, 1)
        }
    
    def _calculate_reference_distance(self) -> float:
        """Calcular distancia de referencia con nearest neighbor"""
        visited = [False] * self.num_customers
        current_x, current_y = self.depot_x, self.depot_y
        total_dist = 0.0
        
        for _ in range(self.num_customers):
            best_dist = float('inf')
            best_idx = -1
            
            for i, c in enumerate(self.customers):
                if not visited[i]:
                    dist = self._calculate_distance(current_x, current_y, c.x, c.y)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
            
            if best_idx >= 0:
                visited[best_idx] = True
                current_x = self.customers[best_idx].x
                current_y = self.customers[best_idx].y
                total_dist += best_dist
        
        # Volver al depósito
        total_dist += self._calculate_distance(current_x, current_y, self.depot_x, self.depot_y)
        
        return total_dist


class VRPEnvironmentWithRealData(VRPEnvironment):
    """
    Extensión del entorno VRP que acepta datos reales de clientes.
    """
    
    def __init__(
        self,
        customers_data: List[Dict],
        vehicles_data: List[Dict],
        depot_data: Dict,
        **kwargs
    ):
        # Inicializar con el número correcto de clientes y vehículos
        super().__init__(
            num_customers=len(customers_data),
            num_vehicles=len(vehicles_data),
            vehicle_capacity=vehicles_data[0].get("capacity", 100) if vehicles_data else 100,
            **kwargs
        )
        
        self.customers_data = customers_data
        self.vehicles_data = vehicles_data
        self.depot_data = depot_data
        
        # Normalizar coordenadas
        self._normalize_coordinates()
    
    def _normalize_coordinates(self):
        """Normalizar coordenadas geográficas a [0, 1]"""
        all_lats = [c["lat"] for c in self.customers_data] + [self.depot_data["lat"]]
        all_lons = [c["lon"] for c in self.customers_data] + [self.depot_data["lon"]]
        
        self.lat_min, self.lat_max = min(all_lats), max(all_lats)
        self.lon_min, self.lon_max = min(all_lons), max(all_lons)
        
        # Evitar división por cero
        lat_range = max(self.lat_max - self.lat_min, 0.001)
        lon_range = max(self.lon_max - self.lon_min, 0.001)
        
        self.depot_x = (self.depot_data["lon"] - self.lon_min) / lon_range
        self.depot_y = (self.depot_data["lat"] - self.lat_min) / lat_range
    
    def reset(self, seed=None, options=None):
        """Reiniciar con datos reales"""
        super().reset(seed=seed, options=options)
        
        lat_range = max(self.lat_max - self.lat_min, 0.001)
        lon_range = max(self.lon_max - self.lon_min, 0.001)
        
        # Usar datos reales para clientes
        self.customers = []
        for i, c in enumerate(self.customers_data):
            self.customers.append(Customer(
                id=i,
                x=(c["lon"] - self.lon_min) / lon_range,
                y=(c["lat"] - self.lat_min) / lat_range,
                demand=c.get("demand", 1),
                priority=c.get("priority", 1),
                visited=False
            ))
        
        # Usar datos reales para vehículos
        self.vehicles = []
        for i, v in enumerate(self.vehicles_data):
            self.vehicles.append(Vehicle(
                id=i,
                capacity=v.get("capacity", self.vehicle_capacity),
                current_x=self.depot_x,
                current_y=self.depot_y
            ))
        
        return self._get_observation(), self._get_info()
    
    def denormalize_coordinates(self, x: float, y: float) -> Tuple[float, float]:
        """Convertir coordenadas normalizadas a lat/lon"""
        lat_range = max(self.lat_max - self.lat_min, 0.001)
        lon_range = max(self.lon_max - self.lon_min, 0.001)
        
        lon = x * lon_range + self.lon_min
        lat = y * lat_range + self.lat_min
        
        return lat, lon
