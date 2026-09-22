# 📖 Referência Técnica: Dicionário de Dados & Esquemas de Armazenamento

Este documento define detalhadamente a estrutura de todos os artefatos de dados, tabelas dinâmicas, esquemas espaciais GeoPackage e metadados JSON do **Gêmeo Digital IoT**.

---

## 🗄️ 1. Datalake Central (`/infra/dados/`)

Os dados do sistema são armazenados em um volume compartilhado montado nos contêineres Docker da stack:

```
infra/dados/
├── digital_twin.dyndb      # Matriz SQLite binária de alta velocidade (Telemetria)
├── digital_twin.gpkg       # Banco Espacial OGC GeoPackage (Cartografia WMS/WFS)
├── sensors_metadata.json   # Metadados de registro e status dos sensores
└── status.json             # Heartbeat e timestamps de sincronização da API
```

---

## 📊 2. Matriz Dinâmica SQLite (`digital_twin.dyndb`)

A matriz dinâmica armazena todas as tabelas de telemetria criadas via ingestão de dados IoT.

### Tabela Interna de Controle: `sys_active_tables`
Armazena qual tabela do DataLake está atualmente selecionada para exibição no dashboard Leaflet.

| Campo | Tipo SQL | Chave | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY | Identificador único numérico. |
| `table_name` | `TEXT` | UNIQUE | Nome da tabela dinâmica de telemetria ativa. |
| `activated_at` | `DATETIME` | - | Timestamp da última seleção. |

### Tabela Genérica de Telemetria IoT (`table_name`)

| Campo | Tipo SQL | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PRIMARY KEY AUTOINCREMENT | ID sequencial do registro. |
| `sensor_id` | `TEXT` | NOT NULL | ID do dispositivo sensor (ex: `TEMP_PELO_01`). |
| `latitude` | `REAL` | NOT NULL | Latitude WGS84 em graus decimais. |
| `longitude` | `REAL` | NOT NULL | Longitude WGS84 em graus decimais. |
| `timestamp` | `DATETIME` | NOT NULL | Momento da coleta do dado IoT. |
| `[variavel_1]` | `REAL / TEXT` | NULLABLE | Variável de telemetria dinamicamente detectada. |
| `[variavel_N]` | `REAL / TEXT` | NULLABLE | Atributo IoT adicional. |

---

## 🌍 3. Cache Espacial GeoPackage (`digital_twin.gpkg`)

O GeoPackage cumpre a norma OGC SQLite para consumo nativo pelo QGIS Server.

### Tabela Espacial Vetorial: `sensores_spatial`

| Coluna | Tipo GeoPackage | Descrição |
| :--- | :--- | :--- |
| `fid` | `INTEGER PRIMARY KEY` | ID de feição SQLite. |
| `geom` | `POINT (EPSG:4326)` | Geometria espacial contendo a localização do sensor. |
| `sensor_id` | `TEXT` | Código único do sensor de telemetria. |
| `tabela_origem` | `TEXT` | Nome da tabela `.dyndb` associada ao sensor. |
| `ultima_leitura` | `DATETIME` | Data e hora do dado mais recente. |
| `valor_atual` | `REAL` | Valor numérico da variável em exibição no mapa. |

---

## 📄 4. Arquivos de Metadados JSON

### A. Metadados de Sensores (`sensors_metadata.json`)
```json
{
  "TEMP_PELO_01": {
    "sensor_id": "TEMP_PELO_01",
    "latitude": -12.9714,
    "longitude": -38.5123,
    "tipo": "Temperatura",
    "unidade": "°C",
    "status": "ativo",
    "ultima_atualizacao": "2026-08-13T12:00:00Z"
  }
}
```

### B. Heartbeat do Sistema (`status.json`)
```json
{
  "last_sync_gpkg": "2026-08-13T12:05:00Z",
  "active_table": "telemetria_pelourinho",
  "qgis_status": "ONLINE",
  "sensor_count": 42
}
```
