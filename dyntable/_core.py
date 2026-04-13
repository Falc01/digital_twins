from __future__ import annotations

import os
import copy
import time
import pickle
from typing import Any, Iterator, Optional

from ._matrix import MatrixStore
from ._types import (
    DynCell, DynColumn, DynType,
    DynTableError, ColumnNotFoundError, RowNotFoundError,
    DuplicateColumnError, TypeMismatchError, ColumnNameError,
    MAX_NAME_LEN,
)

class DynRow:

    __slots__ = ("_table", "id")

    def __init__(self, table: "DynTable", row_id: int) -> None:
        object.__setattr__(self, "_table", table)
        object.__setattr__(self, "id",     row_id)

    def __getitem__(self, col: str) -> Any:
        if not self._table._store.has_column(col):
            raise ColumnNotFoundError(col)
        return self._table._store.get(self.id, col)

    def __setitem__(self, col: str, value: Any) -> None:
        if not self._table._store.has_column(col):
            raise ColumnNotFoundError(col)
        self._table._apply_cell(self.id, col, value)

    def __contains__(self, col: str) -> bool:
        return self._table._store.has_column(col)

    @property
    def created_at(self) -> float:
        return self._table._store.get_timestamp(self.id)

    @property
    def created_at_str(self) -> str:
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(self.created_at))

    def cell(self, col: str) -> DynCell:
        value   = self[col]
        col_def = self._table._columns.get(col)
        if value is None:
            return DynCell(dtype=DynType.NULL, value=None)
        dtype = col_def.dtype if col_def else DynType.AUTO
        if dtype in (DynType.AUTO, DynType.NULL):
            dtype = DynType.infer(value)
        return DynCell(dtype=dtype, value=value)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "created_at": self.created_at_str,
            **{col: self[col] for col in self._table.column_names},
        }

    def __repr__(self) -> str:
        vals = {col: self[col] for col in self._table.column_names}
        return f"DynRow(id={self.id}, data={vals})"

