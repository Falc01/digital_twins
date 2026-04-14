"""
startup_script.py
=================
Injetado no QGIS via: qgis-bin.exe --code startup_script.py

Responsabilidades
-----------------
1. Configura o projeto QGIS (cria ou carrega .qgz)
2. Descobre todas as tabelas .dyndb em PASTA_DADOS
3. Para cada tabela:
   a. Cria um TableExporter  → gera CSV e GeoJSON iniciais
   b. Cria um LayerManager   → carrega a camada no QGIS
   c. Registra no MultiTableWatcher → monitora mudanças futuras
4. Inicia todos os watchers

Adicionar uma nova tabela ao projeto
-------------------------------------
Basta criar o arquivo .dyndb com as colunas corretas (incluindo
colunas de latitude e longitude) e reiniciar o QGIS, ou chamar
_setup_table() manualmente no console Python do QGIS.
"""

import os
import sys

# ── Raiz do projeto ──────────────────────────────────────────────────────────

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Imports do projeto ───────────────────────────────────────────────────────

from config import (
    PASTA_DADOS,
    QGIS_PROJECT_PATH,
    QGIS_BASEMAP_PATH,
    QGIS_LAT_COLUMN,
    QGIS_LON_COLUMN,
    QGIS_CRS,
    QGIS_LAYER_NAME,
    QGIS_DEBOUNCE_MS,
)
from table_manager import TableManager
from qgis_bridge.project_manager import setup_project
from qgis_bridge.exporter import TableExporter, export_all_tables
from qgis_bridge.layer_manager import LayerManager
from qgis_bridge.watcher import MultiTableWatcher

# ── Caminhos absolutos ───────────────────────────────────────────────────────

DATA_DIR = os.path.join(PROJECT_ROOT, PASTA_DADOS)

# ── 1. Configura projeto QGIS ────────────────────────────────────────────────

setup_project(QGIS_PROJECT_PATH, QGIS_BASEMAP_PATH, QGIS_CRS)

# ── 2. Descobre tabelas ──────────────────────────────────────────────────────

manager = TableManager(DATA_DIR)
table_names = manager.list_tables()

if not table_names:
    print(
        "[startup] Nenhuma tabela .dyndb encontrada em:\n"
        f"  {DATA_DIR}\n"
        "  Execute setup_tabela.py para criar a estrutura inicial."
    )

# ── 3. Watcher global ────────────────────────────────────────────────────────

_multi_watcher = MultiTableWatcher()


def _setup_table(table_name: str) -> tuple | None:
    """
    Configura exporter + layer_manager + watcher para uma tabela.
    Retorna (exporter, layer_manager) ou None em caso de erro.
    Pode ser chamado manualmente no console Python do QGIS para
    adicionar uma nova tabela sem reiniciar.
    """
    dyndb_path = os.path.join(DATA_DIR, f"{table_name}.dyndb")

    # Nome da camada: usa QGIS_LAYER_NAME se há só uma tabela, senão usa o nome da tabela
    layer_name = QGIS_LAYER_NAME if len(table_names) == 1 else table_name

    geojson_path = os.path.join(DATA_DIR, f"{table_name}.geojson")
    csv_path     = os.path.join(DATA_DIR, f"{table_name}.csv")

    # Exporter ----------------------------------------------------------------
    exporter = TableExporter(
        table_name         = table_name,
        data_dir           = DATA_DIR,
        output_dir         = DATA_DIR,
        lat_hint           = QGIS_LAT_COLUMN,
        lon_hint           = QGIS_LON_COLUMN,
        export_csv_files   = True,
        export_geojson_files = True,
    )

    print(f"[startup] Exportando '{table_name}'...")
    ok = exporter.refresh()
    if not ok:
        print(f"[startup] Falha ao exportar '{table_name}' — camada não será carregada.")
        return None

    # LayerManager ------------------------------------------------------------
    layer_mgr = LayerManager(
        layer_name   = layer_name,
        project_path = QGIS_PROJECT_PATH,
        geojson_path = geojson_path,
        csv_path     = csv_path,
        lat_col      = QGIS_LAT_COLUMN,
        lon_col      = QGIS_LON_COLUMN,
        crs_str      = QGIS_CRS,
    )
    layer_mgr.reload()

    # Watcher -----------------------------------------------------------------
    _multi_watcher.add(
        dyndb_path            = dyndb_path,
        exporter              = exporter,
        layer_reload_callback = layer_mgr.reload,
        debounce_ms           = QGIS_DEBOUNCE_MS,
    )

    return exporter, layer_mgr


# ── 4. Inicializa todas as tabelas encontradas ───────────────────────────────

_active: dict[str, tuple] = {}

for _name in table_names:
    _result = _setup_table(_name)
    if _result:
        _active[_name] = _result

# ── 5. Inicia watchers ───────────────────────────────────────────────────────

_multi_watcher.start_all()

print(
    f"\n[startup] Inicialização completa.\n"
    f"  Tabelas ativas: {list(_active.keys())}\n"
    f"  Monitoramento: {len(_multi_watcher)} arquivo(s) .dyndb\n"
    f"  Para adicionar uma nova tabela manualmente:\n"
    f"    from startup_script import _setup_table\n"
    f"    _setup_table('nome_da_tabela')\n"
)
