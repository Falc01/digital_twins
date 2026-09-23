"""
<<<<<<< HEAD
Módulo de Simulação de Dados Sintéticos de Pedestres do Pelourinho.

Herda a arquitetura definida nos Docs 00 a 05 da suíte de dados sintéticos.
"""

from src.simulation.schemas import MacroFlowConfig, MacroFlowRequest, MacroFlowResponse
from src.simulation.macro_flow import (
    calculate_circadian_hour,
    calculate_bairro_population,
    distribute_to_gates,
    calculate_macro_flow,
)

__all__ = [
    "MacroFlowConfig",
    "MacroFlowRequest",
    "MacroFlowResponse",
    "calculate_circadian_hour",
    "calculate_bairro_population",
    "distribute_to_gates",
    "calculate_macro_flow",
=======
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
>>>>>>> dd6d2b6f78488711211b92b4346d55562ad7dbf0
]
