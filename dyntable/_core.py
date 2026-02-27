"""
dyntable/_core.py
=================
Implementação da DynTable em Python puro.

PRINCIPAIS DIFERENÇAS em relação à versão C-style anterior:
────────────────────────────────────────────────────────────
1. Sem DynStatus: erros viram exceções específicas
2. Colunas armazenadas em dict {nome → DynColumn} para O(1)
3. Linhas acessíveis por ID: table[row_id]["coluna"]
4. Tabela iterável: for row in table
5. Inferência de tipo automática ao inserir valor
6. Método new_row() aceita kwargs para inserção direta
7. Filtragem de linhas com table.filter(coluna=valor)
"""

from __future__ import annotations

import csv
import io
import time
import copy
from typing import Any, Iterator, Optional, Callable

from ._types import (
    DynCell, DynColumn, DynRow, DynType,
    DynTableError, ColumnNotFoundError, RowNotFoundError,
    DuplicateColumnError, TypeMismatchError, ColumnNameError,
    MAX_NAME_LEN,
)


class DynTable:
    """
    Tabela dinâmica com colunas e linhas criadas em tempo de execução.

    Uso básico:
        table = DynTable("sensores")
        table.add_column("device_id", DynType.STRING)
        table.add_column("temperatura")  # tipo AUTO, inferido no set

        row = table.new_row()
        row["device_id"]   = "sensor-01"
        row["temperatura"] = 23.7        # float inferido automaticamente

        # Acesso direto
        print(table[row.id]["temperatura"])  # → 23.7

        # Iteração
        for row in table:
            print(row["device_id"])
    """

    def __init__(self, name: str):
        if len(name) > MAX_NAME_LEN:
            raise ValueError(f"Nome da tabela excede {MAX_NAME_LEN} caracteres")
        self.name = name

        # ── Colunas: dict para acesso O(1) por nome ──────────────
        # Em C era um array linear com busca O(n).
        # Em Python, dict usa hash table — acesso instantâneo.
        self._columns: dict[str, DynColumn] = {}
        self._col_order: list[str] = []  # preserva ordem de inserção

        # ── Linhas: dict {id → DynRow} ───────────────────────────
        self._rows: dict[int, DynRow] = {}
        self._row_order: list[int] = []  # preserva ordem de inserção

        self._next_id: int = 1

    # ═══════════════════════════════════════════════════════════
    #  COLUNAS
    # ═══════════════════════════════════════════════════════════

    def add_column(self, name: str,
                   dtype: DynType = DynType.AUTO,
                   nullable: bool = True) -> "DynTable":
        """
        Adiciona uma coluna. Pode ser chamado a qualquer momento,
        mesmo após linhas já terem sido inseridas.

        Retorna `self` para permitir encadeamento:
            table.add_column("a").add_column("b").add_column("c")

        Linhas existentes recebem NULL na nova coluna automaticamente.
        """
        if name in self._columns:
            raise DuplicateColumnError(name)

        col = DynColumn(name=name, dtype=dtype, nullable=nullable)
        self._columns[name] = col
        self._col_order.append(name)

        # Expande linhas existentes
        for row in self._rows.values():
            row._add_column(name)

        return self  # encadeamento fluente

    def remove_column(self, name: str) -> "DynTable":
        """Remove coluna e todos os seus dados."""
        if name not in self._columns:
            raise ColumnNotFoundError(name)

        del self._columns[name]
        self._col_order.remove(name)

        for row in self._rows.values():
            row._remove_column(name)

        return self

    def rename_column(self, old: str, new: str) -> "DynTable":
        """Renomeia uma coluna preservando todos os dados."""
        if old not in self._columns:
            raise ColumnNotFoundError(old)
        if new in self._columns:
            raise DuplicateColumnError(new)
        if len(new) > MAX_NAME_LEN or not new.strip():
            raise ColumnNameError(new)

        col = self._columns.pop(old)
        col.name = new
        self._columns[new] = col

        idx = self._col_order.index(old)
        self._col_order[idx] = new

        for row in self._rows.values():
            row._rename_column(old, new)

        return self

    @property
    def columns(self) -> list[DynColumn]:
        """Lista de colunas na ordem de inserção."""
        return [self._columns[n] for n in self._col_order]

    @property
    def column_names(self) -> list[str]:
        return list(self._col_order)

    # ═══════════════════════════════════════════════════════════
    #  LINHAS
    # ═══════════════════════════════════════════════════════════

    def new_row(self, **kwargs) -> DynRow:
        """
        Insere uma linha nova e retorna ela.

        NOVO em relação ao C: aceita kwargs para inserção direta.
            row = table.new_row(device_id="sensor-01", temperatura=23.7)

        Equivale ao C:
            DynRow *r = dyn_row_insert(table);
            dyn_cell_set_string(table, r->id, "device_id", "sensor-01");
            dyn_cell_set_float(table, r->id, "temperatura", 23.7);
        """
        row = DynRow(row_id=self._next_id, col_names=self._col_order)
        self._next_id += 1
        self._rows[row.id] = row
        self._row_order.append(row.id)

        # Aplica kwargs imediatamente
        for col, val in kwargs.items():
            if col not in self._columns:
                raise ColumnNotFoundError(col)
            self._set_cell(row, col, val)

        return row

    def delete_row(self, row_id: int) -> "DynTable":
        """Remove uma linha pelo ID."""
        if row_id not in self._rows:
            raise RowNotFoundError(row_id)
        del self._rows[row_id]
        self._row_order.remove(row_id)
        return self

    def get_row(self, row_id: int) -> DynRow:
        """Retorna uma linha pelo ID. Lança RowNotFoundError se não existir."""
        if row_id not in self._rows:
            raise RowNotFoundError(row_id)
        return self._rows[row_id]

    def set(self, row_id: int, col: str, value: Any) -> "DynTable":
        """
        Define o valor de uma célula. Alternativa ao row["col"] = val
        quando você tem o row_id mas não a referência à linha.

            table.set(1, "temperatura", 25.0)
        """
        row = self.get_row(row_id)
        self._set_cell(row, col, value)
        return self

    def get(self, row_id: int, col: str) -> Any:
        """
        Lê o valor de uma célula.

            temp = table.get(1, "temperatura")
        """
        return self.get_row(row_id)[col]

    # ── Helper interno de set com checagem de tipo ───────────
    def _set_cell(self, row: DynRow, col: str, value: Any) -> None:
        col_def = self._columns[col]
        inferred = DynType.infer(value) if value is not None else DynType.NULL

        # Se a coluna tem tipo fixo, verifica compatibilidade
        if col_def.dtype not in (DynType.AUTO, DynType.NULL) and value is not None:
            if inferred != col_def.dtype:
                # Tenta coerção segura entre tipos compatíveis
                try:
                    if col_def.dtype == DynType.FLOAT and isinstance(value, (int, float)):
                        value = float(value)
                        inferred = DynType.FLOAT
                    elif col_def.dtype == DynType.TIMESTAMP and isinstance(value, (int, float)):
                        value = float(value)
                        inferred = DynType.TIMESTAMP
                    elif col_def.dtype == DynType.INT and isinstance(value, float) and value.is_integer():
                        value = int(value)
                        inferred = DynType.INT
                    elif col_def.dtype == DynType.STRING:
                        value = str(value)
                        inferred = DynType.STRING
                    else:
                        raise TypeMismatchError(col, col_def.dtype.name, value)
                except (ValueError, TypeError):
                    raise TypeMismatchError(col, col_def.dtype.name, value)

        # Se é AUTO e ainda não foi travado, trava o tipo agora
        if col_def.dtype == DynType.AUTO and value is not None and not col_def.locked:
            col_def.dtype = inferred
            col_def.locked = True

        row._data[col] = DynCell(dtype=inferred, value=value)

    # ═══════════════════════════════════════════════════════════
    #  FILTROS E CONSULTAS
    #  NOVO: não existia no C. Python permite isso de forma natural.
    # ═══════════════════════════════════════════════════════════

    def filter(self, **conditions) -> list[DynRow]:
        """
        Retorna linhas que satisfazem todas as condições.

            quentes = table.filter(device_id="sensor-T01")
            table.filter(temperatura=23.7)

        Aceita também callables:
            table.filter(temperatura=lambda v: v is not None and v > 25)
        """
        result = []
        for row in self:
            match = True
            for col, expected in conditions.items():
                actual = row[col] if col in row else None
                if callable(expected):
                    if not expected(actual):
                        match = False; break
                else:
                    if actual != expected:
                        match = False; break
            if match:
                result.append(row)
        return result

    def find_one(self, **conditions) -> Optional[DynRow]:
        """Como filter(), mas retorna só o primeiro resultado (ou None)."""
        results = self.filter(**conditions)
        return results[0] if results else None

    def column_values(self, col: str) -> list[Any]:
        """Retorna todos os valores de uma coluna como lista Python."""
        if col not in self._columns:
            raise ColumnNotFoundError(col)
        return [row[col] for row in self]

    def column_stats(self, col: str) -> dict:
        """
        Estatísticas básicas de uma coluna numérica.
        Retorna min, max, média, contagem de nulos.
        """
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

    # ═══════════════════════════════════════════════════════════
    #  PROTOCOLO PYTHON (operadores e iteração)
    # ═══════════════════════════════════════════════════════════

    def __len__(self) -> int:
        """len(table) → número de linhas."""
        return len(self._rows)

    def __iter__(self) -> Iterator[DynRow]:
        """
        for row in table:  → itera na ordem de inserção.
        Em C não existia isso — você precisava de um loop manual:
            for (size_t i = 0; i < table->row_count; i++) { ... }
        """
        for row_id in self._row_order:
            yield self._rows[row_id]

    def __contains__(self, row_id: int) -> bool:
        """3 in table  → True se o ID existe."""
        return row_id in self._rows

    def __getitem__(self, row_id: int) -> DynRow:
        """table[row_id]  → retorna a linha."""
        return self.get_row(row_id)

    def __bool__(self) -> bool:
        """if table:  → True se tem pelo menos uma linha."""
        return len(self._rows) > 0

    def __repr__(self) -> str:
        cols = ", ".join(self._col_order)
        return f"DynTable('{self.name}', rows={len(self)}, columns=[{cols}])"

    def __str__(self) -> str:
        """print(table) → tabela formatada."""
        if not self._col_order:
            return f"[Tabela '{self.name}' sem colunas]"

        W = 16  # largura de coluna
        header = f"{'ID':<5} | {'criado_em':<20} | " + " | ".join(
            f"{n:<{W}}" for n in self._col_order
        )
        sep = "-" * len(header)
        lines = [f"\n═══ {self.name} ({len(self)} linhas × {len(self._col_order)} colunas) ═══",
                 header, sep]

        for row in self:
            cells = " | ".join(
                f"{row.cell(col).formatted():<{W}}" for col in self._col_order
            )
            lines.append(f"{row.id:<5} | {row.created_at_str:<20} | {cells}")

        return "\n".join(lines) + "\n"

    # ═══════════════════════════════════════════════════════════
    #  PROPRIEDADES ÚTEIS
    # ═══════════════════════════════════════════════════════════

    @property
    def col_count(self) -> int:
        return len(self._columns)

    @property
    def row_count(self) -> int:
        return len(self._rows)

    # ═══════════════════════════════════════════════════════════
    #  SERIALIZAÇÃO
    # ═══════════════════════════════════════════════════════════

    def to_dicts(self) -> list[dict]:
        """
        Converte a tabela inteira para lista de dicts Python.
        Ideal para integração com pandas, JSON, APIs.

            import pandas as pd
            df = pd.DataFrame(table.to_dicts())
        """
        return [row.to_dict() for row in self]

    def export_csv(self, filepath: str) -> None:
        """Exporta para arquivo CSV. Lança OSError se não conseguir escrever."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            self._write_csv(csv.writer(f))

    def to_csv_string(self) -> str:
        """Retorna o CSV como string, sem criar arquivo."""
        buf = io.StringIO()
        self._write_csv(csv.writer(buf))
        return buf.getvalue()

    def _write_csv(self, writer) -> None:
        writer.writerow(["id", "created_at"] + self._col_order)
        for row in self:
            writer.writerow(
                [row.id, row.created_at_str] +
                [row[col] if row[col] is not None else "" for col in self._col_order]
            )

    # ═══════════════════════════════════════════════════════════
    #  CLONAGEM
    # ═══════════════════════════════════════════════════════════

    def clone(self, new_name: Optional[str] = None) -> "DynTable":
        """Cópia profunda e independente da tabela."""
        t = DynTable(new_name or self.name)
        for col in self.columns:
            t.add_column(col.name, col.dtype, col.nullable)
        for row in self:
            new_row = t.new_row()
            for col_name in self._col_order:
                cell = row.cell(col_name)
                if not cell.is_null:
                    new_row[col_name] = copy.deepcopy(cell.value)
            new_row.id = row.id
            new_row.created_at = row.created_at
        t._next_id = self._next_id
        return t
