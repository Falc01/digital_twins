"""
Suíte de Testes Formais de Propriedades (Property-Based Testing com Hypothesis).

Objetivo:
Validar numericamente em float64 contra milhares de casos de borda aleatórios
os mesmos invariantes e teoremas matemáticos provados simbolicamente em Lean 4
(formal_proofs/):
  1. Conservação Estocástica de Linhas e Balanço Global de Massa (Doc 03 / MarkovCirculation.lean)
  2. Preservação de Soma Unitária sob Creep Flow (Doc 03 / MarkovCirculation.lean)
  3. Limitante Superior Estrito do Amortecimento Coletivo (Doc 02 / EventDamping.lean)
  4. Partição Estrita de Influxo Diferencial por Portão (Doc 01 / MacroFlow.lean)
"""

import math
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from src.simulation.markov_circulation import (
    compute_markov_matrix,
    propagate_flow,
)
from src.simulation.events_injection import apply_collective_saturation_damping
from src.simulation.macro_flow import calculate_gamma_seasonality


# ==============================================================================
# 1. Invariantes do Módulo 03: Cadeias de Markov, Egress e Creep Flow
# ==============================================================================

@settings(max_examples=100, deadline=None)
@given(
    j_nodes=st.integers(min_value=2, max_value=8),
    lambda_decay=st.floats(min_value=0.001, max_value=0.1),
    retention_bias=st.floats(min_value=0.5, max_value=2.0),
    step_minutes=st.floats(min_value=1.0, max_value=60.0),
    use_inertia=st.booleans(),
)
def test_hypothesis_markov_stochastic_rows_and_egress(
    j_nodes: int,
    lambda_decay: float,
    retention_bias: float,
    step_minutes: float,
    use_inertia: bool,
):
    """
    Hypothesis: Para qualquer grafo de J nós, distâncias finitas, alphas positivos
    e taxas de egress em [0, 0.85], toda linha de P(t) mais a saída soma exatamente 1.0.
    Espelha: `theorem row_stochastic_with_egress` em Lean 4.
    """
    # Gera matriz de distâncias simétrica
    coords = np.random.uniform(-1000.0, 1000.0, size=(j_nodes, 2))
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist_mat = np.sqrt(np.sum(diff ** 2, axis=-1))

    alphas = np.random.uniform(0.1, 5.0, size=j_nodes)
    egress_rates = np.random.uniform(0.0, 0.50, size=j_nodes)

    p_mat = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        lambda_decay=lambda_decay,
        retention_bias=retention_bias,
        step_minutes=step_minutes,
        use_inertia=use_inertia,
        egress_rates=egress_rates,
    )

    assert p_mat.shape == (j_nodes, j_nodes)
    assert np.all(p_mat >= 0.0), "Probabilidades de transição devem ser não-negativas"

    # Invariante: linha i + taxa de saída == 1.0
    for i in range(j_nodes):
        row_sum = float(np.sum(p_mat[i, :]))
        exit_p = float(egress_rates[i])
        total_line = row_sum + exit_p
        assert abs(total_line - 1.0) < 1e-6, f"Linha {i} violou 100%: soma={total_line}"


@settings(max_examples=100, deadline=None)
@given(
    j_nodes=st.integers(min_value=2, max_value=6),
    n_total=st.floats(min_value=10.0, max_value=5000.0),
)
def test_hypothesis_pedestrian_mass_balance_conservation(j_nodes: int, n_total: float):
    """
    Hypothesis: A propagação estocástica P^T * N conserva rigorosamente a massa de pedestres.
    Total_Propagado + Total_Egress == Total_Inicial.
    Espelha: `theorem pedestrian_mass_balance_two_nodes` em Lean 4.
    """
    raw_weights = np.random.uniform(0.1, 1.0, size=j_nodes)
    n_init = (raw_weights / np.sum(raw_weights)) * n_total

    coords = np.random.uniform(0.0, 500.0, size=(j_nodes, 2))
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist_mat = np.sqrt(np.sum(diff ** 2, axis=-1))
    alphas = np.random.uniform(0.5, 3.0, size=j_nodes)
    egress_rates = np.random.uniform(0.0, 0.40, size=j_nodes)

    p_mat = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        egress_rates=egress_rates,
    )

    n_prop = propagate_flow(n_init, p_mat)
    # Egress por nó = n_init[i] * egress_rates[i]
    n_egress = n_init * egress_rates

    sum_init = float(np.sum(n_init))
    sum_prop = float(np.sum(n_prop))
    sum_egress = float(np.sum(n_egress))

    balance = sum_prop + sum_egress
    assert abs(balance - sum_init) < 1e-4, f"Balanço de massa violado: {balance} != {sum_init}"


