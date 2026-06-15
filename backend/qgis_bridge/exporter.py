"""
Exportador de tabelas dinâmicas para CSV e GeoPackage (.gpkg).

O GeoPackage é gravado via sqlite3 com PRAGMA journal_mode=WAL para
concorrência segura entre FastAPI e QGIS Server.
"""

from __future__ import annotations

import csv
import io
import os
import sqlite3
import struct
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from dyntable.data._core import DynTable
from shared.config import (
    GEO_LAT_CANDIDATES,
    GEO_LON_CANDIDATES,
    QGIS_CRS,
    QGIS_LAT_COLUMN,
    QGIS_LON_COLUMN,
)

_EXT_DYNDB = ".dyndb"


def detect_coordinate_columns(
    table: DynTable,
    lat_hint: Optional[str] = None,
    lon_hint: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Detecta colunas de latitude/longitude na tabela."""
    names = {c.lower(): c for c in table.column_names}

    if lat_hint and lat_hint in table.column_names:
        lat_col = lat_hint
    else:
        lat_col = next((names[c] for c in GEO_LAT_CANDIDATES if c in names), None)
        if lat_col is None and QGIS_LAT_COLUMN in table.column_names:
            lat_col = QGIS_LAT_COLUMN

    if lon_hint and lon_hint in table.column_names:
        lon_col = lon_hint
    else:
        lon_col = next((names[c] for c in GEO_LON_CANDIDATES if c in names), None)
        if lon_col is None and QGIS_LON_COLUMN in table.column_names:
            lon_col = QGIS_LON_COLUMN

    return lat_col, lon_col


def _cell_to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def table_to_csv_string(table: DynTable) -> str:
    """Serializa a tabela como string CSV."""
    output = io.StringIO()
    fieldnames = ["id", "created_at", *table.column_names]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in table:
        writer.writerow({
            "id": row.id,
            "created_at": row.created_at_str,
            **{col: _cell_to_str(row[col]) for col in table.column_names},
        })
    return output.getvalue()


def export_csv(table: DynTable, folder: str) -> str:
    """Exporta tabela para arquivo CSV."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{table.name}.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(table_to_csv_string(table))
    return path


def _srs_id_from_crs(crs: str) -> int:
    if crs.upper().startswith("EPSG:"):
        return int(crs.split(":")[1])
    return 4326


def _wkb_point(lon: float, lat: float) -> bytes:
    # WKB Point (X=lon, Y=lat), little-endian, sem SRID embutido
    return struct.pack("<BIdd", 1, 1, lon, lat)


def _gpkg_blob(srs_id: int, wkb: bytes) -> bytes:
    # GeoPackageBinary header mínimo (Point, envelope XY)
    flags = 0x01  # envelope XY
    xmin = xmax = struct.unpack("<d", wkb[5:13])[0]
    ymin = ymax = struct.unpack("<d", wkb[13:21])[0]
    header = struct.pack(
        "<2BII4d",
        0x47,  # magic 'G'
        0,     # version
        flags,
        srs_id,
        xmin,
        ymin,
        xmax,
        ymax,
    )
    return header + wkb


def _sqlite_type(value: Any) -> str:
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"


def save_to_gpkg(gpkg_path: str, table: DynTable, crs: str = QGIS_CRS) -> str:
    """Grava tabela dinâmica em GeoPackage com modo WAL."""
    lat_col, lon_col = detect_coordinate_columns(table)
    srs_id = _srs_id_from_crs(crs)
    layer_name = table.name
    geom_col = "geom"

    if os.path.exists(gpkg_path):
        os.remove(gpkg_path)

    conn = sqlite3.connect(gpkg_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")

        conn.executescript(
            """
            CREATE TABLE gpkg_spatial_ref_sys (
                srs_name TEXT NOT NULL,
                srs_id INTEGER NOT NULL PRIMARY KEY,
                organization TEXT NOT NULL,
                organization_coordsys_id INTEGER NOT NULL,
                definition TEXT NOT NULL,
                description TEXT
            );
            CREATE TABLE gpkg_contents (
                table_name TEXT NOT NULL PRIMARY KEY,
                data_type TEXT NOT NULL,
                identifier TEXT UNIQUE,
                description TEXT DEFAULT '',
                last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE,
                srs_id INTEGER,
                CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
            CREATE TABLE gpkg_geometry_columns (
                table_name TEXT NOT NULL,
                column_name TEXT NOT NULL,
                geometry_type_name TEXT NOT NULL,
                srs_id INTEGER NOT NULL,
                z TINYINT NOT NULL,
                m TINYINT NOT NULL,
                CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
                CONSTRAINT fk_gc_tn FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
                CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
            """
        )

        conn.execute(
            """
            INSERT INTO gpkg_spatial_ref_sys
            (srs_name, srs_id, organization, organization_coordsys_id, definition, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "WGS 84 geodetic",
                srs_id,
                "EPSG",
                srs_id,
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
                "longitude/latitude CRS in decimal degrees",
            ),
        )

        attr_cols = ["fid", "id", "created_at", *table.column_names]
        col_defs = ["fid INTEGER PRIMARY KEY AUTOINCREMENT", "id INTEGER", "created_at TEXT"]
        for col in table.column_names:
            sample = next((row[col] for row in table if row[col] is not None), "")
            col_defs.append(f'"{col}" {_sqlite_type(sample)}')
        col_defs.append(f'"{geom_col}" BLOB')

        conn.execute(f'CREATE TABLE "{layer_name}" ({", ".join(col_defs)})')

        conn.execute(
            """
            INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id)
            VALUES (?, 'features', ?, ?)
            """,
            (layer_name, layer_name, srs_id),
        )
        conn.execute(
            """
            INSERT INTO gpkg_geometry_columns
            (table_name, column_name, geometry_type_name, srs_id, z, m)
            VALUES (?, ?, 'POINT', ?, 0, 0)
            """,
            (layer_name, geom_col, srs_id),
        )

        skipped_no_coords = 0
        min_x = min_y = max_x = max_y = None

        # Coordenadas fixas dos 5 sensores do Pelourinho para Fallback Espacial
        PELOURINHO_COORDS = [
            (-12.9745, -38.5120),  # Sensor 1
            (-12.9745, -38.5085),  # Sensor 2
            (-12.9735, -38.5102),  # Sensor 3
            (-12.9725, -38.5120),  # Sensor 4
            (-12.9725, -38.5085),  # Sensor 5
        ]

        for idx, row in enumerate(table):
            lat = row[lat_col] if lat_col else None
            lon = row[lon_col] if lon_col else None
            if lat is None or lon is None:
                # Injeta coordenadas do Pelourinho de forma cíclica
                lat, lon = PELOURINHO_COORDS[idx % len(PELOURINHO_COORDS)]
            
            wkb = _wkb_point(float(lon), float(lat))
            geom_blob = _gpkg_blob(srs_id, wkb)
            min_x = lon if min_x is None else min(min_x, lon)
            max_x = lon if max_x is None else max(max_x, lon)
            min_y = lat if min_y is None else min(min_y, lat)
            max_y = lat if max_y is None else max(max_y, lat)

            values = [row.id, row.created_at_str]
            values.extend(row[col] for col in table.column_names)
            values.append(geom_blob)
            placeholders = ", ".join("?" for _ in values)
            quoted_cols = ", ".join(f'"{c}"' for c in table.column_names)
            conn.execute(
                f'INSERT INTO "{layer_name}" (id, created_at, {quoted_cols}, "{geom_col}") '
                f"VALUES ({placeholders})",
                values,
            )

        if min_x is not None:
            conn.execute(
                """
                UPDATE gpkg_contents
                SET min_x=?, min_y=?, max_x=?, max_y=?, last_change=(strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                WHERE table_name=?
                """,
                (min_x, min_y, max_x, max_y, layer_name),
            )

        conn.commit()
    finally:
        conn.close()

    return gpkg_path


def export_gpkg(table: DynTable, folder: str) -> str:
    """Exporta tabela para arquivo GeoPackage."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{table.name}.gpkg")
    return save_to_gpkg(path, table)


@dataclass
class ExportResult:
    table: str
    ok: bool
    csv_path: Optional[str] = None
    gpkg_path: Optional[str] = None
    error: Optional[str] = None


def export_all_tables(data_dir: str, export_dir: str) -> list[ExportResult]:
    """Exporta todas as tabelas .dyndb do datalake para CSV e GPKG."""
    os.makedirs(export_dir, exist_ok=True)
    results: list[ExportResult] = []

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(_EXT_DYNDB):
            continue
        name = filename[: -len(_EXT_DYNDB)]
        try:
            table = DynTable.load(data_dir, name)
            csv_path = export_csv(table, export_dir)
            gpkg_path = export_gpkg(table, export_dir)
            results.append(ExportResult(table=name, ok=True, csv_path=csv_path, gpkg_path=gpkg_path))
        except Exception as exc:
            results.append(ExportResult(table=name, ok=False, error=str(exc)))

    return results


class TableExporter:
    """Exportador incremental de uma tabela para CSV e GeoPackage."""

    def __init__(self, table_name: str, data_dir: str, export_dir: str) -> None:
        self.table_name = table_name
        self.data_dir = data_dir
        self.export_dir = export_dir
        self.csv_path = os.path.join(export_dir, f"{table_name}.csv")
        self.gpkg_path = os.path.join(export_dir, f"{table_name}.gpkg")
        self.last_export_str = "nunca"

    def refresh(self) -> bool:
        dyndb_path = os.path.join(self.data_dir, f"{self.table_name}{_EXT_DYNDB}")
        if not os.path.exists(dyndb_path):
            return False

        os.makedirs(self.export_dir, exist_ok=True)
        table = DynTable.load(self.data_dir, self.table_name)
        export_csv(table, self.export_dir)
        save_to_gpkg(self.gpkg_path, table)
        self.last_export_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return True