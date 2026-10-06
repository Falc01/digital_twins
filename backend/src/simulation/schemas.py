"""
Schemas e modelos Pydantic para o Subsistema de Macro-Fluxo (Doc 01).

Suporta validação de tipos via Pydantic v2 com compatibilidade para o motor analítico,
rotas da API FastAPI e barramento de dados sintéticos do Pelourinho.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

DEFAULT_SENSOR_ID_TO_INDEX = {
    "sensor_elevador_lacerda": 0,
    "elevador_lacerda": 0,
    "sensor_praca_da_se": 1,
    "praca_da_se": 1,
    "sensor_ladeira_do_carmo": 2,
    "ladeira_do_carmo": 2,
    "sensor_largo_pelourinho": 3,
    "largo_pelourinho": 3,
    "sensor_terreiro_jesus": 4,
    "terreiro_jesus": 4,
    "sensor_igreja_rosario": 2,
    "igreja_rosario": 2,
    "sensor_rosario_dos_pretos": 2,
    "rosario_dos_pretos": 2,
}


def resolve_sensor_index(value: Any) -> Optional[int]:
    """Resolve um identificador textual de sensor para o índice numérico correspondente."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw_text = value.strip()
        if not raw_text:
            return None
        if raw_text.isdigit():
            return int(raw_text)

        normalized = re.sub(r"[^a-z0-9]+", "_", raw_text.lower()).strip("_")
        if normalized in DEFAULT_SENSOR_ID_TO_INDEX:
            return DEFAULT_SENSOR_ID_TO_INDEX[normalized]
        return DEFAULT_SENSOR_ID_TO_INDEX.get(normalized.replace("sensor_", ""))
    return None


class SensorGateWeight(BaseModel):
    """Metadados e peso espacial de um portão de entrada do Pelourinho (Canal A)."""
    sensor_id: str = Field(..., description="Identificador único do nó/sensor")
    nome_local: str = Field(..., description="Nome amigável do logradouro ou portão de entrada")
    gate_weight: float = Field(..., ge=0.0, le=1.0, description="Fração w_j de fluxo atribuída a este portão (w_j in [0, 1])")
    max_capacity: Optional[int] = Field(None, ge=0, description="Lotação máxima individual suportada pelo nó")
    min_baseline: Optional[int] = Field(None, ge=0, description="Piso mínimo de circulação na madrugada")
    poi_type: Optional[str] = Field("GATE", description="Categoria do atrator urbano (GATE, POI, SHOW, IGREJA)")


class MacroFlowConfig(BaseModel):
    """
    Parâmetros globais de calibração do modelo circadiano gaussiano e portões de entrada (Canais A e B).
    """
    N_max: int = Field(default=300, ge=0, description="Capacidade/lotação máxima global do Pelourinho (pessoas)")
    N_min: int = Field(default=15, ge=0, description="Piso basal de circulação na madrugada (pessoas)")
    N_max_bairro: int = Field(default=300, ge=0, description="Alias para N_max")
    N_min_bairro: int = Field(default=15, ge=0, description="Alias para N_min")
    t_peak: float = Field(default=16.5, ge=0.0, lt=24.0, description="Horário central do pico em horas fracionárias (ex: 16.5 = 16h30)")
    sigma: float = Field(default=3.0, gt=0.0, description="Largura temporal / espalhamento da janela turística em horas")
    T_cycle: float = Field(default=24.0, gt=0.0, description="Período fundamental circadiano (24h)")
    step_minutes: float = Field(default=5.0, gt=0.0, description="Intervalo temporal do ciclo de simulação em minutos (Δt)")
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
    w_weights: List[float] = Field(
        default_factory=lambda: [0.45, 0.35, 0.20, 0.00],
        description="Vetor de pesos dos portões de entrada (soma estritamente unitária 1.0)",
    )

    @property
    def step_hours(self) -> float:
        """Retorna o passo temporal Δt convertido em horas."""
        return self.step_minutes / 60.0

    @model_validator(mode="before")
    @classmethod
    def harmonize_fields(cls, values: dict) -> dict:
        if isinstance(values, dict):
            # Sincroniza aliases N_max / N_max_bairro
            if "N_max_bairro" in values and "N_max" not in values:
                values["N_max"] = values["N_max_bairro"]
            elif "N_max" in values and "N_max_bairro" not in values:
                values["N_max_bairro"] = values["N_max"]

            # Sincroniza aliases N_min / N_min_bairro
            if "N_min_bairro" in values and "N_min" not in values:
                values["N_min"] = values["N_min_bairro"]
            elif "N_min" in values and "N_min_bairro" not in values:
                values["N_min_bairro"] = values["N_min"]

            # Sincroniza w_weights a partir de gates se gates foi fornecido explicitamente
            if "gates" in values and "w_weights" not in values:
                values["w_weights"] = [g.gate_weight if hasattr(g, "gate_weight") else g["gate_weight"] for g in values["gates"]]
            elif "w_weights" in values and "gates" not in values:
                # Valida w_weights
                w_list = values["w_weights"]
                if any(w < 0.0 for w in w_list):
                    raise ValueError("Nenhum peso w_j pode ser negativo.")
        return values

    @model_validator(mode="after")
    def validate_weights(self) -> "MacroFlowConfig":
        if not self.gates:
            raise ValueError("A lista de portões de entrada não pode ser vazia.")
        total = sum(g.gate_weight for g in self.gates)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"Restrição de Conservação de Fluxo violada (RF03): "
                f"A soma dos pesos dos portões deve ser 1.0 (encontrado: {total:.4f})."
            )
        # Mantém w_weights espelhado com os gates
        self.w_weights = [g.gate_weight for g in self.gates]
        return self


