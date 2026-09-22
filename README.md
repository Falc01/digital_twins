# 🌐 Gêmeo Digital IoT — UNIFACS (Pelourinho, Salvador/BA)

![Status do Servidor](https://img.shields.io/badge/Servidor_OCI-ONLINE_24%2F7-brightgreen?style=for-the-badge&logo=oracle)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-5_Containers-blue?style=for-the-badge&logo=docker)
![QGIS Server](https://img.shields.io/badge/QGIS_Server-Headless_WMS%2FWFS-589632?style=for-the-badge&logo=qgis)
![Documentação](https://img.shields.io/badge/Documentação-Diátaxis_Framework-purple?style=for-the-badge)

Este repositório contém o ecossistema completo e modularizado do projeto de **Gêmeo Digital para Monitoramento de Sensores IoT** da UNIFACS. O sistema realiza a ingestão assíncrona de telemetria de sensores, gerenciamento dinâmico de tabelas no Datalake local, renderização cartográfica via servidor GIS *headless* e visualização em tempo real em um mapa interativo web.

---

## 🌐 Servidor de Homologação em Tempo Real (Live Demo)

A aplicação está implantada e operando de forma contínua em uma Máquina Virtual na nuvem da Oracle Cloud Infrastructure (OCI):

👉 **URL de Acesso ao Vivo:** **[http://137.131.211.210:8080](http://137.131.211.210:8080)**

---

## 🏛️ Visão Geral da Arquitetura (Topologia Hub-and-Spoke)

O sistema é estruturado em cinco contêineres Docker independentes orquestrados por um gateway Nginx proxy reverso:

```
                       ┌──────────────────────────────────────────┐
                       │    Nginx Gateway (Porta 8080 público)    │
                       └────────────────────┬─────────────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         ▼                                  ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐              ┌──────────────────┐
│  Frontend Web    │              │   Backend API    │              │   QGIS Server    │
│  (Leaflet.js)    │ ───────────► │    (FastAPI)     │ ───────────► │  (WMS / WFS)     │
└──────────────────┘              └─────────┬────────┘              └─────────┬────────┘
                                            │                                  │
                                            ▼                                  ▼
                                 ┌──────────────────────────────────────────────────────┐
                                 │   Datalake Central & Shared Volumes (/infra/dados)   │
                                 │   - SQLite Matriz (.dyndb)                           │
                                 │   - GeoPackage Espacial (.gpkg)                      │
                                 │   - Metadados Dinâmicos (sensors_metadata.json)       │
                                 └──────────────────────────────────────────────────────┘
```

---

## 📚 Central de Documentação Técnica (`/docs` - Diátaxis Framework)

A documentação deste repositório foi estruturada seguindo o consagrado **Framework Diátaxis** e o modelo **Docs-as-Code**:

```
docs/
├── 🚀 tutorials/        -> Guias de Aprendizado Orientados a Lições
├── 🛠️ how-to/          -> Passo a Passo para Resolução de Tarefas
├── 📖 reference/       -> Informações Técnicas, Dicionário de Dados e Módulos
├── 💡 explanation/     -> Conceitos de Engenharia, C4 Model e Boas Práticas
└── 🏛️ adrs/            -> Registros Formais de Decisões Arquiteturais
```

### 1. 🚀 Tutorials (Aprendizado Prático)
* 🚀 **[Primeiros Passos com o Gêmeo Digital](docs/tutorials/01_primeiros_passos.md)**: Tutorial do zero ao mapa rodando localmente em 5 minutos.

### 2. 🛠️ How-To Guides (Tarefas & Manutenção)
* 🛠️ **[Guia de Deploy na Oracle Cloud (OCI)](docs/how-to/deploy_oci.md)**: Instalação, firewall VCN e otimização SWAP de 4GB.
* 📥 **[Como Ingerir Dados e Novos Sensores](docs/how-to/adicionar_sensores.md)**: Guia de upload de planilhas CSV/Excel e auto-discovery.
* 🎨 **[Configuração e Estilização no QGIS](docs/how-to/configuracao_qgis.md)**: Edição de projetos `.qgz` e validação WMS/WFS.

### 3. 📖 Reference (Informação Técnica Especificada)
* 🗄️ **[Dicionário de Dados & Esquemas](docs/reference/dicionario_dados.md)**: Especificação das tabelas `.dyndb`, GeoPackage `.gpkg` e JSONs.
* ⚙️ **[Variáveis de Ambiente & Portas](docs/reference/variaveis_ambiente.md)**: Tabela de portas, contêineres e variáveis Docker.
* 📦 **[Especificação dos 10 Sub-módulos](docs/reference/modules/)**:
  - [Motor de Tabelas Dinâmicas (`dyndb`)](docs/reference/modules/modulo_dyntable_engine.md)
  - [API REST FastAPI (`fastapi_api`)](docs/reference/modules/modulo_fastapi_api.md)
  - [Exportador GeoPackage (`gpkg_exporter`)](docs/reference/modules/modulo_gpkg_exporter.md)
  - [Core Cartográfico Leaflet (`frontend_mapa_leaflet`)](docs/reference/modules/modulo_frontend_mapa_leaflet.md)
  - [Painel de Geolocalização (`frontend_georeferenciamento`)](docs/reference/modules/modulo_frontend_georeferenciamento.md)
  - [Portal de Ingestão (`frontend_ingestao_upload`)](docs/reference/modules/modulo_frontend_ingestao_upload.md)
  - [Watcher GIS Headless (`qgis_watcher_daemon`)](docs/reference/modules/modulo_qgis_watcher_daemon.md)
  - [Servidor QGIS Server (`qgis_server`)](docs/reference/modules/modulo_qgis_server.md)
  - [Gateway Nginx (`infraestrutura_gateway_nginx`)](docs/reference/modules/modulo_infraestrutura_gateway_nginx.md)
  - [Orquestração OCI (`infraestrutura_orquestracao_oci`)](docs/reference/modules/modulo_infraestrutura_orquestracao_oci.md)

### 4. 💡 Explanation (Conceitos & Razões de Arquitetura)
* 🏛️ **[Arquitetura C4 Nível 1 e 2](docs/explanation/arquitetura_c4.md)**: Modelagem formal de contexto e contêineres.
* 💡 **[QGIS Desktop vs. QGIS Server](docs/explanation/visao_geral_sistema.md)**: Análise comparativa e razões do modelo headless.
* 🔒 **[Concorrência e Modo WAL](docs/explanation/concorrencia_e_locks.md)**: Resolução de locks SQLite/GeoPackage.
* 📜 **[Guia de Comentários no Código & Docs](docs/explanation/codigo_e_comentarios.md)**: Boas práticas Clean Code e Docstrings.

### 5. 🏛️ ADRs (Architecture Decision Records)
* 📄 **[ADR-001: QGIS Server Headless em Contêiner](docs/adrs/ADR-001_qgis_server_headless.md)**
* 📄 **[ADR-002: Topologia Hub-and-Spoke com Datalake](docs/adrs/ADR-002_topologia_hub_and_spoke_datalake.md)**
* 📄 **[ADR-003: Sincronização Híbrida SQLite/GeoPackage](docs/adrs/ADR-003_sincronizacao_geopackage_sqlite.md)**

---

## 🛠️ Como Executar Localmente

### Pré-requisitos
* **Git**
* **Docker** e **Docker Compose**

### Passos Rápidos
1. Clone o repositório:
   ```bash
   git clone https://github.com/Falc01/digital_twins.git
   cd digital_twins
   ```
2. Inicie a stack de contêineres:
   ```bash
   docker compose up -d
   ```
3. Acesse a aplicação no navegador:
   👉 **`http://localhost:8080`**
