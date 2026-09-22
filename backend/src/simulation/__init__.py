"""
Pacote de Simulação Estocástica de Dados Sintéticos do Gêmeo Digital IoT - UNIFACS.

Implementa a suíte matemática de modelagem de pedestres para o Centro Histórico do Pelourinho,
conforme especificado em docs/explanation/dados_sinteticos/.
"""

from src.simulation.macro_flow import (
    MacroFlowSimulator,
    MacroFlowConfig,
    MacroFlowResult,
    calculate_bairro_volume,
    circadian_hour,
    allocate_gates,
)
from src.simulation.schemas import (
    SensorGateWeight,
    MacroFlowRequest,
    MacroFlowResponse,
    MacroFlowCurvePoint,
    MacroFlowCurveResponse,
)

__all__ = [
    "MacroFlowSimulator",
    "MacroFlowConfig",
    "MacroFlowResult",
    "calculate_bairro_volume",
    "circadian_hour",
    "allocate_gates",
    "SensorGateWeight",
    "MacroFlowRequest",
    "MacroFlowResponse",
    "MacroFlowCurvePoint",
    "MacroFlowCurveResponse",
]
