from __future__ import annotations

import logging
from typing import Any, Optional
from pydantic import ValidationError
from src.qgis.data.models import SensorReading, ProcessingResult, RowData, TableData, normalize_keys
from src.dyntable.logic.table_manager import TableManager

logger = logging.getLogger("qgis_bridge.reader")

class RowByRowReader:
    def __init__(
        self,
        data_dir: str,
        lat_hint: Optional[str] = None,
        lon_hint: Optional[str] = None,
    ) -> None:
        self._data_dir = data_dir
        self._lat_hint = lat_hint
        self._lon_hint = lon_hint

    def list_tables(self) -> list[str]:
        return TableManager(self._data_dir).list_tables()

    def exists(self, table_name: str) -> bool:
        return TableManager(self._data_dir).exists(table_name)

    def iter_valid_rows(
        self,
        table_name: str,
        result: ProcessingResult,
    ):
        manager = TableManager(self._data_dir)
        if not manager.exists(table_name):
            logger.error("Tabela '%s' não encontrada em '%s'", table_name, self._data_dir)
            return

        table = manager.get(table_name)

        for row in table:
            result.total_rows += 1

            raw: dict[str, Any] = {
                col: row[col]
                for col in table.column_names
            }
            raw["row_id"]     = row.id
            raw["created_at"] = row.created_at_str

            normalized = normalize_keys(raw)

            if self._lat_hint and self._lat_hint in raw:
                normalized["latitude"] = raw[self._lat_hint]
            if self._lon_hint and self._lon_hint in raw:
                normalized["longitude"] = raw[self._lon_hint]

            try:
                reading = SensorReading(**normalized)
                result.valid_rows += 1
                yield reading
            except ValidationError as exc:
                messages = "; ".join(
                    f"{e['loc'][0] if e['loc'] else '?'}: {e['msg']}"
                    for e in exc.errors()
                )
                error_msg = (
                    f"Linha {row.id} de '{table_name}' descartada — {messages} "
                    f"| dados: {normalized}"
                )
                result.skipped_rows += 1
                result.errors.append(error_msg)
                logger.debug(error_msg)
                continue
            except Exception as exc:
                error_msg = (
                    f"Linha {row.id} de '{table_name}' erro inesperado: {exc}"
                )
                result.skipped_rows += 1
                result.errors.append(error_msg)
                logger.warning(error_msg)
                continue

    def read_all_valid(self, table_name: str) -> tuple[list[SensorReading], ProcessingResult]:
        result = ProcessingResult(table_name=table_name)
        readings = list(self.iter_valid_rows(table_name, result))
        result.log_summary()
        return readings, result

def readings_to_table_data(
    table_name: str,
    readings: list[SensorReading],
) -> TableData:
    if not readings:
        return TableData(
            name=table_name,
            column_names=[],
            column_types={},
            rows=[],
            lat_col="latitude",
            lon_col="longitude",
        )

    base_cols = [
        "device_id", "latitude", "longitude",
        "temperatura", "humidade", "pressao", "status",
    ]
    extra_cols: list[str] = []
    for r in readings:
        for k in r.extra:
            if k not in base_cols and k not in extra_cols:
                extra_cols.append(k)

    all_cols = base_cols + extra_cols

    col_types: dict[str, str] = {
        "device_id":   "STRING",
        "latitude":    "FLOAT",
        "longitude":   "FLOAT",
        "temperatura": "FLOAT",
        "humidade":    "FLOAT",
        "pressao":     "FLOAT",
        "status":      "STRING",
    }
    for ec in extra_cols:
        col_types[ec] = "AUTO"

    rows: list[RowData] = []
    for r in readings:
        props = r.to_properties()
        values = {col: props.get(col) for col in all_cols}
        rows.append(RowData(
            row_id=r.row_id,
            created_at=r.created_at,
            values=values,
        ))

    return TableData(
        name=table_name,
        column_names=all_cols,
        column_types=col_types,
        rows=rows,
        lat_col="latitude",
        lon_col="longitude",
    )
