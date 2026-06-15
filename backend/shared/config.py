"""
Configuração centralizada do Gêmeo Digital IoT.

Responsável por resolver caminhos absolutos a partir da raiz do projeto,
evitando problemas de execução a partir de diferentes diretórios de trabalho.

Consulte:
- docs/architecture/decisoes-tecnicas.md (seção de paths e isolamento)
- docs/architecture/arquitetura-proposta.md (Datalake Central e volumes)
"""

import os
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
# Sobe para a raiz real do workspace (digital_twins/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))

# =============================================================================
# Dados (Datalake)
# =============================================================================
PASTA_DADOS: str = os.path.join("infra", "dados")
DATA_DIR: str = os.getenv("DATA_DIR") or os.path.join(PROJECT_ROOT, PASTA_DADOS)

TABELA_PADRAO: str | None = None
MAX_TABELAS: int | None = None
MAX_LINHAS_POR_TABELA: int | None = None

# =============================================================================
# QGIS
# =============================================================================
# Caminho do executável QGIS (None = detecção automática no Windows: Program Files\QGIS*)
QGIS_EXE_PATH: str | None = None

QGIS_PROJECT_PATH: str = os.path.join(DATA_DIR, "projeto_iot.qgz")
QGIS_BASEMAP_PATH: str = os.path.join(DATA_DIR, "pelourinho_recortado.tif")

# Hints para colunas de geolocalização (o ingestor/exportador usa quando presentes)
QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"

QGIS_CRS: str = "EPSG:4326"          # CRS dos sensores/pontos
QGIS_BASEMAP_CRS: str = "EPSG:31984" # CRS do raster de basemap (Pelourinho)
QGIS_LAYER_NAME: str = "IoT Sensors"

QGIS_DEBOUNCE_MS: int = 400

# =============================================================================
# Exportação
# =============================================================================
# Atualmente focado exclusivamente em GeoPackage (conforme arquitetura proposta)
EXPORT_GPKG: bool = True

# =============================================================================
# Camada de Dados / Ingestor (MÍNIMO DE HARDCODES)
# =============================================================================
# Candidatos de colunas geográficas (case-insensitive após normalização).
# O ingestor detecta automaticamente se o Excel contém alguma dessas.
# Se NENHUMA estiver presente (ex.: dados de estação meteorológica sem geo),
# nenhuma coluna lat/lon é criada nem valores falsos são injetados.
GEO_LAT_CANDIDATES: list[str] = ["latitude", "lat", "y", "coord_y", "latitud"]
GEO_LON_CANDIDATES: list[str] = ["longitude", "lon", "long", "x", "coord_x", "longitud"]

# Se True, o ingestor tenta inferir tipos (FLOAT para números, STRING caso contrário)
# ao criar colunas a partir do cabeçalho do Excel.
INGEST_INFER_TYPES: bool = True

# Nome padrão para tabela quando não especificado no upload
DEFAULT_INGEST_TABLE: str = "leituras"

# =============================================================================
# Utilitários
# =============================================================================
def get_data_path(filename: str) -> str:
    """Retorna caminho absoluto dentro da pasta de dados."""
    return os.path.join(DATA_DIR, filename)

def get_project_root() -> str:
    """Retorna a raiz absoluta do projeto."""
    return PROJECT_ROOT

def get_geo_candidates() -> tuple[list[str], list[str]]:
    """Retorna os candidatos configurados para detecção de geo (lat, lon)."""
    return list(GEO_LAT_CANDIDATES), list(GEO_LON_CANDIDATES)

