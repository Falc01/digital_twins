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
from src.simulation.events_injection import calculate_events_injection

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


def calculate_gate_egress_probability(
    current_time_hours: float,
    base_rate: float = 0.08,
    step_minutes: float = 5.0,
) -> float:
    """
    Calcula a probabilidade instantânea de saída (egress) através de um nó de portão (GATE).
    
    A curva circadiana de saída é baixa pela manhã/início da tarde (quando o fluxo é
    predominantemente de entrada) e sobe no final da tarde e noite (17h às 23h),
    modelando a dispersão de volta para hotéis, residências e terminais.
    
    Formula:
        M_egress(h) = 1.0 / (1.0 + exp(-0.6 * (h - 17.5)))
        p_exit = base_rate * (0.2 + 0.8 * M_egress(h)) * (step_minutes / 5.0)
    """
    h = calculate_circadian_hour(current_time_hours)
    diff = h - 17.5
    exp_val = -0.6 * diff
    if exp_val > 40.0:
        sigmoid = 0.0
    elif exp_val < -40.0:
        sigmoid = 1.0
    else:
        sigmoid = 1.0 / (1.0 + math.exp(exp_val))
        
    modulation = 0.2 + 0.8 * sigmoid
    rate = base_rate * modulation * (step_minutes / 5.0)
    return float(np.clip(rate, 0.0, 0.85))


