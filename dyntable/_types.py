from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any
import time

MAX_NAME_LEN  = 64
INITIAL_COLS  = 8
INITIAL_ROWS  = 16
GROWTH_FACTOR = 2

class DynTableError(Exception):
    """Base de todas as exceções do dyntable."""

class ColumnNotFoundError(DynTableError):
    def __init__(self, name: str):
        super().__init__(f"Coluna '{name}' não encontrada.")

class RowNotFoundError(DynTableError):
    def __init__(self, row_id: int):
        super().__init__(f"Linha com ID {row_id} não encontrada.")

class DuplicateColumnError(DynTableError):
    def __init__(self, name: str):
        super().__init__(f"Coluna '{name}' já existe.")

class TypeMismatchError(DynTableError):
    def __init__(self, col: str, expected, got):
        super().__init__(
            f"Coluna '{col}' espera {expected}, mas recebeu {type(got).__name__}."
        )

class ColumnNameError(DynTableError):
    def __init__(self, name: str):
        super().__init__(f"Nome de coluna inválido: '{name}'.")

class DynType(IntEnum):
    INT       = 0
    FLOAT     = 1
    STRING    = 2
    BOOL      = 3
    TIMESTAMP = 4
    BYTES     = 5
    AUTO      = 99
    NULL      = 255

    @classmethod
    def infer(cls, value: Any) -> "DynType":
        if isinstance(value, bool):  return cls.BOOL
        if isinstance(value, int):   return cls.INT
        if isinstance(value, float): return cls.FLOAT
        if isinstance(value, str):   return cls.STRING
        if isinstance(value, bytes): return cls.BYTES
        if value is None:            return cls.NULL
        return cls.STRING

@dataclass
class DynColumn:
    name:     str
    dtype:    DynType = DynType.AUTO
    nullable: bool    = True
    locked:   bool    = False

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ColumnNameError(self.name)
        if len(self.name) > MAX_NAME_LEN:
            raise ColumnNameError(self.name)

@dataclass
class DynCell:
    dtype: DynType = DynType.NULL
    value: Any     = None

    @property
    def is_null(self) -> bool:
        return self.value is None or self.dtype == DynType.NULL

    def formatted(self) -> str:
        if self.is_null:
            return "NULL"
        if self.dtype == DynType.BOOL:
            return "true" if self.value else "false"
        if self.dtype == DynType.TIMESTAMP:
            return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.value))
        if self.dtype == DynType.BYTES:
            return f"<bytes:{len(self.value)}>"
        if self.dtype == DynType.FLOAT:
            return f"{self.value:.4f}"
        return str(self.value)

    def __repr__(self) -> str:
        return f"DynCell({self.dtype.name}={self.value!r})"
