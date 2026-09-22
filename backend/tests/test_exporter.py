"""
tests/test_exporter.py
======================
Testes do exporter sem dependência do QGIS.
Execute com: python -m pytest tests/ -v
         ou: python tests/test_exporter.py
"""

import json
import os
import sys
import tempfile
import time

# Garante que a raiz do projeto está no path
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from dyntable import DynTable, DynType
from qgis_bridge.exporter import (
    TableExporter,
    detect_coordinate_columns,
    export_all_tables,
    export_csv,
    export_gpkg,
    save_to_gpkg,
    table_to_csv_string,
)
import sqlite3


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _make_sensor_table(name: str = "sensores") -> DynTable:
    t = DynTable(name)
    t.add_column("device_id",    DynType.STRING)
    t.add_column("latitude",     DynType.FLOAT)
    t.add_column("longitude",    DynType.FLOAT)
    t.add_column("temperatura",  DynType.FLOAT)
    t.add_column("ativo",        DynType.BOOL)

    t.new_row(device_id="S01", latitude=-12.971, longitude=-38.501, temperatura=24.5, ativo=True)
    t.new_row(device_id="S02", latitude=-23.550, longitude=-46.633, temperatura=21.0, ativo=True)
    t.new_row(device_id="S03", latitude=-15.780, longitude=-47.929, temperatura=29.1, ativo=False)
    # Linha sem coordenadas → deve ser ignorada no GeoJSON
    t.new_row(device_id="S04", temperatura=18.0, ativo=True)
    return t


def _make_table_no_coords(name: str = "sem_coords") -> DynTable:
    t = DynTable(name)
    t.add_column("nome",  DynType.STRING)
    t.add_column("valor", DynType.FLOAT)
    t.new_row(nome="A", valor=1.0)
    t.new_row(nome="B", valor=2.0)
    return t


# ─────────────────────────────────────────────
#  Testes
# ─────────────────────────────────────────────

def test_detect_coordinate_columns_by_name():
    t = _make_sensor_table()
    lat, lon = detect_coordinate_columns(t)
    assert lat == "latitude",  f"Esperado 'latitude', obtido {lat!r}"
    assert lon == "longitude", f"Esperado 'longitude', obtido {lon!r}"
    print("✓ detect_coordinate_columns — nomes padrão")


def test_detect_coordinate_columns_aliases():
    t = DynTable("alias_test")
    t.add_column("lat",  DynType.FLOAT)
    t.add_column("long", DynType.FLOAT)
    lat, lon = detect_coordinate_columns(t)
    assert lat == "lat",  f"Esperado 'lat', obtido {lat!r}"
    assert lon == "long", f"Esperado 'long', obtido {lon!r}"
    print("✓ detect_coordinate_columns — aliases (lat / long)")


def test_detect_coordinate_columns_hints():
    t = DynTable("hint_test")
    t.add_column("coord_y_custom", DynType.FLOAT)
    t.add_column("coord_x_custom", DynType.FLOAT)
    lat, lon = detect_coordinate_columns(t, lat_hint="coord_y_custom", lon_hint="coord_x_custom")
    assert lat == "coord_y_custom"
    assert lon == "coord_x_custom"
    print("✓ detect_coordinate_columns — hints explícitos")


def test_detect_no_coords():
    t = _make_table_no_coords()
    lat, lon = detect_coordinate_columns(t)
    assert lat is None and lon is None
    print("✓ detect_coordinate_columns — sem coordenadas → (None, None)")


def test_csv_string_columns():
    t = _make_sensor_table()
    csv_str = table_to_csv_string(t)
    lines = csv_str.strip().splitlines()
    header = lines[0].split(",")
    assert "id" in header
    assert "created_at" in header
    assert "latitude" in header
    assert "longitude" in header
    assert "device_id" in header
    print(f"✓ table_to_csv_string — header correto: {header}")


def test_csv_string_row_count():
    t = _make_sensor_table()
    csv_str = table_to_csv_string(t)
    lines = csv_str.strip().splitlines()
    # 1 header + 4 linhas de dados
    assert len(lines) == 5, f"Esperado 5 linhas, obtido {len(lines)}"
    print(f"✓ table_to_csv_string — {len(lines)-1} linha(s) de dados")


def test_csv_none_as_empty_string():
    t = _make_sensor_table()
    csv_str = table_to_csv_string(t)
    # S04 não tem lat/lon → devem aparecer como campo vazio
    s04_line = [l for l in csv_str.splitlines() if "S04" in l][0]
    parts = s04_line.split(",")
    # lat e lon são colunas 4 e 5 (id, created_at, device_id, latitude, longitude, ...)
    assert "" in parts, f"Esperado campo vazio para None, linha: {s04_line!r}"
    print(f"✓ table_to_csv_string — None vira campo vazio")


