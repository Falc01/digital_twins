# 🌅 Melhoria Doc 01-A: Entrada — Picos Modulares e Presets por Dia da Semana

**Atribuição:** Desenvolvedor A (Parte 1: Dinâmica Circadiana de Entrada)  
**Arquivo Principal de Código:** [`backend/src/simulation/macro_flow.py`](file:///backend/src/simulation/macro_flow.py)  
**Arquivo de Testes:** [`backend/tests/test_macro_flow.py`](file:///backend/tests/test_macro_flow.py)  
**Referência Canônica:** [`docs/explanation/dados_sinteticos/01_modulo_de_entrada.md`](file:///docs/explanation/dados_sinteticos/01_modulo_de_entrada.md)  
**Status:** Especificação Pronta para Implementação  

---

## 📌 1. Visão Geral do Escopo

Este documento isola a responsabilidade de calcular o **influxo diário de pessoas** que entram no Pelourinho pelos portões externos (`Elevador Lacerda`, `Praça da Sé`, `Ladeira do Carmo`).

O desenvolvedor responsável implementará duas evoluções:
1. **Picos 100% Modulares ($M$ picos):** O motor aceita qualquer quantidade $M \ge 1$ de ondas com $(\tau, \sigma, w)$ configuráveis na chamada da simulação;
2. **Presets por Dia da Semana:** Perfis calibrados para Dias Úteis (Seg–Sex), Sábado e Domingo.

---

## 🧮 2. Formulação Matemática

### 2.1. Lotação Basal do Bairro $N_{\text{bairro}}(t)$
$$N_{\text{bairro}}(t) = \left[ N_{\min} + \sum_{m=1}^{M} A_m \cdot \exp\left( -\frac{(h(t) - \tau_m)^2}{2\sigma_m^2} \right) \right]$$

Onde:
* $h(t) = t \pmod{24}$: Hora contínua do dia em horas fracionárias ($[0, 24)$);
* $N_{\min}$: Piso basal da madrugada;
* $N_{\max}$: Capacidade de pico de referência;
* $M$: Quantidade arbitrária de picos informada na chamada ($M=1, 2, 3, 5\dots$);
* $\tau_m$: Horário do cume da onda (ex: $12.5 = 12\text{h}30$);
* $\sigma_m$: Largura da onda em horas;
* $A_m = w_m \cdot (N_{\max} - N_{\min})$: Amplitude modulada pelo peso $w_m \in [0.0, 1.0]$.
  > **Calibração:** O gestor pode definir $w_m = 1.0$ caso queira que o pico toque exatamente o topo de $N_{\max}$.

---

### 2.2. Presets Nativos por Dia da Semana (`day_of_week`)

O desenvolvedor deve disponibilizar os seguintes dicionários padrão no código:

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
* **Pico 1 (Missa do Rosário / São Francisco):** $\tau_1 = 10.0\text{h}$, $\sigma_1 = 1.2\text{h}$, peso $w_1 = 0.70$;
* **Pico 2 (Pôr do Sol na Sé e Mirantes):** $\tau_2 = 16.0\text{h}$, $\sigma_2 = 1.5\text{h}$, peso $w_2 = 0.85$;
* Queda suave após as 19h30 até atingir o piso residual.

---

### 2.3. Influxo Diferencial por Portão Urbano ($\Phi_{\text{in}, g}$)
O Módulo 01 exporta para os portões externos de borda ($g \in \text{GATEs}$):

$$\Delta N_{\text{bairro}}(t, \Delta t) = \max\left(0.0, \; N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t)\right)$$
$$\Phi_{\text{in}, g}(t) = w_g \cdot \Delta N_{\text{bairro}}(t, \Delta t)$$

Com restrição estrita: $\sum_{g \in \text{GATEs}} w_g = 1.0$.

---

## 🛠️ 3. Checklist de Implementação

- [ ] Aceitar lista arbitrária de picos `peaks: Optional[List[CircadianPeak]]` em `calculate_multimodal_bairro_population`.
- [ ] Criar enum e mapeamento `DAY_OF_WEEK_PREFILES` com os presets acima.
- [ ] Implementar a divisão proporcional por portões urbanos no cálculo vetorial.
- [ ] Escrever testes unitários em `backend/tests/test_macro_flow.py` (validar 1, 2, 3 e 5 picos; validar comportamento de Sábado vs Domingo).
