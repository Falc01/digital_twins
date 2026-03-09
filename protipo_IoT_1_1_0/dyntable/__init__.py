"""
dyntable — tabela dinâmica para projetos IoT.

Uso mínimo:
    from dyntable import DynTable, DynType

    # Primeira execução: cria tabela nova
    # Execuções seguintes: carrega do disco automaticamente
    t = DynTable.load_or_create("dados", "sensor_readings")

    t.add_column("device_id", DynType.STRING)
    t.add_column("temperatura")        # tipo inferido automaticamente

    row = t.new_row(device_id="T01", temperatura=23.7)

    t.save("dados")                    # persiste para o próximo uso
"""

from ._types import (
    DynType, DynCell, DynColumn, DynRow,
    DynTableError, ColumnNotFoundError, RowNotFoundError,
    DuplicateColumnError, TypeMismatchError, ColumnNameError,
    MAX_NAME_LEN, INITIAL_COLS, INITIAL_ROWS, GROWTH_FACTOR,
)
from ._core import DynTable

__all__ = [
    "DynTable", "DynType", "DynCell", "DynColumn", "DynRow",
    "DynTableError", "ColumnNotFoundError", "RowNotFoundError",
    "DuplicateColumnError", "TypeMismatchError", "ColumnNameError",
    "MAX_NAME_LEN", "INITIAL_COLS", "INITIAL_ROWS", "GROWTH_FACTOR",
]

__version__ = "2.0.0"
