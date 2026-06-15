from __future__ import annotations

import os
import sys

PROJECT_ROOT = (
    os.environ.get("DYNTABLE_PROJECT_ROOT")
    or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if "__file__" in dir()
    else os.getcwd()
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.config import (
    DATA_DIR,
    QGIS_PROJECT_PATH,
    QGIS_BASEMAP_PATH,
    QGIS_LAT_COLUMN,
    QGIS_LON_COLUMN,
    QGIS_CRS,
    QGIS_LAYER_NAME,
    QGIS_DEBOUNCE_MS,
    EXPORT_GPKG,
)
from src.dyntable.logic.table_manager import TableManager
from src.qgis.logic.project_manager import setup_project
from src.qgis.data.exporter import TableExporter
from src.qgis.data.layer_manager import LayerManager
from src.qgis.logic.watcher import MultiTableWatcher
from src.qgis.logic.pipeline import build_default_pipeline

setup_project(QGIS_PROJECT_PATH, QGIS_BASEMAP_PATH, QGIS_CRS)

manager = TableManager(DATA_DIR)
table_names = manager.list_tables()

if not table_names:
    print(
        f"[startup] Nenhuma tabela .dyndb encontrada em {DATA_DIR}\n"
        "  Execute setup_tabela.py para criar a estrutura inicial."
    )

_multi_watcher = MultiTableWatcher()


def _setup_table(table_name: str):
    dyndb_path = os.path.join(DATA_DIR, f"{table_name}.dyndb")
    layer_name = QGIS_LAYER_NAME if len(table_names) == 1 else table_name

    pipeline = build_default_pipeline(
        data_dir=DATA_DIR,
        lat_hint=QGIS_LAT_COLUMN,
        lon_hint=QGIS_LON_COLUMN,
        export_gpkg=EXPORT_GPKG,
    )

    exporter = TableExporter(
        table_name=table_name,
        data_dir=DATA_DIR,
        output_dir=DATA_DIR,
        pipeline=pipeline,
    )

    print(f"[startup] Exportando '{table_name}'...")
    if not exporter.refresh():
        print(f"[startup] Falha ao exportar '{table_name}' — camada não carregada.")
        return None

    layer_mgr = LayerManager(
        layer_name=layer_name,
        project_path=QGIS_PROJECT_PATH,
        data_dir=DATA_DIR,
        table_name=table_name,
        lat_col=QGIS_LAT_COLUMN,
        lon_col=QGIS_LON_COLUMN,
        crs_str=QGIS_CRS,
    )

    layer_mgr.load_if_missing()   # ← agora é chamado de verdade

    _multi_watcher.add(
        dyndb_path=dyndb_path,
        exporter=exporter,
        layer_reload_callback=layer_mgr.reload,
        debounce_ms=QGIS_DEBOUNCE_MS,
    )

    return exporter, layer_mgr


_active: dict[str, tuple] = {}
for _name in table_names:
    _result = _setup_table(_name)
    if _result:
        _active[_name] = _result

_multi_watcher.start_all()

print(
    f"\n[startup] Inicialização completa.\n"
    f"  Tabelas ativas: {list(_active.keys())}\n"
    f"  Monitoramento: {len(_multi_watcher)} arquivo(s)\n"
)