class MacroFlowRequest(BaseModel):
    """
    Payload de requisição para cálculo do ciclo de macro-fluxo (Canal C).
    """
    current_time_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Tempo contínuo atual de simulação em horas (se omitido, usa hora atual do sistema)",
    )
    step_minutes: Optional[float] = Field(
        default=5.0,
        gt=0.0,
        description="Duração do passo de tempo em minutos (Δt) para cálculo diferencial",
    )
    gamma_seasonality: float = Field(
        default=1.0,
        ge=0.0,
        description="Multiplicador sazonal (ex: 1.0 dia normal, 1.5 verão, 3.5 Carnaval)",
    )
    config: Optional[MacroFlowConfig] = Field(default=None, description="Configuração personalizada (opcional)")
    config_override: Optional[MacroFlowConfig] = Field(default=None, description="Alias para config")
    use_incremental: Optional[bool] = Field(
        default=False,
        description="Se True, atribui a N_rotina os novos ingressos incrementais ΔN_rotina(t) em vez do volume acumulado",
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_config(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if values.get("config_override") and not values.get("config"):
                values["config"] = values["config_override"]
            elif values.get("config") and not values.get("config_override"):
                values["config_override"] = values["config"]
        return values


class SensorAllocation(BaseModel):
    """Alocação detalhada de pedestres calculada para um sensor individual."""
    sensor_id: str
    nome_local: str
    gate_weight: float
    count_pedestrians: float = Field(..., description="Volume N_rotina,j(t) em indivíduos")
    incremental_pedestrians: float = Field(default=0.0, description="Taxa/volume incremental de novos ingressos ΔN_rotina,j(t) no passo Δt")
    delta_pedestrians: float = Field(default=0.0, description="Alias para incremental_pedestrians")

    @model_validator(mode="before")
    @classmethod
    def sync_allocation_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "incremental_pedestrians" in values and "delta_pedestrians" not in values:
                values["delta_pedestrians"] = values["incremental_pedestrians"]
            elif "delta_pedestrians" in values and "incremental_pedestrians" not in values:
                values["incremental_pedestrians"] = values["delta_pedestrians"]
        return values


class MacroFlowResponse(BaseModel):
    """
    Payload de resposta da simulação de macro-fluxo para o instante t (Canal D).
    """
    timestamp_iso: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_time_hours: float = Field(..., description="Timestamp de entrada em horas")
    circadian_hour: float = Field(..., description="Hora do relógio circadiano h(t) em [0, 24)")
    step_minutes: float = Field(default=5.0, description="Duração do ciclo temporal de simulação Δt em minutos")
    gamma_seasonality: float = Field(..., description="Multiplicador sazonal aplicado")
    N_bairro_total: float = Field(..., description="Lotação global calculada para o Pelourinho N_bairro(t)")
    total_bairro_volume: float = Field(..., description="Alias para N_bairro_total")
    delta_N_bairro: float = Field(default=0.0, description="Variação positiva incremental de novos ingressos no bairro ΔN")
    rate_pedestrians_per_minute: float = Field(default=0.0, description="Taxa de influxo de novos pedestres por minuto no bairro")
    N_rotina: List[float] = Field(..., description="Vetor N_rotina(t) em indivíduos para cada portão/sensor")
    vector_N_rotina: List[float] = Field(..., description="Alias para N_rotina")
    delta_N_rotina: List[float] = Field(default_factory=list, description="Vetor de influxo incremental ΔN_rotina(t) para cada portão no passo Δt")
    vector_delta_N_rotina: List[float] = Field(default_factory=list, description="Alias para delta_N_rotina")
    allocations: List[SensorAllocation] = Field(default_factory=list, description="Lista de alocações por sensor")
    sensor_ids: Optional[List[str]] = Field(default=None, description="IDs dos sensores correspondentes")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            # Sincroniza total
            if "total_bairro_volume" in values and "N_bairro_total" not in values:
                values["N_bairro_total"] = values["total_bairro_volume"]
            elif "N_bairro_total" in values and "total_bairro_volume" not in values:
                values["total_bairro_volume"] = values["N_bairro_total"]

            # Sincroniza vetor N_rotina
            if "vector_N_rotina" in values and "N_rotina" not in values:
                values["N_rotina"] = values["vector_N_rotina"]
            elif "N_rotina" in values and "vector_N_rotina" not in values:
                values["vector_N_rotina"] = values["N_rotina"]

            # Sincroniza vetor delta_N_rotina
            if "vector_delta_N_rotina" in values and "delta_N_rotina" not in values:
                values["delta_N_rotina"] = values["vector_delta_N_rotina"]
            elif "delta_N_rotina" in values and "vector_delta_N_rotina" not in values:
                values["vector_delta_N_rotina"] = values["delta_N_rotina"]
        return values


class MacroFlowCurvePoint(BaseModel):
    """Ponto amostral da curva circadiana contínua de 24 horas."""
    hour: float
    hour_formatted: str
    total_bairro_volume: float


class MacroFlowCurveResponse(BaseModel):
    """Série temporal de 24 horas para renderização no dashboard ou gráficos Leaflet."""
    step_hours: float
    gamma_seasonality: float
    N_max_bairro: int
    N_min_bairro: int
    t_peak: float
    sigma: float
    curve: List[MacroFlowCurvePoint]


# ==============================================================================
# Schemas para o Subsistema de Circulação de Markov & POIs (Doc 03)
# ==============================================================================

class NodeCoordinate(BaseModel):
    """
    Coordenada geográfica e metadados de atratividade de um nó de rede (Canal A e B).
    """
    sensor_id: str = Field(..., description="ID único do sensor")
    nome_local: str = Field(..., description="Nome amigável do POI ou logradouro")
    lat: float = Field(..., description="Latitude em graus decimais (WGS84)")
    lng: float = Field(..., description="Longitude em graus decimais (WGS84)")
    poi_type: str = Field(default="POI", description="Categoria: GATE, POI, IGREJA, SHOW")
    base_attraction: float = Field(default=1.0, ge=0.01, description="Peso de atratividade basal alpha_j > 0")
    gate_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Peso de entrada w_j (se portão)")
    max_capacity: int = Field(default=150, gt=0, description="Capacidade máxima de suporte")


class MarkovCirculationConfig(BaseModel):
    """
    Parâmetros de configuração e calibração espacial da rede de Markov (Canal B).
    """
    lambda_decay: float = Field(
        default=0.015,
        gt=0.0,
        description="Taxa de decaimento espacial por metro lambda_d (padrão 0.015 m^-1)",
    )
    retention_bias: float = Field(
        default=1.0,
        gt=0.0,
        description="Viés basal de permanência no mesmo nó (termo diagonal P_ii)",
    )
    step_minutes: float = Field(
        default=5.0,
        gt=0.0,
        description="Duração do ciclo/passo temporal de simulação Δt em minutos",
    )
    dwell_time_minutes: float = Field(
        default=20.0,
        gt=0.0,
        description="Tempo médio estimado de permanência τ_dwell em um logradouro para modelagem de inércia",
    )
    use_inertia: bool = Field(
        default=False,
        description="Ativa inércia temporal de retenção via combinação convexa ρ(Δt) com a matriz gravitacional",
    )
    enable_egress: bool = Field(
        default=False,
        description="Habilita cadeia de Markov aberta com probabilidade de egress (saída do bairro) nos portões",
    )
    base_egress_rate: float = Field(
        default=0.08,
        ge=0.0,
        le=1.0,
        description="Taxa basal horária de dispersão/saída do Pelourinho nos nós do tipo GATE",
    )
    category_attractions: dict[str, float] = Field(
        default_factory=lambda: {
            "GATE": 1.0,
            "POI": 1.5,
            "IGREJA": 1.8,
            "SHOW": 2.5,
        },
        description="Multiplicadores basais por tipo de atrator urbano",
    )
    nodes: List[NodeCoordinate] = Field(
        default_factory=lambda: [
            NodeCoordinate(
                sensor_id="sensor_elevador_lacerda",
                nome_local="Elevador Lacerda",
                lat=-12.97330,
                lng=-38.51260,
                poi_type="GATE",
                base_attraction=1.0,
                gate_weight=0.45,
                max_capacity=150,
            ),
            NodeCoordinate(
                sensor_id="sensor_praca_da_se",
                nome_local="Praça da Sé",
                lat=-12.97380,
                lng=-38.51090,
                poi_type="GATE",
                base_attraction=1.2,
                gate_weight=0.35,
                max_capacity=120,
            ),
            NodeCoordinate(
                sensor_id="sensor_ladeira_do_carmo",
                nome_local="Ladeira do Carmo",
                lat=-12.96980,
                lng=-38.50800,
                poi_type="GATE",
                base_attraction=0.9,
                gate_weight=0.20,
                max_capacity=80,
            ),
            NodeCoordinate(
                sensor_id="sensor_largo_pelourinho",
                nome_local="Largo do Pelourinho",
                lat=-12.97180,
                lng=-38.50850,
                poi_type="SHOW",
                base_attraction=2.5,
                gate_weight=0.00,
                max_capacity=250,
            ),
            NodeCoordinate(
                sensor_id="sensor_terreiro_jesus",
                nome_local="Terreiro de Jesus",
                lat=-12.97310,
                lng=-38.50970,
                poi_type="IGREJA",
                base_attraction=1.8,
                gate_weight=0.00,
                max_capacity=200,
            ),
        ],
        description="Rede de nós de monitoramento do Pelourinho com coordenadas e atratores",
    )

    @model_validator(mode="after")
    def validate_nodes_not_empty(self) -> "MarkovCirculationConfig":
        if not self.nodes or len(self.nodes) < 2:
            raise ValueError("A rede de circulação de Markov precisa de pelo menos 2 nós.")
        return self


class MarkovCirculationRequest(BaseModel):
    """
    Payload de requisição para cálculo do ciclo de circulação e redistribuição (Canal C / D).
    """
    current_state_N: Optional[List[float]] = Field(
        default=None,
        description="Vetor N(t) de pedestres no ciclo anterior. Se omitido, utiliza N_rotina do Doc 01.",
    )
    current_time_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Timestamp contínuo t em horas (se omitido, usa relógio do servidor)",
    )
    gamma_seasonality: float = Field(
        default=1.0,
        ge=0.0,
        description="Multiplicador sazonal da época",
    )
    step_minutes: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Passo temporal da simulação Δt em minutos (se omitido, usa config)",
    )
    enable_egress: Optional[bool] = Field(
        default=None,
        description="Habilitar probabilidade de saída do bairro pelos portões (Cadeia Aberta)",
    )
    use_inertia: Optional[bool] = Field(
        default=None,
        description="Habilitar inércia de permanência temporal ρ(Δt)",
    )
    include_raw_flow: bool = Field(
        default=False,
        description="Compor automaticamente a Massa de Fluxo Físico Bruto N_bruto = N_prop + delta_N + E para o Doc 04",
    )
    delta_N_rotina: Optional[List[float]] = Field(
        default=None,
        description="Vetor opcional de novos ingressos nos portões (Doc 01). Se omitido e include_raw_flow=True, calcula via Doc 01.",
    )
    vector_E_eventos: Optional[List[float]] = Field(
        default=None,
        description="Vetor opcional de pulsos de eventos (Doc 02). Se omitido e include_raw_flow=True, calcula via Doc 02.",
    )
    config: Optional[MarkovCirculationConfig] = Field(
        default=None,
        description="Configuração personalizada de nós e distâncias (opcional)",
    )
    alpha_override: Optional[List[float]] = Field(
        default=None,
        description="Vetor explícito de atratividade alpha_j(t) de dimensão J (opcional)",
    )


