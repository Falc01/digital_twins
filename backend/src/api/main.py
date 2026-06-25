"""
Aplicação FastAPI principal do backend do Gêmeo Digital IoT.

Foco: camada de dados + ingestão funcional + API REST limpa para consumo
pelo frontend externo (desenvolvido por outro integrante).

Características:
- CORS habilitado (pronto para integração frontend)
- Lifespan gerencia o TableManager
- OpenAPI automático em /docs
- Modular (routers separados)
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_table_manager
from src.api.routers import ingest, tables, status, sensors
from shared.config import DATA_DIR
from qgis_bridge.exporter import export_all_tables, detect_coordinate_columns
from dyntable.data._types import DynType


def _pick_active_table(mgr) -> Optional[str]:
    """Escolhe a tabela mais adequada para ser a 'ativa'.

    Prioridade:
    1. Tabela já marcada no status.json existente (preserva escolha do usuário).
    2. Primeira tabela (ordem alfabética) que possua colunas de coordenadas.
    3. Primeira tabela disponível (fallback).
    """
    status_path = Path(DATA_DIR) / "status.json"
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            candidate = data.get("tabela")
            if candidate and mgr.exists(candidate):
                return candidate
        except Exception:
            pass

    # Busca a primeira tabela com colunas de coordenadas
    for name in mgr.list_tables():
        try:
            t = mgr.get(name)
            lat_col, lon_col = detect_coordinate_columns(t)
            if lat_col and lon_col:
                return name
        except Exception:
            continue

    # Último recurso: qualquer tabela
    tables_list = mgr.list_tables()
    return tables_list[0] if tables_list else None

# Para rodar com PYTHONPATH=src ou após pip install -e .
# imports de dyntable são feitos dentro dos routers/dependencies como "from dyntable..."


async def start_periodic_sync() -> None:
    while True:
        mgr = get_table_manager()
        export_all_tables(DATA_DIR, DATA_DIR)

        status_path = Path(DATA_DIR) / "status.json"
        active_table = _pick_active_table(mgr)
        status_data = {
            "ultima_atualizacao": datetime.now().isoformat(timespec="seconds"),
            "status": "sucesso",
            "tabela": active_table,           # singular — usado por sensors.py e status router
            "tabelas": mgr.list_tables(),     # plural  — lista completa para debug/UI
        }
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(status_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[scheduler] Sincronização periódica realizada. Tabela ativa: {active_table}")

        await asyncio.sleep(1800)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    mgr = get_table_manager()
    print(f"[backend] TableManager inicializado em: {DATA_DIR}")
    print(f"[backend] Tabelas existentes: {mgr.list_tables() or 'nenhuma'}")
    sync_task = asyncio.create_task(start_periodic_sync())
    yield
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Gêmeo Digital IoT - Backend",
    description="API funcional para ingestão e consulta de dados dinâmicos (tabelas sem esquema fixo). "
                "Pronto para integração com frontend externo e extensões futuras (QGIS, etc.).",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS - permite que o frontend (qualquer origem durante dev) consuma a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Em produção restringir para o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
# Rotas prefixadas para o Frontend
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api")
app.include_router(tables.router, prefix="/api/v1")
app.include_router(tables.router, prefix="/api")
app.include_router(status.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api")

# Rotas sem prefixo para compatibilidade com os Testes e legado
app.include_router(ingest.router)
app.include_router(tables.router)
app.include_router(status.router)
app.include_router(sensors.router)


# Endpoints de listagem de tipos de dados (DynTypes)
@app.get("/api/types", tags=["types"])
@app.get("/types", tags=["types"])
def get_types():
    return [t.name for t in DynType]


@app.get("/", tags=["root"])
def root():
    return {
        "message": "Gêmeo Digital IoT Backend (funcional)",
        "docs": "/docs",
        "status": "/status",
        "tables": "/tables",
        "ingest_example": "POST /ingest com arquivo .xlsx",
        "data_dir": str(DATA_DIR),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
