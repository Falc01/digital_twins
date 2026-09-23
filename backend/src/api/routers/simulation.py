"""
<<<<<<< HEAD
Router FastAPI para os endpoints da Suíte de Simulação Sintética (Docs 01 a 05).
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Depends

from src.simulation.schemas import MacroFlowConfig, MacroFlowRequest, MacroFlowResponse
from src.simulation.macro_flow import calculate_macro_flow
from src.api.dependencies import TableManagerDep
from src.api.routers.sensors import get_sensors_list

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/macro-flow/config", response_model=MacroFlowConfig)
def get_macro_flow_config() -> MacroFlowConfig:
    """
    Retorna a configuração padrão ativa para a simulação de macro-fluxo (Doc 01).
    """
    return MacroFlowConfig()


@router.post("/macro-flow/calculate", response_model=MacroFlowResponse)
def calculate_macro_flow_endpoint(
    payload: MacroFlowRequest,
    mgr: TableManagerDep = None
) -> MacroFlowResponse:
    """
    Calcula o volume diário de pedestres no Pelourinho N_bairro(t) e a distribuição
    de pessoas nos portões de entrada N_rotina(t) para o instante especificado.
    
    Conforme especificado no Doc 01.
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
            current_time_hours=payload.current_time_hours,
            gamma_seasonality=payload.gamma_seasonality,
            config=payload.config,
            sensor_ids=sensor_ids if sensor_ids else None,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no cálculo de macro-fluxo: {str(e)}")
=======
Router FastAPI para o Subsistema de Simulação Estocástica de Pedestres.

Expõe endpoints de cálculo analítico de macro-fluxo circadiano (Doc 01).
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query

from src.simulation.macro_flow import MacroFlowSimulator
from src.simulation.schemas import (
    MacroFlowConfig,
    MacroFlowCurvePoint,
    MacroFlowCurveResponse,
    MacroFlowRequest,
    MacroFlowResponse,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Instância padrão calibrada para o Centro Histórico do Pelourinho
_DEFAULT_SIMULATOR = MacroFlowSimulator()


@router.get("/macroflow/default-config", response_model=MacroFlowConfig)
def get_default_config():
    """Retorna os parâmetros e portões calibrados por padrão para o Pelourinho."""
    return _DEFAULT_SIMULATOR.config


@router.post("/macroflow", response_model=MacroFlowResponse)
def evaluate_macro_flow(payload: MacroFlowRequest):
    """Calcula o volume global e aloca pedestres aos portões de entrada (Doc 01).
    
    Se current_time_hours for omitido, utiliza o horário operacional atual do servidor.
    """
    sim = _DEFAULT_SIMULATOR
    if payload.config_override:
        sim = MacroFlowSimulator(config=payload.config_override)

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
):
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
):
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
>>>>>>> dd6d2b6f78488711211b92b4346d55562ad7dbf0
