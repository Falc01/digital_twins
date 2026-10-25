"""
Módulo de Controles da Barra Lateral (Sidebar) do Dashboard de Simulação.
"""

from typing import Any, Dict
import streamlit as st


def render_sidebar() -> Dict[str, Any]:
    """
    Renderiza os controles interativos da barra lateral e retorna o dicionário de parâmetros.
    """
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        st.caption("Gêmeo Digital IoT Pelourinho — UNIFACS")
        st.divider()

        st.subheader("1. Parâmetros Populacionais")
        n_max = st.number_input(
            "Capacidade Máxima (N_max)",
            min_value=50,
            max_value=5000,
            value=300,
            step=50,
            help="Lotação máxima teórica do bairro no ápice diário (pessoas).",
        )
        n_min = st.number_input(
            "Piso da Madrugada (N_min)",
            min_value=0,
            max_value=200,
            value=15,
            step=5,
            help="Contagem basal de pessoas na madrugada deserta (pessoas).",
        )
        gamma = st.slider(
            "Fator Sazonal (γ)",
            min_value=1.0,
            max_value=3.5,
            value=1.0,
            step=0.1,
            help="1.0 = Dia útil comum, 1.5 = Alta estação / Verão, 3.5 = Carnaval.",
        )

        st.divider()
        st.subheader("2. Regime Circadiano (Doc 01)")
        regime = st.selectbox(
            "Regime de Modelagem",
            options=["trimodal", "unimodal", "fourier"],
            index=0,
            format_func=lambda x: {
                "trimodal": "Trimodal (Salvador v2.0 - 09h30, 12h30, 16h48)",
                "unimodal": "Unimodal (Gaussiana Simples v1.0)",
                "fourier": "Fourier (Decomposição Harmônica K=3)",
            }.get(x, x),
            help="Trimodal: Reflete o pico de almoço e o vale de calor cobrado na sabatina de Salvador.",
        )

        st.divider()
        st.subheader("3. Granularidade Temporal")
        step_minutes = st.select_slider(
            "Passo de Tempo (Δt)",
            options=[15.0, 30.0, 60.0],
            value=30.0,
            format_func=lambda x: f"{int(x)} minutos",
            help="Intervalo de avanço do relógio da cidade a cada ciclo.",
        )

        enable_events = st.checkbox(
            "Ativar Eventos Culturais (Doc 02)",
            value=False,
            help="Injeta pulsos pontuais de eventos culturais no Pelourinho (ex: Terça da Benção, ensaios).",
        )

    return {
        "n_max": int(n_max),
        "n_min": int(n_min),
        "gamma": float(gamma),
        "regime": regime,
        "step_minutes": float(step_minutes),
        "enable_events": enable_events,
    }
