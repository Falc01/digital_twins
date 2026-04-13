import time
from dyntable import DynTable, DynType

PASTA       = "dados"
NOME_TABELA = "sensor_readings"

COLUNAS = [
    ("device_id",   DynType.STRING,    False),
    ("lido_em",     DynType.TIMESTAMP, False),
    ("localizacao", DynType.STRING,    True),
    ("status",      DynType.STRING,    True),
]

DADOS_EXEMPLO = [
    {"device_id": "sensor-T01", "lido_em": time.time(), "localizacao": "sala-01", "status": "ok"},
    {"device_id": "sensor-P01", "lido_em": time.time(), "localizacao": "sala-02", "status": "ok"},
]


def main():
    print(f"\n📦 Criando tabela '{NOME_TABELA}' em '{PASTA}/'...\n")
    tabela = DynTable(NOME_TABELA)

    for nome, tipo, nullable in COLUNAS:
        tabela.add_column(nome, tipo, nullable=nullable)
        print(f"  ✓ Coluna '{nome}' ({tipo.name})")

    if DADOS_EXEMPLO:
        print(f"\n  Inserindo {len(DADOS_EXEMPLO)} linha(s) de exemplo...")
        for dados in DADOS_EXEMPLO:
            row = tabela.new_row(**dados)
            print(f"    → Linha {row.id}: {dados['device_id']}")

    tabela.save(PASTA)
    print(f"\n✅ Pronto! Arquivo criado: {PASTA}/{NOME_TABELA}.dyndb\n")
    print(tabela)


if __name__ == "__main__":
    main()