def test_gpkg_creation_and_wal(tmp_path):
    t = _make_sensor_table()
    gpkg_path = os.path.join(tmp_path, "sensores.gpkg")
    path = save_to_gpkg(gpkg_path, t)
    assert path == gpkg_path
    assert os.path.exists(gpkg_path)
    
    conn = sqlite3.connect(gpkg_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "gpkg_contents" in tables
        assert "gpkg_geometry_columns" in tables
        assert "sensores" in tables
        
        cursor.execute("SELECT id, device_id, temperatura, ativo FROM sensores ORDER BY id")
        rows = cursor.fetchall()
        assert len(rows) == 4
        assert rows[0] == (1, "S01", 24.5, 1)
    finally:
        conn.close()
    print("✓ test_gpkg_creation_and_wal — GPKG criado em modo WAL com dados alfanuméricos")


def test_export_csv_file(tmp_path):
    t = _make_sensor_table()
    path = export_csv(t, str(tmp_path))
    assert os.path.exists(path), f"Arquivo não criado: {path}"
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "device_id" in content
    assert "S01" in content
    print(f"✓ export_csv — arquivo criado: {os.path.basename(path)}")


def test_export_gpkg_file(tmp_path):
    t = _make_sensor_table()
    path = export_gpkg(t, str(tmp_path))
    assert os.path.exists(path), f"Arquivo não criado: {path}"
    print(f"✓ export_gpkg — arquivo criado: {os.path.basename(path)}")


def test_export_all_tables(tmp_path):
    data_dir = str(tmp_path / "dados")
    os.makedirs(data_dir)

    t1 = _make_sensor_table("sensores")
    t1.save(data_dir)
    t2 = _make_table_no_coords("meta")
    t2.save(data_dir)

    results = export_all_tables(data_dir, data_dir)
    assert len(results) == 2, f"Esperado 2 resultados, obtido {len(results)}"
    ok = [r for r in results if r.ok]
    assert len(ok) == 2
    print(f"✓ export_all_tables — {len(results)} tabela(s) exportada(s) sem erro")


def test_table_exporter_refresh(tmp_path):
    data_dir = str(tmp_path / "exporter_refresh")
    os.makedirs(data_dir)

    t = _make_sensor_table("sensores")
    t.save(data_dir)

    exporter = TableExporter("sensores", data_dir, data_dir)
    ok = exporter.refresh()
    assert ok, "TableExporter.refresh() retornou False"
    assert os.path.exists(exporter.gpkg_path), "GPKG não criado"
    assert os.path.exists(exporter.csv_path),     "CSV não criado"
    assert exporter.last_export_str != "nunca"
    print(f"✓ TableExporter.refresh() — ok, última exportação: {exporter.last_export_str}")


def test_table_exporter_missing_table(tmp_path):
    data_dir = str(tmp_path / "exporter_missing")
    os.makedirs(data_dir)
    exporter = TableExporter("nao_existe", data_dir, data_dir)
    ok = exporter.refresh()
    assert not ok, "Deveria retornar False para tabela inexistente"
    print("✓ TableExporter.refresh() — False para tabela inexistente")


# ─────────────────────────────────────────────
#  Runner manual (sem pytest)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import pathlib

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)

        tests = [
            (test_detect_coordinate_columns_by_name,  []),
            (test_detect_coordinate_columns_aliases,   []),
            (test_detect_coordinate_columns_hints,     []),
            (test_detect_no_coords,                    []),
            (test_csv_string_columns,                  []),
            (test_csv_string_row_count,                []),
            (test_csv_none_as_empty_string,            []),
            (test_gpkg_creation_and_wal,               [tmp_path]),
            (test_export_csv_file,                     [tmp_path]),
            (test_export_gpkg_file,                    [tmp_path]),
            (test_export_all_tables,                   [tmp_path]),
            (test_table_exporter_refresh,              [tmp_path]),
            (test_table_exporter_missing_table,        [tmp_path]),
        ]

        passed = failed = 0
        for fn, args in tests:
            try:
                fn(*args)
                passed += 1
            except Exception as exc:
                print(f"✗ {fn.__name__}: {exc}")
                failed += 1

        print(f"\n{'='*50}")
        print(f"Resultado: {passed} passaram, {failed} falharam")
        if failed:
            sys.exit(1)
