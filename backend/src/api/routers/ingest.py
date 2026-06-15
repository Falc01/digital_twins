"""
Router de ingestão de dados (Excel/arquivos) para tabelas dinâmicas.

Endpoint principal para o frontend externo carregar os dados de teste.
Usa o ExcelIngestor melhorado (geo opcional, sem hardcodes).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from src.api.dependencies import TableManagerDep
from src.api.schemas import IngestResponse
from dyntable.logic.ingestors import IngestorFactory
from shared.config import DEFAULT_INGEST_TABLE, DATA_DIR

router = APIRouter(tags=["ingest"])


@router.post("/upload", response_model=IngestResponse, summary="Ingerir arquivo Excel/CSV em tabela dinâmica")
@router.post("/ingest", response_model=IngestResponse, summary="Ingerir arquivo Excel/CSV em tabela dinâmica")
async def ingest_file(
    file: UploadFile = File(..., description="Arquivo .xlsx ou .xls com os dados"),
    table_name: Optional[str] = Form(None, description="Nome da tabela (default: leituras ou nome do arquivo)"),
    mgr: TableManagerDep = None,
) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".xlsx", ".xls"):
        raise HTTPException(status_code=400, detail="Apenas arquivos Excel (.xlsx, .xls) são suportados por enquanto.")

    # Nome da tabela
    final_table = (table_name or Path(file.filename).stem or DEFAULT_INGEST_TABLE).strip()
    if not final_table:
        final_table = DEFAULT_INGEST_TABLE

    # Salvar temporariamente (o ingestor precisa de path no disco)
    try:
        with NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Executa ingestão (o ingestor já faz get_or_create + save)
        before = mgr.exists(final_table)
        rows_before = mgr.get(final_table).row_count if before else 0

        IngestorFactory.process_file(tmp_path, final_table, mgr)

        after_table = mgr.get(final_table)
        rows_after = after_table.row_count
        ingested = rows_after - rows_before

        # Sincroniza imediatamente o GeoPackage e o CSV no Datalake
        try:
            from qgis_bridge.exporter import export_csv, export_gpkg
            export_csv(after_table, mgr.folder)
            export_gpkg(after_table, mgr.folder)
            print(f"[ingest] Tabela {final_table} exportada para CSV/GPKG imediatamente após upload.")
        except Exception as e:
            print(f"[ingest] Falha na exportação imediata de {final_table} para CSV/GPKG: {e}")

        # Atualiza status/telemetria simples (arquivo no datalake)
        _write_status(final_table, ingested)

        return IngestResponse(
            table=final_table,
            rows_ingested=ingested,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
    finally:
        # Limpa arquivo temporário
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def _write_status(table: str, rows: int) -> None:
    """Escreve status.json simples no datalake (compatível com visão da arquitetura)."""
    import json
    status_path = Path(DATA_DIR) / "status.json"
    data = {
        "ultima_atualizacao": datetime.now().isoformat(timespec="seconds"),
        "status": "pendente",
        "tabela": table,
        "rows_adicionados": rows,
    }
    status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
