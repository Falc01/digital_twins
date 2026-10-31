# 🐙 Backlog de Issues para o GitHub — Divisão Modular por Subtarefas

Este documento contém o texto pronto para abrir as **4 Issues leves no GitHub**, perfeitamente divididas para evitar sobrecarga em qualquer desenvolvedor da equipe de Iniciação Científica (UNIFACS).

---

## 📋 Issue #1A: [Doc 01-A] Entrada: Picos Modulares e Presets de Dias da Semana

**Título sugerido:**  
`[FEAT][DOC 01-A] Entrada: Picos Modulares Abertos e Presets de Dias da Semana (Útil, Sábado, Domingo)`

**Labels:** `module-01`, `enhancement`, `backend`, `math-model`  
**Responsável Recomendado:** Colega A (Fase 1)  
**Arquivo Exclusivo de Código:** `backend/src/simulation/macro_flow.py`  
**Arquivo de Testes:** `backend/tests/test_macro_flow.py`  

### Descrição da Issue:

#### 🎯 Contexto & Objetivo
Evoluir a curva de entrada diária para que o motor suporte:
1. Uma lista dinâmica e aberta de $M$ picos com $(\tau, \sigma, w)$ configuráveis por simulação (sem quantidade fixa);
2. Dicionários de calibração padrão para dias úteis (2 picos comerciais), sábado (3 picos com vida noturna) e domingo (2 picos sacros/familiares).

