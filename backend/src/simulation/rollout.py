"""
Motor de Simulação Contínua / Encadeamento Temporal (Rollout 24h) dos Pedestres do Pelourinho.

Integra de forma contínua:
- Doc 01 (Módulo de Entrada): Influxo macroscópico basal nos portões (ΔN_rotina, regime trimodal v2.0).
- Doc 02 (Injeção de Eventos): Pulsos culturais pontuais opcionais (E(t)).
- Doc 03 (Circulação de Rede): Redistribuição espacial via Cadeias de Markov e Egress (saída natural).

Fornece execução em Lote (Batch instantâneo) e em Tempo Real (Live Streaming Ticker).
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Sequence, Union
import numpy as np

from src.simulation.macro_flow import (
    MacroFlowSimulator,
    calculate_circadian_hour,
    calculate_macro_flow,
)
from src.simulation.markov_circulation import (
    MarkovCirculationSimulator,
    compute_markov_matrix,
    propagate_flow,
)
from src.simulation.events_injection import calculate_events_injection
from src.simulation.schemas import (
    MacroFlowConfig,
    MarkovCirculationConfig,
    NodeCoordinate,
    UrbanGateNode,
)

logger = logging.getLogger("simulation.rollout")


@dataclass
class RolloutStep:
    """Representa o estado completo e os fluxos de um passo discreto de simulação."""
    step_index: int
    time_hours: float
    hour_formatted: str
    total_population: float
    total_inflow: float
    total_egress: float
    net_flux: float
    state_N: List[float]
    node_names: List[str]
    poi_types: List[str]
    inflow_by_gate: Dict[str, float]
    egress_by_gate: Dict[str, float]
    occupancy_by_node: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "time_hours": round(self.time_hours, 2),
            "hour_formatted": self.hour_formatted,
            "total_population": round(self.total_population, 2),
            "total_inflow": round(self.total_inflow, 2),
            "total_egress": round(self.total_egress, 2),
            "net_flux": round(self.net_flux, 2),
            "state_N": [round(v, 2) for v in self.state_N],
            "inflow_by_gate": {k: round(v, 2) for k, v in self.inflow_by_gate.items()},
            "egress_by_gate": {k: round(v, 2) for k, v in self.egress_by_gate.items()},
            "occupancy_by_node": {k: round(v, 2) for k, v in self.occupancy_by_node.items()},
        }


@dataclass
class RolloutSummary:
    """Resumo estatístico consolidado de uma simulação de 24 horas."""
    total_steps: int
    step_minutes: float
    cumulative_inflow: float
    cumulative_egress: float
    peak_population: float
    peak_time_hours: float
    peak_time_formatted: str
    final_population: float
    net_city_balance: float
    regime: str
    steps: List[RolloutStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_steps": self.total_steps,
            "step_minutes": self.step_minutes,
            "cumulative_inflow": round(self.cumulative_inflow, 2),
            "cumulative_egress": round(self.cumulative_egress, 2),
            "peak_population": round(self.peak_population, 2),
            "peak_time_hours": round(self.peak_time_hours, 2),
            "peak_time_formatted": self.peak_time_formatted,
            "final_population": round(self.final_population, 2),
            "net_city_balance": round(self.net_city_balance, 2),
            "regime": self.regime,
            "steps": [s.to_dict() for s in self.steps],
        }


class RolloutSimulationEngine:
    """
    Motor central de orquestração contínua do Gêmeo Digital.
    
    Avança os ciclos discretos de simulação computando:
    1. Entrada (Doc 01): ΔN_rotina(t) ponderada pelos portões de borda;
    2. Eventos (Doc 02): E(t) pulsos nos atratores culturais;
    3. Circulação e Egress (Doc 03): N_propagado = P(t)^T * N(t) com extração de saídas;
    4. Atualização de Estado: N(t+1) = N_propagado + ΔN_rotina + E.
    """

    def __init__(
        self,
        macro_config: Optional[MacroFlowConfig] = None,
        markov_config: Optional[MarkovCirculationConfig] = None,
        regime: str = "trimodal",
        gamma: float = 1.0,
        enable_events: bool = False,
    ) -> None:
        self.macro_config = macro_config or MacroFlowConfig(regime=regime)
        self.markov_config = markov_config or MarkovCirculationConfig()
        self.regime = regime
        self.gamma = gamma
        self.enable_events = enable_events

        self.markov_sim = MarkovCirculationSimulator(config=self.markov_config)
        self.macro_sim = MacroFlowSimulator(config=self.macro_config)

        self.node_names = self.markov_sim.node_names
        self.sensor_ids = self.markov_sim.sensor_ids
        self.poi_types = self.markov_sim.poi_types
        self.j_nodes = len(self.node_names)

    @staticmethod
    def format_hour(t_hours: float) -> str:
        """Formata hora fracionária contínua para HH:MM."""
        h = int(t_hours % 24)
        m = int(round((t_hours % 1.0) * 60))
        if m >= 60:
            h = (h + 1) % 24
            m = 0
        return f"{h:02d}:{m:02d}"

    def run_step(
        self,
        current_state_N: np.ndarray,
        t_hours: float,
        step_minutes: float = 30.0,
        step_index: int = 1,
    ) -> Tuple[np.ndarray, RolloutStep]:
        """
        Executa um único passo de simulação discreta.
        
        Args:
            current_state_N: Vetor (J,) com a população atual nos nós.
            t_hours: Horário contínuo em horas (ex: 8.5 para 08h30).
            step_minutes: Duração do ciclo Δt em minutos.
            step_index: Índice sequencial do passo.
            
        Returns:
            Tuple[np.ndarray, RolloutStep]: Novo vetor de estado N(t+1) e metadados detalhados do passo.
        """
        h = calculate_circadian_hour(t_hours)
        dt = float(step_minutes)

        # 1. Doc 01: Taxa de Influxo de Novos Ingressos nos Portões
        macro_res = calculate_macro_flow(
            current_time_hours=t_hours,
            gamma_seasonality=self.gamma,
            config=self.macro_config,
            step_minutes=dt,
            use_incremental=True,
            regime=self.regime,
        )
        delta_inflow_raw = np.array(
            macro_res.delta_N_rotina if macro_res.delta_N_rotina else macro_res.vector_delta_N_rotina,
            dtype=np.float64,
        )
        if len(delta_inflow_raw) < self.j_nodes:
            delta_inflow = np.pad(delta_inflow_raw, (0, self.j_nodes - len(delta_inflow_raw)), "constant")
        else:
            delta_inflow = delta_inflow_raw[:self.j_nodes]

        # 2. Doc 02: Pulsos de Eventos Culturais (Opcional)
        events_vec = np.zeros(self.j_nodes, dtype=np.float64)
        if self.enable_events:
            caps = [node.max_capacity for node in self.markov_config.nodes]
            raw_e = calculate_events_injection(current_time_hours=t_hours, node_capacities=caps)
            if len(raw_e) < self.j_nodes:
                events_vec = np.pad(raw_e, (0, self.j_nodes - len(raw_e)), "constant")
            else:
                events_vec = np.array(raw_e[:self.j_nodes], dtype=np.float64)

        # 3. Doc 03: Matriz de Markov & Egress (Saída Natural dos Portões)
        markov_res = self.markov_sim.propagate(
            current_state_N=current_state_N,
            t_hours=t_hours,
            gamma=self.gamma,
            step_minutes=dt,
            enable_egress=True,
            use_inertia=True,
            include_raw_flow=False,
        )

        n_propagated = np.array(markov_res.vector_N_propagado, dtype=np.float64)
        n_egress = np.array(markov_res.vector_N_egress, dtype=np.float64)

        # 4. Atualização de Estado:
        # Base circulante que se redistribui no tempo: N_base(t+1) = N_propagado + Influxo
        new_state_base = np.maximum(0.0, n_propagated + delta_inflow)

        # Lotação total observada no nó no instante t: inclui a presença do evento (Doc 02)
        total_occupancy_N = np.maximum(0.0, new_state_base + events_vec)

        # Metadados por nó formatados estritamente como inteiros (sem frações estranhas na UI)
        inflow_dict = {}
        egress_dict = {}
        occupancy_dict = {}
        for idx, name in enumerate(self.node_names):
            occupancy_dict[name] = float(int(round(total_occupancy_N[idx])))
            if self.poi_types[idx].upper() == "GATE":
                inflow_dict[name] = float(int(round(delta_inflow[idx])))
                egress_dict[name] = float(int(round(n_egress[idx])))

        tot_pop = float(int(round(np.sum(total_occupancy_N))))
        tot_in = float(int(round(np.sum(delta_inflow))))
        tot_out = float(int(round(np.sum(n_egress))))
        net_flux = tot_in - tot_out

        step_info = RolloutStep(
            step_index=step_index,
            time_hours=t_hours,
            hour_formatted=self.format_hour(t_hours),
            total_population=tot_pop,
            total_inflow=tot_in,
            total_egress=tot_out,
            net_flux=net_flux,
            state_N=[float(int(round(v))) for v in total_occupancy_N],
            node_names=self.node_names,
            poi_types=self.poi_types,
            inflow_by_gate=inflow_dict,
            egress_by_gate=egress_dict,
            occupancy_by_node=occupancy_dict,
        )

        return new_state_base, step_info

    def run_batch(
        self,
        start_hour: float = 0.0,
        end_hour: float = 24.0,
        step_minutes: float = 30.0,
        initial_population: Optional[Sequence[float]] = None,
    ) -> RolloutSummary:
        """
        Executa a simulação completa de 24 horas em lote (Batch instantâneo).
        """
        dt_hours = step_minutes / 60.0
        total_steps = int(math.ceil((end_hour - start_hour) / dt_hours))

        # Estado inicial (se omitido, madrugada vazia com piso basal distribuído)
        if initial_population is not None:
            current_N = np.array(initial_population, dtype=np.float64)
        else:
            base_macro = calculate_macro_flow(
                current_time_hours=start_hour,
                gamma_seasonality=self.gamma,
                config=self.macro_config,
                regime=self.regime,
            )
            raw_v = base_macro.vector_N_rotina
            if len(raw_v) < self.j_nodes:
                current_N = np.pad(raw_v, (0, self.j_nodes - len(raw_v)), "constant")
            else:
                current_N = np.array(raw_v[:self.j_nodes], dtype=np.float64)

        steps: List[RolloutStep] = []
        cum_in = 0.0
        cum_out = 0.0
        peak_pop = -1.0
        peak_t = start_hour

        for s_idx in range(1, total_steps + 1):
            t_curr = start_hour + (s_idx - 1) * dt_hours
            current_N, step_data = self.run_step(
                current_state_N=current_N,
                t_hours=t_curr,
                step_minutes=step_minutes,
                step_index=s_idx,
            )
            steps.append(step_data)
            cum_in += step_data.total_inflow
            cum_out += step_data.total_egress

            if step_data.total_population > peak_pop:
                peak_pop = step_data.total_population
                peak_t = t_curr

        final_pop = float(np.sum(current_N))

        return RolloutSummary(
            total_steps=total_steps,
            step_minutes=step_minutes,
            cumulative_inflow=cum_in,
            cumulative_egress=cum_out,
            peak_population=peak_pop,
            peak_time_hours=peak_t,
            peak_time_formatted=self.format_hour(peak_t),
            final_population=final_pop,
            net_city_balance=cum_in - cum_out,
            regime=self.regime,
            steps=steps,
        )

    def run_live_generator(
        self,
        start_hour: float = 0.0,
        end_hour: float = 24.0,
        step_minutes: float = 30.0,
        delay_seconds: float = 2.0,
        initial_population: Optional[Sequence[float]] = None,
    ) -> Generator[RolloutStep, None, RolloutSummary]:
        """
        Executa a simulação passo a passo emitindo cada ciclo com um intervalo real de espera.
        Ideal para consumo interativo via terminal, SSE ou WebSockets.
        """
        dt_hours = step_minutes / 60.0
        total_steps = int(math.ceil((end_hour - start_hour) / dt_hours))

        if initial_population is not None:
            current_N = np.array(initial_population, dtype=np.float64)
        else:
            base_macro = calculate_macro_flow(
                current_time_hours=start_hour,
                gamma_seasonality=self.gamma,
                config=self.macro_config,
                regime=self.regime,
            )
            raw_v = base_macro.vector_N_rotina
            if len(raw_v) < self.j_nodes:
                current_N = np.pad(raw_v, (0, self.j_nodes - len(raw_v)), "constant")
            else:
                current_N = np.array(raw_v[:self.j_nodes], dtype=np.float64)

        steps: List[RolloutStep] = []
        cum_in = 0.0
        cum_out = 0.0
        peak_pop = -1.0
        peak_t = start_hour

        for s_idx in range(1, total_steps + 1):
            t_curr = start_hour + (s_idx - 1) * dt_hours
            current_N, step_data = self.run_step(
                current_state_N=current_N,
                t_hours=t_curr,
                step_minutes=step_minutes,
                step_index=s_idx,
            )
            steps.append(step_data)
            cum_in += step_data.total_inflow
            cum_out += step_data.total_egress

            if step_data.total_population > peak_pop:
                peak_pop = step_data.total_population
                peak_t = t_curr

            yield step_data

            if s_idx < total_steps and delay_seconds > 0.0:
                time.sleep(delay_seconds)

        final_pop = float(np.sum(current_N))

        return RolloutSummary(
            total_steps=total_steps,
            step_minutes=step_minutes,
            cumulative_inflow=cum_in,
            cumulative_egress=cum_out,
            peak_population=peak_pop,
            peak_time_hours=peak_t,
            peak_time_formatted=self.format_hour(peak_t),
            final_population=final_pop,
            net_city_balance=cum_in - cum_out,
            regime=self.regime,
            steps=steps,
        )
