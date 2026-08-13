# 🏛️ ADR-002: Topologia Hub-and-Spoke com Datalake Compartilhado

* **Status:** Aceito
* **Data:** 2026-06-26
* **Decisores:** Time de Arquitetura do Gêmeo Digital IoT / UNIFACS

---

## 🎯 Contexto & Problema
A arquitetura necessitava integrar microsserviços heterogêneos (API Python FastAPI, Servidor C++ QGIS Server, Daemon PyQGIS e Frontend Web Nginx) sem criar dependências em cascata síncronas e frágeis.

---

## 💡 Decisão Considerada
Adotar a **Topologia Estrela (Hub-and-Spoke)**, na qual todos os contêineres orbitam um **Datalake Central** baseado em um volume de disco compartilhado (`/infra/dados`).

---

## ⚖️ Consequências & Trade-offs

### Positivas:
- **Desacoplamento Total:** Nenhum contêiner depende do estado ativo em cascata do outro.
- **Resiliência e Tolerância a Falhas:** Se o QGIS Server for suspenso para manutenção, o backend FastAPI continua efetuando a ingestão de dados IoT no SQLite normalmente.
- **Simplicidade de Infraestrutura:** Elimina a necessidade de instalar brokers pesados de mensageria (Kafka/RabbitMQ) na VM de 1GB da OCI.

### Negativas / Limitações:
- Exige atenção rigorosa ao controle de trava de arquivos (*file locking*) no SQLite, resolvido via modo WAL.
