"""
dyntable/_types.py
==================
Tipos, constantes e exceções do sistema.

DIFERENÇAS DA VERSÃO C-STYLE:
──────────────────────────────
• DynStatus foi REMOVIDO como retorno de funções.
  Em Python, erros são sinalizados por exceções — é o padrão da linguagem.
  Criamos exceções específicas por categoria de erro (abaixo).

• DynType ainda existe, mas agora é OPCIONAL: se você não informar
  o tipo ao criar uma coluna, a tabela infere automaticamente pelo
  valor que você inserir.

• DynCell agora tem __getitem__/__setitem__ para acesso dict-like.

• DynRow agora é subscritável: row["coluna"] = valor
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any
import time

# ─────────────────────────────────────────────
#  CONSTANTES  (mantidas do C, são úteis)
# ─────────────────────────────────────────────
MAX_NAME_LEN  = 64
INITIAL_COLS  = 8
INITIAL_ROWS  = 16
GROWTH_FACTOR = 2


# ─────────────────────────────────────────────
#  EXCEÇÕES  (substituem DynStatus)
#
#  Em C: if (dyn_col_add(t, ...) == DYN_ERR_DUPLICATE) { ... }
#  Em Python: try: t.add_column(...) except DuplicateColumnError: ...
#
#  Vantagem: exceções propagam automaticamente pela pilha de chamadas.
#  Você não precisa checar o retorno de cada função — o erro para
#  tudo e sobe até alguém que sabe lidar com ele.
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
#  TIPOS SUPORTADOS
#  Mantemos DynType — a checagem de tipo explícita
#  é importante para IoT onde você quer saber se
#  temperature_c é float ou string.
# ─────────────────────────────────────────────
class DynType(IntEnum):
    INT       = 0
    FLOAT     = 1
    STRING    = 2
    BOOL      = 3
    TIMESTAMP = 4
    BYTES     = 5
    AUTO      = 99   # NOVO: a tabela infere o tipo automaticamente
    NULL      = 255

    @classmethod
    def infer(cls, value: Any) -> "DynType":
        """
        NOVO em relação ao C: infere o DynType pelo valor Python.
        Em C isso não era possível porque tipos são estáticos.
        Em Python, type(value) diz o tipo em runtime.
        """
        if isinstance(value, bool):   return cls.BOOL       # bool antes de int!
        if isinstance(value, int):    return cls.INT
        if isinstance(value, float):  return cls.FLOAT
        if isinstance(value, str):    return cls.STRING
        if isinstance(value, bytes):  return cls.BYTES
        if value is None:             return cls.NULL
        return cls.STRING  # fallback: converte para string


# ─────────────────────────────────────────────
#  COLUNA
# ─────────────────────────────────────────────
@dataclass
class DynColumn:
    name: str
    dtype: DynType = DynType.AUTO  # AUTO = inferir no primeiro set
    nullable: bool = True
    locked: bool = False           # NOVO: após ter dados, trava o tipo

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ColumnNameError(self.name)
        if len(self.name) > MAX_NAME_LEN:
            raise ColumnNameError(self.name)


# ─────────────────────────────────────────────
#  CÉLULA
#  Simplificada: sem union explícita (Python já é dinâmico)
# ─────────────────────────────────────────────
@dataclass
class DynCell:
    dtype: DynType = DynType.NULL
    value: Any = None

    @property
    def is_null(self) -> bool:
        return self.dtype == DynType.NULL

    def formatted(self) -> str:
        """Representação legível do valor."""
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


# ─────────────────────────────────────────────
#  LINHA
#  NOVO: subscritável como dict — row["coluna"]
#  Em C você acessava row->cells[col_index].
#  Aqui usamos o nome diretamente.
# ─────────────────────────────────────────────
class DynRow:
    """
    Linha da tabela. Internamente usa dict para acesso O(1) por nome.

    Em C: row->cells[dyn_col_index(table, "temp")]
    Em Python: row["temp"]   ← muito mais limpo
    """

    def __init__(self, row_id: int, col_names: list[str]):
        self.id: int = row_id
        self.created_at: float = time.time()
        # _data: {nome_coluna → DynCell}
        # Dict tem acesso O(1) vs a busca linear O(n) do C
        self._data: dict[str, DynCell] = {name: DynCell() for name in col_names}

    # ── Acesso dict-like ──────────────────────────────────

    def __getitem__(self, col: str) -> Any:
        """row["temperatura"] → retorna o valor (não a DynCell)."""
        if col not in self._data:
            raise ColumnNotFoundError(col)
        cell = self._data[col]
        return cell.value  # retorna o valor puro, não a célula

    def __setitem__(self, col: str, value: Any) -> None:
        """row["temperatura"] = 23.7"""
        if col not in self._data:
            raise ColumnNotFoundError(col)
        dtype = DynType.infer(value) if value is not None else DynType.NULL
        self._data[col] = DynCell(dtype=dtype, value=value)

    def __contains__(self, col: str) -> bool:
        """'temperatura' in row"""
        return col in self._data

    def cell(self, col: str) -> DynCell:
        """Acesso à DynCell completa (com tipo), quando necessário."""
        if col not in self._data:
            raise ColumnNotFoundError(col)
        return self._data[col]

    def _add_column(self, col: str) -> None:
        """Chamado internamente quando uma nova coluna é adicionada à tabela."""
        self._data[col] = DynCell()

    def _remove_column(self, col: str) -> None:
        """Chamado internamente quando uma coluna é removida."""
        self._data.pop(col, None)

    def _rename_column(self, old: str, new: str) -> None:
        """Chamado internamente ao renomear coluna."""
        self._data[new] = self._data.pop(old, DynCell())

    def to_dict(self) -> dict:
        """Converte a linha para dict puro — útil para serialização."""
        return {
            "id": self.id,
            "created_at": self.created_at_str,
            **{col: cell.value for col, cell in self._data.items()}
        }

    @property
    def created_at_str(self) -> str:
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(self.created_at))

    def __repr__(self) -> str:
        vals = {col: cell.value for col, cell in self._data.items()}
        return f"DynRow(id={self.id}, data={vals})"
