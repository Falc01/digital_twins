from __future__ import annotations

import logging
import os
import sqlite3
import struct
import sys
import time
from typing import Any

# Adiciona o diretório backend/src ao sys.path para carregar o dyntable
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_HERE, "..", ".."))
_BACKEND_SRC = os.path.join(_WORKSPACE, "backend", "src")
if _BACKEND_SRC not in sys.path:
    sys.path.insert(0, _BACKEND_SRC)

try:
    from dyntable import DynTable, DynType
except ImportError:
    # Fallback/stub para possibilitar execução do script em ambientes isolados
    class DynType:
        INT = 0
        FLOAT = 1
        STRING = 2
        BOOL = 3
        TIMESTAMP = 4
        BYTES = 5
        AUTO = 99
        NULL = 255

logger = logging.getLogger("qgis_bridge.gpkg_sync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Mapeamento do DynType para tipos do SQLite
_DYNTYPE_TO_SQLITE = {
    0: "INTEGER",    # DynType.INT
    1: "REAL",       # DynType.FLOAT
    2: "TEXT",       # DynType.STRING
    3: "INTEGER",    # DynType.BOOL
    4: "REAL",       # DynType.TIMESTAMP
    5: "BLOB",       # DynType.BYTES
    99: "TEXT",      # DynType.AUTO
    255: "TEXT",     # DynType.NULL
}

_LAT_CANDIDATES = {"lat", "latitude", "lat_grau", "y", "coord_y", "geo_lat"}
_LON_CANDIDATES = {"lon", "long", "longitude", "lng", "lon_grau", "x", "coord_x", "geo_lon"}


def detect_coordinate_columns(
    table: Any,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Detecta automaticamente as colunas de coordenadas a partir do nome.
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


def make_point_gpkg_wkb(lon: float, lat: float, srid: int = 4326) -> bytes:
    """
    Gera o cabeçalho binário padrão do GeoPackage (8 bytes) + WKB Point.
    """
    # Header GP (2 bytes) + Version 0 (1 byte) + Flags 1 (little-endian header, no envelope) + SRS_ID (4 bytes)
    header = b"GP\x00\x01" + struct.pack("<i", srid)
    # WKB padrão: byte order (1 = little endian) + geom type (1 = Point) + X (lon) + Y (lat)
    wkb = struct.pack("<bIdd", 1, 1, lon, lat)
    return header + wkb


def bootstrap_gpkg_metadata(conn: sqlite3.Connection, srid: int = 4326) -> None:
    """
    Cria as tabelas de metadados obrigatórias para o padrão GeoPackage (.gpkg).
    """
    conn.execute("PRAGMA application_id = 0x47504B47")  # "GPKG" em hex
    conn.execute("PRAGMA user_version = 10200")        # Versão GPKG 1.2.0

    # Criação das tabelas de metadados padrão OGC
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT,
            description TEXT DEFAULT '',
            last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S.000Z','now')),
            min_x REAL,
            min_y REAL,
            max_x REAL,
            max_y REAL,
            srs_id INTEGER,
            FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
        );
        CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
            CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
        );
    """)

    # Garante a inserção do CRS WGS 84 (EPSG:4326) se não existir
    conn.execute("""
        INSERT OR IGNORE INTO gpkg_spatial_ref_sys VALUES (
            'WGS 84 geodetic', 4326, 'EPSG', 4326,
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
            'longitude/latitude in decimal degrees on WGS 84'
        )
    """)


def sync_table_to_gpkg(
    table: Any,
    output_dir: str,
    lat_hint: str | None = None,
    lon_hint: str | None = None,
    srid: int = 4326,
) -> str:
    """
    Sincroniza uma DynTable para um arquivo GeoPackage (.gpkg) ativando o modo WAL.
    Re-cria a tabela física do sensor e atualiza os metadados espaciais de limite.
    """
    os.makedirs(output_dir, exist_ok=True)
    gpkg_path = os.path.join(output_dir, f"{table.name}.gpkg")
    tname = table.name

    # Conecta ao SQLite
    conn = sqlite3.connect(gpkg_path)
    try:
        # ── 1. Ativação do Modo WAL para Concorrência Segura ──────────────────
        conn.execute("PRAGMA journal_mode=WAL;")
        bootstrap_gpkg_metadata(conn, srid)

        # ── 2. Detecção de Colunas de Coordenadas ────────────────────────────
        lat_col, lon_col = detect_coordinate_columns(table, lat_hint, lon_hint)
        is_spatial = lat_col is not None and lon_col is not None

        # ── 3. Construção do Schema DDL ──────────────────────────────────────
        columns_ddl = []
        if is_spatial:
            columns_ddl.append("geom POINT")
        columns_ddl.append("id INTEGER PRIMARY KEY")
        columns_ddl.append("created_at TEXT")

        for col_name in table.column_names:
            # Pula as colunas de lat/lon originais se formos representá-las apenas na geometria,
            # mas é comum mantê-las também como atributos alfanuméricos. Vamos mantê-las por segurança.
            col_type = table._columns[col_name].dtype
            sqlite_type = _DYNTYPE_TO_SQLITE.get(int(col_type), "TEXT")
            columns_ddl.append(f'"{col_name}" {sqlite_type}')

        # Re-cria a tabela alfanumérica/vetorial
        conn.execute(f'DROP TABLE IF EXISTS "{tname}"')
        conn.execute(f'CREATE TABLE "{tname}" ({", ".join(columns_ddl)})')

        # ── 4. Inserção de Registros & Cálculo de Bounding Box ───────────────
        lats, lons = [], []
        placeholders = ", ".join(["?"] * (len(columns_ddl)))
        insert_sql = f'INSERT INTO "{tname}" VALUES ({placeholders})'

        for row in table:
            geom_bytes = None
            if is_spatial:
                try:
                    lat_val = row[lat_col]
                    lon_val = row[lon_col]
                    if lat_val is not None and lon_val is not None:
                        lat_f = float(lat_val)
                        lon_f = float(lon_val)
                        lats.append(lat_f)
                        lons.append(lon_f)
                        geom_bytes = make_point_gpkg_wkb(lon_f, lat_f, srid)
                except (ValueError, TypeError):
                    pass

            # Prepara os valores correspondentes ao DDL da linha
            row_vals = []
            if is_spatial:
                row_vals.append(geom_bytes)
            row_vals.append(row.id)
            row_vals.append(row.created_at_str)

            for col_name in table.column_names:
                row_vals.append(row[col_name])

            conn.execute(insert_sql, row_vals)

        # ── 5. Atualização de Registros de Metadados do GeoPackage ────────────
        if is_spatial:
            # Registra a coluna de geometria no GPKG
            conn.execute("DELETE FROM gpkg_geometry_columns WHERE table_name = ?", (tname,))
            conn.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?, 'geom', 'POINT', ?, 0, 0)",
                (tname, srid),
            )

        # Atualiza limites espaciais e conteúdo
        min_x = min(lons) if lons else None
        min_y = min(lats) if lats else None
        max_x = max(lons) if lons else None
        max_y = max(lats) if lats else None

        conn.execute("DELETE FROM gpkg_contents WHERE table_name = ?", (tname,))
        conn.execute(
            """
            INSERT INTO gpkg_contents (table_name, data_type, identifier, description, min_x, min_y, max_x, max_y, srs_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tname,
                "features" if is_spatial else "attributes",
                tname,
                f"Tabela de dados e telemetria {tname}",
                min_x,
                min_y,
                max_x,
                max_y,
                srid if is_spatial else None,
            ),
        )

        conn.commit()
        logger.info("GeoPackage sincronizado com sucesso: %s (linhas: %d)", gpkg_path, len(table))
    finally:
        conn.close()

    return gpkg_path
