# 📦 Especificação Técnica: Orquestração & Nuvem OCI (`infraestrutura_orquestracao_oci`)

## 1. 🎯 Resumo Executivo & Responsabilidade Única
O módulo **`infraestrutura_orquestracao_oci`** engloba a infraestrutura como código e o ambiente de implantação em nuvem (`docker-compose.yml` e scripts de implantação OCI). Sua **responsabilidade única** é provisionar a stack completa de 5 microsserviços em contêineres Docker, gerenciar o ciclo de vida dos volumes compartilhados no DataLake e implementar a estratégia de mitigação de memória RAM física por meio de **SWAP Linux de 4GB** na instância Always Free da Oracle Cloud.

---

## 2. 📊 Arquitetura Visual & Diagrama de Sequência (Mermaid)

```mermaid
graph TB
    subgraph Oracle Cloud Infrastructure (OCI - VM AMD Micro)
        OS[Ubuntu 24.04 LTS - 1GB RAM Física]
        SWAP[Arquivo SWAP 4GB /swapfile]
        OS --- SWAP
        
        subgraph Docker Engine & Compose Ecosystem
            NGX[gd-nginx]
            FRONT[gd-frontend]
            BACK[gd-backend]
            SERVER[gd-qgis-server]
            WATCHER[gd-qgis-watcher]
        end
        
        subgraph Persistent Shared DataLake Volume
            VOL[(/infra/dados - Shared Volume)]
        end
        
        BACK --- VOL
        SERVER --- VOL
        WATCHER --- VOL
    end
```

---

## 3. 📋 Análise de Requisitos (RFs e RNFs com ID)

| ID | Tipo | Descrição do Requisito | Critério de Aceite |
| :--- | :--- | :--- | :--- |
| **RF-INF-01** | Funcional | Orquestrar os 5 microsserviços com inicialização em um único comando. | Executar `docker compose up -d` e subir toda a stack de forma automatizada. |
| **RF-INF-02** | Funcional | Compartilhar os dados do DataLake entre o Backend, QGIS Server e Watcher. | Mapear o volume host `./infra/dados:/infra/dados` em todos os contêineres necessários. |
| **RNF-INF-01**| Confiabilidade| Evitar Out-Of-Memory Daemon Crash em hardware com 1GB de RAM. | Configurar e ativar 4GB de memória virtual SWAP no Linux Ubuntu. |
| **RNF-INF-02**| Disponibilidade| Garantir autorrecuperação dos serviços em caso de reboot da VM. | Aplicar a política `restart: always` em todos os serviços no `docker-compose.yml`. |

---

## 4. 🔑 Dicionário de Variáveis, Atributos & Tipagem de Dados

| Atributo / Variável | Tipo de Dado | Descrição & Escopo | Exemplo / Valor Padrão |
| :--- | :--- | :--- | :--- |
| `docker-compose.yml` | `YAML` | Arquivo de especificação e orquestração de contêineres Docker. | N/A |
| `/swapfile` | `File` | Arquivo especial do Linux utilizado como extensão de memória RAM. | `4096 MB` (4 GB) |
| `digital_twins_net` | `Network` | Rede interna isolada do Docker (Driver Bridge) para comunicação. | `bridge` |
| `ports` | `Array` | Mapeamento de portas entre o host externo e o contêiner interno. | `"8080:8080"` |

---

## 5. 🔄 Fluxo de Dados & Contratos de Interface (Public API)

### Estrutura do Orquestrador (`docker-compose.yml`):

```yaml
version: '3.8'

services:
  gd-nginx:
    image: nginx:alpine
    ports:
      - "8080:8080"
    volumes:
      - ./infra/docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: always

  gd-backend:
    build: ./backend
    volumes:
      - ./infra/dados:/infra/dados
    restart: always

  gd-frontend:
    build: ./frontend
    restart: always

  gd-qgis-server:
    image: qgis/qgis-server:latest
    volumes:
      - ./infra/dados:/infra/dados
    restart: always

  gd-qgis-watcher:
    build: ./qgis_integration
    volumes:
      - ./infra/dados:/infra/dados
    restart: always
```

---

## 6. 🛡️ Matriz de Resiliência, Casos de Borda & Tolerância a Falhas

| Caso de Borda / Falha potencial | Impacto no Sistema | Estratégia de Mitigação / Solução Aplicada |
| :--- | :--- | :--- |
| **Esgotamento da RAM de 1GB durante o processamento espacial PyQGIS** | Queda do Docker Daemon ou encerramento abrupto do processo (OOM Killer). | Criação de arquivo SWAP de 4GB com `swappiness=10` para absorver picos de memória. |
| **Reboot não planejado da VM pela Oracle Cloud** | Todos os contêineres parariam de responder. | Configuração de `restart: always` e serviço `docker.service` habilitado no `systemctl`. |
| **Incompatibilidade de permissão de escrita no volume compartilhado** | O backend ou o watcher não conseguem salvar arquivos em `/infra/dados`. | Configuração de permissões `chmod -R 777 /infra/dados` e sincronização de PIDs. |

---

## 7. 🧪 Estratégia de Testabilidade & Cobertura (QA)

* **Testes de Infraestrutura e Carga:** Executados via SSH na Máquina Virtual.
* **Cenários Cobertos:**
  1. Execução de `sudo docker ps` para confirmar que os 5 contêineres estão no estado `Up`.
  2. Inspeção de consumo de memória via `free -h` para validar a utilização do arquivo SWAP.
  3. Simulação de reboot da VM (`sudo reboot`) e verificação do restabelecimento automático de todos os serviços.
