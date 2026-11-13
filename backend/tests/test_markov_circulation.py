"""
Suíte de Testes Automatizados para a Circulação de Rede de Markov & POIs (Doc 03).

Valida os Requisitos Funcionais (RF01 a RF05) e Não-Funcionais (RNF01 a RNF02)
especificados em docs/explanation/dados_sinteticos/03_circulacao_markov_pois.md.
"""

import os
import sys
import time
import pytest
import numpy as np
from fastapi.testclient import TestClient

# Adiciona backend/ e backend/src/ ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from src.simulation.markov_circulation import (
    MarkovCirculationSimulator,
    compute_distance_matrix,
    evaluate_hourly_attraction,
    compute_markov_matrix,
    propagate_flow,
    propagate_markov_flow,
)
from src.simulation.schemas import (
    MarkovCirculationConfig,
    MarkovCirculationRequest,
    NodeCoordinate,
)
from src.api.main import app

client = TestClient(app)


# ==============================================================================
# 1. Testes de Distâncias e Geometria Espacial (Canal A)
# ==============================================================================

def test_distance_matrix_symmetry_and_diagonal():
    """Valida cálculo de matriz simétrica com diagonal estritamente nula."""
    coords = [
        (-12.97330, -38.51260),  # Lacerda
        (-12.97380, -38.51090),  # Sé
        (-12.97180, -38.50850),  # Pelourinho
    ]
    dist_mat = compute_distance_matrix(coords)
    
    assert dist_mat.shape == (3, 3)
    # Diagonal principal deve ser zero
    for i in range(3):
        assert dist_mat[i, i] == 0.0
        
    # Simetria d_ij == d_ji
    assert pytest.approx(dist_mat[0, 1]) == dist_mat[1, 0]
    assert pytest.approx(dist_mat[0, 2]) == dist_mat[2, 0]
    assert pytest.approx(dist_mat[1, 2]) == dist_mat[2, 1]
    
    # As distâncias reais no Pelourinho entre Sé e Lacerda devem ser da ordem de 150m a 250m
    assert 100.0 < dist_mat[0, 1] < 300.0


# ==============================================================================
# 2. Testes da Matriz de Markov e Propriedade Estocástica (RF01, RF04)
# ==============================================================================

def test_markov_stochastic_rows_rf01_rf04():
    """RF01 & RF04: Toda linha da matriz P(t) deve somar estritamente 1.0."""
    dist_mat = np.array([
        [0.0, 150.0, 300.0],
        [150.0, 0.0, 180.0],
        [300.0, 180.0, 0.0],
    ])
    alphas = [1.0, 2.0, 1.5]
    
    p_mat = compute_markov_matrix(dist_mat, alphas, lambda_decay=0.015)
    
    assert p_mat.shape == (3, 3)
    # Todas as probabilidades devem ser não-negativas
    assert np.all(p_mat >= 0.0)
    
    # Cada linha i deve somar exatamente 1.0 (propriedade estocástica)
    row_sums = np.sum(p_mat, axis=1)
    for idx, s in enumerate(row_sums):
        assert pytest.approx(s, abs=1e-6) == 1.0, f"Linha {idx} não soma 1.0 (soma = {s})"


def test_distance_decay_rf03():
    """RF03: Decaimento de probabilidade com a distância espacial d_ij."""
    # Nó 0 a 50m do Nó 1, e a 400m do Nó 2 (mesmo alpha)
    dist_mat = np.array([
        [0.0, 50.0, 400.0],
        [50.0, 0.0, 350.0],
        [400.0, 350.0, 0.0],
    ])
    alphas = [1.0, 1.0, 1.0]
    
    p_mat = compute_markov_matrix(dist_mat, alphas, lambda_decay=0.015, retention_bias=1.0)
    
    # Probabilidade de transição para o nó próximo (50m) deve ser muito superior ao nó remoto (400m)
    p_to_near = p_mat[0, 1]
    p_to_far = p_mat[0, 2]
    assert p_to_near > p_to_far * 10.0, f"P_perto ({p_to_near}) deveria ser > 10x P_longe ({p_to_far})"