class MarkovNodeFlow(BaseModel):
    """Detalhamento de fluxo migratório em um nó individual da malha urbana."""
    sensor_id: str
    nome_local: str
    poi_type: str
    initial_pedestrians: float = Field(..., description="Pessoas no sensor no início do ciclo N_i(t)")
    retained_pedestrians: float = Field(..., description="Pessoas que permaneceram no mesmo local (P_ii * N_i)")
    inflow_pedestrians: float = Field(..., description="Pessoas recebidas de outros sensores vizinhos")
    outflow_pedestrians: float = Field(..., description="Pessoas que migraram para outros sensores")
    egress_pedestrians: float = Field(default=0.0, description="Pessoas que saíram do bairro por este nó (se GATE)")
    final_propagated_pedestrians: float = Field(..., description="Lotação propagada final N_j,propagado(t+1)")


class MarkovCirculationResponse(BaseModel):
    """
    Payload de resposta da propagação de circulação de rede de Markov (Canal D).
    """
    timestamp_iso: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_time_hours: float
    circadian_hour: float
    gamma_seasonality: float
    step_minutes: float = Field(default=5.0, description="Passo temporal Δt considerado no ciclo em minutos")
    egress_enabled: bool = Field(default=False, description="Indica se a taxa de egress nos portões esteve ativa")
    total_initial_pedestrians: float
    total_propagated_pedestrians: float
    total_egress_pedestrians: float = Field(default=0.0, description="Total de pedestres que saíram do bairro neste ciclo")
    vector_N_propagado: List[float] = Field(
        ...,
        description="Vetor N_propagado(t+1) em indivíduos para transmissão direta ao barramento",
    )
    vector_N_egress: List[float] = Field(
        default_factory=list,
        description="Vetor com quantidade de pessoas que saíram por cada portão neste ciclo",
    )
    vector_N_bruto: Optional[List[float]] = Field(
        default=None,
        description="Massa de Fluxo Físico Bruto N_bruto = N_propagado + delta_N_rotina + E_eventos pronta para o Doc 04",
    )
    transition_matrix: List[List[float]] = Field(
        ...,
        description="Matriz estocástica de transição P(t) de dimensão J x J",
    )
    attraction_vector: List[float] = Field(
        ...,
        description="Vetor de atratividades instantâneas alpha_j(t)",
    )
    node_flows: List[MarkovNodeFlow]
    sensor_ids: List[str]
    conservation_error: float = Field(
        default=0.0,
        description="Erro absoluto de balanço |(N_prop + N_egress) - N_ini|",
    )


