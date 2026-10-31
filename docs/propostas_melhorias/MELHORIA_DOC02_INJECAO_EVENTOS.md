# 🎭 Melhoria Doc 02: Injeção de Eventos — Catálogo Cultural, Cortejos e Blindagem de Carnaval

**Atribuição:** Desenvolvedor B (Responsável pelo Módulo de Eventos)  
**Arquivo Principal de Código:** [`backend/src/simulation/events_injection.py`](file:///backend/src/simulation/events_injection.py)  
**Arquivos de Dados:** [`backend/shared/calendario_cultural.json`](file:///backend/shared/calendario_cultural.json) e [`backend/shared/agenda_eventos.json`](file:///backend/shared/agenda_eventos.json)  
**Arquivo de Testes:** [`backend/tests/test_events_injection.py`](file:///backend/tests/test_events_injection.py)  
**Referência Canônica:** [`docs/explanation/dados_sinteticos/02_injecao_eventos.md`](file:///docs/explanation/dados_sinteticos/02_injecao_eventos.md)  
**Status:** Especificação Pronta para Implementação  

---

## 📌 1. Visão Geral do Escopo do Módulo 02

O **Módulo de Injeção de Eventos** calcula o acréscimo pontual de público ($\mathbf{E}(t) \in \mathbb{R}^J$) gerado por manifestações culturais, ensaios de blocos afro, celebrações religiosas e eventos espontâneos no Pelourinho, sem depender de sensores físicos no chão.

Nesta evolução, o Módulo 02 ganha:
1. **Catálogo Cultural Autêntico e Rico:** Ampliação das bases JSON com eventos tradicionais de Salvador (Didá, Filhos de Gandhy, Gerônimo, Capoeira, Santa Bárbara e São João);
2. **Modelagem de Cortejos Itinerantes:** Suporte a eventos que se deslocam pelo espaço (ondas móveis que avançam de rua em rua com velocidade média $v \approx 2\text{ km/h}$);
3. **Blindagem contra Saturação em Megacomemorações (Carnaval):** Trava contra acúmulos numéricos infinitos e colapso de capacidade física nas ladeiras históricas.

---

## 🧮 2. Formulação Matemática

### 2.1. Equação do Pulso Estático no Nó $j$
Para atrações concentradas em um ponto fixo (ex: palco no Largo do Pelourinho):

$$E_j(t) = \sum_{m=1}^{M_j} A_{jm} \cdot \exp\left( -\frac{(t - \tau_{jm})^2}{2\sigma_{jm}^2} \right)$$

Onde:
* $t$: Horário contínuo atual de simulação em horas;
* $A_{jm}$: Magnitude de pico do evento (indivíduos);
* $\tau_{jm}$: Horário central do evento (ex: $20.0 = 20\text{h}00$);
* $\sigma_{jm}$: Duração / dispersão da atração em horas (ex: $\sigma = 1.5\text{h}$).

---

### 2.2. Modelagem de Cortejos e Procissões em Movimento (Itinerantes)
Um cortejo (procissão, afoxé, bloco de percussão) percorre uma sequência ordenada de nós $\mathcal{W} = (n_1, n_2, \dots, n_K)$.

Para cada nó $n_k$ do itinerário, o pico de público ocorre com uma defasagem temporal proporcional à distância percorrida a pé:

$$\tau_{n_k} = \tau_{\text{início}} + \sum_{i=1}^{k-1} \frac{\text{distância}(n_i, n_{i+1})}{v_{\text{marcha}}}$$

* $v_{\text{marcha}} \approx 2.0\text{ km/h}$ ($33.3\text{ metros/minuto}$): Velocidade típica de procissão/cortejo com multidão;
* Cada nó do percurso recebe um pulso Gaussiano defasado no tempo, criando visualmente uma "onda viva" que viaja pelo mapa.

---

### 2.3. Blindagem de Saturação para Eventos Atípicos — Aplicar Evento Carnaval
Em megacomemorações como o Carnaval, dezenas de milhares de pessoas acessam o Pelourinho simultaneamente. Para evitar explosões numéricas e distorções físicas, o sistema incorpora mecanismos de saturação respaldados pela literatura clássica de dinâmica de pedestres:

#### Fundamentação Científica (Provas e Literatura Canônica):
1. **John Fruin (1971) — *Pedestrian Planning and Design* (Manual do TRB / Highway Capacity Manual):**
   * Define os Níveis de Serviço (LOS A a F). No nível **LOS F (Colapso de Fluxo)**, quando a densidade ultrapassa $80\%$ a $85\%$ da capacidade crítica ($> 2.5\text{ pessoas/m}^2$), o contato físico se torna forçado, o escoamento colapsa em mais de $70\%$ e surge o efeito sanfona (*stop-and-go*), aprisionando a multidão no mesmo local.
2. **Dirk Helbing (Revista *Nature*, 2000) — *Simulating Dynamical Features of Escape Panic*:**
   * Demonstrou que em aglomerações extremas ocorre uma transição de fase (*jamming transition*): a multidão deixa de se comportar como fluxo livre e transiciona para um estado de **sólido viscoso granular**, onde o tempo de permanência local tende assintoticamente ao valor máximo ($P_{jj} \to 0.95$).
3. **Ulrich Weidmann (ETH Zürich, 1993) — *Diagrama Fundamental do Pedestre*:**
   * Estabeleceu a equação clássica de decaimento de velocidade: $v(\rho) = v_0 [1 - \exp(-\gamma(1/\rho - 1/\rho_{\max}))]$, comprovando que a velocidade de escoamento atinge patamares próximos de zero quando a densidade atinge o limiar crítico de saturação ($\rho \to \rho_{\max}$).

#### Mecanismos de Blindagem Implementados:
1. **Trava de Saturação por Nó ($N_{j, \max}$):**
   A magnitude injetada por eventos no nó $j$ não pode ultrapassar o teto físico do logradouro:
   $$A_{\text{evento}, j} \le 0.95 \cdot N_{j, \max}$$
2. **Fator de Amortecimento Coletivo:**
   Se múltiplos eventos simultâneos coincidirem no mesmo nó, o volume combinado sofre amortecimento logístico de aglomeração:
   $$E_j^{\text{calibrado}}(t) = \frac{E_j(t)}{1.0 + \frac{E_j(t)}{1.5 \cdot N_{j, \max}}}$$
   Isso garante que mesmo durante o Carnaval, nenhuma rua histórica atinja contagens fisicamente impossíveis de pessoas/m².
3. **Preset "Aplicar Evento Carnaval":**
   Ao ativar este modo na simulação, o sistema ajusta automaticamente o multiplicador sazonal ($\gamma$), limita a taxa de entrada nos portões externos (simulando a vazão de revista dos portais de segurança da PMBA) e estende o ápice de movimentação para a madrugada (até as 04h00).

---

## 📁 3. Expansão das Bases de Dados JSON

### 3.1. `backend/shared/calendario_cultural.json` (Recorrência Semanal)
O Dev B deve cadastrar os seguintes eventos semanais:
1. `terca_bencao_olodum`: Terça-feira, 20h00, Largo do Pelourinho ($A=180, \sigma=1.5\text{h}$);
2. `terca_bencao_geronimo`: Terça-feira, 19h30, Escadaria do Passo ($A=120, \sigma=1.8\text{h}$);
3. `quinta_ensaio_dida`: Quinta-feira, 16h00, Rua João de Deus ($A=90, \sigma=1.2\text{h}$);
4. `sabado_filhos_gandhy`: Sábado, 17h00, Rua Maciel / Terreiro ($A=150, \sigma=2.0\text{h}$);
5. `domingo_missa_rosario`: Domingo, 09h30, Igreja Rosário dos Pretos ($A=100, \sigma=1.0\text{h}$);
6. `roda_capoeira_diaria`: Diário (Seg a Sáb), 15h30, Terreiro de Jesus ($A=45, \sigma=0.8\text{h}$).

### 3.2. `backend/shared/agenda_eventos.json` (Eventos Pontuais do Calendário Baiano)
1. `festa_santa_barbara`: 04/Dezembro, Missa campal e caruru (Largo do Pelourinho, $A=200$);
2. `lavagem_bonfim_preliminar`: 2ª Quinta de Janeiro, Concentração Elevador Lacerda;
3. `sao_joao_pelourinho`: 23 e 24/Junho, Palcos simultâneos nos Largos Terreiro, Pelourinho e Quincas Berro d'Água;
4. `evento_carnaval`: Fevereiro, dias com múltiplos blocos tradicionais e cortejos de rua.

---

## 🛠️ 4. Tarefas de Implementação para o Dev B

- [ ] **Expansão de Dados:**
  - Atualizar os arquivos JSON com os eventos e rotas acima.
- [ ] **Lógica de Cortejo Itinerante em `events_injection.py`:**
  - Adicionar suporte a eventos do tipo `ITINERANT`, aceitando uma lista de `waypoints: List[int]` (índices de nós) e calculando a defasagem temporal de cada um.
- [ ] **Blindagem Numérica:**
  - Aplicar o amortecimento logístico coletivo para nós com eventos concorrentes.
- [ ] **Exportação de Saída Vetorial:**
  - Manter a exportação do vetor $\mathbf{E}(t) \in \mathbb{R}^J$ em NumPy `float64` com tempo de execução $< 30\ \mu\text{s}$.
- [ ] **Testes Automatizados em `backend/tests/test_events_injection.py`:**
  - Testar pulso estático vs. cortejo itinerante (verificar que nó 2 atinge o pico depois do nó 1).
  - Testar estresse com 5 eventos simultâneos garantindo que nenhum nó estoure sua capacidade máxima física.
