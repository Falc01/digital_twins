import os, sys

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    PASTA_DADOS, QGIS_PROJECT_PATH, QGIS_BASEMAP_PATH,
    QGIS_LAT_COLUMN, QGIS_LON_COLUMN, QGIS_CRS,
    QGIS_LAYER_NAME, QGIS_DEBOUNCE_MS,
)

def _find_csv(pasta: str) -> str | None:
    pasta_abs = os.path.join(PROJECT_ROOT, pasta)
    if not os.path.exists(pasta_abs):
        return None
    for fname in sorted(os.listdir(pasta_abs)):
        if fname.endswith(".csv"):
            return os.path.join(pasta_abs, fname)
    return None

CSV_PATH = _find_csv(PASTA_DADOS)
if not CSV_PATH:
    print("[qgis_bridge] Nenhum CSV na pasta de dados. Exporte um pelo Streamlit primeiro.")

from qgis_bridge.project_manager import setup_project
from qgis_bridge.layer_manager   import LayerManager
from qgis_bridge.watcher         import CSVWatcher

setup_project(QGIS_PROJECT_PATH, QGIS_BASEMAP_PATH, QGIS_CRS)

_fallback = os.path.join(PROJECT_ROOT, PASTA_DADOS, "sensor_readings.csv")
layer_manager = LayerManager(
    csv_path     = CSV_PATH or _fallback,
    lat_col      = QGIS_LAT_COLUMN,
    lon_col      = QGIS_LON_COLUMN,
    crs_str      = QGIS_CRS,
    layer_name   = QGIS_LAYER_NAME,
    project_path = QGIS_PROJECT_PATH,
)
if CSV_PATH:
    layer_manager.reload()

_watcher = CSVWatcher(
    csv_path    = CSV_PATH or _fallback,
    callback    = layer_manager.reload,
    debounce_ms = QGIS_DEBOUNCE_MS,
)
_watcher.start()
print("[qgis_bridge] Inicialização completa. Sincronização ativa.")
