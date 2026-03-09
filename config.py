"""
config.py
=========
Configuração central do projeto.

Este é o ÚNICO arquivo que você precisa editar para:
  - mudar onde os dados são salvos
  - trocar o nome da pasta de dados
  - configurar o caminho do QGIS
  - adicionar configurações globais futuras

Qualquer frontend (Streamlit, Flask, CLI, etc.) importa daqui.
Nenhum frontend deve ter configurações hardcoded.

Uso em qualquer arquivo do projeto:
    from config import PASTA_DADOS, TABELA_PADRAO
"""

import os

# ─────────────────────────────────────────────────────────────
#  CAMINHOS
# ─────────────────────────────────────────────────────────────

# Pasta onde todas as tabelas são salvas.
PASTA_DADOS: str = "dados"

# Nome da tabela que abre por padrão no Streamlit.
# Se None, o Streamlit abre sem tabela selecionada.
TABELA_PADRAO: str | None = None

# ─────────────────────────────────────────────────────────────
#  LIMITES
# ─────────────────────────────────────────────────────────────

# Número máximo de tabelas permitidas (None = sem limite)
MAX_TABELAS: int | None = None

# Número máximo de linhas por tabela (None = sem limite)
MAX_LINHAS_POR_TABELA: int | None = None

# ─────────────────────────────────────────────────────────────
#  QGIS BRIDGE
# ─────────────────────────────────────────────────────────────

# Caminho para o executável do QGIS.
# O launcher tenta detectar automaticamente — edite aqui
# apenas se a detecção automática falhar.
# Exemplo: r"C:\Program Files\QGIS 3.34\bin\qgis-bin.exe"
QGIS_EXE_PATH: str | None = None

# Arquivo de projeto QGIS (.qgz).
# Criado automaticamente na primeira vez, reutilizado depois.
QGIS_PROJECT_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados", "projeto_iot.qgz"
)

# Imagem local usada como basemap no QGIS.
# Coloque o arquivo dentro da pasta dados/ e atualize o nome se necessário.
QGIS_BASEMAP_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados", "pelourinho_recortado.tif"
)

# Nomes das colunas de coordenadas no CSV.
QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"

# Sistema de referência de coordenadas (padrão WGS84 lat/lon).
QGIS_CRS: str = "EPSG:4326"

# Nome da camada de pontos IoT dentro do QGIS.
QGIS_LAYER_NAME: str = "IoT Sensors"

# Janela de debounce em milissegundos.
# Evita recargas múltiplas quando o sistema de arquivos
# emite vários sinais para uma única escrita.
QGIS_DEBOUNCE_MS: int = 300
