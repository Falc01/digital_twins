# 💡 Conceitos: Concorrência, Transações e Locks de Banco de Dados

Este documento explica o modelo de concorrência, prevenção de travamentos de arquivo (*locks*) e integridade de dados adotado no **Gêmeo Digital IoT**.

---

## 🔒 1. O Desafio da Concorrência em Bancos de Arquivo Único (SQLite / GeoPackage)

Tanto o banco da matriz dinâmica (`digital_twin.dyndb`) quanto o banco espacial GeoPackage (`digital_twin.gpkg`) são baseados no mecanismo do **SQLite**.

Por padrão, quando um processo tenta escrever em um banco SQLite padrão enquanto outro processo está lendo, pode ocorrer o erro:
`sqlite3.OperationalError: database is locked`

---

## ⚡ 2. A Solução: Modo WAL (Write-Ahead Logging)

Para permitir leitura simultânea em tempo real (QGIS Server servindo WMS) enquanto a API FastAPI insere novos dados de telemetria, ativamos o modo **WAL (Write-Ahead Logging)** nas conexões SQLite:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```

### Como Funciona o Modo WAL:
1. **Separador de Leitura e Escrita:** As alterações de escrita são gravadas inicialmente em um arquivo auxiliar de log (`.dyndb-wal`) sem bloquear o arquivo principal de dados (`.dyndb`).
2. **Leitores Não Bloqueiam Escritores:** O QGIS Server pode ler snapshots consistentes do mapa enquanto o backend insere leituras IoT simultaneamente.
3. **Escritores Não Bloqueiam Leitores:** A navegação do usuário no mapa Leaflet não sofre travamentos ou congelamentos durante a ingestão de planilhas pesadas.
4. **Busy Timeout de 5 Segundos (`busy_timeout=5000`):** Se duas gravações ocorrerem no mesmo milissegundo, a segunda gravação aguardará até 5000ms pela liberação da trava antes de lançar erro.

---

## 🔄 3. Estratégia de Sincronização Assíncrona

```
[ Ingestão CSV/Excel ] ──► [ Inserção SQLite .dyndb ]
                                     │ (Trigger / Background Task)
                                     ▼
                        [ Conversão Batch Espacial ]
                                     │
                                     ▼
                        [ Atualização .gpkg (Modo WAL) ] ──► [ QGIS Watcher Signal ]
```

1. A gravação inicial ocorre com máxima prioridade no `.dyndb`.
2. A atualização das feições espaciais no GeoPackage ocorre em lote (*batch update*), minimizando o número de transações de escrita e garantindo performance em tempo real.
