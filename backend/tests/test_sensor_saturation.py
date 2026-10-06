"""
Bateria de Testes Unitários e de Integração para o Subsistema de Sensoriamento IoT (Doc 04).

Cobre exaustivamente:
- RF01: Integração de fluxos nodais N_bruto(t+1) = N_propagado + Delta N_rotina + E;
- RF02: Barreira logística de Richards, ancoragem em zero e teto intransponível;
- RF03: Os 3 métodos de ruído instrumental (Uniforme, Gaussiano, Ornstein-Uhlenbeck);
- RF04: Discretização, não-negatividade e limitador estrito [0, N_max] in N;
- RF05: Formatação de telemetria, regras de status e persistência no Datalake;
- RNF01: Latência analítica de sensoriamento < 1 ms;
- RNF02: Estabilidade e memória estática do processo estocástico;
- Endpoints REST da API FastAPI (incluindo rota direta para o Leaflet).
"""

import math
import tempfile
import time
from typing import List

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.simulation.sensor_saturation import (
    SensorSaturationSimulator,
    calculate_richards_saturation,
    generate_sensor_noise,
    clip_and_discretize_sensor_readings,
    determine_sensor_status,
    simulate_sensor_telemetry,
)
from src.simulation.schemas import (
    RichardsSaturationConfig,
    SensorNoiseConfig,
    SensorNoiseType,
    SensorNodeMetadata,
    SensorSaturationConfig,
    SensorSaturationRequest,
    SensorTelemetryResponse,
)
from src.dyntable.logic.table_manager import TableManager

client = TestClient(app)


# ==============================================================================
# 1. Testes de Integração de Fluxos Físicos Nodal (RF01)
# ==============================================================================

def test_rf01_nodal_vector_sum_integration():
    """RF01: N_bruto(t+1) deve ser a soma exata elemento a elemento dos 3 fluxos físicos."""
    sim = SensorSaturationSimulator()

    prop = [30.0, 40.0, 20.0, 50.0, 10.0]
    rotina = [15.0, 10.0, 5.0, 0.0, 0.0]
    eventos = [0.0, 0.0, 0.0, 100.0, 50.0]

    resp = sim.evaluate(
        N_propagado=prop,
        delta_N_rotina=rotina,
        vector_E_eventos=eventos,
        noise_method="NONE",
    )

    expected_bruto = [45.0, 50.0, 25.0, 150.0, 60.0]
    assert np.allclose(resp.vector_N_bruto, expected_bruto, atol=1e-2)


def test_rf01_explicit_raw_flow_override():
    """RF01: Quando N_bruto é fornecido diretamente, ele deve prevalecer sem recompor os canais."""
    sim = SensorSaturationSimulator()
    custom_bruto = [100.0, 80.0, 60.0, 200.0, 150.0]

    resp = sim.evaluate(N_bruto=custom_bruto, noise_method="NONE")
    assert np.allclose(resp.vector_N_bruto, custom_bruto, atol=1e-2)


# ==============================================================================
# 2. Testes da Barreira Logística de Richards (RF02)
# ==============================================================================

def test_rf02_richards_zero_anchoring():
    """RF02: Com ancoragem em zero ativa, N_bruto = 0 deve resultar estritamente em S = 0.0."""
    n_zero = np.zeros(5, dtype=np.float64)
    n_max = np.array([150.0, 120.0, 80.0, 250.0, 200.0], dtype=np.float64)

    s_anchored = calculate_richards_saturation(
        N_bruto=n_zero,
        N_max=n_max,
        kappa=0.08,
        zero_anchored=True,
    )
    assert np.allclose(s_anchored, 0.0, atol=1e-6), "Ancoragem falhou: pedestres fantasmas em rua vazia!"

    # Sem ancoragem, a sigmoide clássica produz resíduo positivo S(0) > 0
    s_unanchored = calculate_richards_saturation(
        N_bruto=n_zero,
        N_max=n_max,
        kappa=0.08,
        zero_anchored=False,
    )
    assert np.all(s_unanchored > 0.0), "Curva não-ancorada deveria apresentar S(0) > 0"


