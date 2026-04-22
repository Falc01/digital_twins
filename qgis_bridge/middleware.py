from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import struct
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


_LAT_CANDIDATES = {"lat", "latitude", "lat_grau", "y", "coord_y", "geo_lat"}
_LON_CANDIDATES = {"lon", "long", "longitude", "lng", "lon_grau", "x", "coord_x", "geo_lon"}


@dataclass
class RowData:
    row_id: int
    created_at: str
    values: dict[str, Any]


@dataclass
class TableData:
    name: str
    column_names: list[str]
    column_types: dict[str, str]
    rows: list[RowData]
    lat_col: str | None = None
    lon_col: str | None = None


def detect_coordinate_columns(
    column_names: list[str],
    lat_hint: str | None = None,
    lon_hint: str | None = None,
) -> tuple[str | None, str | None]:
    names_lower = {n.lower(): n for n in column_names}

    def _pick(candidates: set[str], hint: str | None) -> str | None:
        if hint and hint in column_names:
            return hint
        for cand in candidates:
            if cand in names_lower:
                return names_lower[cand]
        return None

    return _pick(_LAT_CANDIDATES, lat_hint), _pick(_LON_CANDIDATES, lon_hint)


class BaseReader(ABC):
    @abstractmethod
    def read(self, table_name: str) -> TableData: ...

    @abstractmethod
    def exists(self, table_name: str) -> bool: ...

    @abstractmethod
    def list_tables(self) -> list[str]: ...


class BaseWriter(ABC):
    @property
    @abstractmethod
    def extension(self) -> str: ...

    @abstractmethod
    def write(self, data: TableData, output_dir: str) -> str: ...


class DyndbReader(BaseReader):
    def __init__(self, data_dir: str, lat_hint: str | None = None, lon_hint: str | None = None) -> None:
        self._data_dir = data_dir
        self._lat_hint = lat_hint
        self._lon_hint = lon_hint

    def list_tables(self) -> list[str]:
        from table_manager import TableManager
        return TableManager(self._data_dir).list_tables()

    def exists(self, table_name: str) -> bool:
        from table_manager import TableManager
        return TableManager(self._data_dir).exists(table_name)

    def read(self, table_name: str) -> TableData:
        from table_manager import TableManager
        table = TableManager(self._data_dir).get(table_name)
        lat_col, lon_col = detect_coordinate_columns(
            table.column_names, self._lat_hint, self._lon_hint
        )
        col_types = {col.name: col.dtype.name for col in table.columns}
        rows = [
            RowData(
                row_id=row.id,
                created_at=row.created_at_str,
                values={col: row[col] for col in table.column_names},
            )
            for row in table
        ]
        return TableData(
            name=table_name,
            column_names=table.column_names,
            column_types=col_types,
            rows=rows,
            lat_col=lat_col,
            lon_col=lon_col,
        )


class CsvWriter(BaseWriter):
    @property
    def extension(self) -> str:
        return ".csv"

    def write(self, data: TableData, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{data.name}.csv")
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["id", "created_at"] + data.column_names)
        for row in data.rows:
            writer.writerow(
                [row.row_id, row.created_at]
                + [("" if row.values.get(c) is None else row.values[c]) for c in data.column_names]
            )
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(buf.getvalue())
        return path


