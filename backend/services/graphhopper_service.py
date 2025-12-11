"""
===========================================
Servicio de GraphHopper - Motor de Rutas
===========================================
"""

import httpx
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from config.settings import settings


class GraphHopperService:
    """
    Cliente para el servicio de GraphHopper.
    
    Proporciona:
    - Cálculo de rutas entre puntos
    - Matrices de distancia/tiempo
    - Geocoding inverso
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.GRAPHHOPPER_URL
        self.timeout = settings.GRAPHHOPPER_TIMEOUT
    
    async def health_check(self) -> bool:
        """Verificar conexión a GraphHopper"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"GraphHopper health check failed: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Obtener información del servicio"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/info")
                if response.status_code == 200:
                    return response.json()
                return {}
        except Exception as e:
            logger.error(f"Error obteniendo info de GraphHopper: {e}")
            return {}
    
    async def get_route(
        self,
        points: List[Tuple[float, float]],
        profile: str = "car",
        instructions: bool = True,
        calc_points: bool = True
    ) -> Dict[str, Any]:
        """
        Calcular ruta entre múltiples puntos.
        
        Args:
            points: Lista de (lat, lon)
            profile: Perfil de vehículo (car, truck, motorcycle)
            instructions: Incluir instrucciones de navegación
            calc_points: Incluir puntos de la geometría
        
        Returns:
            Información de la ruta
        """
        # Construir parámetros
        params = {
            "profile": profile,
            "locale": "es",
            "instructions": str(instructions).lower(),
            "calc_points": str(calc_points).lower(),
            "points_encoded": "false"
        }
        
        # Agregar puntos
        for i, (lat, lon) in enumerate(points):
            params[f"point"] = params.get("point", [])
            if isinstance(params["point"], list):
                params["point"].append(f"{lat},{lon}")
            else:
                params["point"] = [params["point"], f"{lat},{lon}"]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/route",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "paths" in data and len(data["paths"]) > 0:
                        path = data["paths"][0]
                        return {
                            "success": True,
                            "distance_meters": path.get("distance", 0),
                            "time_ms": path.get("time", 0),
                            "points": self._parse_points(path.get("points", {})),
                            "instructions": path.get("instructions", []),
                            "bbox": path.get("bbox", [])
                        }
                
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error calculando ruta: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_matrix(
        self,
        points: List[Tuple[float, float]],
        profile: str = "car",
        out_arrays: List[str] = ["distances", "times"]
    ) -> Dict[str, Any]:
        """
        Calcular matriz de distancias/tiempos entre puntos.
        
        Args:
            points: Lista de (lat, lon)
            profile: Perfil de vehículo
            out_arrays: Qué calcular (distances, times, weights)
        
        Returns:
            Matrices de distancia y/o tiempo
        """
        # Construir cuerpo de la solicitud
        body = {
            "profile": profile,
            "points": [[lon, lat] for lat, lon in points],
            "out_arrays": out_arrays
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/matrix",
                    json=body
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "distances": data.get("distances", []),
                        "times": data.get("times", []),
                        "weights": data.get("weights", [])
                    }
                
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error calculando matriz: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_optimized_route(
        self,
        points: List[Tuple[float, float]],
        profile: str = "car",
        round_trip: bool = True
    ) -> Dict[str, Any]:
        """
        Calcular ruta optimizada (TSP) entre puntos.
        
        Args:
            points: Lista de (lat, lon), primer punto es depósito
            profile: Perfil de vehículo
            round_trip: Si debe volver al inicio
        
        Returns:
            Ruta optimizada con orden de visita
        """
        # Construir cuerpo para optimize API
        body = {
            "profile": profile,
            "points": [[lon, lat] for lat, lon in points],
            "optimize": "true",
            "round_trip": str(round_trip).lower()
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                response = await client.post(
                    f"{self.base_url}/optimize",
                    json=body
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "solution" in data:
                        solution = data["solution"]
                        return {
                            "success": True,
                            "distance": solution.get("distance", 0),
                            "time": solution.get("time", 0),
                            "order": solution.get("order", []),
                            "unassigned": solution.get("unassigned", [])
                        }
                
                # Fallback: devolver ruta sin optimizar
                return await self.get_route(points, profile)
                
        except Exception as e:
            logger.error(f"Error en optimize: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_points(self, points_data: Dict) -> List[Dict[str, float]]:
        """Parsear puntos de la respuesta de GraphHopper"""
        if not points_data:
            return []
        
        coordinates = points_data.get("coordinates", [])
        return [
            {"lat": coord[1], "lon": coord[0]}
            for coord in coordinates
        ]
    
    async def geocode_reverse(
        self,
        lat: float,
        lon: float
    ) -> Optional[str]:
        """
        Obtener dirección a partir de coordenadas.
        
        Args:
            lat: Latitud
            lon: Longitud
        
        Returns:
            Dirección o None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/geocode",
                    params={
                        "reverse": "true",
                        "point": f"{lat},{lon}",
                        "locale": "es"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", [])
                    if hits:
                        return hits[0].get("name", "")
                
                return None
                
        except Exception as e:
            logger.error(f"Error en geocode: {e}")
            return None
