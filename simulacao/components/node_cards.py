"""
Módulo de Renderização dos Cards de Nós Urbanos (GATEs e POIs).

Apresenta o balanço físico de cada nó monitorado com legendas cristalinas:
- GATEs (Portões): Lotação atual, Entrada da Cidade (Doc 01), Saída da Cidade/Egress (Doc 03) e Saldo Líquido.
- POIs (Praças Internas): Lotação atual, Chegadas de outras ruas, Partidas para outras ruas e Permanência (Dwell).
"""

from typing import Any, Dict, List, Optional
import streamlit as st
from src.simulation.rollout import RolloutStep
from src.simulation.schemas import MarkovNodeFlow


def render_node_cards(
    step_info: RolloutStep,
    node_flows: Optional[List[MarkovNodeFlow]] = None,
):
    """
    Renderiza um grid de 5 colunas com os nós monitorados do Pelourinho.
    """
    st.subheader(f"⏱️ Estado do Bairro às {step_info.hour_formatted} — Lotação Total: {step_info.total_population:.1f} pessoas")
    
    # Mapeia fluxos do Doc 03 caso fornecidos
    flows_map: Dict[str, MarkovNodeFlow] = {}
    if node_flows:
        for flow in node_flows:
            flows_map[flow.nome_local] = flow

    cols = st.columns(len(step_info.node_names))

    for idx, (col, name, p_type) in enumerate(zip(cols, step_info.node_names, step_info.poi_types)):
        curr_pop = step_info.occupancy_by_node.get(name, 0.0)
        is_gate = (p_type.upper() == "GATE")

        with col:
            if is_gate:
                inflow = step_info.inflow_by_gate.get(name, 0.0)
                egress = step_info.egress_by_gate.get(name, 0.0)
                net = inflow - egress

                # Card estilizado para Portões de Borda
                st.markdown(
                    f"""
                    <div style="border: 2px solid #2563EB; border-radius: 10px; padding: 12px; background-color: #1E293B; color: white;">
                        <span style="font-size: 0.8rem; background-color: #2563EB; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🚪 PORTÃO (GATE)</span>
                        <h4 style="margin: 8px 0 4px 0; color: #93C5FD;">{name}</h4>
                        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 6px;">{curr_pop:.1f} <span style="font-size: 0.9rem; font-weight: normal; color: #94A3B8;">pessoas</span></div>
                        <hr style="border: none; border-top: 1px solid #334155; margin: 8px 0;" />
                        <div style="font-size: 0.85rem; color: #4ADE80;">🟢 <b>Entrada:</b> +{inflow:.1f} pess/ciclo</div>
                        <div style="font-size: 0.85rem; color: #F87171;">🔴 <b>Saída (Egress):</b> -{egress:.1f} pess/ciclo</div>
                        <div style="font-size: 0.85rem; color: {'#60A5FA' if net >= 0 else '#FBBF24'}; font-weight: bold; margin-top: 4px;">
                            ⚖️ <b>Saldo Líquido:</b> {net:+.1f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("ℹ️ *Fronteira física externa da cidade.*")
            else:
                # Card estilizado para POIs / Praças Internas
                flow = flows_map.get(name)
                chegaram = flow.inflow_pedestrians if flow else 0.0
                partiram = flow.outflow_pedestrians if flow else 0.0
                ficaram = flow.retained_pedestrians if flow else curr_pop

                st.markdown(
                    f"""
                    <div style="border: 2px solid #10B981; border-radius: 10px; padding: 12px; background-color: #064E3B; color: white;">
                        <span style="font-size: 0.8rem; background-color: #10B981; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🏛️ PRAÇA (POI)</span>
                        <h4 style="margin: 8px 0 4px 0; color: #A7F3D0;">{name}</h4>
                        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 6px;">{curr_pop:.1f} <span style="font-size: 0.9rem; font-weight: normal; color: #D1FAE5;">pessoas</span></div>
                        <hr style="border: none; border-top: 1px solid #047857; margin: 8px 0;" />
                        <div style="font-size: 0.85rem; color: #6EE7B7;">↗️ <b>Chegaram de ruas:</b> +{chegaram:.1f}</div>
                        <div style="font-size: 0.85rem; color: #FCA5A5;">↘️ <b>Partiram p/ ruas:</b> -{partiram:.1f}</div>
                        <div style="font-size: 0.85rem; color: #FDE047; font-weight: bold; margin-top: 4px;">
                            ☕ <b>Permanência:</b> {ficaram:.1f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("ℹ️ *Circulação interna e lazer entre ruas.*")

    st.markdown("<br/>", unsafe_allow_html=True)
