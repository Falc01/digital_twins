"""
tests/test_exporter.py
======================
Testes do exporter sem dependência do QGIS.
Foca na exportação para GeoPackage (.gpkg).
"""

import os
import sys
import tempfile
import sqlite3

# Garante que a raiz do projeto está no path
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from src.dyntable.data._core import DynTable, DynType
from src.qgis.data.exporter import (
    TableExporter,
    detect_coordinate_columns,
    export_all_tables,
)


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
    # Linha sem coordenadas → deve ser ignorada na insercao geoespacial se tratada assim,
    # mas o gpkg processa conforme middleware.
    t.new_row(device_id="S04", temperatura=18.0, ativo=True)
    return t


def test_export_all_tables(tmp_path):
    data_dir = str(tmp_path / "dados")
    os.makedirs(data_dir)

    t1 = _make_sensor_table("sensores")
    t1.save(data_dir)

    results = export_all_tables(data_dir, data_dir)
    assert len(results) == 1, f"Esperado 1 resultado, obtido {len(results)}"
    assert results[0].ok
    print(f"[OK] export_all_tables — tabela exportada sem erro")

    gpkg_path = results[0].gpkg_path
    assert gpkg_path and os.path.exists(gpkg_path)

    con = sqlite3.connect(gpkg_path)
    try:
        cur = con.cursor()
        cur.execute("SELECT count(*) FROM sensores")
        count = cur.fetchone()[0]
        # Esperado 3 linhas, pois 1 não tem coordenada e é descartada.
        assert count == 3
    finally:
        con.close()
    print(f"[OK] export_all_tables — gpkg criado e preenchido")

def test_table_exporter_refresh(tmp_path):
    data_dir = str(tmp_path / "exporter_refresh")
    os.makedirs(data_dir)

    t = _make_sensor_table("sensores")
    t.save(data_dir)

    exporter = TableExporter("sensores", data_dir, data_dir)
    ok = exporter.refresh()
    assert ok, "TableExporter.refresh() retornou False"
    assert os.path.exists(exporter.gpkg_path), "GPKG não criado"
    print(f"[OK] TableExporter.refresh() — ok")


if __name__ == "__main__":
    import pathlib

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)

        tests = [
            (test_export_all_tables,                   [tmp_path]),
            (test_table_exporter_refresh,              [tmp_path]),
        ]

        passed = failed = 0
        for fn, args in tests:
            try:
                fn(*args)
                passed += 1
            except Exception as exc:
                print(f"[FAIL] {fn.__name__}: {exc}")
                failed += 1

        print(f"\n{'='*50}")
        print(f"Resultado: {passed} passaram, {failed} falharam")
        if failed:
            sys.exit(1)
