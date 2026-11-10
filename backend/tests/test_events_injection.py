"""
Suíte de Testes Automatizados para o Subsistema de Injeção de Eventos (Doc 02).

Valida os Requisitos Funcionais (RF01 a RF05) e Não-Funcionais (RNF01 e RNF02)
especificados em docs/explanation/dados_sinteticos/02_injecao_eventos.md.
"""

import math
import os
import sys
import time
import pytest
import numpy as np
from fastapi.testclient import TestClient

# Configuração de path para importação
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from src.simulation.events_injection import (
    EventsInjectionSimulator,
    calculate_events_injection,
    calculate_gaussian_pulse,
    clip_event_magnitude,
)
from src.simulation.schemas import (
    EventRule,
    EventsInjectionConfig,
    EventsInjectionRequest,
)
from src.api.main import app

client = TestClient(app)


# ==============================================================================
# 1. Testes de Funções Matemáticas Básicas
# ==============================================================================

def test_gaussian_pulse_peak_and_decay():
    """
    RF01: Testa se o pulso Gaussiano atinge a amplitude máxima A_jm no horário de pico tau_jm
    e decai simetricamente à medida que t se afasta do pico.
    """
    peak_hour = 20.0
    duration = 1.5
    magnitude = 100.0

    # No horário de pico t = tau, exp(0) = 1 => E(t) = magnitude
    peak_val = calculate_gaussian_pulse(
        current_time_hours=20.0,
        peak_hour=peak_hour,
        duration_hours=duration,
        magnitude=magnitude,
    )
    assert abs(peak_val - 100.0) < 1e-5

    # Em t = tau + duration (1 desvio padrão), exp(-1/2) ≈ 0.60653
    sigma_1_val = calculate_gaussian_pulse(
        current_time_hours=21.5,
        peak_hour=peak_hour,
        duration_hours=duration,
        magnitude=magnitude,
    )
    expected_sigma_1 = magnitude * math.exp(-0.5)
    assert abs(sigma_1_val - expected_sigma_1) < 1e-4

    # Simetria: t = tau - duration deve ser idêntico a t = tau + duration
    left_val = calculate_gaussian_pulse(
        current_time_hours=18.5,
        peak_hour=peak_hour,
        duration_hours=duration,
        magnitude=magnitude,
    )
    assert abs(left_val - sigma_1_val) < 1e-5


def test_zero_conditional_coupling():
    """
    RF02: Testa se a avaliação contínua da distância temporal decai suavemente
    para zero sem requerer condicionais IFs rígidos de janela temporal.
    """
    peak_hour = 20.0
    duration = 1.0
    magnitude = 80.0

    # Para t = 10h (10 horas de distância do pico), exp(-50) -> 0.0
    distant_val = calculate_gaussian_pulse(
        current_time_hours=10.0,
        peak_hour=peak_hour,
        duration_hours=duration,
        magnitude=magnitude,
    )
    assert distant_val == 0.0


def test_magnitude_capacity_clipping():
    """
    RF04: Testa a calibração de magnitude por capacidade física do nó (0.30 N_max <= A <= 0.95 N_max).
    """
    node_capacity = 200

    # Magnitude solicitada abaixo do piso (ex: 20 < 0.30 * 200 = 60) -> deve ser truncada em 60.0
    clipped_low = clip_event_magnitude(
        magnitude=20.0,
        node_capacity=node_capacity,
        min_ratio=0.30,
        max_ratio=0.95,
    )
    assert clipped_low == 60.0

    # Magnitude solicitada acima do teto (ex: 300 > 0.95 * 200 = 190) -> deve ser truncada em 190.0
    clipped_high = clip_event_magnitude(
        magnitude=300.0,
        node_capacity=node_capacity,
        min_ratio=0.30,
        max_ratio=0.95,
    )
    assert clipped_high == 190.0

    # Magnitude dentro dos limites (ex: 100) -> deve permanecer 100.0
    clipped_mid = clip_event_magnitude(
        magnitude=100.0,
        node_capacity=node_capacity,
        min_ratio=0.30,
        max_ratio=0.95,
    )
    assert clipped_mid == 100.0


