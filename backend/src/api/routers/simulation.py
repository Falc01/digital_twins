"""
Router FastAPI para o Subsistema de Simulação Estocástica de Pedestres (Docs 01 a 05).

Expõe endpoints para:
- Macro-fluxo circadiano basal e portões de entrada (Doc 01);
- Circulação de rede via Cadeias de Markov e atração de POIs (Doc 03).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from src.simulation.macro_flow import (
    MacroFlowSimulator,
    calculate_macro_flow,
)
from src.simulation.markov_circulation import (
    MarkovCirculationSimulator,
    propagate_markov_flow,
)
from src.simulation.schemas import (
    MacroFlowConfig,
    MacroFlowCurvePoint,
    MacroFlowCurveResponse,
    MacroFlowRequest,
    MacroFlowResponse,
    MarkovCirculationConfig,
    MarkovCirculationRequest,
    MarkovCirculationResponse,
)
from src.api.dependencies import TableManagerDep
from src.api.routers.sensors import get_sensors_list

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Instâncias padrão calibradas para o Centro Histórico do Pelourinho
_DEFAULT_SIMULATOR = MacroFlowSimulator()
_DEFAULT_MARKOV_SIMULATOR = MarkovCirculationSimulator()


# ==============================================================================
# Endpoints do Subsistema de Macro-Fluxo (Doc 01)
# ==============================================================================

@router.get("/macro-flow/config", response_model=MacroFlowConfig)
@router.get("/macroflow/default-config", response_model=MacroFlowConfig)
def get_macro_flow_config() -> MacroFlowConfig:
    """
    Retorna os parâmetros e portões padrão ativos para a simulação de macro-fluxo (Doc 01).
    """
    return _DEFAULT_SIMULATOR.config


@router.post("/macro-flow/calculate", response_model=MacroFlowResponse)
def calculate_macro_flow_endpoint(
    payload: MacroFlowRequest,
    mgr: TableManagerDep = None
) -> MacroFlowResponse:
    """
    Calcula o volume diário de pedestres no Pelourinho N_bairro(t) e a distribuição
    de pessoas nos portões de entrada N_rotina(t) para o instante especificado.
    """
    sensor_ids: List[str] = []
    if mgr is not None:
        try:
            sensors = get_sensors_list(mgr)
            sensor_ids = [s["id"] for s in sensors if "id" in s]
        except Exception:
            sensor_ids = []

    try:
        response = calculate_macro_flow(
            current_time_hours=payload.current_time_hours if payload.current_time_hours is not None else 16.5,
            gamma_seasonality=payload.gamma_seasonality,
            config=payload.config or payload.config_override,
            sensor_ids=sensor_ids if sensor_ids else None,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no cálculo de macro-fluxo: {str(e)}")


@router.post("/macroflow", response_model=MacroFlowResponse)
def evaluate_macro_flow(payload: MacroFlowRequest) -> MacroFlowResponse:
    """Calcula o volume global e aloca pedestres aos portões de entrada (Doc 01).
    
    Se current_time_hours for omitido, utiliza o horário operacional atual do servidor.
    """
    sim = _DEFAULT_SIMULATOR
    active_cfg = payload.config or payload.config_override
    if active_cfg:
        sim = MacroFlowSimulator(config=active_cfg)

    result = sim.evaluate(
        t_hours=payload.current_time_hours,
        gamma=payload.gamma_seasonality,
    )
    return result.to_response()


@router.get("/macroflow", response_model=MacroFlowResponse)
def get_macro_flow_instant(
    time_hours: Optional[float] = Query(
        None,
        description="Instante contínuo t em horas (ex: 16.5). Se omitido, usa hora atual.",
    ),
    gamma: float = Query(
        1.0,
        ge=0.1,
        le=10.0,
        description="Fator sazonal gamma (1.0 dias comuns, 1.5 verão, 3.5 carnaval)",
    ),
) -> MacroFlowResponse:
    """Consulta rápida via GET do estado do macro-fluxo instantâneo."""
    result = _DEFAULT_SIMULATOR.evaluate(t_hours=time_hours, gamma=gamma)
    return result.to_response()


@router.get("/macroflow/curve", response_model=MacroFlowCurveResponse)
def get_macro_flow_24h_curve(
    step_minutes: float = Query(
        15.0,
        ge=1.0,
        le=60.0,
        description="Intervalo amostral da curva em minutos (padrão: 15 min)",
    ),
    gamma: float = Query(
        1.0,
        ge=0.1,
        le=10.0,
        description="Fator sazonal multiplicador",
    ),
) -> MacroFlowCurveResponse:
    """Retorna a série temporal completa de 24 horas para renderização em gráficos."""
    step_hours = step_minutes / 60.0
    curve_data = _DEFAULT_SIMULATOR.generate_24h_curve(step_hours=step_hours, gamma=gamma)
    points = [MacroFlowCurvePoint(**p) for p in curve_data]
    
    cfg = _DEFAULT_SIMULATOR.config
    return MacroFlowCurveResponse(
        step_hours=step_hours,
        gamma_seasonality=gamma,
        N_max_bairro=cfg.N_max_bairro,
        N_min_bairro=cfg.N_min_bairro,
        t_peak=cfg.t_peak,
        sigma=cfg.sigma,
        curve=points,
    )


# ==============================================================================
# Endpoints do Subsistema de Circulação de Markov & POIs (Doc 03)
# ==============================================================================

@router.get("/markov/config", response_model=MarkovCirculationConfig)
def get_markov_config() -> MarkovCirculationConfig:
    """
    Retorna a calibração espacial ativa da rede de Markov e coordenadas dos nós (Doc 03).
    """
    return _DEFAULT_MARKOV_SIMULATOR.config


@router.get("/markov/matrix")
def get_markov_transition_matrix(
    time_hours: Optional[float] = Query(
        None,
        description="Horário contínuo em horas (ex: 16.5). Se omitido, usa hora atual.",
    ),
) -> Dict[str, Any]:
    """
    Retorna a matriz de transição estocástica P(t) e os pesos atratores alpha(t) para o horário (Doc 03).
    """
    p_mat, alphas = _DEFAULT_MARKOV_SIMULATOR.evaluate_transition_matrix(t_hours=time_hours)
    return {
        "time_hours": time_hours,
        "sensor_ids": _DEFAULT_MARKOV_SIMULATOR.sensor_ids,
        "node_names": _DEFAULT_MARKOV_SIMULATOR.node_names,
        "attraction_alphas": [round(float(a), 3) for a in alphas.tolist()],
        "transition_matrix": [[round(float(p), 4) for p in row] for row in p_mat.tolist()],
        "distance_matrix_meters": [
            [round(float(d), 1) for d in row] for row in _DEFAULT_MARKOV_SIMULATOR.distance_matrix.tolist()
        ],
    }


@router.post("/markov/propagate", response_model=MarkovCirculationResponse)
def propagate_markov_network(
    payload: MarkovCirculationRequest,
) -> MarkovCirculationResponse:
    """
    Executa a propagação estocástica de pedestres na rede de Markov (Doc 03).
    
    Se current_state_N for omitido, consome o vetor N_rotina do Doc 01 como ponto de partida.
    Retorna N_propagado(t+1) = P(t)^T * N(t).
    """
    try:
        sim = _DEFAULT_MARKOV_SIMULATOR
        if payload.config:
            sim = MarkovCirculationSimulator(config=payload.config)

        response = sim.propagate(
            current_state_N=payload.current_state_N,
            t_hours=payload.current_time_hours,
            gamma=payload.gamma_seasonality,
            alpha_override=payload.alpha_override,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na circulação de Markov: {str(e)}")
