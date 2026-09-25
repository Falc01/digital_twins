"""
Pacote de Simulação Estocástica de Dados Sintéticos do Gêmeo Digital IoT - UNIFACS.

Implementa a suíte matemática de modelagem de pedestres para o Centro Histórico do Pelourinho,
conforme especificado em docs/explanation/dados_sinteticos/.
"""

from src.simulation.schemas import (
    SensorGateWeight,
    SensorAllocation,
    MacroFlowConfig,
    MacroFlowRequest,
    MacroFlowResponse,
    MacroFlowCurvePoint,
    MacroFlowCurveResponse,
    NodeCoordinate,
    MarkovCirculationConfig,
    MarkovCirculationRequest,
    MarkovNodeFlow,
    MarkovCirculationResponse,
)
from src.simulation.macro_flow import (
    MacroFlowSimulator,
    MacroFlowResult,
    calculate_circadian_hour,
    circadian_hour,
    current_system_hour,
    calculate_bairro_population,
    calculate_bairro_volume,
    normalize_gate_weights,
    distribute_to_gates,
    allocate_gates,
    calculate_macro_flow,
)
from src.simulation.markov_circulation import (
    MarkovCirculationSimulator,
    compute_distance_matrix,
    evaluate_hourly_attraction,
    compute_markov_matrix,
    propagate_flow,
    propagate_markov_flow,
)

__all__ = [
    # Schemas Macro-Fluxo (Doc 01)
    "SensorGateWeight",
    "SensorAllocation",
    "MacroFlowConfig",
    "MacroFlowRequest",
    "MacroFlowResponse",
    "MacroFlowCurvePoint",
    "MacroFlowCurveResponse",
    # Motor Macro-Fluxo (Doc 01)
    "MacroFlowSimulator",
    "MacroFlowResult",
    "calculate_circadian_hour",
    "circadian_hour",
    "current_system_hour",
    "calculate_bairro_population",
    "calculate_bairro_volume",
    "normalize_gate_weights",
    "distribute_to_gates",
    "allocate_gates",
    "calculate_macro_flow",
    # Schemas Circulação Markoviana (Doc 03)
    "NodeCoordinate",
    "MarkovCirculationConfig",
    "MarkovCirculationRequest",
    "MarkovNodeFlow",
    "MarkovCirculationResponse",
    # Motor Circulação Markoviana (Doc 03)
    "MarkovCirculationSimulator",
    "compute_distance_matrix",
    "evaluate_hourly_attraction",
    "compute_markov_matrix",
    "propagate_flow",
    "propagate_markov_flow",
]