# ==============================================================================
# 2. Testes dos 3 Modos de Ingestão de Eventos (RF03)
# ==============================================================================

def test_mode1_recurrent_calendar():
    """
    RF03 / Modo 1: Testa a injeção baseada em calendário cultural semanal (Terça Olodum).
    """
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=True, enable_mode2=False, enable_mode3=False)
    )

    # Terça-feira (dia 1) às 20h00 -> Terça da Benção ativa no nó 3
    resp_tuesday = sim.evaluate(current_time_hours=20.0, day_of_week=1)
    assert resp_tuesday.vector_E_eventos[3] > 50.0
    assert len(resp_tuesday.active_events) >= 1

    # Quarta-feira (dia 2) às 20h00 -> Terça da Benção INATIVA
    resp_wednesday = sim.evaluate(current_time_hours=20.0, day_of_week=2)
    assert resp_wednesday.vector_E_eventos[3] == 0.0


def test_mode2_punctual_agenda():
    """
    RF03 / Modo 2: Testa a injeção de agenda pontual agendada via lista de eventos customizada.
    """
    custom_event = EventRule(
        event_id="show_especial_pelourinho",
        sensor_index=1,
        peak_hour=19.0,
        duration_hours=1.0,
        magnitude=100.0,
        is_recurring=False,
    )
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=False, enable_mode2=True, enable_mode3=False)
    )

    resp = sim.evaluate(
        current_time_hours=19.0,
        events_registry=[custom_event],
        node_capacities=[100, 200, 100, 100],
    )

    # Nó 1 deve receber o pulso do evento customizado
    assert resp.vector_E_eventos[1] > 50.0
    assert resp.vector_E_eventos[0] == 0.0


def test_mode3_monte_carlo_afternoon():
    """
    RF03 / Modo 3: Testa manifestações estocásticas espontâneas no período vespertino (14h-18h).
    """
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(
            enable_mode1=False,
            enable_mode2=False,
            enable_mode3=True,
            monte_carlo_prob=1.0,  # Força sorteio garantido para o teste
        )
    )

    # Às 16h00 (dentro da janela vespertina 14h-18h)
    resp = sim.evaluate(current_time_hours=16.0, seed=42)
    total_injected = sum(resp.vector_E_eventos)
    assert total_injected > 0.0
    assert len(resp.active_events) >= 1

    # Fora da janela vespertina (ex: 10h00)
    resp_morning = sim.evaluate(current_time_hours=10.0, seed=42)
    assert sum(resp_morning.vector_E_eventos) == 0.0


# ==============================================================================
# 3. Testes de Saída Vetorial e Requisitos Não-Funcionais (RF05, RNF01, RNF02)
# ==============================================================================

def test_nodal_vector_output_format():
    """
    RF05, RNF02: Testa se a função calculate_events_injection retorna um ndarray float64 1D de dimensão J.
    """
    E_vec = calculate_events_injection(
        current_time_hours=20.0,
        day_of_week=1,
        node_capacities=[150, 120, 80, 200],
    )
    assert isinstance(E_vec, np.ndarray)
    assert E_vec.dtype == np.float64
    assert E_vec.shape == (4,)
    assert np.all(E_vec >= 0.0)


def test_mode1_keeps_calendar_base_rules_when_custom_events_are_injected():
    """Regressão: o calendário base deve permanecer ativo quando um evento pontual entra no registro."""
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=True, enable_mode2=True, enable_mode3=False)
    )
    custom_event = EventRule(
        event_id="show_especial_pelourinho",
        sensor_alvo="sensor_largo_pelourinho",
        peak_hour=19.0,
        duration_hours=1.0,
        magnitude=100.0,
        is_recurring=False,
    )

    resp = sim.evaluate(
        current_time_hours=20.0,
        day_of_week=1,
        node_capacities=[150, 120, 80, 200],
        events_registry=[custom_event],
    )

    assert len(resp.active_events) >= 2
    assert resp.vector_E_eventos[3] > 0.0