def test_poi_attraction_rf02():
    """RF02: Aumentar alpha_j de um nó específico aumenta a probabilidade de migração para ele."""
    dist_mat = np.array([
        [0.0, 100.0, 100.0],
        [100.0, 0.0, 100.0],
        [100.0, 100.0, 0.0],
    ])
    # Cenário base com atratividades iguais
    p_base = compute_markov_matrix(dist_mat, [1.0, 1.0, 1.0], lambda_decay=0.01)
    
    # Cenário com Nó 2 promovido a super atrator (ex: show no Largo)
    p_show = compute_markov_matrix(dist_mat, [1.0, 1.0, 5.0], lambda_decay=0.01)
    
    # A probabilidade de ir do Nó 0 para o Nó 2 deve ter disparado
    assert p_show[0, 2] > p_base[0, 2] * 2.0


# ==============================================================================
# 3. Testes de Conservação Estrita de Pedestres (RF04, RF05)
# ==============================================================================

def test_pedestrian_conservation_rf04_rf05():
    """RF04 & RF05: O total de pedestres redistribuído sum(N_prop) == sum(N_inicial)."""
    simulator = MarkovCirculationSimulator()
    initial_counts = [120.0, 85.0, 45.0, 10.0, 0.0]
    
    res = simulator.propagate(current_state_N=initial_counts, t_hours=16.5)
    
    assert pytest.approx(res.total_initial_pedestrians) == 260.0
    assert pytest.approx(res.total_propagated_pedestrians) == 260.0
    assert res.conservation_error < 1e-4
    
    # Nenhum sensor deve terminar com contagem negativa
    for val in res.vector_N_propagado:
        assert val >= 0.0


def test_hourly_attraction_modulation():
    """RF02: Valida modulação dinâmica horária dos campos atratores alpha_j(t)."""
    base_alphas = [1.0, 1.0, 1.0]
    types = ["GATE", "IGREJA", "SHOW"]
    
    # Às 10h da manhã: Igreja deve estar em pico superior a Show
    alphas_morning = evaluate_hourly_attraction(10.0, base_alphas, types)
    assert alphas_morning[1] > alphas_morning[2]
    
    # Às 19h da noite: Show deve estar em ápice muito superior a Igreja
    alphas_night = evaluate_hourly_attraction(19.0, base_alphas, types)
    assert alphas_night[2] > alphas_night[1] * 1.5


# ==============================================================================
# 4. Testes de Validação e Erros Robustos
# ==============================================================================

def test_matrix_dimension_validation():
    """Valida rejeição de matriz não quadrada ou vetor de alpha incompatível."""
    invalid_dist = np.zeros((3, 2))
    with pytest.raises(ValueError, match="quadrada"):
        compute_markov_matrix(invalid_dist, [1.0, 1.0, 1.0])
        
    square_dist = np.zeros((3, 3))
    with pytest.raises(ValueError, match="dimensão"):
        compute_markov_matrix(square_dist, [1.0, 1.0])  # apenas 2 alphas para 3 nós


def test_negative_attraction_rejection():
    """Valida rejeição de alpha_j <= 0."""
    dist_mat = np.zeros((2, 2))
    with pytest.raises(ValueError, match="estritamente positivos"):
        compute_markov_matrix(dist_mat, [1.0, -0.5])


def test_markov_simulator_fallback_doc01():
    """Desacoplamento: se current_state_N for omitido, consome Doc 01 automaticamente."""
    simulator = MarkovCirculationSimulator()
    res = simulator.propagate(current_state_N=None, t_hours=16.5, gamma=1.0)
    
    # No ápice das 16h30 com gamma=1.0, o Doc 01 injeta 300 pessoas
    assert pytest.approx(res.total_initial_pedestrians, abs=1.0) == 300.0
    assert pytest.approx(res.total_propagated_pedestrians, abs=1.0) == 300.0
    assert len(res.vector_N_propagado) == 5


# ==============================================================================
# 5. Testes de Performance em Álgebra Linear (RNF01, RNF02)
# ==============================================================================

