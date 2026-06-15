"""
Testes básicos do backend funcional.

Usa TestClient do FastAPI + o Excel real fornecido pelo usuário.
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Garante que podemos importar o pacote
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.api.main import app
from shared.config import DATA_DIR

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Gêmeo Digital IoT Backend" in r.text


def test_status_initial():
    r = client.get("/status")
    assert r.status_code == 200
    # Pode ser "sem_dados" ou ok dependendo do estado
    assert "status" in r.json()


def test_ingest_and_query_user_excel():
    """Teste end-to-end com o Excel real que o usuário adicionou."""
    xlsx_path = Path("infra/dados/dados_temperatura_salvador_pelourinho.xlsx")
    assert xlsx_path.exists(), "Excel de teste não encontrado"

    table_name = "test_estacao_funcional"

    # Upload
    with open(xlsx_path, "rb") as f:
        files = {"file": (xlsx_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"table_name": table_name}
        r = client.post("/ingest", files=files, data=data)

    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["table"] == table_name
    assert payload["rows_ingested"] > 2000

    # List tables
    r = client.get("/tables")
    assert r.status_code == 200
    assert table_name in r.json()["tables"]

    # Get schema
    r = client.get(f"/tables/{table_name}")
    assert r.status_code == 200
    info = r.json()
    assert info["row_count"] > 2000
    assert len(info["columns"]) > 15  # muitas colunas do tempo

    # Query rows (dados reais)
    r = client.get(f"/tables/{table_name}/rows?limit=3")
    assert r.status_code == 200
    rows_resp = r.json()
    assert rows_resp["returned"] == 3
    assert "temperatura" in str(rows_resp).lower() or "data" in rows_resp["rows"][0]["data"]

    # Status deve refletir a ingestão recente
    r = client.get("/status")
    assert r.status_code == 200
    st = r.json()
    assert st["tabela"] == table_name or st["status"] in ("ok", "sucesso")
