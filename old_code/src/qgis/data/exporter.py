"""
qgis_bridge/exporter.py
=======================
Exporta tabelas .dyndb para CSV e GeoJSON consumíveis pelo QGIS.

Responsabilidades
-----------------
- Detectar automaticamente colunas de coordenadas (lat/lon)
- Exportar para CSV delimitado (provider "delimitedtext" do QGIS)
- Exportar para GeoJSON (provider "ogr" do QGIS — mais robusto)
- Exportar todas as tabelas de uma pasta de dados de uma vez
- Fornecer watch_and_export() para uso no startup_script

Nenhuma dependência do QGIS aqui — este módulo roda fora do QGIS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.qgis.logic.pipeline import ExportPipeline   # só para o type checker, sem import circular em runtime

import os
import time
from typing import Any

from src.dyntable.data._core import DynTable
from src.dyntable.logic.table_manager import TableManager

# ─────────────────────────────────────────────
#  Nomes candidatos para lat/lon (case-insensitive)
# ─────────────────────────────────────────────

_LAT_CANDIDATES = {"lat", "latitude", "lat_grau", "y", "coord_y", "geo_lat"}
_LON_CANDIDATES = {"lon", "long", "longitude", "lng", "lon_grau", "x", "coord_x", "geo_lon"}


def detect_coordinate_columns(
    table: DynTable,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Tenta descobrir quais colunas contêm latitude e longitude.

    Prioridade:
    1. Hints explícitos (lat_hint / lon_hint)
    2. Nome da coluna bate com _LAT_CANDIDATES / _LON_CANDIDATES
    3. Nenhuma encontrada → retorna (None, None)
    """
    names_lower = {n.lower(): n for n in table.column_names}

    def _pick(candidates: set[str], hint: str | None) -> str | None:
        if hint and hint in table.column_names:
            return hint
        for cand in candidates:
            if cand in names_lower:
                return names_lower[cand]
        return None

    lat_col = _pick(_LAT_CANDIDATES, lat_hint)
    lon_col = _pick(_LON_CANDIDATES, lon_hint)
    return lat_col, lon_col





# ─────────────────────────────────────────────
#  Exportação em lote
# ─────────────────────────────────────────────

class ExportResult:
    """Resultado de uma exportação em lote."""

    __slots__ = ("table_name", "gpkg_path", "error")

    def __init__(
        self,
        table_name: str,
        gpkg_path: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.table_name = table_name
        self.gpkg_path = gpkg_path
        self.error = error

    @property
    def ok(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        if self.ok:
            return f"ExportResult('{self.table_name}', gpkg={self.gpkg_path!r})"
        return f"ExportResult('{self.table_name}', ERROR={self.error})"


def export_all_tables(
    data_dir: str,
    output_dir: str | None = None,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
    export_gpkg_files: bool = True,
) -> list[ExportResult]:
    """
    Exporta todas as tabelas .dyndb em data_dir.

    Parâmetros
    ----------
    data_dir         : pasta onde ficam os .dyndb
    output_dir       : pasta de saída (padrão: data_dir)
    lat_hint/lon_hint: sugestão de nome de coluna para coordenadas
    export_gpkg_files: gerar GPKG

    Retorna lista de ExportResult (um por tabela).
    """
    output_dir = output_dir or data_dir
    manager = TableManager(data_dir)
    results: list[ExportResult] = []

    for name in manager.list_tables():
        gpkg_path: str | None = None
        try:
            table = manager.get(name)

            if export_gpkg_files:
                from src.qgis.data.gpkg_writer import GpkgWriter
                from src.qgis.logic.reader import RowByRowReader, readings_to_table_data
                reader = RowByRowReader(data_dir, lat_hint, lon_hint)
                readings, _ = reader.read_all_valid(name)
                table_data = readings_to_table_data(name, readings)
                gpkg_path = GpkgWriter().write(table_data, output_dir)

            results.append(ExportResult(name, gpkg_path=gpkg_path))

        except Exception as exc:
            print(f"[exporter] ERRO ao exportar '{name}': {exc}")
            results.append(ExportResult(name, error=exc))

    return results


# ─────────────────────────────────────────────
#  TableExporter — exportador por tabela, com cache de paths
# ─────────────────────────────────────────────

class TableExporter:

    def __init__(
        self,
        table_name: str,
        data_dir: str,
        output_dir: str | None = None,
        pipeline: "ExportPipeline | None" = None,
        lat_hint: str | None = None,
        lon_hint: str | None = None,
        export_gpkg_files: bool = True,
    ) -> None:
        self.table_name        = table_name
        self.data_dir          = data_dir
        self.output_dir        = output_dir or data_dir
        self._pipeline         = pipeline
        self.lat_hint          = lat_hint
        self.lon_hint          = lon_hint
        self.export_gpkg_files = export_gpkg_files

        self.gpkg_path    = os.path.join(self.output_dir, f"{table_name}.gpkg")
        self._last_export: float = 0.0

    def refresh(self) -> bool:
        try:
            if self._pipeline:
                self._pipeline.refresh(self.table_name, self.output_dir)
            else:
                manager = TableManager(self.data_dir)
                if not manager.exists(self.table_name):
                    print(f"[exporter] Tabela '{self.table_name}' não encontrada.")
                    return False
                table = manager.get(self.table_name)
                if self.export_gpkg_files:
                    from src.qgis.data.gpkg_writer import GpkgWriter
                    from src.qgis.logic.reader import RowByRowReader, readings_to_table_data
                    reader = RowByRowReader(self.data_dir, self.lat_hint, self.lon_hint)
                    readings, _ = reader.read_all_valid(self.table_name)
                    table_data = readings_to_table_data(self.table_name, readings)
                    GpkgWriter().write(table_data, self.output_dir)

            self._last_export = time.time()
            return True
        except Exception as exc:
            print(f"[exporter] ERRO em refresh() para '{self.table_name}': {exc}")
            return False

    @property
    def last_export_str(self) -> str:
        if not self._last_export:
            return "nunca"
        return time.strftime("%H:%M:%S", time.localtime(self._last_export))
