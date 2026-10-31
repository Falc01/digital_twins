# 🐙 Backlog de Issues para o GitHub — Divisão por Módulo (1 Dev por Subsistema)

Este documento contém o texto pronto para abrir as **3 Issues no GitHub**, distribuídas de forma isolada para cada integrante da equipe de Iniciação Científica (UNIFACS).

---

## 📋 Issue #1: [Módulo 01] Evolução do Macro-Fluxo: Picos Modulares, Perfis Semanais e Sazonalidade

**Título sugerido:**  
`[FEAT][DOC 01] Macro-Fluxo: Picos Modulares Abertos, Presets de Dias da Semana e Fator Sazonal/Clima`

**Labels:** `module-01`, `enhancement`, `backend`, `math-model`  
**Responsável Recomendado:** Colega A (Módulo de Entrada)  
**Arquivo Exclusivo de Código:** `backend/src/simulation/macro_flow.py`  
**Arquivo de Testes:** `backend/tests/test_macro_flow.py`  

### Descrição da Issue:

#### 🎯 Contexto & Objetivo
Evoluir o Módulo de Entrada (Doc 01) para que ele deixe de ter uma curva de 3 picos fixos e passe a suportar:
1. Uma lista arbitrária de $M$ picos com $(\tau, \sigma, w)$ dinâmicos por simulação;
2. Perfis padrão de dias da semana (`WEEKDAY`, `SATURDAY`, `SUNDAY`);
3. Multiplicador sazonal mensal de Salvador ($M(1..12)$) e fator de atenuação de chuva ($\omega_{\text{clima}}$).

#### 📐 Especificação Técnica
- Consulte o documento completo em: [`docs/propostas_melhorias/MELHORIA_DOC01_MACRO_FLUXO_ENTRADA.md`](file:///docs/propostas_melhorias/MELHORIA_DOC01_MACRO_FLUXO_ENTRADA.md)

#### 📋 Checklist de Tarefas
- [ ] Atualizar `calculate_multimodal_bairro_population` para receber lista aberta de picos `peaks: Optional[List[CircadianPeak]]`.
- [ ] Criar dicionários de presets calibrados para dias úteis (2 picos), sábado (3 picos) e domingo (2 picos).
- [ ] Implementar a tabela mensal $M(\text{mês})$ de Salvador e categorias de chuva (`SOL_LIMPO`, `CHUVA_MODERADA`, `TEMPESTADE`).
- [ ] Escrever testes unitários em `backend/tests/test_macro_flow.py` cobrindo picos customizados e validações de dia/clima.

#### 🏁 Critério de Aceitação (DoD)
- 100% dos testes do Módulo 01 passando (`pytest backend/tests/test_macro_flow.py`).
- Zero alteração em arquivos fora do Módulo 01.

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
