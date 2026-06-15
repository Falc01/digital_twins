import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_HERE)

# ── Dados ────────────────────────────────────────────────────────────────────

PASTA_DADOS:    str        = os.path.join("infra", "dados")
TABELA_PADRAO:  str | None = None       # None = sem padrão (usa primeira encontrada)

MAX_TABELAS:           int | None = None
MAX_LINHAS_POR_TABELA: int | None = None

# ── QGIS ─────────────────────────────────────────────────────────────────────

# Caminho do executável do QGIS.
# None = detecção automática (Windows: Program Files\QGIS*)
QGIS_EXE_PATH: str | None = None

QGIS_PROJECT_PATH: str = os.path.join(PROJECT_ROOT, "infra", "dados", "projeto_iot.qgz")
QGIS_BASEMAP_PATH: str = os.path.join(PROJECT_ROOT, "infra", "dados", "pelourinho_recortado.tif")

# Colunas que o exportador vai procurar para lat/lon (hint — não obrigatório).
QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"

QGIS_CRS:         str = "EPSG:4326"
QGIS_LAYER_NAME:  str = "IoT Sensors"   # usado só quando há uma única tabela
QGIS_DEBOUNCE_MS: int = 400             # ms de espera antes de recarregar

# ── Exportador ───────────────────────────────────────────────────────────────

DATA_DIR: str = os.path.join(PROJECT_ROOT, PASTA_DADOS)

# Gerar GeoPackage (.gpkg) para o QGIS ler como banco vetorial
EXPORT_GPKG: bool = True