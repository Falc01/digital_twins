"""
Suíte de Testes Automatizados para a Simulação Contínua / Rollout 24h (Docs 01 + 02 + 03).
"""

import math
import numpy as np
import pytest

from src.simulation.rollout import RolloutSimulationEngine, RolloutStep, RolloutSummary
from src.simulation.schemas import MacroFlowConfig, MarkovCirculationConfig


def test_rollout_step_execution():
    """Testa se um único passo de simulação computa entradas, saídas e novo estado."""
    engine = RolloutSimulationEngine(regime="trimodal", gamma=1.0)
    init_state = np.array([50.0, 40.0, 20.0, 10.0, 10.0], dtype=np.float64)

    new_state, step_data = engine.run_step(
        current_state_N=init_state,
        t_hours=12.5,
        step_minutes=30.0,
        step_index=1,
    )

    assert len(new_state) == 5
    assert np.all(new_state >= 0.0), "População não pode ser negativa"
    assert step_data.total_population > 0.0
    assert step_data.step_index == 1
    assert "Elevador Lacerda" in step_data.inflow_by_gate
    assert "Praça da Sé" in step_data.inflow_by_gate
    assert "Ladeira do Carmo" in step_data.inflow_by_gate


def test_rollout_batch_24h_execution():
    """Testa a execução completa do dia em lote (24h de 30 em 30 min)."""
    engine = RolloutSimulationEngine(regime="trimodal", gamma=1.0)
    summary = engine.run_batch(
        start_hour=0.0,
        end_hour=24.0,
        step_minutes=30.0,
    )

    assert summary.total_steps == 48
    assert len(summary.steps) == 48
    assert summary.cumulative_inflow > 0.0
    assert summary.cumulative_egress > 0.0
    assert summary.peak_population > 0.0
    assert 11.0 <= summary.peak_time_hours <= 17.5, "Pico de pedestres deve ocorrer no período comercial/turístico"

    # Invariante: Em nenhum momento a população pode ser negativa
    for step in summary.steps:
        assert step.total_population >= 0.0
        assert step.total_inflow >= 0.0
        assert step.total_egress >= 0.0


def test_rollout_determinism_identical_runs():
    """Valida se execuções com mesmos parâmetros N_max e N_min produzem resultados 100% idênticos."""
    cfg = MacroFlowConfig(N_max=300, N_min=15, regime="trimodal")
    engine1 = RolloutSimulationEngine(macro_config=cfg, regime="trimodal")
    engine2 = RolloutSimulationEngine(macro_config=cfg, regime="trimodal")

    summary1 = engine1.run_batch(start_hour=6.0, end_hour=18.0, step_minutes=60.0)
    summary2 = engine2.run_batch(start_hour=6.0, end_hour=18.0, step_minutes=60.0)

    assert summary1.total_steps == summary2.total_steps
    assert math.isclose(summary1.cumulative_inflow, summary2.cumulative_inflow, rel_tol=1e-9)
    assert math.isclose(summary1.cumulative_egress, summary2.cumulative_egress, rel_tol=1e-9)
    assert math.isclose(summary1.peak_population, summary2.peak_population, rel_tol=1e-9)
    
    for s1, s2 in zip(summary1.steps, summary2.steps):
        assert np.allclose(s1.state_N, s2.state_N, atol=1e-9)


def test_rollout_live_generator():
    """Testa se o gerador em tempo real produz passos válidos sem delay."""
    engine = RolloutSimulationEngine(regime="trimodal")
    gen = engine.run_live_generator(
        start_hour=10.0,
        end_hour=12.0,
        step_minutes=30.0,
        delay_seconds=0.0,
    )

    steps_received = list(gen)
    assert len(steps_received) == 4
    assert steps_received[0].hour_formatted == "10:00"
    assert steps_received[-1].hour_formatted == "11:30"


def test_rollout_step_size_consistency_with_events():
    """Valida se a ativação de eventos com diferentes passos (30m vs 60m) é consistente e produz inteiros."""
    engine_30 = RolloutSimulationEngine(regime="trimodal", enable_events=True)
    engine_60 = RolloutSimulationEngine(regime="trimodal", enable_events=True)

    summary_30 = engine_30.run_batch(start_hour=0.0, end_hour=24.0, step_minutes=30.0)
    summary_60 = engine_60.run_batch(start_hour=0.0, end_hour=24.0, step_minutes=60.0)

    # Ingressos acumulados devem ser consistentes (< 5% de tolerância de discretização)
    assert math.isclose(summary_30.cumulative_inflow, summary_60.cumulative_inflow, rel_tol=0.05)
    assert math.isclose(summary_30.cumulative_egress, summary_60.cumulative_egress, rel_tol=0.05)

    # Picos não devem explodir (evita acúmulo descontrolado de 900+ pessoas às 23h)
    assert summary_30.peak_population <= 350.0
    assert summary_60.peak_population <= 350.0

    # Valores devem ser estritamente inteiros
    for s in summary_30.steps:
        assert float(s.total_population).is_integer()
        for count in s.state_N:
            assert float(count).is_integer()
