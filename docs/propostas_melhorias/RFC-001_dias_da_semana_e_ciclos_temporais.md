# 📅 RFC-001: Modelagem de Dias da Semana, Perfis Circadianos Diferenciados e Simulação Multidiária

**Status:** Proposta Técnica (Backlog / Para Implementação)  
**Módulo Pertencente:** Doc 01 (`backend/src/simulation/macro_flow.py`) e Motor de Rollout (`backend/src/simulation/rollout.py`)  
**Contexto Institucional:** UNIFACS — Iniciação Científica (IC) — Gêmeo Digital IoT Pelourinho  
**Data:** Outubro de 2026  

---

## 📌 1. Motivação e Diagnóstico do Estado Atual

### 1.1. Diagnóstico do Código Atual
Na versão atual do código (`macro_flow.py` v2.0):
* A curva circadiana de influxo $N_{\text{bairro}}(t)$ calcula a hora do dia via módulo simples:
  $$h(t) = t \pmod{24}$$
* O conjunto de picos trimodais padrão (`DEFAULT_TRIMODAL_PEAKS`: 09h30, 12h30, 16h48) é fixo e aplicado **indistintamente** para qualquer dia.
* No motor de rollout (`rollout.py`), a execução ocorre em um horizonte fechado de 24 horas de um dia genérico.
* **Problema:** Uma terça-feira de expediente comercial tem uma dinâmica urbana completamente diferente de um sábado à noite ou de um domingo pela manhã no Pelourinho.

---

## 🏛️ 2. Fundamentação Urbana no Pelourinho

O Centro Histórico de Salvador apresenta três regimes semanais bem demarcados:

1. **Dias Úteis (Segunda a Sexta):**
   * **Fluxo Operacional e Administrativo:** Abertura dos serviços públicos e comércio matinal (08h00 - 09h00), forte concentração no horário de almoço na Praça da Sé e Terreiro (12h00 - 13h30), e pico de retorno/comércio vespertino (17h00 - 18h30).
   * **Noite Típica:** Movimentação moderada após 20h00, exceto às terças-feiras (Terça da Bênção / Olodum).