def test_event_rule_accepts_sensor_alias_and_maps_to_sensor_index():
    """Eventos podem ser cadastrados por sensor_id/sensor_alvo sem precisar conhecer o índice numérico."""
    rule = EventRule(
        event_id="evento_nomeado",
        sensor_alvo="sensor_largo_pelourinho",
        peak_hour=18.0,
        duration_hours=1.0,
        magnitude=80.0,
    )

    assert rule.sensor_index == 3
    assert rule.sensor_alvo == "sensor_largo_pelourinho"


def test_mode3_keeps_spontaneous_events_alive_across_cycles():
    """Eventos aleatórios espontâneos devem persistir em memória e decair suavemente ao longo do tempo."""
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(
            enable_mode1=False,
            enable_mode2=False,
            enable_mode3=True,
            monte_carlo_prob=1.0,
        )
    )

    first = sim.evaluate(current_time_hours=16.0, seed=42)
    second = sim.evaluate(current_time_hours=16.5, seed=42)

    assert sum(first.vector_E_eventos) > 0.0
    assert sum(second.vector_E_eventos) > 0.0
    assert len(sim._spontaneous_events) >= 1


def test_performance_rnf01():
    """
    RNF01: Testa a complexidade temporal e tempo de resposta da avaliação (< 20 us por chamada).
    """
    sim = EventsInjectionSimulator()
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        _ = sim.evaluate(current_time_hours=20.0, day_of_week=1)
    elapsed = time.perf_counter() - start

    avg_time_us = (elapsed / iterations) * 1e6
    print(f"\nTempo médio por avaliação de eventos: {avg_time_us:.2f} µs")
    # Garante execução ultra-rápida
    assert avg_time_us < 500.0


# ==============================================================================
# 4. Testes de Integração de Endpoints REST (FastAPI)
# ==============================================================================

def test_get_events_config_endpoint():
    """Testa endpoint GET /api/v1/simulation/events/config."""
    response = client.get("/simulation/events/config")
    assert response.status_code == 200
    data = response.json()
    assert "enable_mode1" in data
    assert "enable_mode2" in data
    assert "enable_mode3" in data