# ==============================================================================
# Schemas para Subsistema de Injeção Dinâmica de Eventos (Doc 02)
# ==============================================================================

class EventRule(BaseModel):
    """
    Especificação de Evento Cultural / Espectáculo (Modo 1 e Modo 2).
    """
    event_id: str = Field(..., description="Identificador único do evento ou regra de calendário")
    sensor_index: Optional[int] = Field(None, ge=0, description="Índice do nó/sensor afetado na matriz (0..J-1)")
    sensor_alvo: Optional[str] = Field(None, description="ID do sensor ou nome do local (opcional)")
    peak_hour: float = Field(..., ge=0.0, lt=24.0, description="Horário tau_jm de pico máximo em horas fracionárias")
    duration_hours: float = Field(..., gt=0.0, description="Largura/dispersão temporal sigma_jm em horas")
    magnitude: float = Field(..., ge=0.0, description="Amplitude A_jm de lotação agregada pelo evento")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Dia da semana (0=Segunda, 6=Domingo) para eventos recorrentes")
    is_recurring: bool = Field(default=False, description="Indica se é uma regra semanal recorrente (Modo 1)")

    @model_validator(mode="before")
    @classmethod
    def harmonize_event_fields(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "regra_id" in values and "event_id" not in values:
                values["event_id"] = values["regra_id"]
            if "hora_pico" in values and "peak_hour" not in values:
                values["peak_hour"] = values["hora_pico"]
            if "duracao_h" in values and "duration_hours" not in values:
                values["duration_hours"] = values["duracao_h"]
            if "sensor_id" in values and "sensor_alvo" not in values:
                values["sensor_alvo"] = values["sensor_id"]
            if "dia_semana" in values and "day_of_week" not in values:
                values["day_of_week"] = values["dia_semana"]
            if "sensor_index" in values and isinstance(values["sensor_index"], str):
                values["sensor_index"] = resolve_sensor_index(values["sensor_index"])
        return values

    @model_validator(mode="after")
    def resolve_sensor_alias(self) -> "EventRule":
        if self.sensor_index is None:
            sensor_ref = self.sensor_alvo
            if sensor_ref is None:
                raise ValueError("Evento precisa de sensor_index ou sensor_alvo/sensor_id válido.")
            resolved_index = resolve_sensor_index(sensor_ref)
            if resolved_index is None:
                raise ValueError(f"sensor_alvo '{sensor_ref}' não corresponde a um sensor conhecido do Pelourinho.")
            self.sensor_index = resolved_index
        return self


class EventsInjectionConfig(BaseModel):
    """
    Configuração global do subsistema de injeção de eventos.
    """
    enable_mode1: bool = Field(default=True, description="Habilita Calendário Cultural Fixo (Modo 1)")
    enable_mode2: bool = Field(default=True, description="Habilita Agenda de Eventos Pontuais (Modo 2)")
    enable_mode3: bool = Field(default=True, description="Habilita Eventos Estocásticos Monte Carlo (Modo 3)")
    monte_carlo_prob: float = Field(default=0.15, ge=0.0, le=1.0, description="Probabilidade p de manifestação espontânea à tarde")
    min_capacity_ratio: float = Field(default=0.30, ge=0.0, le=1.0, description="Piso mínimo de corte de capacidade (0.30 * N_max)")
    max_capacity_ratio: float = Field(default=0.95, ge=0.0, le=1.0, description="Teto máximo de trava de capacidade (0.95 * N_max)")


class EventsInjectionRequest(BaseModel):
    """
    Payload de requisição para cálculo do vetor de injeção de eventos E(t) (Canal C).
    """
    current_time_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Timestamp contínuo t em horas (se omitido, usa horário atual do sistema)",
    )
    day_of_week: Optional[int] = Field(
        default=None,
        ge=0,
        le=6,
        description="Dia da semana 0..6 (se omitido, usa dia atual do sistema)",
    )
    node_capacities: Optional[List[int]] = Field(
        default=None,
        description="Vetor com capacidade máxima N_j_max de cada nó/sensor (Canal A)",
    )
    events_registry: Optional[List[EventRule]] = Field(
        default=None,
        description="Lista de eventos agendados para avaliação (Canal C)",
    )
    enable_mode1: bool = Field(default=True, description="Ativar Modo 1 (Calendário Cultural Fixo)")
    enable_mode2: bool = Field(default=True, description="Ativar Modo 2 (Agenda Externa Pontual)")
    enable_mode3: bool = Field(default=True, description="Ativar Modo 3 (Monte Carlo Estocástico)")


