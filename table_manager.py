"""
table_manager.py
================
Gerenciador de múltiplas tabelas.

Esta camada fica ENTRE o frontend e o dyntable:

    Frontend (Streamlit / Flask / CLI / qualquer coisa)
         ↓  chama métodos do TableManager
    TableManager   ← você está aqui
         ↓  usa DynTable internamente
    DynTable + disco (CSV + schema.json)

O frontend nunca fala com DynTable diretamente para operações
de gerenciamento (criar, deletar, listar tabelas). Ele só
recebe a tabela ativa e opera sobre ela.

Isso significa que trocar o Streamlit por outro frontend
não exige mudar nada aqui nem no dyntable.

Uso básico:
    from table_manager import TableManager

    mgr = TableManager("dados")

    # Cria uma nova tabela
    t = mgr.create("leituras_temp")

    # Lista todas as tabelas salvas
    print(mgr.list_tables())   # → ["leituras_temp"]

    # Carrega uma tabela existente
    t = mgr.get("leituras_temp")

    # Deleta uma tabela
    mgr.delete("leituras_temp")
"""

from __future__ import annotations

import os
import json
from typing import Optional

from dyntable import DynTable, DynType


class TableNotFoundError(Exception):
    def __init__(self, name: str):
        super().__init__(
            f"Tabela '{name}' não encontrada em disco. "
            f"Use create() para criar uma nova."
        )

class TableAlreadyExistsError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Tabela '{name}' já existe.")


