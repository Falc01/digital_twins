# 🌅 Doc 01: Macro-Fluxo Circadiano & Distribuição por Portões de Entrada ($w_j$)
## Especificação Técnica para Simulação do Volume Diário de Pedestres no Pelourinho (v2.0)

**Classificação:** Especificação Técnica de Subsistema / Modelo Matemático  
**Módulo Pertencente:** Container de API (`backend/src/api/` — Subsistema de Macro-Fluxo)  
**Documento Central de Referência:** [`00_arquitetura_ingestao_e_fluxo_dados.md`](file:///home/dancs/Documents/digital_twins/docs/explanation/dados_sinteticos/00_arquitetura_ingestao_e_fluxo_dados.md)  
**Log de Melhorias v2.0:** [`docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md`](file:///home/dancs/Documents/digital_twins/docs/logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md)  

---

## 📌 1. Visão Geral e Contextualização Urbana

O Centro Histórico do Pelourinho opera como um **sistema urbano aberto**: o público não é fixo dentro do bairro. Ao longo do dia, turistas e moradores entram pelas portas principais de acesso (Elevador Lacerda, Praça da Sé, Ladeira do Carmo) pela manhã e dispersam de volta aos hotéis e residências no período noturno.

A responsabilidade deste módulo é calcular o **volume diário basal de pedestres no Pelourinho ($N_{\text{bairro}}(t)$)** e a **taxa pura de novos ingressos ($\Delta N_{\text{bairro}}$)**, suportando o modelo clássico do Sino Gaussiano e a evolução multimodal (Mistura Trimodal e Harmônicos de Fourier), alocando essa quantidade nos nós urbanos de portão através do vetor de pesos $\mathbf{w}$.

```mermaid
flowchart TD
    subgraph Entradas["IMPORTAÇÃO (CONFORME DOC 00)"]
        CA["Canal A: Grafo Urbano e Nós de Portão\n[N_min, N_max_bairro, Vetor w_j, UrbanGateNode]"]
        CB["Canal B: config_simulacao.yaml\n[Regime: Unimodal, Trimodal ou Fourier K=3]"]
        CC["Canal C: Relógio do Servidor & UI\n[Hora t, Passo Δt, Multiplicador γ_epoca]"]
    end

    subgraph Processamento["PROCESSAMENTO MATEMÁTICO (DOC 01 v2.0)"]
        Curva["1. Avaliar Curva Circadiana N_bairro(t):\n• Modo Unimodal: Sino Gaussiano Clássico\n• Modo Trimodal: Mistura Urbana (09h30, 12h30, 16h48)\n• Modo Fourier: Decomposição Harmônica K=3"]
        Dif["2. Calcular Influxo Diferencial:\nΔN_bairro(t, Δt) = max(0, N_bairro(t + Δt) - N_bairro(t))"]
        Pond["3. Ponderar por Nó de Portão Urbano:\nΦ_in,g(t) = w_g × ΔN_bairro(t, Δt)\nN_rotina,g(t) = w_g × N_bairro(t)"]
    end

    subgraph Saida["EXPORTAÇÃO (CANAL D)"]
        VetorOut["Ground Truth de Portões Urbanos:\nN_rotina(t) e ΔN_rotina(t) ∈ ℝ^J (em indivíduos)"]
    end

    CA & CB & CC --> Curva
    Curva --> Dif
    Dif --> Pond
    Pond --> VetorOut
```

---

## 📋 2. Requisitos do Subsistema

### 2.1. Requisitos Funcionais (RFs)
* **RF01 — Curvas Circadianas Configuráveis:** O módulo deve computar a lotação global do Pelourinho $N_{\text{bairro}}(t)$ suportando o Sino Gaussiano unimodal clássico ($t_{\text{pico}} \approx 16\text{h}30$, $\sigma \approx 3\text{h}$), a Mistura Trimodal Urbana (picos às 09h30, 12h30 e 16h48) e Séries Harmônicas de Fourier ($K=3$);
* **RF02 — Distribuição por Portões Urbanos ($w_g$):** O módulo deve alocar o fluxo entre os nós de portão de entrada física através do vetor de pesos $\mathbf{w} \in \mathbb{R}^J$, onde cada elemento $w_g \in [0, 1]$ representa a fatia do público que acessa o bairro por aquele portão;
* **RF03 — Conservação Estrita de Fluxo:** A soma de todos os pesos de portão deve ser estritamente unitária ($\sum_{g \in \text{GATEs}} w_g = 1.0$). Atratores internos sem entrada física externa (`node_largo_pelourinho`, `node_terreiro_jesus`) possuem peso estrito $w = 0.0$;
* **RF04 — Modulação Sazonal ($\gamma$):** O módulo deve multiplicar a curva pelo fator sazonal $\gamma$ (ex: $\gamma = 1.0$ dias úteis; $\gamma = 1.5$ alta estação; $\gamma = 3.5$ Carnaval);
* **RF05 — Relógio Circadiano Contínuo:** O módulo deve calcular a hora circadiana através do operador módulo $h(t) = t \pmod{24}$, garantindo simulação ininterrupta 24 horas por dia;
* **RF06 — Influxo Diferencial de Borda ($\Delta N$):** Computar a variação positiva de ingressos no intervalo $[t, t + \Delta t]$ isolando novos pedestres para alimentar a cadeia de Markov (Doc 03) sem gerar duplicação de contagem.

### 2.2. Requisitos Não-Funcionais (RNFs)
* **RNF01 — Complexidade Temporal $O(1)$:** A avaliação analítica da função executa em tempo constante ($< 30\ \mu\text{s}$) por ciclo;
* **RNF02 — Exportação Direta em Indivíduos:** A função deve retornar diretamente a **quantidade de pessoas físicas calculadas** para cada portão (em unidades de indivíduos);
* **RNF03 — Desacoplamento Topológico Limpo:** As entidades espaciais operam como `UrbanGateNode`, dissociando o chão da cidade dos sensores eletrônicos de telemetria IoT (delegados ao Doc 04).

---

## 🧮 3. Formulação Matemática

### 3.1. Regime Clássico: Sino Gaussiano Unimodal
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ N_{\min} + (N_{\max, \text{bairro}} - N_{\min}) \cdot \exp\left( -\frac{(h(t) - t_{\text{pico}})^2}{2\sigma^2} \right) \right]$$

### 3.2. Regime Trimodal Urbano (Padrão Salvador — v2.0)
Três fluxos parciais somados modelando o ritmo comercial, gastronômico e turístico:
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ N_{\min} + \sum_{m=1}^{3} A_m \cdot \exp\left( -\frac{(h(t) - \tau_m)^2}{2\sigma_m^2} \right) \right]$$