class EventNodeBonus(BaseModel):
    """Bônus de público injetado em um nó específico."""
    sensor_id: str
    sensor_index: int
    event_bonus: float = Field(..., description="Volume E_j(t) de público injetado pelo evento (indivíduos)")
    node_capacity: int = Field(..., description="Capacidade máxima N_j_max do nó")
    active_events_count: int = Field(..., description="Número de eventos ativos impactando este nó")


class EventsInjectionResponse(BaseModel):
    """
    Payload de resposta contendo o vetor de injeção de eventos E(t) (Canal D).
    """
    timestamp_iso: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_time_hours: float
    day_of_week: int
    vector_E_eventos: List[float] = Field(
        ...,
        description="Vetor nodal E(t) em array float64 de tamanho J para transmissão ao Doc 04",
    )
    node_bonuses: List[EventNodeBonus]
    active_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lista de eventos que contribuíram ativamente com E_j > 0.01",
    )


# ==============================================================================
# Schemas para Saturação de Richards, Ruído Instrumental IoT & Telemetria (Doc 04)
# ==============================================================================

class SensorNoiseType(str, Enum):
    """Métodos de perturbação estocástica instrumental dos sensores IoT (RF03)."""
    NONE = "NONE"
    UNIFORM = "UNIFORM"
    GAUSSIAN = "GAUSSIAN"
    ORNSTEIN_UHLENBECK = "ORNSTEIN_UHLENBECK"
    OU = "OU"


