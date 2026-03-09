"""
setup_tabela.py
===============
Rode este script UMA VEZ para criar e salvar a estrutura
inicial da tabela no disco.

Depois disso, o Streamlit e qualquer script Python vão
carregar essa estrutura automaticamente com load_or_create().

Uso:
    python3 setup_tabela.py
"""

import time
from dyntable import DynTable, DynType

# ─────────────────────────────────────────────────────────
#  CONFIGURAÇÃO — ajuste conforme seu projeto IoT
# ─────────────────────────────────────────────────────────
PASTA       = "dados"           # onde os arquivos vão ser salvos
NOME_TABELA = "sensor_readings" # nome da tabela (vira o prefixo dos arquivos)

# ─────────────────────────────────────────────────────────
#  COLUNAS INICIAIS
#  Adicione aqui só o que você JÁ SABE que vai ter.
#  Novas colunas podem ser adicionadas depois, a qualquer
#  momento, pelo Streamlit ou por qualquer script Python.
# ─────────────────────────────────────────────────────────
COLUNAS = [
    # (nome,          tipo,             nullable)
    ("device_id",    DynType.STRING,    False),   # identificador do sensor — obrigatório
    ("lido_em",      DynType.TIMESTAMP, False),   # quando a leitura foi feita — obrigatório
    ("localizacao",  DynType.STRING,    True),    # onde o sensor está instalado
    ("status",       DynType.STRING,    True),    # "ok", "alerta", "erro", etc.
]

# ─────────────────────────────────────────────────────────
#  LINHAS DE EXEMPLO (opcional)
#  Deixe a lista vazia se quiser começar sem dados:
#  DADOS_EXEMPLO = []
# ─────────────────────────────────────────────────────────
DADOS_EXEMPLO = [
    {"device_id": "sensor-T01", "lido_em": time.time(), "localizacao": "sala-01", "status": "ok"},
    {"device_id": "sensor-P01", "lido_em": time.time(), "localizacao": "sala-02", "status": "ok"},
]


# ─────────────────────────────────────────────────────────
#  EXECUÇÃO
# ─────────────────────────────────────────────────────────
def main():
    print(f"\n📦 Criando tabela '{NOME_TABELA}' em '{PASTA}/'...\n")

    tabela = DynTable(NOME_TABELA)

    # Adiciona as colunas
    for nome, tipo, nullable in COLUNAS:
        tabela.add_column(nome, tipo, nullable=nullable)
        print(f"  ✓ Coluna '{nome}' ({tipo.name}, nullable={nullable})")

    # Insere linhas de exemplo, se houver
    if DADOS_EXEMPLO:
        print(f"\n  Inserindo {len(DADOS_EXEMPLO)} linha(s) de exemplo...")
        for dados in DADOS_EXEMPLO:
            row = tabela.new_row(**dados)
            print(f"    → Linha {row.id}: {dados['device_id']}")

    # Salva no disco
    tabela.save(PASTA)

    print(f"""
✅ Pronto! Arquivos criados:

   {PASTA}/{NOME_TABELA}.csv
   {PASTA}/{NOME_TABELA}.schema.json

Para abrir no Streamlit:
   streamlit run app.py

Para usar em scripts Python:
   from dyntable import DynTable
   tabela = DynTable.load_or_create("{PASTA}", "{NOME_TABELA}")
""")

    # Mostra a tabela criada
    print(tabela)


if __name__ == "__main__":
    main()
