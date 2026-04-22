import os

_HERE = os.path.dirname(os.path.abspath(__file__))

# ── Dados ────────────────────────────────────────────────────────────────────

PASTA_DADOS:    str        = "dados"
TABELA_PADRAO:  str | None = None       # None = sem padrão (usa primeira encontrada)

MAX_TABELAS:           int | None = None
MAX_LINHAS_POR_TABELA: int | None = None

# ── QGIS ─────────────────────────────────────────────────────────────────────

# Caminho do executável do QGIS.
# None = detecção automática (Windows: Program Files\QGIS*)
# Exemplo Windows: r"C:\Program Files\QGIS 3.36\bin\qgis-bin.exe"
# Exemplo Linux:   "/usr/bin/qgis"
QGIS_EXE_PATH: str | None = None

QGIS_PROJECT_PATH: str = os.path.join(_HERE, "dados", "projeto_iot.qgz")
QGIS_BASEMAP_PATH: str = os.path.join(_HERE, "dados", "pelourinho_recortado.tif")

# Colunas que o exportador vai procurar para lat/lon (hint — não obrigatório).
# O exporter detecta automaticamente variações comuns (lat, latitude, y, etc.)
# mas estas configurações têm prioridade se o nome for diferente do padrão.
QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"

QGIS_CRS:         str = "EPSG:4326"
QGIS_LAYER_NAME:  str = "IoT Sensors"   # usado só quando há uma única tabela
QGIS_DEBOUNCE_MS: int = 400             # ms de espera antes de recarregar

# ── Exportador ───────────────────────────────────────────────────────────────

DATA_DIR: str = os.path.join(_HERE, PASTA_DADOS)

# Gerar GeoJSON além do CSV (recomendado: True — o QGIS lê melhor)
EXPORT_GEOJSON: bool = True

# Gerar CSV (mantido para compatibilidade e ferramentas externas)
EXPORT_CSV: bool = True

# GeoJSON compacto (None) ou indentado para debug (ex: 2)
GEOJSON_INDENT: int | None = None

# Gerar GeoPackage (.gpkg) para o QGIS ler como banco vetorial
EXPORT_GPKG: bool = True