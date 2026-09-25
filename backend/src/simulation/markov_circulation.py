"""
Motor Matemático de Circulação de Rede via Cadeias de Markov & Gravidade de POIs (Doc 03).

Modela a migração estocástica e redistribuição interna de pedestres entre os nós
monitorados do Centro Histórico do Pelourinho via álgebra linear vetorizada em NumPy (O(J^2)).

Classificação: Subsistema de Rede e Roteamento (Doc 03)
Complexidade Temporal: O(J^2)
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import List, Optional, Sequence, Tuple, Union
import numpy as np

from src.simulation.schemas import (
    MarkovCirculationConfig,
    MarkovCirculationRequest,
    MarkovCirculationResponse,
    MarkovNodeFlow,
    NodeCoordinate,
)
from src.simulation.macro_flow import (
    calculate_circadian_hour,
    current_system_hour,
    calculate_macro_flow,
)

logger = logging.getLogger("simulation.markov_circulation")


def compute_distance_matrix(coords: Sequence[Tuple[float, float]]) -> np.ndarray:
    """
    Computa a matriz simétrica de distâncias geográficas euclidianas d_ij em metros (Canal A).
    
    Aplica projeção euclidiana local plana corrigida pelo cosseno da latitude média de Salvador/BA.
    
    Args:
        coords: Lista de tuplas (latitude, longitude) em graus decimais WGS84.
        
    Returns:
        np.ndarray: Matriz (J, J) float64 simétrica com diagonal nula (distâncias em metros).
    """
    j_nodes = len(coords)
    dist_matrix = np.zeros((j_nodes, j_nodes), dtype=np.float64)
    
    for i in range(j_nodes):
        lat_i, lng_i = coords[i]
        for j in range(i + 1, j_nodes):
            lat_j, lng_j = coords[j]
            
            # Conversão para metros usando aproximação de latitude local
            mean_lat_rad = math.radians((lat_i + lat_j) / 2.0)
            dx = (lng_j - lng_i) * math.cos(mean_lat_rad) * 111320.0
            dy = (lat_j - lat_i) * 110540.0
            distance_m = math.sqrt(dx * dx + dy * dy)
            
            dist_matrix[i, j] = distance_m
            dist_matrix[j, i] = distance_m
            
    return dist_matrix


def evaluate_hourly_attraction(
    t_hours: float,
    base_alphas: Sequence[float],
    poi_types: Sequence[str],
) -> np.ndarray:
    """
    Modula a atratividade horária alpha_j(t) de cada POI conforme seu papel urbano (RF02).
    
    - IGREJA: Pico matinal/vespertino (missas e visitação histórica);
    - SHOW / POI: Pico vespertino/noturno (apresentações, ensaios de blocos e turismo);
    - GATE: Pico nos horários de entrada (manhã) e dispersão turística (fim de tarde).
    
    Args:
        t_hours: Horário contínuo em horas (t >= 0).
        base_alphas: Vetor de atratividades basais de dimensão J.
        poi_types: Lista de categorias ('GATE', 'POI', 'IGREJA', 'SHOW').
        
    Returns:
        np.ndarray: Vetor float64 de dimensão (J,) com atratividades instantâneas alpha_j(t) > 0.
    """
    h = calculate_circadian_hour(t_hours)
    j_nodes = len(base_alphas)
    alphas = np.zeros(j_nodes, dtype=np.float64)
    
    for idx, (base_alpha, p_type) in enumerate(zip(base_alphas, poi_types)):
        p_upper = p_type.upper() if isinstance(p_type, str) else "POI"
        
        if p_upper == "IGREJA":
            # Pico de atração por volta das 10h30 (sigma = 3.0h)
            diff = h - 10.5
            bell = math.exp(-(diff * diff) / (2.0 * 9.0))
            modulation = 1.0 + 0.8 * bell
        elif p_upper in ("SHOW", "EVENTO"):
            # Pico cultural entre 18h e 21h (centralizado em 19h00, sigma = 2.5h)
            diff = h - 19.0
            bell = math.exp(-(diff * diff) / (2.0 * 6.25))
            modulation = 1.0 + 1.2 * bell
        elif p_upper == "GATE":
            # Portões de entrada física: picos matinal (08h) e de dispersão (17h30)
            diff_in = h - 8.5
            diff_out = h - 17.5
            bell_in = math.exp(-(diff_in * diff_in) / (2.0 * 4.0))
            bell_out = math.exp(-(diff_out * diff_out) / (2.0 * 4.0))
            modulation = 1.0 + 0.4 * (bell_in + bell_out)
        else:  # POI padrão / praça
            # Lenta ascensão vespertina (pico às 16h30 acompanhando o turismo)
            diff = h - 16.5
            bell = math.exp(-(diff * diff) / (2.0 * 12.25))
            modulation = 1.0 + 0.5 * bell
            
        alphas[idx] = max(0.1, float(base_alpha) * modulation)
        
    return alphas


def compute_markov_matrix(
    dist_matrix: np.ndarray,
    alpha_vector: Sequence[float],
    lambda_decay: float = 0.015,
    retention_bias: float = 1.0,
) -> np.ndarray:
    """
    Computa a Matriz Estocástica de Transição de Markov P(t) de dimensão J x J (RF01, RF03, RF04).
    
    Formula:
        Numerador_ij = alpha_j(t) * exp( -lambda_d * d_ij )
        Numerador_ii = Numerador_ii * retention_bias
        Denominador_i = sum_k Numerador_ik
        P_ij = Numerador_ij / Denominador_i
        
    Propriedade Estocástica Rigorosa:
        sum_j P_ij = 1.0 para todo i (linha unitária).
        
    Args:
        dist_matrix: Matriz (J, J) de distâncias euclidianas em metros.
        alpha_vector: Vetor (J,) de atratividade instantânea dos POIs.
        lambda_decay: Taxa de atrito espacial lambda_d (padrão 0.015 m^-1).
        retention_bias: Fator multiplicativo de permanência no mesmo nó.
        
    Returns:
        np.ndarray: Matriz (J, J) float64 estocástica de probabilidades.
    """
    d_mat = np.asarray(dist_matrix, dtype=np.float64)
    alphas = np.asarray(alpha_vector, dtype=np.float64)
    j_nodes = d_mat.shape[0]
    
    if d_mat.shape[0] != d_mat.shape[1]:
        raise ValueError("A matriz de distâncias deve ser quadrada (J x J).")
    if alphas.ndim != 1 or len(alphas) != j_nodes:
        raise ValueError(f"O vetor de atratividades deve ter dimensão igual a {j_nodes}.")
    if np.any(alphas <= 0.0):
        raise ValueError("Todos os valores de atratividade alpha_j devem ser estritamente positivos.")
    if lambda_decay <= 0.0:
        raise ValueError("A taxa de decaimento lambda_decay deve ser estritamente positiva.")

    # Numerador gravitacional vetorizado: broadcast de alpha_j sobre a exponencial de distâncias
    # dist_matrix tem shape (J, J); alphas tem shape (J,) -> alphas atua como coluna de destino j
    spatial_decay = np.exp(-lambda_decay * d_mat)
    numerator = alphas[np.newaxis, :] * spatial_decay
    
    # Aplica o viés de permanência no mesmo logradouro se diferente de 1.0
    if retention_bias != 1.0 and retention_bias > 0.0:
        np.fill_diagonal(numerator, np.diag(numerator) * retention_bias)
        
    # Normalização estocástica por linha: Denominador_i = sum_k Numerador_ik
    denominators = np.sum(numerator, axis=1, keepdims=True)
    denominators = np.where(denominators <= 0.0, 1.0, denominators)
    p_matrix = numerator / denominators
    return p_matrix


def propagate_flow(
    current_N: Union[np.ndarray, Sequence[float]],
    transition_matrix: np.ndarray,
) -> np.ndarray:
    """
    Propaga o vetor de ocupação através da álgebra linear da matriz de Markov (RF05).
    
    Formula:
        N_propagado(t+1) = P(t)^T * N(t)
        N_j,propagado(t+1) = sum_i P_ij(t) * N_i(t)
        
    Conservação de Pedestres:
        sum_j N_j,propagado(t+1) == sum_i N_i(t)
        
    Args:
        current_N: Vetor (J,) de pedestres no ciclo atual.
        transition_matrix: Matriz estocástica P(t) de dimensão (J, J).
        
    Returns:
        np.ndarray: Vetor (J,) float64 com a contagem redistribuída em indivíduos.
    """
    n_vec = np.asarray(current_N, dtype=np.float64)
    p_mat = np.asarray(transition_matrix, dtype=np.float64)
    
    if n_vec.ndim != 1:
        raise ValueError("O vetor de ocupação atual current_N deve ser 1D.")
    if p_mat.shape != (len(n_vec), len(n_vec)):
        raise ValueError(
            f"Dimensão incompatível: vetor N tem tamanho {len(n_vec)} e "
            f"matriz P tem dimensões {p_mat.shape}."
        )
        
    # Álgebra linear: N_propagado = P^T * N_atual
    # No NumPy, p_mat.T @ n_vec equivale a dot(p_mat.T, n_vec)
    n_propagado = np.dot(p_mat.T, n_vec)
    return n_propagado


class MarkovCirculationSimulator:
    """
    Simulador de Circulação de Rede via Cadeias de Markov & POIs (Doc 03).
    
    Gerencia a topologia dos sensores, o cálculo de distâncias geográficas,
    a matriz de transição dinâmica e a redistribuição contínua de pedestres.
    """

    def __init__(self, config: Optional[MarkovCirculationConfig] = None) -> None:
        self.config = config or MarkovCirculationConfig()
        self._init_spatial_network()

    def _init_spatial_network(self) -> None:
        """Inicializa coordenadas e pré-computa matriz de distâncias d_ij."""
        coords = [(node.lat, node.lng) for node in self.config.nodes]
        self.distance_matrix = compute_distance_matrix(coords)
        self.sensor_ids = [node.sensor_id for node in self.config.nodes]
        self.node_names = [node.nome_local for node in self.config.nodes]
        self.poi_types = [node.poi_type for node in self.config.nodes]
        self.base_alphas = [node.base_attraction for node in self.config.nodes]

    def evaluate_transition_matrix(
        self,
        t_hours: Optional[float] = None,
        alpha_override: Optional[Sequence[float]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula a matriz estocástica P(t) e o vetor de atratividades alpha(t) para o horário dado.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (p_matrix, alpha_vector).
        """
        if t_hours is None:
            t_hours = current_system_hour()
            
        if alpha_override is not None:
            alphas = np.asarray(alpha_override, dtype=np.float64)
            if len(alphas) != len(self.sensor_ids):
                raise ValueError(
                    f"alpha_override deve ter exatamente {len(self.sensor_ids)} elementos."
                )
        else:
            alphas = evaluate_hourly_attraction(
                t_hours=t_hours,
                base_alphas=self.base_alphas,
                poi_types=self.poi_types,
            )
            
        p_matrix = compute_markov_matrix(
            dist_matrix=self.distance_matrix,
            alpha_vector=alphas,
            lambda_decay=self.config.lambda_decay,
            retention_bias=self.config.retention_bias,
        )
        return p_matrix, alphas

    def propagate(
        self,
        current_state_N: Optional[Sequence[float]] = None,
        t_hours: Optional[float] = None,
        gamma: float = 1.0,
        alpha_override: Optional[Sequence[float]] = None,
    ) -> MarkovCirculationResponse:
        """
        Executa um ciclo completo de redistribuição de pedestres por Markov (Doc 03).
        
        Se current_state_N for omitido, consome o vetor N_rotina(t) do Doc 01 como baseline.
        
        Args:
            current_state_N: Vetor N(t) com a contagem atual de cada sensor.
            t_hours: Instante contínuo t em horas. Se None, lê relógio operacional.
            gamma: Multiplicador sazonal da época.
            alpha_override: Vetor opcional de atratividades customizadas.
            
        Returns:
            MarkovCirculationResponse: Payload com N_propagado, matriz P e fluxos nodais.
        """
        if t_hours is None:
            t_hours = current_system_hour()
            
        h = calculate_circadian_hour(t_hours)
        j_nodes = len(self.sensor_ids)
        
        # Fallback de desacoplamento: se N(t) não foi informado, utiliza a rotina diária do Doc 01
        if current_state_N is None:
            macro_res = calculate_macro_flow(
                current_time_hours=t_hours,
                gamma_seasonality=gamma,
            )
            raw_n = macro_res.vector_N_rotina
            # Ajusta tamanho se a malha de Markov tiver nós internos sem entrada física
            if len(raw_n) < j_nodes:
                n_init = np.pad(raw_n, (0, j_nodes - len(raw_n)), "constant", constant_values=0.0)
            else:
                n_init = np.array(raw_n[:j_nodes], dtype=np.float64)
        else:
            n_init = np.asarray(current_state_N, dtype=np.float64)
            if len(n_init) != j_nodes:
                raise ValueError(
                    f"Vetor de estado N deve ter tamanho {j_nodes} (fornecido: {len(n_init)})."
                )

        # Avalia matriz estocástica P(t) e atratores
        p_matrix, alphas = self.evaluate_transition_matrix(
            t_hours=t_hours,
            alpha_override=alpha_override,
        )
        
        # Propagação matricial: N_propagado = P^T * N_inicial
        n_propagated = propagate_flow(n_init, p_matrix)
        
        # Detalhamento de fluxos por nó para auditoria urbana
        node_flows: List[MarkovNodeFlow] = []
        for idx in range(j_nodes):
            init_val = float(n_init[idx])
            p_ii = float(p_matrix[idx, idx])
            retained = init_val * p_ii
            outflow = init_val - retained
            final_val = float(n_propagated[idx])
            inflow = final_val - retained
            
            node_flows.append(
                MarkovNodeFlow(
                    sensor_id=self.sensor_ids[idx],
                    nome_local=self.node_names[idx],
                    poi_type=self.poi_types[idx],
                    initial_pedestrians=round(init_val, 2),
                    retained_pedestrians=round(retained, 2),
                    inflow_pedestrians=round(max(0.0, inflow), 2),
                    outflow_pedestrians=round(max(0.0, outflow), 2),
                    final_propagated_pedestrians=round(final_val, 2),
                )
            )
            
        tot_ini = float(np.sum(n_init))
        tot_prop = float(np.sum(n_propagated))
        cons_err = abs(tot_prop - tot_ini)
        
        return MarkovCirculationResponse(
            timestamp_iso=datetime.now().isoformat(),
            current_time_hours=t_hours,
            circadian_hour=round(h, 4),
            gamma_seasonality=gamma,
            total_initial_pedestrians=round(tot_ini, 2),
            total_propagated_pedestrians=round(tot_prop, 2),
            vector_N_propagado=[round(v, 2) for v in n_propagated.tolist()],
            transition_matrix=[[round(float(p), 4) for p in row] for row in p_matrix.tolist()],
            attraction_vector=[round(float(a), 3) for a in alphas.tolist()],
            node_flows=node_flows,
            sensor_ids=self.sensor_ids,
            conservation_error=round(cons_err, 6),
        )


def propagate_markov_flow(
    current_state_N: Optional[Sequence[float]] = None,
    current_time_hours: Optional[float] = None,
    gamma_seasonality: float = 1.0,
    config: Optional[MarkovCirculationConfig] = None,
    alpha_override: Optional[Sequence[float]] = None,
) -> MarkovCirculationResponse:
    """
    Função principal do Subsistema de Circulação de Markov (Doc 03).
    Executa a propagação estocástica e retorna a resposta formatada para a API ou barramento.
    """
    simulator = MarkovCirculationSimulator(config=config)
    return simulator.propagate(
        current_state_N=current_state_N,
        t_hours=current_time_hours,
        gamma=gamma_seasonality,
        alpha_override=alpha_override,
    )
