"""
Subsistema de Saturação Física de Richards, Ruído Instrumental IoT & Telemetria (Doc 04).

Implementa:
- RF01: Integração nodal dos fluxos brutos N_bruto(t+1) = N_propagado(t+1) + Delta N_rotina(t) + E(t);
- RF02: Barreira logística de capacidade de Richards S_j(N_bruto) com ancoragem em zero;
- RF03: Injeção de ruído instrumental estocástico (Uniforme, Gaussiano, Ornstein-Uhlenbeck com reversão à média);
- RF04: Discretização e limitador estrito clip(round(S + eps), 0, N_max) in N;
- RF05: Emissão e persistência de telemetria IoT (GeoPackage e Leaflet);
- RNF01: Latência inferior a 1 ms por ciclo de sensoriamento;
- RNF02: Estabilidade estocástica do processo OU em memória fixa.
"""

from __future__ import annotations

import math
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from src.simulation.schemas import (
    RichardsSaturationConfig,
    SensorNoiseConfig,
    SensorNoiseType,
    SensorNodeMetadata,
    SensorSaturationConfig,
    SensorSaturationRequest,
    SensorTelemetryItem,
    SensorTelemetryResponse,
)


# ==============================================================================
# 1. Funções Matemáticas Fundamentais de Sensoriamento
# ==============================================================================

def calculate_richards_saturation(
    N_bruto: Union[np.ndarray, List[float]],
    N_max: Union[np.ndarray, List[float]],
    kappa: Union[float, np.ndarray, List[float]] = 0.08,
    lambda_0: Optional[Union[float, np.ndarray, List[float]]] = None,
    zero_anchored: bool = True,
) -> np.ndarray:
    """
    Calcula a saturação física não-linear via curva logística de Richards (RF02).

    Fórmula clássica:
        S_raw(N) = N_max / (1 + exp(-kappa * [N_bruto - lambda_0]))

    Ancoragem em zero (zero_anchored=True):
        Elimina "pedestres fantasmas" garantindo S_adj(0) = 0.0 e S_adj(N -> inf) = N_max:
        S(0) = N_max / (1 + exp(kappa * lambda_0))
        S_adj(N) = max(0.0, (S_raw(N) - S(0)) / (1.0 - S(0) / N_max))

    Args:
        N_bruto: Vetor de pedestres brutos em R^J
        N_max: Vetor de capacidades máximas físicas N_j,max em R^J
        kappa: Declividade logística kappa_j > 0 (escalar ou vetor)
        lambda_0: Ponto de inflexão (se None, padrão é N_max * 0.5)
        zero_anchored: Se True, aplica calibração zero-anchored

    Returns:
        np.ndarray: Vetor contínuo S de shape (J,), com 0.0 <= S_j <= N_j,max
    """
    n_in = np.asarray(N_bruto, dtype=np.float64)
    n_ceiling = np.asarray(N_max, dtype=np.float64)

    if n_in.shape != n_ceiling.shape:
        raise ValueError(
            f"Dimensões incompatíveis: N_bruto ({n_in.shape}) e N_max ({n_ceiling.shape})"
        )

    # Inflexão padrão: metade da capacidade máxima (lambda_0 = N_max / 2)
    if lambda_0 is None:
        l0 = n_ceiling * 0.5
    else:
        l0 = np.asarray(lambda_0, dtype=np.float64)

    k = np.asarray(kappa, dtype=np.float64)

    # Prevenção de overflow/underflow em exp(-kappa * (N - lambda_0))
    # z no intervalo [-60.0, 60.0] garante precisão de ponto flutuante IEEE-754
    exponent = -k * (n_in - l0)
    exponent_clipped = np.clip(exponent, -60.0, 60.0)

    s_raw = n_ceiling / (1.0 + np.exp(exponent_clipped))

    if zero_anchored:
        # Ponto correspondente a N_bruto = 0
        exp_zero = np.clip(k * l0, -60.0, 60.0)
        s_zero = n_ceiling / (1.0 + np.exp(exp_zero))

        denominator = 1.0 - (s_zero / np.maximum(n_ceiling, 1e-9))
        denominator_safe = np.where(np.abs(denominator) < 1e-12, 1e-12, denominator)

        s_adj = (s_raw - s_zero) / denominator_safe
        s_final = np.clip(s_adj, 0.0, n_ceiling)
    else:
        s_final = np.clip(s_raw, 0.0, n_ceiling)

    return s_final


