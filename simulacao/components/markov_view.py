"""
Módulo de Visualização Interativa da Matriz de Transição de Markov (Doc 03).
"""

from typing import List
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.simulation.markov_circulation import MarkovCirculationSimulator


def render_markov_view(sim: MarkovCirculationSimulator, t_hours: float, step_minutes: float = 30.0):
    """
    Renderiza o Heatmap da Matriz Estocástica P(t) e as Atratividades alpha_j(t).
    """
    st.subheader(f"🔄 Matriz de Transição de Markov P(t) às {int(t_hours):02d}:{int((t_hours % 1)*60):02d}")
    st.caption("A matriz P(t) rege as probabilidades estocásticas de caminhada dos pedestres entre cada rua e praça do Pelourinho.")

    p_mat, alphas = sim.evaluate_transition_matrix(
        t_hours=t_hours,
        step_minutes=step_minutes,
        enable_egress=True,
        use_inertia=True,
    )

    labels = [name.replace("Elevador Lacerda", "Elevador").replace("Praça da Sé", "Sé").replace("Ladeira do Carmo", "Carmo").replace("Largo do Pelourinho", "Pelourinho").replace("Terreiro de Jesus", "Terreiro") for name in sim.node_names]

    # Converte para porcentagem formatada
    p_pct = p_mat * 100.0
    text_labels = [[f"{val:.1f}%" for val in row] for row in p_pct]

    col1, col2 = st.columns([3, 1])

    with col1:
        fig = go.Figure(
            data=go.Heatmap(
                z=p_pct,
                x=labels,
                y=labels,
                text=text_labels,
                texttemplate="%{text}",
                textfont={"size": 13, "color": "white"},
                colorscale="Blues",
                colorbar=dict(title="Probabilidade (%)"),
                zmin=0.0,
                zmax=100.0,
            )
        )

        fig.update_layout(
            title="Matriz de Probabilidades Estocásticas (Linha = Origem, Coluna = Destino)",
            xaxis_title="Destino (Para Onde Vai)",
            yaxis_title="Origem (De Onde Sai)",
            height=420,
            margin=dict(l=40, r=40, t=50, b=40),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🧭 Como Ler a Matriz:")
        st.markdown(
            r"""
            * **Diagonal Principal ($P_{ii}$)**: Probabilidade da pessoa permanecer parada no mesmo nó durante o ciclo (inércia de visitação).
            * **Fora da Diagonal ($P_{ij}$)**: Chance de migrar para outro logradouro, ponderada pela gravidade ($e^{-\lambda d_{ij}}$).
            * **Soma da Linha < 100%**: A diferença é exatamente a taxa de **Egress** (pessoas que deixam a cidade pelos portões).
            """
        )
        st.markdown("---")
        st.markdown("#### 🌟 Atratividade $\\alpha_j(t)$:")
        for name, a, p_type in zip(labels, alphas, sim.poi_types):
            badge = "🚪" if p_type.upper() == "GATE" else "🏛️"
            st.write(f"{badge} **{name}**: `{a:.2f}`")
