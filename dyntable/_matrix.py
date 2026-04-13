from __future__ import annotations
from typing import Any


class MatrixStore:

    __slots__ = (
        "_matrix", "_col_names", "_col_index",
        "_row_ids", "_row_ts", "_next_id",
    )

    def __init__(self) -> None:
        self._matrix:    list[list[Any]] = []
        self._col_names: list[str]       = []
        self._col_index: dict[str, int]  = {}
        self._row_ids:   list[int]       = []
        self._row_ts:    list[float]     = []
        self._next_id:   int             = 1

    # ═══════════════════════════
    #  DIMENSÕES
    # ═══════════════════════════

    @property
    def row_count(self) -> int:
        return len(self._matrix)

    @property
    def col_count(self) -> int:
        return len(self._col_names)

    # ═══════════════════════════
    #  COLUNAS
    # ═══════════════════════════

    def add_column(self, name: str) -> int:
        idx = len(self._col_names)
        self._col_names.append(name)
        self._col_index[name] = idx
        for row in self._matrix:
            row.append(None)
        return idx

    def remove_column(self, name: str) -> None:
        idx = self._col_index.pop(name)
        del self._col_names[idx]
        for col, i in self._col_index.items():
            if i > idx:
                self._col_index[col] = i - 1
        for row in self._matrix:
            del row[idx]

    def rename_column(self, old: str, new: str) -> None:
        idx = self._col_index.pop(old)
        self._col_names[idx] = new
        self._col_index[new] = idx

    def has_column(self, name: str) -> bool:
        return name in self._col_index

    def add_row(self, row_id: int, timestamp: float) -> int:
        idx = len(self._matrix)
        self._matrix.append([None] * self.col_count)
        self._row_ids.append(row_id)
        self._row_ts.append(timestamp)
        return idx

    def delete_row(self, row_id: int) -> None:
        idx = self._id_to_idx(row_id)
        del self._matrix[idx]
        del self._row_ids[idx]
        del self._row_ts[idx]

    def row_id_exists(self, row_id: int) -> bool:
        return row_id in self._row_ids

    def get(self, row_id: int, col_name: str) -> Any:
        return self._matrix[self._id_to_idx(row_id)][self._col_index[col_name]]

    def set(self, row_id: int, col_name: str, value: Any) -> None:
        self._matrix[self._id_to_idx(row_id)][self._col_index[col_name]] = value

    def get_row_values(self, row_id: int) -> list[Any]:
        return list(self._matrix[self._id_to_idx(row_id)])

    def get_col_values(self, col_name: str) -> list[Any]:
        idx = self._col_index[col_name]
        return [row[idx] for row in self._matrix]

    def get_timestamp(self, row_id: int) -> float:
        return self._row_ts[self._id_to_idx(row_id)]

    def iter_rows(self):
        for i, row in enumerate(self._matrix):
            yield self._row_ids[i], self._row_ts[i], list(row)

    def _id_to_idx(self, row_id: int) -> int:
        try:
            return self._row_ids.index(row_id)
        except ValueError:
            raise KeyError(f"Row ID {row_id} não encontrado.")

    def __repr__(self) -> str:
        return f"MatrixStore({self.row_count}x{self.col_count}, cols={self._col_names})"
