# 📄 Relatório Técnico: Resolução do Log 01 (v2.0)
## Desacoplamento Urbano, Multimodalidade Circadiana & Balanço Estrito de Portaria

**Data:** 23 de Outubro de 2026  
**Contexto:** Gêmeo Digital IoT do Centro Histórico do Pelourinho — UNIFACS  
**Documento Referenciado:** [`docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md`](file:///home/dancs/Documents/digital_twins/docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md)  
**Especificação Técnica:** [`docs/explanation/dados_sinteticos/01_modulo_de_entrada.md`](file:///home/dancs/Documents/digital_twins/docs/explanation/dados_sinteticos/01_modulo_de_entrada.md)  
**Módulos Alterados:** `backend/src/simulation/macro_flow.py`, `backend/src/simulation/schemas.py`, `backend/src/simulation/__init__.py`, `backend/src/api/routers/simulation.py`, `backend/src/simulation/cli_macro_flow.py`, `backend/tests/test_macro_flow.py`  
**Status Final:** ✅ Homologado com 27/27 testes unitários do Módulo 01 e 95/95 testes aprovados em toda a suíte do backend (100% green).

---

## 🎯 1. Sumário Executivo

Durante a sabatina de orientação dos dados sintéticos do Gêmeo Digital, foram apresentados três questionamentos metodológicos essenciais:
1. **Artificialidade do Pico Único Simétrico:** O Centro Histórico de Salvador não opera com uma curva gaussiana unimodal simétrica com único ápice às 16h30. O dia real conta com abertura comercial matinal (~09h30), forte pico de gastronomia e almoço (~12h30), vale de calor/digestão pós-almoço (~14h00), ápice turístico e cultural no pôr do sol (~16h48) e dispersão noturna gradual.
2. **Mistura Conceitual de Camadas (Topologia Urbana vs. Hardware IoT):** Os portões de entrada física da cidade estavam tipados como dispositivos de hardware (`SensorGateWeight` / `sensor_elevador_lacerda`), acoplando precocemente o espaço geográfico à eletrônica de sensoriamento.
3. **Balanço Estrito de Novos Ingressos ($\Phi_{\text{in}}$) e Exclusão de POIs Internos:** As praças centrais (Terreiro de Jesus, Largo do Pelourinho) não geram público espontâneo vindo do exterior; todo influxo inicial surge pelos portões de borda ($w_g$) e só atinge os POIs via transição de Markov (Doc 03).

Este documento relata as soluções físico-matemáticas implementadas, a arquitetura de desacoplamento, os testes adicionados e a garantia de 100% de retrocompatibilidade com a API legada.

---

## 🔍 2. O Porquê: Diagnóstico dos Problemas

### 2.1. O Problema da Curva Unimodal Simétrica
Na versão 1.0, a lotação era gerada por:
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ N_{\min} + (N_{\max} - N_{\min}) \cdot \exp\left( -\frac{(h(t) - 16.5)^2}{2 \times 3.0^2} \right) \right]$$

Essa modelagem impunha simetria estrita:
- Às 12h00 ($t=12.0$), a distância ao pico (16.5) é de 4.5 horas.
- Às 14h00 ($t=14.0$), a distância ao pico (16.5) é de 2.5 horas.
- Consequentemente, na v1.0 o volume às 14h00 era **maior** do que às 12h00, o que contrariava a dinâmica empírica do Pelourinho, onde o horário de almoço atrai massas aos restaurantes e o início da tarde sofre desaceleração térmica.

### 2.2. Acoplamento de Hardware IoT no Nível Macro
No Doc 01 v1.0, o modelo manipulava `SensorGateWeight` com prefixos `sensor_*`. Contudo, portões de acesso (Elevador Lacerda, Praça da Sé, Ladeira do Carmo) são **nós de fronteira urbana**, independentes de haver uma câmera YOLO, um sensor de barreira infravermelho ou um radar IoT instalado. Parâmetros instrumentais (saturação de Richards, ruído de Ornstein-Uhlenbeck) pertencem estritamente ao Doc 04.

---

## 🛠️ 3. O Que Foi Feito: Implementação Técnica

### 3.1. Entidade Urbana Neutra: `UrbanGateNode`
Criada a abstração topológica em [`backend/src/simulation/schemas.py`](file:///home/dancs/Documents/digital_twins/backend/src/simulation/schemas.py):

```python
class UrbanGateNode(BaseModel):
    node_id: str = Field(default="", description="Identificador único do nó urbano no grafo")
    sensor_id: str = Field(default="", description="Alias transparente para telemetria IoT")
    nome_local: str = Field(..., description="Nome amigável do portão de entrada")
    gate_weight: float = Field(..., ge=0.0, le=1.0, description="Fração w_g de fluxo")
    max_capacity: Optional[int] = Field(None, ge=0)
    min_baseline: Optional[int] = Field(None, ge=0)
    poi_type: Optional[str] = Field("GATE")
```

**Regras de Projeto:**
- `SensorGateWeight` herda diretamente de `UrbanGateNode`, preservando retrocompatibilidade total;
- Portões padrão atualizados para:
  * `node_elevador_lacerda` ($w_1 = 0.45$);
  * `node_praca_da_se` ($w_2 = 0.35$);
  * `node_ladeira_do_carmo` ($w_3 = 0.20$);
  * `node_largo_pelourinho` (POI interno — peso estrito $w = 0.00$).
- `MacroFlowConfig` aceita tanto `gates` quanto `urban_gates`.
- `MacroFlowResponse` reporta tanto `node_ids` quanto `sensor_ids`.

---

### 3.2. Formulação Matemática Multimodal

Criada a rotina analítica em tempo constante $O(1)$:
```python
def calculate_multimodal_bairro_population(...)
```

#### Regime A: Mistura Trimodal Urbana (Calibrada para Salvador)
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ N_{\min} + \sum_{m=1}^{3} A_m \cdot \exp\left( -\frac{(h(t) - \tau_m)^2}{2\sigma_m^2} \right) \right]$$

Com a parametrização oficial:
1. **Pico Matinal (Abertura Comercial / Missas):** $\tau_1 = 9.5$ (09h30), $\sigma_1 = 1.8\text{ h}$, $A_1 = 0.35 \times (N_{\max} - N_{\min})$;
2. **Pico Gastronômico (Almoço Histórico):** $\tau_2 = 12.5$ (12h30), $\sigma_2 = 1.2\text{ h}$, $A_2 = 0.55 \times (N_{\max} - N_{\min})$;
3. **Pico Turístico e Cultural (Ápice / Pôr do Sol):** $\tau_3 = 16.8$ (16h48), $\sigma_3 = 2.2\text{ h}$, $A_3 = 0.90 \times (N_{\max} - N_{\min})$.

#### Regime B: Decomposição Harmônica de Fourier ($K=3$)
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ \beta_0 + \sum_{k=1}^{3} \left( a_k \cos\left(\frac{2\pi k h(t)}{24}\right) + b_k \sin\left(\frac{2\pi k h(t)}{24}\right) \right) \right]$$

