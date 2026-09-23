# 🎯 Contexto Ativo de Sessão — digital_twins

- **Data de Atualização**: 23 de Setembro de 2026
- **Estado Atual**:
  1. Suíte Modular de Documentação Técnica (`docs/explanation/dados_sinteticos/00_` a `05_`) concluída e versionada no GitHub (`origin/main`).
  2. Colegas de equipe (Perrone / Daniel) implementaram a parte referente ao Subsistema de Macro-Fluxo Circadiano (Doc 01) em `backend/src/simulation/` (`macro_flow.py`, `schemas.py`, `cli_macro_flow.py`), configuraram `config_simulacao.yaml`, integraram rotas na API FastAPI (`routers/simulation.py`) e adicionaram testes (`tests/test_macro_flow.py`).
  3. Módulos matemáticos desenhados e escopo de trabalho do João:
     - Doc 00: Ingestão e Barramento Central;
     - Doc 01: Macro-Fluxo Diário ($N_{\text{rotina}}$) [Implementado pelos colegas - sob auditoria];
     - Doc 02: Injeção Dinâmica de Eventos ($\mathbf{E}$);
     - Doc 03: Circulação Markoviana e POIs ($\mathbf{P}$);
     - Doc 04: Saturação de Richards, Ruído IoT e Datalake;
     - Doc 05: Validação Estatística (KS 2D / KL) e Langevin.
- **Foco Ativo**: Auditar a implementação dos colegas (`backend/src/simulation/` e rotas da API) em relação aos requisitos matemáticos e arquiteturais dos Docs 00-05, reportar inconsistências e preparar para codar os módulos do João.
- **Resumo do Último Marco**: Código dos colegas integrado localmente; auditoria técnica em andamento.
