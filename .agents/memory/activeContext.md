# 🎯 Contexto Ativo de Sessão — digital_twins

- **Data de Atualização**: 23 de Setembro de 2026
- **Estado Atual**:
  1. Suíte Modular de Documentação Técnica (`docs/explanation/dados_sinteticos/00_` a `05_`) concluída e versionada no GitHub (`origin/main`).
  2. Colegas de equipe (Perrone) enviaram implementações do módulo de simulação para o repositório remoto (`backend/src/simulation/` com `macro_flow.py`, `schemas.py`, rotas FastAPI e testes).
  3. Módulos matemáticos desenhados e prontos para integração:
     - Doc 00: Ingestão e Barramento Central;
     - Doc 01: Macro-Fluxo Diário ($N_{\text{rotina}}$);
     - Doc 02: Injeção Dinâmica de Eventos ($\mathbf{E}$);
     - Doc 03: Circulação Markoviana e POIs ($\mathbf{P}$);
     - Doc 04: Saturação de Richards, Ruído IoT e Datalake;
     - Doc 05: Validação Estatística (KS 2D / KL) e Langevin.
- **Foco Ativo**: Executar `git pull origin main`, auditar a implementação dos colegas em `backend/src/simulation/` em relação aos Docs 00 a 05, implementar os módulos restantes do João e consolidar o pipeline de dados sintéticos integrado com a API e o GeoPackage.
- **Resumo do Último Marco**: Documentação modular aprovada e sincronizada; código inicial de simulação enviado pelos colegas para o repo remoto.