Calculando analiticamente a derivada $dN/dt$ (slope) e a taxa diferencial de novos ingressos $\Delta N = \max(0.0, N(t + \Delta t) - N(t))$.

---

### 3.3. Demonstrativo Numérico Comparativo (Regime Trimodal)

Com $N_{\min} = 15$, $N_{\max} = 300$, $\gamma = 1.0$:

| Horário | Contexto Urbano | Volume Calculado ($N_{\text{bairro}}$) | Influxo Diferencial ($\Delta N / 5\text{min}$) |
| :---: | :--- | :---: | :---: |
| **03:00** | Madrugada Deserta | $15.2$ pessoas | $0.00$ |
| **09:30** | Missas e Abertura do Comércio | $123.0$ pessoas | $1.15$ |
| **12:30** | Pico de Almoço (Terreiro / S. Francisco) | **$234.6$ pessoas** | $0.64$ |
| **14:00** | Vale de Digestão / Calor Baiano | **$205.3$ pessoas** | $0.00$ |
| **16:48** | Ápice Turístico / Pôr do Sol | **$271.8$ pessoas** | $0.00$ |
| **20:00** | Dispersão Noturna | $104.1$ pessoas | $0.00$ |

> [!NOTE]
> **Validação da Sabatina:** O volume às **12h30 ($234.6$)** supera claramente o volume às **14h00 ($205.3$)**, reproduzindo perfeitamente o comportamento urbano real cobrado pela orientação acadêmica.