Onde:
1. **Pico 1 — Missas Matinais e Comércio:** $\tau_1 = 09.5$ (09h30), $\sigma_1 = 1.8\text{ h}$, $A_1 = 0.35 \times (N_{\max} - N_{\min})$;
2. **Pico 2 — Almoço Histórico:** $\tau_2 = 12.5$ (12h30), $\sigma_2 = 1.2\text{ h}$, $A_2 = 0.55 \times (N_{\max} - N_{\min})$;
3. **Pico 3 — Ápice Turístico / Pôr do Sol:** $\tau_3 = 16.8$ (16h48), $\sigma_3 = 2.2\text{ h}$, $A_3 = 0.90 \times (N_{\max} - N_{\min})$.

### 3.3. Regime Espectral de Fourier ($K=3$)
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ \beta_0 + \sum_{k=1}^{3} \left( a_k \cos\left(\frac{2\pi k h(t)}{24}\right) + b_k \sin\left(\frac{2\pi k h(t)}{24}\right) \right) \right]$$

### 3.4. Taxa de Influxo Nodal ($\Delta N_{\text{in}}$)
$$\Delta N_{\text{bairro}}(t, \Delta t) = \max\left(0.0, \; N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t)\right)$$
$$\Phi_{\text{in}, g}(t) = w_g \cdot \Delta N_{\text{bairro}}(t, \Delta t)$$

Onde:
* $h(t) = t \pmod{24}$ é a hora do dia no relógio circadiano ($h \in [0, 24)$);
* $N_{\min}$ é a população flutuante residual da madrugada ($03\text{h}00$);
* $N_{\max, \text{bairro}}$ é a capacidade máxima total acumulada no centro histórico;
* $t_{\text{pico}}$ é o horário central de ápice de visitação (ex: $16.5 = 16\text{h}30$);
* $\sigma$ é a largura temporal da janela turística (ex: $\sigma = 3.0\text{ h}$);
* $\gamma$ é o multiplicador sazonal ($\gamma = 1.0$ dias normais; $\gamma > 1.0$ eventos/verão).

---

### 3.2. Ponderação Espacial por Portão de Entrada ($w_j$)
A quantidade de pessoas da rotina diária no sensor $j$ no instante $t$ é:

$$N_{j, \text{rotina}}(t) = w_j \cdot N_{\text{bairro}}(t)$$

