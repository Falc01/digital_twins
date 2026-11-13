# 🔬 Suíte de Verificação Formal em Lean 4 — Gêmeo Digital IoT do Pelourinho

**Instituição:** UNIFACS — Iniciação Científica (IC)  
**Pesquisador:** João Spinola Falcão  
**Domínio:** Verificação Mecanizada de Invariantes em Mobilidade Urbana e Simulação Estocástica de Pedestres  
**Ferramentas:** Lean 4 (`v4.35.0`), Lake Build System, Property-Based Testing com `Hypothesis`

---

## 📌 1. Visão Geral e Motivação Acadêmica

Para publicação em periódicos e conferências internacionais de cidades inteligentes (Smart Cities / Urban Digital Twins), a formulação matemática do framework sintético de pedestres do Pelourinho (Docs 01 a 05) é submetida à **verificação formal assistida por computador**.

Utilizando o provador de teoremas **Lean 4**, demonstramos mecanicamente que o modelo não contém falhas algébricas estruturais, garantindo:
1. **Conservação Estocástica Rigorosa:** A probabilidade de redistribuição de pedestres mais a evasão nos portões soma exatamente $100\%$ em todas as iterações ($\sum_j P_{ij} + P_{i, \text{egress}} = 1$);
2. **Blindagem contra Densidades Infinitas:** O amortecimento coletivo logístico de eventos (Fruin / Helbing / Weidmann) garante que a atração em megacomemorações (Carnaval) é estritamente limitada superiormente por $D \cdot N_{j, \max}$;
3. **Balanço Físico de Massa:** A quantidade total de pessoas no bairro após propagação matricial somada aos que saíram é estritamente igual à lotação inicial ($N_{\text{prop}} + N_{\text{egress}} = N_{\text{inicial}}$).

---

## 🗂️ 2. Estrutura dos Módulos

```text
formal_proofs/
├── lakefile.lean                      # Configuração do Lake
├── lean-toolchain                     # Versão oficial estável do Lean 4
├── README.md                          # Este documento científico
├── PelourinhoProofs.lean              # Ponto de entrada da biblioteca
└── PelourinhoProofs/
    ├── Basic.lean                     # Agregação dos teoremas
    ├── MacroFlow.lean                 # Doc 01: Não-negatividade basal e partição de portões
    ├── EventDamping.lean              # Doc 02: Limitação estrita do amortecimento logístico
    └── MarkovCirculation.lean         # Doc 03: Invariante de Markov, Creep Flow e Egress
```

---

## 🧮 3. Teoremas Formalizados

### 3.1. Doc 01: Macro-Fluxo Circadiano (`MacroFlow.lean`)
* `bairro_population_bounded_below`: $\forall t, N_{\text{bairro}}(t) \ge N_{\min} \ge 0$;
* `gate_influx_partition_conserved`: $\sum_{g} w_g \Delta N = \Delta N$ sob $\sum w_g = 1$;
* `effective_gamma_strictly_positive`: $\gamma_{\text{efetivo}} > 0$ se $\gamma_{\text{manual}}, \gamma_{\text{estação}}, \omega_{\text{clima}} > 0$.

### 3.2. Doc 02: Blindagem de Eventos e Carnaval (`EventDamping.lean`)
* `damping_zero`: $E = 0 \implies E_{\text{calibrado}} = 0$;
* `damping_nonneg`: $\forall E \ge 0, E_{\text{calibrado}} \ge 0$;
* `damping_upper_bound`: $\forall E \ge 0, E_{\text{calibrado}} < D \cdot N_{j, \max}$ (provando que mesmo com $E \to \infty$ a superlotação física é impossível).

### 3.3. Doc 03: Circulação Markoviana e Saídas (`MarkovCirculation.lean`)
* `row_stochastic_with_egress`: $\forall i, \sum_j P_{ij} + P_{i, \text{egress}} = 1$;
* `transition_prob_nonneg`: $\forall i, j, P_{ij} \ge 0$;
* `creep_flow_row_conservation`: preservação estrita de $\sum_j P_{ij} = 1$ sob o aumento de inércia $P_{ii}$ quando $N_i > 0.85 N_{j, \max}$;
* `pedestrian_mass_balance_two_nodes`: $N_{\text{propagado}} + N_{\text{egress}} = N_{\text{inicial}}$.

---

## 🚀 4. Como Compilar e Verificar as Provas

No terminal (com Lean 4 instalado):

```powershell
cd formal_proofs
lake build
```