def test_rf02_richards_asymptotic_ceiling():
    """RF02: Mesmo sob superlotação extrema (ex: 50.000 pessoas), S(N) nunca deve ultrapassar N_max."""
    n_extreme = np.array([50000.0, 80000.0, 25000.0, 99999.0, 45000.0], dtype=np.float64)
    n_max = np.array([150.0, 120.0, 80.0, 250.0, 200.0], dtype=np.float64)

    s_extreme = calculate_richards_saturation(
        N_bruto=n_extreme,
        N_max=n_max,
        kappa=0.08,
        zero_anchored=True,
    )

    # Todos os valores devem estar limitados pelo teto máximo de cada nó
    assert np.all(s_extreme <= n_max + 1e-6)
    assert np.allclose(s_extreme, n_max, atol=1e-3)


def test_rf02_richards_monotonicity():
    """RF02: A função de saturação deve ser monotonicamente não-decrescente em todo o domínio."""
    n_max = np.array([150.0], dtype=np.float64)
    inputs = np.linspace(0, 300, 100)
    outputs = [
        float(calculate_richards_saturation([x], n_max, kappa=0.08, zero_anchored=True)[0])
        for x in inputs
    ]

    for i in range(len(outputs) - 1):
        assert outputs[i + 1] >= outputs[i] - 1e-9, f"Não-monotonicidade detectada em x={inputs[i]}"


def test_rf02_richards_inflection_point():
    """RF02: No ponto de inflexão lambda_0 = N_max / 2, o valor não-ancorado atinge exatamente 50% de N_max."""
    n_max = np.array([200.0], dtype=np.float64)
    lambda_0 = np.array([100.0], dtype=np.float64)

    s_inflection = calculate_richards_saturation(
        N_bruto=lambda_0,
        N_max=n_max,
        kappa=0.08,
        lambda_0=lambda_0,
        zero_anchored=False,
    )
    assert pytest.approx(float(s_inflection[0]), abs=1e-3) == 100.0


def test_rf02_numerical_stability_extreme_inputs():
    """RF02: Prevenção de overflow/underflow em exponenciais com valores bizarros (-1e8 e +1e8)."""
    n_weird = np.array([-1e8, 1e8], dtype=np.float64)
    n_max = np.array([100.0, 100.0], dtype=np.float64)

    s_res = calculate_richards_saturation(n_weird, n_max, kappa=0.08, zero_anchored=True)
    assert not np.isnan(s_res).any()
    assert not np.isinf(s_res).any()
    assert s_res[0] == 0.0
    assert pytest.approx(s_res[1], abs=1e-3) == 100.0


# ==============================================================================
# 3. Testes dos Três Métodos de Ruído Instrumental IoT (RF03)
# ==============================================================================

def test_rf03_noise_method_none():
    """RF03 / Método NONE: Epsilon deve ser exatamente zero."""
    eps, state = generate_sensor_noise(method="NONE", size=5)
    assert np.all(eps == 0.0)
    assert np.all(state == 0.0)


def test_rf03_noise_method_uniform():
    """RF03 / Método UNIFORM: Perturbações devem pertencer estritamente ao intervalo [-R, +R]."""
    r_val = 3.0
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(500):
        eps, _ = generate_sensor_noise(
            method="UNIFORM",
            size=5,
            uniform_range_R=r_val,
            rng=rng,
        )
        assert np.all(eps >= -r_val)
        assert np.all(eps <= r_val)
        samples.append(eps)

    # Média temporal deve convergir para 0.0
    mean_val = np.mean(samples)
    assert abs(mean_val) < 0.2


def test_rf03_noise_method_gaussian():
    """RF03 / Método GAUSSIAN: Deve produzir ruído com média ~ 0 e desvio ~ sigma."""
    sigma_val = 2.5
    rng = np.random.default_rng(123)
    samples = [
        generate_sensor_noise(method="GAUSSIAN", size=10, gaussian_sigma=sigma_val, rng=rng)[0]
        for _ in range(1000)
    ]
    all_vals = np.concatenate(samples)
    assert abs(np.mean(all_vals)) < 0.15
    assert abs(np.std(all_vals) - sigma_val) < 0.20


def test_rf03_noise_method_ornstein_uhlenbeck_persistence():
    """RF03 / Método OU: Deve apresentar autocorrelação temporal positiva e reversão à média."""
    rng = np.random.default_rng(999)
    theta = 1.2
    sigma = 2.0
    dt_hours = 5.0 / 60.0  # 5 minutos

    # Simula trajetória de 200 passos
    state = None
    trajectory = []
    for _ in range(200):
        eps, state = generate_sensor_noise(
            method="ORNSTEIN_UHLENBECK",
            size=1,
            dt_hours=dt_hours,
            prev_state=state,
            ou_theta=theta,
            ou_sigma=sigma,
            rng=rng,
        )
        trajectory.append(float(eps[0]))

    traj_arr = np.array(trajectory)

    # Coeficiente de autocorrelação lag-1 deve ser positivo (inércia do hardware)
    lag1_autocorr = np.corrcoef(traj_arr[:-1], traj_arr[1:])[0, 1]
    expected_decay = math.exp(-theta * dt_hours)  # ~0.905
    assert lag1_autocorr > 0.6, f"Autocorrelação temporal insuficiente: {lag1_autocorr:.3f}"
    assert pytest.approx(lag1_autocorr, abs=0.25) == expected_decay