class SensorNodeMetadata(BaseModel):
    """Metadados físicos e espaciais de um nó de sensoriamento IoT."""
    sensor_id: str = Field(..., description="Identificador único do nó/sensor")
    nome_local: str = Field(..., description="Nome amigável do logradouro ou POI monitorado")
    max_capacity: int = Field(default=150, gt=0, description="Teto físico intransponível N_j,max (Canal A)")
    kappa: float = Field(default=0.08, gt=0.0, description="Declividade logística de Richards kappa_j")
    inflection_point: Optional[float] = Field(
        default=None,
        description="Ponto médio lambda_0,j. Se omitido, utiliza max_capacity * 0.5",
    )
    lat: Optional[float] = Field(default=None, description="Latitude WGS84")
    lng: Optional[float] = Field(default=None, description="Longitude WGS84")
    area_m2: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Área de cobertura em m² para cálculo de densidade de pedestres",
    )


class RichardsSaturationConfig(BaseModel):
    """Parâmetros da barreira de capacidade logística de Richards (Canal B)."""
    kappa: float = Field(
        default=0.08,
        gt=0.0,
        description="Declividade da função sigmoide logística kappa (padrão 0.08 h^-1)",
    )
    inflection_ratio: float = Field(
        default=0.5,
        gt=0.0,
        le=1.0,
        description="Fração de N_max onde ocorre a inflexão lambda_0 = N_max * inflection_ratio",
    )
    zero_anchored: bool = Field(
        default=True,
        description="Garante que S_adj(0) = 0, eliminando pedestres fantasmas em ruas vazias",
    )


