"""
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
]
