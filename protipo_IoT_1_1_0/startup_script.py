"""
startup_script.py
=================
Ponto de entrada injetado no QGIS via:
    qgis-bin.exe --code startup_script.py

Este script é executado automaticamente depois que o QGIS
termina de carregar. Ele:

  1. Adiciona a raiz do projeto ao sys.path (para encontrar qgis_bridge)
  2. Lê as configurações do config.py
  3. Configura o projeto .qgz (cria ou carrega)
  4. Carrega a camada de pontos IoT
  5. Inicia o watcher que mantém tudo sincronizado

Não edite a lógica aqui — edite config.py para mudar caminhos,
ou os módulos em qgis_bridge/ para mudar comportamentos.
"""

import os
import sys

# ── 1. Adiciona a raiz do projeto ao path ────────────────────
# __file__ pode não estar definido quando executado via --code,
# então usa getcwd() como fallback.
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print(f"[qgis_bridge] Raiz do projeto: {PROJECT_ROOT}")

# ── 2. Importa configurações ─────────────────────────────────
try:
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
except ImportError as e:
    print(f"[qgis_bridge] ERRO: Não foi possível importar config.py: {e}")
    print(f"[qgis_bridge] Verifique se PROJECT_ROOT está correto: {PROJECT_ROOT}")
    raise

# ── 3. Monta o caminho do CSV ────────────────────────────────
# O CSV que o QGIS monitora é o primeiro CSV encontrado na pasta
# de dados, ou pode ser configurado diretamente.
# Por enquanto pega o primeiro .csv da pasta (excluindo schema).
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
    print(f"[qgis_bridge] Nenhum CSV encontrado em '{PASTA_DADOS}'.")
    print("[qgis_bridge] Crie uma tabela no Streamlit antes de abrir o QGIS.")
    # Não levanta exceção — o watcher continuará tentando quando o arquivo aparecer

# ── 4. Importa módulos do bridge ─────────────────────────────
from qgis_bridge.project_manager import setup_project
from qgis_bridge.layer_manager   import LayerManager
from qgis_bridge.watcher         import CSVWatcher

# ── 5. Configura o projeto ───────────────────────────────────
setup_project(
    project_path=QGIS_PROJECT_PATH,
    basemap_path=QGIS_BASEMAP_PATH,
    crs_str=QGIS_CRS,
)

# ── 6. Configura o LayerManager ──────────────────────────────
layer_manager = LayerManager(
    csv_path     = CSV_PATH or os.path.join(PROJECT_ROOT, PASTA_DADOS, "dados\sensor_readings.csv"),
    lat_col      = QGIS_LAT_COLUMN,
    lon_col      = QGIS_LON_COLUMN,
    crs_str      = QGIS_CRS,
    layer_name   = QGIS_LAYER_NAME,
    project_path = QGIS_PROJECT_PATH,
)

# Carga inicial se o CSV existir
if CSV_PATH:
    layer_manager.reload()

# ── 7. Inicia o watcher ──────────────────────────────────────
# Guarda referência em variável de nível de módulo para que o
# garbage collector do Python não destrua o objeto (e com ele
# o QFileSystemWatcher e o QTimer).
_watcher = CSVWatcher(
    csv_path    = CSV_PATH or os.path.join(PROJECT_ROOT, PASTA_DADOS, "dados\sensor_readings.csv"),
    callback    = layer_manager.reload,
    debounce_ms = QGIS_DEBOUNCE_MS,
)
_watcher.start()

print("[qgis_bridge] Inicialização completa. Sincronização ativa.")
print(f"[qgis_bridge] Monitorando: {CSV_PATH}")