def generate_sensor_noise(
    method: Union[str, SensorNoiseType],
    size: int,
    dt_hours: float = 5.0 / 60.0,
    prev_state: Optional[np.ndarray] = None,
    uniform_range_R: float = 3.0,
    gaussian_sigma: float = 2.5,
    ou_theta: float = 1.2,
    ou_sigma: float = 2.0,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gera o vetor de ruído instrumental estocástico epsilon(t) segundo o método ativo (RF03).

    Métodos:
    1. 'NONE': Ruído nulo (0.0);
    2. 'UNIFORM': Variação independente uniforme em [-R, +R];
    3. 'GAUSSIAN': Ruído branco normal N(0, sigma^2);
    4. 'ORNSTEIN_UHLENBECK' (ou 'OU'): Processo de reversão à média com persistência temporal:
       eps(t + dt) = eps(t) * exp(-theta * dt) + sigma_sensor * sqrt((1 - exp(-2*theta*dt))/(2*theta)) * Z_t

    Args:
        method: Nome do método de perturbação estocástica
        size: Dimensão J do vetor de sensores
        dt_hours: Passo temporal Delta t em horas (ex: 5 min = 5/60 = 0.0833 h)
        prev_state: Estado anterior eps(t) para o processo de Ornstein-Uhlenbeck
        uniform_range_R: Semi-intervalo R para ruído uniforme
        gaussian_sigma: Desvio padrão para ruído gaussiano
        ou_theta: Taxa horária de reversão à média theta
        ou_sigma: Volatilidade da difusão sigma_sensor
        rng: Gerador NumPy para reprodutibilidade

    Returns:
        Tuple[np.ndarray, np.ndarray]: (ruido_atual, proximo_estado)
    """
    if rng is None:
        rng = np.random.default_rng()

    norm_method = (
        method.value if isinstance(method, SensorNoiseType) else str(method).strip().upper()
    )

    if norm_method == "NONE":
        eps = np.zeros(size, dtype=np.float64)
        return eps, eps.copy()

    if norm_method == "UNIFORM":
        eps = rng.uniform(-uniform_range_R, uniform_range_R, size=size).astype(np.float64)
        return eps, eps.copy()

    if norm_method == "GAUSSIAN":
        eps = rng.normal(0.0, gaussian_sigma, size=size).astype(np.float64)
        return eps, eps.copy()

    if norm_method in ("ORNSTEIN_UHLENBECK", "OU"):
        if prev_state is None or len(prev_state) != size:
            current_eps = np.zeros(size, dtype=np.float64)
        else:
            current_eps = np.asarray(prev_state, dtype=np.float64)

        dt = max(dt_hours, 1e-6)
        theta = max(ou_theta, 1e-6)
        sigma = max(ou_sigma, 0.0)

        # Fator de decaimento determínico: exp(-theta * dt)
        decay = math.exp(-theta * dt)

        # Variância condicional exata do processo Ornstein-Uhlenbeck integrado
        exp_2theta_dt = math.exp(-2.0 * theta * dt)
        variance_factor = (1.0 - exp_2theta_dt) / (2.0 * theta)
        std_diffusion = sigma * math.sqrt(max(0.0, variance_factor))

        # Inovação gaussiana padrão Z_t ~ N(0, 1)
        z_t = rng.standard_normal(size=size)

        # Atualização discreta exata
        next_eps = current_eps * decay + std_diffusion * z_t
        return next_eps, next_eps.copy()

    raise ValueError(
        f"Método de ruído desconhecido: '{method}'. Opções válidas: NONE, UNIFORM, GAUSSIAN, ORNSTEIN_UHLENBECK"
    )


def clip_and_discretize_sensor_readings(
    S: Union[np.ndarray, List[float]],
    epsilon: Union[np.ndarray, List[float]],
    N_max: Union[np.ndarray, List[float]],
) -> np.ndarray:
    """
    Aplica discretização e operador de limitador estrito clip(round(S + eps), 0, N_max) in N (RF04).

    Garante:
    - Leituras inteiras estritas N_j^sensor in N;
    - Não-negatividade física (N_j^sensor >= 0);
    - Teto intransponível da capacidade do espaço (N_j^sensor <= N_j,max).

    Args:
        S: Vetor contínuo saturado de Richards em R^J
        epsilon: Vetor de ruído instrumental em R^J
        N_max: Vetor de capacidade máxima N_j,max

    Returns:
        np.ndarray: Leituras discretas inteiras de shape (J,), dtype=np.int64
    """
    s_arr = np.asarray(S, dtype=np.float64)
    eps_arr = np.asarray(epsilon, dtype=np.float64)
    ceil_arr = np.asarray(N_max, dtype=np.float64)

    raw_signal = s_arr + eps_arr
    rounded = np.rint(raw_signal)
    bounded = np.clip(rounded, 0.0, ceil_arr)
    return bounded.astype(np.int64)


def determine_sensor_status(occupancy_pct: float) -> str:
    """
    Classifica o nível de alerta de aglomeração do sensor segundo a taxa percentual de ocupação.

    - CRITICO: taxa > 90%
    - ATENCAO: 70% < taxa <= 90%
    - NORMAL: taxa <= 70%
    """
    if occupancy_pct > 90.0:
        return "CRITICO"
    if occupancy_pct > 70.0:
        return "ATENCAO"
    return "NORMAL"


# ==============================================================================
# 2. Classe Simuladora de Sensoriamento e Integração IoT
# ==============================================================================

class SensorSaturationSimulator:
    """
    Motor analítico para o Subsistema de Sensoriamento IoT e Barreira de Richards (Doc 04).

    Mantém:
    - Configuração de nós, capacidades e parâmetros de saturação;
    - Estado de ruído de Ornstein-Uhlenbeck em memória estática (_ou_noise_state) sem vazamento (RNF02);
    - Cache da última leitura de telemetria emitida;
    - Integração opcional com o Datalake GeoPackage (tabela telemetria_sensores).
    """

    def __init__(
        self,
        config: Optional[SensorSaturationConfig] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.config = config or SensorSaturationConfig()
        active_seed = seed if seed is not None else self.config.noise.seed
        self._rng = np.random.default_rng(active_seed)
        self._ou_noise_state: Optional[np.ndarray] = None
        self._latest_response: Optional[SensorTelemetryResponse] = None

    @property
    def node_count(self) -> int:
        return len(self.config.nodes)

    @property
    def sensor_ids(self) -> List[str]:
        return [node.sensor_id for node in self.config.nodes]

    @property
    def node_names(self) -> List[str]:
        return [node.nome_local for node in self.config.nodes]

    @property
    def node_capacities(self) -> np.ndarray:
        return np.array([node.max_capacity for node in self.config.nodes], dtype=np.float64)

    @property
    def node_kappas(self) -> np.ndarray:
        return np.array(
            [node.kappa if node.kappa > 0.0 else self.config.richards.kappa for node in self.config.nodes],
            dtype=np.float64,
        )

    @property
    def node_inflections(self) -> np.ndarray:
        return np.array(
            [
                node.inflection_point
                if node.inflection_point is not None
                else node.max_capacity * self.config.richards.inflection_ratio
                for node in self.config.nodes
            ],
            dtype=np.float64,
        )

    def reset_state(self) -> None:
        """Reinicia o estado interno do ruído de Ornstein-Uhlenbeck para zero."""
        self._ou_noise_state = None

    def evaluate(
        self,
        N_bruto: Optional[Union[np.ndarray, List[float]]] = None,
        N_propagado: Optional[Union[np.ndarray, List[float]]] = None,
        N_rotina: Optional[Union[np.ndarray, List[float]]] = None,
        delta_N_rotina: Optional[Union[np.ndarray, List[float]]] = None,
        vector_E_eventos: Optional[Union[np.ndarray, List[float]]] = None,
        current_time_hours: Optional[float] = None,
        step_minutes: Optional[float] = None,
        noise_method: Optional[Union[str, SensorNoiseType]] = None,
        persist_telemetry: bool = False,
        reset_noise_state: bool = False,
        table_manager: Any = None,
    ) -> SensorTelemetryResponse:
        """
        Executa o pipeline completo do Doc 04 (RF01 a RF05):
        1. Integra fluxos brutos se N_bruto não for fornecido explicitamente;
        2. Aplica a barreira logística de Richards com ancoragem em zero;
        3. Injeta ruído instrumental estocástico;
        4. Discretiza e aplica limitador estrito [0, N_max];
        5. Constrói o payload de telemetria IoT e opcionalmente persiste no GeoPackage.
        """
        if reset_noise_state:
            self.reset_state()

        t_hours = (
            current_time_hours
            if current_time_hours is not None
            else (datetime.now().hour + datetime.now().minute / 60.0)
        )
        dt_min = step_minutes if step_minutes is not None else self.config.step_minutes
        dt_hours = dt_min / 60.0

        # RF01: Determinação do vetor de fluxo físico bruto N_bruto
        if N_bruto is not None:
            n_raw = np.asarray(N_bruto, dtype=np.float64)
            size = len(n_raw)
        else:
            # Integração nodal elemento a elemento: N_prop + Delta_N_rotina + E_eventos
            size = self.node_count

            # 1. Componente de propagação de Markov (Doc 03)
            if N_propagado is not None:
                prop_arr = np.asarray(N_propagado, dtype=np.float64)
            else:
                from src.simulation.markov_circulation import MarkovCirculationSimulator
                markov_sim = MarkovCirculationSimulator()
                markov_res = markov_sim.propagate(t_hours=t_hours, step_minutes=dt_min)
                prop_arr = np.asarray(markov_res.vector_N_propagado, dtype=np.float64)

            # 2. Componente de novos ingressos nos portões de rotina (Doc 01)
            if delta_N_rotina is not None:
                rot_arr = np.asarray(delta_N_rotina, dtype=np.float64)
            elif N_rotina is not None:
                rot_arr = np.asarray(N_rotina, dtype=np.float64)
            else:
                from src.simulation.macro_flow import MacroFlowSimulator
                macro_sim = MacroFlowSimulator()
                macro_res = macro_sim.evaluate(t_hours=t_hours, step_minutes=dt_min)
                # Adapta tamanho caso a malha de portões do Doc 01 tenha tamanho diferente
                base_rot = np.asarray(macro_res.delta_N_rotina or macro_res.N_rotina, dtype=np.float64)
                rot_arr = np.zeros(len(prop_arr), dtype=np.float64)
                min_len = min(len(base_rot), len(rot_arr))
                rot_arr[:min_len] = base_rot[:min_len]

            # 3. Componente de injeção de eventos (Doc 02)
            if vector_E_eventos is not None:
                evt_arr = np.asarray(vector_E_eventos, dtype=np.float64)
            else:
                from src.simulation.events_injection import EventsInjectionSimulator
                events_sim = EventsInjectionSimulator()
                evt_res = events_sim.evaluate(current_time_hours=t_hours)
                base_evt = np.asarray(evt_res.vector_E_eventos, dtype=np.float64)
                evt_arr = np.zeros(len(prop_arr), dtype=np.float64)
                min_len = min(len(base_evt), len(evt_arr))
                evt_arr[:min_len] = base_evt[:min_len]

            # Ajuste de dimensões de compatibilidade
            max_dim = max(len(prop_arr), len(rot_arr), len(evt_arr))
            p_pad = np.pad(prop_arr, (0, max_dim - len(prop_arr)))
            r_pad = np.pad(rot_arr, (0, max_dim - len(rot_arr)))
            e_pad = np.pad(evt_arr, (0, max_dim - len(evt_arr)))

            n_raw = p_pad + r_pad + e_pad
            size = max_dim

        # Alinha parâmetros de capacidade física N_max para a dimensão observada
        if size == self.node_count:
            capacities = self.node_capacities
            kappas = self.node_kappas
            inflections = self.node_inflections
            nodes_meta = self.config.nodes
        else:
            # Caso o tamanho do vetor de entrada seja diferente dos nós padrão
            capacities = np.array(
                [self.config.nodes[i].max_capacity if i < self.node_count else 150 for i in range(size)],
                dtype=np.float64,
            )
            kappas = np.full(size, self.config.richards.kappa, dtype=np.float64)
            inflections = capacities * self.config.richards.inflection_ratio
            nodes_meta = [
                self.config.nodes[i]
                if i < self.node_count
                else SensorNodeMetadata(
                    sensor_id=f"sensor_extra_{i}",
                    nome_local=f"Sensor Extra {i}",
                    max_capacity=int(capacities[i]),
                    kappa=self.config.richards.kappa,
                )
                for i in range(size)
            ]

        # RF02: Aplicação da barreira logística de Richards
        s_richards = calculate_richards_saturation(
            N_bruto=n_raw,
            N_max=capacities,
            kappa=kappas,
            lambda_0=inflections,
            zero_anchored=self.config.richards.zero_anchored,
        )

        # RF03: Injeção de Ruído Instrumental IoT
        active_noise_method = noise_method if noise_method is not None else self.config.noise.method
        eps_noise, next_ou_state = generate_sensor_noise(
            method=active_noise_method,
            size=size,
            dt_hours=dt_hours,
            prev_state=self._ou_noise_state,
            uniform_range_R=self.config.noise.uniform_range_R,
            gaussian_sigma=self.config.noise.gaussian_sigma,
            ou_theta=self.config.noise.ou_theta,
            ou_sigma=self.config.noise.ou_sigma,
            rng=self._rng,
        )
        self._ou_noise_state = next_ou_state

        # RF04: Discretização e Limitador Estrito [0, N_max]
        n_sensor_discrete = clip_and_discretize_sensor_readings(
            S=s_richards,
            epsilon=eps_noise,
            N_max=capacities,
        )

        # RF05: Formatação de Telemetria IoT para Leaflet e GeoPackage
        now_iso = datetime.now().isoformat()
        items: List[SensorTelemetryItem] = []

        for idx in range(size):
            meta = nodes_meta[idx]
            count = int(n_sensor_discrete[idx])
            cap = int(capacities[idx])
            occ_pct = round((count / max(cap, 1)) * 100.0, 2)

            # Área de cobertura (se não informada, assume densidade de projeto 1 pessoa/m²)
            area = meta.area_m2 if (meta.area_m2 and meta.area_m2 > 0.0) else float(cap)
            density = round(count / max(area, 0.1), 2)
            status = determine_sensor_status(occ_pct)

            items.append(
                SensorTelemetryItem(
                    sensor_id=meta.sensor_id,
                    nome_local=meta.nome_local,
                    count=count,
                    max_capacity=cap,
                    occupancy_pct=occ_pct,
                    density_m2=density,
                    status=status,
                    latitude=meta.lat,
                    longitude=meta.lng,
                    raw_input=round(float(n_raw[idx]), 2),
                    saturated_val=round(float(s_richards[idx]), 2),
                    noise_val=round(float(eps_noise[idx]), 2),
                )
            )

        persisted_count = 0
        if persist_telemetry:
            persisted_count = self._persist_to_datalake(items, now_iso, table_manager=table_manager)

        method_str = (
            active_noise_method.value
            if isinstance(active_noise_method, SensorNoiseType)
            else str(active_noise_method).upper()
        )

        response = SensorTelemetryResponse(
            timestamp_iso=now_iso,
            current_time_hours=t_hours,
            noise_method=method_str,
            step_minutes=dt_min,
            vector_N_bruto=[round(float(x), 2) for x in n_raw.tolist()],
            vector_S_richards=[round(float(x), 2) for x in s_richards.tolist()],
            vector_epsilon_noise=[round(float(x), 2) for x in eps_noise.tolist()],
            vector_N_sensor=[int(x) for x in n_sensor_discrete.tolist()],
            sensors=items,
            persisted_rows=persisted_count,
        )

        self._latest_response = response
        return response

    def _persist_to_datalake(
        self,
        items: List[SensorTelemetryItem],
        timestamp_iso: str,
        table_manager: Any = None,
    ) -> int:
        """
        Persiste as leituras de telemetria na tabela telemetria_sensores do Datalake (.dyndb / GeoPackage).
        """
        mgr = table_manager
        if mgr is None:
            try:
                from src.dyntable.logic.table_manager import TableManager
                from shared.config import DATA_DIR
                mgr = TableManager(DATA_DIR)
            except Exception:
                return 0

        try:
            from src.dyntable.data._types import DynType

            table_name = "telemetria_sensores"
            table, created = mgr.get_or_create(table_name)

            if created or not table.column_names:
                table.add_column("sensor_id", DynType.STRING)
                table.add_column("timestamp", DynType.STRING)
                table.add_column("contagem_pedestres", DynType.INT)
                table.add_column("densidade_m2", DynType.FLOAT)
                table.add_column("status_aglomeracao", DynType.STRING)
                table.add_column("taxa_ocupacao_pct", DynType.FLOAT)
                table.add_column("capacidade_max", DynType.INT)

            for item in items:
                table.new_row(
                    sensor_id=item.sensor_id,
                    timestamp=timestamp_iso,
                    contagem_pedestres=item.count,
                    densidade_m2=item.density_m2,
                    status_aglomeracao=item.status,
                    taxa_ocupacao_pct=item.occupancy_pct,
                    capacidade_max=item.max_capacity,
                )

            mgr.save(table)
            return len(items)
        except Exception as e:
            # Fallback tolerante a falhas sem interromper a execução do fluxo analítico
            return 0

    def get_latest_telemetry(self) -> Optional[SensorTelemetryResponse]:
        """Retorna o cache da última leitura de telemetria gerada ou gera uma instantânea."""
        if self._latest_response is not None:
            return self._latest_response
        return self.evaluate()


# Instância singleton padrão do simulador calibrada para a rede de sensoriamento do Pelourinho
_DEFAULT_SATURATION_SIMULATOR = SensorSaturationSimulator()


def simulate_sensor_telemetry(
    request: Optional[SensorSaturationRequest] = None,
    config: Optional[SensorSaturationConfig] = None,
    table_manager: Any = None,
) -> SensorTelemetryResponse:
    """
    Função funcional de alto nível para invocação direta do Subsistema de Sensoriamento (Doc 04).
    """
    sim = _DEFAULT_SATURATION_SIMULATOR
    if config is not None or (request is not None and request.config is not None):
        cfg = config or request.config
        sim = SensorSaturationSimulator(config=cfg)

    req = request or SensorSaturationRequest()

    return sim.evaluate(
        N_bruto=req.N_bruto or req.vector_N_bruto,
        N_propagado=req.N_propagado or req.vector_N_propagado,
        N_rotina=req.N_rotina,
        delta_N_rotina=req.delta_N_rotina,
        vector_E_eventos=req.vector_E_eventos,
        current_time_hours=req.current_time_hours,
        step_minutes=req.step_minutes,
        noise_method=req.noise_method,
        persist_telemetry=req.persist_telemetry,
        reset_noise_state=req.reset_noise_state,
        table_manager=table_manager,
    )
