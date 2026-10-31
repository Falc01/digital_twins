# 🔄 Melhoria Doc 03: Circulação de Rede & Saída — Tipagem Urbana de POIs e Egress Dinâmico

**Atribuição:** Desenvolvedor C (Responsável pelo Módulo de Circulação, Markov e Saída)  
**Arquivo Principal de Código:** [`backend/src/simulation/markov_circulation.py`](file:///backend/src/simulation/markov_circulation.py)  
**Arquivo de Testes:** [`backend/tests/test_markov_circulation.py`](file:///backend/tests/test_markov_circulation.py)  
**Referência Canônica:** [`docs/explanation/dados_sinteticos/03_circulacao_markov_pois.md`](file:///docs/explanation/dados_sinteticos/03_circulacao_markov_pois.md)  
**Status:** Especificação Pronta para Implementação  

---

## 📌 1. Visão Geral do Escopo do Módulo 03

O **Módulo de Circulação e Saída** governa como os pedestres se movem dentro do labirinto de ruas do Pelourinho através de uma **Cadeia de Markov Espacial** calibrada pelo Modelo Gravitacional. Além disso, ele é o responsável exclusivo por computar a **saída definitiva das pessoas da cidade ($Egress$)** através dos nós de portão de borda.

Nesta evolução, o Módulo 03 ganha:
1. **Tipagem Semântica Urbana:** Nós classificados formalmente como `GATE`, `COMERCIO`, `RELIGIOSO` e `CULTURAL`;
2. **Atratividade Gravitacional Dinâmica por Dia da Semana ($\alpha_j(t, \text{dia})$):** As igrejas atraem no domingo de manhã, o comércio atrai nos dias úteis, e os bares/largos atraem no sábado à noite;
3. **Mecanismo de Retenção sob Multidão ("Creep Flow"):** Em ruas muito cheias, a velocidade de caminhada cai e a inércia local ($P_{jj}$) aumenta;
4. **Vetor Rigoroso de Evasão ($Egress$):** Cálculo das pessoas que deixam o Pelourinho pelos portões externos.

---

## 🧮 2. Formulação Matemática

### 2.1. Matriz de Transição Estocástica de Markov ($P_{ij}$)
A probabilidade de um pedestre localizado no nó $i$ transitar para o nó vizinho $j$ no intervalo $\Delta t$ é dada por:

$$P_{ij}(t) = \frac{A_j(t) \cdot e^{-\lambda_d \cdot d_{ij}} \cdot \mathbb{I}(\text{adjacente}(i, j))}{\sum_{k} A_k(t) \cdot e^{-\lambda_d \cdot d_{ik}} \cdot \mathbb{I}(\text{adjacente}(i, k)) + E_i(t)}$$

Onde:
* $d_{ij}$: Distância geográfica em metros entre os nós $i$ e $j$;
* $\lambda_d$: Taxa de decaimento por distância ($\approx 0.015\text{ m}^{-1}$);
* $\mathbb{I}(\text{adjacente}(i, j))$: Matriz topológica binária de ruas conectadas (impede "teletransporte" entre nós que não possuem rua direta);
* $A_j(t) = \alpha_j(t, \text{dia})$: Força atrativa do nó de destino $j$.

---

### 2.2. Tabela de Atratividade Gravitacional $\alpha_j(t, \text{dia})$

O desenvolvedor deve implementar a modulação horária e semanal de $\alpha_j$:

| Tipo de Nó | Dias Úteis (Seg - Sex) | Sábado | Domingo |
| :--- | :--- | :--- | :--- |
| **`COMERCIO`** | $\alpha = 2.0$ entre 10h e 17h; $\alpha = 0.5$ à noite | $\alpha = 2.2$ entre 09h e 14h; $\alpha = 0.2$ à noite | $\alpha = 0.1$ o dia todo (comércio fechado) |
| **`RELIGIOSO`** | $\alpha = 1.0$ (turismo sacro regular) | $\alpha = 1.2$ de dia | **$\alpha = 3.5$ entre 09h e 12h** (missas históricas) |
| **`CULTURAL`** | $\alpha = 1.5$ de dia; $\alpha = 0.8$ após 20h | $\alpha = 2.0$ à tarde; **$\alpha = 3.0$ entre 20h e 23h** | $\alpha = 2.0$ no pôr do sol; cai após 19h30 |
| **`GATE` (Portões)** | Atrai forte a partir das 18h (saída) | Retenção interna alta; portões atraem após 22h30 | Portões começam a atrair saída cedo (19h) |

---

### 2.3. Mecanismo de Saturação e Inércia Local ("Creep Flow")
Quando um nó histórico atinge alta densidade populacional ($N_j > 0.85 N_{j, \max}$), a multidão compactada reduz a vazão das ruas estreitas. Esse limiar está fundamentado na literatura clássica de física de pedestres:
* **John Fruin (1971, *Pedestrian Planning and Design*):** Limiar do Nível de Serviço F (*LOS F — Breakdown*), onde densidades acima de $80\% - 85\%$ do espaço crítico provocam colapso de escoamento e transição para movimento em ondas de choque (*stop-and-go*).
* **Dirk Helbing (*Nature*, 2000):** Transição de fase para estado viscoso granular (*jamming transition*), onde a probabilidade de transição para nós vizinhos cai e a inércia local converge para $P_{jj} \to 0.95$.
* **Ulrich Weidmann (1993):** Curva exponencial de decrescimento de velocidade no Diagrama Fundamental do Pedestre conforme $\rho \to \rho_{\max}$.

A probabilidade de permanecer no mesmo nó (diagonal $P_{jj}$) é formalmente amplificada:

$$P_{jj}^{\text{efetivo}}(t) = P_{jj}^{\text{base}} + (1.0 - P_{jj}^{\text{base}}) \cdot \left[ \frac{1}{1 + \exp\left( -\kappa \cdot (N_j(t) - 0.85 N_{j, \max}) \right)} \right]$$

Com $\kappa \approx 0.08$. Isso impede que o modelo transfira magicamente centenas de pessoas para ruas vizinhas que já estão congestionadas.

---

### 2.4. Cálculo do Vetor de Saída da Cidade ($Egress$)
Apenas os nós classificados como `GATE` possuem probabilidade de evasão física do centro histórico:

Para cada nó de portão $g \in \text{GATEs}$:
$$N_{\text{egress}, g}(t) = N_g(t) \cdot P_{g, \text{egress}}(t)$$

Com a invariante estocástica estrita: todas as linhas da matriz de transição (incluindo a coluna de saída) devem somar **rigorosamente 100%**:
$$\sum_{j=1}^J P_{ij}(t) + P_{i, \text{egress}}(t) = 1.0 \quad (\forall i)$$

---

## 🛠️ 3. Tarefas de Implementação para o Dev C

- [ ] **Configuração e Schemas:**
  - Garantir que cada nó urbano em `MarkovCirculationConfig` possua o campo `poi_type` preenchido (`GATE`, `COMERCIO`, `RELIGIOSO`, `CULTURAL`).
- [ ] **Implementação em `markov_circulation.py`:**
  - Implementar a função `get_poi_attraction(poi_type, hour, day_of_week) -> float` conforme a tabela de calibração.
  - Implementar a trava de inércia por saturação na diagonal $P_{jj}$ ("creep flow").
  - Garantir que a saída vetorial retorne o estado propagado $N_{\text{propagado}}$ e o vetor de evasão $N_{\text{egress}}$ por portão.
- [ ] **Testes Automatizados em `backend/tests/test_markov_circulation.py`:**
  - Testar normalização estocástica: soma das probabilidades de todas as linhas deve ser $1.0000 \pm 10^{-6}$.
  - Testar que aos domingos de manhã o nó religioso atrai $> 3\times$ mais pedestres que o nó comercial.
  - Testar que aos sábados à noite a probabilidade de saída ($Egress$) é menor que às quintas-feiras no mesmo horário.
