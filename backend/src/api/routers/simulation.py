"""
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
