# 🏛️ ADR-003: Sincronização Híbrida SQLite `.dyndb` e OGC GeoPackage `.gpkg`

* **Status:** Aceito
* **Data:** 2026-06-26
* **Decisores:** Time de Arquitetura do Gêmeo Digital IoT / UNIFACS

---

## 🎯 Contexto & Problema
O sistema precisa de duas capacidades com exigências distintas:
1. Gravação ultrarrápida de matrizes dinâmicas de telemetria IoT com esquemas de colunas mutáveis.
2. Formato cartográfico espacial vetorial compatível nativamente com a norma OGC exigida pelo QGIS Server.

---

## 💡 Decisão Considerada
Utilizar um modelo híbrido:
- **`digital_twin.dyndb` (SQLite):** Banco primário de ingestão e matriz dinâmica de telemetria.
- **`digital_twin.gpkg` (GeoPackage OGC):** Cache espacial vetorial com geometrias `POINT (WGS84)` sincronizado assincronamente pela API FastAPI.

---

## ⚖️ Consequências & Trade-offs

### Positivas:
- O backend consegue ingerir planilhas brutas instantaneamente sem bloquear a renderização espacial.
- O QGIS Server consome o GeoPackage nativo sem necessidade de conversores em tempo de execução.
- Concorrência de leitura e escrita otimizada via `PRAGMA journal_mode=WAL`.

### Negativas / Limitações:
- Duplicação controlada de dados entre o banco tabular e o arquivo espacial, gerenciada via sincronização da API.
