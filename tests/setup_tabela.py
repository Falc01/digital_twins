import time
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from src.dyntable.data._core import DynTable, DynType

PASTA       = os.path.join(os.path.dirname(_HERE), "infra", "dados")
NOME_TABELA = "sensor_readings"

COLUNAS = [
    ("device_id",   DynType.STRING,    False),
    ("lido_em",     DynType.TIMESTAMP, False),
    ("lat",         DynType.FLOAT,     False),
    ("lon",         DynType.FLOAT,     False),
    ("localizacao", DynType.STRING,    True),
    ("status",      DynType.STRING,    True),
]

DADOS_EXEMPLO = [
    {"device_id": "sensor-T01", "lido_em": time.time(), "lat": -12.9734, "lon": -38.5100, "localizacao": "sala-01", "status": "ok"},
    {"device_id": "sensor-P01", "lido_em": time.time(), "lat": -12.9732, "lon": -38.5100, "localizacao": "sala-02", "status": "ok"},
]

def main():
    print(f"\n[INIT] Criando tabela '{NOME_TABELA}' em '{PASTA}/'...\n")
    tabela = DynTable(NOME_TABELA)

    for nome, tipo, nullable in COLUNAS:
        tabela.add_column(nome, tipo, nullable=nullable)
        print(f"  [OK] Coluna '{nome}' ({tipo.name})")

    if DADOS_EXEMPLO:
        print(f"\n  Inserindo {len(DADOS_EXEMPLO)} linha(s) de exemplo...")
        for dados in DADOS_EXEMPLO:
            row = tabela.new_row(**dados)
            print(f"    -> Linha {row.id}: {dados['device_id']}")

    tabela.save(PASTA)
    print(f"\n[SUCESSO] Arquivo criado: {PASTA}/{NOME_TABELA}.dyndb\n")
    print(tabela)

if __name__ == "__main__":
    main()
