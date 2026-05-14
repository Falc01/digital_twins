from __future__ import annotations

import os
import pickle
from src.dyntable.data._core import DynTable, DynType


class TableNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Tabela '{name}' não encontrada. Use create() para criar.")

class TableAlreadyExistsError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Tabela '{name}' já existe.")


class TableManager:
    _EXT = ".dyndb"

    def __init__(self, folder: str) -> None:
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def list_tables(self) -> list[str]:
        return sorted(
            f[: -len(self._EXT)]
            for f in os.listdir(self.folder)
            if f.endswith(self._EXT)
        )

    def exists(self, name: str) -> bool:
        return os.path.exists(self._path(name))

    def create(self, name: str) -> DynTable:
        if self.exists(name):
            raise TableAlreadyExistsError(name)
        t = DynTable(name)
        t.save(self.folder)
        return t

    def get(self, name: str) -> DynTable:
        if not self.exists(name):
            raise TableNotFoundError(name)
        return DynTable.load(self.folder, name)

    def get_or_create(self, name: str) -> tuple[DynTable, bool]:
        if self.exists(name):
            return DynTable.load(self.folder, name), False
        t = DynTable(name)
        t.save(self.folder)
        return t, True

    def save(self, table: DynTable) -> None:
        table.save(self.folder)

    def delete(self, name: str) -> None:
        if not self.exists(name):
            raise TableNotFoundError(name)
        os.remove(self._path(name))

    def rename(self, old: str, new: str) -> DynTable:
        if not self.exists(old):
            raise TableNotFoundError(old)
        if self.exists(new):
            raise TableAlreadyExistsError(new)
        t      = DynTable.load(self.folder, old)
        t.name = new
        t.save(self.folder)
        self.delete(old)
        return t

    def info(self, name: str) -> dict:
        t = self.get(name)
        return {
            "name":      t.name,
            "columns":   t.column_names,
            "col_count": t.col_count,
            "row_count": t.row_count,
            "next_id":   t._store._next_id,
        }

    def info_all(self) -> list[dict]:
        return [self.info(n) for n in self.list_tables()]

    def _path(self, name: str) -> str:
        return os.path.join(self.folder, f"{name}{self._EXT}")

    def __repr__(self) -> str:
        return f"TableManager(folder='{self.folder}', tables={self.list_tables()})"
