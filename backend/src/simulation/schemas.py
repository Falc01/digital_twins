"""
Schemas para o subsistema de simulação estocástica de pedestres.

Suporta Pydantic v2 quando disponível (FastAPI) e dataclasses nativas como fallback,
garantindo compatibilidade universal em qualquer interpretador Python 3.11+.
"""

from __future__ import annotations

from typing import List, Optional

try:
    from pydantic import BaseModel, Field, field_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    from dataclasses import dataclass, field

    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self):
            return self.__dict__


if HAS_PYDANTIC:
    class SensorGateWeight(BaseModel):
        """Metadados e peso espacial de um portão de entrada do Pelourinho (Canal A)."""
        sensor_id: str = Field(..., description="Identificador único do nó/sensor")
        nome_local: str = Field(..., description="Nome amigável do logradouro ou portão de entrada")
        gate_weight: float = Field(..., ge=0.0, le=1.0, description="Fração w_j de fluxo atribuída a este portão (w_j in [0, 1])")
        max_capacity: Optional[int] = Field(None, ge=0, description="Lotação máxima individual suportada pelo nó")
        min_baseline: Optional[int] = Field(None, ge=0, description="Piso mínimo de circulação na madrugada")
        poi_type: Optional[str] = Field("GATE", description="Categoria do atrator urbano (GATE, POI, SHOW, IGREJA)")


    class MacroFlowConfig(BaseModel):
        """Parâmetros globais de calibração do modelo circadiano gaussiano (Canal B)."""
        N_max_bairro: int = Field(300, gt=0, description="Lotação máxima acumulada no centro histórico em ápice turístico")
        N_min_bairro: int = Field(15, ge=0, description="Piso de circulação residual da madrugada (03h00)")
        t_peak: float = Field(16.5, ge=0.0, lt=24.0, description="Horário de ápice de visitação (ex: 16.5 = 16h30)")
        sigma: float = Field(3.0, gt=0.0, description="Largura temporal do espalhamento turístico (em horas)")
        T_cycle: float = Field(24.0, gt=0.0, description="Período fundamental circadiano (24h)")
        gates: List[SensorGateWeight] = Field(
            default_factory=lambda: [
                SensorGateWeight(
                    sensor_id="sensor_elevador_lacerda",
                    nome_local="Elevador Lacerda",
                    gate_weight=0.45,
                    max_capacity=150,
                    min_baseline=7,
                    poi_type="GATE",
                ),
                SensorGateWeight(
                    sensor_id="sensor_praca_da_se",
                    nome_local="Praça da Sé",
                    gate_weight=0.35,
                    max_capacity=120,
                    min_baseline=5,
                    poi_type="GATE",
                ),
                SensorGateWeight(
                    sensor_id="sensor_ladeira_do_carmo",
                    nome_local="Ladeira do Carmo",
                    gate_weight=0.20,
                    max_capacity=80,
                    min_baseline=3,
                    poi_type="GATE",
                ),
                SensorGateWeight(
                    sensor_id="sensor_largo_pelourinho",
                    nome_local="Largo do Pelourinho (Interno)",
                    gate_weight=0.00,
                    max_capacity=200,
                    min_baseline=2,
                    poi_type="POI",
                ),
            ],
            description="Lista de nós de sensoriamento com seus respectivos pesos espaciais",
        )

        @field_validator("gates")
        @classmethod
        def validate_weights_sum(cls, gates: List[SensorGateWeight]) -> List[SensorGateWeight]:
            """Garante a conservação de fluxo (RF03: sum(w_j) == 1.0 com tolerância numérica)."""
            if not gates:
                raise ValueError("A lista de portões de entrada não pode ser vazia.")
            total = sum(g.gate_weight for g in gates)
            if abs(total - 1.0) > 1e-4:
                raise ValueError(
                    f"Restrição de Conservação de Fluxo violada (RF03): "
                    f"A soma dos pesos dos portões deve ser 1.0 (encontrado: {total:.4f})."
                )
            return gates


    class MacroFlowRequest(BaseModel):
        """Payload de requisição para avaliação de macro-fluxo (Canal C)."""
        current_time_hours: Optional[float] = Field(
            None,
            description="Instante contínuo t em horas (ex: 16.5 para 16h30). Se nulo, usa o relógio do servidor.",
        )
        gamma_seasonality: float = Field(
            1.0,
            ge=0.1,
            le=10.0,
            description="Fator sazonal gamma (1.0 dias normais, 1.5 verão/alta estação, 3.5 carnaval)",
        )
        config_override: Optional[MacroFlowConfig] = Field(
            None,
            description="Configuração customizada de parâmetros e portões (opcional)",
        )


    class SensorAllocation(BaseModel):
        """Alocação detalhada de pedestres calculada para um sensor individual."""
        sensor_id: str
        nome_local: str
        gate_weight: float
        count_pedestrians: float = Field(..., description="Volume N_rotina,j(t) em indivíduos")


    class MacroFlowResponse(BaseModel):
        """Resposta com o estado do macro-fluxo avaliado (Canal D)."""
        timestamp_iso: str
        circadian_hour: float = Field(..., description="Hora circadiana h(t) in [0, 24)")
        gamma_seasonality: float
        total_bairro_volume: float = Field(..., description="Volume total N_bairro(t) em indivíduos")
        allocations: List[SensorAllocation]
        vector_N_rotina: List[float] = Field(..., description="Vetor N_rotina(t) em formato numérico direto para o barramento")


    class MacroFlowCurvePoint(BaseModel):
        """Ponto amostral da curva circadiana contínua de 24 horas."""
        hour: float
        hour_formatted: str
        total_bairro_volume: float


    class MacroFlowCurveResponse(BaseModel):
        """Série temporal de 24 horas para renderização no dashboard ou gráficos."""
        step_hours: float
        gamma_seasonality: float
        N_max_bairro: int
        N_min_bairro: int
        t_peak: float
        sigma: float
        curve: List[MacroFlowCurvePoint]