class DynTable:

    def __init__(self, name: str) -> None:
        if len(name) > MAX_NAME_LEN:
            raise ValueError(f"Nome excede {MAX_NAME_LEN} caracteres")
        self.name        = name
        self._store      = MatrixStore()
        self._columns:   dict[str, DynColumn] = {}
        self._col_order: list[str]             = []

    def add_column(self, name: str,
                   dtype: DynType = DynType.AUTO,
                   nullable: bool = True) -> "DynTable":
        if name in self._columns:
            raise DuplicateColumnError(name)
        col = DynColumn(name=name, dtype=dtype, nullable=nullable)
        self._columns[name] = col
        self._col_order.append(name)
        self._store.add_column(name)
        return self

    def remove_column(self, name: str) -> "DynTable":
        if name not in self._columns:
            raise ColumnNotFoundError(name)
        del self._columns[name]
        self._col_order.remove(name)
        self._store.remove_column(name)
        return self

    def rename_column(self, old: str, new: str) -> "DynTable":
        if old not in self._columns:
            raise ColumnNotFoundError(old)
        if new in self._columns:
            raise DuplicateColumnError(new)
        if not new.strip() or len(new) > MAX_NAME_LEN:
            raise ColumnNameError(new)
        col      = self._columns.pop(old)
        col.name = new
        self._columns[new]       = col
        self._col_order[self._col_order.index(old)] = new
        self._store.rename_column(old, new)
        return self

    @property
    def columns(self) -> list[DynColumn]:
        return [self._columns[n] for n in self._col_order]

    @property
    def column_names(self) -> list[str]:
        return list(self._col_order)

    def new_row(self, **kwargs) -> DynRow:
        row_id = self._store._next_id
        self._store._next_id += 1
        self._store.add_row(row_id, time.time())
        for col, val in kwargs.items():
            if col not in self._columns:
                raise ColumnNotFoundError(col)
            self._apply_cell(row_id, col, val)
        return DynRow(self, row_id)

    def delete_row(self, row_id: int) -> "DynTable":
        if not self._store.row_id_exists(row_id):
            raise RowNotFoundError(row_id)
        self._store.delete_row(row_id)
        return self

    def get_row(self, row_id: int) -> DynRow:
        if not self._store.row_id_exists(row_id):
            raise RowNotFoundError(row_id)
        return DynRow(self, row_id)

    def set(self, row_id: int, col: str, value: Any) -> "DynTable":
        self.get_row(row_id)          # valida existência
        self._apply_cell(row_id, col, value)
        return self

    def get(self, row_id: int, col: str) -> Any:
        return self.get_row(row_id)[col]

    def _apply_cell(self, row_id: int, col: str, value: Any) -> None:
        col_def  = self._columns[col]
        inferred = DynType.infer(value) if value is not None else DynType.NULL

        if col_def.dtype not in (DynType.AUTO, DynType.NULL) and value is not None:
            if inferred != col_def.dtype:
                try:
                    if col_def.dtype == DynType.FLOAT and isinstance(value, (int, float)):
                        value, inferred = float(value), DynType.FLOAT
                    elif col_def.dtype == DynType.TIMESTAMP and isinstance(value, (int, float)):
                        value, inferred = float(value), DynType.TIMESTAMP
                    elif col_def.dtype == DynType.INT and isinstance(value, float) and value.is_integer():
                        value, inferred = int(value), DynType.INT
                    elif col_def.dtype == DynType.STRING:
                        value, inferred = str(value), DynType.STRING
                    else:
                        raise TypeMismatchError(col, col_def.dtype.name, value)
                except (ValueError, TypeError):
                    raise TypeMismatchError(col, col_def.dtype.name, value)

        if col_def.dtype == DynType.AUTO and value is not None and not col_def.locked:
            col_def.dtype  = inferred
            col_def.locked = True

        self._store.set(row_id, col, value)

    def filter(self, **conditions) -> list[DynRow]:
        return [
            row for row in self
            if all(
                (cond(row[col]) if callable(cond) else row[col] == cond)
                for col, cond in conditions.items()
            )
        ]

    def find_one(self, **conditions) -> Optional[DynRow]:
        r = self.filter(**conditions)
        return r[0] if r else None

    def column_values(self, col: str) -> list[Any]:
        if col not in self._columns:
            raise ColumnNotFoundError(col)
        return self._store.get_col_values(col)

    def column_stats(self, col: str) -> dict:
        if col not in self._columns:
            raise ColumnNotFoundError(col)
        values = [v for v in self.column_values(col) if v is not None]
        nulls  = len(self) - len(values)
        if not values:
            return {"count": 0, "nulls": nulls, "min": None, "max": None, "avg": None}
        return {
            "count": len(values),
            "nulls": nulls,
            "min":   min(values),
            "max":   max(values),
            "avg":   sum(values) / len(values),
        }

    def __len__(self)              -> int:           return self._store.row_count
    def __bool__(self)             -> bool:          return self._store.row_count > 0
    def __contains__(self, rid)    -> bool:          return self._store.row_id_exists(rid)
    def __getitem__(self, rid)     -> DynRow:        return self.get_row(rid)

    def __iter__(self) -> Iterator[DynRow]:
        for row_id, _, _ in self._store.iter_rows():
            yield DynRow(self, row_id)

    @property
    def col_count(self) -> int:  return len(self._columns)
    @property
    def row_count(self) -> int:  return self._store.row_count

    def __repr__(self) -> str:
        return f"DynTable('{self.name}', {self.row_count}x{self.col_count})"

    def __str__(self) -> str:
        if not self._col_order:
            return f"[Tabela '{self.name}' sem colunas]"
        W      = 16
        header = f"{'ID':<5} | {'criado_em':<20} | " + " | ".join(f"{n:<{W}}" for n in self._col_order)
        lines  = [f"\n=== {self.name} ({self.row_count}x{self.col_count}) ===", header, "-" * len(header)]
        for row in self:
            cells = " | ".join(f"{row.cell(col).formatted():<{W}}" for col in self._col_order)
            lines.append(f"{row.id:<5} | {row.created_at_str:<20} | {cells}")
        return "\n".join(lines) + "\n"

    def to_dicts(self) -> list[dict]:
        return [row.to_dict() for row in self]

    def to_csv_string(self) -> str:
        import io, csv as csvmod
        buf    = io.StringIO()
        writer = csvmod.writer(buf)
        writer.writerow(["id", "created_at"] + self._col_order)
        for row in self:
            writer.writerow(
                [row.id, row.created_at_str] +
                [row[col] if row[col] is not None else "" for col in self._col_order]
            )
        return buf.getvalue()

    def export_csv(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_csv_string())

    def save(self, folder: str = ".") -> None:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{self.name}.dyndb")
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, folder: str, name: str) -> "DynTable":
        path = os.path.join(folder, f"{name}.dyndb")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Arquivo não encontrado: {path}\n"
                f"Use table.save('{folder}') para criar primeiro."
            )
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def load_or_create(cls, folder: str, name: str) -> "DynTable":
        try:
            return cls.load(folder, name)
        except FileNotFoundError:
            return cls(name)

    def clone(self, new_name: Optional[str] = None) -> "DynTable":
        t = DynTable(new_name or self.name)
        for col in self.columns:
            t.add_column(col.name, col.dtype, col.nullable)
        for row in self:
            nr = t.new_row()
            for col_name in self._col_order:
                v = row[col_name]
                if v is not None:
                    t._apply_cell(nr.id, col_name, copy.deepcopy(v))
        t._store._next_id = self._store._next_id
        return t