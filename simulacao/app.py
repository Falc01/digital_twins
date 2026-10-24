"""
Gêmeo Digital IoT Pelourinho — Dashboard Interativo de Simulação Estocástica.
UNIFACS — Iniciação Científica (IC).

Para executar:
  streamlit run simulacao/app.py
"""

import os
import sys

# Injeta caminhos do backend no Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if os.path.join(BACKEND_DIR, "src") not in sys.path:
    sys.path.insert(0, os.path.join(BACKEND_DIR, "src"))

import streamlit as st
import numpy as np

from src.simulation.rollout import RolloutSimulationEngine
from src.simulation.schemas import MacroFlowConfig
from simulacao.components.sidebar import render_sidebar
from simulacao.components.node_cards import render_node_cards
from simulacao.components.markov_view import render_markov_view
from simulacao.components.timeline_view import render_timeline_charts


def main():
    st.set_page_config(
        page_title="Gêmeo Digital IoT — Pelourinho",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 1. Renderiza Controles da Barra Lateral
    params = render_sidebar()

    # 2. Cabeçalho Principal
    st.title("🏙️ Gêmeo Digital IoT — Centro Histórico do Pelourinho")
    st.markdown(
        """
        **Iniciação Científica (UNIFACS)** | **Arquitetura de Dados Sintéticos (Docs 01, 02 e 03)**  
        *Simulação contínua do fluxo de pedestres, circulação estocástica por Cadeias de Markov e balanço estrito de portaria.*
        """
    )
    st.markdown("---")

    # 3. Inicializa o Motor de Simulação
    macro_cfg = MacroFlowConfig(
        N_max=params["n_max"],
        N_min=params["n_min"],
        gamma_seasonality=params["gamma"],
        regime=params["regime"],
    )

    engine = RolloutSimulationEngine(
        macro_config=macro_cfg,
        regime=params["regime"],
        gamma=params["gamma"],
        enable_events=params["enable_events"],
    )

    # 4. Pré-computa a Simulação Completa de 24 Horas
    summary = engine.run_batch(
        start_hour=0.0,
        end_hour=24.0,
        step_minutes=params["step_minutes"],
    )

    # 5. Seletor de Horário para Inspeção Instantânea
    col_time, col_info = st.columns([3, 1])
    with col_time:
        hour_labels = [step.hour_formatted for step in summary.steps]
        selected_hour_str = st.select_slider(
            "🕒 Navegar pelo Relógio da Cidade (Horário de Inspeção):",
            options=hour_labels,
            value=hour_labels[len(hour_labels) // 2],
            help="Arraste para inspecionar exatamente o estado e o balanço em qualquer horário do dia.",
        )
    with col_info:
        selected_step_idx = hour_labels.index(selected_hour_str)
        curr_step = summary.steps[selected_step_idx]
        st.metric(
            label="Lotação no Horário",
            value=f"{curr_step.total_population:.1f} pess.",
            delta=f"{curr_step.net_flux:+.1f} fluxo líquido",
        )

    # Obtém detalhes de fluxo de Markov para o horário inspecionado
    markov_res = engine.markov_sim.propagate(
        current_state_N=curr_step.state_N,
        t_hours=curr_step.time_hours,
        gamma=params["gamma"],
        step_minutes=params["step_minutes"],
        enable_egress=True,
        use_inertia=True,
    )

    # 6. Abas Principais da Aplicação
    tab_dashboard, tab_timeline, tab_markov, tab_doc = st.tabs([
        "📊 Painel de Bordo (Cards dos Nós)",
        "📈 Curvas de 24 Horas & Balanço",
        "🔄 Matriz de Transição P(t)",
        "📖 Metodologia & Legendas da IC",
    ])

    with tab_dashboard:
        render_node_cards(step_info=curr_step, node_flows=markov_res.node_flows)

    with tab_timeline:
        render_timeline_charts(summary=summary)

    with tab_markov:
        render_markov_view(
            sim=engine.markov_sim,
            t_hours=curr_step.time_hours,
            step_minutes=params["step_minutes"],
        )

    with tab_doc:
        st.subheader("📚 Guia de Metodologia & Fundamentação Teórica")
        st.markdown(
            f"""
            ### Estrutura do Gêmeo Digital IoT
            * **Doc 01 (Módulo de Entrada)**: Curva circadiana com regime **{params['regime'].upper()}**. Gera novos ingressos ($\\Delta N$) apenas nos portões externos ($w_g$).
            * **Doc 02 (Injeção de Eventos)**: Pulsos culturais pontuais ($E(t)$) em praças internas.
            * **Doc 03 (Circulação de Rede & Markov)**: Matriz $\\mathbf{{P}}(t)$ calibrada por modelo gravitacional ($e^{{-\\lambda d_{{ij}}}}$) com inércia e taxa de evasão nos portões ($p_{{\\text{{exit}}}}$).
            * **Doc 04 (Sensoriamento IoT)**: Saturação logística de Richards e ruído de medição de Ornstein-Uhlenbeck.
            
            ---
            ### Legenda e Significado das Variáveis:
            | Nomenclatura | O que representa fisicamente? |
            | :--- | :--- |
            | **Lotação Atual ($N_j$)** | Total de pedestres presentes fisicamente naquele nó no instante inspecionado. |
            | **Entrada (Portões)** | Novos indivíduos vindos do exterior de Salvador que ingressaram no Pelourinho neste passo. |
            | **Saída / Egress (Portões)** | Pedestres que encerraram a visita ao centro histórico e foram embora da cidade por este portão. |
            | **Chegadas / Partidas (Praças)** | Migração interna de pedestres caminhando entre as ruas e praças do Pelourinho. |
            | **Permanência (POIs)** | Pedestres que permaneceram no mesmo local descansando, consumindo ou visitando atrativos. |
            """
        )


if __name__ == "__main__":
    main()
