"""
Módulo de Renderização dos Cards de Nós Urbanos (GATEs e POIs).

Apresenta o balanço físico de cada nó monitorado com contagens estritamente inteiras
e indicação dinâmica do campo de atratividade temporal alpha_j(t):
- GATEs (Portões): Lotação atual, Entrada da Cidade (Doc 01), Saída/Egress (Doc 03), Saldo e Ímã de Retorno.
- POIs (Praças Internas): Lotação atual, Chegadas de outras ruas, Partidas, Permanência e Polo Atrator.
"""

from typing import Any, Dict, List, Optional, Sequence
import streamlit as st
from src.simulation.rollout import RolloutStep
from src.simulation.schemas import MarkovNodeFlow


def render_node_cards(
    step_info: RolloutStep,
    node_flows: Optional[List[MarkovNodeFlow]] = None,
    alpha_vector: Optional[Sequence[float]] = None,
):
    """
    Renderiza um grid de 5 colunas com os nós monitorados do Pelourinho (valores inteiros).
    """
    tot_pop_int = int(round(step_info.total_population))
    st.subheader(f"⏱️ Estado do Bairro às {step_info.hour_formatted} — Lotação Total: {tot_pop_int:,} pessoas")
    
    # Mapeia fluxos do Doc 03 caso fornecidos
    flows_map: Dict[str, MarkovNodeFlow] = {}
    if node_flows:
        for flow in node_flows:
            flows_map[flow.nome_local] = flow

    cols = st.columns(len(step_info.node_names))

    for idx, (col, name, p_type) in enumerate(zip(cols, step_info.node_names, step_info.poi_types)):
        curr_pop = int(round(step_info.occupancy_by_node.get(name, 0.0)))
        is_gate = (p_type.upper() == "GATE")
        alpha_val = float(alpha_vector[idx]) if alpha_vector is not None and idx < len(alpha_vector) else 1.0

        with col:
            if is_gate:
                inflow = int(round(step_info.inflow_by_gate.get(name, 0.0)))
                egress = int(round(step_info.egress_by_gate.get(name, 0.0)))
                net = inflow - egress

                # Explicação dinâmica da atratividade do portão
                if alpha_val >= 2.0:
                    alpha_badge = f"<span style='color: #F87171; font-weight: bold;'>🧲 α={alpha_val:.2f}x (Forte Ímã de Saída/Egress)</span>"
                elif alpha_val >= 1.0:
                    alpha_badge = f"<span style='color: #FBBF24;'>🧲 α={alpha_val:.2f}x (Transição Vespertina)</span>"
                else:
                    alpha_badge = f"<span style='color: #94A3B8;'>🚪 α={alpha_val:.2f}x (Portão de Entrada Diurna)</span>"

                # Card estilizado para Portões de Borda
                st.markdown(
                    f"""
                    <div style="border: 2px solid #2563EB; border-radius: 10px; padding: 12px; background-color: #1E293B; color: white;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.75rem; background-color: #2563EB; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🚪 PORTÃO (GATE)</span>
                        </div>
                        <h4 style="margin: 8px 0 4px 0; color: #93C5FD; font-size: 1.05rem;">{name}</h4>
                        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 4px;">{curr_pop} <span style="font-size: 0.85rem; font-weight: normal; color: #94A3B8;">pessoas</span></div>
                        <div style="font-size: 0.78rem; margin-bottom: 6px;">{alpha_badge}</div>
                        <hr style="border: none; border-top: 1px solid #334155; margin: 6px 0;" />
                        <div style="font-size: 0.83rem; color: #4ADE80;">🟢 <b>Entrada:</b> +{inflow} pess/ciclo</div>
                        <div style="font-size: 0.83rem; color: #F87171;">🔴 <b>Saída (Egress):</b> -{egress} pess/ciclo</div>
                        <div style="font-size: 0.83rem; color: {'#60A5FA' if net >= 0 else '#FBBF24'}; font-weight: bold; margin-top: 4px;">
                            ⚖️ <b>Saldo Líquido:</b> {net:+d}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("ℹ️ *Fronteira física externa de Salvador.*")
            else:
                # Card estilizado para POIs / Praças Internas
                flow = flows_map.get(name)
                chegaram = int(round(flow.inflow_pedestrians)) if flow else 0
                partiram = int(round(flow.outflow_pedestrians)) if flow else 0
                ficaram = int(round(flow.retained_pedestrians)) if flow else curr_pop

                # Explicação dinâmica da atratividade do POI
                if alpha_val >= 2.5:
                    alpha_badge = f"<span style='color: #34D399; font-weight: bold;'>🌟 α={alpha_val:.2f}x (Epicentro de Atração)</span>"
                elif alpha_val >= 1.2:
                    alpha_badge = f"<span style='color: #A7F3D0;'>🏛️ α={alpha_val:.2f}x (Atração Turística Ativa)</span>"
                else:
                    alpha_badge = f"<span style='color: #6EE7B7;'>🚶 α={alpha_val:.2f}x (Circulação Dispersa)</span>"

                st.markdown(
                    f"""
                    <div style="border: 2px solid #10B981; border-radius: 10px; padding: 12px; background-color: #064E3B; color: white;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.75rem; background-color: #10B981; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🏛️ PRAÇA (POI)</span>
                        </div>
                        <h4 style="margin: 8px 0 4px 0; color: #A7F3D0; font-size: 1.05rem;">{name}</h4>
                        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 4px;">{curr_pop} <span style="font-size: 0.85rem; font-weight: normal; color: #D1FAE5;">pessoas</span></div>
                        <div style="font-size: 0.78rem; margin-bottom: 6px;">{alpha_badge}</div>
                        <hr style="border: none; border-top: 1px solid #047857; margin: 6px 0;" />
                        <div style="font-size: 0.83rem; color: #6EE7B7;">↗️ <b>Chegaram de ruas:</b> +{chegaram}</div>
                        <div style="font-size: 0.83rem; color: #FCA5A5;">↘️ <b>Partiram p/ ruas:</b> -{partiram}</div>
                        <div style="font-size: 0.83rem; color: #FDE047; font-weight: bold; margin-top: 4px;">
                            ☕ <b>Permanência:</b> {ficaram}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("ℹ️ *Circulação de lazer e permanência.*")

    st.markdown("<br/>", unsafe_allow_html=True)
