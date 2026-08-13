# 📖 Referência Técnica: Variáveis de Ambiente & Mapeamento de Portas

Este documento compila todas as portas de rede, variáveis de ambiente e montagens de volumes de disco utilizadas nos contêineres Docker do **Gêmeo Digital IoT**.

---

## 🌐 1. Mapeamento Geral de Portas de Rede

```
                               ┌────────────────────────────────┐
                               │  Nginx Gateway (Porta 8080)    │
                               └───────────────┬────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
    ┌────────────────────┐          ┌────────────────────┐          ┌────────────────────┐
    │ Frontend Web (80)  │          │ Backend API (8000) │          │ QGIS Server (8081) │
    └────────────────────┘          └────────────────────┘          └────────────────────┘
```

| Serviço | Nome do Container | Porta Interna | Porta Exposta (Host/Nginx) | Função |
| :--- | :--- | :--- | :--- | :--- |
| **Nginx Gateway** | `nginx_gateway` | `80` | **`8080` (Público)** | Proxy reverso e balanceador de carga único. |
| **FastAPI Backend**| `fastapi_api` | `8000` | Interno (`8080/api`) | REST API, Ingestão CSV/Excel e CRUD de sensores. |
| **Frontend Web** | `frontend_web` | `80` | Interno (`8080/`) | Dashboard Leaflet.js, HTML5 e CSS. |
| **QGIS Server** | `qgis_server` | `8081` | Interno (`8080/qgis`)| Servidor Headless OGC WMS/WFS. |
| **QGIS Watcher** | `qgis_watcher` | N/A | Interno (Background) | Daemon PyQGIS de sincronização de projetos `.qgz`. |

---

## ⚙️ 2. Variáveis de Ambiente (Environment Variables)

As variáveis de ambiente são injetadas via `docker-compose.yml` ou arquivo `.env` local na raiz:

### Backend FastAPI (`fastapi_api`)
| Variável | Valor Padrão | Descrição |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` / `development` | Define modo de log e reload da aplicação. |
| `DATA_DIR` | `/app/infra/dados` | Caminho do volume montado contendo as bases SQLite/GeoPackage. |
| `LOG_LEVEL` | `INFO` | Nível de detalhamento dos logs Python. |
| `CORS_ORIGINS` | `*` | Origens HTTP permitidas para requisições cross-origin. |

### QGIS Server (`qgis_server`)
| Variável | Valor Padrão | Descrição |
| :--- | :--- | :--- |
| `QGIS_PROJECT_FILE` | `/io/infra/dados/pelourinho_map.qgz` | Caminho absoluto do projeto cartográfico `.qgz`. |
| `MAX_SERVER_THREADS` | `4` | Número de threads de renderização WMS paralela. |
| `QGIS_SERVER_LOG_LEVEL` | `1` (Warning) | Nível de log do motor C++ do QGIS Server. |

---

## 💾 3. Volume de Armazenamento Compartilhado

Todos os microsserviços leem e escrevem no volume de dados compartilhado:

- **Host (Máquina Real / VM):** `./infra/dados`
- **Contêineres Docker:** `/app/infra/dados` ou `/io/infra/dados`
- **Permissões de Leitura/Escrita:** `0777` ou `u+rw` para permitir concorrência do usuário Docker.
