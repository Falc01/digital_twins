# 💡 Visão Geral do Sistema: Razões de Design & Arquitetura de Mapas

Este documento apresenta a fundamentação teórica e as decisões de engenharia que moldaram a arquitetura do **Gêmeo Digital da UNIFACS**, destacando o comparativo entre QGIS Desktop e QGIS Server e a topologia Hub-and-Spoke.

---

## 1. QGIS Desktop vs. QGIS Server: Entendendo as Diferenças

Durante a concepção da infraestrutura geoespacial, foi necessário decidir entre executar a interface do QGIS Desktop no servidor ou utilizar o motor dedicado QGIS Server.

| Aspecto de Engenharia | QGIS Desktop | QGIS Server (Escolha do Projeto) |
| :--- | :--- | :--- |
| **Interface de Usuário** | Interface gráfica (GUI) completa com janelas, menus e ferramentas visuais. | Sem interface gráfica (*headless*). Executa de forma transparente em background. |
| **Objetivo Principal** | Autoria manual, design cartográfico, edição de vetores e análise espacial por humanos. | Publicação web automatizada, servindo tiles de mapa (WMS) e feições (WFS) via HTTP. |
| **Consumo de Memória (RAM)** | ~1.5 GB a 2.0 GB por instância aberta. | ~150 MB a 300 MB por processo em contêiner Docker. |
| **Protocolo de Comunicação**| Cliques manuais e eventos de janela do SO. | Requisições HTTP REST / OGC (WMS/WFS/WMTS). |
| **Concorrência** | Arquivo `.qgz` único travado por 1 usuário local. | Múltiplos clientes consumindo imagens via WMS concorrentemente. |

---

## 2. Os Desafios de Rodar QGIS Desktop em Kubernetes / Servidores

Tentar servir o QGIS Desktop em nuvem via streaming de vídeo (VNC/X11) traria severas limitações:
1. **Alto Custo de Nuvem (Densidade de RAM):** Na máquina virtual OCI Always Free de 1GB de RAM, abrir o QGIS Desktop provocaria travamento imediato por falta de memória (*OOM Kill*).
2. **Conflito de Arquivos Estáticos:** Arquivos de projeto QGIS (`.qgz`) não foram desenhados para escrita simultânea por múltiplos operadores.
3. **Latência de Streaming:** Fazer streaming do aplicativo via web gera consumo excessivo de banda e latência nos cliques do mapa.

### A Solução Adotada: QGIS Server Headless + Leaflet.js
Separamos a **autoria do mapa** (feita offline pelo cartógrafo no QGIS Desktop) do **serviço de mapa** (servido de forma ultra-rápida via QGIS Server Headless para o frontend Leaflet).

---

## 3. A Topologia Hub-and-Spoke (Estrela)

Para garantir que a queda de um serviço não derrube o ecossistema, o sistema adota a topologia em Estrela:

- Os contêineres **não conversam diretamente entre si em cascata bloqueante**.
- Todos orbitam o **Datalake Central** (volume montado no sistema de arquivos).
- **Vantagem de Tolerância a Falhas:** Se o QGIS Server for reiniciado, a API FastAPI continua recebendo dados de telemetria IoT normalmente no banco SQLite, e o painel tabular do frontend permanece 100% operacional.
