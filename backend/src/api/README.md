# src/api - Backend Funcional (FastAPI)

Este módulo implementa o **backend já funcional** entregue nesta fase.

## Executar

```powershell
# Instalar com as dependências de API
pip install -e ".[api,dev]"

# Subir o servidor
uvicorn src.api.main:app --reload
```

Acesse:
- http://127.0.0.1:8000/docs (Swagger / OpenAPI)
- http://127.0.0.1:8000/redoc

## Endpoints principais

- `POST /ingest` — upload de .xlsx (usa o ExcelIngestor sem hardcodes de geo)
- `GET /tables` — lista de tabelas
- `GET /tables/{name}` — metadados da tabela
- `GET /tables/{name}/rows?limit=50` — dados (paginado)
- `GET /status` — última atualização

## Integração com Frontend Externo

O frontend (desenvolvido por outro integrante) deve consumir esta API REST.

CORS está habilitado. O contrato é estável via Pydantic models + OpenAPI.

## Sem hardcodes de geo

O Excel de teste atual (estações meteorológicas) não possui colunas de localização.
O ingestor detecta automaticamente e **não injeta** valores falsos de lat/lon.
Tudo é controlado por `shared/config.py` (GEO_*_CANDIDATES).

Ver também `docs/architecture/arquitetura-proposta.md` (seção do Adaptador FastAPI).