class GeoJsonWriter(BaseWriter):
    def __init__(self, indent: int | None = None) -> None:
        self._indent = indent

    @property
    def extension(self) -> str:
        return ".geojson"

    def write(self, data: TableData, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{data.name}.geojson")
        features = []
        skipped = 0
        if data.lat_col and data.lon_col:
            for row in data.rows:
                feat = self._to_feature(row, data.column_names, data.lat_col, data.lon_col)
                if feat is not None:
                    features.append(feat)
                else:
                    skipped += 1
        geojson = {
            "type": "FeatureCollection",
            "name": data.name,
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
            "_meta": {
                "table": data.name,
                "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_rows": len(data.rows),
                "exported_features": len(features),
                "skipped_no_coords": skipped,
                "lat_col": data.lat_col,
                "lon_col": data.lon_col,
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=self._indent)
        return path

    def _to_feature(self, row: RowData, col_names: list[str],
                    lat_col: str, lon_col: str) -> dict | None:
        try:
            lat = float(row.values[lat_col])
            lon = float(row.values[lon_col])
        except (TypeError, ValueError, KeyError):
            return None
        props: dict[str, Any] = {"id": row.row_id, "created_at": row.created_at}
        for col in col_names:
            props[col] = row.values.get(col)
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        }


class GpkgWriter(BaseWriter):
    _DYNTYPE_TO_SQLITE: dict[str, str] = {
        "INT": "INTEGER", "FLOAT": "REAL", "STRING": "TEXT",
        "BOOL": "INTEGER", "TIMESTAMP": "REAL", "BYTES": "BLOB",
        "AUTO": "TEXT", "NULL": "TEXT",
    }

    def __init__(self, srid: int = 4326) -> None:
        self._srid = srid

    @property
    def extension(self) -> str:
        return ".gpkg"

    def write(self, data: TableData, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{data.name}.gpkg")
        con = sqlite3.connect(path)
        try:
            self._bootstrap(con)
            if data.lat_col and data.lon_col:
                self._write_spatial(con, data)
            else:
                self._write_attributes(con, data)
            con.commit()
        finally:
            con.close()
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
                last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S.000Z','now')),
                min_x REAL, min_y REAL, max_x REAL, max_y REAL, srs_id INTEGER,
                FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
            CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
                table_name TEXT NOT NULL, column_name TEXT NOT NULL,
                geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
                z TINYINT NOT NULL, m TINYINT NOT NULL,
                CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
                CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
        """)
        con.execute("""
            INSERT OR IGNORE INTO gpkg_spatial_ref_sys VALUES (
                'WGS 84 geodetic', 4326, 'EPSG', 4326,
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
                'longitude/latitude coordinates in decimal degrees on the WGS 84 spheroid'
            )
        """)

    def _col_defs(self, data: TableData, with_geom: bool = False) -> str:
        parts = []
        if with_geom:
            parts.append("geom BLOB")
        parts += ["id INTEGER PRIMARY KEY", "created_at TEXT"]
        for col_name in data.column_names:
            sqlite_type = self._DYNTYPE_TO_SQLITE.get(data.column_types.get(col_name, "AUTO"), "TEXT")
            parts.append(f'"{col_name}" {sqlite_type}')
        return ", ".join(parts)

    def _row_values(self, row: RowData, col_names: list[str],
                    geom: bytes | None = None, include_geom: bool = False) -> list:
        base = [row.row_id, row.created_at] + [row.values.get(c) for c in col_names]
        return ([geom] + base) if include_geom else base

    def _write_spatial(self, con: sqlite3.Connection, data: TableData) -> None:
        tname = data.name
        con.execute(f'DROP TABLE IF EXISTS "{tname}"')
        con.execute(f'CREATE TABLE "{tname}" ({self._col_defs(data, with_geom=True)})')
        con.execute(
            "INSERT OR REPLACE INTO gpkg_geometry_columns VALUES (?, 'geom', 'POINT', ?, 0, 0)",
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
            INSERT OR REPLACE INTO gpkg_contents
            VALUES (?, 'features', ?, '', strftime('%Y-%m-%dT%H:%M:%S.000Z','now'), ?, ?, ?, ?, ?)
        """, (tname, tname,
               min(lons) if lons else None, min(lats) if lats else None,
               max(lons) if lons else None, max(lats) if lats else None,
               self._srid))
        placeholders = ",".join(["?"] * (3 + len(data.column_names)))
        sql = f'INSERT INTO "{tname}" VALUES ({placeholders})'
        for row in data.rows:
            try:
                geom = self._point_wkb(float(row.values[data.lon_col]), float(row.values[data.lat_col]))
            except (TypeError, ValueError, KeyError):
                geom = None
            con.execute(sql, self._row_values(row, data.column_names, geom=geom, include_geom=True))

    def _write_attributes(self, con: sqlite3.Connection, data: TableData) -> None:
        tname = data.name
        con.execute(f'DROP TABLE IF EXISTS "{tname}"')
        con.execute(f'CREATE TABLE "{tname}" ({self._col_defs(data, with_geom=False)})')
        con.execute("""
            INSERT OR REPLACE INTO gpkg_contents
            VALUES (?, 'attributes', ?, '', strftime('%Y-%m-%dT%H:%M:%S.000Z','now'),
                    NULL, NULL, NULL, NULL, NULL)
        """, (tname, tname))
        placeholders = ",".join(["?"] * (2 + len(data.column_names)))
        sql = f'INSERT INTO "{tname}" VALUES ({placeholders})'
        for row in data.rows:
            con.execute(sql, self._row_values(row, data.column_names))

    def _point_wkb(self, lon: float, lat: float) -> bytes:
        header = b"GP\x00\x01" + struct.pack("<i", self._srid)
        wkb = struct.pack("<bIdd", 1, 1, lon, lat)
        return header + wkb


class ExportPipeline:
    def __init__(self, reader: BaseReader, writers: list[BaseWriter]) -> None:
        self._reader = reader
        self._writers = writers

    def refresh(self, table_name: str, output_dir: str) -> dict[str, str]:
        data = self._reader.read(table_name)
        return {w.extension: w.write(data, output_dir) for w in self._writers}

    def refresh_all(self, output_dir: str) -> dict[str, dict[str, str]]:
        return {name: self.refresh(name, output_dir) for name in self._reader.list_tables()}

    def exists(self, table_name: str) -> bool:
        return self._reader.exists(table_name)

    def list_tables(self) -> list[str]:
        return self._reader.list_tables()

    def output_paths(self, table_name: str, output_dir: str) -> dict[str, str]:
        return {w.extension: os.path.join(output_dir, f"{table_name}{w.extension}") for w in self._writers}


def build_default_pipeline(
    data_dir: str,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
    export_csv: bool = True,
    export_geojson: bool = True,
    export_gpkg: bool = True,
    geojson_indent: int | None = None,
    gpkg_srid: int = 4326,
) -> ExportPipeline:
    reader: BaseReader = DyndbReader(data_dir, lat_hint=lat_hint, lon_hint=lon_hint)
    writers: list[BaseWriter] = []
    if export_csv:
        writers.append(CsvWriter())
    if export_geojson:
        writers.append(GeoJsonWriter(indent=geojson_indent))
    if export_gpkg:
        writers.append(GpkgWriter(srid=gpkg_srid))
    return ExportPipeline(reader, writers)
