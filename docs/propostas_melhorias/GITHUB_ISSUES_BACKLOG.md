# 🐙 Backlog de Issues para o GitHub — Novas Funcionalidades de Simulação

Este documento contém a redação pronta e padronizada das **3 Issues do GitHub**, prontas para serem copiadas e criadas no repositório pela equipe de Iniciação Científica (UNIFACS).

---

## 📋 Issue #1: Modelagem de Diferenciação por Dias da Semana & Simulação Multidiária

**Título sugerido:**  
`[FEAT] Diferenciação Circadiana por Dias da Semana (Úteis vs Finais de Semana) e Suporte Multidiário`

**Labels:** `enhancement`, `backend`, `simulation`, `math-model`, `doc01`

### Descrição da Issue:

#### 🎯 Contexto & Motivação
Atualmente, o subsistema de Macro-Fluxo (Doc 01 / `macro_flow.py`) avalia uma única curva trimodal fixa (09h30, 12h30, 16h48) para todos os dias. No Pelourinho real, a dinâmica de fluxo de uma terça-feira comercial é profundamente distinta de um sábado (que possui ápice noturno prolongado até as 23h nos largos e bares) e de um domingo (com pico sacral matinal na Igreja do Rosário dos Pretos e pôr do sol na Praça da Sé).

Além disso, o motor de rollout (`rollout.py`) executa apenas ciclos de 24 horas estáticas de um dia genérico, impedindo a análise contínua de uma semana inteira (Segunda a Domingo).

