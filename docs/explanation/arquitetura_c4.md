# 🏛️ Conceitos & Arquitetura C4: Gêmeo Digital IoT

Este documento apresenta a modelagem formal da arquitetura do sistema do **Gêmeo Digital da UNIFACS**, utilizando o **Modelo C4** (Contexto e Contêineres) para mapear os componentes, barramentos de comunicação e fluxos de persistência.

---

## 1. Visão de Contexto (Modelo C4 - Nível 1)

O mapa de contexto estabelece as fronteiras do sistema, mostrando como o operador/usuário final e os dispositivos/arquivos IoT interagem com a solução.

```mermaid
graph TD
    User([👤 Usuário Final / Operador]) -->|Interage com mapa e faz upload| GDSystem[🖥️ Sistema do Gêmeo Digital]
    IoTData([🔌 Dispositivos IoT / Planilhas CSV-Excel]) -->|Ingere dados brutos heterogêneos| GDSystem
    GDSystem -->|Consome telemetria e renderiza| MatrizDB[(📊 Datalake / SQLite + GeoPackage)]
```

### Componentes do Nível 1:
* **Usuário Final / Operador:** Acessa o dashboard web no navegador para visualizar o estado em tempo real dos sensores e cadastrar novas coordenadas.
* **Sistema do Gêmeo Digital:** Ecossistema em contêineres que processa, valida, geoespacializa e serve os dados cartográficos.
* **Datalake Central:** Camada de persistência local contendo a matriz dinâmica `.dyndb` e o banco espacial `.gpkg`.

---

## 2. Visão de Contêineres (Modelo C4 - Nível 2)

A aplicação adota a **Topologia Estrela (Hub-and-Spoke)**, na qual 5 microsserviços Docker desacoplados orbitam um volume de dados compartilhado.

```mermaid
flowchart TD
    %% Usuário e Nginx Gateway
    Client([👤 Navegador Web / Cliente]) -->|Requisição HTTP :8080| Nginx["🌐 Nginx Gateway Proxy<br>(Contêiner Nginx)"]
    
    subgraph Services ["🐳 Microsserviços Docker"]
        Nginx -->|/api/*| API["⚡ Backend REST API<br>(FastAPI / Python)"]
        Nginx -->|/ | Front["🎨 Interface Web<br>(HTML5 / Leaflet.js)"]
        Nginx -->|/qgis/*| QGIS["🗺️ Servidor GIS Headless<br>(QGIS Server)"]
        Watcher["⚙️ GIS Watcher Daemon<br>(PyQGIS Daemon)"]
    end
    
    subgraph Storage ["💾 Datalake Central Compartilhado (/infra/dados)"]
        DynDB[("📊 Matriz Dinâmica<br>(digital_twin.dyndb)")]
        GPKG[("🌍 GeoPackage Espacial<br>(digital_twin.gpkg)")]
        QGZ[("🗺️ Projeto Cartográfico<br>(pelourinho_map.qgz)")]
        Status[("📄 Heartbeat & Metadados<br>(status.json)")]
    end

    %% Integrações
    API -->|1. Grava Telemetria| DynDB
    API -->|2. Converte & Atualiza| GPKG
    API -->|3. Atualiza Timestamp| Status
    Watcher -->|4. Monitora & Regenera| QGZ
    QGIS -->|5. Lê Projeto & Camadas| QGZ
    QGIS -->|6. Serve WMS/WFS| Nginx
```

---

## 3. Padrão Adapter (Design Pattern)

A API FastAPI atua como um **Adaptador de Dados (Data Adapter)**:
1. Os dados brutos de entrada (CSV, Excel ou payloads IoT) podem possuir qualquer estrutura de colunas.
2. A API ingested esses dados e os padroniza na matriz dinâmica `.dyndb`.
3. Em seguida, a API adapta esses registros tabulares em feições geométricas vetoriais de pontos (`POINT`) dentro do arquivo GeoPackage `.gpkg`.
4. Dessa forma, o **QGIS Server** não precisa entender a lógica de negócio ou ingestão IoT; ele apenas consome a especificação padrão OGC do GeoPackage.
