# 🏙️ Dashboard Interativo de Simulação Estocástica de Pedestres
## Gêmeo Digital IoT Pelourinho — UNIFACS (Iniciação Científica)

Dashboard web modular construído em **Streamlit** e **Plotly** para inspeção, controle e apresentação visual do motor matemático de simulação de pedestres do Centro Histórico do Pelourinho (Docs 01, 02 e 03).

---

## 🚀 Como Executar

Na raiz do repositório, execute:

```powershell
streamlit run simulacao/app.py
```

O navegador abrirá automaticamente no endereço: `http://localhost:8501`.

---

## 🗂️ Arquitetura Modular (`simulacao/`)

A aplicação foi estruturada de forma 100% modular para facilitar a manutenção e evolução:

* **`app.py`**: Ponto de entrada principal da aplicação, orquestrando o layout, tabs e sincronização temporal.
* **`components/sidebar.py`**: Controles dinâmicos da barra lateral (capacidade $N_{\max}$, piso $N_{\min}$, sazonalidade $\gamma$, regimes trimodal/unimodal/fourier, passo $\Delta t$).
* **`components/node_cards.py`**: Renderização em grid dos 5 nós com separação semântica e cores distintas:
  * **Portões (GATEs)**: Elevador Lacerda, Praça da Sé, Ladeira do Carmo (Entradas da cidade, saídas/egress e saldo líquido).
  * **Praças (POIs)**: Largo do Pelourinho, Terreiro de Jesus (Chegadas de ruas, partidas para ruas e tempo de permanência).
* **`components/markov_view.py`**: Heatmap interativo 5x5 da matriz de transição estocástica $\mathbf{P}(t)$ e atratividades $\alpha_j(t)$.
* **`components/timeline_view.py`**: Curvas de 24 horas de lotação, balanço de portões e métricas executivas consolidadas.

---

## 📊 Funcionalidades em Destaque

1. **Alteração Instantânea de Parâmetros**: Mude a capacidade de $150$ para $1000$ pessoas com um simples clique ou digitação na barra lateral.
2. **Comparativo de Regimes**: Compare a curva **Trimodal v2.0** com a antiga curva Unimodal para demonstrar a correção do pico de almoço (12h30) e do vale de calor (14h00).
3. **Navegador Temporal (Scrubber)**: Arraste o slider de horas para inspecionar exatamente o que está acontecendo na cidade em qualquer horário do dia.
4. **Didática e Legendas Integradas**: Tooltips e aba metodológica completa para consulta durante apresentações e sabatinas.
