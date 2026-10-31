# 🎭 RFC-002: Enriquecimento Cultural de Eventos & Blindagem para Eventos Atípicos (Carnaval / Circuito Batatinha)

**Status:** Proposta Técnica (Backlog / Para Implementação)  
**Módulo Pertencente:** Doc 02 (`backend/src/simulation/events_injection.py`), Doc 03 (`backend/src/simulation/markov_circulation.py`) e Rollout (`backend/src/simulation/rollout.py`)  
**Contexto Institucional:** UNIFACS — Iniciação Científica (IC) — Gêmeo Digital IoT Pelourinho  
**Data:** Outubro de 2026  

---

## 📌 1. Motivação e Diagnóstico do Estado Atual

### 1.1. Diagnóstico do Código Atual
Na implementação atual:
1. **Catálogo Esquelético:** O arquivo `calendario_cultural.json` possui apenas 2 eventos semanais (Terça do Olodum e Missa do Rosário) e `agenda_eventos.json` apenas 2 eventos pontuais. Salvador possui uma das agendas culturais e sincréticas mais densas do mundo.
2. **Eventos Estáticos:** O modelo atual assume eventos pontuais parados em um único sensor $j$. Não suporta **cortejos e procissões em movimento** (ex: Afoxé Filhos de Gandhy ou ensaios itinerantes do Olodum descendo as ladeiras).
3. **Limitação Crítica no Rollout (`rollout.py` linha 219):**
   ```python
   new_state_base = np.maximum(0.0, n_propagated + delta_inflow)
   total_occupancy_N = np.maximum(0.0, new_state_base + events_vec)
   ```
   *Problema:* O vetor $E(t)$ é somado apenas na exibição de ocupação! Os indivíduos do evento **não são inseridos no estado circulante** da rede. No passo seguinte, quando o pulso gaussiano cessa, as pessoas simplesmente evaporam, em vez de se dispersarem pelo grafo de ruas e saírem pelos portões via Cadeias de Markov.
4. **Vulnerabilidade a Eventos Atípicos (Carnaval):** No Carnaval (Circuito Batatinha), o centro histórico recebe centenas de milhares de pessoas. Se um multiplicador $\gamma = 3.5$ ou eventos massivos forem acionados, o modelo atual não simula os efeitos de **hiper-saturação física (efeito funil / creep flow)**, nem a **reconfiguração de segurança dos portões de entrada**.

---

## 🏛️ 2. Fundamentação Urbana: A Dinâmica Cultural de Salvador

