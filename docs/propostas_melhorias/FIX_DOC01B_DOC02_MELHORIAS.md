# 🔧 Fix Spec — Ajustes Pós-Revisão (Doc 01-B e Doc 02)

**Referências:**
- [`docs/propostas_melhorias/MELHORIA_DOC01B_SAZONALIDADE_E_CLIMA.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/propostas_melhorias/MELHORIA_DOC01B_SAZONALIDADE_E_CLIMA.md)
- [`docs/propostas_melhorias/MELHORIA_DOC02_INJECAO_EVENTOS.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/propostas_melhorias/MELHORIA_DOC02_INJECAO_EVENTOS.md)
- **Commits de referência no GitHub (`origin/main`):** `84702a64`, `158e1f48`
- **Status:** Pendente de Correção (Apenas Especificação — Sem Alteração de Código)

---

## 📌 Objetivo

Registrar objetivamente **o que deve ser ajustado** nos módulos **Doc 01-B** e **Doc 02** para alinhar a implementação do `origin/main` às especificações originais de melhoria.

---

## 1. Fix Doc 01-B — Sazonalidade, Clima e Override de $\gamma$

**Arquivos envolvidos:**
- [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py)
- [`backend/shared/config_simulacao.yaml`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/shared/config_simulacao.yaml)
- [`backend/tests/test_macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/tests/test_macro_flow.py)

### ❌ Desvio Atual
As seções `seasonality` e `weather` foram adicionadas em `config_simulacao.yaml`, porém `SEASON_FACTORS` e `WEATHER_FACTORS` em `macro_flow.py` estão **hardcoded**. Editar o YAML não altera o comportamento do motor.

### ✅ O que deve mudar
1. **Leitura dinâmica do YAML em `macro_flow.py`:**
   - Criar helper (ex.: `load_season_weather_factors(config_path=...)`) que leia `simulation.macro_flow.seasonality` e `simulation.macro_flow.weather` de `backend/shared/config_simulacao.yaml`.
   - Manter os dicionários atuais (`SEASON_FACTORS`, `WEATHER_FACTORS`) apenas como **fallback** caso o arquivo YAML não exista ou alguma chave esteja ausente, preservando aliases em português (`VERAO`, `CHUVA_FRACA`, etc.).
2. **Integração em `calculate_gamma_seasonality`:**
   - Consultar os fatores carregados do YAML (com cache ou recarga explícita), garantindo que alterações nos pesos do `config_simulacao.yaml` reflitam diretamente no $\gamma_{\text{efetivo}}$.
3. **Teste unitário em `test_macro_flow.py`:**
   - Adicionar teste usando arquivo YAML temporário (ou override de caminho) comprovando que alterar um peso em `seasonality` ou `weather` no YAML muda o resultado de `calculate_gamma_seasonality`.

---

## 2. Fix Doc 02 — Injeção de Eventos, Cortejos e Blindagem de Carnaval

**Arquivos envolvidos:**
- [`backend/src/simulation/events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/events_injection.py)
- [`backend/shared/agenda_eventos.json`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/shared/agenda_eventos.json)
- [`backend/tests/test_events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/tests/test_events_injection.py)

### 2.1. Completar o Preset `"Aplicar Evento Carnaval"` (`apply_carnaval_preset`)
* **Desvio Atual:** Ativar `apply_carnaval_preset=True` em `EventsInjectionConfig` apenas reduz `damping_factor` de `1.5` para `1.2`.
* **O que deve mudar:**
  1. Definir um contrato explícito de parâmetros para o modo Carnaval (ex.: helper ou bloco de preset acoplável ao rollout/macro-fluxo) que:
     - Ajuste automaticamente o multiplicador sazonal $\gamma$ para regime de megacomemoração (conforme Seção 2.3 do Doc 02);
     - Aplique **teto/limitador de vazão de entrada nos portões externos** (simulando os portais de revista da PMBA);
     - Estenda a janela/ápice de movimentação de eventos e fluxo para a **madrugada (até as 04h00)**.
  2. Garantir que `apply_carnaval_preset=True` continue mantendo o amortecimento coletivo ativo e exportando metadados claros no resultado para consumo pelo motor de rollout/dashboard.

### 2.2. Completar [`backend/shared/agenda_eventos.json`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/shared/agenda_eventos.json)
* **Desvio Atual:** Os eventos foram simplificados em relação à Seção 3.2 do Doc 02 (`festa_santa_barbara` com magnitude `80.0`, `sao_joao_pelourinho` em apenas 1 nó e `evento_carnaval` como evento `STATIC` único).
* **O que deve mudar:**
  1. **`festa_santa_barbara`:** Atualizar `magnitude` para `200.0` (conforme spec $A = 200$).
  2. **`sao_joao_pelourinho`:** Expandir para **palcos simultâneos** nos Largos **Terreiro de Jesus**, **Largo do Pelourinho** e **Quincas Berro d'Água** (múltiplas entradas ou registros por palco no mesmo dia/horário).
  3. **`evento_carnaval`:** Cadastrar pelo menos um bloco/cortejo usando `event_type: "ITINERANT"` com sequência ordenada de `waypoints` pelos nós do Pelourinho (além de eventuais palcos estáticos).

### 2.3. Usar Distâncias Reais do Grafo em `calculate_itinerant_pulses`
* **Desvio Atual:** `calculate_itinerant_pulses` em `events_injection.py` soma `distance_per_step_m = 100.0` fixo entre quaisquer waypoints consecutivos.
* **O que deve mudar:**
  1. Adicionar parâmetro opcional `distance_matrix: Optional[np.ndarray] = None` (ou `node_coords`) em `calculate_itinerant_pulses` e `EventsInjectionSimulator.evaluate`.
  2. Quando `distance_matrix` for fornecida, calcular $\tau_{n_k} = \tau_{\text{início}} + \sum_{i=1}^{k-1} \frac{d(n_i, n_{i+1})}{v_{\text{marcha}}}$ usando `distance_matrix[waypoints[k-1], waypoints[k]]`.
  3. Manter `distance_per_step_m=100.0` apenas como **fallback** quando nenhuma matriz de distâncias for passada (preservando retrocompatibilidade com chamadas/testes existentes).
  4. Adicionar teste em `test_events_injection.py` validando que distâncias diferentes entre pares de waypoints produzem defasagens temporais proporcionais à distância real.
