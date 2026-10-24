"""
Módulo de Visualização Temporal e Balanço de Portões em 24 Horas.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.simulation.rollout import RolloutSummary


def render_timeline_charts(summary: RolloutSummary):
    """
    Renderiza os gráficos de evolução temporal de 24 horas e balanço de portões.
    """
    st.subheader("📈 Curva Circadiana de 24 Horas & Balanço de Ingressos/Saídas")

    # Métricas Executivas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pico Máximo de Lotação", f"{summary.peak_population:.1f} pessoas", f"às {summary.peak_time_formatted}")
    m2.metric("Total de Ingressos no Dia", f"+{summary.cumulative_inflow:.1f} pessoas", "Entraram no Pelourinho")
    m3.metric("Total de Saídas (Egress)", f"-{summary.cumulative_egress:.1f} pessoas", "Foram embora da cidade")
    m4.metric("Saldo Líquido da Cidade", f"{summary.net_city_balance:+.1f} pessoas", "Balanço residual diário")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Prepara DataFrame para gráficos
    rows = []
    for step in summary.steps:
        row = {
            "Horário": step.hour_formatted,
            "Hora (dec)": step.time_hours,
            "Lotação Total": step.total_population,
            "Total Ingressos (+In)": step.total_inflow,
            "Total Saídas (-Out)": step.total_egress,
            "Saldo do Ciclo": step.net_flux,
        }
        for g_name, in_val in step.inflow_by_gate.items():
            eg_val = step.egress_by_gate.get(g_name, 0.0)
            short = g_name.replace("Elevador Lacerda", "Elevador").replace("Praça da Sé", "Sé").replace("Ladeira do Carmo", "Carmo")
            row[f"In_{short}"] = in_val
            row[f"Out_{short}"] = eg_val
        rows.append(row)

    df = pd.DataFrame(rows)

    tab_curve, tab_gates, tab_table = st.tabs(["📊 Curva de Lotação Total", "🚪 Balanço por Portão", "📋 Tabela de Dados"])

    with tab_curve:
        fig_curve = go.Figure()

        # Linha da população total
        fig_curve.add_trace(
            go.Scatter(
                x=df["Horário"],
                y=df["Lotação Total"],
                mode="lines+markers",
                name="População no Bairro (N_bairro)",
                line=dict(color="#3B82F6", width=3),
                marker=dict(size=6),
            )
        )

        # Adiciona anotação no pico
        fig_curve.add_annotation(
            x=summary.peak_time_formatted,
            y=summary.peak_population,
            text=f"Ápice: {summary.peak_population:.1f}p ({summary.peak_time_formatted})",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#EF4444",
            ax=0,
            ay=-40,
        )

        fig_curve.update_layout(
            title=f"Evolução Contínua da Lotação do Pelourinho (Regime {summary.regime.upper()})",
            xaxis_title="Hora do Dia",
            yaxis_title="Pedestres no Bairro (Pessoas)",
            height=400,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40),
        )

        st.plotly_chart(fig_curve, use_container_width=True)

    with tab_gates:
        fig_gates = go.Figure()

        fig_gates.add_trace(
            go.Bar(
                x=df["Horário"],
                y=df["Total Ingressos (+In)"],
                name="Novos Ingressos (+Entradas)",
                marker_color="#10B981",
            )
        )

        fig_gates.add_trace(
            go.Bar(
                x=df["Horário"],
                y=-df["Total Saídas (-Out)"],
                name="Dispersão (-Saídas/Egress)",
                marker_color="#EF4444",
            )
        )

        fig_gates.update_layout(
            title="Balanço Dinâmico de Entradas e Saídas da Cidade nos Portões de Borda",
            xaxis_title="Hora do Dia",
            yaxis_title="Pedestres / Ciclo",
            barmode="relative",
            height=400,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40),
        )

        st.plotly_chart(fig_gates, use_container_width=True)

    with tab_table:
        st.dataframe(df, use_container_width=True)