2. **Sábado (Ritmo Híbrido & Notívago):**
   * **Manhã Comercial:** Comércio intenso e feirantes na transição da Baixa dos Sapateiros para o Pelourinho (10h00 - 12h00).
   * **Tarde Turística Plena:** Grande afluência de visitantes regionais e interestaduais (14h00 - 18h00).
   * **Noite Cultural Estendida:** Bares, restaurantes e palcos dos largos (Largo do Pelourinho, Quincas Berro d'Água, Pedro Archanjo) mantêm o ápice populacional até as **22h30 - 23h30**, com queda suave na madrugada.

3. **Domingo (Turismo Contemplativo & Religioso):**
   * **Manhã Sacra:** Missas com atabaques na Igreja de Nossa Senhora do Rosário dos Pretos e celebrações na Igreja de São Francisco (09h00 - 11h30).
   * **Almoço e Tarde Turística:** Ápice familiar no pôr do sol da Praça da Sé e Mirante da Misericórdia (15h30 - 18h00).
   * **Encerramento Precoce:** Desaceleração rápida após as 19h30; às 21h00 as ruas já se encontram com fluxo próximo ao piso basal $N_{\min}$.

---

## 🧮 3. Especificação Matemática

### 3.1. Classificação do Tipo de Dia
Seja $d \in \{0, 1, 2, 3, 4, 5, 6\}$ o dia da semana no padrão ISO (0 = Segunda-feira, 6 = Domingo):

$$\text{TipoDia}(d) = \begin{cases} 
\text{WEEKDAY} & \text{se } d \in \{0, 1, 2, 3, 4\} \\
\text{SATURDAY} & \text{se } d = 5 \\
\text{SUNDAY} & \text{se } d = 6 
\end{cases}$$

### 3.2. Picos Circadianos por Tipo de Dia

Para o regime Trimodal ($m \in \{1, 2, 3\}$):
$$N_{\text{bairro}}(t, d) = \gamma \cdot \left[ N_{\min}(d) + \sum_{m=1}^{3} A_m(d) \cdot \exp\left( -\frac{(h(t) - \tau_m(d))^2}{2\sigma_m(d)^2} \right) \right]$$

#### Calibração Sugerida de Parâmetros:

| Parâmetro | Dias Úteis (Seg - Sex) | Sábado | Domingo |
| :--- | :--- | :--- | :--- |
| **Piso Basal ($N_{\min}$)** | $15$ pessoas | $25$ pessoas | $10$ pessoas |
| **Capacidade Pico ($N_{\max}$)** | $300$ pessoas | $420$ pessoas | $320$ pessoas |
| **Pico 1 ($\tau_1, \sigma_1, w_1$)** | $08.5\text{h}$, $\sigma=1.5\text{h}$, $w=0.40$ (Entrada trabalho/serviços) | $10.5\text{h}$, $\sigma=1.8\text{h}$, $w=0.50$ (Comércio e passeios) | $10.0\text{h}$, $\sigma=1.2\text{h}$, $w=0.60$ (Missas e visitas sacras) |
| **Pico 2 ($\tau_2, \sigma_2, w_2$)** | $12.5\text{h}$, $\sigma=1.0\text{h}$, $w=0.60$ (Almoço executivo/popular) | $15.5\text{h}$, $\sigma=1.8\text{h}$, $w=0.75$ (Passeios da tarde) | $15.8\text{h}$, $\sigma=1.8\text{h}$, $w=0.85$ (Pôr do sol / atrativos) |
| **Pico 3 ($\tau_3, \sigma_3, w_3$)** | $17.5\text{h}$, $\sigma=1.5\text{h}$, $w=0.70$ (Saída de expediente / happy hour) | $21.5\text{h}$, $\sigma=2.2\text{h}$, $w=0.95$ (Vida noturna e música) | $18.5\text{h}$, $\sigma=1.2\text{h}$, $w=0.40$ (Encerramento antecipado) |

### 3.3. Ciclo Intra-Mensal (Efeito Calendário Comercial / Quinzena)
O poder de compra e visitação urbana no comércio local sofre um incremento cíclico associado aos dias de pagamento de salários (1º ao 5º dia útil do mês e dia 20 para adiantamentos):

$$\phi_{\text{mes}}(dia\_do\_mes) = \begin{cases}
1.15 & \text{se } dia\_do\_mes \in [1, 7] \quad (\text{Primeiro quinto útil}) \\
1.08 & \text{se } dia\_do\_mes \in [18, 22] \quad (\text{Adiantamento quinzenal}) \\
0.95 & \text{caso contrário} \quad (\text{Dias regulares})
\end{cases}$$

O volume global modulado torna-se:
$$N_{\text{final}}(t, d, dia\_do\_mes) = N_{\text{bairro}}(t, d) \cdot \phi_{\text{mes}}(dia\_do\_mes)$$

---

## 🛠️ 4. Impactos Arquiteturais e Requisitos Técnicos

### 4.1. Alterações no `MacroFlowSimulator` (`macro_flow.py`)
1. Adicionar parâmetro opcional `day_of_week: int = 0` (0..6) em `calculate_macro_flow` e `calculate_multimodal_bairro_population`.
2. Criar dicionário de calibração `DAY_OF_WEEK_PROFILES` mapeando os perfis acima.
3. Se `day_of_week` não for informado, utilizar a data do sistema operacional via `datetime.now().weekday()`.

### 4.2. Suporte à Simulação Multidiária (`rollout.py`)
1. Implementar método `run_multi_day_batch(days=7, start_weekday=0, step_minutes=30.0)`:
   * Mantém o vetor de ocupação residual dos nós de 23h59 para 00h00 do dia seguinte.
   * Alterna dinamicamente a curva circadiana base conforme o dia da semana avança.
2. Adicionar no `RolloutStep` o metadado `day_index` e `weekday_name` ("Segunda", "Terça", etc.).

### 4.3. Atualização no Dashboard Web (`simulacao/app.py` e `sidebar.py`)
1. Adicionar seletor de dia da semana na barra lateral:
   * Opções: `["Segunda a Sexta (Útil)", "Sábado", "Domingo", "Semana Completa (7 Dias Contínuos)"]`.
2. No gráfico da linha do tempo, permitir visualização com divisores verticais de transição de dias.

---

## ✅ 5. Critérios de Aceitação (DoD)
- [ ] Testes unitários validando que Sábado possui ápice noturno após as 21h enquanto Domingo decai após as 19h.
- [ ] Continuidade estrita de conservação de fluxo na transição entre dias consecutivos no rollout de 7 dias (sem saltos de descontinuidade populacional em $t = 24.0$).
- [ ] Cobertura de testes $\ge 90\%$ nas novas funções de perfil semanal.
