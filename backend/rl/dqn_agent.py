"""
===========================================
DQN Agent - Agente de Deep Q-Learning para VRP
===========================================
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import deque
import random
from loguru import logger


class DQNNetwork(nn.Module):
    """
    Red neuronal para aproximar la función Q.
    
    Arquitectura:
    - Capas fully connected con ReLU
    - Dueling architecture opcional
    - Dropout para regularización
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: List[int] = [256, 256, 128],
        dueling: bool = True,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.dueling = dueling
        self.action_dim = action_dim
        
        # Capas compartidas (feature extractor)
        layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_dims[:-1]:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        self.feature_layer = nn.Sequential(*layers)
        
        if dueling:
            # Rama de valor de estado V(s)
            self.value_stream = nn.Sequential(
                nn.Linear(prev_dim, hidden_dims[-1]),
                nn.ReLU(),
                nn.Linear(hidden_dims[-1], 1)
            )
            
            # Rama de ventaja A(s, a)
            self.advantage_stream = nn.Sequential(
                nn.Linear(prev_dim, hidden_dims[-1]),
                nn.ReLU(),
                nn.Linear(hidden_dims[-1], action_dim)
            )
        else:
            # Red tradicional
            self.output_layer = nn.Sequential(
                nn.Linear(prev_dim, hidden_dims[-1]),
                nn.ReLU(),
                nn.Linear(hidden_dims[-1], action_dim)
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        features = self.feature_layer(x)
        
        if self.dueling:
            value = self.value_stream(features)
            advantage = self.advantage_stream(features)
            # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
            q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        else:
            q_values = self.output_layer(features)
        
        return q_values


class ReplayBuffer:
    """
    Experience Replay Buffer para almacenar transiciones.
    
    Implementación con deque para eficiencia de memoria.
    """
    
    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)
    
    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        action_mask: Optional[np.ndarray] = None
    ):
        """Agregar transición al buffer"""
        self.buffer.append((
            state, action, reward, next_state, done,
            action_mask if action_mask is not None else np.ones(1)
        ))
    
    def sample(self, batch_size: int) -> Tuple:
        """Muestrear batch aleatorio"""
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])
        action_masks = np.array([t[5] for t in batch])
        
        return states, actions, rewards, next_states, dones, action_masks
    
    def __len__(self) -> int:
        return len(self.buffer)


class PrioritizedReplayBuffer(ReplayBuffer):
    """
    Prioritized Experience Replay para muestreo ponderado por TD-error.
    """
    
    def __init__(self, capacity: int = 100000, alpha: float = 0.6):
        super().__init__(capacity)
        self.priorities = deque(maxlen=capacity)
        self.alpha = alpha  # Exponente de priorización
    
    def push(self, state, action, reward, next_state, done, action_mask=None, priority=1.0):
        super().push(state, action, reward, next_state, done, action_mask)
        self.priorities.append(priority ** self.alpha)
    
    def sample(self, batch_size: int, beta: float = 0.4) -> Tuple:
        """Muestreo con probabilidades proporcionales a prioridad"""
        priorities = np.array(self.priorities)
        probs = priorities / priorities.sum()
        
        indices = np.random.choice(len(self.buffer), size=batch_size, p=probs)
        
        # Importance sampling weights
        weights = (len(self.buffer) * probs[indices]) ** (-beta)
        weights = weights / weights.max()
        
        batch = [self.buffer[i] for i in indices]
        
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])
        action_masks = np.array([t[5] for t in batch])
        
        return states, actions, rewards, next_states, dones, action_masks, indices, weights
    
    def update_priorities(self, indices: List[int], td_errors: np.ndarray):
        """Actualizar prioridades basadas en TD-error"""
        for idx, td_error in zip(indices, td_errors):
            self.priorities[idx] = (abs(td_error) + 1e-6) ** self.alpha