def test_markov_performance_rnf01_rnf02():
    """RNF01: Multiplicação matricial O(J^2) com NumPy deve ser < 50 µs por ciclo para 5 nós."""
    dist_mat = np.zeros((5, 5), dtype=np.float64)
    alphas = np.array([1.0, 1.2, 0.9, 2.5, 1.8], dtype=np.float64)
    state = np.array([100.0, 80.0, 50.0, 40.0, 30.0], dtype=np.float64)
    iterations = 5000
    
    p_mat = compute_markov_matrix(dist_mat, alphas)
    
    # Benchmark da multiplicação matricial pura N_prop = P^T * N (RNF01: < 50 µs)
    start_prop = time.perf_counter()
    for _ in range(iterations):
        _ = propagate_flow(state, p_mat)
    elapsed_prop = time.perf_counter() - start_prop
    avg_prop_us = (elapsed_prop / iterations) * 1e6
    assert avg_prop_us < 50.0, f"Tempo de multiplicação matricial O(J^2) elevado: {avg_prop_us:.2f} µs"

    # Benchmark da computação completa da matriz + propagação (< 100 µs)
    start_math = time.perf_counter()
    for _ in range(iterations):
        p = compute_markov_matrix(dist_mat, alphas)
        _ = propagate_flow(state, p)
    elapsed_math = time.perf_counter() - start_math
    avg_math_us = (elapsed_math / iterations) * 1e6
    assert avg_math_us < 100.0, f"Tempo matricial completo O(J^2) elevado: {avg_math_us:.2f} µs"

    # Benchmark do ciclo completo com serialização de nós (< 2.0 ms)
    simulator = MarkovCirculationSimulator()
    start_full = time.perf_counter()
    for _ in range(1000):
        _ = simulator.propagate(current_state_N=state, t_hours=16.5)
    elapsed_full = time.perf_counter() - start_full
    avg_full_ms = (elapsed_full / 1000) * 1e3
    assert avg_full_ms < 2.0, f"Tempo de ciclo completo com serialização elevado: {avg_full_ms:.2f} ms"


# ==============================================================================
# 6. Testes dos Endpoints REST FastAPI
# ==============================================================================

def test_api_get_markov_config():
    """Testa endpoint GET /api/v1/simulation/markov/config."""
    res = client.get("/api/v1/simulation/markov/config")
    assert res.status_code == 200
    data = res.json()
    assert "lambda_decay" in data
    assert len(data["nodes"]) == 5
    assert data["nodes"][0]["sensor_id"] == "sensor_elevador_lacerda"


def test_api_get_markov_matrix():
    """Testa endpoint GET /api/v1/simulation/markov/matrix."""
    res = client.get("/api/v1/simulation/markov/matrix?time_hours=16.5")
    assert res.status_code == 200
    data = res.json()
    assert "transition_matrix" in data
    assert len(data["transition_matrix"]) == 5
    # Verifica que linha 0 soma 1.0
    assert pytest.approx(sum(data["transition_matrix"][0]), abs=1e-3) == 1.0


def test_api_post_markov_propagate():
    """Testa endpoint POST /api/v1/simulation/markov/propagate."""
    payload = {
        "current_time_hours": 16.5,
        "gamma_seasonality": 1.0,
        "current_state_N": [100.0, 80.0, 50.0, 30.0, 40.0],
    }
    res = client.post("/api/v1/simulation/markov/propagate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_initial_pedestrians"] == 300.0
    assert pytest.approx(data["total_propagated_pedestrians"]) == 300.0
    assert len(data["vector_N_propagado"]) == 5
    assert len(data["node_flows"]) == 5


# ==============================================================================
# 7. Testes de Inércia Temporal, Cadeia Aberta (Egress) e Integração N_bruto
# ==============================================================================

def test_temporal_inertia_and_step_minutes():
    """Testa se passos curtos (dt=1 min) aumentam a retenção diagonal P_ii em relação a passos longos."""
    dist_mat = np.array([
        [0.0, 100.0],
        [100.0, 0.0],
    ])
    alphas = [1.0, 1.0]

    p_short = compute_markov_matrix(
        dist_mat, alphas, step_minutes=1.0, dwell_time_minutes=20.0, use_inertia=True
    )
    p_long = compute_markov_matrix(
        dist_mat, alphas, step_minutes=15.0, dwell_time_minutes=20.0, use_inertia=True
    )

    # Com dt menor, a inércia rho é maior, logo a permanência P_ii é maior
    assert p_short[0, 0] > p_long[0, 0]
    # Ambos mantêm linhas somando 1.0
    assert pytest.approx(sum(p_short[0]), abs=1e-5) == 1.0
    assert pytest.approx(sum(p_long[0]), abs=1e-5) == 1.0


def test_open_markov_chain_gate_egress():
    """Testa conservação da cadeia aberta: N_propagado + N_egress == N_inicial."""
    sim = MarkovCirculationSimulator()
    state = [100.0, 80.0, 50.0, 150.0, 90.0]

    res = sim.propagate(
        current_state_N=state,
        t_hours=19.0,  # Noite: alta taxa de dispersão nos portões
        step_minutes=5.0,
        enable_egress=True,
    )

    assert res.egress_enabled is True
    assert res.total_egress_pedestrians > 0.0
    # Portões de entrada (índices 0, 1, 2) devem ter egress > 0
    assert res.vector_N_egress[0] > 0.0
    assert res.vector_N_egress[1] > 0.0
    # POIs internos (índices 3 e 4 - SHOW e IGREJA) têm egress == 0.0
    assert res.vector_N_egress[3] == 0.0
    assert res.vector_N_egress[4] == 0.0

    # Balanço físico estrito de conservação
    total_balance = res.total_propagated_pedestrians + res.total_egress_pedestrians
    assert pytest.approx(total_balance, abs=1e-4) == res.total_initial_pedestrians
    assert res.conservation_error < 1e-4