---

## 🧪 4. Validação por Testes Automatizados

Foram adicionados 4 novos testes unitários formais em [`backend/tests/test_macro_flow.py`](file:///home/dancs/Documents/digital_twins/backend/tests/test_macro_flow.py):

1. **`test_multimodal_trimodal_mixture_item2`**:
   - Valida que $N(12.5) > N(14.0)$ e que o pico global ocorre no final da tarde ($16.8\text{h}$);
   - Valida conservação estrita de fluxo: $\sum_{g} \Phi_{\text{in}, g} = \Delta N_{\text{bairro}}$.
2. **`test_multimodal_fourier_regime_b`**:
   - Valida a periodicidade estrita de 24 horas: $N(t) = N(t + 24)$;
   - Valida suavidade e não-negatividade de $\Delta N$.
3. **`test_urban_gate_node_desacoplamento_item1`**:
   - Valida o desacoplamento de entidades urbanas e aliases transparentes `node_id` / `sensor_id`;
   - Valida a regra estrita de peso $0.0$ para atratores internos (`node_largo_pelourinho`).
4. **`test_multimodal_simulator_and_24h_curve_v2` & `test_api_multimodal_integration`**:
   - Valida a geração de série temporal de 24h multimodal (96 pontos a cada 15 min);
   - Valida serialização nos endpoints FastAPI (`/api/v1/simulation/macro-flow/calculate`) com suporte ao parâmetro `regime="trimodal"`.

### Resultado da Suíte de Testes:
```
============================== 27 passed in 3.19s ==============================
============================== 95 passed in 40.82s (Suíte Global) ==============
100% DE SUCESSO E HOMOLOGAÇÃO
```

---

## 📂 5. Rastreabilidade dos Arquivos Modificados

- [`backend/src/simulation/schemas.py`](file:///home/dancs/Documents/digital_twins/backend/src/simulation/schemas.py): Criação de `UrbanGateNode`, harmonização de aliases `node_id`/`sensor_id`, suporte a `regime`, `peaks` e `urban_gates`.
- [`backend/src/simulation/macro_flow.py`](file:///home/dancs/Documents/digital_twins/backend/src/simulation/macro_flow.py): Implementação de `CircadianPeak`, `DEFAULT_TRIMODAL_PEAKS`, `calculate_multimodal_bairro_population()`, `calculate_multimodal_bairro_volume()`, `calculate_multimodal_bairro_influx()`, e atualização de `MacroFlowSimulator` e `calculate_macro_flow()`.
- [`backend/src/simulation/__init__.py`](file:///home/dancs/Documents/digital_twins/backend/src/simulation/__init__.py): Exportação pública dos novos símbolos do Módulo 01 v2.0.
- [`backend/src/api/routers/simulation.py`](file:///home/dancs/Documents/digital_twins/backend/src/api/routers/simulation.py): Suporte ao parâmetro `regime` nos endpoints de macro-fluxo.
- [`backend/src/simulation/cli_macro_flow.py`](file:///home/dancs/Documents/digital_twins/backend/src/simulation/cli_macro_flow.py): Suporte à flag `--regime {unimodal,trimodal,fourier}` e visualização de curvas multimodais no terminal.
- [`backend/tests/test_macro_flow.py`](file:///home/dancs/Documents/digital_twins/backend/tests/test_macro_flow.py): Inclusão dos testes automatizados da v2.0.
- [`docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md`](file:///home/dancs/Documents/digital_twins/docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md): Atualização de status para homologado com checklist completo.