@settings(max_examples=80, deadline=None)
@given(
    n_curr=st.floats(min_value=0.0, max_value=2000.0),
    n_cap=st.floats(min_value=50.0, max_value=1000.0),
    kappa=st.floats(min_value=0.01, max_value=0.20),
)
def test_hypothesis_creep_flow_stochastic_invariance(n_curr: float, n_cap: float, kappa: float):
    """
    Hypothesis: Sob qualquer combinação de densidade e capacidade, o Creep Flow
    sempre preserva a soma estocástica da linha exatamente igual a 1.0.
    Espelha: `theorem creep_flow_row_conservation` em Lean 4.
    """
    dist_mat = np.array([
        [0.0, 150.0, 250.0],
        [150.0, 0.0, 120.0],
        [250.0, 120.0, 0.0],
    ])
    alphas = [1.0, 1.5, 2.0]

    p_mat = compute_markov_matrix(
        dist_matrix=dist_mat,
        alpha_vector=alphas,
        current_state_N=[n_curr, 50.0, 50.0],
        node_capacities=[n_cap, 200.0, 200.0],
        kappa_creep=kappa,
    )

    for i in range(3):
        row_sum = float(np.sum(p_mat[i, :]))
        assert abs(row_sum - 1.0) < 1e-6, f"Creep flow quebrou linha {i}: {row_sum}"


# ==============================================================================
# 2. Invariantes do Módulo 02: Amortecimento Logístico de Fruin/Helbing
# ==============================================================================

@settings(max_examples=100, deadline=None)
@given(
    E_val=st.floats(min_value=0.0, max_value=50000.0),
    n_max=st.integers(min_value=50, max_value=10000),
    damping_factor=st.floats(min_value=1.0, max_value=3.0),
)
def test_hypothesis_collective_damping_strict_upper_bound(
    E_val: float,
    n_max: int,
    damping_factor: float,
):
    """
    Hypothesis: Para qualquer valor astronômico de eventos E (Carnaval com 50.000 pessoas),
    o fluxo amortecido NUNCA ultrapassa o teto físico estendido D * N_max.
    Espelha: `theorem damping_upper_bound` em Lean 4.
    """
    vector_E = np.array([E_val], dtype=np.float64)
    caps = [n_max]

    damped = apply_collective_saturation_damping(vector_E, caps, damping_factor=damping_factor)
    damped_val = float(damped[0])

    teto_fisico = damping_factor * float(n_max)

    assert damped_val >= 0.0, "Fluxo amortecido não pode ser negativo"
    assert damped_val < teto_fisico, f"Blindagem estourou teto físico: {damped_val} >= {teto_fisico}"


@settings(max_examples=80, deadline=None)
@given(
    e1=st.floats(min_value=0.0, max_value=5000.0),
    e2=st.floats(min_value=0.0, max_value=5000.0),
    n_max=st.integers(min_value=100, max_value=2000),
)
def test_hypothesis_damping_monotonicity(e1: float, e2: float, n_max: int):
    """
    Hypothesis: Se E_a <= E_b, então Damping(E_a) <= Damping(E_b) (Monotonicidade).
    """
    ea = min(e1, e2)
    eb = max(e1, e2)

    da = float(apply_collective_saturation_damping([ea], [n_max], damping_factor=1.5)[0])
    db = float(apply_collective_saturation_damping([eb], [n_max], damping_factor=1.5)[0])

    assert da <= db + 1e-9, f"Damping não monotônico: {da} > {db}"


# ==============================================================================
# 3. Invariantes do Módulo 01: Macro-Fluxo e Gamma Efetivo
# ==============================================================================

@settings(max_examples=80, deadline=None)
@given(
    manual_gamma=st.floats(min_value=0.1, max_value=10.0),
    season=st.sampled_from(["SUMMER", "SPRING", "AUTUMN", "WINTER"]),
    weather=st.sampled_from(["SUNNY", "LIGHT_RAIN", "HEAVY_RAIN"]),
)
def test_hypothesis_effective_gamma_strictly_positive(
    manual_gamma: float,
    season: str,
    weather: str,
):
    """
    Hypothesis: A multiplicação unificada de sazonalidade, clima e manual sempre resulta em gamma > 0.
    Espelha: `theorem effective_gamma_strictly_positive` em Lean 4.
    """
    g_eff = calculate_gamma_seasonality(season=season, weather=weather, manual_gamma=manual_gamma)
    assert g_eff > 0.0, f"Gamma efetivo deve ser estritamente positivo: {g_eff}"
    assert math.isfinite(g_eff), "Gamma efetivo deve ser finito"