def test_orchestrate_raw_physical_flow_for_doc04():
    """Testa composição de N_bruto = N_propagado + delta_N_rotina + E_eventos."""
    sim = MarkovCirculationSimulator()
    state = [50.0, 40.0, 30.0, 80.0, 60.0]

    res = sim.propagate(
        current_state_N=state,
        t_hours=16.5,
        include_raw_flow=True,
        delta_N_rotina=[10.0, 5.0, 2.0, 0.0, 0.0],
        vector_E_eventos=[0.0, 0.0, 0.0, 45.0, 0.0],
    )

    assert res.vector_N_bruto is not None
    assert len(res.vector_N_bruto) == 5

    # Para o nó 3 (Largo do Pelourinho): N_bruto = N_prop[3] + 0.0 + 45.0
    expected_node3 = res.vector_N_propagado[3] + 45.0
    assert pytest.approx(res.vector_N_bruto[3], abs=0.05) == expected_node3

    # Para o nó 0 (Elevador Lacerda): N_bruto = N_prop[0] + 10.0 + 0.0
    expected_node0 = res.vector_N_propagado[0] + 10.0
    assert pytest.approx(res.vector_N_bruto[0], abs=0.05) == expected_node0


def test_api_markov_propagate_with_egress_and_raw_flow():
    """Testa rota HTTP POST com egress e composição de N_bruto ativados."""
    payload = {
        "current_time_hours": 18.0,
        "gamma_seasonality": 1.0,
        "step_minutes": 5.0,
        "enable_egress": True,
        "include_raw_flow": True,
        "current_state_N": [60.0, 50.0, 30.0, 100.0, 80.0],
    }
    res = client.post("/api/v1/simulation/markov/propagate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["egress_enabled"] is True
    assert data["total_egress_pedestrians"] > 0.0
    assert data["vector_N_bruto"] is not None
    assert len(data["vector_N_bruto"]) == 5
    assert data["conservation_error"] < 1e-4


# ==============================================================================
# 7. Testes das Propostas de Melhoria Doc 03 (Tipagem de POIs, Creep Flow & Egress)
# ==============================================================================

def test_stochastic_normalization_invariant_100_percent():
    """Valida a invariante estocástica estrita: sum_j P_ij + P_egress == 1.000000 +- 1e-6."""
    from src.simulation.markov_circulation import compute_markov_matrix

    dist_mat = np.array([
        [0.0, 100.0, 200.0],
        [100.0, 0.0, 150.0],
        [200.0, 150.0, 0.0],
    ])
    alphas = [1.0, 1.5, 2.0]
    egress_rates = [0.12, 0.0, 0.0]  # nó 0 é portão

    # Com egress e creep flow
    p_mat = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        egress_rates=egress_rates,
        current_state_N=[250.0, 40.0, 20.0],
        node_capacities=[200.0, 100.0, 100.0],
    )

    # Para cada linha i: soma das probabilidades internas + egress rate == 1.0
    for i in range(3):
        row_sum = float(np.sum(p_mat[i, :]))
        exit_p = egress_rates[i]
        assert abs((row_sum + exit_p) - 1.0) < 1e-6, f"Linha {i} violou normalização: {row_sum + exit_p}"


def test_dynamic_attraction_sunday_religious_vs_commercial():
    """Valida que aos domingos de manhã o nó RELIGIOSO atrai > 3x mais que o COMERCIO."""
    from src.simulation.markov_circulation import get_poi_attraction

    # Domingo (day_of_week = 6) às 10h30 (missas históricas)
    alpha_religioso = get_poi_attraction(poi_type="RELIGIOSO", hour=10.5, day_of_week=6)
    alpha_comercio = get_poi_attraction(poi_type="COMERCIO", hour=10.5, day_of_week=6)

    # RELIGIOSO = 3.5, COMERCIO = 0.1
    assert alpha_religioso >= 3.0
    assert alpha_comercio <= 0.2
    assert alpha_religioso > 3.0 * alpha_comercio
    assert alpha_religioso / alpha_comercio > 10.0