class DQNAgent:
    """
    Agente de Deep Q-Learning para optimización de rutas VRP.
    
    Características:
    - Double DQN para reducir sobreestimación
    - Dueling architecture
    - Experience replay
    - Epsilon-greedy con decay
    - Action masking para acciones válidas
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        memory_size: int = 100000,
        target_update_freq: int = 10,
        hidden_dims: List[int] = [256, 256, 128],
        dueling: bool = True,
        double_dqn: bool = True,
        device: str = "auto"
    ):
        # Configuración del dispositivo
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        logger.info(f"DQN Agent usando dispositivo: {self.device}")
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.double_dqn = double_dqn
        
        # Redes neuronales
        self.policy_net = DQNNetwork(
            state_dim, action_dim, hidden_dims, dueling
        ).to(self.device)
        
        self.target_net = DQNNetwork(
            state_dim, action_dim, hidden_dims, dueling
        ).to(self.device)
        
        # Copiar pesos iniciales
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizador
        self.optimizer = optim.Adam(
            self.policy_net.parameters(),
            lr=learning_rate
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer, step_size=1000, gamma=0.95
        )
        
        # Replay buffer
        self.memory = ReplayBuffer(memory_size)
        
        # Contadores
        self.steps_done = 0
        self.episodes_done = 0
        
        # Métricas
        self.losses = []
        self.rewards = []
    
    def select_action(
        self,
        state: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        training: bool = True
    ) -> int:
        """
        Seleccionar acción usando epsilon-greedy.
        
        Args:
            state: Estado actual
            action_mask: Máscara de acciones válidas (1=válida)
            training: Si está en modo entrenamiento
        
        Returns:
            Índice de la acción seleccionada
        """
        # Exploración epsilon-greedy
        if training and random.random() < self.epsilon:
            # Acción aleatoria entre las válidas
            if action_mask is not None:
                valid_actions = np.where(action_mask == 1)[0]
                return np.random.choice(valid_actions)
            return random.randrange(self.action_dim)
        
        # Explotación: usar la red
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            
            # Aplicar máscara de acciones
            if action_mask is not None:
                mask_tensor = torch.FloatTensor(action_mask).to(self.device)
                # Poner -inf en acciones inválidas
                q_values = q_values.masked_fill(mask_tensor == 0, float('-inf'))
            
            return q_values.argmax(dim=1).item()
    
    def train_step(self) -> Optional[float]:
        """
        Realizar un paso de entrenamiento.
        
        Returns:
            Pérdida del paso o None si no hay suficientes muestras
        """
        if len(self.memory) < self.batch_size:
            return None
        
        # Muestrear batch
        states, actions, rewards, next_states, dones, _ = self.memory.sample(
            self.batch_size
        )
        
        # Convertir a tensores
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Q-valores actuales
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Q-valores objetivo
        with torch.no_grad():
            if self.double_dqn:
                # Double DQN: usar policy_net para seleccionar, target_net para evaluar
                next_actions = self.policy_net(next_states).argmax(dim=1)
                next_q = self.target_net(next_states).gather(1, next_actions.unsqueeze(1))
            else:
                # DQN estándar
                next_q = self.target_net(next_states).max(dim=1)[0].unsqueeze(1)
            
            target_q = rewards.unsqueeze(1) + self.gamma * next_q * (1 - dones.unsqueeze(1))
        
        # Calcular pérdida (Huber loss para estabilidad)
        loss = F.smooth_l1_loss(current_q, target_q)
        
        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping para estabilidad
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        
        self.optimizer.step()
        
        self.steps_done += 1
        self.losses.append(loss.item())
        
        return loss.item()
    
    def update_target_network(self):
        """Actualizar red objetivo copiando pesos de policy_net"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def decay_epsilon(self):
        """Reducir epsilon gradualmente"""
        self.epsilon = max(
            self.epsilon_end,
            self.epsilon * self.epsilon_decay
        )
    
    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        action_mask: Optional[np.ndarray] = None
    ):
        """Almacenar transición en memoria"""
        self.memory.push(state, action, reward, next_state, done, action_mask)
    
    def end_episode(self, total_reward: float):
        """Llamar al final de cada episodio"""
        self.episodes_done += 1
        self.rewards.append(total_reward)
        self.decay_epsilon()
        self.scheduler.step()
        
        # Actualizar target network periódicamente
        if self.episodes_done % self.target_update_freq == 0:
            self.update_target_network()
    
    def save(self, path: str):
        """Guardar modelo"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episodes_done': self.episodes_done,
            'steps_done': self.steps_done,
            'config': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'gamma': self.gamma,
                'epsilon_end': self.epsilon_end,
                'epsilon_decay': self.epsilon_decay,
                'batch_size': self.batch_size
            }
        }, path)
        logger.info(f"Modelo guardado en: {path}")
    
    def load(self, path: str):
        """Cargar modelo"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_end)
        self.episodes_done = checkpoint.get('episodes_done', 0)
        self.steps_done = checkpoint.get('steps_done', 0)
        logger.info(f"Modelo cargado desde: {path}")
    
    def get_metrics(self) -> Dict:
        """Obtener métricas de entrenamiento"""
        return {
            'episodes': self.episodes_done,
            'steps': self.steps_done,
            'epsilon': self.epsilon,
            'avg_loss_last_100': np.mean(self.losses[-100:]) if self.losses else 0,
            'avg_reward_last_100': np.mean(self.rewards[-100:]) if self.rewards else 0,
            'best_reward': max(self.rewards) if self.rewards else 0
        }
