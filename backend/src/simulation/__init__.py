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
    EventRule,
    EventsInjectionConfig,
    EventsInjectionRequest,
    EventNodeBonus,
    EventsInjectionResponse,
    SensorNoiseType,
    SensorNodeMetadata,
    RichardsSaturationConfig,
    SensorNoiseConfig,
    SensorSaturationConfig,
    SensorSaturationRequest,
    SensorTelemetryItem,
    SensorTelemetryResponse,
)
from src.simulation.macro_flow import (
    MacroFlowSimulator,
    MacroFlowResult,
    BairroPopulation,
    calculate_circadian_hour,
    circadian_hour,
    current_system_hour,
    calculate_bairro_population,
    calculate_bairro_volume,
    calculate_bairro_influx,
    normalize_gate_weights,
    distribute_to_gates,
    allocate_gates,
    distribute_influx_to_gates,
    calculate_macro_flow,
)
from src.simulation.markov_circulation import (
    MarkovCirculationSimulator,
    compute_distance_matrix,
    evaluate_hourly_attraction,
    calculate_gate_egress_probability,
    compute_markov_matrix,
    propagate_flow,
    propagate_markov_flow,
)
from src.simulation.events_injection import (
    EventsInjectionSimulator,
    calculate_gaussian_pulse,
    clip_event_magnitude,
    calculate_events_injection,
)
from src.simulation.sensor_saturation import (
    SensorSaturationSimulator,
    calculate_richards_saturation,
    generate_sensor_noise,
    clip_and_discretize_sensor_readings,
    determine_sensor_status,
    simulate_sensor_telemetry,
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
    "BairroPopulation",
    "calculate_circadian_hour",
    "circadian_hour",
    "current_system_hour",
    "calculate_bairro_population",
    "calculate_bairro_volume",
    "calculate_bairro_influx",
    "normalize_gate_weights",
    "distribute_to_gates",
    "allocate_gates",
    "distribute_influx_to_gates",
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
    "calculate_gate_egress_probability",
    "compute_markov_matrix",
    "propagate_flow",
    "propagate_markov_flow",
    # Schemas Injeção de Eventos (Doc 02)
    "EventRule",
    "EventsInjectionConfig",
    "EventsInjectionRequest",
    "EventNodeBonus",
    "EventsInjectionResponse",
    # Motor Injeção de Eventos (Doc 02)
    "EventsInjectionSimulator",
    "calculate_gaussian_pulse",
    "clip_event_magnitude",
    "calculate_events_injection",
    # Schemas Saturação Richards & Ruído IoT (Doc 04)
    "SensorNoiseType",
    "SensorNodeMetadata",
    "RichardsSaturationConfig",
    "SensorNoiseConfig",
    "SensorSaturationConfig",
    "SensorSaturationRequest",
    "SensorTelemetryItem",
    "SensorTelemetryResponse",
    # Motor Saturação Richards & Ruído IoT (Doc 04)
    "SensorSaturationSimulator",
    "calculate_richards_saturation",
    "generate_sensor_noise",
    "clip_and_discretize_sensor_readings",
    "determine_sensor_status",
    "simulate_sensor_telemetry",
]