Em notação vetorial para os $J$ nós da rede:
$$\mathbf{N}_{\text{rotina}}(t) = \mathbf{w} \cdot N_{\text{bairro}}(t) = \begin{bmatrix} w_1 \\ w_2 \\ \vdots \\ w_J \end{bmatrix} \cdot \gamma \cdot \left[ N_{\min} + (N_{\max, \text{bairro}} - N_{\min}) \cdot \exp\left( -\frac{(h(t) - t_{\text{pico}})^2}{2\sigma^2} \right) \right]$$

Com a restrição física de conservação:
$$\sum_{j=1}^J w_j = 1.0$$

---

## 📖 4. Dicionário de Variáveis e Tipagem do Módulo

| Símbolo (Opção A) | Símbolo (Opção B) | Tipo Primitivo | Unidade | Descrição / Valor Típico | Canal de Origem |
| :---: | :---: | :---: | :---: | :--- | :---: |
| $t$ | $t$ | `float64` | horas | Tempo acumulado contínuo ($t \ge 0$). | Canal C |
| $h(t)$ | $t_{\text{hora}}$ | `float64` | horas | Hora do dia ($h \in [0, 24)$). | Canal C |
| $N_{\max, \text{bairro}}$ | $N_{\text{max\_bairro}}$ | `int` | indivíduos | Lotação máxima global do Pelourinho ($300$). | Canal A |
| $N_{\min}$ | $N_{\text{min\_bairro}}$ | `int` | indivíduos | Piso basal da madrugada ($15$). | Canal A |
| $t_{\text{pico}}$ | $t_{\text{pico}}$ | `float64` | horas | Horário central do pico ($16.5 = 16\text{h}30$). | Canal B |
| $\sigma$ | $t_{\text{duracao}}$ | `float64` | horas | Espalhamento do pico ($3.0\text{ h}$). | Canal B |
| $\gamma$ | $\gamma_{\text{epoca}}$ | `float64` | adimensional | Multiplicador de época ($1.0$ a $3.5$). | Canal C |
| $\mathbf{w}$ | $\mathbf{w}_{\text{portoes}}$ | `ndarray (J,)` | frações | Vetor de pesos dos portões ($\sum w_j = 1$). | Canal A |
| $\mathbf{N}_{\text{rotina}}(t)$ | $\mathbf{N}_{\text{rotina}}(t)$ | `ndarray (J,)` | **indivíduos** | **Vetor de saída com a contagem de pessoas**. | Canal D (Saída) |

---

## 📥 5. Formato de Importação (Entradas da Função)

O desenvolvedor deve estruturar a classe/função deste módulo para receber as seguintes entradas conforme o [Doc 00](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/explanation/dados_sinteticos/00_arquitetura_ingestao_e_fluxo_dados.md):

### 5.1. Parâmetros de Configuração e Metadados
* **`w_weights` (`np.ndarray` float64 de tamanho $J$):** Lidos da coluna `gate_weight` da tabela de sensores no GeoPackage.  
  * *Exemplo para 4 nós:* `w_weights = np.array([0.45, 0.35, 0.20, 0.00])`  
  *(Sensor 1: Elevador Lacerda 45%; Sensor 2: Praça da Sé 35%; Sensor 3: Ladeira do Carmo 20%; Sensor 4: Largo interno 0%)*.
* **`N_max` (`int`):** Capacidade global do bairro (ex: `300`).
* **`N_min` (`int`):** Piso basal do bairro (ex: `15`).
* **`t_peak` (`float`):** `16.5`.
* **`sigma` (`float`):** `3.0`.

### 5.2. Parâmetros Dinâmicos de Execução (Por Ciclo)
* **`current_time_hours` (`float`):** Timestamp atual $t$ convertido em horas fracionárias (ex: `16.5` para 16h30).
* **`gamma_seasonality` (`float`):** Fator sazonal (ex: `1.0` ou `1.5`).

---

## 📤 6. Formato de Exportação (Saída para o Canal D)

A função deve exportar um array NumPy 1D contendo a **contagem exata de pessoas da rotina geradas para cada nó**:

```python
# Especificação do Retorno da Função:
# N_rotina -> np.ndarray de shape (J,), dtype=np.float64
# Exemplo de saída às 16h30 (Ápice turístico com N_bairro = 300 pessoas no total):
# N_rotina = np.array([135.0, 105.0, 60.0, 0.0])
```

Este vetor é transmitido diretamente em memória RAM para o **Doc 04**, onde será somado à circulação de Markov (Doc 03) e aos eventos pontuais (Doc 02).
