"""
config.py
=========
Configuração central do projeto.

Este é o ÚNICO arquivo que você precisa editar para:
  - mudar onde os dados são salvos
  - trocar o nome da pasta de dados
  - adicionar configurações globais futuras

Qualquer frontend (Streamlit, Flask, CLI, etc.) importa daqui.
Nenhum frontend deve ter configurações hardcoded.

Uso em qualquer arquivo do projeto:
    from config import PASTA_DADOS, TABELA_PADRAO
"""

# ─────────────────────────────────────────────────────────────
#  CAMINHOS
# ─────────────────────────────────────────────────────────────

# Pasta onde todas as tabelas são salvas.
# Mude aqui para mover os dados para outro lugar — nada mais
# precisa ser alterado no projeto.
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