class SensorNoiseConfig(BaseModel):
    """Parâmetros dos métodos de ruído instrumental estocástico (RF03)."""
    method: SensorNoiseType = Field(
        default=SensorNoiseType.ORNSTEIN_UHLENBECK,
        description="Método de ruído ativo: NONE, UNIFORM, GAUSSIAN ou ORNSTEIN_UHLENBECK",
    )
    uniform_range_R: float = Field(
        default=3.0,
        ge=0.0,
        description="Semi-intervalo R para ruído uniforme U(-R, +R) em pessoas (padrão 3.0)",
    )
    gaussian_sigma: float = Field(
        default=2.5,
        ge=0.0,
        description="Desvio padrão sigma_ruido para ruído gaussiano N(0, sigma^2) em pessoas (padrão 2.5)",
    )
    ou_theta: float = Field(
        default=1.2,
        gt=0.0,
        description="Taxa horária theta de reversão à média no processo de Ornstein-Uhlenbeck (padrão 1.2 h^-1)",
    )
    ou_sigma: float = Field(
        default=2.0,
        ge=0.0,
        description="Volatilidade sigma_sensor da difusão no processo de Ornstein-Uhlenbeck (padrão 2.0)",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Semente para reprodutibilidade estocástica em testes e calibrações",
    )


class SensorSaturationConfig(BaseModel):
    """Configuração consolidada do subsistema de saturação, ruído e sensoriamento IoT."""
    richards: RichardsSaturationConfig = Field(
        default_factory=RichardsSaturationConfig,
        description="Parâmetros da barreira de saturação de Richards",
    )
    noise: SensorNoiseConfig = Field(
        default_factory=SensorNoiseConfig,
        description="Parâmetros de ruído instrumental IoT",
    )
    step_minutes: float = Field(
        default=5.0,
        gt=0.0,
        description="Passo temporal Delta t em minutos para discretização de Ornstein-Uhlenbeck",
    )
    nodes: List[SensorNodeMetadata] = Field(
        default_factory=lambda: [
            SensorNodeMetadata(
                sensor_id="sensor_elevador_lacerda",
                nome_local="Elevador Lacerda",
                max_capacity=150,
                kappa=0.08,
                lat=-12.97330,
                lng=-38.51260,
                area_m2=150.0,
            ),
            SensorNodeMetadata(
                sensor_id="sensor_praca_da_se",
                nome_local="Praça da Sé",
                max_capacity=120,
                kappa=0.08,
                lat=-12.97380,
                lng=-38.51090,
                area_m2=120.0,
            ),
            SensorNodeMetadata(
                sensor_id="sensor_ladeira_do_carmo",
                nome_local="Ladeira do Carmo",
                max_capacity=80,
                kappa=0.08,
                lat=-12.96980,
                lng=-38.50800,
                area_m2=80.0,
            ),
            SensorNodeMetadata(
                sensor_id="sensor_largo_pelourinho",
                nome_local="Largo do Pelourinho",
                max_capacity=250,
                kappa=0.08,
                lat=-12.97180,
                lng=-38.50850,
                area_m2=250.0,
            ),
            SensorNodeMetadata(
                sensor_id="sensor_terreiro_jesus",
                nome_local="Terreiro de Jesus",
                max_capacity=200,
                kappa=0.08,
                lat=-12.97310,
                lng=-38.50970,
                area_m2=200.0,
            ),
        ],
        description="Lista de nós de sensoriamento com suas capacidades e metadados",
    )


