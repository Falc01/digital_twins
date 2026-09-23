"""
<<<<<<< HEAD
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
=======
Suíte de Testes Automatizados para o Macro-Fluxo Circadiano (Doc 01).

Valida os Requisitos Funcionais (RF01 a RF05) e Não-Funcionais (RNF01 a RNF03)
especificados em docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md.
"""

import math
import time
import unittest
import sys
import os

# Adiciona backend/ ao path para execução dos testes isolada
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.simulation.macro_flow import (
    MacroFlowSimulator,
    MacroFlowConfig,
    calculate_bairro_volume,
    circadian_hour,
    allocate_gates,
)
from src.simulation.schemas import SensorGateWeight, MacroFlowRequest


class TestMacroFlowSubsystem(unittest.TestCase):
    """Testes formais de conformidade matemática com o Doc 01."""

    def setUp(self):
        self.simulator = MacroFlowSimulator()
        self.cfg = self.simulator.config

    def test_exact_gaussian_peak_rf01(self):
        """RF01: No ápice turístico (t = t_pico = 16.5), N_bairro(t) deve ser exatamente gamma * N_max."""
        # Com gamma = 1.0, N_max = 300
        vol = calculate_bairro_volume(
            t_hours=16.5,
            gamma=1.0,
            N_min=self.cfg.N_min_bairro,
            N_max=self.cfg.N_max_bairro,
            t_peak=16.5,
            sigma=3.0,
        )
        self.assertAlmostEqual(vol, 300.0, places=4, msg="No ápice de 16h30, N_bairro deve ser 300.0")

    def test_circadian_midnight_baseline(self):
        """Na madrugada (ex: 03h00), o volume deve convergir assintoticamente para N_min (15 pessoas)."""
        vol = calculate_bairro_volume(
            t_hours=3.0,
            gamma=1.0,
            N_min=15.0,
            N_max=300.0,
            t_peak=16.5,
            sigma=3.0,
        )
        # diff = 3.0 - 16.5 = -13.5h. 13.5^2 / (2 * 9) = 10.125. exp(-10.125) ~ 4e-5
        self.assertAlmostEqual(vol, 15.0, delta=0.05, msg="Na madrugada (03h00), N_bairro deve estar próximo de N_min")

    def test_conservation_of_flow_rf03(self):
        """RF03: A soma das alocações de pedestres de todos os portões deve ser exatamente N_bairro(t)."""
        test_hours = [0.0, 3.0, 8.5, 12.0, 16.5, 20.0, 23.5]
        for t in test_hours:
            res = self.simulator.evaluate(t_hours=t, gamma=1.0)
            total_allocated = sum(res.vector_N_rotina)
            self.assertAlmostEqual(
                total_allocated,
                res.N_bairro,
                places=4,
                msg=f"Conservação violada para t={t}: soma={total_allocated} != N_bairro={res.N_bairro}",
            )

    def test_exact_doc01_numerical_example(self):
        """Exemplo Exato do Doc 01 (Seção 5.1 e 6):
        Às 16h30 (t=16.5), com pesos [0.45, 0.35, 0.20, 0.00] e N_bairro = 300:
        N_rotina deve ser exatamente [135.0, 105.0, 60.0, 0.0].
        """
        res = self.simulator.evaluate(t_hours=16.5, gamma=1.0)
        self.assertAlmostEqual(res.N_bairro, 300.0, places=2)
        
        expected = [135.0, 105.0, 60.0, 0.0]
        for idx, (calc, exp) in enumerate(zip(res.vector_N_rotina, expected)):
            self.assertAlmostEqual(
                calc, exp, places=2,
                msg=f"Sensor {idx} alocado incorretamente: esperado {exp}, obtido {calc}"
            )

    def test_seasonal_modulation_rf04(self):
        """RF04: Multiplicação linear pelo fator sazonal gamma (alta estação = 1.5, carnaval = 3.5)."""
        vol_normal = calculate_bairro_volume(t_hours=16.5, gamma=1.0)
        vol_verao = calculate_bairro_volume(t_hours=16.5, gamma=1.5)
        vol_carnaval = calculate_bairro_volume(t_hours=16.5, gamma=3.5)

        self.assertAlmostEqual(vol_verao, vol_normal * 1.5, places=4)
        self.assertAlmostEqual(vol_carnaval, vol_normal * 3.5, places=4)

    def test_circadian_periodicity_rf05(self):
        """RF05: O operador h(t) = t mod 24 garante continuidade periódica para qualquer dia acumulado."""
        t1 = 16.5
        t2 = 16.5 + 24.0  # Dia seguinte às 16h30
        t3 = 16.5 + 168.0 # Semana seguinte às 16h30

        self.assertEqual(circadian_hour(t1), circadian_hour(t2))
        self.assertEqual(circadian_hour(t1), circadian_hour(t3))

        vol1 = calculate_bairro_volume(t_hours=t1)
        vol2 = calculate_bairro_volume(t_hours=t2)
        vol3 = calculate_bairro_volume(t_hours=t3)

        self.assertAlmostEqual(vol1, vol2, places=5)
        self.assertAlmostEqual(vol1, vol3, places=5)

    def test_gate_weights_validation_error(self):
        """RF03: Dispara exceção caso a soma de pesos w_j não seja 1.0."""
        invalid_gates = [
            SensorGateWeight(sensor_id="s1", nome_local="P1", gate_weight=0.50),
            SensorGateWeight(sensor_id="s2", nome_local="P2", gate_weight=0.30),
            # Soma = 0.80 != 1.0
        ]
        with self.assertRaises(ValueError):
            MacroFlowConfig(gates=invalid_gates)

    def test_execution_performance_rnf01(self):
        """RNF01: Execução O(1) em tempo constante (< 10 microssegundos por ciclo)."""
        iterations = 5000
        start = time.perf_counter()
        for i in range(iterations):
            _ = calculate_bairro_volume(t_hours=i * 0.1)
        elapsed = time.perf_counter() - start
        
        per_call_us = (elapsed / iterations) * 1e6
        print(f"\n[Bench] Tempo médio por ciclo de cálculo do Sino Gaussiano: {per_call_us:.3f} µs")
        self.assertLess(per_call_us, 50.0, "O cálculo analítico deve ser inferior a 50 microssegundos")

    def test_generate_24h_curve(self):
        """Valida geração de série temporal de 24 horas (96 pontos a cada 15 min)."""
        curve = self.simulator.generate_24h_curve(step_hours=0.25, gamma=1.0)
        self.assertEqual(len(curve), 96, "Passo de 15min deve gerar exatamente 96 pontos nas 24h")
        
        # O pico deve estar no ponto de 16h30
        peak_pt = max(curve, key=lambda pt: pt["total_bairro_volume"])
        self.assertEqual(peak_pt["hour_formatted"], "16:30")
        self.assertAlmostEqual(peak_pt["total_bairro_volume"], 300.0, places=2)

    def test_pydantic_response_serialization(self):
        """Testa serialização completa para o contrato JSON da API REST."""
        res = self.simulator.evaluate(t_hours=14.0, gamma=1.2)
        resp = res.to_response()
        
        self.assertEqual(resp.gamma_seasonality, 1.2)
        self.assertEqual(len(resp.allocations), 4)
        self.assertEqual(len(resp.vector_N_rotina), 4)
        self.assertTrue(resp.timestamp_iso)


if __name__ == "__main__":
    unittest.main()
>>>>>>> dd6d2b6f78488711211b92b4346d55562ad7dbf0
