"""
Routers para gerenciamento e consulta de tabelas dinâmicas.

Usado pelo frontend externo para descobrir dados e buscar leituras.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from src.api.dependencies import TableManagerDep
from src.api.schemas import (
    TableList, TableInfo, ColumnInfo,
    RowsResponse, RowResponse,
)
from dyntable.data._core import DynRow

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("/", response_model=TableList)
def list_tables(mgr: TableManagerDep) -> TableList:
    return TableList(tables=mgr.list_tables())


@router.get("/{name}", response_model=TableInfo)
def get_table(name: str, mgr: TableManagerDep) -> TableInfo:
    if not mgr.exists(name):
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")

    t = mgr.get(name)
    cols = [
        ColumnInfo(name=c.name, type=c.dtype.name, nullable=c.nullable)
        for c in t.columns
    ]
    return TableInfo(
        name=t.name,
        columns=cols,
        row_count=t.row_count,
        col_count=t.col_count,
    )


@router.get("/{name}/rows", response_model=RowsResponse)
def get_rows(
    name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    mgr: TableManagerDep = None,
) -> RowsResponse:
    if not mgr.exists(name):
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")

    t = mgr.get(name)
    total = t.row_count

    rows: list[RowResponse] = []
    for i, row in enumerate(t):
        if i < offset:
            continue
        if len(rows) >= limit:
            break
        rows.append(
            RowResponse(
                id=row.id,
                created_at=row.created_at_str,
                data={col: row[col] for col in t.column_names},
            )
        )

    return RowsResponse(
        table=name,
        total=total,
        returned=len(rows),
        rows=rows,
    )
