"""
Motor Matemático do Macro-Fluxo Circadiano de Pedestres do Pelourinho (Doc 01).

Calcula o volume basal urbano de pedestres N_bairro(t) via Sino Gaussiano contínuo
e distribui entre os portões de acesso físico via vetor de pesos espaciais w.

Classificação: Subsistema de Macro-Fluxo (Doc 01)
Complexidade Temporal: O(1)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAS_NUMPY = False

from src.simulation.schemas import (
    MacroFlowConfig,
    MacroFlowResponse,
    SensorAllocation,
    SensorGateWeight,
)


def circadian_hour(t_hours: float) -> float:
    """Calcula a hora circadiana contínua h(t) = t mod 24 no intervalo [0, 24).
    
    Garante suporte para simulação ininterrupta ao longo de dias e semanas (RF05).
    """
    return float(t_hours % 24.0)


def current_system_hour() -> float:
    """Obtém o horário atual do sistema operacional em horas fracionárias (Canal C).
    
    Exemplo: 16h30 -> 16.5
    """
    now = datetime.now()
    return now.hour + (now.minute / 60.0) + (now.second / 3600.0) + (now.microsecond / 3.6e9)


def calculate_bairro_volume(
    t_hours: float,
    gamma: float = 1.0,
    N_min: float = 15.0,
    N_max: float = 300.0,
    t_peak: float = 16.5,
    sigma: float = 3.0,
) -> float:
    """Avalia analiticamente a exata fórmula fechada do Sino Gaussiano validada (RF01, RF04).
    
    N_bairro(t) = gamma * [ N_min + (N_max - N_min) * exp( - (h(t) - t_pico)^2 / (2 * sigma^2) ) ]
    
    Args:
        t_hours: Tempo contínuo em horas (t >= 0).
        gamma: Multiplicador sazonal (ex: 1.0 dias comuns, 1.5 alta estação, 3.5 carnaval).
        N_min: População residual mínima da madrugada (03h00).
        N_max: Capacidade máxima total do centro histórico em horário de pico.
        t_peak: Horário central do pico de visitação (ex: 16.5 para 16h30).
        sigma: Desvio padrão / largura temporal do espalhamento turístico (em horas).
        
    Returns:
        float: Volume global instantâneo de pedestres N_bairro(t) em indivíduos.
    """
    h = circadian_hour(t_hours)
    diff = h - t_peak
    exponent = -(diff * diff) / (2.0 * sigma * sigma)
    
    # Evita underflow numérico extremo em exp()
    if exponent < -50.0:
        bell = 0.0
    else:
        bell = math.exp(exponent)
        
    volume = gamma * (N_min + (N_max - N_min) * bell)
    return float(max(0.0, volume))


def allocate_gates(
    N_bairro: float,
    weights: Sequence[float],
) -> Union[List[float], "np.ndarray"]:
    """Aloca o volume global N_bairro(t) aos portões de entrada via vetor de pesos w (RF02).
    
    N_rotina,j(t) = w_j * N_bairro(t)
    
    Retorna vetor de dimensão J em indivíduos (RNF02).
    """
    if HAS_NUMPY:
        w_arr = np.asarray(weights, dtype=np.float64)
        return w_arr * N_bairro
    else:
        return [float(w * N_bairro) for w in weights]


@dataclass
class MacroFlowResult:
    """Estrutura em memória RAM intermediária para transmissão ao barramento (Canal D)."""
    t_hours: float
    circadian_h: float
    gamma: float
    N_bairro: float
    vector_N_rotina: List[float]
    allocations: List[SensorAllocation]
    timestamp_iso: str

    def to_response(self) -> MacroFlowResponse:
        """Converte para modelo Pydantic para serialização na API FastAPI."""
        return MacroFlowResponse(
            timestamp_iso=self.timestamp_iso,
            circadian_hour=round(self.circadian_h, 4),
            gamma_seasonality=self.gamma,
            total_bairro_volume=round(self.N_bairro, 2),
            allocations=self.allocations,
            vector_N_rotina=[round(v, 2) for v in self.vector_N_rotina],
        )


class MacroFlowSimulator:
    """Simulador de Macro-Fluxo de Pedestres do Pelourinho (Doc 01).
    
    Gerencia a configuração dos nós de sensoriamento, validação de conservação
    de fluxo (RF03) e avaliações contínuas em O(1).
    """

    def __init__(self, config: MacroFlowConfig | None = None) -> None:
        self.config = config or MacroFlowConfig()
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Garante a conservação de fluxo sum(w_j) == 1.0 (RF03)."""
        total = sum(g.gate_weight for g in self.config.gates)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"Conservação de fluxo violada (RF03): soma dos pesos = {total:.4f} != 1.0"
            )

    @property
    def gate_weights(self) -> List[float]:
        return [g.gate_weight for g in self.config.gates]

    @property
    def sensor_ids(self) -> List[str]:
        return [g.sensor_id for g in self.config.gates]

    def evaluate(
        self,
        t_hours: float | None = None,
        gamma: float = 1.0,
    ) -> MacroFlowResult:
        """Executa um ciclo completo de cálculo analítico em O(1) (RNF01).
        
        Args:
            t_hours: Instante contínuo em horas. Se None, lê relógio atual do sistema.
            gamma: Multiplicador sazonal da época.
            
        Returns:
            MacroFlowResult: Contagem de pessoas por portão e total do bairro.
        """
        if t_hours is None:
            t_hours = current_system_hour()
            
        h = circadian_hour(t_hours)
        N_bairro = calculate_bairro_volume(
            t_hours=t_hours,
            gamma=gamma,
            N_min=self.config.N_min_bairro,
            N_max=self.config.N_max_bairro,
            t_peak=self.config.t_peak,
            sigma=self.config.sigma,
        )
        
        weights = self.gate_weights
        raw_allocated = allocate_gates(N_bairro, weights)
        
        if HAS_NUMPY and isinstance(raw_allocated, np.ndarray):
            vec_list = raw_allocated.tolist()
        else:
            vec_list = list(raw_allocated)
            
        allocations: List[SensorAllocation] = []
        for gate, val in zip(self.config.gates, vec_list):
            allocations.append(
                SensorAllocation(
                    sensor_id=gate.sensor_id,
                    nome_local=gate.nome_local,
                    gate_weight=gate.gate_weight,
                    count_pedestrians=round(val, 2),
                )
            )
            
        return MacroFlowResult(
            t_hours=t_hours,
            circadian_h=h,
            gamma=gamma,
            N_bairro=N_bairro,
            vector_N_rotina=vec_list,
            allocations=allocations,
            timestamp_iso=datetime.now().isoformat(),
        )

    def generate_24h_curve(
        self,
        step_hours: float = 0.25,
        gamma: float = 1.0,
    ) -> List[dict]:
        """Gera os pontos amostrais de 00h00 a 23h45 da curva circadiana contínua.
        
        Args:
            step_hours: Passo temporal em horas (ex: 0.25h = 15 minutos).
            gamma: Fator sazonal aplicado.
            
        Returns:
            List[dict]: Dicionários com hour, hour_formatted e total_bairro_volume.
        """
        curve = []
        t = 0.0
        while t < 24.0:
            h_int = int(t)
            m_int = int(round((t - h_int) * 60))
            time_str = f"{h_int:02d}:{m_int:02d}"
            
            vol = calculate_bairro_volume(
                t_hours=t,
                gamma=gamma,
                N_min=self.config.N_min_bairro,
                N_max=self.config.N_max_bairro,
                t_peak=self.config.t_peak,
                sigma=self.config.sigma,
            )
            
            curve.append({
                "hour": round(t, 2),
                "hour_formatted": time_str,
                "total_bairro_volume": round(vol, 2),
            })
            t += step_hours
            
        return curve
