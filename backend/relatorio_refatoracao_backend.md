# Guia de Refatoração e Melhorias do Backend (Gêmeo Digital)

Este guia prático foi criado para orientar o desenvolvedor do backend na reestruturação e refatoração da API FastAPI e biblioteca `dyntable`, alinhando-as com as especificações da banca (uso do modo WAL, GeoPackage e ciclos de 30-60min) e preparando-as para integração com o frontend.

---

## 1. Correção de Caminhos e Centralização de Configurações

### O Problema Atual:
O ambiente foi modularizado, mas o `PROJECT_ROOT` em `backend/shared/config.py` ainda aponta localmente para a pasta `backend/`. Isso faz com que a pasta de dados (`DATA_DIR`) seja criada dentro da pasta de código (`backend/infra/dados`), impedindo o compartilhamento de arquivos com o QGIS Server e Frontend.

### Solução Proposta:
Ajuste a resolução de caminhos para subir mais um nível na hierarquia (saindo de `backend/` e acessando a raiz real do workspace). Assim, ambos os módulos lerão e escreverão na mesma pasta `infra/dados/` na raiz:

```python
# backend/shared/config.py
_HERE = os.path.dirname(os.path.abspath(__file__))
# Sobe para a raiz real do workspace (digital_twins/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE)) 

# Resolve o caminho para a pasta compartilhada do Datalake
PASTA_DADOS = os.path.join("infra", "dados")
DATA_DIR = os.path.join(PROJECT_ROOT, PASTA_DADOS)
```

> [!WARNING]
> **Eliminação de Código Duplicado:**
> Remova os arquivos redundantes `config.py` e `table_manager.py` localizados na raiz da pasta `backend/`. O código deve importar exclusivamente as versões de `backend/shared/config.py` e `backend/src/dyntable/logic/table_manager.py`.

---

## 2. Alinhamento de Rotas (Compatibilidade com o Frontend)

O frontend (`web_interface/app.js`) realiza requisições HTTP para a API buscando recursos sob o prefixo `/api` (ex: `/api/tables`, `/api/launch_qgis`, `/api/types`).

### A. Prefixar Roteadores no FastAPI
No arquivo `backend/src/api/main.py`, adicione o prefixo ao registrar as rotas:

```python
app.include_router(tables.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
```

### B. Implementação Pontual de Endpoints Faltantes
Em `backend/src/api/routers/tables.py`, é necessário implementar as rotas de gerenciamento de estrutura solicitadas pela interface. Por exemplo, a inclusão de novas colunas dinâmicas:

```python
@router.post("/tables/{name}/columns", status_code=201)
def add_column(name: str, payload: dict = Body(...), mgr: TableManagerDep = None):
    # Carrega a tabela dinamicamente do TableManager
    table = mgr.get(name)
    # Adiciona a coluna com o tipo especificado
    table.add_column(payload["name"], DynType[payload["type"]], payload.get("nullable", True))
    # Salva a matriz de volta no disco (.dyndb)
    mgr.save(table)
    return {"column": payload["name"]}
```
*(Repita esta lógica simples para as operações de exclusão de coluna, renomeação de coluna e criação/exclusão de tabelas).*

---

## 3. Implementação do GeoPackage (.gpkg) e Modo WAL

### O Problema:
O exportador atual gera apenas arquivos CSV e GeoJSON. A arquitetura proposta exige o uso de **GeoPackage (.gpkg)** para obter índices espaciais (R-Tree) e suporte a concorrência segura.

### Solução Proposta:
Substitua o arquivo GeoJSON gerado no `TableExporter` por um GeoPackage. Como o `.gpkg` é estruturado sobre o **SQLite**, utilize o driver padrão `sqlite3` do Python para criar as tabelas espaciais e forçar o uso do **Modo WAL** para evitar travamentos de arquivo (*File Locks*):

```python
# qgis_bridge/exporter.py ou módulo de escrita do backend
import sqlite3

def save_to_gpkg(gpkg_path, table_data):
    conn = sqlite3.connect(gpkg_path)
    try:
        # Ativação do modo WAL para concorrência segura entre FastAPI e QGIS Server
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # Criação da tabela de atributos e inserção dos dados espaciais
        # ... lógica de insert (usando a tabela de metadados do GeoPackage)
        conn.commit()
    finally:
        conn.close()
```

---

## 4. Scheduler de Sincronização Periódica

### Funcionamento:
Em vez de atualizar o cache espacial imediatamente após cada inserção (o que gera alto consumo de CPU e concorrência no disco), as atualizações devem ocorrer em lote.

A API FastAPI grava dados na matriz `.dyndb` imediatamente e atualiza o `status.json` para `"pendente"`. Em paralelo, um loop periódico realiza a sincronização a cada 30-60 minutos:

```python
# backend/src/api/main.py
import asyncio

async def start_periodic_sync():
    while True:
        # 1. Lê a matriz de dados .dyndb
        # 2. Executa a exportação em lote para o GeoPackage (.gpkg)
        # 3. Salva a telemetria com timestamp de sucesso no status.json
        print("[scheduler] Sincronização periódica realizada.")
        
        # Dorme por 30 minutos (1800 segundos)
        await asyncio.sleep(1800)
```

---

## 5. Checklist de Tarefas (Backend)

* [ ] **Ajustar Paths:** Alterar `shared/config.py` para apontar para `infra/dados/` na raiz do workspace.
* [ ] **Unificar Configurações:** Deletar os arquivos duplicados da raiz da pasta `backend`.
* [ ] **Adicionar prefixo `/api`:** Incluir o prefixo no registro das rotas do FastAPI.
* [ ] **Implementar CRUD de Colunas:** Criar rotas para criar tabelas e adicionar/remover/renomear colunas no FastAPI.
* [ ] **Substituir GeoJSON por GPKG:** Implementar gravação no GeoPackage utilizando `sqlite3` e ativar `PRAGMA journal_mode=WAL;`.
* [ ] **Criar Loop do Scheduler:** Implementar a rotina periódica assíncrona (a cada 30-60min) para consolidação de dados.
* [ ] **Atualizar Dependências:** Sincronizar o `requirements.txt` com as dependências do FastAPI.