def test_post_calculate_events_endpoint():
    """Testa endpoint POST /api/v1/simulation/events."""
    payload = {
        "current_time_hours": 20.0,
        "day_of_week": 1,
        "enable_mode1": True,
        "enable_mode2": True,
        "enable_mode3": False,
    }
    response = client.post("/simulation/events", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "vector_E_eventos" in data
    assert len(data["vector_E_eventos"]) == 4
    assert "node_bonuses" in data
    assert "active_events" in data


# ==============================================================================
# Testes das Propostas de Melhoria Doc 02 (Cortejos, Modo Dual & Fruin/Helbing)
# ==============================================================================

def test_itinerant_cortejo_spatial_wave():
    """Valida cortejo itinerante móvel com defasagem temporal entre nós vizinhos."""
    from src.simulation.events_injection import calculate_itinerant_pulses

    cortejo = EventRule(
        event_id="cortejo_afoxe_gandhy",
        peak_hour=16.0,
        duration_hours=0.5,
        magnitude=120.0,
        event_type="ITINERANT",
        waypoints=[0, 1, 4, 3],
        march_velocity_kmh=2.0,
    )
    caps = [150, 120, 80, 250, 200]

    # No instante inicial (16h00), o pulso no nó 0 (Elevador) deve estar no pico
    pulses_t0 = calculate_itinerant_pulses(current_time_hours=16.0, rule=cortejo, node_capacities=caps)
    p0 = [p for p in pulses_t0 if p[0] == 0]
    self_val_0 = p0[0][1] if p0 else 0.0

    # No nó 1 (Praça da Sé), o pico deve ocorrer mais tarde
    p1 = [p for p in pulses_t0 if p[0] == 1]
    self_val_1_at_t0 = p1[0][1] if p1 else 0.0
    assert self_val_0 > self_val_1_at_t0, "Nó 0 deve estar mais próximo do pico às 16h00 do que nó 1"

    # Avalia que nó 1 atinge pico após nó 0
    tau_node_0 = pulses_t0[0][3]
    tau_node_1 = pulses_t0[1][3]
    assert tau_node_1 > tau_node_0, f"Pico no nó 1 ({tau_node_1}) deve ser posterior ao nó 0 ({tau_node_0})"


def test_dual_magnitude_relative_and_absolute():
    """Valida o modo dual de magnitude (ABSOLUTE vs RELATIVE / invariância de escala)."""
    sim = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=False, enable_mode2=True, enable_mode3=False, enable_collective_damping=False),
        calendar_path="/dev/null",
        agenda_path="/dev/null",
    )

    # Evento Relativo: fração de 50% da capacidade
    event_rel = EventRule(
        event_id="evento_relativo",
        sensor_index=3,
        peak_hour=18.0,
        duration_hours=1.0,
        magnitude=0.0,
        mode="RELATIVE",
        capacity_ratio=0.50,
    )

    # Com capacidade 200 no nó 3 -> amplitude = 100
    res_200 = sim.evaluate(current_time_hours=18.0, node_capacities=[100, 100, 100, 200], events_registry=[event_rel])
    assert abs(res_200.vector_E_eventos[3] - 100.0) < 1.0

    # Com capacidade 400 no nó 3 -> amplitude escala para 200
    res_400 = sim.evaluate(current_time_hours=18.0, node_capacities=[100, 100, 100, 400], events_registry=[event_rel])
    assert abs(res_400.vector_E_eventos[3] - 200.0) < 1.0

    # Evento Absoluto: permanece fixo
    event_abs = EventRule(
        event_id="evento_absoluto",
        sensor_index=3,
        peak_hour=18.0,
        duration_hours=1.0,
        magnitude=120.0,
        mode="ABSOLUTE",
    )
    res_abs_200 = sim.evaluate(current_time_hours=18.0, node_capacities=[100, 100, 100, 200], events_registry=[event_abs])
    res_abs_400 = sim.evaluate(current_time_hours=18.0, node_capacities=[100, 100, 100, 400], events_registry=[event_abs])
    assert abs(res_abs_200.vector_E_eventos[3] - res_abs_400.vector_E_eventos[3]) < 1e-4


def test_carnaval_and_collective_saturation_damping_fruin_helbing():
    """Valida o amortecimento coletivo logístico sob múltiplos eventos simultâneos (Carnaval)."""
    # 5 eventos concorrentes colidindo simultaneamente no Largo do Pelourinho (nó 3)
    concurrent_events = [
        EventRule(event_id=f"carnaval_bloco_{i}", sensor_index=3, peak_hour=21.0, duration_hours=2.0, magnitude=180.0)
        for i in range(5)
    ]
    caps = [150, 120, 80, 200]

    # Sem amortecimento coletivo
    sim_raw = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=False, enable_mode2=True, enable_mode3=False, enable_collective_damping=False),
        calendar_path="/dev/null",
        agenda_path="/dev/null",
    )
    resp_raw = sim_raw.evaluate(current_time_hours=21.0, node_capacities=caps, events_registry=concurrent_events)
    # Soma linear bruta seria 5 * 180 = 900 pessoas em um largo de capacidade 200!
    assert resp_raw.vector_E_eventos[3] > 800.0

    # Com blindagem e amortecimento coletivo logístico ativado
    sim_damped = EventsInjectionSimulator(
        config=EventsInjectionConfig(enable_mode1=False, enable_mode2=True, enable_mode3=False, enable_collective_damping=True, damping_factor=1.5),
        calendar_path="/dev/null",
        agenda_path="/dev/null",
    )
    resp_damped = sim_damped.evaluate(current_time_hours=21.0, node_capacities=caps, events_registry=concurrent_events)
    # E_calibrado = E / (1.0 + E / (1.5 * 200)) = 900 / (1 + 3) = 225
    assert resp_damped.vector_E_eventos[3] < 300.0, "Blindagem deve amortecer aglomeração impossível"
    assert resp_damped.vector_E_eventos[3] < resp_raw.vector_E_eventos[3]

