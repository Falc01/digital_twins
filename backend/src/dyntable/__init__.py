"""
Módulo dyntable - Core de Tabelas Dinâmicas (Pure Python).

Fornece estruturas de dados sem esquema fixo (DynTable, DynRow, MatrixStore)
otimizadas para ingestão heterogênea de dados IoT, com suporte a tipos
dinâmicos e persistência simples (.dyndb).

Principais classes:
- TableManager: gerenciamento de tabelas persistidas
- ExcelIngestor / IngestorFactory: ingestão de planilhas (geo opcional, mínimo hardcode)

Ver:
- docs/architecture/decisoes-tecnicas.md (Pure Python Core)
- docs/architecture/arquitetura-proposta.md
- shared/config.py (GEO_*_CANDIDATES para controle de geolocalização)

Este módulo é o coração do backend de dados e deve permanecer com dependências mínimas.
"""

# Registrar aliases de módulos legados em sys.modules para retrocompatibilidade com tabelas .dyndb antigas salvas via pickle.
import sys
from .data import _core, _matrix, _types
sys.modules['dyntable._core'] = _core
sys.modules['dyntable._matrix'] = _matrix
sys.modules['dyntable._types'] = _types

from .data._core import DynTable, DynRow
from .data._types import DynType, DynColumn, DynCell
from .logic.table_manager import TableManager, TableNotFoundError, TableAlreadyExistsError
from .logic.ingestors import ExcelIngestor, IngestorFactory, BaseIngestor

__all__ = [
    "DynTable", "DynRow", "DynType", "DynColumn", "DynCell",
    "TableManager", "TableNotFoundError", "TableAlreadyExistsError",
    "ExcelIngestor", "IngestorFactory", "BaseIngestor",
]
