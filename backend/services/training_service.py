"""
===========================================
Servicio de Entrenamiento RL
===========================================
"""

import numpy as np
from typing import Dict, Any, Optional, Callable
from loguru import logger
import asyncio
import os
import time

from rl.vrp_environment import VRPEnvironment
from rl.dqn_agent import DQNAgent
from schemas import TrainingConfig
from config.settings import settings


class TrainingService:
    """
    Servicio para entrenar agentes de Reinforcement Learning.
    
    Soporta:
    - Entrenamiento con diferentes configuraciones
    - Callbacks para monitoreo
    - Guardado de checkpoints
    - Evaluación durante entrenamiento
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.agent: Optional[DQNAgent] = None
        self.env: Optional[VRPEnvironment] = None
        self.is_training = False
        self.should_stop = False
        self.start_time = None
        self.db_session = None  # Para guardar historial
    
    async def train(
        self,
        callback: Optional[Callable] = None,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Ejecutar entrenamiento del agente.
        
        Args:
            callback: Función callback(episode, reward, epsilon, avg_reward)
        
        Returns:
            Diccionario con resultados del entrenamiento
        """
        self.is_training = True
        self.should_stop = False
        self.start_time = time.time()
        self.db_session = db_session
        
        # Crear entorno
        self.env = VRPEnvironment(
            num_customers=self.config.num_customers,
            num_vehicles=self.config.num_vehicles,
            vehicle_capacity=self.config.vehicle_capacity
        )
        
        # Calcular dimensiones
        state_dim = self.config.num_customers * 5 + 4
        action_dim = self.config.num_customers + 1
        
        # Crear agente
        self.agent = DQNAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=self.config.learning_rate,
            gamma=self.config.gamma,
            epsilon_start=self.config.epsilon_start,
            epsilon_end=self.config.epsilon_end,
            epsilon_decay=self.config.epsilon_decay,
            batch_size=self.config.batch_size,
            memory_size=self.config.memory_size
        )
        
        logger.info(f"Iniciando entrenamiento: {self.config.model_name}")
        logger.info(f"Episodios: {self.config.episodes}, Clientes: {self.config.num_customers}")
        
        rewards_history = []
        best_reward = float('-inf')
        
        for episode in range(self.config.episodes):
            if self.should_stop:
                logger.info("Entrenamiento detenido por usuario")
                break
            
            # Ejecutar episodio
            episode_reward = await self._run_episode()
            rewards_history.append(episode_reward)
            
            # Actualizar mejor recompensa
            if episode_reward > best_reward:
                best_reward = episode_reward
            
            # Calcular promedio
            avg_reward = np.mean(rewards_history[-100:])
            
            # Callback
            if callback:
                callback(
                    episode + 1,
                    episode_reward,
                    self.agent.epsilon,
                    avg_reward
                )
            
            # Guardar historial en BD cada 10 episodios (para no saturar BD)
            if (episode + 1) % 10 == 0 and self.db_session:
                try:
                    await self._save_training_history(
                        episode + 1,
                        episode_reward,
                        avg_reward,
                        self.agent.epsilon,
                        self.agent.get_metrics().get('avg_loss_last_100', 0)
                    )
                except Exception as e:
                    logger.warning(f"Error guardando historial: {e}")
            
            # Log cada 100 episodios
            if (episode + 1) % 100 == 0:
                metrics = self.agent.get_metrics()
                logger.info(
                    f"Episode {episode + 1}/{self.config.episodes} | "
                    f"Reward: {episode_reward:.2f} | "
                    f"Avg: {avg_reward:.2f} | "
                    f"Epsilon: {self.agent.epsilon:.4f} | "
                    f"Loss: {metrics['avg_loss_last_100']:.4f}"
                )
            
            # Guardar checkpoint cada 500 episodios
            if (episode + 1) % 500 == 0:
                checkpoint_path = os.path.join(
                    settings.MODEL_PATH,
                    f"{self.config.model_name}_checkpoint_{episode + 1}.pt"
                )
                os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
                self.agent.save(checkpoint_path)
                logger.info(f"Checkpoint guardado: {checkpoint_path}")
        
        # Guardar modelo final
        final_path = os.path.join(
            settings.MODEL_PATH,
            f"{self.config.model_name}.pt"
        )
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        self.agent.save(final_path)
        
        training_time = time.time() - self.start_time
        self.is_training = False
        
        logger.info(f"Entrenamiento completado en {training_time:.1f}s")
        logger.info(f"Mejor recompensa: {best_reward:.2f}")
        
        return {
            "model_name": self.config.model_name,
            "model_path": final_path,
            "episodes_trained": episode + 1,
            "final_avg_reward": np.mean(rewards_history[-100:]),
            "best_reward": best_reward,
            "training_time_seconds": training_time,
            "metrics": self.agent.get_metrics()
        }
    
    async def _run_episode(self) -> float:
        """Ejecutar un episodio de entrenamiento"""
        state, info = self.env.reset()
        done = False
        total_reward = 0
        
        while not done:
            # Obtener máscara de acciones válidas
            action_mask = self.env.get_action_mask()
            
            # Seleccionar acción
            action = self.agent.select_action(state, action_mask, training=True)
            
            # Ejecutar acción
            next_state, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            
            # Almacenar transición
            self.agent.store_transition(
                state, action, reward, next_state, done, action_mask
            )
            
            # Entrenar
            self.agent.train_step()
            
            state = next_state
            total_reward += reward
        
        # Finalizar episodio
        self.agent.end_episode(total_reward)
        
        return total_reward
    
    def stop(self):
        """Detener el entrenamiento"""
        self.should_stop = True
    
    async def _save_training_history(
        self,
        episode: int,
        reward: float,
        avg_reward: float,
        epsilon: float,
        loss: float
    ):
        """Guardar historial de entrenamiento en BD"""
        if not self.db_session:
            return
            
        try:
            from sqlalchemy import text
            import time
            
            query = text("""
                INSERT INTO rl_training_history (
                    model_name, episode, total_reward, avg_distance,
                    epsilon, loss, training_time_seconds, hyperparameters
                ) VALUES (
                    :model_name, :episode, :reward, :avg_distance,
                    :epsilon, :loss, :time, :hyperparams
                )
            """)
            
            elapsed = time.time() - self.start_time if self.start_time else 0
            
            await self.db_session.execute(query, {
                "model_name": self.config.model_name,
                "episode": episode,
                "reward": reward,
                "avg_distance": -avg_reward if avg_reward < 0 else abs(avg_reward),  # Convertir reward a distancia aproximada
                "epsilon": epsilon,
                "loss": loss,
                "time": elapsed,
                "hyperparams": self.config.dict()
            })
            await self.db_session.commit()
        except Exception as e:
            logger.warning(f"Error guardando historial de entrenamiento: {e}")
            if self.db_session:
                await self.db_session.rollback()
    
    async def evaluate(
        self,
        num_episodes: int = 10,
        render: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluar el agente entrenado.
        
        Args:
            num_episodes: Número de episodios de evaluación
            render: Si mostrar visualización
        
        Returns:
            Métricas de evaluación
        """
        if self.agent is None:
            raise ValueError("No hay agente cargado para evaluar")
        
        rewards = []
        distances = []
        served_ratios = []
        
        for _ in range(num_episodes):
            state, _ = self.env.reset()
            done = False
            total_reward = 0
            
            while not done:
                action_mask = self.env.get_action_mask()
                action = self.agent.select_action(state, action_mask, training=False)
                state, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                total_reward += reward
            
            quality = self.env.get_solution_quality()
            rewards.append(total_reward)
            distances.append(quality["total_distance"])
            served_ratios.append(quality["service_rate"])
        
        return {
            "avg_reward": np.mean(rewards),
            "std_reward": np.std(rewards),
            "avg_distance": np.mean(distances),
            "avg_service_rate": np.mean(served_ratios),
            "num_episodes": num_episodes
        }
