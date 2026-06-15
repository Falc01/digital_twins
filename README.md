# Gêmeo Digital IoT — UNIFACS

Este repositório contém o ecossistema modularizado do projeto de **Gêmeo Digital para Monitoramento IoT** da UNIFACS (Salvador/BA). O sistema integra a ingestão assíncrona de telemetria de sensores, persistência em datalake centralizado, renderização cartográfica via servidor GIS e visualização web em tempo real.

---

## 🗺️ Visão Geral dos Módulos

O projeto é dividido em quatro módulos físicos e independentes para facilitar o desenvolvimento paralelo, conteinerização e escalabilidade do sistema:

### 1. Backend (`/backend`)
* **O que faz:** Camada lógica e de ingestão de dados. É responsável por receber payloads HTTP dos sensores, processá-los na biblioteca de tabelas dinâmicas `dyntable`, gerenciar a matriz local `.dyndb` e persistir em lote (Micro-batching) os dados no banco espacial `.gpkg` usando o SQLite em modo WAL (Write-Ahead Logging) para mitigar travamentos de escrita.
* **Onde é expresso:** Interface de API REST HTTP construída com **FastAPI** (Python).

### 2. Frontend (`/frontend`)
* **O que faz:** Painel web interativo baseado em mapas. Consome as geometrias e imagens diretamente do QGIS Server (WMS/WFS) e as variáveis de status/dados de sensores da API do FastAPI. Realiza a autodescoberta dinâmica de atributos via DescribeFeatureType do WFS.
* **Onde é expresso:** Interface do navegador do usuário final utilizando **Leaflet.js** (HTML5/CSS3/JavaScript ES6) e servida localmente por um servidor estático Node.js.

### 3. Integração QGIS (`/qgis_integration`)
* **O que faz:** Automação e publicação cartográfica. Contém a biblioteca `qgis_bridge` e os scripts de inicialização (`startup_script.py`) do QGIS Server, responsáveis por carregar o projeto `.qgz` de engenharia do mapa de forma headless e expô-lo via padrões OGC (WMS/WFS).
* **Onde é expresso:** Servidor de mapas headless (**QGIS Server**).

### 4. Infraestrutura e Datalake (`/infra`)
* **O que faz:** Núcleo de dados e orquestração. Contém a pasta `/dados` que funciona como o **Datalake Central** (abrigando a base espacial do GeoPackage `.gpkg`, a matriz `.dyndb` e imagens raster de satélite) e a pasta `/docker` destinada a gerenciar o Docker Compose e volumes de disco compartilhados.
* **Onde é expresso:** Camada de persistência local e empacotamento de containers (Docker).

---

## 🌿 Estrutura de Branches (Fluxo de Trabalho)

Para otimizar o trabalho de uma equipe de 3 integrantes, o repositório é configurado com isolamento restrito de escopos por ramificação. **Nenhum arquivo ou diretório de módulo é compartilhado entre as branches de desenvolvimento**.

### Branches de Consolidação
* **`main`**: Contém a estrutura unificada estável (todos os módulos consolidados + pasta `documentos/` de especificação). É a branch principal de produção.
* **`main-legacy`**: Contém estritamente o código legado original histórico do projeto (`old_code/`) para preservação e consulta de compatibilidade.

### Branches de Desenvolvimento (Escopos Exclusivos)
Ao fazer o checkout em qualquer uma dessas branches, o seu workspace exibirá **apenas** a pasta correspondente e o `.gitignore`/`README.md`.
* **`dev-backend`**: Exibe apenas a pasta `/backend` (Trabalho do desenvolvedor Backend).
* **`dev-frontend`**: Exibe apenas a pasta `/frontend` (Trabalho do desenvolvedor Frontend).
* **`dev-qgis-integration`**: Exibe apenas a pasta `/qgis_integration` (Trabalho do desenvolvedor SIG/QGIS).
* **`dev-infra`**: Exibe apenas a pasta `/infra` (Trabalho de DevOps para Docker e banco de dados).

---

## 🚀 Como Executar

### Pré-requisitos
* Python 3.10+ (para Backend e QGIS Integration)
* Node.js (para Frontend)
* QGIS Desktop / Server (para renderização cartográfica WMS/WFS)

### Desenvolvimento Local do Frontend
1. Acesse o diretório:
   ```bash
   cd frontend
   ```
2. Instale as dependências:
   ```bash
   npm install
   ```
3. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```
   O painel de controle estará acessível em `http://localhost:3000`.
