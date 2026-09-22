"""
Router de status / telemetria (alinhado com a visão de arquitetura dos PDFs).

O frontend pode consultar para mostrar "última atualização" ao usuário.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

from src.api.dependencies import TableManagerDep
from src.api.schemas import StatusResponse
from shared.config import DATA_DIR

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def get_status(mgr: TableManagerDep) -> StatusResponse:
    status_path = Path(DATA_DIR) / "status.json"

    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            return StatusResponse(
                ultima_atualizacao=data.get("ultima_atualizacao"),
                status=data.get("status", "sucesso"),
                tabela=data.get("tabela"),
                rows=data.get("rows_adicionados"),
            )
        except Exception:
            pass

    # Fallback: status derivado do manager (se houver tabelas)
    tables = mgr.list_tables()
    if tables:
        latest = mgr.get(tables[0])
        return StatusResponse(
            status="ok",
            tabela=tables[0],
            rows=latest.row_count,
        )

    return StatusResponse(status="sem_dados")
