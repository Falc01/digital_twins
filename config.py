import os

PASTA_DADOS:    str       = "dados"
TABELA_PADRAO:  str | None = None

MAX_TABELAS:           int | None = None
MAX_LINHAS_POR_TABELA: int | None = None

QGIS_EXE_PATH: str | None = None

QGIS_PROJECT_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados", "projeto_iot.qgz"
)
QGIS_BASEMAP_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados", "basemap.tif"
)

QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"
QGIS_CRS:        str = "EPSG:4326"
QGIS_LAYER_NAME: str = "IoT Sensors"
QGIS_DEBOUNCE_MS: int = 300
