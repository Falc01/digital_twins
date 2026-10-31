# ☀️ RFC-003: Modelo Global de Sazonalidade Anual & Atenuação Climática Pluviométrica

**Status:** Proposta Técnica (Backlog / Para Implementação)  
**Módulo Pertencente:** Doc 01 (`backend/src/simulation/macro_flow.py`) e Configuração Geral (`backend/shared/config_simulacao.yaml`)  
**Contexto Institucional:** UNIFACS — Iniciação Científica (IC) — Gêmeo Digital IoT Pelourinho  
**Data:** Outubro de 2026  

---

## 📌 1. Motivação e Diagnóstico do Estado Atual

### 1.1. Diagnóstico do Código Atual
Na arquitetura atual:
* A sazonalidade é tratada como um multiplicador escalar estático $\gamma$ (`gamma_seasonality`, padrão 1.0), configurável apenas manualmente por slider no frontend ou chamada de API.
* **Problema:** Não existe conexão com o **mês do ano** (calendário de alta/baixa estação de Salvador) nem com **condições meteorológicas** (chuva, tempestades e avisos da CODESAL — Defesa Civil de Salvador).
* O Pelourinho é um centro urbano histórico a céu aberto, com ruas inclinadas e piso de pedra ("cabeça de negro" e paralelepípedos). Em dias de chuva torrencial, o turismo zera e o comércio retrai bruscamente.

---

## 🏛️ 2. Fundamentação Urbana e Climática de Salvador

A dinâmica de fluxo turístico e de pedestres em Salvador é fortemente sazonal e bimoldada por dois fatores cardeais:

### 2.1. Calendário de Temporadas Turísticas
1. **Alta Temporada de Verão (Dezembro a Março):**
   * Férias escolares, chegada de dezenas de transatlânticos no Porto de Salvador (cujo fluxo sobe prioritariamente pelo Elevador Lacerda), festivais de pré-carnaval e o próprio Carnaval.
   * Multiplicador turístico típico: $\gamma \approx 1.40 - 1.85$.
2. **Quadra Chuvosa / Baixa Temporada (Abril a Julho):**
   * Período de maior precipitação histórica da cidade (médias de 200mm a 320mm/mês). O turismo a pé em declive sofre retração acentuada.
   * Multiplicador típico: $\gamma \approx 0.65 - 0.85$.
   * *Exceção Junina:* A segunda quinzena de junho apresenta uma subida pontual decorrente do São João da Bahia no Pelourinho ($\gamma \approx 1.25$).
3. **Média Temporada / Primavera Cultural (Agosto a Novembro):**
   * Fluxo contínuo de congressos científicos, turismo histórico europeu e estadunidense, viagens corporativas e preparação para o verão.
   * Multiplicador típico: $\gamma \approx 1.00 - 1.15$.

---

## 🧮 3. Modelagem Matemática da Sazonalidade

Propõe-se a substituição do $\gamma$ puramente manual por uma **decomposição multiplicativa contínua**:

$$\gamma_{\text{efetivo}}(t) = \gamma_{\text{base}} \cdot M(\text{mês}) \cdot D(\text{dia}) \cdot \omega_{\text{clima}}$$

Onde:
* $\gamma_{\text{base}}$: Multiplicador manual ou de calibração basal (padrão 1.0);
* $M(m) \in [0.6, 2.0]$: Curva sazonal mensal de Salvador ($m \in \{1, \dots, 12\}$);
* $D(d) \in [0.9, 1.3]$: Modulador do tipo de dia (especificado na RFC-001);
* $\omega_{\text{clima}} \in [0.15, 1.0]$: Fator redutor de intempéries pluviométricas.

---

### 3.1. Calibração Mensal $M(m)$ para Salvador