def test_rf03_ornstein_uhlenbeck_mean_reversion_from_shock():
    """RF03 / Método OU: Um choque extremo inicial (+20 pessoas) deve decair exponencialmente para zero."""
    theta = 1.2
    dt_hours = 0.5  # passos de 30 minutos
    shock_state = np.array([20.0], dtype=np.float64)

    # Desativa difusão (sigma=0) para verificar apenas a reversão determinística à média
    state = shock_state
    for _ in range(5):
        _, state = generate_sensor_noise(
            method="OU",
            size=1,
            dt_hours=dt_hours,
            prev_state=state,
            ou_theta=theta,
            ou_sigma=0.0,
        )

    # Após 2.5 horas com theta=1.2, deve decair por exp(-1.2 * 2.5) = exp(-3) = 0.0498
    expected = 20.0 * math.exp(-1.2 * 2.5)
    assert pytest.approx(float(state[0]), abs=1e-3) == expected


# ==============================================================================
# 4. Testes de Discretização e Limitadores Estritos (RF04)
# ==============================================================================

def test_rf04_discretization_and_bounds():
    """RF04: N_sensor deve ser estritamente inteiro in N e limitado por [0, N_max]."""
    s = np.array([50.4, 0.2, 119.8, 150.0], dtype=np.float64)
    eps = np.array([-1.2, -5.0, 3.5, 10.0], dtype=np.float64)  # ruído empurra para baixo e para cima
    n_max = np.array([100.0, 50.0, 120.0, 150.0], dtype=np.float64)

    bounded = clip_and_discretize_sensor_readings(s, eps, n_max)

    # 1. Deve ser inteiro
    assert issubclass(bounded.dtype.type, np.integer)
    # 2. 50.4 - 1.2 = 49.2 -> 49
    assert bounded[0] == 49
    # 3. 0.2 - 5.0 = -4.8 -> travado em 0 (não-negatividade)
    assert bounded[1] == 0
    # 4. 119.8 + 3.5 = 123.3 -> travado em 120 (teto N_max)
    assert bounded[2] == 120
    # 5. 150.0 + 10.0 = 160.0 -> travado em 150 (teto N_max)
    assert bounded[3] == 150


# ==============================================================================
# 5. Testes de Telemetria e Datalake GeoPackage (RF05)
# ==============================================================================

def test_rf05_status_classification():
    """RF05: Avalia transições de status NORMAL (<=70%), ATENCAO (70-90%) e CRITICO (>90%)."""
    assert determine_sensor_status(0.0) == "NORMAL"
    assert determine_sensor_status(50.0) == "NORMAL"
    assert determine_sensor_status(70.0) == "NORMAL"
    assert determine_sensor_status(70.01) == "ATENCAO"
    assert determine_sensor_status(85.0) == "ATENCAO"
    assert determine_sensor_status(90.0) == "ATENCAO"
    assert determine_sensor_status(90.01) == "CRITICO"
    assert determine_sensor_status(100.0) == "CRITICO"


def test_rf05_telemetry_payload_structure():
    """RF05: Valida conformidade do schema de telemetria emitido para o Leaflet."""
    sim = SensorSaturationSimulator()
    resp = sim.evaluate(N_bruto=[50, 70, 40, 100, 80], current_time_hours=16.5)

    assert isinstance(resp, SensorTelemetryResponse)
    assert len(resp.sensors) == 5
    assert resp.current_time_hours == 16.5
    assert len(resp.vector_N_sensor) == 5

    first = resp.sensors[0]
    assert first.sensor_id == "sensor_elevador_lacerda"
    assert first.count >= 0
    assert first.max_capacity == 150
    assert 0.0 <= first.occupancy_pct <= 100.0
    assert first.status in ("NORMAL", "ATENCAO", "CRITICO")
    assert first.latitude is not None
    assert first.longitude is not None