else:
    @dataclass
    class SensorGateWeight:
        sensor_id: str
        nome_local: str
        gate_weight: float
        max_capacity: Optional[int] = None
        min_baseline: Optional[int] = None
        poi_type: Optional[str] = "GATE"

    @dataclass
    class MacroFlowConfig:
        N_max_bairro: int = 300
        N_min_bairro: int = 15
        t_peak: float = 16.5
        sigma: float = 3.0
        T_cycle: float = 24.0
        gates: List[SensorGateWeight] = field(
            default_factory=lambda: [
                SensorGateWeight("sensor_elevador_lacerda", "Elevador Lacerda", 0.45, 150, 7, "GATE"),
                SensorGateWeight("sensor_praca_da_se", "Praça da Sé", 0.35, 120, 5, "GATE"),
                SensorGateWeight("sensor_ladeira_do_carmo", "Ladeira do Carmo", 0.20, 80, 3, "GATE"),
                SensorGateWeight("sensor_largo_pelourinho", "Largo do Pelourinho (Interno)", 0.00, 200, 2, "POI"),
            ]
        )

        def __post_init__(self):
            if not self.gates:
                raise ValueError("A lista de portões de entrada não pode ser vazia.")
            total = sum(g.gate_weight for g in self.gates)
            if abs(total - 1.0) > 1e-4:
                raise ValueError(
                    f"Restrição de Conservação de Fluxo violada (RF03): "
                    f"A soma dos pesos dos portões deve ser 1.0 (encontrado: {total:.4f})."
                )

    @dataclass
    class MacroFlowRequest:
        current_time_hours: Optional[float] = None
        gamma_seasonality: float = 1.0
        config_override: Optional[MacroFlowConfig] = None

    @dataclass
    class SensorAllocation:
        sensor_id: str
        nome_local: str
        gate_weight: float
        count_pedestrians: float

    @dataclass
    class MacroFlowResponse:
        timestamp_iso: str
        circadian_hour: float
        gamma_seasonality: float
        total_bairro_volume: float
        allocations: List[SensorAllocation]
        vector_N_rotina: List[float]

    @dataclass
    class MacroFlowCurvePoint:
        hour: float
        hour_formatted: str
        total_bairro_volume: float

    @dataclass
    class MacroFlowCurveResponse:
        step_hours: float
        gamma_seasonality: float
        N_max_bairro: int
        N_min_bairro: int
        t_peak: float
        sigma: float
        curve: List[MacroFlowCurvePoint]
