"""
Routers para gerenciamento e consulta de tabelas dinâmicas.

Usado pelo frontend externo para descobrir dados e buscar leituras.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Body

from src.api.dependencies import TableManagerDep
from src.api.schemas import (
    TableList, TableInfo, ColumnInfo,
    RowsResponse, RowResponse,
)
from dyntable.data._core import DynRow
from dyntable.data._types import DynType
from dyntable.logic.table_manager import TableNotFoundError, TableAlreadyExistsError

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("/", response_model=TableList)
def list_tables(mgr: TableManagerDep) -> TableList:
    return TableList(tables=mgr.list_tables())


@router.post("/", status_code=201)
def create_table(payload: dict = Body(...), mgr: TableManagerDep = None):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Campo 'name' é obrigatório")
    try:
        mgr.create(name)
    except TableAlreadyExistsError:
        raise HTTPException(status_code=409, detail=f"Tabela '{name}' já existe")
    return {"table": name}


@router.delete("/{name}", status_code=204)
def delete_table(name: str, mgr: TableManagerDep = None):
    try:
        mgr.delete(name)
    except TableNotFoundError:
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")


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


@router.post("/{name}/columns", status_code=201)
def add_column(name: str, payload: dict = Body(...), mgr: TableManagerDep = None):
    if not mgr.exists(name):
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")
    table = mgr.get(name)
    table.add_column(payload["name"], DynType[payload["type"]], payload.get("nullable", True))
    mgr.save(table)
    return {"column": payload["name"]}


@router.delete("/{name}/columns/{column_name}", status_code=204)
def remove_column(name: str, column_name: str, mgr: TableManagerDep = None):
    if not mgr.exists(name):
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")
    table = mgr.get(name)
    table.remove_column(column_name)
    mgr.save(table)


@router.patch("/{name}/columns/{column_name}")
def rename_column(
    name: str,
    column_name: str,
    payload: dict = Body(...),
    mgr: TableManagerDep = None,
):
    if not mgr.exists(name):
        raise HTTPException(status_code=404, detail=f"Tabela '{name}' não encontrada")
    new_name = payload.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="Campo 'name' é obrigatório")
    table = mgr.get(name)
    table.rename_column(column_name, new_name)
    mgr.save(table)
    return {"column": new_name}
