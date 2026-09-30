"""
Motor Matemático do Macro-Fluxo Circadiano & Distribuição por Portões (Doc 01).

Implementação de alta performance (NumPy float64, O(1)) da curva do Sino Gaussiano 
e alocação proporcional de pedestres nos portões de entrada do Pelourinho.

Classificação: Subsistema de Macro-Fluxo (Doc 01)
Complexidade Temporal: O(1)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence, Tuple, Union
import numpy as np

from src.simulation.schemas import (
    MacroFlowConfig,
    MacroFlowResponse,
    SensorAllocation,
    SensorGateWeight,
)

logger = logging.getLogger("simulation.macro_flow")


def calculate_circadian_hour(current_time_hours: float) -> float:
    """
    Calcula a hora equivalente no relógio circadiano contínuo [0, 24).
    
    Formula: h(t) = t mod 24 (RF05)
    
    Args:
        current_time_hours (float): Timestamp contínuo acumulado em horas (t >= 0).
        
    Returns:
        float: Hora do dia h(t) em [0, 24).
    """
    return float(current_time_hours % 24.0)


def circadian_hour(t_hours: float) -> float:
    """Alias para calculate_circadian_hour (RF05)."""
    return calculate_circadian_hour(t_hours)


def current_system_hour() -> float:
    """
    Obtém o horário atual do sistema operacional em horas fracionárias (Canal C).
    
    Exemplo: 16h30 -> 16.5
    """
    now = datetime.now()
    return now.hour + (now.minute / 60.0) + (now.second / 3600.0) + (now.microsecond / 3.6e9)


class BairroPopulation(tuple):
    """
    Estrutura matemática que unifica a lotação global N_bairro(t) e a taxa diferencial ΔN (Item 1 e 2).
    
    Herda de tuple de 2 elementos (N_bairro, circadian_hour) para preservar 100% de
    retrocompatibilidade com chamadas do tipo:
        N_bairro, h_t = calculate_bairro_population(...)
        
    Ao mesmo tempo, expõe propriedades ricas para acoplamento dinâmico (Doc 00 e Doc 03):
        pop.delta_N, pop.rate_per_minute, pop.step_minutes, pop.slope.
    """
    def __new__(
        cls,
        N_bairro: float,
        circadian_hour: float,
        delta_N: float = 0.0,
        rate_per_minute: float = 0.0,
        step_minutes: float = 5.0,
        slope: float = 0.0,
    ):
        instance = super().__new__(cls, (float(N_bairro), float(circadian_hour)))
        instance._delta_N = float(delta_N)
        instance._rate_per_minute = float(rate_per_minute)
        instance._step_minutes = float(step_minutes)
        instance._slope = float(slope)
        return instance

    @property
    def N_bairro(self) -> float:
        """Volume total absoluto instantâneo no bairro N_bairro(t)."""
        return self[0]

    @property
    def circadian_hour(self) -> float:
        """Hora circadiana h(t) em [0, 24)."""
        return self[1]

    @property
    def delta_N(self) -> float:
        """Taxa diferencial de novos ingressos ΔN no intervalo [t, t + Δt]."""
        return self._delta_N

    @property
    def rate_per_minute(self) -> float:
        """Fluxo incremental médio de passagem por minuto (indivíduos/min)."""
        return self._rate_per_minute

    @property
    def step_minutes(self) -> float:
        """Duração do passo de tempo Δt em minutos."""
        return self._step_minutes

    @property
    def slope(self) -> float:
        """Derivada analítica instantânea dN/dt da curva gaussiana (indivíduos/hora)."""
        return self._slope


def calculate_bairro_population(
    current_time_hours: float,
    N_max: int = 300,
    N_min: int = 15,
    t_peak: float = 16.5,
    sigma: float = 3.0,
    gamma_seasonality: float = 1.0,
    step_minutes: float = 5.0,
) -> BairroPopulation:
    """
    Calcula o volume global diário de pedestres no Pelourinho N_bairro(t)
    aplicando a curva fechada do Sino Gaussiano (RF01, RF04) e a taxa diferencial
    de novos ingressos no ciclo Δt (Item 1 e 2).
    
    Formula:
        N_bairro(t) = gamma * [ N_min + (N_max - N_min) * exp( - (h(t) - t_pico)^2 / (2 * sigma^2) ) ]
        Delta_N(t) = max(0.0, N_bairro(t + dt) - N_bairro(t))
        
    Args:
        current_time_hours (float): Tempo contínuo t em horas.
        N_max (int): Capacidade máxima total acumulada no bairro.
        N_min (int): Lotação flutuante residual da madrugada.
        t_peak (float): Horário de pico (ex: 16.5 = 16h30).
        sigma (float): Largura temporal da janela turística em horas.
        gamma_seasonality (float): Fator de modulação sazonal (ex: 1.0 normal, 1.5 verão).
        step_minutes (float): Intervalo de ciclo temporal em minutos (padrão 5.0 min).
        
    Returns:
        BairroPopulation: Tupla retrocompatível (N_bairro(t), h(t)) com propriedades
                          delta_N, rate_per_minute, step_minutes e slope.
    """
    h_t = calculate_circadian_hour(current_time_hours)
    two_sigma_sq = 2.0 * (sigma ** 2)
    
    # Avaliação analítica da Gaussiana no instante t: exp( - (h(t) - t_pico)^2 / (2 * sigma^2) )
    diff = h_t - t_peak
    exponent = -(diff * diff) / two_sigma_sq
    
    if exponent < -50.0:
        gaussian_term = 0.0
    else:
        gaussian_term = math.exp(exponent)
    
    amplitude = N_max - N_min
    N_bairro = float(max(0.0, gamma_seasonality * (N_min + amplitude * gaussian_term)))
    
    # Avaliação analítica no próximo instante t + dt para influxo diferencial ΔN (Item 1 e 2)
    dt_hours = step_minutes / 60.0
    h_next = calculate_circadian_hour(current_time_hours + dt_hours)
    diff_next = h_next - t_peak
    exponent_next = -(diff_next * diff_next) / two_sigma_sq
    
    if exponent_next < -50.0:
        gaussian_next = 0.0
    else:
        gaussian_next = math.exp(exponent_next)
        
    N_bairro_next = float(max(0.0, gamma_seasonality * (N_min + amplitude * gaussian_next)))
    
    # Variação positiva (apenas novos ingressos através dos portões)
    delta_N = float(max(0.0, N_bairro_next - N_bairro))
    rate_per_minute = delta_N / step_minutes if step_minutes > 0.0 else 0.0
    
    # Inclinação analítica da curva dN/dt (pessoas/hora)
    slope = float(gamma_seasonality * amplitude * gaussian_term * (-(diff) / (sigma ** 2)))
    
    return BairroPopulation(
        N_bairro=N_bairro,
        circadian_hour=h_t,
        delta_N=delta_N,
        rate_per_minute=rate_per_minute,
        step_minutes=step_minutes,
        slope=slope,
    )


def calculate_bairro_volume(
    t_hours: float,
    gamma: float = 1.0,
    N_min: float = 15.0,
    N_max: float = 300.0,
    t_peak: float = 16.5,
    sigma: float = 3.0,
    step_minutes: float = 5.0,
) -> float:
    """
    Avalia analiticamente a exata fórmula fechada do Sino Gaussiano (RF01, RF04).
    Retorna apenas N_bairro(t) em indivíduos.
    """
    vol, _ = calculate_bairro_population(
        current_time_hours=t_hours,
        N_max=int(N_max),
        N_min=int(N_min),
        t_peak=t_peak,
        sigma=sigma,
        gamma_seasonality=gamma,
        step_minutes=step_minutes,
    )
    return vol


def calculate_bairro_influx(
    current_time_hours: float,
    step_minutes: float = 5.0,
    N_max: int = 300,
    N_min: int = 15,
    t_peak: float = 16.5,
    sigma: float = 3.0,
    gamma_seasonality: float = 1.0,
) -> Tuple[float, float]:
    """
    Calcula a taxa diferencial de novos ingressos no bairro Pelourinho no intervalo [t, t + dt] (Item 1 e 2).
    
    Formula:
        Delta_N = max(0, N_bairro(t + dt) - N_bairro(t))
        rate_per_minute = Delta_N / step_minutes
        
    Returns:
        Tuple[float, float]: (Delta_N, rate_per_minute) em indivíduos e indivíduos/minuto.
    """
    pop = calculate_bairro_population(
        current_time_hours=current_time_hours,
        N_max=N_max,
        N_min=N_min,
        t_peak=t_peak,
        sigma=sigma,
        gamma_seasonality=gamma_seasonality,
        step_minutes=step_minutes,
    )
    return pop.delta_N, pop.rate_per_minute


def normalize_gate_weights(w_weights: Union[np.ndarray, Sequence[float]]) -> np.ndarray:
    """
    Valida e normaliza o vetor de pesos dos portões de entrada w para garantir
    a restrição física de conservação de fluxo: sum(w_j) == 1.0 (RF03).
    
    Args:
        w_weights: Vetor de pesos dos portões.
        
    Returns:
        np.ndarray: Vetor float64 de dimensão (J,) com soma estritamente unitária.
    """
    w_arr = np.array(w_weights, dtype=np.float64)
    if w_arr.ndim != 1 or w_arr.size == 0:
        raise ValueError("O vetor de pesos w_weights deve ser 1D e não vazio.")
        
    if np.any(w_arr < 0.0):
        raise ValueError("Pesos de portão w_j não podem conter valores negativos.")
        
    w_sum = float(np.sum(w_arr))
    if w_sum <= 0.0:
        raise ValueError("A soma dos pesos dos portões deve ser estritamente maior que zero.")
        
    if not np.isclose(w_sum, 1.0, atol=1e-4):
        logger.warning(
            f"Soma dos pesos dos portões ({w_sum:.6f}) difere de 1.0. "
            "Aplicando normalização defensiva para conservação de fluxo."
        )
        w_arr = w_arr / w_sum
        
    return w_arr


def distribute_to_gates(
    N_bairro: float,
    w_weights: Union[np.ndarray, Sequence[float]]
) -> np.ndarray:
    """
    Pondera o volume global N_bairro(t) entre os J sensores de portão através
    do vetor de pesos w_j (RF02).
    
    Formula:
        N_rotina,j(t) = w_j * N_bairro(t)
        N_rotina(t) = w * N_bairro(t)
        
    Args:
        N_bairro (float): Lotação global do bairro ou taxa incremental em indivíduos.
        w_weights: Vetor de pesos dos portões.
        
    Returns:
        np.ndarray: Vetor (J,) float64 com contagem de pessoas por portão (indivíduos).
    """
    if isinstance(w_weights, np.ndarray) and w_weights.dtype == np.float64:
        return w_weights * float(N_bairro)
    w_norm = normalize_gate_weights(w_weights)
    return w_norm * float(N_bairro)


def allocate_gates(
    N_bairro: float,
    weights: Sequence[float],
) -> np.ndarray:
    """Alias para distribute_to_gates (RF02)."""
    return distribute_to_gates(N_bairro, weights)


def distribute_influx_to_gates(
    delta_N: float,
    w_weights: Union[np.ndarray, Sequence[float]],
) -> np.ndarray:
    """
    Distribui a taxa diferencial de novos ingressos delta_N entre os portões de entrada (Item 1).
    
    Formula:
        delta_N_rotina,j(t) = w_j * delta_N(t)
    """
    return distribute_to_gates(delta_N, w_weights)


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
    step_minutes: float = 5.0
    delta_N_bairro: float = 0.0
    rate_pedestrians_per_minute: float = 0.0
    vector_delta_N_rotina: List[float] = field(default_factory=list)
    delta_N_rotina: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.delta_N_rotina and self.vector_delta_N_rotina:
            self.delta_N_rotina = self.vector_delta_N_rotina
        elif not self.vector_delta_N_rotina and self.delta_N_rotina:
            self.vector_delta_N_rotina = self.delta_N_rotina

    def to_response(self) -> MacroFlowResponse:
        """Converte para modelo Pydantic para serialização na API FastAPI."""
        return MacroFlowResponse(
            timestamp_iso=self.timestamp_iso,
            current_time_hours=self.t_hours,
            circadian_hour=round(self.circadian_h, 4),
            step_minutes=round(self.step_minutes, 2),
            gamma_seasonality=self.gamma,
            N_bairro_total=round(self.N_bairro, 2),
            total_bairro_volume=round(self.N_bairro, 2),
            delta_N_bairro=round(self.delta_N_bairro, 2),
            rate_pedestrians_per_minute=round(self.rate_pedestrians_per_minute, 4),
            allocations=self.allocations,
            vector_N_rotina=[round(v, 2) for v in self.vector_N_rotina],
            N_rotina=[round(v, 2) for v in self.vector_N_rotina],
            vector_delta_N_rotina=[round(v, 2) for v in self.vector_delta_N_rotina],
            delta_N_rotina=[round(v, 2) for v in self.vector_delta_N_rotina],
            sensor_ids=[a.sensor_id for a in self.allocations] if self.allocations else None,
        )


class MacroFlowSimulator:
    """
    Simulador de Macro-Fluxo de Pedestres do Pelourinho (Doc 01).
    
    Gerencia a configuração dos nós de sensoriamento, validação de conservação
    de fluxo (RF03) e avaliações contínuas em O(1).
    """

    def __init__(self, config: Optional[MacroFlowConfig] = None) -> None:
        self.config = config or MacroFlowConfig()
        self._validate_weights()
        self._weights_cache = np.array(self.gate_weights, dtype=np.float64)

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
        t_hours: Optional[float] = None,
        gamma: float = 1.0,
        step_minutes: Optional[float] = None,
    ) -> MacroFlowResult:
        """Executa um ciclo completo de cálculo analítico e diferencial em O(1) (RNF01, Itens 1 e 2)."""
        if t_hours is None:
            t_hours = current_system_hour()
            
        dt_minutes = step_minutes if step_minutes is not None else getattr(self.config, "step_minutes", 5.0)
        h = calculate_circadian_hour(t_hours)
        
        pop = calculate_bairro_population(
            current_time_hours=t_hours,
            N_max=self.config.N_max,
            N_min=self.config.N_min,
            t_peak=self.config.t_peak,
            sigma=self.config.sigma,
            gamma_seasonality=gamma,
            step_minutes=dt_minutes,
        )
        N_bairro = pop.N_bairro
        delta_N = pop.delta_N
        rate_min = pop.rate_per_minute
        
        raw_allocated = self._weights_cache * N_bairro
        raw_delta = self._weights_cache * delta_N
        vec_list = raw_allocated.tolist()
        delta_vec_list = raw_delta.tolist()
            
        allocations: List[SensorAllocation] = []
        for gate, val, d_val in zip(self.config.gates, vec_list, delta_vec_list):
            allocations.append(
                SensorAllocation(
                    sensor_id=gate.sensor_id,
                    nome_local=gate.nome_local,
                    gate_weight=gate.gate_weight,
                    count_pedestrians=round(val, 2),
                    incremental_pedestrians=round(d_val, 2),
                    delta_pedestrians=round(d_val, 2),
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
            step_minutes=dt_minutes,
            delta_N_bairro=delta_N,
            rate_pedestrians_per_minute=rate_min,
            vector_delta_N_rotina=delta_vec_list,
            delta_N_rotina=delta_vec_list,
        )

    def generate_24h_curve(
        self,
        step_hours: float = 0.25,
        gamma: float = 1.0,
    ) -> List[dict]:
        """Gera os pontos amostrais de 00h00 a 23h45 da curva circadiana contínua."""
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


def calculate_macro_flow(
    current_time_hours: float,
    gamma_seasonality: float = 1.0,
    config: Optional[MacroFlowConfig] = None,
    sensor_ids: Optional[list[str]] = None,
    step_minutes: Optional[float] = None,
    use_incremental: bool = False,
) -> MacroFlowResponse:
    """
    Função principal do Subsistema de Macro-Fluxo (Doc 01).
    Recebe os parâmetros de entrada (Canais A, B, C) e calcula a distribuição de pessoas
    na rotina dos portões (Canal D), oferecendo tanto o volume global absoluto quanto
    o fluxo diferencial incremental de novos ingressos ΔN (Item 1 e 2).
    """
    if config is None:
        config = MacroFlowConfig()
        
    dt_minutes = step_minutes if step_minutes is not None else getattr(config, "step_minutes", 5.0)
    
    pop = calculate_bairro_population(
        current_time_hours=current_time_hours,
        N_max=config.N_max,
        N_min=config.N_min,
        t_peak=config.t_peak,
        sigma=config.sigma,
        gamma_seasonality=gamma_seasonality,
        step_minutes=dt_minutes,
    )
    
    N_bairro = pop.N_bairro
    delta_N = pop.delta_N
    
    # Otimização O(1) de multiplicação direta em lista
    w_list = config.w_weights
    vec_list = [w * N_bairro for w in w_list]
    delta_vec_list = [w * delta_N for w in w_list]
    
    allocations = []
    if config.gates and len(config.gates) == len(vec_list):
        for gate, val, d_val in zip(config.gates, vec_list, delta_vec_list):
            allocations.append(
                SensorAllocation(
                    sensor_id=gate.sensor_id,
                    nome_local=gate.nome_local,
                    gate_weight=gate.gate_weight,
                    count_pedestrians=round(val, 2),
                    incremental_pedestrians=round(d_val, 2),
                    delta_pedestrians=round(d_val, 2),
                )
            )
            
    active_N_rotina = delta_vec_list if use_incremental else vec_list
    
    return MacroFlowResponse(
        current_time_hours=current_time_hours,
        circadian_hour=pop.circadian_hour,
        step_minutes=dt_minutes,
        gamma_seasonality=gamma_seasonality,
        N_bairro_total=N_bairro,
        total_bairro_volume=N_bairro,
        delta_N_bairro=delta_N,
        rate_pedestrians_per_minute=pop.rate_per_minute,
        N_rotina=active_N_rotina,
        vector_N_rotina=active_N_rotina,
        delta_N_rotina=delta_vec_list,
        vector_delta_N_rotina=delta_vec_list,
        allocations=allocations,
        sensor_ids=sensor_ids or ([g.sensor_id for g in config.gates] if config.gates else None),
    )
