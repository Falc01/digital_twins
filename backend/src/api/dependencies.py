"""
Dependências FastAPI para o backend (TableManager singleton-ish via lifespan).

Facilita testes (sobrescrever a dependency) e mantém o gerenciador de dados centralizado.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from shared.config import DATA_DIR
from dyntable.logic.table_manager import TableManager


@lru_cache(maxsize=1)
def get_table_manager() -> TableManager:
    """Retorna (cached) o TableManager apontando para o DataLake padrão."""
    return TableManager(DATA_DIR)


# Tipo para injeção de dependência
TableManagerDep = Annotated[TableManager, Depends(get_table_manager)]
