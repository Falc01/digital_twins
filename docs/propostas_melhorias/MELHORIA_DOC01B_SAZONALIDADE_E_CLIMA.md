# ☀️ Melhoria Doc 01-B: Sazonalidade das 4 Estações, Fator Climático e Calibração de Gamma

**Atribuição:** Desenvolvedor A (Parte 2: Sazonalidade, Clima e Calibração)  
**Arquivo Principal de Código:** [`backend/src/simulation/macro_flow.py`](file:///backend/src/simulation/macro_flow.py) e [`backend/shared/config_simulacao.yaml`](file:///backend/shared/config_simulacao.yaml)  
**Arquivo de Testes:** [`backend/tests/test_macro_flow.py`](file:///backend/tests/test_macro_flow.py)  
**Referência Canônica:** [`docs/explanation/dados_sinteticos/01_modulo_de_entrada.md`](file:///docs/explanation/dados_sinteticos/01_modulo_de_entrada.md)  
**Status:** Especificação Pronta para Implementação  

---

## 📌 1. Visão Geral do Escopo

Este documento isola a responsabilidade de modular a escala global de público do Pelourinho através do multiplicador **$\gamma$ (gamma)**.

O objetivo é substituir o slider puramente arbitrário por uma **camada de Sazonalidade e Clima simples**, garantindo que o gestor/pesquisador sempre possa **sobrescrever ou calibrar manualmente os valores primários**.

---

## 🧮 2. Formulação Matemática

### 2.1. Equação Unificada do Multiplicador Sazonal
$$\gamma_{\text{efetivo}} = \gamma_{\text{manual}} \cdot \gamma_{\text{estação}} \cdot \omega_{\text{clima}}$$

Onde:
* $\gamma_{\text{manual}}$: Controle de ajuste fino do gestor (padrão $1.0$, configurável livremente de $0.1$ a $5.0$);
* $\gamma_{\text{estação}}$: Peso da temporada turística do ano;
* $\omega_{\text{clima}}$: Fator redutor de intempéries pluviométricas (chuva).

---

### 2.2. Tabela das 4 Estações em Salvador

| Estação do Ano | Dinâmica de Turismo e Circulação | Peso Padrão $\gamma_{\text{estação}}$ |
| :--- | :--- | :---: |
| ☀️ **Verão** | **Alta Estação:** Férias, cruzeiros no Porto, ensaios e turismo pleno. | **$1.50$** |
| 🌸 **Primavera** | **Média Estação:** Turismo cultural contínuo, tempo seco e congressos. | **$1.10$** |
| 🍂 **Outono** | **Transição:** Início das chuvas de abril/maio, arrefecimento turístico. | **$0.90$** |
| ❄️ **Inverno** | **Baixa Estação:** Meses mais chuvosos de Salvador (maio a julho). | **$0.75$** |

*Nota:* Os pesos acima residem no arquivo `config_simulacao.yaml` e podem ser alterados pelo pesquisador a qualquer momento sem recompilação.

---

### 2.3. Fator de Chuva ($\omega_{\text{clima}}$)
Devido ao calçamento histórico de pedra secular ("cabeça de negro") e ladeiras a céu aberto, a chuva esvazia o fluxo de rua:

1. ☀️ **Sol / Tempo Firme (`SUNNY`):** $\omega_{\text{clima}} = 1.00$ (sem impacto);
2. 🌦️ **Chuva Fraca / Garoa (`LIGHT_RAIN`):** $\omega_{\text{clima}} = 0.80$ (queda de 20%);
3. ⛈️ **Chuva Forte / Tempestade (`HEAVY_RAIN`):** $\omega_{\text{clima}} = 0.40$ (queda de 60%, fluxo restrito a coberturas).

---

### 2.4. Autonomia Total do Gestor (Override Manual)
O gestor sempre possui a palavra final sobre os parâmetros:
1. **Modo Automático:** O gestor escolhe a Estação e o Clima nos seletores, e o sistema calcula $\gamma_{\text{efetivo}} = \gamma_{\text{estação}} \times \omega_{\text{clima}}$.
2. **Modo Manual / Override:** Um campo numérico permite que o gestor digite diretamente o $\gamma$ desejado (ex: $\gamma = 2.15$), ignorando os multiplicadores automáticos caso queira realizar um experimento científico controlado.

---

## 🛠️ 3. Checklist de Implementação

- [ ] Adicionar seção de sazonalidade e clima em `backend/shared/config_simulacao.yaml`.
- [ ] Implementar a função `calculate_gamma_seasonality(season, weather, manual_gamma=1.0) -> float` em `macro_flow.py`.
- [ ] Integrar $\gamma_{\text{efetivo}}$ no cálculo da curva circadiana $N_{\text{bairro}}(t)$.
- [ ] Escrever testes unitários em `backend/tests/test_macro_flow.py` cobrindo as 4 estações, os 3 climas e o override manual.
