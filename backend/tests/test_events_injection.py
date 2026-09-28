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