#### 📐 Especificação Técnica de Referência
- Consulte o documento completo em: [`docs/propostas_melhorias/RFC-001_dias_da_semana_e_ciclos_temporais.md`](file:///docs/propostas_melhorias/RFC-001_dias_da_semana_e_ciclos_temporais.md)

#### 📋 Tarefas Técnicas de Implementação
- [ ] **Modelagem no `macro_flow.py`**:
  - [ ] Implementar enum/tipo `DayType` (`WEEKDAY`, `SATURDAY`, `SUNDAY`).
  - [ ] Criar constante `DAY_OF_WEEK_PROFILES` com picos específicos ($\tau_m, \sigma_m, w_m$) e capacidades ($N_{\min}, N_{\max}$) para cada categoria.
  - [ ] Adicionar suporte a `day_of_week` no cálculo analítico da população do bairro $N_{\text{bairro}}(t, d)$.
- [ ] **Rollout Multidiário no `rollout.py`**:
  - [ ] Adicionar método `run_multi_day_batch(days=7, start_weekday=0, step_minutes=30.0)` preservando o estado residual dos nós na virada da meia-noite ($t=24.0 \to t=0.0$).
  - [ ] Adicionar campos `day_index` e `weekday_name` nos metadados do `RolloutStep`.
- [ ] **Interface Web no Streamlit (`simulacao/`)**:
  - [ ] Adicionar filtro de dia da semana na barra lateral (`sidebar.py`).
  - [ ] Exibir linhas verticais tracejadas de troca de dia no gráfico de linha temporal (`timeline_view.py`).
- [ ] **Testes Automatizados (`backend/tests/test_macro_flow.py` e `test_rollout.py`)**:
  - [ ] Testar se Sábado atinge ápice após 21h00 enquanto Domingo desacelera após 19h00.
  - [ ] Garantir continuidade e conservação de fluxo na virada de 7 dias consecutivos.

#### 🏁 Critérios de Aceitação (DoD)
- Simulação de 7 dias executa 336 passos (a cada 30 min) sem interrupções ou erros de descontinuidade.
- Cobertura de testes $\ge 90\%$ no subsistema de fluxo com dias da semana.

---

## 📋 Issue #2: Expansão Cultural de Eventos & Blindagem contra Saturação em Eventos Atípicos (Carnaval)

**Título sugerido:**  
`[FEAT] Enriquecimento do Catálogo Cultural de Eventos e Blindagem Estocástica para o Carnaval (Circuito Batatinha)`

**Labels:** `enhancement`, `simulation`, `safety-guard`, `doc02`, `doc03`

### Descrição da Issue:

#### 🎯 Contexto & Motivação
O módulo de injeção de eventos (Doc 02 / `events_injection.py`) contém atualmente apenas 2 eventos semanais fixos e 2 eventos na agenda pontual. Salvador possui um dos calendários afro-culturais e litúrgicos mais vibrantes do país (ensaios de blocos, afoxés itinerantes, rodas de capoeira, festas de largo).

Adicionalmente, identificamos dois gargalos arquiteturais graves:
1. No `rollout.py`, o vetor de eventos $E(t)$ é somado apenas na exibição e não entra no estado dinâmico da cadeia de Markov; quando o evento acaba, as pessoas somem em vez de circular pelas ruas e sair pelos portões.
2. Em eventos extremos (Carnaval - Circuito Batatinha), o excesso de pedestres causa estrangulamento nas ladeiras ("creep flow") e a PMBA reconfigura os portões com portais de abordagem de segurança. O sistema precisa de blindagem para não quebrar ou gerar probabilidades negativas/irreais sob $\gamma \ge 3.5$.

#### 📐 Especificação Técnica de Referência
- Consulte o documento completo em: [`docs/propostas_melhorias/RFC-002_incremento_eventos_e_blindagem_carnaval.md`](file:///docs/propostas_melhorias/RFC-002_incremento_eventos_e_blindagem_carnaval.md)

#### 📋 Tarefas Técnicas de Implementação
- [ ] **Enriquecimento dos Dados**:
  - [ ] Expandir `backend/shared/calendario_cultural.json` com rodas de capoeira (Terreiro), ensaio da Didá (João de Deus), Afoxé Filhos de Gandhy e Gerônimo no Passo.
  - [ ] Expandir `backend/shared/agenda_eventos.json` com Festa de Santa Bárbara, Ensaio de Verão, São João e os 6 dias de Carnaval.
- [ ] **Modelagem de Eventos Itinerantes (Cortejos)**:
  - [ ] Suportar eventos em movimento com propagação de pulso temporal entre múltiplos nós adjacentes (baseado em velocidade de caminhada de $\sim 2\text{ km/h}$).
- [ ] **Blindagem de Saturação & Acoplamento no Rollout**:
  - [ ] Corrigir `rollout.py` para injetar o fluxo de evento $\Delta E_j(t)$ no vetor de estado que alimenta a matriz de Markov do passo seguinte.
  - [ ] Implementar mecanismo de inércia por saturação ("creep flow"): se ocupação $> 85\%$, a retenção $P_{jj}$ aumenta e a taxa de evacuação cai suavemente.
  - [ ] Implementar reconfiguração dos pesos de portão $\mathbf{w}$ durante o Carnaval (portais de triagem da PMBA).
- [ ] **Testes de Estresse (`backend/tests/test_events_injection.py` e `test_rollout.py`)**:
  - [ ] Teste de estresse com $\gamma = 4.0$ comprovando estabilidade numérica (sem NaN, matriz estocástica válida com soma das linhas = 100%).
  - [ ] Teste de dissipação: pedestres atraídos por um show continuam saindo pelos portões de borda após o término do evento.

#### 🏁 Critérios de Aceitação (DoD)
- Não há desaparecimento repentino de multidões pós-evento.
- O sistema suporta cenários com até 1.500 pessoas circulando simultaneamente no Pelourinho com tempo de resposta $< 100\text{ ms}$ por tick.

---

## 📋 Issue #3: Modelo Global de Sazonalidade Anual (12 Meses) & Atenuação por Condições Climáticas

**Título sugerido:**  
`[FEAT] Modelo de Sazonalidade Anual para Salvador (12 Meses) com Atenuação Pluviométrica (Chuva/Tempestade)`

**Labels:** `enhancement`, `backend`, `simulation`, `climate`, `doc01`

### Descrição da Issue:

#### 🎯 Contexto & Motivação
Atualmente o fator sazonal $\gamma$ é um parâmetro manual estático ajustado arbitrariamente. No mundo real, Salvador possui uma dinâmica turística fortemente pautada pelos 12 meses do ano (altíssima estação no verão e nos cruzeiros vs. baixa estação acentuada na quadra chuvosa de outono/inverno).

Além disso, sendo o Pelourinho um centro histórico com calçamento secular de pedra em declive acentuado, dias de chuva moderada ou tempestade geram evacuação imediata do público para coberturas e arrefecimento do fluxo em até 80%.

#### 📐 Especificação Técnica de Referência
- Consulte o documento completo em: [`docs/propostas_melhorias/RFC-003_modelo_sazonalidade_e_fatores_climaticos.md`](file:///docs/propostas_melhorias/RFC-003_modelo_sazonalidade_e_fatores_climaticos.md)

#### 📋 Tarefas Técnicas de Implementação
- [ ] **Configuração e Calibração**:
  - [ ] Inserir tabela de pesos mensais de Salvador $M(1 \dots 12)$ no `backend/shared/config_simulacao.yaml` (Janeiro = 1.65 até Maio = 0.70).
  - [ ] Adicionar parâmetros climáticos e categorias (`SOL_LIMPO`, `CHUVA_FRACA`, `CHUVA_MODERADA`, `TEMPESTADE`).
- [ ] **Cálculo da Sazonalidade Composta no Backend**:
  - [ ] Implementar cálculo de $\gamma_{\text{efetivo}} = \gamma_{\text{base}} \cdot M(\text{mês}) \cdot D(\text{dia}) \cdot \omega_{\text{clima}}$.
  - [ ] Expor os novos parâmetros nos schemas Pydantic e nas funções de entrada do macro-fluxo.
- [ ] **Controles e Feedback no Dashboard Streamlit (`simulacao/`)**:
  - [ ] Adicionar seletor dropdown de "Mês do Ano" (com tags de Alta, Baixa ou Média Temporada).
  - [ ] Adicionar seletor de "Clima Atual" (com ícones de sol, chuva e temporal).
  - [ ] Exibir card informativo com o $\gamma_{\text{efetivo}}$ resultante em tempo real.
- [ ] **Testes Automatizados (`backend/tests/test_macro_flow.py`)**:
  - [ ] Validar que uma simulação em Maio sob Chuva Forte produz volume cerca de $4\times$ menor que Janeiro com Sol.
  - [ ] Testar retrocompatibilidade: sem parâmetros, o sistema opera com $\gamma = 1.0$.

#### 🏁 Critérios de Aceitação (DoD)
- Todas as rotas de simulação aceitam mês e condição climática sem quebrar contratos de API anteriores.
- 100% dos testes da suíte de simulação verdes.
