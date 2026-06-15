from __future__ import annotations

import os
import sqlite3
import sys
import unittest

# Adiciona o diretório qgis_integration e qgis_bridge ao path para importar gpkg_sync
_HERE = os.path.dirname(os.path.abspath(__file__))
_QGIS_INTEGRATION = os.path.abspath(os.path.join(_HERE, ".."))
if _QGIS_INTEGRATION not in sys.path:
    sys.path.insert(0, _QGIS_INTEGRATION)

from qgis_bridge.gpkg_sync import sync_table_to_gpkg


# Mock classes do dyntable para teste isolado
class MockDynColumn:
    def __init__(self, name: str, dtype: int, nullable: bool = True):
        self.name = name
        self.dtype = dtype
        self.nullable = nullable


class MockDynRow:
    def __init__(self, row_id: int, created_at_str: str, data: dict):
        self.id = row_id
        self.created_at_str = created_at_str
        self._data = data

    def __getitem__(self, item):
        return self._data.get(item)


class MockDynTable:
    def __init__(self, name: str):
        self.name = name
        self.column_names = []
        self._columns = {}
        self._rows = []

    def add_column(self, name: str, dtype: int, nullable: bool = True):
        self.column_names.append(name)
        self._columns[name] = MockDynColumn(name, dtype, nullable)

    def add_row(self, row_id: int, created_at_str: str, **kwargs):
        self._rows.append(MockDynRow(row_id, created_at_str, kwargs))

    def __iter__(self):
        return iter(self._rows)

    def __len__(self):
        return len(self._rows)


class TestGeoPackageSync(unittest.TestCase):
    def setUp(self):
        # Pasta de testes temporários
        self.test_dir = os.path.join(_QGIS_INTEGRATION, "tests", "temp_data")
        os.makedirs(self.test_dir, exist_ok=True)
        self.table_name = "test_sensors"
        self.gpkg_path = os.path.join(self.test_dir, f"{self.table_name}.gpkg")
        
        # Cria uma tabela mock de exemplo
        self.table = MockDynTable(self.table_name)
        # 0 = INT, 1 = FLOAT, 2 = STRING
        self.table.add_column("device_id", 2)
        self.table.add_column("latitude", 1)
        self.table.add_column("longitude", 1)
        self.table.add_column("temperature", 1)
        self.table.add_column("status", 2)
        
        # Adiciona dados espaciais e alfanuméricos
        self.table.add_row(1, "2026-06-15T12:00:00Z", device_id="SEN001", latitude=-12.9711, longitude=-38.5108, temperature=24.5, status="OK")
        self.table.add_row(2, "2026-06-15T12:10:00Z", device_id="SEN002", latitude=-12.9722, longitude=-38.5119, temperature=25.2, status="WARNING")
        # Registro sem coordenada válida
        self.table.add_row(3, "2026-06-15T12:20:00Z", device_id="SEN003", latitude=None, longitude=None, temperature=None, status="ERROR")

    def tearDown(self):
        # Limpa arquivos gerados no teste
        if os.path.exists(self.gpkg_path):
            try:
                # Fecha conexões que possam estar abertas
                os.remove(self.gpkg_path)
                wal_path = f"{self.gpkg_path}-wal"
                shm_path = f"{self.gpkg_path}-shm"
                if os.path.exists(wal_path): os.remove(wal_path)
                if os.path.exists(shm_path): os.remove(shm_path)
            except Exception:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except Exception:
                pass

    def test_sync_to_gpkg_creation_and_wal(self):
        # Executa sincronização
        path = sync_table_to_gpkg(self.table, self.test_dir, lat_hint="latitude", lon_hint="longitude")
        self.assertEqual(path, self.gpkg_path)
        self.assertTrue(os.path.exists(self.gpkg_path))
        
        # Conecta no SQLite gerado para validar metadados e registros
        conn = sqlite3.connect(self.gpkg_path)
        try:
            # ── 1. Validação do Modo WAL ─────────────────────────────────────
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            self.assertEqual(journal_mode.lower(), "wal")
            
            # ── 2. Validação de Tabelas Obrigatórias do GeoPackage ───────────
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            self.assertIn("gpkg_spatial_ref_sys", tables)
            self.assertIn("gpkg_contents", tables)
            self.assertIn("gpkg_geometry_columns", tables)
            self.assertIn(self.table_name, tables)
            
            # ── 3. Validação dos Registros Alfanuméricos ─────────────────────
            cursor.execute(f'SELECT id, created_at, device_id, temperature, status FROM "{self.table_name}" ORDER BY id')
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], (1, "2026-06-15T12:00:00Z", "SEN001", 24.5, "OK"))
            self.assertEqual(rows[1], (2, "2026-06-15T12:10:00Z", "SEN002", 25.2, "WARNING"))
            self.assertEqual(rows[2], (3, "2026-06-15T12:20:00Z", "SEN003", None, "ERROR"))
            
            # ── 4. Validação das Geometrias (WKB Point) ──────────────────────
            cursor.execute(f'SELECT geom FROM "{self.table_name}" WHERE id = 1')
            geom_bytes = cursor.fetchone()[0]
            self.assertIsNotNone(geom_bytes)
            
            # Valida assinatura GeoPackage (cabeçalho de 8 bytes, starts with 'GP')
            self.assertTrue(geom_bytes.startswith(b"GP\x00\x01"))
            
            # ── 5. Validação dos Metadados de Bounding Box ───────────────────
            cursor.execute("SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name = ?", (self.table_name,))
            bbox = cursor.fetchone()
            # Mínimos e máximos das coordenadas de SEN001 e SEN002 (-38.5119 a -38.5108 e -12.9722 a -12.9711)
            self.assertAlmostEqual(bbox[0], -38.5119)
            self.assertAlmostEqual(bbox[1], -12.9722)
            self.assertAlmostEqual(bbox[2], -38.5108)
            self.assertAlmostEqual(bbox[3], -12.9711)
            
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
