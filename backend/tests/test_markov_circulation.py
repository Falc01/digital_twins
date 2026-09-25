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