def test_rf05_datalake_geopackage_persistence():
    """RF05: Com persist_telemetry=True, persiste os dados na tabela telemetria_sensores."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = TableManager(tmp_dir)
        sim = SensorSaturationSimulator()

        resp = sim.evaluate(
            N_bruto=[40, 50, 30, 80, 60],
            persist_telemetry=True,
            table_manager=mgr,
        )

        assert resp.persisted_rows == 5
        assert mgr.exists("telemetria_sensores")

        table = mgr.get("telemetria_sensores")
        assert table.row_count == 5
        assert "sensor_id" in table.column_names
        assert "contagem_pedestres" in table.column_names
        assert "densidade_m2" in table.column_names
        assert "status_aglomeracao" in table.column_names


# ==============================================================================
# 6. Testes de Requisitos Não-Funcionais (RNF01 e RNF02)
# ==============================================================================

def test_rnf01_performance_streaming_latency():
    """RNF01: Latência analítica completa da rede de sensores deve ser < 1 ms (1000 µs) por ciclo."""
    sim = SensorSaturationSimulator(seed=42)
    n_bruto = [50.0, 75.0, 60.0, 180.0, 120.0]
    iterations = 2000

    # Medição do ciclo matemático puro (Richards + Ruído OU + Discretização)
    n_max = sim.node_capacities
    kappas = sim.node_kappas
    l0 = sim.node_inflections

    start = time.perf_counter()
    state = np.zeros(5, dtype=np.float64)
    for _ in range(iterations):
        s = calculate_richards_saturation(n_bruto, n_max, kappa=kappas, lambda_0=l0)
        eps, state = generate_sensor_noise("OU", 5, dt_hours=0.0833, prev_state=state)
        _ = clip_and_discretize_sensor_readings(s, eps, n_max)
    elapsed = time.perf_counter() - start

    avg_us = (elapsed / iterations) * 1e6
    assert avg_us < 500.0, f"Tempo médio analítico excessivo: {avg_us:.2f} µs (deve ser < 1000 µs)"


def test_rnf02_stochastic_stability_and_no_memory_leak():
    """RNF02: Estado do ruído de Ornstein-Uhlenbeck deve permanecer estável em memória fixa."""
    sim = SensorSaturationSimulator(seed=123)

    # Executa 500 ciclos sequenciais
    for _ in range(500):
        resp = sim.evaluate(N_bruto=[60, 50, 40, 100, 70])

    # O estado interno deve ter tamanho exato J=5
    assert sim._ou_noise_state is not None
    assert sim._ou_noise_state.shape == (5,)

    # Os valores do ruído não devem divergir para o infinito
    assert np.all(np.abs(sim._ou_noise_state) < 25.0)

    # Reset de estado zera a memória
    sim.reset_state()
    assert sim._ou_noise_state is None


# ==============================================================================
# 7. Testes dos Endpoints REST FastAPI
# ==============================================================================

def test_api_get_saturation_config():
    """Testa endpoint GET /api/v1/simulation/saturation/config."""
    res = client.get("/api/v1/simulation/saturation/config")
    assert res.status_code == 200
    data = res.json()
    assert "richards" in data
    assert "noise" in data
    assert data["richards"]["kappa"] == 0.08
    assert len(data["nodes"]) == 5


def test_api_post_saturation_evaluate():
    """Testa endpoint POST /api/v1/simulation/saturation/evaluate."""
    payload = {
        "N_bruto": [60.0, 90.0, 110.0, 240.0, 190.0],
        "noise_method": "GAUSSIAN",
        "current_time_hours": 17.0,
    }
    res = client.post("/api/v1/simulation/saturation/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "vector_N_sensor" in data
    assert len(data["vector_N_sensor"]) == 5
    assert len(data["sensors"]) == 5
    assert data["noise_method"] == "GAUSSIAN"


def test_api_get_telemetry_latest():
    """Testa endpoint GET /api/v1/simulation/telemetry/latest."""
    res = client.get("/api/v1/simulation/telemetry/latest")
    assert res.status_code == 200
    data = res.json()
    assert "sensors" in data
    assert len(data["sensors"]) == 5


def test_api_get_direct_telemetry_for_leaflet():
    """RF05: Testa a rota HTTP direta /api/v1/telemetry/latest exposta para o frontend Leaflet."""
    res = client.get("/api/v1/telemetry/latest")
    assert res.status_code == 200
    data = res.json()
    assert "timestamp_iso" in data
    assert "sensors" in data
    assert len(data["sensors"]) == 5
