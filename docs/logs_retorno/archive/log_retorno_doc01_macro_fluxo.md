# 📋 Log de Retorno Técnico — Módulo 01: Macro-Fluxo Circadiano
## Análise de Integração e Ajustes Necessários para Simulação Dinâmica

**Documento Referenciado:** [`docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md)  
**Arquivo de Implementação:** [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py)  
**Destinatário:** Responsável pelo Desenvolvimento do Módulo 01  
**Status Atual:** ✅ **[RESOLVIDO] Homologado e 100% Validado (23/23 testes unitários verdes no backend)**  
**Data da Resolução:** 30/09/2026  

---

### 📌 Contexto da Revisão
O módulo atual calcula com precisão matemática a curva contínua do sino gaussiano circadiano e distribui as frações de acesso proporcionalmente pelos portões de entrada física do Pelourinho ($w_j$). A unificação de compatibilidade realizada no backend garantiu 100% de aprovação na suíte de testes.

No entanto, durante os testes de acoplamento do barramento integrado (Docs 00, 03 e 04), identificamos dois pontos de modelagem física que precisavam de ajuste para que o simulador dinâmico funcionasse de forma realista ao longo de 24 horas.

---

### Item 1: Conflito Conceitual entre Lotação Absoluta Instantânea vs. Taxa de Influxo Nodal

#### 📍 Onde estava o problema:
No arquivo [`backend/src/simulation/macro_flow.py`](file:///c:/Users/Daniel%20Costa/Documents/Antigravity/Digital%20Twins/backend/src/simulation/macro_flow.py#L97-L127) e na Seção 3.2 da especificação:
```python
# Trecho em macro_flow.py:
N_bairro = gamma_seasonality * (N_min + (N_max - N_min) * gaussian_term)

# E na distribuição pelos portões:
allocated_volume = gate.gate_weight * total_bairro_volume
```
E na fórmula de integração nodal prevista no Doc 00 e Doc 04:
```python
N_bruto(t + 1) = N_propagado(t + 1) + N_rotina(t) + E(t)
```

#### ⚠️ Problema (Causa - Consequências):
- **Causa:** O módulo calculava $N_{\text{rotina}}(t)$ apenas como o volume **total acumulado de pessoas presentes no bairro** naquele horário (por exemplo, 300 pessoas no ápice das 16h30) e alocava essas 300 pessoas diretamente como valor instantâneo dos nós de portão.
- **Consequências:** Na simulação contínua ciclo a ciclo (a cada 5 minutos), a Cadeia de Markov (Doc 03) já conserva e redistribui as pessoas que entraram nos passos anteriores. Somar o total de 300 pessoas inteiras novamente a cada iteração fazia a população do simulador acumular indefinidamente (600, 900, 1200...), estourando a capacidade dos sensores em poucos minutos e gerando leituras permanentemente saturadas e irreais.

#### ✅ Solução Implementada:
1. **Estrutura Híbrida `BairroPopulation(tuple)`:**
   Criada a classe matemática `BairroPopulation` que herda de `tuple` com 2 elementos `(N_bairro, circadian_hour)`, preservando 100% de retrocompatibilidade com desempacotamentos legados `vol, h = calculate_bairro_population(...)`, ao mesmo tempo em que disponibiliza as propriedades `.delta_N`, `.rate_per_minute`, `.step_minutes` e `.slope`.
2. **Cálculo da Taxa Diferencial de Ingressos ($\Delta N$):**
   Implementada a avaliação analítica no próximo ciclo $t + \Delta t$:
   $$\Delta N(t, \Delta t) = \max(0.0, N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t))$$
   $$\text{rate\_per\_minute} = \frac{\Delta N}{\Delta t}$$
3. **Distribuição Proporcional pelos Portões:**
   Criada a função `distribute_influx_to_gates(delta_N, w_weights)` e integrados os vetores `delta_N_rotina` / `vector_delta_N_rotina` em `MacroFlowResult` e `MacroFlowResponse`. Cada `SensorAllocation` agora reporta tanto `count_pedestrians` (lotação estática) quanto `incremental_pedestrians` / `delta_pedestrians` (fluxo dinâmico de novos ingressos).
4. **Flag `use_incremental`:**
   Adicionado o parâmetro `use_incremental: bool = False` em `calculate_macro_flow` e no payload `MacroFlowRequest`. Quando ativado, `N_rotina` reflete diretamente os novos ingressos incrementais $\Delta \mathbf{N}_{\text{rotina}}(t)$, acoplando-se perfeitamente à equação $\mathbf{N}_{\text{bruto}}(t + 1) = \mathbf{N}_{\text{propagado}}(t + 1) + \Delta \mathbf{N}_{\text{rotina}}(t) + \mathbf{E}(t)$ sem explosão de público.

---

### Item 2: Ausência do Intervalo de Ciclo ($\Delta t$ / `step_minutes`) na Assinatura de Cálculo

#### 📍 Onde estava o problema:
Na definição das funções em [`backend/src/simulation/macro_flow.py`](file:///c:/Users/Daniel%20Costa/Documents/Antigravity/Digital%20Twins/backend/src/simulation/macro_flow.py#L60-L70):
```python
def calculate_bairro_population(
    current_time_hours: float,
    N_max: int = 300,
    N_min: int = 15,
    t_peak: float = 16.5,
    sigma: float = 3.0,
    gamma_seasonality: float = 1.0,
) -> Tuple[float, float]:
```

#### ⚠️ Problema (Causa - Consequências):
- **Causa:** A função recebia apenas o horário atual $t$, sem ter conhecimento da granularidade temporal do ciclo de simulação ($\Delta t = 5.0$ minutos, configurado no `config_simulacao.yaml`).
- **Consequências:** O módulo ficava impossibilitado de calcular derivadas, velocidades de fluxo ou o volume de pedestres que entraram durante a janela de tempo decorrida sem que módulos externos tivessem que realizar interpolações manuais ou suposições sobre o passo.

#### ✅ Solução Implementada:
1. **Inclusão de `step_minutes: float = 5.0`:**
   - Adicionado no modelo `MacroFlowConfig` (`step_minutes: float = 5.0` e helper `step_hours`).
   - Adicionado na assinatura de `calculate_bairro_population(..., step_minutes: float = 5.0)`.
   - Adicionado em `calculate_bairro_volume`, `calculate_bairro_influx`, `MacroFlowSimulator.evaluate` e `calculate_macro_flow`.
   - Adicionado no schema `MacroFlowRequest` e `MacroFlowResponse`.
   - Adicionado como query param nos endpoints GET e POST do FastAPI em `src/api/routers/simulation.py`.
   - Adicionado argumento `--dt / --step-minutes` na interface CLI (`cli_macro_flow.py`).
2. **Cálculo da Inclinação Analítica e Taxa de Passagem:**
   - Disponibilizada a derivada analítica $dN/dt = \gamma (N_{\max} - N_{\min}) \cdot \exp(\dots) \cdot \left(-\frac{h(t) - t_{\text{pico}}}{\sigma^2}\right)$ em `BairroPopulation.slope`.
   - Disponibilizada a taxa de passagem por minuto `rate_pedestrians_per_minute` tanto no bairro quanto por sensor.

---

### 🧪 Homologação e Cobertura de Testes
- A suíte de testes em `backend/tests/test_macro_flow.py` foi expandida de 20 para **23 testes unitários automatizados**.
- Novos testes adicionados:
  - `test_differential_influx_item1`: valida conservação de $\sum \Delta N_{\text{rotina}, j} == \Delta N$, comportamento positivo em horário de ascensão (14h) e convergência a zero no ápice (16h30).
  - `test_step_minutes_granularity_item2`: valida consistência física ao variar $\Delta t$ de 2.5 min para 5.0 min, comprovando invariância do volume total e proporcionalidade do incremento.
  - `test_api_differential_flow_integration`: valida o contrato REST FastAPI retornando `step_minutes`, `delta_N_bairro`, `delta_N_rotina` e comportamento do flag `use_incremental`.
- **Status do repositório:** 62/62 testes passando (100% green) em toda a suíte do backend.