#### 📐 Especificação Técnica
- Consulte o documento completo em: [`docs/propostas_melhorias/MELHORIA_DOC01A_DIAS_DA_SEMANA_E_PICOS.md`](file:///docs/propostas_melhorias/MELHORIA_DOC01A_DIAS_DA_SEMANA_E_PICOS.md)

#### 📋 Checklist de Tarefas
- [ ] Atualizar `calculate_multimodal_bairro_population` para receber lista aberta de picos `peaks: Optional[List[CircadianPeak]]`.
- [ ] Criar presets padrão calibrados para `WEEKDAY`, `SATURDAY` e `SUNDAY`.
- [ ] Garantir o cálculo analítico do influxo diferencial por portão ($\Phi_{\text{in}, g}$).
- [ ] Escrever testes unitários em `backend/tests/test_macro_flow.py` validando 1, 2, 3 e 5 picos e os dias da semana.

#### 🏁 Critério de Aceitação (DoD)
- 100% dos testes passando (`pytest backend/tests/test_macro_flow.py`).

---

## 📋 Issue #1B: [Doc 01-B] Entrada: Sazonalidade das 4 Estações, Fator Climático e Calibração de Gamma

**Título sugerido:**  
`[FEAT][DOC 01-B] Entrada: Sazonalidade das 4 Estações, Redutor de Chuva e Override Manual de Gamma`

**Labels:** `module-01`, `enhancement`, `backend`, `climate`  
**Responsável Recomendado:** Colega A (Fase 2) ou Colega B  
**Arquivo Exclusivo de Código:** `backend/src/simulation/macro_flow.py`, `backend/shared/config_simulacao.yaml`  
**Arquivo de Testes:** `backend/tests/test_macro_flow.py`  

### Descrição da Issue:

#### 🎯 Contexto & Objetivo
Implementar a modulação do multiplicador $\gamma$ integrando:
1. As 4 estações em Salvador (Verão $1.50$, Primavera $1.10$, Outono $0.90$, Inverno $0.75$);
2. Três níveis de chuva (Sol $1.0$, Chuva Fraca $0.80$, Tempestade $0.40$);
3. Controle e override manual total pelo gestor ($\gamma_{\text{final}} = \gamma_{\text{manual}} \cdot \gamma_{\text{estacao}} \cdot \omega_{\text{clima}}$).

#### 📐 Especificação Técnica
- Consulte o documento completo em: [`docs/propostas_melhorias/MELHORIA_DOC01B_SAZONALIDADE_E_CLIMA.md`](file:///docs/propostas_melhorias/MELHORIA_DOC01B_SAZONALIDADE_E_CLIMA.md)

#### 📋 Checklist de Tarefas
- [ ] Adicionar tabela de estações e fatores climáticos no `backend/shared/config_simulacao.yaml`.
- [ ] Implementar cálculo de $\gamma_{\text{efetivo}}$ com suporte a override manual.
- [ ] Escrever testes unitários em `backend/tests/test_macro_flow.py` validando as estações, chuvas e override.

#### 🏁 Critério de Aceitação (DoD)
- 100% dos testes verdes e retrocompatibilidade com $\gamma = 1.0$ preservada.

---

## 📋 Issue #2: [Módulo 02] Injeção de Eventos: Catálogo Cultural, Cortejos Itinerantes e Blindagem de Carnaval

**Título sugerido:**  
`[FEAT][DOC 02] Injeção de Eventos: Catálogo Baiano Rico, Cortejos Móveis e Blindagem de Carnaval`

**Labels:** `module-02`, `enhancement`, `simulation`, `events`  
**Responsável Recomendado:** Colega B (Módulo de Eventos)  
**Arquivos de Código:** `backend/src/simulation/events_injection.py`, `backend/shared/calendario_cultural.json`, `backend/shared/agenda_eventos.json`  
**Arquivo de Testes:** `backend/tests/test_events_injection.py`  

### Descrição da Issue:

#### 🎯 Contexto & Objetivo
Expandir o Módulo de Injeção de Eventos (Doc 02) com o rico patrimônio cultural de Salvador e dotá-lo de robustez contra megacomemorações:
1. Cadastrar eventos reais nos arquivos JSON (Didá, Filhos de Gandhy, Gerônimo, Missas, Capoeira, Santa Bárbara e São João);
2. Modelar cortejos itinerantes em movimento através de nós ordenados;
3. Implementar blindagem de saturação física para evitar aglomerações irreais durante o Carnaval.

#### 📐 Especificação Técnica
- Consulte o documento completo em: [`docs/propostas_melhorias/MELHORIA_DOC02_INJECAO_EVENTOS.md`](file:///docs/propostas_melhorias/MELHORIA_DOC02_INJECAO_EVENTOS.md)

#### 📋 Checklist de Tarefas
- [ ] Cadastrar os eventos culturais em `calendario_cultural.json` e `agenda_eventos.json`.
- [ ] Suportar eventos itinerantes (`ITINERANT`) com cálculo de defasagem temporal entre nós vizinhos.
- [ ] Aplicar o amortecimento logístico de capacidade máxima física nos nós com eventos simultâneos.
- [ ] Criar testes unitários em `backend/tests/test_events_injection.py` validando passagem de cortejo e trava de saturação.

#### 🏁 Critério de Aceitação (DoD)
- 100% dos testes do Módulo 02 verdes (`pytest backend/tests/test_events_injection.py`).
- Nenhuma dependência externa adicionada.

---

## 📋 Issue #3: [Módulo 03] Circulação e Saída: Tipagem Urbana de POIs e Egress Dinâmico

**Título sugerido:**  
`[FEAT][DOC 03] Markov: Tipagem de POIs (Comércio, Sacro, Cultura), Gravidade Temporal e Egress`

**Labels:** `module-03`, `enhancement`, `simulation`, `markov`  
**Responsável Recomendado:** Colega C (Módulo de Circulação & Saída)  
**Arquivo Exclusivo de Código:** `backend/src/simulation/markov_circulation.py`  
**Arquivo de Testes:** `backend/tests/test_markov_circulation.py`  

### Descrição da Issue:

#### 🎯 Contexto & Objetivo
Evoluir a Cadeia de Markov e o Modelo Gravitacional (Doc 03) para incorporar dinâmicas urbanas reais:
1. Classificar formalmente os nós em `GATE`, `COMERCIO`, `RELIGIOSO` e `CULTURAL`;
2. Criar atratividade gravitacional dinâmica $\alpha_j(t, \text{dia})$ (igrejas atraem no domingo de manhã; bares atraem no sábado à noite);
3. Implementar inércia de "creep flow" quando um nó estiver com densidade $> 85\%$;
4. Garantir cálculo exato do vetor de evasão nos portões de borda ($Egress$).

#### 📐 Especificação Técnica
- Consulte o documento completo em: [`docs/propostas_melhorias/MELHORIA_DOC03_CIRCULACAO_MARKOV_SAIDA.md`](file:///docs/propostas_melhorias/MELHORIA_DOC03_CIRCULACAO_MARKOV_SAIDA.md)

#### 📋 Checklist de Tarefas
- [ ] Adicionar campo `poi_type` aos nós de configuração do grafo urbano.
- [ ] Implementar a tabela horária/semanal de atratividade $\alpha_j(t, \text{dia})$.
- [ ] Implementar o aumento de inércia $P_{jj}$ sob alta densidade local de pessoas ("creep flow").
- [ ] Garantir que o vetor de saída $N_{\text{egress}}$ seja retornado com rigor estocástico (soma das probabilidades da linha = 100%).
- [ ] Escrever testes unitários em `backend/tests/test_markov_circulation.py`.

#### 🏁 Critério de Aceitação (DoD)
- 100% dos testes do Módulo 03 verdes (`pytest backend/tests/test_markov_circulation.py`).
- Matriz estocástica invariante preservada em todas as rodadas.
