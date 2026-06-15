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
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_table_manager
from src.api.routers import ingest, tables, status
from shared.config import DATA_DIR
from qgis_bridge.exporter import export_all_tables

# Para rodar com PYTHONPATH=src ou após pip install -e .
# imports de dyntable são feitos dentro dos routers/dependencies como "from dyntable..."


async def start_periodic_sync() -> None:
    while True:
        mgr = get_table_manager()
        export_all_tables(DATA_DIR, DATA_DIR)

        status_path = Path(DATA_DIR) / "status.json"
        status_data = {
            "ultima_atualizacao": datetime.now().isoformat(timespec="seconds"),
            "status": "sucesso",
            "tabelas": mgr.list_tables(),
        }
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(status_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("[scheduler] Sincronização periódica realizada.")

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
app.include_router(ingest.router, prefix="/api")
app.include_router(tables.router, prefix="/api")
app.include_router(status.router)


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
