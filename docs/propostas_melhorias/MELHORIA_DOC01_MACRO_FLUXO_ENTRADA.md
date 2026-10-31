# 🌅 Melhoria Doc 01: Módulo de Entrada — Macro-Fluxo, Picos Modulares e Sazonalidade

**Atribuição:** Desenvolvedor A (Responsável pelo Módulo de Entrada / Macro-Fluxo)  
**Arquivo Principal de Código:** [`backend/src/simulation/macro_flow.py`](file:///backend/src/simulation/macro_flow.py)  
**Arquivo de Testes:** [`backend/tests/test_macro_flow.py`](file:///backend/tests/test_macro_flow.py)  
**Referência Canônica:** [`docs/explanation/dados_sinteticos/01_modulo_de_entrada.md`](file:///docs/explanation/dados_sinteticos/01_modulo_de_entrada.md)  
**Status:** Especificação Pronta para Implementação  

---

## 📌 1. Visão Geral do Escopo do Módulo 01

O **Módulo de Entrada** é a "torneira" do Gêmeo Digital: ele calcula quantas pessoas físicas acessam o Centro Histórico do Pelourinho ao longo das 24 horas do dia e reparte esse influxo entre os portões externos de entrada (`Elevador Lacerda`, `Praça da Sé`, `Ladeira do Carmo`).

Nesta evolução, o Módulo 01 deixa de ter uma curva com 3 picos fixos e ganha:
1. **Picos 100% Modulares ($M$ Picos):** O motor aceita qualquer quantidade de picos com horários, larguras e amplitudes customizáveis por simulação;
2. **Presets Nativos por Dia da Semana:** Perfis calibrados para Dias Úteis (Seg–Sex), Sábado e Domingo;
3. **Sazonalidade Integrada:** Modulação mensal ($M(\text{mês})$) e redutor pluviométrico para dias de chuva ($\omega_{\text{clima}}$).

---

## 🧮 2. Formulação Matemática

### 2.1. Equação Geral de Lotação do Bairro $N_{\text{bairro}}(t)$
O volume total instantâneo de pessoas estimado para o bairro é dado por:

$$N_{\text{bairro}}(t) = \gamma_{\text{efetivo}} \cdot \left[ N_{\min} + \sum_{m=1}^{M} A_m \cdot \exp\left( -\frac{(h(t) - \tau_m)^2}{2\sigma_m^2} \right) \right]$$

Onde:
* $h(t) = t \pmod{24}$: Hora circadiana do dia em horas fracionárias ($[0, 24)$);
* $N_{\min}$: Piso basal da madrugada (moradores, funcionários e segurança noturna);
* $N_{\max}$: Lotação máxima de referência do centro histórico;
* $M$: Quantidade arbitrária de picos informada na simulação ($M \ge 1$);
* $\tau_m$: Horário central do ápice da onda $m$ (ex: $12.5 = 12\text{h}30$);
* $\sigma_m$: Dispersão temporal em horas (largura da Gaussiana);
* $A_m = w_m \cdot (N_{\max} - N_{\min})$: Amplitude do pico, modulada pelo peso relativo $w_m \in [0.0, 1.0]$.
  > **Nota de Calibração:** O operador da simulação pode configurar $w_m = 1.0$ caso queira que o pico toque exatamente o teto de $N_{\max}$.

---

### 2.2. Presets Padrão por Dia da Semana (`day_of_week`)

O desenvolvedor deve disponibilizar os seguintes dicionários de calibração padrão:

#### A. Dias Úteis (Segunda a Sexta — `WEEKDAY` / dias 0 a 4)
* **Perfil:** Comércio e repartições públicas, com almoço forte e volta para casa.
* $N_{\min} = 15$, $N_{\max} = 300$;
* **Pico 1 (Almoço / Serviços):** $\tau_1 = 12.5\text{h}$, $\sigma_1 = 1.2\text{h}$, peso $w_1 = 0.65$;
* **Pico 2 (Saída do Trabalho / Comércio):** $\tau_2 = 17.2\text{h}$, $\sigma_2 = 1.8\text{h}$, peso $w_2 = 0.90$.

#### B. Sábado (`SATURDAY` / dia 5)
* **Perfil:** Comércio matinal, turismo à tarde e vida noturna prolongada nos largos.
* $N_{\min} = 25$, $N_{\max} = 420$;
* **Pico 1 (Feira e Comércio):** $\tau_1 = 10.5\text{h}$, $\sigma_1 = 1.5\text{h}$, peso $w_1 = 0.50$;
* **Pico 2 (Passeio Turístico da Tarde):** $\tau_2 = 16.0\text{h}$, $\sigma_2 = 1.8\text{h}$, peso $w_2 = 0.75$;
* **Pico 3 (Noite Cultural / Bares):** $\tau_3 = 21.5\text{h}$, $\sigma_3 = 2.2\text{h}$, peso $w_3 = 0.95$.

#### C. Domingo (`SUNDAY` / dia 6)
* **Perfil:** Missas históricas pela manhã, passeios de contemplação à tarde e encerramento cedo.
* $N_{\min} = 10$, $N_{\max} = 320$;
* **Pico 1 (Missa Cantada do Rosário / São Francisco):** $\tau_1 = 10.0\text{h}$, $\sigma_1 = 1.2\text{h}$, peso $w_1 = 0.70$;
* **Pico 2 (Pôr do Sol na Sé e Mirantes):** $\tau_2 = 16.0\text{h}$, $\sigma_2 = 1.5\text{h}$, peso $w_2 = 0.85$;
* Queda suave após as 19h30 até atingir o piso residual.

---

### 2.3. Sazonalidade Anual & Fator Climático
O multiplicador $\gamma_{\text{efetivo}}$ deixa de ser apenas um número estático e passa a calcular:

$$\gamma_{\text{efetivo}} = \gamma_{\text{base}} \cdot M(\text{mês}) \cdot \omega_{\text{clima}}$$

1. **Curva Mensal de Salvador $M(\text{mês})$:**
   * Janeiro ($1.65$), Fevereiro ($1.85$), Março ($1.20$);
   * Abril ($0.80$), Maio ($0.70$ — mês mais chuvoso), Junho ($1.15$ — São João), Julho ($0.85$);
   * Agosto ($0.95$), Setembro ($1.00$), Outubro ($1.10$), Novembro ($1.25$), Dezembro ($1.50$).
2. **Atenuação Climática $\omega_{\text{clima}}$:**
   * `SOL_LIMPO` ou `NUBLADO`: $\omega = 1.00$
   * `CHUVA_FRACA`: $\omega = 0.80$
   * `CHUVA_MODERADA`: $\omega = 0.50$
   * `TEMPESTADE`: $\omega = 0.20$ (queda de 80% do tráfego a céu aberto)

---

### 2.4. Influxo Diferencial por Portão Urbano ($\Phi_{\text{in}, g}$)
O Módulo 01 exporta para os portões externos de borda ($g \in \text{GATEs}$):

$$\Delta N_{\text{bairro}}(t, \Delta t) = \max\left(0.0, \; N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t)\right)$$
$$\Phi_{\text{in}, g}(t) = w_g \cdot \Delta N_{\text{bairro}}(t, \Delta t)$$

Com $\sum_{g \in \text{GATEs}} w_g = 1.0$.

---

## 🛠️ 3. Tarefas de Implementação para o Dev A

- [ ] **Contratos e Schemas:**
  - Suportar lista de picos `peaks: Optional[List[CircadianPeak]]` em `calculate_multimodal_bairro_population`.
  - Criar dataclass/enum para `DayType` (`WEEKDAY`, `SATURDAY`, `SUNDAY`).
- [ ] **Implementação em `macro_flow.py`:**
  - Implementar resolução automática de picos: se `peaks` for omitido, seleciona o preset correspondente ao `day_of_week`.
  - Implementar cálculo de $\gamma_{\text{efetivo}}$ combinando mês e categoria climática.
  - Garantir complexidade analítica $O(M)$ onde $M < 10$ ($< 25\ \mu\text{s}$).
- [ ] **Testes Automatizados em `backend/tests/test_macro_flow.py`:**
  - Validar simulação com 1 pico (unimodal), 2 picos, 3 picos e 5 picos.
  - Validar que Sábado mantém fluxo alto após as 21h enquanto Domingo decai.
  - Validar que Maio sob Tempestade reduz o fluxo proporcionalmente em relação a Janeiro com Sol.
