"""
Pydantic schemas para o backend do Gêmeo Digital IoT.

Usados para responses da API (documentação automática via FastAPI).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    row_count: int
    col_count: int


class TableList(BaseModel):
    tables: list[str]


class RowResponse(BaseModel):
    id: int
    created_at: str
    data: dict[str, Any]


class RowsResponse(BaseModel):
    table: str
    total: int
    returned: int
    rows: list[RowResponse]


class StatusResponse(BaseModel):
    ultima_atualizacao: Optional[str] = None
    status: str = "desconhecido"
    tabela: Optional[str] = None
    rows: Optional[int] = None


class IngestResponse(BaseModel):
    table: str
    rows_ingested: int
    message: str = "Ingestão concluída com sucesso"
    timestamp: str