### 2.1. Catálogo Rico de Manifestações Tradicionais
* **Terça da Bênção & Ensaios Afro (Semanal):** Olodum no Largo do Pelourinho, Didá na Rua João de Deus, Gerônimo na Escadaria do Passo.
* **Rodas de Capoeira e Manifestações de Rua (Diário/Espontâneo):** Terreiro de Jesus e Praça da Sé (manhã e tarde).
* **Festas Litúrgicas e Populares de Salvador (Calendário Anual):**
  * *Festa de Santa Bárbara (04/Dez):* Missa campal no Largo do Pelourinho, distribuição de caruru e cortejo até o Corpo de Bombeiros na Baixa dos Sapateiros.
  * *Lavagem do Bonfim (2ª Quinta-feira de Jan):* Influxo massivo partindo do Elevador Lacerda / Comércio.
  * *Festa de Iemanjá (02/Fev):* Concentração cultural preliminar no Pelourinho com descida para o mar.
  * *São João do Pelourinho (Junho):* Palcos múltiplos simultâneos em todos os largos (Terreiro, Pelourinho, Quincas Berro d'Água, Pedro Archanjo).

### 2.2. A Singularidade do Carnaval (Circuito Batatinha)
O Circuito Batatinha (Pelourinho) é dedicado ao samba, blocos tradicionais, afoxés e fanfarras infantis:
* As ladeiras históricas estreitas funcionam como **gargalos hidrodinâmicos**.
* A Polícia Militar da Bahia (PMBA) instala **Portais de Abordagem e Segurança** nos portões externos (Elevador Lacerda, Terreiro de Jesus/Praça da Sé, Ladeira do Carmo/Taboão), alterando o balanceamento de entrada e saída.

---

## 🧮 3. Modelagem Matemática Avançada

### 3.1. Correção Fundamental de Acoplamento no Rollout (Injeção Real de Estado)
Os indivíduos atraídos por um evento cultural não desaparecem no ar quando o show termina. A injeção $E(t)$ deve alimentar o estado ativo do nó:

$$N_j(t + \Delta t) = N_{j, \text{propagado}}(t) + \Phi_{\text{in}, j}(t) + \Delta E_j(t)$$

Onde $\Delta E_j(t) = \max(0.0, E_j(t + \Delta t) - E_j(t))$ representa o influxo diferencial do evento. Uma vez no nó, essas pessoas entram na matriz estocástica $P_{jk}$ de circulação e eventualmente evacuam pelos portões de borda ($Egress$).

---

### 3.2. Modelagem de Eventos em Cortejo / Itinerantes
Um cortejo (procissão, afoxé, bloco de percussão) percorre uma sequência ordenada de nós espaciais $\mathcal{K} = (k_1, k_2, \dots, k_r)$ com velocidades médias de deslocamento urbano $v \approx 1.5 - 2.5\text{ km/h}$.

Para um nó $j = k_i$ na rota do cortejo, o horário de pico é defasado pelo tempo de marcha:
$$\tau_j = \tau_{\text{inicio}} + \sum_{m=1}^{i-1} \frac{\text{distância}(k_m, k_{m+1})}{v_{\text{marcha}}}$$

O pulso de público no sensor $j$ é:
$$E_j^{\text{cortejo}}(t) = A_{\text{bloco}} \cdot \exp\left( -\frac{(t - \tau_j)^2}{2\sigma_{\text{bloco}}^2} \right)$$

Isso produz uma "onda viajante" de pedestres realista que percorre as ruas do mapa.

---

### 3.3. Blindagem Matemática para Eventos Atípicos (Regime de Carnaval)

#### A. Mecanismo de Saturação e Colapso de Velocidade ("Creep Flow")
Quando a densidade local $\rho_j = \frac{N_j}{\text{Área}_j}$ ultrapassa a densidade de conforto $\rho_c \approx 1.5\text{ pessoas/m}^2$, a retenção na rua aumenta drasticamente e a velocidade de evacuação colapsa (efeito de multidão compactada).

Modulamos a probabilidade de retenção na diagonal da matriz de Markov ($P_{jj}$) e o decaimento da taxa de saída:

$$P_{jj}^{\text{carnaval}}(t) = P_{jj}^{\text{base}} + (1.0 - P_{jj}^{\text{base}}) \cdot \left[ \frac{1}{1 + \exp\left( -\kappa \cdot (N_j(t) - 0.85 N_{j, \max}) \right)} \right]$$

* **Interpretação:** Quando o nó atinge 85% da capacidade física, a multidão fica imprensada, elevando a inércia local $P_{jj} \to 0.95$ e impedindo que milhares de pessoas sejam deslocadas instantaneamente para ruas vizinhas já congestionadas.

#### B. Reconfiguração de Topologia de Portões (Portais PMBA)
Em regime de evento atípico (`regime == "carnaval"`):
* O vetor de pesos de entrada $\mathbf{w}$ é reconfigurado para refletir a triagem dos portais de segurança da PMBA:
  * Elevador Lacerda (Portal 1): $w = 0.50$ (controle de catracas e revista lenta);
  * Terreiro / Praça da Sé (Portal 2): $w = 0.40$;
  * Ladeira do Carmo (Portal 3): $w = 0.10$ (restrito a moradores e serviços).
* Inclusão de trava de segurança rígida:
  $$\sum_{j} N_j(t) \le N_{\text{bairro, colapso}} = 4.5 \cdot N_{\text{max, basal}}$$

---

## 🛠️ 4. Especificação Técnica de Implementação

### 4.1. Expansão dos Arquivos JSON de Dados
1. **`backend/shared/calendario_cultural.json`**:
   * Adicionar regras semanais: Terça do Olodum, Terça da Benção, Quinta da Didá, Sábado de Ensaio dos Filhos de Gandhy, Domingo da Missa do Rosário e Roda de Capoeira do Terreiro.
2. **`backend/shared/agenda_eventos.json`**:
   * Cadastrar os macro-eventos da cidade: Festa de Santa Bárbara, Ensaio Geral de Verão, São João do Pelô e os 6 dias de Carnaval.

### 4.2. Refatoração do `EventsInjectionSimulator`
* Suporte a eventos do tipo `ITINERANT` com lista de `waypoints` (passagem temporal ordenada por nós).
* Flag de configuração `atypical_event_shielding: bool = True` para ativar a trava de contenção de fluxo durante megacomemorações.

### 4.3. Correção no `RolloutSimulationEngine`
* Integrar os ingressos de eventos de forma aditiva contínua no vetor dinâmico de estado que alimenta a matriz de transição do passo seguinte.

---

## ✅ 5. Critérios de Aceitação (DoD)
- [ ] População de eventos dissipa-se gradualmente através da rede de Markov e sai pelos portões mesmo após o encerramento da apresentação (eliminação de "pedestres fantasmas" que desapareciam abruptamente).
- [ ] Teste de estresse com $\gamma = 4.0$ (Carnaval) não causa estouro de memória, valores NaN, nem violação de probabilidade na matriz estocástica.
- [ ] Implementação de ao menos 1 cortejo itinerante funcional cruzando 3 nós consecutivos.
