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
    from .middleware import ExportPipeline   # só para o type checker, sem import circular em runtime

import csv
import io
import json
import os
import time
from typing import Any

from dyntable import DynTable
from table_manager import TableManager

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
#  CSV
# ─────────────────────────────────────────────

def table_to_csv_string(table: DynTable) -> str:
    """
    Serializa a tabela como CSV UTF-8.
    Inclui 'id' e 'created_at' como primeiras colunas.
    Valores None viram string vazia.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["id", "created_at"] + table.column_names)
    for row in table:
        writer.writerow(
            [row.id, row.created_at_str]
            + [("" if row[col] is None else row[col]) for col in table.column_names]
        )
    return buf.getvalue()


def export_csv(
    table: DynTable,
    output_dir: str,
    filename: str | None = None,
) -> str:
    """
    Escreve <output_dir>/<filename>.csv e retorna o caminho completo.
    filename padrão: nome da tabela.
    """
    os.makedirs(output_dir, exist_ok=True)
    fname = (filename or table.name) + ".csv"
    path = os.path.join(output_dir, fname)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(table_to_csv_string(table))
    return path


# ─────────────────────────────────────────────
#  GeoJSON
# ─────────────────────────────────────────────

def _row_to_geojson_feature(
    row,
    col_names: list[str],
    lat_col: str,
    lon_col: str,
) -> dict | None:
    """
    Converte uma DynRow em Feature GeoJSON.
    Retorna None se lat ou lon forem nulos ou inválidos.
    """
    try:
        lat = float(row[lat_col])
        lon = float(row[lon_col])
    except (TypeError, ValueError):
        return None

    props: dict[str, Any] = {
        "id": row.id,
        "created_at": row.created_at_str,
    }
    for col in col_names:
        v = row[col]
        props[col] = v if v is not None else None

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def table_to_geojson(
    table: DynTable,
    lat_col: str | None = None,
    lon_col: str | None = None,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
) -> dict:
    """
    Converte a tabela em um FeatureCollection GeoJSON.

    Parâmetros
    ----------
    lat_col / lon_col : nomes explícitos (têm precedência)
    lat_hint / lon_hint : sugestões para detect_coordinate_columns()

    Retorna o dict GeoJSON (não serializado).
    Linhas sem coordenadas válidas são silenciosamente ignoradas.
    """
    if not lat_col or not lon_col:
        lat_col, lon_col = detect_coordinate_columns(table, lat_hint, lon_hint)

    features: list[dict] = []
    skipped = 0

    if lat_col and lon_col:
        for row in table:
            feat = _row_to_geojson_feature(row, table.column_names, lat_col, lon_col)
            if feat is not None:
                features.append(feat)
            else:
                skipped += 1

    geojson = {
        "type": "FeatureCollection",
        "name": table.name,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
        "_meta": {
            "table": table.name,
            "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_rows": table.row_count,
            "exported_features": len(features),
            "skipped_no_coords": skipped,
            "lat_col": lat_col,
            "lon_col": lon_col,
        },
    }
    return geojson


def export_geojson(
    table: DynTable,
    output_dir: str,
    filename: str | None = None,
    lat_col: str | None = None,
    lon_col: str | None = None,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
    indent: int | None = None,
) -> str:
    """
    Escreve <output_dir>/<filename>.geojson e retorna o caminho completo.

    indent=None → JSON compacto (menor, mais rápido)
    indent=2    → JSON legível (útil para debug)
    """
    os.makedirs(output_dir, exist_ok=True)
    fname = (filename or table.name) + ".geojson"
    path = os.path.join(output_dir, fname)

    data = table_to_geojson(
        table,
        lat_col=lat_col,
        lon_col=lon_col,
        lat_hint=lat_hint,
        lon_hint=lon_hint,
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

    meta = data["_meta"]
    print(
        f"[exporter] '{table.name}' → {fname} "
        f"({meta['exported_features']} features"
        + (f", {meta['skipped_no_coords']} sem coords" if meta["skipped_no_coords"] else "")
        + ")"
    )
    return path


# ─────────────────────────────────────────────
#  Exportação em lote
# ─────────────────────────────────────────────

class ExportResult:
    """Resultado de uma exportação em lote."""

    __slots__ = ("table_name", "csv_path", "geojson_path", "error")

    def __init__(
        self,
        table_name: str,
        csv_path: str | None = None,
        geojson_path: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.table_name = table_name
        self.csv_path = csv_path
        self.geojson_path = geojson_path
        self.error = error

    @property
    def ok(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        if self.ok:
            return f"ExportResult('{self.table_name}', csv={self.csv_path!r}, geojson={self.geojson_path!r})"
        return f"ExportResult('{self.table_name}', ERROR={self.error})"


def export_all_tables(
    data_dir: str,
    output_dir: str | None = None,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
    export_csv_files: bool = True,
    export_geojson_files: bool = True,
    geojson_indent: int | None = None,
) -> list[ExportResult]:
    """
    Exporta todas as tabelas .dyndb em data_dir.

    Parâmetros
    ----------
    data_dir         : pasta onde ficam os .dyndb
    output_dir       : pasta de saída (padrão: data_dir)
    lat_hint/lon_hint: sugestão de nome de coluna para coordenadas
    export_csv_files : gerar CSV além do GeoJSON
    export_geojson_files : gerar GeoJSON
    geojson_indent   : formatação do JSON (None = compacto)

    Retorna lista de ExportResult (um por tabela).
    """
    output_dir = output_dir or data_dir
    manager = TableManager(data_dir)
    results: list[ExportResult] = []

    for name in manager.list_tables():
        csv_path: str | None = None
        geojson_path: str | None = None
        try:
            table = manager.get(name)

            if export_csv_files:
                csv_path = export_csv(table, output_dir)

            if export_geojson_files:
                geojson_path = export_geojson(
                    table,
                    output_dir,
                    lat_hint=lat_hint,
                    lon_hint=lon_hint,
                    indent=geojson_indent,
                )

            results.append(ExportResult(name, csv_path, geojson_path))

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
        export_csv_files: bool = True,
        export_geojson_files: bool = True,
        export_gpkg_files: bool = True,
    ) -> None:
        self.table_name        = table_name
        self.data_dir          = data_dir
        self.output_dir        = output_dir or data_dir
        self._pipeline         = pipeline           # bug 1 corrigido
        self.lat_hint          = lat_hint
        self.lon_hint          = lon_hint
        self.export_csv_files  = export_csv_files
        self.export_geojson_files = export_geojson_files
        self.export_gpkg_files = export_gpkg_files  # bug 2 corrigido

        self.csv_path     = os.path.join(self.output_dir, f"{table_name}.csv")
        self.geojson_path = os.path.join(self.output_dir, f"{table_name}.geojson")
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
                if self.export_csv_files:
                    export_csv(table, self.output_dir)
                if self.export_geojson_files:
                    export_geojson(table, self.output_dir,
                                   lat_hint=self.lat_hint, lon_hint=self.lon_hint)
                # bug 2 corrigido: export_gpkg_files agora é realmente usado
                if self.export_gpkg_files:
                    from .middleware import GpkgWriter, DyndbReader
                    reader = DyndbReader(self.data_dir, self.lat_hint, self.lon_hint)
                    GpkgWriter().write(reader.read(self.table_name), self.output_dir)

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
