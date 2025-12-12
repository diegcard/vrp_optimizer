import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useStartTraining, useTrainingStatus, useStopTraining, useTrainingHistory, useModels, useLoadModel, useDeleteModel } from '../hooks/useApi'
import toast from 'react-hot-toast'
import type { TrainingConfig } from '../types'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Badge from '../components/ui/Badge'

const defaultConfig: TrainingConfig = {
  num_episodes: 1000,
  learning_rate: 0.001,
  gamma: 0.99,
  epsilon_start: 1.0,
  epsilon_end: 0.01,
  epsilon_decay: 0.995,
  batch_size: 64,
  buffer_size: 10000,
}

export default function Training() {
  const { data: status } = useTrainingStatus()
  const { data: history = [] } = useTrainingHistory(500)
  const { data: models = [] } = useModels()
  
  const startTraining = useStartTraining()
  const stopTraining = useStopTraining()
  const loadModel = useLoadModel()
  const deleteModel = useDeleteModel()
  
  const [config, setConfig] = useState<TrainingConfig>(defaultConfig)
  const [showConfigModal, setShowConfigModal] = useState(false)
  
  const handleStartTraining = async () => {
    try {
      await startTraining.mutateAsync(config)
      toast.success('Entrenamiento iniciado')
    } catch (error) {
      toast.error('Error al iniciar entrenamiento')
    }
  }
  
  const handleStopTraining = async () => {
    try {
      await stopTraining.mutateAsync()
      toast.success('Entrenamiento detenido')
    } catch (error) {
      toast.error('Error al detener entrenamiento')
    }
  }
  
  const handleLoadModel = async (modelId: string) => {
    try {
      await loadModel.mutateAsync(modelId)
      toast.success('Modelo cargado exitosamente')
    } catch (error) {
      toast.error('Error al cargar modelo')
    }
  }
  
  const handleDeleteModel = async (modelId: string) => {
    if (confirm('¿Está seguro de eliminar este modelo?')) {
      try {
        await deleteModel.mutateAsync(modelId)
        toast.success('Modelo eliminado')
      } catch (error) {
        toast.error('Error al eliminar modelo')
      }
    }
  }
  
  const isTraining = status?.is_training ?? false
  const progress = status && status.total_episodes > 0 
    ? Math.min((status.current_episode / status.total_episodes) * 100, 100) 
    : 0
  
  // Formatear tiempo
  const formatTime = (seconds?: number) => {
    if (!seconds || seconds < 0) return '--:--'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`
  }
  
  // Preparar datos para gráfico
  const chartData = history.slice(-100).map((h, i) => {
    const reward = h.total_reward || h.reward || 0
    const windowStart = Math.max(0, i - 10)
    const windowEnd = i + 1
    const windowSize = windowEnd - windowStart
    const avgReward = history.slice(windowStart, windowEnd)
      .reduce((acc, x) => acc + (x.total_reward || x.reward || 0), 0) / windowSize
    
    return {
      episode: h.episode,
      reward,
      avgReward: avgReward || 0,
      epsilon: (h.epsilon || 0) * 100,
    }
  })
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Entrenamiento RL</h1>
          <p className="text-gray-500 mt-1">Deep Q-Network para Optimización de Rutas VRP</p>
        </div>
        
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setShowConfigModal(true)}
            disabled={isTraining}
          >
            ⚙️ Configuración
          </Button>
          
          {isTraining ? (
            <Button
              variant="danger"
              onClick={handleStopTraining}
              isLoading={stopTraining.isPending}
            >
              ⏹️ Detener Entrenamiento
            </Button>
          ) : (
            <Button
              onClick={handleStartTraining}
              isLoading={startTraining.isPending}
              disabled={startTraining.isPending}
            >
              ▶️ Iniciar Entrenamiento
            </Button>
          )}
        </div>
      </div>
      
      {/* Training Status */}
      {status && (status.is_training || status.current_episode > 0) && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Estado del Entrenamiento</h2>
            <Badge variant={status.is_training ? 'primary' : 'success'}>
              {status.is_training ? '🔄 En progreso' :
               status.current_episode >= status.total_episodes && status.total_episodes > 0 ? '✅ Completado' : '⏸️ Pausado'}
            </Badge>
          </div>
          
          {/* Progress bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-gray-700">Progreso del Entrenamiento</span>
              <span className="font-semibold text-primary-600">
                {status.current_episode} / {status.total_episodes} episodios ({progress.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden shadow-inner">
              <div 
                className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                style={{ width: `${progress}%` }}
              >
                {progress > 10 && (
                  <span className="text-xs font-bold text-white">{progress.toFixed(0)}%</span>
                )}
              </div>
            </div>
          </div>
          
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
              <p className="text-xs font-medium text-blue-700 mb-1">Reward Actual</p>
              <p className="text-2xl font-bold text-blue-900">
                {status.current_reward !== null && status.current_reward !== undefined 
                  ? status.current_reward.toFixed(2) 
                  : '--'}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
              <p className="text-xs font-medium text-green-700 mb-1">Mejor Reward</p>
              <p className="text-2xl font-bold text-green-900">
                {status.best_reward !== null && status.best_reward !== undefined 
                  ? status.best_reward.toFixed(2) 
                  : '--'}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
              <p className="text-xs font-medium text-purple-700 mb-1">Promedio (últimos 100)</p>
              <p className="text-2xl font-bold text-purple-900">
                {status.avg_reward_last_100 !== null && status.avg_reward_last_100 !== undefined 
                  ? status.avg_reward_last_100.toFixed(2) 
                  : '--'}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
              <p className="text-xs font-medium text-orange-700 mb-1">Epsilon (Exploración)</p>
              <p className="text-2xl font-bold text-orange-900">
                {(status.epsilon * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          
          {/* Time Info */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p className="text-sm text-gray-500 mb-1">Tiempo Transcurrido</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatTime(status.elapsed_time_seconds)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Tiempo Estimado Restante</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatTime(status.estimated_remaining_seconds)}
              </p>
            </div>
          </div>
        </Card>
      )}
      
      {/* Training Chart */}
      {chartData.length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Curva de Aprendizaje</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="episode" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="reward" 
                  stroke="#3b82f6" 
                  name="Reward"
                  dot={false}
                />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="avgReward" 
                  stroke="#10b981" 
                  name="Promedio Móvil"
                  dot={false}
                  strokeWidth={2}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="epsilon" 
                  stroke="#f59e0b" 
                  name="Epsilon (%)"
                  dot={false}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
      
      {/* Saved Models */}
      <Card>
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Modelos Guardados</h2>
        
        {models.length > 0 ? (
          <div className="space-y-3">
            {models.map((model) => (
              <div 
                key={model.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div>
                  <p className="font-medium">{model.name}</p>
                  <div className="flex gap-4 text-sm text-gray-500">
                    <span>{model.num_episodes || model.trained_episodes || 0} episodios</span>
                    <span>Reward: {model.final_reward?.toFixed(2) ?? 'N/A'}</span>
                    <span>{model.created_at ? new Date(model.created_at).toLocaleDateString() : 'N/A'}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleLoadModel(model.id)}
                    disabled={loadModel.isPending}
                    className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded hover:bg-primary-200"
                  >
                    Cargar
                  </button>
                  <button
                    onClick={() => handleDeleteModel(model.id)}
                    disabled={deleteModel.isPending}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">🤖</div>
            <p className="font-medium">No hay modelos guardados</p>
            <p className="text-sm mt-1">Entrene el agente para crear un modelo</p>
          </div>
        )}
      </Card>
      
      {/* Config Modal */}
      <Modal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        title="Configuración de Entrenamiento"
        size="lg"
      >
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Número de Episodios
                </label>
                <input
                  type="number"
                  value={config.num_episodes}
                  onChange={(e) => setConfig({ ...config, num_episodes: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Learning Rate
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={config.learning_rate}
                    onChange={(e) => setConfig({ ...config, learning_rate: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gamma (Descuento)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.gamma}
                    onChange={(e) => setConfig({ ...config, gamma: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Epsilon Inicial
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.epsilon_start}
                    onChange={(e) => setConfig({ ...config, epsilon_start: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Epsilon Final
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.epsilon_end}
                    onChange={(e) => setConfig({ ...config, epsilon_end: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Epsilon Decay
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    value={config.epsilon_decay}
                    onChange={(e) => setConfig({ ...config, epsilon_decay: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={config.batch_size}
                    onChange={(e) => setConfig({ ...config, batch_size: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Buffer Size
                  </label>
                  <input
                    type="number"
                    value={config.buffer_size}
                    onChange={(e) => setConfig({ ...config, buffer_size: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
            </div>
        
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={() => setShowConfigModal(false)}
            className="flex-1"
          >
            Cancelar
          </Button>
          <Button
            onClick={() => {
              setShowConfigModal(false)
              toast.success('Configuración guardada')
            }}
            className="flex-1"
          >
            Guardar Configuración
          </Button>
        </div>
      </Modal>
    </div>
  )
}
