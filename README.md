# 🌐 Gêmeo Digital IoT — UNIFACS (Pelourinho, Salvador/BA)

![Status do Servidor](https://img.shields.io/badge/Servidor_OCI-ONLINE_24%2F7-brightgreen?style=for-the-badge&logo=oracle)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-5_Containers-blue?style=for-the-badge&logo=docker)
![QGIS Server](https://img.shields.io/badge/QGIS_Server-Headless_WMS%2FWFS-589632?style=for-the-badge&logo=qgis)

Este repositório contém o ecossistema completo e modularizado do projeto de **Gêmeo Digital para Monitoramento de Sensores IoT** da UNIFACS. O sistema realiza a ingestão assíncrona de telemetria de sensores, gerenciamento dinâmico de tabelas no DataLake, renderização cartográfica via servidor GIS headless e visualização em tempo real em um mapa interativo web.

---

## 📑 Especificações Técnicas dos Módulos (Acesso Rápido)

Acesse diretamente as especificações detalhadas de cada um dos 10 sub-módulos da arquitetura sem precisar navegar entre pastas:

### 📦 Camada Backend (`/backend`)
* 📄 **[Motor de Tabelas Dinâmicas (`dyntable_engine`)](docs/modules/modulo_dyntable_engine.md)**: Persistência binária `.dyndb` e aliasing de desserialização legada.
* 📄 **[API REST FastAPI (`fastapi_api`)](docs/modules/modulo_fastapi_api.md)**: Endpoints HTTP de ingestão, CRUD de sensores e gerenciamento de tabelas.
* 📄 **[Exportador GeoPackage (`gpkg_exporter`)](docs/modules/modulo_gpkg_exporter.md)**: Sincronização espacial SQLite -> OGC GeoPackage (`.gpkg`).

### 🎨 Camada Frontend (`/frontend`)
* 📄 **[Core de Cartografia Leaflet (`frontend_mapa_leaflet`)](docs/modules/modulo_frontend_mapa_leaflet.md)**: Inicialização de mapas, basemaps e camadas WFS/WMS/Heatmap.
* 📄 **[Painel de Geolocalização & Gestão (`frontend_georeferenciamento`)](docs/modules/modulo_frontend_georeferenciamento.md)**: Modo crosshair de alocação de coordenadas por clique e tabelas ativas.
* 📄 **[Portal de Ingestão & Upload (`frontend_ingestao_upload`)](docs/modules/modulo_frontend_ingestao_upload.md)**: Form de upload de planilhas CSV/Excel e drag-and-drop (`upload.html`).

### 🗺️ Camada de Geoprocessamento GIS (`/qgis_integration`)
* 📄 **[Watcher GIS Headless (`qgis_watcher_daemon`)](docs/modules/modulo_qgis_watcher_daemon.md)**: Daemon PyQGIS autônomo e regenerador de projetos `.qgz`.
* 📄 **[Servidor GIS Headless (`qgis_server`)](docs/modules/modulo_qgis_server.md)**: Instância QGIS Server fornecendo serviços OGC WMS/WFS em contêiner.

### 🌐 Camada de Infraestrutura (`/infra` e Nuvem)
* 📄 **[Gateway Nginx (`infraestrutura_gateway_nginx`)](docs/modules/modulo_infraestrutura_gateway_nginx.md)**: Reverse proxy na porta 8080 e preservação de host/porta.
* 📄 **[Orquestração & Nuvem OCI (`infraestrutura_orquestracao_oci`)](docs/modules/modulo_infraestrutura_orquestracao_oci.md)**: Docker Compose de 5 serviços e otimização SWAP 4GB Linux.

---

## 🚀 Servidor de Homologação em Tempo Real (Live Demo)

A aplicação está implantada e operando de forma contínua em uma Máquina Virtual na nuvem da Oracle Cloud Infrastructure (OCI):

🌐 **URL de Acesso ao Vivo:** [http://137.131.211.210:8080](http://137.131.211.210:8080)

> [!NOTE]
> O servidor de homologação conta com os 5 microsserviços rodando via Docker Compose com sincronização automática de arquivos e otimização de memória virtual SWAP.

---

## 🗺️ Visão Geral da Arquitetura

O sistema é estruturado em quatro módulos físicos independentes e orquestrados por um gateway Nginx:

```
                      ┌──────────────────────────────────────────┐
                      │    Nginx Gateway (Porta 8080 público)     │
                      └────────────────────┬─────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  Frontend Web    │             │   Backend API    │             │   QGIS Server    │
│  (Leaflet.js)    │ ──────────► │    (FastAPI)     │ ──────────► │  (WMS / WFS)     │
└──────────────────┘             └─────────┬────────┘             └─────────┬────────┘
                                           │                                 │
                                           ▼                                 ▼
                                ┌─────────────────────────────────────────────────────┐
                                │   Datalake Central & Shared Volumes (/infra/dados)  │
                                │   - SQLite / GeoPackage (.gpkg)                      │
                                │   - Metadados Dinâmicos (sensors_metadata.json)      │
                                └─────────────────────────────────────────────────────┘
```

---

## 📚 Central de Documentação Técnica (`/docs`)

Para consultar os manuais conceituais, registros de infraestrutura e relatórios de refatoração, navegue pela pasta [docs](docs):

* 📖 **[Guia de Implantação OCI (DEPLOY.md)](docs/DEPLOY.md):** Passo a passo do deploy na Oracle Cloud, configuração de rede (VCN/Security Lists) e memória SWAP.
* 🛠️ **[Diário de Desenvolvimento (LOG_DESENVOLVIMENTO.md)](docs/LOG_DESENVOLVIMENTO.md):** Registro técnico de todos os problemas de engenharia resolvidos durante o projeto.
* 🏛️ **[Modelagem de Arquitetura C4 (proposed_architecture.md)](docs/proposed_architecture.md):** Visão de contexto, contêineres e padrão Adapter.
* 🌐 **[Visão Geral do Sistema (project_overview.md)](docs/project_overview.md):** Comparativo QGIS Desktop vs Server e topologia em estrela.
* ⚙️ **[Relatório do Backend](backend/relatorio_refatoracao_backend.md):** Especificação da refatoração e estrutura de rotas.
* 🎨 **[Relatório do Frontend](frontend/relatorio_refatoracao_frontend.md):** Guia da arquitetura modular do frontend.

---

## 🛠️ Como Executar Localmente

Caso deseje rodar a stack completa na sua própria máquina de desenvolvimento:

### Pré-requisitos
* **Docker** e **Docker Compose** instalados.

### Passos
1. Clone o repositório:
   ```bash
   git clone https://github.com/Falc01/digital_twins.git
   cd digital_twins
   ```
2. Inicie todos os serviços com o Docker Compose:
   ```bash
   docker compose up -d
   ```
3. Acesse o painel local em: `http://localhost:8080`
