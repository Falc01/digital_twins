# 📋 Log de Melhorias e Mudanças — Módulo 01 (v2.0): Desacoplamento Urbano & Multimodalidade Circadiana

**Documento Referenciado:** [`docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/explanation/dados_sinteticos/01_entrada_saida_diaria.md)  
**Arquivo de Implementação:** [`backend/src/simulation/macro_flow.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/macro_flow.py)  
**Classificação:** Especificação Técnica de Evolução & Resolução de Apontamentos de Orientação  
**Autor:** João Spinola Falcão & Supervisor Técnico Digital Twins  
**Data:** 09/10/2026  
**Status:** 🟡 **[EM IMPLEMENTAÇÃO / ESPECIFICADO]**

---

## 📌 1. Motivação da Revisão (Sabatina do Orientador)

Durante a apresentação dos resultados preliminares da suíte de dados sintéticos, a orientação levantou três questionamentos metodológicos críticos sobre o Módulo 01:
1. **A curva de pico único é artificial:** O comportamento urbano real do Pelourinho não é um sino simétrico isolado centralizado às 16h30. O dia possui vales e múltiplos picos (movimento matinal às 09h, pico de almoço às 12h, queda às 14h e novo pico no fim da tarde);
2. **Mistura entre Entidades Urbanas e Hardware IoT:** Os portões de entrada física estavam nomeados e tipados como "sensores", misturando o espaço geográfico da cidade com o dispositivo eletrônico de telemetria;
3. **Balanço Estrito de Portaria:** A necessidade de explicitar o volume puro de novos ingressos ($\Phi_{\text{in}}$) por portão a cada passo de tempo $\Delta t$, isolando o chão da cidade de ruídos instrumentais para alimentar a cadeia aberta de circulação (Doc 03).

---

## 🛠️ 2. Itens de Mudança & Especificação Técnica

### Item 1: Desacoplamento Topológico (Grafo Urbano vs. Sensor IoT)

#### 📍 Diagnóstico Anterior:
No Doc 01 original, os portões de entrada eram definidos dentro de `MacroFlowConfig` sob a lista `gates` contendo objetos `SensorGateWeight`, com identificadores prefixados como `sensor_elevador_lacerda`, `sensor_praca_da_se` e `sensor_ladeira_do_carmo`. Isso gerava acoplamento precoce: o motor de mobilidade urbana acreditava que estava manipulando dispositivos de hardware.

#### ✅ Mudança Arquitetural:
1. **Entidade Urbana Neutra (`UrbanGateNode`):**  
   O Doc 01 passa a operar exclusivamente sobre **Nós de Portão Urbano** (`GATE`):
   * `node_elevador_lacerda` (Portão Oeste / Acesso Comércio e Cidade Baixa — Peso $w_1 = 0.45$);
   * `node_praca_da_se` (Portão Sudoeste / Acesso Terminal Praça da Sé — Peso $w_2 = 0.35$);
   * `node_ladeira_do_carmo` (Portão Norte / Acesso Santo Antônio Além do Carmo — Peso $w_3 = 0.20$).
2. **Exclusão de POIs Internos do Influxo Externo:**  
   Praças internas (`node_terreiro_jesus`, `node_largo_pelourinho`) possuem peso estrito $w_j = 0.0$ no Doc 01. O público não surge espontaneamente no interior do bairro: ele ingressa pelos portões e migra internamente através da matriz de transição do Doc 03.
3. **Camada IoT Delegada ao Doc 04:**  
   Nenhum parâmetro de hardware (ruído, erro de câmera, saturação de Richards) é processado no Doc 01. O Doc 01 gera o **Ground Truth de Entrada**.

---

### Item 2: Multimodalidade Circadiana (Fim do Sino Simétrico Único)

#### 📍 Diagnóstico Anterior:
A formulação clássica adotava uma única Gaussiana centrada em $t_{\text{pico}} = 16.5$ com $\sigma = 3.0\text{ h}$:
$$N_{\text{bairro}}(t) = N_{\min} + (N_{\max} - N_{\min}) \cdot \exp\left( -\frac{(h(t) - 16.5)^2}{2 \times 3^2} \right)$$
Essa formulação tornava a manhã e a noite excessivamente simétricas e impedia que as 12h00 tivessem maior afluência que as 14h00.

