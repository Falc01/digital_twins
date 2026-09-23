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

__all__ = [
    "SensorGateWeight",
    "SensorAllocation",
    "MacroFlowConfig",
    "MacroFlowRequest",
    "MacroFlowResponse",
    "MacroFlowCurvePoint",
    "MacroFlowCurveResponse",
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
]