class SensorSaturationRequest(BaseModel):
    """Payload de requisição para execução do subsistema de sensoriamento (Doc 04)."""
    N_bruto: Optional[List[float]] = Field(
        default=None,
        description="Vetor de fluxo físico bruto consolidado N_bruto(t+1) em R^J. Se informado, pula a soma dos 3 canais.",
    )
    vector_N_bruto: Optional[List[float]] = Field(
        default=None,
        description="Alias para N_bruto",
    )
    N_propagado: Optional[List[float]] = Field(
        default=None,
        description="Vetor N_propagado(t+1) originado do Doc 03",
    )
    vector_N_propagado: Optional[List[float]] = Field(
        default=None,
        description="Alias para N_propagado",
    )
    N_rotina: Optional[List[float]] = Field(
        default=None,
        description="Vetor N_rotina(t) originado do Doc 01",
    )
    delta_N_rotina: Optional[List[float]] = Field(
        default=None,
        description="Vetor de novos ingressos Delta N_rotina(t) originado do Doc 01",
    )
    vector_E_eventos: Optional[List[float]] = Field(
        default=None,
        description="Vetor E(t) de acréscimo de eventos originado do Doc 02",
    )
    current_time_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Timestamp contínuo t em horas (se omitido, usa hora atual)",
    )
    step_minutes: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Duração do ciclo temporal Delta t em minutos",
    )
    noise_method: Optional[str] = Field(
        default=None,
        description="Override opcional do método de ruído (NONE, UNIFORM, GAUSSIAN, ORNSTEIN_UHLENBECK)",
    )
    persist_telemetry: bool = Field(
        default=False,
        description="Se True, persiste as leituras na tabela telemetria_sensores do Datalake",
    )
    reset_noise_state: bool = Field(
        default=False,
        description="Se True, zera a memória de estado anterior do ruído de Ornstein-Uhlenbeck",
    )
    config: Optional[SensorSaturationConfig] = Field(
        default=None,
        description="Configuração customizada de saturação, ruído e nós (opcional)",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_saturation_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "vector_N_bruto" in values and "N_bruto" not in values:
                values["N_bruto"] = values["vector_N_bruto"]
            elif "N_bruto" in values and "vector_N_bruto" not in values:
                values["vector_N_bruto"] = values["N_bruto"]

            if "vector_N_propagado" in values and "N_propagado" not in values:
                values["N_propagado"] = values["vector_N_propagado"]
            elif "N_propagado" in values and "vector_N_propagado" not in values:
                values["vector_N_propagado"] = values["N_propagado"]
        return values


class SensorTelemetryItem(BaseModel):
    """Leitura emitida por um sensor individual compatível com Leaflet e GeoPackage."""
    sensor_id: str
    nome_local: str
    count: int = Field(..., ge=0, description="Contagem inteira discretizada emitida N_j^sensor")
    max_capacity: int = Field(..., ge=0, description="Capacidade máxima de suporte N_j,max")
    occupancy_pct: float = Field(..., ge=0.0, description="Taxa percentual de ocupação em % (0..100)")
    density_m2: float = Field(..., ge=0.0, description="Densidade estimada em pessoas / m²")
    status: str = Field(..., description="Status de aglomeração: NORMAL, ATENCAO (>70%) ou CRITICO (>90%)")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raw_input: Optional[float] = Field(None, description="Volume físico bruto não atenuado N_bruto,j")
    saturated_val: Optional[float] = Field(None, description="Valor contínuo saturado Richards S_j")
    noise_val: Optional[float] = Field(None, description="Perturbação instrumental injetada epsilon_j")


class SensorTelemetryResponse(BaseModel):
    """Payload consolidado de telemetria IoT emitido para o Datalake e Mapa Leaflet (RF05)."""
    timestamp_iso: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_time_hours: float
    noise_method: str
    step_minutes: float = Field(default=5.0)
    vector_N_bruto: List[float] = Field(
        ...,
        description="Vetor de entrada de fluxo físico bruto N_bruto(t+1)",
    )
    vector_S_richards: List[float] = Field(
        ...,
        description="Vetor de fluxo saturado contínuo após a barreira de Richards S(t+1)",
    )
    vector_epsilon_noise: List[float] = Field(
        ...,
        description="Vetor de ruído instrumental estocástico injetado epsilon(t)",
    )
    vector_N_sensor: List[int] = Field(
        ...,
        description="Vetor final de leituras discretas emitidas pelo sensoriamento N_sensor(t+1)",
    )
    sensors: List[SensorTelemetryItem] = Field(
        ...,
        description="Lista detalhada por sensor para consumo no frontend Leaflet e QGIS",
    )
    persisted_rows: int = Field(
        default=0,
        description="Quantidade de registros persistidos na tabela telemetria_sensores",
    )



