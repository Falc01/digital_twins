"""Camada de lógica do dyntable (gerenciamento de tabelas e ingestores)."""

from .table_manager import (
    TableManager,
    TableNotFoundError,
    TableAlreadyExistsError,
)
from .ingestors import (
    BaseIngestor,
    ExcelIngestor,
    IngestorFactory,
)

__all__ = [
    "TableManager",
    "TableNotFoundError",
    "TableAlreadyExistsError",
    "BaseIngestor",
    "ExcelIngestor",
    "IngestorFactory",
]