def compute_markov_matrix(
    dist_matrix: np.ndarray,
    alpha_vector: Sequence[float],
    lambda_decay: float = 0.015,
    retention_bias: float = 1.0,
    step_minutes: float = 5.0,
    dwell_time_minutes: float = 20.0,
    use_inertia: bool = False,
    egress_rates: Optional[Sequence[float]] = None,
) -> np.ndarray:
    """
    Computa a Matriz Estocástica de Transição de Markov P(t) de dimensão J x J (RF01, RF03, RF04).
    
    Suporta:
    - Gravidade Espacial de Huff: Numerador_ij = alpha_j(t) * exp(-lambda_d * d_ij);
    - Inércia Temporal Convexo: rho = exp(-dt / tau_dwell);
    - Cadeia de Markov Aberta com Egress: P_ij = (1 - p_exit,i) * P_ij_interno.
        
    Args:
        dist_matrix: Matriz (J, J) de distâncias euclidianas em metros.
        alpha_vector: Vetor (J,) de atratividade instantânea dos POIs.
        lambda_decay: Taxa de atrito espacial lambda_d (padrão 0.015 m^-1).
        retention_bias: Fator multiplicativo de permanência no mesmo nó.
        step_minutes: Passo temporal da simulação dt em minutos.
        dwell_time_minutes: Tempo médio de permanência tau_dwell para inércia.
        use_inertia: Ativar inércia de permanência temporal.
        egress_rates: Vetor opcional (J,) com probabilidade de saída de cada nó (GATE).
        
    Returns:
        np.ndarray: Matriz (J, J) float64 de probabilidades de transição.
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
    spatial_decay = np.exp(-lambda_decay * d_mat)
    numerator = alphas[np.newaxis, :] * spatial_decay
    
    # Aplica o viés de permanência no mesmo logradouro se diferente de 1.0
    if retention_bias != 1.0 and retention_bias > 0.0:
        np.fill_diagonal(numerator, np.diag(numerator) * retention_bias)
        
    # Normalização estocástica por linha: Denominador_i = sum_k Numerador_ik
    denominators = np.sum(numerator, axis=1, keepdims=True)
    denominators = np.where(denominators <= 0.0, 1.0, denominators)
    p_matrix = numerator / denominators

    # Inércia temporal baseada no tempo médio de permanência e granularidade Δt
    if use_inertia and dwell_time_minutes > 0.0 and step_minutes > 0.0:
        rho = math.exp(-step_minutes / dwell_time_minutes)
        p_inertial = (1.0 - rho) * p_matrix
        np.fill_diagonal(p_inertial, np.diag(p_inertial) + rho)
        p_matrix = p_inertial

    # Cadeia de Markov aberta: aplica taxas de egress nos nós de portão
    if egress_rates is not None:
        egress_arr = np.asarray(egress_rates, dtype=np.float64)
        if len(egress_arr) == j_nodes:
            survival = np.clip(1.0 - egress_arr, 0.0, 1.0)[:, np.newaxis]
            p_matrix = p_matrix * survival

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
        
    Args:
        current_N: Vetor (J,) de pedestres no ciclo atual.
        transition_matrix: Matriz P(t) de dimensão (J, J).
        
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
    n_propagado = np.dot(p_mat.T, n_vec)
    return n_propagado


class MarkovCirculationSimulator:
    """
    Simulador de Circulação de Rede via Cadeias de Markov & POIs (Doc 03).
    
    Gerencia a topologia dos sensores, o cálculo de distâncias geográficas,
    a matriz de transição dinâmica, a inércia temporal, egress nos portões
    e a redistribuição contínua de pedestres.
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
        step_minutes: Optional[float] = None,
        enable_egress: Optional[bool] = None,
        use_inertia: Optional[bool] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula a matriz estocástica P(t) e o vetor de atratividades alpha(t) para o horário dado.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (p_matrix, alpha_vector).
        """
        if t_hours is None:
            t_hours = current_system_hour()
            
        dt = step_minutes if step_minutes is not None else self.config.step_minutes
        egress_on = enable_egress if enable_egress is not None else self.config.enable_egress
        inertia_on = use_inertia if use_inertia is not None else self.config.use_inertia
            
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
            
        egress_rates = None
        if egress_on:
            egress_rates = [
                calculate_gate_egress_probability(t_hours, self.config.base_egress_rate, dt)
                if p_type.upper() == "GATE" else 0.0
                for p_type in self.poi_types
            ]
            
        p_matrix = compute_markov_matrix(
            dist_matrix=self.distance_matrix,
            alpha_vector=alphas,
            lambda_decay=self.config.lambda_decay,
            retention_bias=self.config.retention_bias,
            step_minutes=dt,
            dwell_time_minutes=self.config.dwell_time_minutes,
            use_inertia=inertia_on,
            egress_rates=egress_rates,
        )
        return p_matrix, alphas

    def propagate(
        self,
        current_state_N: Optional[Sequence[float]] = None,
        t_hours: Optional[float] = None,
        gamma: float = 1.0,
        alpha_override: Optional[Sequence[float]] = None,
        step_minutes: Optional[float] = None,
        enable_egress: Optional[bool] = None,
        use_inertia: Optional[bool] = None,
        include_raw_flow: bool = False,
        delta_N_rotina: Optional[Sequence[float]] = None,
        vector_E_eventos: Optional[Sequence[float]] = None,
    ) -> MarkovCirculationResponse:
        """
        Executa um ciclo completo de redistribuição de pedestres por Markov (Doc 03).
        
        Se current_state_N for omitido, consome o vetor N_rotina(t) do Doc 01 como baseline.
        
        Args:
            current_state_N: Vetor N(t) com a contagem atual de cada sensor.
            t_hours: Instante contínuo t em horas. Se None, lê relógio operacional.
            gamma: Multiplicador sazonal da época.
            alpha_override: Vetor opcional de atratividades customizadas.
            step_minutes: Duração do ciclo temporal em minutos.
            enable_egress: Habilitar cadeia aberta com saída nos portões.
            use_inertia: Habilitar inércia de permanência temporal.
            include_raw_flow: Compor N_bruto(t+1) com novos ingressos e eventos para o Doc 04.
            delta_N_rotina: Influxo diferencial dos portões (Doc 01).
            vector_E_eventos: Pulsos de eventos nodais (Doc 02).
            
        Returns:
            MarkovCirculationResponse: Payload com N_propagado, matriz P, fluxos nodais e N_bruto.
        """
        if t_hours is None:
            t_hours = current_system_hour()
            
        dt = step_minutes if step_minutes is not None else self.config.step_minutes
        egress_on = enable_egress if enable_egress is not None else self.config.enable_egress
        inertia_on = use_inertia if use_inertia is not None else self.config.use_inertia
            
        h = calculate_circadian_hour(t_hours)
        j_nodes = len(self.sensor_ids)
        
        # Fallback de desacoplamento: se N(t) não foi informado, utiliza a rotina diária do Doc 01
        if current_state_N is None:
            macro_res = calculate_macro_flow(
                current_time_hours=t_hours,
                gamma_seasonality=gamma,
                step_minutes=dt,
            )
            raw_n = macro_res.vector_N_rotina
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

        # Avalia matriz P(t) e atratores
        p_matrix, alphas = self.evaluate_transition_matrix(
            t_hours=t_hours,
            alpha_override=alpha_override,
            step_minutes=dt,
            enable_egress=egress_on,
            use_inertia=inertia_on,
        )
        
        # Propagação matricial: N_propagado = P^T * N_inicial
        n_propagated = propagate_flow(n_init, p_matrix)
        
        # Cálculo de egress (pedestres que deixam o bairro pelos portões)
        row_sums = np.sum(p_matrix, axis=1)
        egress_fractions = np.maximum(0.0, 1.0 - row_sums)
        n_egress = n_init * egress_fractions
        
        # Detalhamento de fluxos por nó para auditoria urbana
        node_flows: List[MarkovNodeFlow] = []
        for idx in range(j_nodes):
            init_val = float(n_init[idx])
            p_ii = float(p_matrix[idx, idx])
            retained = init_val * p_ii
            egress_val = float(n_egress[idx])
            outflow = max(0.0, init_val - retained - egress_val)
            final_val = float(n_propagated[idx])
            inflow = max(0.0, final_val - retained)
            
            node_flows.append(
                MarkovNodeFlow(
                    sensor_id=self.sensor_ids[idx],
                    nome_local=self.node_names[idx],
                    poi_type=self.poi_types[idx],
                    initial_pedestrians=round(init_val, 2),
                    retained_pedestrians=round(retained, 2),
                    inflow_pedestrians=round(max(0.0, inflow), 2),
                    outflow_pedestrians=round(max(0.0, outflow), 2),
                    egress_pedestrians=round(egress_val, 2),
                    final_propagated_pedestrians=round(final_val, 2),
                )
            )
            
        tot_ini = float(np.sum(n_init))
        tot_prop = float(np.sum(n_propagated))
        tot_egress = float(np.sum(n_egress))
        cons_err = abs((tot_prop + tot_egress) - tot_ini)
        
        # Orquestração do Fluxo Físico Bruto N_bruto(t+1) para o Doc 04
        vector_N_bruto_out = None
        if include_raw_flow:
            # 1. Taxa incremental do Doc 01
            if delta_N_rotina is not None:
                d_rot = np.asarray(delta_N_rotina, dtype=np.float64)
            else:
                macro_dt = calculate_macro_flow(
                    current_time_hours=t_hours,
                    gamma_seasonality=gamma,
                    step_minutes=dt,
                    use_incremental=True,
                )
                raw_d = macro_dt.delta_N_rotina if macro_dt.delta_N_rotina else macro_dt.vector_N_rotina
                d_rot = np.asarray(raw_d, dtype=np.float64)
            if len(d_rot) < j_nodes:
                d_rot = np.pad(d_rot, (0, j_nodes - len(d_rot)), "constant", constant_values=0.0)
            else:
                d_rot = d_rot[:j_nodes]

            # 2. Pulsos de eventos do Doc 02
            if vector_E_eventos is not None:
                e_vec = np.asarray(vector_E_eventos, dtype=np.float64)
            else:
                caps = [node.max_capacity for node in self.config.nodes]
                e_vec = calculate_events_injection(
                    current_time_hours=t_hours,
                    day_of_week=None,
                    node_capacities=caps,
                )
            if len(e_vec) < j_nodes:
                e_vec = np.pad(e_vec, (0, j_nodes - len(e_vec)), "constant", constant_values=0.0)
            else:
                e_vec = e_vec[:j_nodes]

            # 3. Composição física bruta: N_bruto = N_propagado + delta_N + E
            n_bruto = n_propagated + d_rot + e_vec
            vector_N_bruto_out = [round(float(v), 2) for v in n_bruto.tolist()]

        return MarkovCirculationResponse(
            timestamp_iso=datetime.now().isoformat(),
            current_time_hours=t_hours,
            circadian_hour=round(h, 4),
            gamma_seasonality=gamma,
            step_minutes=round(dt, 2),
            egress_enabled=bool(egress_on),
            total_initial_pedestrians=round(tot_ini, 2),
            total_propagated_pedestrians=round(tot_prop, 2),
            total_egress_pedestrians=round(tot_egress, 2),
            vector_N_propagado=[round(v, 2) for v in n_propagated.tolist()],
            vector_N_egress=[round(v, 2) for v in n_egress.tolist()],
            vector_N_bruto=vector_N_bruto_out,
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
    step_minutes: Optional[float] = None,
    enable_egress: Optional[bool] = None,
    use_inertia: Optional[bool] = None,
    include_raw_flow: bool = False,
    delta_N_rotina: Optional[Sequence[float]] = None,
    vector_E_eventos: Optional[Sequence[float]] = None,
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
        step_minutes=step_minutes,
        enable_egress=enable_egress,
        use_inertia=use_inertia,
        include_raw_flow=include_raw_flow,
        delta_N_rotina=delta_N_rotina,
        vector_E_eventos=vector_E_eventos,
    )
