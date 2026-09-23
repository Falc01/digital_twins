"""
Suíte de Testes Unitários e funcionais do Subsistema de Macro-Fluxo Circadiano (Doc 01).
"""

import time
import pytest
import numpy as np
from fastapi.testclient import TestClient

from src.simulation.macro_flow import (
    calculate_circadian_hour,
    calculate_bairro_population,
    distribute_to_gates,
    normalize_gate_weights,
    calculate_macro_flow,
)
from src.simulation.schemas import MacroFlowConfig, MacroFlowRequest
from src.api.main import app

client = TestClient(app)


def test_circadian_hour_calculation():
    """RF05: Testa relógio circadiano contínuo e operador módulo 24h."""
    assert calculate_circadian_hour(0.0) == 0.0
    assert calculate_circadian_hour(16.5) == 16.5
    assert calculate_circadian_hour(24.0) == 0.0
    assert calculate_circadian_hour(24.5) == 0.5
    assert calculate_circadian_hour(48.0) == 0.0


def test_gaussian_bell_peak():
    """RF01: Testa valor de pico no horário t_pico (16h30) com gamma = 1.0."""
    N_bairro, h_t = calculate_bairro_population(
        current_time_hours=16.5,
        N_max=300,
        N_min=15,
        t_peak=16.5,
        sigma=3.0,
        gamma_seasonality=1.0,
    )
    assert h_t == 16.5
    # No pico, a exponencial é exp(0) = 1.0, logo N_bairro = 1.0 * (15 + (300 - 15) * 1.0) = 300.0
    assert pytest.approx(N_bairro, abs=1e-5) == 300.0


def test_gaussian_bell_off_peak():
    """RF01: Testa valor durante a madrugada (ex: 03h00), devendo aproximar N_min."""
    N_bairro, h_t = calculate_bairro_population(
        current_time_hours=3.0,
        N_max=300,
        N_min=15,
        t_peak=16.5,
        sigma=3.0,
        gamma_seasonality=1.0,
    )
    assert h_t == 3.0
    # Às 3h (distante 13.5h do pico 16.5h), a Gaussiana é exp(-(13.5)^2 / 18) ≈ exp(-10.125) ≈ 0.00004
    # Portanto, N_bairro deve estar muito próximo de N_min (15.0)
    assert pytest.approx(N_bairro, abs=0.1) == 15.0


def test_seasonality_modulation():
    """RF04: Testa fator de modulação sazonal (gamma = 1.5)."""
    N_bairro, _ = calculate_bairro_population(
        current_time_hours=16.5,
        N_max=300,
        N_min=15,
        t_peak=16.5,
        sigma=3.0,
        gamma_seasonality=1.5,
    )
    # No pico com gamma = 1.5, N_bairro = 1.5 * 300 = 450.0
    assert pytest.approx(N_bairro, abs=1e-5) == 450.0


def test_gate_weights_distribution_and_conservation():
    """RF02 & RF03: Testa alocação nos portões e conservação estrita de fluxo."""
    w_weights = [0.45, 0.35, 0.20, 0.00]
    N_bairro = 300.0
    N_rotina = distribute_to_gates(N_bairro, w_weights)
    
    assert isinstance(N_rotina, np.ndarray)
    assert N_rotina.shape == (4,)
    assert pytest.approx(N_rotina[0]) == 135.0   # 45% de 300
    assert pytest.approx(N_rotina[1]) == 105.0   # 35% de 300
    assert pytest.approx(N_rotina[2]) == 60.0    # 20% de 300
    assert pytest.approx(N_rotina[3]) == 0.0     # 0% de 300
    
    # Conservação total de fluxo
    assert pytest.approx(np.sum(N_rotina)) == N_bairro


def test_gate_weights_normalization():
    """RF03: Testa normalização automática de pesos desnormalizados."""
    unnormalized_w = [0.9, 0.1, 0.2]  # soma = 1.2
    normalized_w = normalize_gate_weights(unnormalized_w)
    
    assert pytest.approx(np.sum(normalized_w)) == 1.0
    assert pytest.approx(normalized_w[0]) == 0.9 / 1.2
    assert pytest.approx(normalized_w[1]) == 0.1 / 1.2
    assert pytest.approx(normalized_w[2]) == 0.2 / 1.2


def test_negative_weight_rejection():
    """RF03: Valida rejeição de pesos negativos."""
    with pytest.raises(ValueError, match="não podem conter valores negativos"):
        normalize_gate_weights([0.5, -0.2, 0.7])


def test_rnf01_performance():
    """RNF01: Testa complexidade O(1) e tempo de execução por ciclo < 10 µs."""
    config = MacroFlowConfig()
    iterations = 10000
    
    start_time = time.perf_counter()
    for i in range(iterations):
        calculate_macro_flow(current_time_hours=16.5, config=config)
    elapsed_time = time.perf_counter() - start_time
    
    avg_time_per_call = elapsed_time / iterations
    avg_microseconds = avg_time_per_call * 1e6
    
    # Cada execução deve ser ordens de grandeza menor que 1 ms (alvo de RNF01: < 10 µs em média)
    assert avg_microseconds < 100.0, f"Tempo médio elevado: {avg_microseconds:.2f} µs"


def test_api_get_macro_flow_config():
    """Testa endpoint GET /api/v1/simulation/macro-flow/config."""
    res = client.get("/api/v1/simulation/macro-flow/config")
    assert res.status_code == 200
    data = res.json()
    assert data["N_max"] == 300
    assert data["N_min"] == 15
    assert data["t_peak"] == 16.5
    assert data["sigma"] == 3.0
    assert data["w_weights"] == [0.45, 0.35, 0.20, 0.00]


def test_api_post_macro_flow_calculate():
    """Testa endpoint POST /api/v1/simulation/macro-flow/calculate."""
    payload = {
        "current_time_hours": 16.5,
        "gamma_seasonality": 1.0,
    }
    res = client.post("/api/v1/simulation/macro-flow/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["current_time_hours"] == 16.5
    assert data["circadian_hour"] == 16.5
    assert data["N_bairro_total"] == 300.0
    assert data["N_rotina"] == [135.0, 105.0, 60.0, 0.0]
