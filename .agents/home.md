# 🏠 Home Local do Supervisor — digital_twins (Padrão Atlas v2.0)

## 📊 Status do Projeto (Operação v2.0 Ativa)
- **Status Geral**: **Subsistema de Circulação de Rede via Cadeias de Markov (Doc 03) Concluído e Homologado**. Total de 33/33 testes unitários verdes no backend. Aguardando entrega do Doc 02 pelos colegas e preparando implementação do Doc 04 (Saturação de Richards e Ruído IoT) e Doc 00 (Barramento Central Integrado).
- **Contexto Ativo**: [.agents/memory/activeContext.md](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/memory/activeContext.md)
- **Progresso de Tarefas**: [.agents/memory/progress.md](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/memory/progress.md)
- **Log de Decisões**: [.agents/memory/decisionsLog.md](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/memory/decisionsLog.md)
- **Cofre de Ideias Local**: [.agents/ideas.md](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/ideas.md)

---

## 🏛️ Motor Dialético: Conselho dos Seis Chapéus (`.agents/council/`)
- 🎩 **Status**: Ativo em 6 personas ([`hat_white.md`](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/council/hat_white.md) a [`hat_blue.md`](file:///C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/.agents/council/hat_blue.md)).
- 🎯 **Uso**: Execute `/conselho [proposta]` para sabatina formal completa antes de refatorações de simulação, alterações em esquemas GeoPackage ou decisões de arquitetura de containers.

---

## ⚙️ Stack Técnica Oficial
- **Backend & Simulação**: Python 3.12+, FastAPI, Uvicorn, Pydantic, GeoPackage SQLite (`.gpkg`).
- **Cartografia & GIS**: QGIS Server Headless, PyQGIS Daemon (`.qgz`), Leaflet.js.
- **Infraestrutura**: Docker Compose (5 containers) com Nginx Gateway (porta 8080).
- **Testes**: `pytest backend/tests/` (33/33 testes passando).

---

## 🚀 Foco Ativo & Próximos Passos
1. **Aguardar Doc 02**: Receber módulo de Injeção Dinâmica de Eventos ($E(t)$) da equipe.
2. **Implementar Doc 04**: Modelagem de Saturação de Richards, Ruído IoT e Datalake.
3. **Integrar Doc 00**: Barramento Central Integrado com persistência periódica no GeoPackage.
