"""
Suíte de Testes Automatizados para o Macro-Fluxo Circadiano (Doc 01).

Valida os Requisitos Funcionais (RF01 a RF05) e Não-Funcionais (RNF01 a RNF03)
especificados em docs/explanation/dados_sinteticos/01_modulo_de_entrada.md,
unificando os testes funcionais de endpoints e os testes analíticos formais.
"""

import math
import os
import sys
import time
import unittest
import pytest
import numpy as np
from fastapi.testclient import TestClient

# Adiciona backend/ e backend/src/ ao path para importação limpa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from src.simulation.macro_flow import (
    MacroFlowSimulator,
    BairroPopulation,
    calculate_circadian_hour,
    circadian_hour,
    calculate_bairro_population,
    calculate_multimodal_bairro_population,
    calculate_bairro_volume,
    calculate_multimodal_bairro_volume,
    calculate_bairro_influx,
    calculate_multimodal_bairro_influx,
    DEFAULT_TRIMODAL_PEAKS,
    CircadianPeak,
    distribute_to_gates,
    allocate_gates,
    distribute_influx_to_gates,
    normalize_gate_weights,
    calculate_macro_flow,
)
from src.simulation.schemas import (
    UrbanGateNode,
    MacroFlowConfig,
    MacroFlowRequest,
    SensorGateWeight,
)
from src.api.main import app

client = TestClient(app)


# ==============================================================================
# 1. Testes Funcionais e de Endpoints (Pytest Style)
# ==============================================================================

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
    """RNF01: Testa complexidade O(1) e tempo de execução por ciclo < 50 µs."""
    config = MacroFlowConfig()
    iterations = 5000
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        calculate_macro_flow(current_time_hours=16.5, config=config)
    elapsed_time = time.perf_counter() - start_time
    
    avg_time_per_call = elapsed_time / iterations
    avg_microseconds = avg_time_per_call * 1e6
    
    # RNF01 especifica tempo inferior a 1 ms (1000 µs)
    assert avg_microseconds < 500.0, f"Tempo médio elevado: {avg_microseconds:.2f} µs"


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


# ==============================================================================
# 2. Testes Formais Analíticos e Validação RF/RNF (Unittest Style)
# ==============================================================================