class TableManager:
    """
    Gerencia múltiplas DynTables em uma pasta.

    Cada tabela vive em dois arquivos dentro de `folder`:
        <nome>.csv
        <nome>.schema.json

    O TableManager sabe quais tabelas existem lendo os
    arquivos .schema.json na pasta — não precisa de um
    arquivo de índice separado.
    """

    def __init__(self, folder: str):
        """
        Parâmetros:
            folder → pasta onde as tabelas são salvas.
                     Criada automaticamente se não existir.
        """
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    # ═══════════════════════════════════════════════════════
    #  LISTAGEM
    # ═══════════════════════════════════════════════════════

    def list_tables(self) -> list[str]:
        """
        Retorna os nomes de todas as tabelas salvas na pasta,
        em ordem alfabética.

            mgr.list_tables()  # → ["leituras", "sensores", "alertas"]

        Descobre as tabelas lendo quais arquivos .schema.json
        existem — sem precisar de um índice separado.
        """
        tables = []
        for fname in os.listdir(self.folder):
            if fname.endswith(".schema.json"):
                # "sensor_readings.schema.json" → "sensor_readings"
                tables.append(fname.replace(".schema.json", ""))
        return sorted(tables)

    def exists(self, name: str) -> bool:
        """Retorna True se a tabela existe em disco."""
        schema_path = os.path.join(self.folder, f"{name}.schema.json")
        return os.path.exists(schema_path)

    # ═══════════════════════════════════════════════════════
    #  CRIAÇÃO E CARREGAMENTO
    # ═══════════════════════════════════════════════════════

    def create(self, name: str) -> DynTable:
        """
        Cria uma tabela nova vazia e a salva imediatamente.
        Lança TableAlreadyExistsError se já existir.

            tabela = mgr.create("alertas")
        """
        if self.exists(name):
            raise TableAlreadyExistsError(name)
        table = DynTable(name)
        table.save(self.folder)
        return table

    def get(self, name: str) -> DynTable:
        """
        Carrega uma tabela existente do disco.
        Lança TableNotFoundError se não existir.

            tabela = mgr.get("leituras")
        """
        if not self.exists(name):
            raise TableNotFoundError(name)
        return DynTable.load(self.folder, name)

    def get_or_create(self, name: str) -> tuple[DynTable, bool]:
        """
        Carrega a tabela se existir, ou cria uma nova se não existir.
        Retorna (tabela, foi_criada).

            tabela, nova = mgr.get_or_create("leituras")
            if nova:
                tabela.add_column("device_id", DynType.STRING)
                mgr.save(tabela)

        O booleano `foi_criada` permite que o chamador saiba se
        precisa configurar as colunas iniciais.
        """
        if self.exists(name):
            return DynTable.load(self.folder, name), False
        table = DynTable(name)
        table.save(self.folder)
        return table, True

    # ═══════════════════════════════════════════════════════
    #  SALVAMENTO
    # ═══════════════════════════════════════════════════════

    def save(self, table: DynTable) -> None:
        """
        Salva o estado atual de uma tabela no disco.

        O frontend chama isso após qualquer operação de escrita.
        Ao centralizar o save aqui, nenhum frontend precisa
        saber qual é a pasta — ele só passa a tabela.

            mgr.save(tabela)
        """
        table.save(self.folder)

    # ═══════════════════════════════════════════════════════
    #  DELEÇÃO E RENOMEAÇÃO
    # ═══════════════════════════════════════════════════════

    def delete(self, name: str) -> None:
        """
        Deleta permanentemente uma tabela e seus arquivos do disco.
        Lança TableNotFoundError se não existir.

            mgr.delete("tabela_antiga")
        """
        if not self.exists(name):
            raise TableNotFoundError(name)
        csv_path    = os.path.join(self.folder, f"{name}.csv")
        schema_path = os.path.join(self.folder, f"{name}.schema.json")
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(schema_path):
            os.remove(schema_path)

    def rename(self, old_name: str, new_name: str) -> DynTable:
        """
        Renomeia uma tabela: carrega, muda o nome, salva com novo nome,
        deleta os arquivos antigos.
        Lança TableNotFoundError se old_name não existir.
        Lança TableAlreadyExistsError se new_name já existir.

            tabela = mgr.rename("temp", "leituras_temperatura")
        """
        if not self.exists(old_name):
            raise TableNotFoundError(old_name)
        if self.exists(new_name):
            raise TableAlreadyExistsError(new_name)
        table = DynTable.load(self.folder, old_name)
        table.name = new_name
        table.save(self.folder)
        self.delete(old_name)
        return table

    # ═══════════════════════════════════════════════════════
    #  METADADOS RÁPIDOS (sem carregar a tabela inteira)
    # ═══════════════════════════════════════════════════════

    def info(self, name: str) -> dict:
        """
        Retorna informações sobre uma tabela lendo SÓ o schema.json,
        sem carregar os dados do CSV. Útil para listar tabelas com
        detalhes sem custo de carregar tudo.

            mgr.info("leituras")
            # {
            #   "name": "leituras",
            #   "columns": ["device_id", "temperatura"],
            #   "col_count": 2,
            #   "next_id": 47,     ← indica quantas linhas já foram inseridas
            # }
        """
        if not self.exists(name):
            raise TableNotFoundError(name)
        schema_path = os.path.join(self.folder, f"{name}.schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Conta linhas no CSV sem carregar tudo na memória
        csv_path = os.path.join(self.folder, f"{name}.csv")
        row_count = 0
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                # subtrai 1 pelo cabeçalho
                row_count = sum(1 for _ in f) - 1

        return {
            "name":      schema["name"],
            "columns":   [c["name"] for c in schema["columns"]],
            "col_count": len(schema["columns"]),
            "row_count": max(0, row_count),
            "next_id":   schema["next_id"],
        }

    def info_all(self) -> list[dict]:
        """
        Retorna info() de todas as tabelas, sem carregar nenhum CSV.
        Ideal para renderizar uma lista de tabelas na UI.

            for info in mgr.info_all():
                print(info["name"], info["row_count"], "linhas")
        """
        return [self.info(name) for name in self.list_tables()]

    # ═══════════════════════════════════════════════════════
    #  REPRESENTAÇÃO
    # ═══════════════════════════════════════════════════════

    def __repr__(self) -> str:
        tables = self.list_tables()
        return f"TableManager(folder='{self.folder}', tables={tables})"