def test_saturday_night_egress_lower_than_thursday_night():
    """Valida que aos sábados à noite a probabilidade de egress nos portões é menor que nas quintas-feiras."""
    from src.simulation.markov_circulation import calculate_gate_egress_probability

    # Às 20h00
    egress_saturday = calculate_gate_egress_probability(current_time_hours=20.0, day_of_week=5)
    egress_thursday = calculate_gate_egress_probability(current_time_hours=20.0, day_of_week=3)

    assert egress_saturday < egress_thursday, (
        f"Egress de sábado ({egress_saturday:.4f}) deve ser menor que de quinta-feira ({egress_thursday:.4f})"
    )


def test_creep_flow_high_density_inertia_boost():
    """Valida o mecanismo de creep flow: se N_j > 0.85 N_max, a diagonal P_jj aumenta expressivamente."""
    from src.simulation.markov_circulation import compute_markov_matrix

    dist_mat = np.array([
        [0.0, 100.0],
        [100.0, 0.0],
    ])
    alphas = [1.0, 1.0]

    # Cenário normal: nó 0 tem 50 pessoas de capacidade 200 (25% - densidade livre)
    p_free = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        current_state_N=[50.0, 50.0],
        node_capacities=[200.0, 200.0],
    )
    p00_free = p_free[0, 0]

    # Cenário saturado (Creep Flow): nó 0 tem 190 pessoas de capacidade 200 (95% - LOS F)
    p_crowded = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        current_state_N=[190.0, 50.0],
        node_capacities=[200.0, 200.0],
    )
    p00_crowded = p_crowded[0, 0]

    assert p00_crowded > p00_free, f"Inércia sob creep flow ({p00_crowded}) deve superar fluxo livre ({p00_free})"
    assert np.allclose(np.sum(p_crowded, axis=1), [1.0, 1.0], atol=1e-6)

def test_default_config_canonical_poi_types():
    """Valida tipagem sem?ntica can?nica nos n?s padr?o de MarkovCirculationConfig (Doc 03)."""
    cfg = MarkovCirculationConfig()
    poi_types = [node.poi_type for node in cfg.nodes]
    assert poi_types == ["GATE", "GATE", "GATE", "CULTURAL", "RELIGIOSO"]


def test_creep_flow_isolated_node_preserves_stochasticity():
    """Garante que um n? isolado (p_base == 1.0) saturado preserva soma de linha == 1.0."""
    dist_mat = np.array([
        [0.0, 100.0],
        [100.0, 0.0],
    ])
    adj = np.array([
        [1.0, 0.0],  # n? 0 isolado (sem sa?da para n? 1)
        [0.0, 1.0],
    ])
    p_mat = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=[1.0, 1.0],
        adjacency_matrix=adj,
        current_state_N=[250.0, 10.0],
        node_capacities=[200.0, 200.0],
    )
    assert pytest.approx(float(np.sum(p_mat[0, :])), abs=1e-6) == 1.0
    assert pytest.approx(float(p_mat[0, 0]), abs=1e-6) == 1.0


def test_day_of_week_forwarded_in_wrapper_and_api():
    """Valida que propagate_markov_flow e endpoints REST repassam day_of_week corretamente."""
    res_sun = propagate_markov_flow(
        current_state_N=[50.0, 50.0, 50.0, 50.0, 50.0],
        current_time_hours=10.5,
        day_of_week=6,
    )
    res_sat = propagate_markov_flow(
        current_state_N=[50.0, 50.0, 50.0, 50.0, 50.0],
        current_time_hours=10.5,
        day_of_week=5,
    )
    # Domingo 10h30: n? 4 (Terreiro de Jesus / RELIGIOSO) deve atrair mais que no S?bado 10h30
    assert res_sun.attraction_vector[4] > res_sat.attraction_vector[4]

    api_res = client.post(
        "/api/v1/simulation/markov/propagate",
        json={
            "current_time_hours": 10.5,
            "day_of_week": 6,
            "current_state_N": [50.0, 50.0, 50.0, 50.0, 50.0],
        },
    )
    assert api_res.status_code == 200
    assert api_res.json()["attraction_vector"][4] == res_sun.attraction_vector[4]

    mat_res = client.get("/api/v1/simulation/markov/matrix?time_hours=10.5&day_of_week=6")
    assert mat_res.status_code == 200
    assert mat_res.json()["attraction_alphas"][4] == res_sun.attraction_vector[4]
