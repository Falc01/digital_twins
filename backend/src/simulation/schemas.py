"""
Schemas e modelos Pydantic para o Subsistema de Macro-Fluxo (Doc 01).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MacroFlowConfig(BaseModel):
    """
    Parâmetros de configuração e calibração para a curva Gaussiana e distribuição de portões.
    """
    N_max: int = Field(default=300, ge=0, description="Capacidade/lotação máxima global do Pelourinho (pessoas)")
    N_min: int = Field(default=15, ge=0, description="Piso basal de circulação na madrugada (pessoas)")
    t_peak: float = Field(default=16.5, description="Horário central do pico em horas fracionárias (ex: 16.5 = 16h30)")
    sigma: float = Field(default=3.0, gt=0.0, description="Largura temporal / espalhamento da janela turística em horas")
    w_weights: List[float] = Field(
        default_factory=lambda: [0.45, 0.35, 0.20, 0.00],
        description="Vetor de pesos dos portões de entrada (soma estritamente unitária 1.0)"
    )

    @field_validator("w_weights")
    @classmethod
    def validate_weights(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("w_weights não pode ser uma lista vazia.")
        if any(w < 0.0 for w in v):
            raise ValueError("Nenhum peso w_j pode ser negativo.")
        return v


class MacroFlowRequest(BaseModel):
    """
    Payload de requisição para cálculo do ciclo de macro-fluxo.
    """
    current_time_hours: float = Field(..., ge=0.0, description="Tempo contínuo atual de simulação em horas")
    gamma_seasonality: float = Field(default=1.0, ge=0.0, description="Multiplicador sazonal (ex: 1.0 dia normal, 1.5 verão, 3.5 Carnaval)")
    config: Optional[MacroFlowConfig] = Field(default=None, description="Configuração personalizada (opcional)")


class MacroFlowResponse(BaseModel):
    """
    Payload de resposta da simulação de macro-fluxo para o instante t.
    """
    current_time_hours: float = Field(..., description="Timestamp de entrada em horas")
    circadian_hour: float = Field(..., description="Hora do relógio circadiano h(t) em [0, 24)")
    gamma_seasonality: float = Field(..., description="Multiplicador sazonal aplicado")
    N_bairro_total: float = Field(..., description="Lotação global calculada para o Pelourinho N_bairro(t)")
    N_rotina: List[float] = Field(..., description="Vetor N_rotina(t) em indivíduos para cada portão/sensor")
    sensor_ids: Optional[List[str]] = Field(default=None, description="IDs dos sensores correspondentes, se aplicável")