#### ✅ Nova Formulação Matemática (Modo Trimodal / Fourier $K=3$):
O cálculo de $N_{\text{bairro}}(t)$ evolui para suportar dois regimes selecionáveis:

#### Regime A: Mistura Trimodal Urbana (Consagrada para Centros Históricos)
Três curvas de fluxo somadas que moldam a dinâmica comercial e turística:
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ N_{\min} + \sum_{m=1}^{3} A_m \cdot \exp\left( -\frac{(h(t) - \tau_m)^2}{2\sigma_m^2} \right) \right]$$

Onde os três picos padrão são calibrados para Salvador:
1. **Pico 1 — Abertura Comercial e Missas Matinais:**  
   $\tau_1 = 09.5$ (09h30), $\sigma_1 = 1.8\text{ h}$, amplitude $A_1 = 0.35 \times (N_{\max} - N_{\min})$;
2. **Pico 2 — Almoço e Gastronomia Histórica (Terreiro de Jesus / Cruzeiro de São Francisco):**  
   $\tau_2 = 12.5$ (12h30), $\sigma_2 = 1.2\text{ h}$, amplitude $A_2 = 0.55 \times (N_{\max} - N_{\min})$;
3. **Pico 3 — Ápice Turístico / Pôr do Sol e Movimento Cultural:**  
   $\tau_3 = 16.8$ (16h48), $\sigma_3 = 2.2\text{ h}$, amplitude $A_3 = 0.90 \times (N_{\max} - N_{\min})$.

*Efeito prático:* Às 12h30 o fluxo atinge patamar elevado; às 14h00 sofre o vale de digestão/calor baiano; e às 16h45 atinge o pico máximo diário, dispersando ao anoitecer.

#### Regime B: Decomposição Harmônica de Fourier ($K=3$)
Alternativa espectral contínua conforme formalizado no artigo principal de dados sintéticos:
$$N_{\text{bairro}}(t) = \gamma \cdot \left[ \beta_0 + \sum_{k=1}^{3} \left( a_k \cos\left(\frac{2\pi k h(t)}{24}\right) + b_k \sin\left(\frac{2\pi k h(t)}{24}\right) \right) \right]$$

---

### Item 3: Preservação da Taxa Diferencial Nodal de Ingressos ($\Delta \mathbf{N}_{\text{in}}$)

O cálculo de influxo diferencial introduzido na v1.0 é preservado e padronizado:
$$\Delta N_{\text{bairro}}(t, \Delta t) = \max\left(0.0, \; N_{\text{bairro}}(t + \Delta t) - N_{\text{bairro}}(t)\right)$$

Para cada portão de entrada $g \in \{\text{Lacerda}, \text{Sé}, \text{Carmo}\}$:
$$\Phi_{\text{in}, g}(t) = w_g \cdot \Delta N_{\text{bairro}}(t, \Delta t)$$

Com a garantia estrita de conservação:
$$\sum_{g \in \text{GATEs}} w_g = 1.0 \implies \sum_{g} \Phi_{\text{in}, g}(t) = \Delta N_{\text{bairro}}(t, \Delta t)$$

---

## 📊 3. Resumo de Impacto nas Interfaces e Contratos

| Elemento | Versão Anterior (v1.0) | Nova Versão (v2.0) |
| :--- | :--- | :--- |
| **Identificadores de Portão** | `sensor_elevador_lacerda` | `node_elevador_lacerda` (ou alias transparente) |
| **Tipo de Curva** | Gaussiana Simples Unimodal (1 pico às 16h30) | Trimodal Paramétrica (09h30, 12h30 e 16h45) ou Fourier $K=3$ |
| **Isolamento de Camada** | Acoplado com conceitos de telemetria | 100% focado no Ground Truth de entrada física |
| **Compatibilidade de API** | Retorna tupla `BairroPopulation` e `MacroFlowResponse` | Mantém retrocompatibilidade total com as rotas FastAPI existentes |

---

## ✅ 4. Plano de Ação para Implementação no Código

1. [ ] Atualizar `macro_flow.py` adicionando a função `calculate_multimodal_bairro_population()` com suporte a múltiplos picos;
2. [ ] Manter retrocompatibilidade com chamadas legadas que passam `t_peak` e `sigma` únicos;
3. [ ] Atualizar schemas em `schemas.py` com o modelo `UrbanGateNode` e harmonização de aliases;
4. [ ] Validar a suíte de testes com `pytest backend/tests/test_macro_flow.py`.
