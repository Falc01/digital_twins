# 📋 Log de Retorno Técnico — Módulo 01: Macro-Fluxo Circadiano
## Análise de Integração e Ajustes Necessários para Simulação Dinâmica

**Documento Referenciado:** [`docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md)  
**Arquivo de Implementação:** [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py)  
**Destinatário:** Responsável pelo Desenvolvimento do Módulo 01  
**Status Atual:** Funcional e homologado com 20 testes unitários verdes.

---

### 📌 Contexto da Revisão
O módulo atual calcula com precisão matemática a curva contínua do sino gaussiano circadiano e distribui as frações de acesso proporcionalmente pelos portões de entrada física do Pelourinho ($w_j$). A unificação de compatibilidade realizada no backend garantiu 100% de aprovação na suíte de testes.

No entanto, durante os testes de acoplamento do barramento integrado (Docs 00, 03 e 04), identificamos dois pontos de modelagem física que precisam de ajuste para que o simulador dinâmico funcione de forma realista ao longo de 24 horas.

---

### Item 1: Conflito Conceitual entre Lotação Absoluta Instantânea vs. Taxa de Influxo Nodal

#### 📍 Onde está o problema:
No arquivo [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py#L97-L127) e na Seção 3.2 da especificação:
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
- **Causa:** O módulo calcula $N_{\text{rotina}}(t)$ como o volume **total acumulado de pessoas presentes no bairro** naquele horário (por exemplo, 300 pessoas no ápice das 16h30) e aloca essas 300 pessoas diretamente como valor instantâneo dos nós de portão.
- **Consequências:** Na simulação contínua ciclo a ciclo (a cada 5 minutos), a Cadeia de Markov (Doc 03) já conserva e redistribui as pessoas que entraram nos passos anteriores. Somar o total de 300 pessoas inteiras novamente a cada iteração faz a população do simulador acumular indefinidamente (600, 900, 1200...), estourando a capacidade dos sensores em poucos minutos e gerando leituras permanentemente saturadas e irreais.

#### ✅ Solução (Como e Efeitos):
- **Como:** O módulo deve disponibilizar também a **taxa diferencial de novos ingressos** por intervalo de tempo ($\Delta t$). Isto é feito calculando a variação positiva da curva entre o instante atual e o próximo ciclo ($\Delta N = \max(0, N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t))$) e distribuindo apenas esse acréscimo pelos portões através do vetor de pesos $w_j$. A função original de volume total permanece útil como âncora de calibração ou estado inicial.
- **Efeitos:** Os portões de entrada passam a injetar no simulador estritamente os pedestres que estão cruzando o acesso do bairro naquele instante. A circulação interna fica preservada pela Cadeia de Markov e a quantidade total de pedestres no Pelourinho passa a respeitar fielmente a curva teórica do sino, sem explosão de público.

---

### Item 2: Ausência do Intervalo de Ciclo ($\Delta t$ / `step_minutes`) na Assinatura de Cálculo

#### 📍 Onde está o problema:
Na definição das funções em [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py#L60-L70):
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
- **Causa:** A função recebe apenas o horário atual $t$, sem ter conhecimento da granularidade temporal do ciclo de simulação ($\Delta t = 5.0$ minutos, configurado no `config.yaml`).
- **Consequências:** O módulo fica impossibilitado de calcular derivadas, velocidades de fluxo ou o volume de pedestres que entraram durante a janela de tempo decorrida sem que módulos externos tenham que realizar interpolações manuais ou suposições sobre o passo.

#### ✅ Solução (Como e Efeitos):
- **Como:** Adicionar o parâmetro de duração do passo de tempo na configuração e na assinatura do método (com valor padrão de 5 minutos / frações de hora), permitindo avaliar a inclinação da curva gaussiana no intervalo decorrido.
- **Efeitos:** Permite acoplamento direto com o relógio do motor de simulação (Doc 00), fornecendo tanto o volume instantâneo quanto o fluxo incremental de passagem por minuto de forma consistente.
