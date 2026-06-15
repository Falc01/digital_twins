from __future__ import annotations

import logging
import os
import sqlite3
import struct
from abc import ABC, abstractmethod
from typing import Optional
from src.qgis.data.models import TableData, RowData

logger = logging.getLogger("qgis_bridge.writer")

class BaseWriter(ABC):
    @property
    @abstractmethod
    def extension(self) -> str: ...

    @abstractmethod
    def write(self, data: TableData, output_dir: str) -> str: ...

class GpkgWriter(BaseWriter):
    _DYNTYPE_TO_SQLITE: dict[str, str] = {
        "INT": "INTEGER", "FLOAT": "REAL", "STRING": "TEXT",
        "BOOL": "INTEGER", "TIMESTAMP": "REAL", "BYTES": "BLOB",
        "AUTO": "TEXT",    "NULL": "TEXT",
    }

    def __init__(self, srid: int = 4326) -> None:
        self._srid = srid

    @property
    def extension(self) -> str:
        return ".gpkg"

    def write(self, data: TableData, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{data.name}.gpkg")
        con  = sqlite3.connect(path)
        try:
            self._bootstrap(con)
            if data.lat_col and data.lon_col:
                self._write_spatial(con, data)
            else:
                self._write_attributes(con, data)
            con.commit()
        finally:
            con.close()
        logger.info("GPKG escrito: %s (%d linhas)", path, len(data.rows))
        return path

    def _bootstrap(self, con: sqlite3.Connection) -> None:
        con.execute("PRAGMA application_id = 0x47504B47")
        con.execute("PRAGMA user_version = 10200")
        con.executescript("""
            CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys (
                srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
                organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
                definition TEXT NOT NULL, description TEXT
            );
            CREATE TABLE IF NOT EXISTS gpkg_contents (
                table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
                identifier TEXT, description TEXT DEFAULT '',
                last_change DATETIME NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%S.000Z','now')),
                min_x REAL, min_y REAL, max_x REAL, max_y REAL, srs_id INTEGER,
                FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
            CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
                table_name TEXT NOT NULL, column_name TEXT NOT NULL,
                geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
                z TINYINT NOT NULL, m TINYINT NOT NULL,
                CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
                CONSTRAINT fk_gc_srs
                    FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
        """)
        con.execute("""
            INSERT OR IGNORE INTO gpkg_spatial_ref_sys VALUES (
                'WGS 84 geodetic', 4326, 'EPSG', 4326,
                'GEOGCS["WGS 84",DATUM["WGS_1984",
                  SPHEROID["WGS 84",6378137,298.257223563]],
                  PRIMEM["Greenwich",0],
                  UNIT["degree",0.0174532925199433]]',
                'longitude/latitude in decimal degrees on WGS 84'
            )
        """)

    def _col_defs(self, data: TableData, with_geom: bool = False) -> str:
        parts = []
        if with_geom:
            parts.append("geom POINT")
        parts += ["id INTEGER PRIMARY KEY", "created_at TEXT"]
        for col_name in data.column_names:
            sqlite_type = self._DYNTYPE_TO_SQLITE.get(
                data.column_types.get(col_name, "AUTO"), "TEXT"
            )
            parts.append(f'"{col_name}" {sqlite_type}')
        return ", ".join(parts)

    def _row_values(
        self,
        row: RowData,
        col_names: list[str],
        geom: Optional[bytes] = None,
        include_geom: bool = False,
    ) -> list:
        base = [row.row_id, row.created_at] + [row.values.get(c) for c in col_names]
        return ([geom] + base) if include_geom else base

    def _write_spatial(self, con: sqlite3.Connection, data: TableData) -> None:
        tname = data.name
        con.execute(f'DROP TABLE IF EXISTS "{tname}"')
        con.execute(f'CREATE TABLE "{tname}" ({self._col_defs(data, with_geom=True)})')
        con.execute(
            "INSERT OR REPLACE INTO gpkg_geometry_columns "
            "VALUES (?, 'geom', 'POINT', ?, 0, 0)",
            (tname, self._srid),
        )
        lons, lats = [], []
        for row in data.rows:
            try:
                lons.append(float(row.values[data.lon_col]))
                lats.append(float(row.values[data.lat_col]))
            except (TypeError, ValueError, KeyError):
                pass
        con.execute("""
            INSERT OR REPLACE INTO gpkg_contents VALUES (
                ?, 'features', ?, '',
                strftime('%Y-%m-%dT%H:%M:%S.000Z','now'),
                ?, ?, ?, ?, ?
            )
        """, (tname, tname,
              min(lons) if lons else None, min(lats) if lats else None,
              max(lons) if lons else None, max(lats) if lats else None,
              self._srid))
        placeholders = ",".join(["?"] * (3 + len(data.column_names)))
        sql = f'INSERT INTO "{tname}" VALUES ({placeholders})'
        for row in data.rows:
            try:
                geom = self._point_wkb(
                    float(row.values[data.lon_col]),
                    float(row.values[data.lat_col]),
                )
            except (TypeError, ValueError, KeyError):
                geom = None
            con.execute(sql, self._row_values(
                row, data.column_names, geom=geom, include_geom=True
            ))

    def _write_attributes(self, con: sqlite3.Connection, data: TableData) -> None:
        tname = data.name
        con.execute(f'DROP TABLE IF EXISTS "{tname}"')
        con.execute(f'CREATE TABLE "{tname}" ({self._col_defs(data, with_geom=False)})')
        con.execute("""
            INSERT OR REPLACE INTO gpkg_contents VALUES (
                ?, 'attributes', ?, '',
                strftime('%Y-%m-%dT%H:%M:%S.000Z','now'),
                NULL, NULL, NULL, NULL, NULL
            )
        """, (tname, tname))
        placeholders = ",".join(["?"] * (2 + len(data.column_names)))
        sql = f'INSERT INTO "{tname}" VALUES ({placeholders})'
        for row in data.rows:
            con.execute(sql, self._row_values(row, data.column_names))

    def _point_wkb(self, lon: float, lat: float) -> bytes:
        header = b"GP\x00\x01" + struct.pack("<i", self._srid)
        wkb    = struct.pack("<bIdd", 1, 1, lon, lat)
        return header + wkb
