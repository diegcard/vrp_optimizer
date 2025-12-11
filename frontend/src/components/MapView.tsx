import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Customer, Route, Coordinates } from '../types'

// Fix for default marker icons in Leaflet with webpack/vite
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Custom icons
const createCustomerIcon = (index: number) => L.divIcon({
  className: 'custom-marker',
  html: `<div class="customer-marker">${index + 1}</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

const depotIcon = L.divIcon({
  className: 'custom-marker',
  html: `<div class="depot-marker">🏭</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
})

// Route colors
const routeColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

interface MapViewProps {
  customers: Customer[]
  depot?: Coordinates
  routes?: Route[]
  onCustomerClick?: (customer: Customer) => void
  onMapClick?: (latlng: { lat: number; lng: number }) => void
  center?: [number, number]
  zoom?: number
}

function MapController({ center, zoom }: { center?: [number, number]; zoom?: number }) {
  const map = useMap()
  
  useEffect(() => {
    if (center) {
      map.setView(center, zoom || 12)
    }
  }, [center, zoom, map])
  
  return null
}

export default function MapView({
  customers,
  depot,
  routes,
  onCustomerClick,
  onMapClick,
  center = [4.6577, -74.0553], // Bogotá
  zoom = 12,
}: MapViewProps) {
  const mapRef = useRef<L.Map>(null)
  
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      ref={mapRef}
      className="h-full w-full rounded-lg shadow-lg"
      onClick={(e: any) => onMapClick?.(e.latlng)}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <MapController center={center} zoom={zoom} />
      
      {/* Depot marker */}
      {depot && (
        <Marker position={[depot.lat, depot.lon]} icon={depotIcon}>
          <Popup>
            <div className="font-semibold">🏭 Centro de Distribución</div>
            <div className="text-sm text-gray-600">
              Lat: {depot.lat.toFixed(6)}<br />
              Lon: {depot.lon.toFixed(6)}
            </div>
          </Popup>
        </Marker>
      )}
      
      {/* Customer markers */}
      {customers.map((customer, index) => (
        <Marker
          key={customer.id}
          position={[customer.location.lat, customer.location.lon]}
          icon={createCustomerIcon(index)}
          eventHandlers={{
            click: () => onCustomerClick?.(customer),
          }}
        >
          <Popup>
            <div className="font-semibold">{customer.name}</div>
            <div className="text-sm text-gray-600">
              {customer.address && <div>{customer.address}</div>}
              <div>Demanda: {customer.demand}</div>
              <div>Prioridad: {customer.priority}</div>
            </div>
          </Popup>
        </Marker>
      ))}
      
      {/* Routes */}
      {routes?.map((route, routeIndex) => {
        const positions = route.geometry.map(p => [p.lat, p.lon] as [number, number])
        const color = routeColors[routeIndex % routeColors.length]
        
        return (
          <Polyline
            key={route.vehicle_id}
            positions={positions}
            pathOptions={{
              color,
              weight: 4,
              opacity: 0.8,
            }}
          >
            <Popup>
              <div className="font-semibold">Ruta {routeIndex + 1}</div>
              <div className="text-sm">
                <div>Vehículo: {route.vehicle_id}</div>
                <div>Distancia: {route.total_distance_km} km</div>
                <div>Tiempo: {route.total_time_minutes} min</div>
                <div>Paradas: {route.points.length}</div>
              </div>
            </Popup>
          </Polyline>
        )
      })}
    </MapContainer>
  )
}
