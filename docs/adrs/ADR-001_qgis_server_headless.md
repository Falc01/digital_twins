# 🏛️ ADR-001: Adoção do QGIS Server Headless em vez de QGIS Desktop em Nuvem

* **Status:** Aceito
* **Data:** 2026-06-26
* **Decisores:** Time de Arquitetura do Gêmeo Digital IoT / UNIFACS

---

## 🎯 Contexto & Problema
Para a camada de visualização cartográfica geoespacial do Gêmeo Digital (Pelourinho, Salvador/BA), precisávamos servir mapas cartográficos ricos baseados no ecossistema QGIS.
Surgiu a proposta inicial de executar instâncias da interface gráfica do QGIS Desktop dentro de contêineres e transmiti-las via streaming (VNC) para o navegador web.

---

## 💡 Decisão Considerada
Adotar o **QGIS Server** em modo sem interface gráfica (*Headless*) rodando nativamente em contêiner Docker, desacoplado da interface web Leaflet.js.

---

## ⚖️ Consequências & Trade-offs

### Positivas:
- **Redução Massiva de Consumo de RAM:** QGIS Server consome ~150MB de RAM por processo, contra ~2GB de uma instância do QGIS Desktop com GUI. Isso viabiliza a execução na máquina virtual gratuita da Oracle Cloud (OCI) de 1GB de RAM.
- **Serviço OGC Padronizado:** Exposição de endpoints WMS (imagens de mapa) e WFS (feições GeoJSON) padrão da indústria.
- **Concorrência Escalável:** Suporte a múltiplos clientes HTTP acessando o mapa em tempo real sem conflitos de travamento de arquivo do aplicativo desktop.

### Negativas / Limitações:
- Requer a configuração prévia e autoria do arquivo de projeto `.qgz` via QGIS Desktop local antes do envio para o servidor.