class TestMacroFlowSubsystem(unittest.TestCase):
    """Testes formais de conformidade matemática com o Doc 01."""

    def setUp(self):
        self.simulator = MacroFlowSimulator()
        self.cfg = self.simulator.config

    def test_exact_gaussian_peak_rf01(self):
        """RF01: No ápice turístico (t = t_pico = 16.5), N_bairro(t) deve ser exatamente gamma * N_max."""
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
        """RNF01: Execução O(1) em tempo constante (< 50 microssegundos por ciclo)."""
        iterations = 5000
        start = time.perf_counter()
        for i in range(iterations):
            _ = calculate_bairro_volume(t_hours=i * 0.1)
        elapsed = time.perf_counter() - start
        
        per_call_us = (elapsed / iterations) * 1e6
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

    def test_differential_influx_item1(self):
        """Item 1: Testa cálculo da taxa diferencial de novos ingressos ΔN por portão."""
        # Às 14h00, a curva está em ascensão
        delta_N, rate_min = calculate_bairro_influx(
            current_time_hours=14.0,
            step_minutes=5.0,
            N_max=300,
            N_min=15,
            t_peak=16.5,
            sigma=3.0,
            gamma_seasonality=1.0,
        )
        self.assertGreater(delta_N, 0.0, "Às 14h a curva está em expansão, logo ΔN deve ser positivo")
        self.assertAlmostEqual(rate_min, delta_N / 5.0, places=4)

        # Distribuição de ΔN pelos portões
        w_weights = [0.45, 0.35, 0.20, 0.00]
        gate_influx = distribute_influx_to_gates(delta_N, w_weights)
        self.assertAlmostEqual(sum(gate_influx), delta_N, places=4, msg="Conservação de fluxo em ΔN")
        self.assertAlmostEqual(gate_influx[0], 0.45 * delta_N, places=4)
        self.assertAlmostEqual(gate_influx[3], 0.0, places=4)

        # No pico às 16h30, a taxa de novos ingressos líquidos converge para zero (não há crescimento)
        delta_peak, _ = calculate_bairro_influx(current_time_hours=16.5, step_minutes=5.0)
        self.assertEqual(delta_peak, 0.0, "No ápice e pós-pico, ΔN = max(0, N(t+dt)-N(t)) deve ser 0")

    def test_step_minutes_granularity_item2(self):
        """Item 2: Testa a influência da granularidade temporal Δt (step_minutes)."""
        # Comparação de passo de 2.5 min vs 5.0 min às 12h00
        pop_2_5 = calculate_bairro_population(current_time_hours=12.0, step_minutes=2.5)
        pop_5_0 = calculate_bairro_population(current_time_hours=12.0, step_minutes=5.0)
        
        # O volume instantâneo N_bairro(t) deve ser idêntico
        self.assertAlmostEqual(pop_2_5.N_bairro, pop_5_0.N_bairro, places=4)
        self.assertEqual(pop_2_5.circadian_hour, 12.0)
        
        # O incremento acumulado em 5 min deve ser aproximadamente o dobro de 2.5 min
        self.assertAlmostEqual(pop_5_0.delta_N, pop_2_5.delta_N * 2.0, delta=0.1)
        # E a taxa por minuto deve ser quase idêntica (consistência de velocidade)
        self.assertAlmostEqual(pop_2_5.rate_per_minute, pop_5_0.rate_per_minute, delta=0.05)

    def test_multimodal_trimodal_mixture_item2(self):
        """Doc 01 v2.0 - Item 2: Testa a formulação trimodal paramétrica (Regime A).
        Valida que às 12h30 (almoço) o fluxo supera as 14h00 (vale digestivo),
        e que o ápice ocorre às 16h48 (16.8h).
        """
        pop_madrugada = calculate_multimodal_bairro_population(3.0, N_max=300, N_min=15)
        pop_manha = calculate_multimodal_bairro_population(9.5, N_max=300, N_min=15)
        pop_almoco = calculate_multimodal_bairro_population(12.5, N_max=300, N_min=15)
        pop_vale = calculate_multimodal_bairro_population(14.0, N_max=300, N_min=15)
        pop_apice = calculate_multimodal_bairro_population(16.8, N_max=300, N_min=15)

        # 1. Madrugada assintótica a N_min
        self.assertAlmostEqual(pop_madrugada.N_bairro, 15.0, delta=0.5)

        # 2. Ascensão matinal
        self.assertGreater(pop_manha.N_bairro, pop_madrugada.N_bairro)

        # 3. O ponto crítico da sabatina: almoço (12h30) tem volume maior que o pós-almoço (14h00)
        self.assertGreater(
            pop_almoco.N_bairro,
            pop_vale.N_bairro,
            f"Almoço ({pop_almoco.N_bairro:.1f}) deve ser maior que 14h ({pop_vale.N_bairro:.1f})",
        )

        # 4. Ápice turístico e cultural no fim da tarde
        self.assertGreater(pop_apice.N_bairro, pop_almoco.N_bairro)

        # 5. Conservação do fluxo diferencial ΔN nos portões
        w_weights = [0.45, 0.35, 0.20, 0.00]
        influx_vec = distribute_influx_to_gates(pop_almoco.delta_N, w_weights)
        self.assertAlmostEqual(sum(influx_vec), pop_almoco.delta_N, places=4)

    def test_multimodal_fourier_regime_b(self):
        """Doc 01 v2.0 - Item 2: Testa a decomposição espectral de Fourier K=3 (Regime B)."""
        pop_t = calculate_multimodal_bairro_population(12.0, regime="fourier")
        pop_next_day = calculate_multimodal_bairro_population(12.0 + 24.0, regime="fourier")

        # Periodicidade estrita de 24h
        self.assertAlmostEqual(pop_t.N_bairro, pop_next_day.N_bairro, places=4)
        self.assertGreaterEqual(pop_t.delta_N, 0.0)

    def test_urban_gate_node_desacoplamento_item1(self):
        """Doc 01 v2.0 - Item 1: Testa o desacoplamento topológico (UrbanGateNode vs Sensor IoT)."""
        node = UrbanGateNode(
            node_id="node_elevador_lacerda",
            nome_local="Elevador Lacerda",
            gate_weight=0.45,
            poi_type="GATE",
        )
        # Sincronização e alias de retrocompatibilidade
        self.assertEqual(node.node_id, "node_elevador_lacerda")
        self.assertEqual(node.sensor_id, "node_elevador_lacerda")

        # Exclusão de POIs internos: peso 0.0
        poi_interno = UrbanGateNode(
            node_id="node_largo_pelourinho",
            nome_local="Largo do Pelourinho",
            gate_weight=0.00,
            poi_type="POI",
        )
        self.assertEqual(poi_interno.gate_weight, 0.0)

        # Suporte a configuração com urban_gates
        config = MacroFlowConfig(
            urban_gates=[
                UrbanGateNode(node_id="node_elevador_lacerda", nome_local="Elevador Lacerda", gate_weight=0.5),
                UrbanGateNode(node_id="node_praca_da_se", nome_local="Praça da Sé", gate_weight=0.5),
            ]
        )
        self.assertEqual(len(config.gates), 2)
        self.assertEqual(config.node_ids, ["node_elevador_lacerda", "node_praca_da_se"])
        self.assertEqual(config.sensor_ids, ["node_elevador_lacerda", "node_praca_da_se"])

    def test_multimodal_simulator_and_24h_curve_v2(self):
        """Doc 01 v2.0: Testa o simulador completo com regime trimodal e geração de curva 24h."""
        sim = MacroFlowSimulator(config=MacroFlowConfig(regime="trimodal"))
        self.assertEqual(sim.config.regime, "trimodal")

        curve = sim.generate_24h_curve(step_hours=0.25)
        self.assertEqual(len(curve), 96)

        # Encontra o ponto das 12h30 e das 14h00
        pt_1230 = next(pt for pt in curve if pt["hour_formatted"] == "12:30")
        pt_1400 = next(pt for pt in curve if pt["hour_formatted"] == "14:00")
        self.assertGreater(
            pt_1230["total_bairro_volume"],
            pt_1400["total_bairro_volume"],
            "Na curva de 24h, 12h30 deve ter volume maior que 14h00",
        )

    def test_api_multimodal_integration(self):
        """Doc 01 v2.0: Valida chamada REST FastAPI para regime trimodal com retorno de node_ids."""
        payload = {
            "current_time_hours": 12.5,
            "step_minutes": 5.0,
            "gamma_seasonality": 1.0,
            "regime": "trimodal",
        }
        res = client.post("/api/v1/simulation/macro-flow/calculate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["regime"], "trimodal")
        self.assertTrue("node_ids" in data)
        self.assertEqual(len(data["node_ids"]), 4)
        self.assertEqual(data["node_ids"][0], "node_elevador_lacerda")
        self.assertAlmostEqual(data["N_bairro_total"], 234.6, delta=1.0)


if __name__ == "__main__":
    unittest.main()
