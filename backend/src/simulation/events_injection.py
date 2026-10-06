"""
Motor Matemático para Injeção Dinâmica de Eventos e Padrões Culturais (Doc 02).

Calcula o vetor nodal E(t) em R^J de acréscimo pontual de público gerado por
atrações culturais, celebrações agendadas e manifestações espontâneas no Pelourinho,
sem dependência de datasets históricos prévios.

Classificação: Container de API / Subsistema de Eventos (Doc 02)
Complexidade Temporal: O(M) onde M é o número de eventos ativos (< 20 us)
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from src.simulation.schemas import (
    EventNodeBonus,
    EventRule,
    EventsInjectionConfig,
    EventsInjectionRequest,
    EventsInjectionResponse,
)

logger = logging.getLogger("simulation.events_injection")

# Caminhos padrão para arquivos de configuração JSON de eventos (Modo 1 e Modo 2)
DEFAULT_CALENDAR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "shared", "calendario_cultural.json"
)
DEFAULT_AGENDA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "shared", "agenda_eventos.json"
)


def calculate_gaussian_pulse(
    current_time_hours: float,
    peak_hour: float,
    duration_hours: float,
    magnitude: float,
) -> float:
    """
    Calcula a contribuição de um pulso Gaussiano individual no tempo t (RF01, RF02).

    Fórmula: E_jm(t) = A_jm * exp( - (t - tau_jm)^2 / (2 * sigma_jm^2) )

    Args:
        current_time_hours (float): Horário contínuo t em horas.
        peak_hour (float): Horário de pico tau_jm em horas fracionárias.
        duration_hours (float): Dispersão temporal sigma_jm em horas.
        magnitude (float): Amplitude A_jm em número de indivíduos.

    Returns:
        float: Volume de público injetado pelo pulso no instante t.
    """
    if duration_hours <= 0.0 or magnitude <= 0.0:
        return 0.0

    delta_t = current_time_hours - peak_hour
    exponent = -(delta_t * delta_t) / (2.0 * duration_hours * duration_hours)

    if exponent < -40.0:
        return 0.0

    return float(magnitude * math.exp(exponent))



def clip_event_magnitude(
    magnitude: float,
    node_capacity: int,
    min_ratio: float = 0.30,
    max_ratio: float = 0.95,
) -> float:
    """
    Aplica a calibração de magnitude por capacidade física do nó (RF04, Section 3.3).

    Fórmula: A_jm = clip(A_jm, min_ratio * N_j_max, max_ratio * N_j_max)

    Args:
        magnitude (float): Amplitude bruta desejada A_jm.
        node_capacity (int): Capacidade máxima física N_j_max do nó.
        min_ratio (float): Piso mínimo de proporcionalidade (default 0.30).
        max_ratio (float): Teto máximo de proporcionalidade (default 0.95).

    Returns:
        float: Amplitude A_jm calibrada dentro dos limites físicos do logradouro.
    """
    if node_capacity <= 0:
        return max(0.0, magnitude)

    min_cap = min_ratio * node_capacity
    max_cap = max_ratio * node_capacity

    return float(np.clip(magnitude, min_cap, max_cap))


class EventsInjectionSimulator:
    """
    Simulador de Injeção Dinâmica de Eventos e Padrões Culturais (Doc 02).

    Suporta os 3 Modos de Ingestão:
      - Modo 1: Calendário Cultural Fixo (Recorrente por dia da semana)
      - Modo 2: Agenda Externa Pontual (Tabela/JSON de eventos agendados)
      - Modo 3: Monte Carlo Estocástico Espontâneo (Sorteio probabilístico p=0.15 à tarde)
    """

    def __init__(
        self,
        config: Optional[EventsInjectionConfig] = None,
        default_node_capacities: Optional[List[int]] = None,
        calendar_path: str = DEFAULT_CALENDAR_PATH,
        agenda_path: str = DEFAULT_AGENDA_PATH,
    ) -> None:
        """
        Inicializa o simulador de eventos com configurações e tabelas padrão.
        """
        self.config = config or EventsInjectionConfig()
        self.calendar_path = calendar_path
        self.agenda_path = agenda_path

        # Capacidades padrão de nós caso Canal A não seja fornecido (J = 4 por padrão)
        # Index 0: Elevador Lacerda (150)
        # Index 1: Praça da Sé (120)
        # Index 2: Ladeira do Carmo / Rosário (80)
        # Index 3: Largo do Pelourinho (200)
        self.default_node_capacities = (
            default_node_capacities
            if default_node_capacities is not None
            else [150, 120, 80, 200]
        )

        self._calendar_rules: List[EventRule] = self._load_calendar_rules()
        self._agenda_events: List[EventRule] = self._load_agenda_events()
        self._spontaneous_events: List[Dict[str, Any]] = []

    def _load_calendar_rules(self) -> List[EventRule]:
        """Carrega regras do Modo 1 (Calendário Cultural Fixo) de arquivo JSON se existir."""
        rules = []
        if os.path.exists(self.calendar_path):
            try:
                with open(self.calendar_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        item["is_recurring"] = True
                        rules.append(EventRule.model_validate(item))
            except Exception as e:
                logger.warning(f"Não foi possível carregar {self.calendar_path}: {e}")
        return rules

    def _load_agenda_events(self) -> List[EventRule]:
        """Carrega eventos do Modo 2 (Agenda Externa Pontual) de arquivo JSON se existir."""
        events = []
        if os.path.exists(self.agenda_path):
            try:
                with open(self.agenda_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        item["is_recurring"] = False
                        events.append(EventRule.model_validate(item))
            except Exception as e:
                logger.warning(f"Não foi possível carregar {self.agenda_path}: {e}")
        return events

    def evaluate(
        self,
        current_time_hours: Optional[float] = None,
        day_of_week: Optional[int] = None,
        node_capacities: Optional[List[int]] = None,
        events_registry: Optional[List[EventRule]] = None,
        seed: Optional[int] = None,
    ) -> EventsInjectionResponse:
        """
        Executa o cálculo vetorial de injeção de eventos E(t) em R^J (RF01 - RF05).

        Args:
            current_time_hours (float, opcional): Hora contínua t em [0, 24).
            day_of_week (int, opcional): Dia da semana 0..6.
            node_capacities (List[int], opcional): Vetor de capacidade N_j_max.
            events_registry (List[EventRule], opcional): Lista customizada de eventos.
            seed (int, opcional): Semente aleatória para reprodutibilidade no Modo 3.

        Returns:
            EventsInjectionResponse: Payload contendo vetor E(t), nó a nó, e eventos ativos.
        """
        now = datetime.now()
        if current_time_hours is None:
            current_time_hours = now.hour + (now.minute / 60.0) + (now.second / 3600.0)

        t_hours = float(current_time_hours % 24.0)

        if day_of_week is None:
            day_of_week = now.weekday()

        caps = (
            np.array(node_capacities, dtype=np.int32)
            if node_capacities is not None
            else np.array(self.default_node_capacities, dtype=np.int32)
        )
        J = len(caps)

        # RNF02: Vetorização e Memória - Array NumPy float64 pré-alocado
        vector_E = np.zeros(J, dtype=np.float64)
        active_events_list: List[Dict[str, Any]] = []
        node_active_counts = np.zeros(J, dtype=np.int32)

        # ======================================================================
        # MODO 1: Calendário Cultural Fixo (Recorrente por Dia da Semana)
        # ======================================================================
        if self.config.enable_mode1:
            base_rules = list(self._calendar_rules)
            if events_registry is not None:
                base_rules.extend(
                    [e for e in events_registry if e.is_recurring or e.day_of_week is not None]
                )
            for rule in base_rules:
                if rule.day_of_week is not None and rule.day_of_week != day_of_week:
                    continue

                j = int(rule.sensor_index)
                if 0 <= j < J:
                    calibrated_A = clip_event_magnitude(
                        magnitude=rule.magnitude,
                        node_capacity=caps[j],
                        min_ratio=self.config.min_capacity_ratio,
                        max_ratio=self.config.max_capacity_ratio,
                    )
                    pulse = calculate_gaussian_pulse(
                        current_time_hours=t_hours,
                        peak_hour=rule.peak_hour,
                        duration_hours=rule.duration_hours,
                        magnitude=calibrated_A,
                    )
                    if pulse > 0.001:
                        vector_E[j] += pulse
                        node_active_counts[j] += 1
                        active_events_list.append(
                            {
                                "mode": "Mode 1 (Calendar)",
                                "event_id": rule.event_id,
                                "sensor_index": j,
                                "pulse_value": round(pulse, 4),
                                "calibrated_magnitude": round(calibrated_A, 2),
                                "peak_hour": rule.peak_hour,
                                "duration_hours": rule.duration_hours,
                            }
                        )

        # ======================================================================
        # MODO 2: Agenda de Eventos Pontuais (JSON / GeoPackage)
        # ======================================================================
        if self.config.enable_mode2:
            base_agenda = list(self._agenda_events)
            if events_registry is not None:
                base_agenda.extend(
                    [e for e in events_registry if (not e.is_recurring) and (e.day_of_week is None)]
                )
            for event in base_agenda:
                j = int(event.sensor_index)
                if 0 <= j < J:
                    calibrated_A = clip_event_magnitude(
                        magnitude=event.magnitude,
                        node_capacity=caps[j],
                        min_ratio=self.config.min_capacity_ratio,
                        max_ratio=self.config.max_capacity_ratio,
                    )
                    pulse = calculate_gaussian_pulse(
                        current_time_hours=t_hours,
                        peak_hour=event.peak_hour,
                        duration_hours=event.duration_hours,
                        magnitude=calibrated_A,
                    )
                    if pulse > 0.001:
                        vector_E[j] += pulse
                        node_active_counts[j] += 1
                        active_events_list.append(
                            {
                                "mode": "Mode 2 (Agenda)",
                                "event_id": event.event_id,
                                "sensor_index": j,
                                "pulse_value": round(pulse, 4),
                                "calibrated_magnitude": round(calibrated_A, 2),
                                "peak_hour": event.peak_hour,
                                "duration_hours": event.duration_hours,
                            }
                        )

        # ======================================================================
        # MODO 3: Monte Carlo Estocástico Espontâneo (Pelourinho Afternoon)
        # ======================================================================
        self._spontaneous_events = [
            event for event in self._spontaneous_events
            if abs(t_hours - event["peak_hour"]) <= 3.0 * event["duration_hours"]
        ]

        for spontaneous_event in self._spontaneous_events:
            target_j = int(spontaneous_event["sensor_index"])
            if 0 <= target_j < J:
                pulse = calculate_gaussian_pulse(
                    current_time_hours=t_hours,
                    peak_hour=spontaneous_event["peak_hour"],
                    duration_hours=spontaneous_event["duration_hours"],
                    magnitude=spontaneous_event["magnitude"],
                )
                if pulse > 0.001:
                    vector_E[target_j] += pulse
                    node_active_counts[target_j] += 1
                    active_events_list.append(
                        {
                            "mode": "Mode 3 (Monte Carlo)",
                            "event_id": spontaneous_event["event_id"],
                            "sensor_index": target_j,
                            "pulse_value": round(pulse, 4),
                            "calibrated_magnitude": round(spontaneous_event["magnitude"], 2),
                            "peak_hour": spontaneous_event["peak_hour"],
                            "duration_hours": spontaneous_event["duration_hours"],
                        }
                    )

        if self.config.enable_mode3 and (14.0 <= t_hours <= 18.0):
            active_now = any(
                abs(t_hours - event["peak_hour"]) <= 3.0 * event["duration_hours"]
                for event in self._spontaneous_events
            )
            if not active_now:
                rng = np.random.default_rng(seed)
                u = rng.random()
                if u <= self.config.monte_carlo_prob:
                    target_j = int(rng.integers(0, J))
                    raw_A = float(rng.normal(35.0, 10.0))
                    duration = float(rng.uniform(0.5, 1.2))

                    calibrated_A = clip_event_magnitude(
                        magnitude=max(5.0, raw_A),
                        node_capacity=caps[target_j],
                        min_ratio=self.config.min_capacity_ratio,
                        max_ratio=self.config.max_capacity_ratio,
                    )
                    event = {
                        "event_id": f"mc_spontaneous_node_{target_j}_{len(self._spontaneous_events)}",
                        "sensor_index": target_j,
                        "peak_hour": t_hours,
                        "duration_hours": duration,
                        "magnitude": calibrated_A,
                    }
                    self._spontaneous_events.append(event)

                    pulse = calculate_gaussian_pulse(
                        current_time_hours=t_hours,
                        peak_hour=t_hours,
                        duration_hours=duration,
                        magnitude=calibrated_A,
                    )
                    if pulse > 0.001:
                        vector_E[target_j] += pulse
                        node_active_counts[target_j] += 1
                        active_events_list.append(
                            {
                                "mode": "Mode 3 (Monte Carlo)",
                                "event_id": event["event_id"],
                                "sensor_index": target_j,
                                "pulse_value": round(pulse, 4),
                                "calibrated_magnitude": round(calibrated_A, 2),
                                "peak_hour": t_hours,
                                "duration_hours": round(duration, 2),
                            }
                        )

        # Prepara bônus detalhado nó a nó
        node_bonuses = [
            EventNodeBonus(
                sensor_id=f"sensor_{j}",
                sensor_index=j,
                event_bonus=float(vector_E[j]),
                node_capacity=int(caps[j]),
                active_events_count=int(node_active_counts[j]),
            )
            for j in range(J)
        ]

        return EventsInjectionResponse(
            timestamp_iso=now.isoformat(),
            current_time_hours=t_hours,
            day_of_week=day_of_week,
            vector_E_eventos=[float(val) for val in vector_E],
            node_bonuses=node_bonuses,
            active_events=active_events_list,
        )


def calculate_events_injection(
    current_time_hours: Optional[float] = None,
    day_of_week: Optional[int] = None,
    node_capacities: Optional[List[int]] = None,
    events_registry: Optional[List[EventRule]] = None,
    enable_mode1: bool = True,
    enable_mode2: bool = True,
    enable_mode3: bool = True,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Função funcional de alto nível para obter diretamente o array NumPy float64 (Doc 02).

    Args:
        current_time_hours (float, opcional): Hora contínua t.
        day_of_week (int, opcional): Dia da semana 0..6.
        node_capacities (List[int], opcional): Capacidades dos nós J.
        events_registry (List[EventRule], opcional): Lista de eventos.
        enable_mode1 (bool): Ativar Calendário Cultural Fixo.
        enable_mode2 (bool): Ativar Agenda de Eventos Pontuais.
        enable_mode3 (bool): Ativar Monte Carlo Estocástico.
        seed (int, opcional): Semente aleatória.

    Returns:
        np.ndarray: Array 1D de shape (J,), dtype=np.float64 com o vetor E_eventos(t).
    """
    cfg = EventsInjectionConfig(
        enable_mode1=enable_mode1,
        enable_mode2=enable_mode2,
        enable_mode3=enable_mode3,
    )
    sim = EventsInjectionSimulator(config=cfg)
    resp = sim.evaluate(
        current_time_hours=current_time_hours,
        day_of_week=day_of_week,
        node_capacities=node_capacities,
        events_registry=events_registry,
        seed=seed,
    )
    return np.array(resp.vector_E_eventos, dtype=np.float64)
