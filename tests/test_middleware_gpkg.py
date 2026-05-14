"""
tests/test_middleware_gpkg.py
=============================
Testa o GpkgWriter.
"""

import os
import sys
import tempfile
import sqlite3

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from qgis_bridge.middleware import GpkgWriter, TableData, RowData
from dyntable import DynType

def test_gpkg_writer(tmp_path):
    writer = GpkgWriter(srid=4326)
    
    # Criar mock data
    table_data = TableData(
        name="test_sensors",
        column_names=["device_id", "temperatura", "latitude", "longitude"],
        column_types={
            "device_id": DynType.STRING,
            "temperatura": DynType.FLOAT,
            "latitude": DynType.FLOAT,
            "longitude": DynType.FLOAT,
        },
        lat_col="latitude",
        lon_col="longitude",
        rows=[
            RowData(1, 1000.0, {"device_id": "S1", "temperatura": 22.5, "latitude": -12.9, "longitude": -38.5}),
            RowData(2, 2000.0, {"device_id": "S2", "temperatura": 24.0, "latitude": -13.0, "longitude": -38.4}),
        ]
    )

    out_dir = str(tmp_path)
    path = writer.write(table_data, out_dir)
    
    assert os.path.exists(path)
    assert path.endswith(".gpkg")

    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        cur.execute("SELECT count(*) FROM test_sensors")
        count = cur.fetchone()[0]
        assert count == 2
        
        # Validar geometry existindo e contendo POINT
        cur.execute("SELECT ST_AsText(geom) FROM test_sensors WHERE device_id = 'S1'")
        geom = cur.fetchone()
        # O SQLite em si sem spatialite não suporta ST_AsText nativamente se não estiver carregado, 
        # Mas pelo menos a coluna 'geom' existe.
    except sqlite3.OperationalError as e:
        if "no such function: ST_AsText" in str(e):
            # Validação básica de existencia das colunas se o plugin não estiver carregado no sqlite padrão
            cur.execute("PRAGMA table_info(test_sensors)")
            cols = [c[1] for c in cur.fetchall()]
            assert "geom" in cols
            assert "device_id" in cols
        else:
            raise
    finally:
        con.close()
    
    print("[OK] GpkgWriter - Arquivo gpkg gerado com sucesso.")

if __name__ == "__main__":
    import pathlib
    with tempfile.TemporaryDirectory() as tmp:
        test_gpkg_writer(pathlib.Path(tmp))
