# 🌐 Gêmeo Digital IoT — UNIFACS (Pelourinho, Salvador/BA)

![Status do Servidor](https://img.shields.io/badge/Servidor_OCI-ONLINE_24%2F7-brightgreen?style=for-the-badge&logo=oracle)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-5_Containers-blue?style=for-the-badge&logo=docker)
![QGIS Server](https://img.shields.io/badge/QGIS_Server-Headless_WMS%2FWFS-589632?style=for-the-badge&logo=qgis)

Este repositório contém o ecossistema completo e modularizado do projeto de **Gêmeo Digital para Monitoramento de Sensores IoT** da UNIFACS. O sistema realiza a ingestão assíncrona de telemetria de sensores, gerenciamento dinâmico de tabelas no DataLake, renderização cartográfica via servidor GIS headless e visualização em tempo real em um mapa interativo web.

---

## 🚀 Servidor de Homologação em Tempo Real (Live Demo)

A aplicação está implantada e operando de forma contínua em uma Máquina Virtual na nuvem da Oracle Cloud Infrastructure (OCI):

🌐 **URL de Acesso ao Vivo:** [http://137.131.211.210:8080](http://137.131.211.210:8080)

> [!NOTE]
> O servidor de homologação conta com os 5 microsserviços rodando via Docker Compose com sincronização automática de arquivos e otimização de memória virtual SWAP.

---

## 🗺️ Visão Geral dos Módulos e Arquitetura

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

### 1. Backend API (`/backend`)
* **Tecnologias:** FastAPI (Python 3.10+), `dyntable`, SQLite/GeoPackage.
* **Responsabilidade:** Ingestão de planilhas CSV/Excel, CRUD de sensores, gerenciamento de tabelas ativas no DataLake e exportação imediata para o formato espacial `.gpkg`. Possui suporte a tabelas legadas via mapeamento dinâmico de módulos.

### 2. Frontend Web (`/frontend`)
* **Tecnologias:** Leaflet.js, HTML5, Vanilla CSS3 (com Glassmorphism e Dark Mode), Node.js (Servidor estático).
* **Responsabilidade:** Interface do usuário final. Exibe o mapa do Pelourinho, lista de sensores ativos, mapas de calor dinâmicos e o **Painel de Geolocalização Pendente**, permitindo que o usuário atribua coordenadas a novos sensores diretamente clicando no mapa.

### 3. Integração QGIS & Watcher (`/qgis_integration`)
* **Tecnologias:** QGIS Server Headless, Python Watcher Daemon, PyQGIS.
* **Responsabilidade:** O daemon `watcher_headless.py` monitora a pasta do DataLake em tempo real. Qualquer alteração no banco GeoPackage regera o projeto `.qgz` de engenharia e instrui o QGIS Server a servir as novas camadas WFS/WMS atualizadas de forma transparente.

### 4. Infraestrutura e DataLake (`/infra`)
* **Tecnologias:** Docker Compose, Nginx Reverse Proxy, Linux SWAP.
* **Responsabilidade:** Gerenciamento de volumes compartilhados, orquestração dos contêineres e roteamento interno de portas HTTP.

---

## 📚 Documentação Técnica do Projeto

Para conferir os detalhes técnicos de implementação, correções de engenharia e guias de implantação, consulte os documentos abaixo:

* 📖 **[DEPLOY.md](DEPLOY.md):** Guia passo a passo do deploy na Oracle Cloud, configuração de rede (VCN/Security Lists), liberação de portas e otimização de memória SWAP.
* 🛠️ **[LOG_DESENVOLVIMENTO.md](LOG_DESENVOLVIMENTO.md):** Diário de bordo técnico com todos os problemas de engenharia encontrados durante o desenvolvimento (desserialização Pickle, Nginx port-stripping, fallback WFS) e como foram resolvidos.
* ⚙️ **[Relatório do Backend](backend/relatorio_refatoracao_backend.md):** Especificação detalhada da refatoração do backend e estrutura de rotas.
* 🎨 **[Relatório do Frontend](frontend/relatorio_refatoracao_frontend.md):** Guia da arquitetura modular da interface e componentes visuais.

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
