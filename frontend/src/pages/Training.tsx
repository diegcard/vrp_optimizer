import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useStartTraining, useTrainingStatus, useStopTraining, useTrainingHistory, useModels, useLoadModel, useDeleteModel } from '../hooks/useApi'
import toast from 'react-hot-toast'
import type { TrainingConfig } from '../types'

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
  const progress = status && status.total_episodes > 0 ? (status.current_episode / status.total_episodes) * 100 : 0
  
  // Preparar datos para gráfico
  const chartData = history.slice(-100).map((h, i) => ({
    episode: h.episode,
    reward: h.total_reward || h.reward || 0,
    avgReward: history.slice(Math.max(0, i - 10), i + 1).reduce((acc, x) => acc + (x.total_reward || x.reward || 0), 0) / Math.min(i + 1, 10),
    epsilon: (h.epsilon || 0) * 100,
  }))
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Entrenamiento RL</h1>
          <p className="text-gray-500">Deep Q-Network para VRP</p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={() => setShowConfigModal(true)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            disabled={isTraining}
          >
            ⚙️ Configuración
          </button>
          
          {isTraining ? (
            <button
              onClick={handleStopTraining}
              disabled={stopTraining.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              ⏹️ Detener
            </button>
          ) : (
            <button
              onClick={handleStartTraining}
              disabled={startTraining.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              ▶️ Iniciar Entrenamiento
            </button>
          )}
        </div>
      </div>
      
      {/* Training Status */}
      {status && (status.is_training || status.current_episode > 0) && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Estado del Entrenamiento</h2>
            <span className={`px-3 py-1 rounded-full text-sm ${
              status.is_training ? 'bg-blue-100 text-blue-700' :
              status.current_episode >= status.total_episodes && status.total_episodes > 0 ? 'bg-green-100 text-green-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {status.is_training ? '🔄 En progreso' :
               status.current_episode >= status.total_episodes && status.total_episodes > 0 ? '✅ Completado' : 'Inactivo'}
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Progreso</span>
              <span>{status.current_episode} / {status.total_episodes} episodios</span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
          
          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Reward Actual</p>
              <p className="text-xl font-bold">{status.current_reward?.toFixed(2) ?? 'N/A'}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Mejor Reward</p>
              <p className="text-xl font-bold text-green-600">{status.best_reward?.toFixed(2) ?? 'N/A'}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Promedio (últimos 100)</p>
              <p className="text-xl font-bold">{status.avg_reward_last_100?.toFixed(2) ?? 'N/A'}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Tiempo transcurrido</p>
              <p className="text-xl font-bold">{Math.floor((status.elapsed_time_seconds || 0) / 60)}:{String(Math.floor((status.elapsed_time_seconds || 0) % 60)).padStart(2, '0')}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Training Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Curva de Aprendizaje</h2>
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
        </div>
      )}
      
      {/* Saved Models */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Modelos Guardados</h2>
        
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
          <div className="text-center py-8 text-gray-500">
            No hay modelos guardados. Entrene el agente para crear un modelo.
          </div>
        )}
      </div>
      
      {/* Config Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" style={{ zIndex: 9999 }}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl" style={{ zIndex: 10000 }}>
            <h2 className="text-xl font-bold mb-4">Configuración de Entrenamiento</h2>
            
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
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowConfigModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  setShowConfigModal(false)
                  toast.success('Configuración guardada')
                }}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
