"""
Motor Matemático do Macro-Fluxo Circadiano & Distribuição por Portões (Doc 01).

Implementação de alta performance (NumPy float64, O(1)) da curva do Sino Gaussiano 
e alocação proporcional de pedestres nos portões de entrada do Pelourinho.
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional, Union
import numpy as np

from src.simulation.schemas import MacroFlowConfig, MacroFlowResponse

logger = logging.getLogger("simulation.macro_flow")


def calculate_circadian_hour(current_time_hours: float) -> float:
    """
    Calcula a hora equivalente no relógio circadiano contínuo [0, 24).
    
    Formula: h(t) = t mod 24
    
    Args:
        current_time_hours (float): Timestamp continuo acumulado em horas (t >= 0).
        
    Returns:
        float: Hora do dia h(t) em [0, 24).
    """
    return float(current_time_hours % 24.0)


def calculate_bairro_population(
    current_time_hours: float,
    N_max: int = 300,
    N_min: int = 15,
    t_peak: float = 16.5,
    sigma: float = 3.0,
    gamma_seasonality: float = 1.0,
) -> Tuple[float, float]:
    """
    Calcula o volume global diário de pedestres no Pelourinho N_bairro(t)
    aplicando a curva fechada do Sino Gaussiano.
    
    Formula:
        N_bairro(t) = gamma * [ N_min + (N_max - N_min) * exp( - (h(t) - t_pico)^2 / (2 * sigma^2) ) ]
        
    Args:
        current_time_hours (float): Tempo continuo t em horas.
        N_max (int): Capacidade máxima total acumulada no bairro.
        N_min (int): Lotação flutuante residual da madrugada.
        t_peak (float): Horário de pico (ex: 16.5 = 16h30).
        sigma (float): Largura temporal da janela turística em horas.
        gamma_seasonality (float): Fator de modulação sazonal (ex: 1.0 normal, 1.5 verão).
        
    Returns:
        Tuple[float, float]: (N_bairro(t), h(t)) em indivíduos e hora circadiana.
    """
    h_t = calculate_circadian_hour(current_time_hours)
    
    # Avaliação analítica da Gaussiana: exp( - (h(t) - t_pico)^2 / (2 * sigma^2) )
    exponent = -((h_t - t_peak) ** 2) / (2.0 * (sigma ** 2))
    gaussian_term = np.exp(exponent)
    
    N_bairro = gamma_seasonality * (N_min + (N_max - N_min) * gaussian_term)
    return float(N_bairro), h_t


def normalize_gate_weights(w_weights: Union[np.ndarray, list]) -> np.ndarray:
    """
    Valida e normaliza o vetor de pesos dos portões de entrada w para garantir
    a restrição física de conservação de fluxo: sum(w_j) == 1.0.
    
    Args:
        w_weights (Union[np.ndarray, list]): Vetor de pesos dos portões.
        
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
        
    if not np.isclose(w_sum, 1.0, atol=1e-5):
        logger.warning(
            f"Soma dos pesos dos portões ({w_sum:.6f}) difere de 1.0. "
            "Aplicando normalização automática para conservação de fluxo."
        )
        w_arr = w_arr / w_sum
        
    return w_arr


def distribute_to_gates(
    N_bairro: float,
    w_weights: Union[np.ndarray, list]
) -> np.ndarray:
    """
    Pondera o volume global N_bairro(t) entre os J sensores de portão através
    do vetor de pesos w_j.
    
    Formula:
        N_rotina,j(t) = w_j * N_bairro(t)
        N_rotina(t) = w * N_bairro(t)
        
    Args:
        N_bairro (float): Lotação global do bairro em indivíduos.
        w_weights (Union[np.ndarray, list]): Vetor de pesos dos portões.
        
    Returns:
        np.ndarray: Vetor (J,) float64 com contagem de pessoas por portão (indivíduos).
    """
    w_norm = normalize_gate_weights(w_weights)
    N_rotina = w_norm * float(N_bairro)
    return N_rotina


def calculate_macro_flow(
    current_time_hours: float,
    gamma_seasonality: float = 1.0,
    config: Optional[MacroFlowConfig] = None,
    sensor_ids: Optional[list[str]] = None
) -> MacroFlowResponse:
    """
    Função principal do Subsistema de Macro-Fluxo (Doc 01).
    Recebe os parâmetros de entrada (Canais A, B, C) e calcula a distribuição de pessoas
    na rotina dos portões (Canal D).
    
    Args:
        current_time_hours (float): Timestamp contínuo t em horas.
        gamma_seasonality (float): Fator sazonal.
        config (Optional[MacroFlowConfig]): Parâmetros de calibração. Se None, usa padrões.
        sensor_ids (Optional[list[str]]): Lista de IDs dos sensores correspondentes aos portões.
        
    Returns:
        MacroFlowResponse: Payload Pydantic pronto para consumo de API ou barramento.
    """
    if config is None:
        config = MacroFlowConfig()
        
    N_bairro, h_t = calculate_bairro_population(
        current_time_hours=current_time_hours,
        N_max=config.N_max,
        N_min=config.N_min,
        t_peak=config.t_peak,
        sigma=config.sigma,
        gamma_seasonality=gamma_seasonality,
    )
    
    N_rotina_arr = distribute_to_gates(N_bairro, config.w_weights)
    
    return MacroFlowResponse(
        current_time_hours=current_time_hours,
        circadian_hour=h_t,
        gamma_seasonality=gamma_seasonality,
        N_bairro_total=N_bairro,
        N_rotina=N_rotina_arr.tolist(),
        sensor_ids=sensor_ids,
    )