| Mês ($m$) | Nome | Temporada Urbana | Índice Sazonal $M(m)$ | Justificativa |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Janeiro | Alta Verão / Festas | $1.65$ | Férias, ensaios de verão, Lavagem do Bonfim |
| **2** | Fevereiro | Super Alta / Carnaval | $1.85$ | Festa de Iemanjá, ápice de cruzeiros, Carnaval |
| **3** | Março | Transição Pós-Carnaval | $1.20$ | Arrefecimento pós-folia, retorno às aulas |
| **4** | Abril | Início Quadra Chuvosa | $0.80$ | Aumento de chuvas de outono, queda turística |
| **5** | Maio | Ápice Pluviométrico | $0.70$ | Mês mais chuvoso do ano em Salvador (>300mm) |
| **6** | Junho | Baixa + Janela São João | $1.15$ | Festas juninas e forró no Pelourinho |
| **7** | Julho | Inverno Baiano | $0.85$ | Chuvas persistentes e ventos marítimos |
| **8** | Agosto | Média Temporada | $0.95$ | Retomada do turismo escolar e cultural |
| **9** | Setembro | Início da Primavera | $1.00$ | Tempo seco, fluxo equilibrado |
| **10** | Outubro | Média Temporada | $1.10$ | Turismo histórico internacional e eventos |
| **11** | Novembro | Mês da Consciência Negra | $1.25$ | Forte afluência cultural e afro-turismo |
| **12** | Dezembro | Abertura do Verão | $1.50$ | Férias de fim de ano, Natal e Réveillon |

---

### 3.2. Função de Atenuação Meteorológica $\omega_{\text{clima}}$

O impacto da chuva no tráfego de pedestres segue uma curva logística decrescente em função do volume instantâneo ou regime de precipitação $R$ (em mm/h):

$$\omega_{\text{clima}}(R) = \omega_{\min} + \frac{1.0 - \omega_{\min}}{1.0 + \left(\frac{R}{R_0}\right)^\alpha}$$

Onde:
* $\omega_{\min} = 0.20$: Piso mínimo residual (pedestres abrigados sob marquises, restaurantes e transporte essencial);
* $R_0 = 4.0\text{ mm/h}$: Ponto de meia-atenuação (chuva moderada onde 50% das pessoas buscam abrigo imediato);
* $\alpha = 2.0$: Declividade da aversão à chuva.

#### Categorias Práticas de Entrada:
Se o sistema não dispuser de telemetria pluviométrica contínua em mm/h, suporta categorias discretas:
1. `SOL_LIMPO` ou `NUBLADO`: $\omega_{\text{clima}} = 1.00$
2. `CHUVA_FRACA` / Garôa ($R \le 2\text{ mm/h}$): $\omega_{\text{clima}} = 0.80$
3. `CHUVA_MODERADA` ($2 < R \le 10\text{ mm/h}$): $\omega_{\text{clima}} = 0.50$
4. `TEMPESTADE` / Alerta CODESAL ($R > 10\text{ mm/h}$): $\omega_{\text{clima}} = 0.20$

---

## 🛠️ 4. Especificação Técnica de Implementação

### 4.1. Atualização do `config_simulacao.yaml`
Adicionar bloco de sazonalidade:
```yaml
simulation:
  seasonality:
    enable_climate_attenuation: true
    default_climate_condition: "SOL_LIMPO"
    monthly_weights:
      1: 1.65
      2: 1.85
      3: 1.20
      4: 0.80
      5: 0.70
      6: 1.15
      7: 0.85
      8: 0.95
      9: 1.00
      10: 1.10
      11: 1.25
      12: 1.50
```

### 4.2. Integração com o Backend e API
* Endpoint `/simulation/run` e classes `MacroFlowConfig` passam a aceitar:
  * `month: Optional[int] = None` (1 a 12);
  * `weather_condition: Optional[str] = "SOL_LIMPO"`.
* Se não fornecidos, `month` é inferido de `datetime.now().month`.

### 4.3. Exposição no Dashboard Streamlit (`simulacao/components/sidebar.py`)
* Widget seletor de "Mês do Ano" (com indicativo de Alta/Baixa estação).
* Widget seletor de "Condição Climática" (Sol, Nublado, Chuva Fraca, Temporal).
* Exibição visual do $\gamma_{\text{efetivo}}$ resultante calculado dinamicamente em tempo real.

---

## ✅ 5. Critérios de Aceitação (DoD)
- [ ] Validação numérica: Simulação para o mês de Maio sob Tempestade deve produzir volume $\sim 4$ vezes menor que Janeiro em Sol Limpo.
- [ ] Retrocompatibilidade: Se os parâmetros de mês e clima forem omitidos, o sistema mantém $\gamma = 1.0$ e comportamento idêntico à v2.0.
- [ ] Testes unitários com parametrização cobrindo os 12 meses e as 4 categorias climáticas.
