"""
Módulo de Visualização em Plano Cartesiano 2D & Heatmap Contínuo de Tráfego de Pedestres.

Projeta os 5 nós monitorados do Pelourinho em coordenadas métricas relativas (centradas no Terreiro de Jesus):
- Eixo X (metros): Sentido Oeste (Elevador/Baía) <-> Leste (Carmo)
- Eixo Y (metros): Sentido Sul (Praça da Sé) <-> Norte (Ladeira do Carmo)

Renderiza:
1. Heatmap Contínuo de Densidade Populacional via mistura de Gaussianas 2D;
2. Grafo de Ruas com Arestas Topológicas ponderadas pelo fluxo ativo de pedestres (N_i * P_ij);
3. Marcadores Nodais dos Portões (GATEs) e Praças (POIs) com contagens estritamente inteiras.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.simulation.rollout import RolloutStep
from src.simulation.markov_circulation import MarkovCirculationSimulator


# Coordenadas relativas planas em metros (Origem (0, 0) no Terreiro de Jesus)
# Calculadas a partir das coordenadas WGS84 reais com correção de latitude de Salvador/BA
PELOURINHO_CARTESIAN_COORDS: Dict[str, Tuple[float, float, str]] = {
    "Elevador Lacerda": (-314.0, -22.0, "GATE"),
    "Praça da Sé": (-130.0, -77.0, "GATE"),
    "Ladeira do Carmo": (184.0, 365.0, "GATE"),
    "Largo do Pelourinho": (130.0, 144.0, "POI"),
    "Terreiro de Jesus": (0.0, 0.0, "POI"),
}

# Arestas de ruas conectadas fisicamente (Topologia Urbana)
TOPOLOGICAL_EDGES = [
    ("Elevador Lacerda", "Praça da Sé"),
    ("Elevador Lacerda", "Terreiro de Jesus"),
    ("Praça da Sé", "Terreiro de Jesus"),
    ("Terreiro de Jesus", "Largo do Pelourinho"),
    ("Largo do Pelourinho", "Ladeira do Carmo"),
]


def render_cartesian_view(
    step_info: RolloutStep,
    sim: MarkovCirculationSimulator,
    step_minutes: float = 30.0,
):
    """
    Renderiza o Plano Cartesiano 2D com Heatmap Contínuo e Grafo de Fluxo.
    """
    st.subheader(f"🗺️ Plano Cartesiano 2D & Densidade Contínua de Pedestres às {step_info.hour_formatted}")
    st.caption(
        "Projeção espacial métrica do Pelourinho (metros reais a partir do Terreiro de Jesus). "
        "A mancha de calor reflete a concentração contínua da massa e a espessura das ruas reflete o fluxo de pessoas caminhando."
    )

    # 1. Avalia a matriz P(t) e os fluxos instantâneos
    p_mat, alphas = sim.evaluate_transition_matrix(
        t_hours=step_info.time_hours,
        step_minutes=step_minutes,
        enable_egress=True,
        use_inertia=True,
    )

    # Associa população inteira a cada nó
    node_names = step_info.node_names
    pops = [int(round(step_info.occupancy_by_node.get(name, 0.0))) for name in node_names]
    max_pop = max(pops) if max(pops) > 0 else 1

    # Extrai coordenadas ordenadas
    xs = []
    ys = []
    types = []
    for name in node_names:
        coord = PELOURINHO_CARTESIAN_COORDS.get(name, (0.0, 0.0, "POI"))
        xs.append(coord[0])
        ys.append(coord[1])
        types.append(coord[2])

    fig = go.Figure()

    # 2. Computa Grade 2D para Heatmap de Densidade Contínua (Gaussian Kernel Density)
    grid_x = np.linspace(-420, 280, 71)
    grid_y = np.linspace(-150, 440, 60)
    GX, GY = np.meshgrid(grid_x, grid_y)
    density = np.zeros_like(GX, dtype=np.float64)

    sigma_spatial = 55.0  # Raio de espalhamento pedestre no espaço urbano (55 metros)
    two_sig_sq = 2.0 * (sigma_spatial ** 2)

    for i, name in enumerate(node_names):
        pop_i = pops[i]
        if pop_i > 0:
            dx = GX - xs[i]
            dy = GY - ys[i]
            dist_sq = dx * dx + dy * dy
            density += pop_i * np.exp(-dist_sq / two_sig_sq)

    # Heatmap Contínuo de Superfície (Contour)
    fig.add_trace(
        go.Contour(
            x=grid_x,
            y=grid_y,
            z=density,
            contours=dict(
                coloring="heatmap",
                showlines=False,
            ),
            colorscale=[
                [0.0, "rgba(15, 23, 42, 0.0)"],
                [0.15, "rgba(30, 58, 138, 0.35)"],
                [0.35, "rgba(2, 132, 199, 0.55)"],
                [0.60, "rgba(234, 179, 8, 0.70)"],
                [0.80, "rgba(249, 115, 22, 0.85)"],
                [1.0, "rgba(239, 68, 68, 0.95)"],
            ],
            colorbar=dict(
                title=dict(text="Densidade (pess/área)", font=dict(color="white", size=11)),
                tickfont=dict(color="white", size=10),
                len=0.75,
            ),
            hoverinfo="skip",
            name="Mancha de Calor",
        )
    )

    # 3. Desenha as Arestas de Conexão Topológica entre Ruas
    active_transfers: List[Dict[str, Any]] = []
    flow_max = 1.0

    for u_name, v_name in TOPOLOGICAL_EDGES:
        if u_name in node_names and v_name in node_names:
            u_idx = node_names.index(u_name)
            v_idx = node_names.index(v_name)

            f_uv = pops[u_idx] * p_mat[u_idx, v_idx]
            f_vu = pops[v_idx] * p_mat[v_idx, u_idx]
            tot_edge_flow = f_uv + f_vu
            if tot_edge_flow > flow_max:
                flow_max = tot_edge_flow

            active_transfers.append({
                "u": u_name,
                "v": v_name,
                "u_x": xs[u_idx],
                "u_y": ys[u_idx],
                "v_x": xs[v_idx],
                "v_y": ys[v_idx],
                "f_uv": int(round(f_uv)),
                "f_vu": int(round(f_vu)),
                "tot": int(round(tot_edge_flow)),
            })

    for edge in active_transfers:
        width = 2.0 + 8.0 * (edge["tot"] / max(1.0, flow_max))
        # Linha da rua
        fig.add_trace(
            go.Scatter(
                x=[edge["u_x"], edge["v_x"]],
                y=[edge["u_y"], edge["v_y"]],
                mode="lines",
                line=dict(color="#38BDF8", width=width),
                hoverinfo="text",
                hovertext=(
                    f"🛣️ <b>Conexão:</b> {edge['u']} ↔ {edge['v']}<br>"
                    f"➡️ {edge['u']} ➔ {edge['v']}: <b>{edge['f_uv']} pess</b><br>"
                    f"⬅️ {edge['v']} ➔ {edge['u']}: <b>{edge['f_vu']} pess</b><br>"
                    f"🚶 Fluxo Bidirecional: <b>{edge['tot']} pess/ciclo</b>"
                ),
                showlegend=False,
            )
        )

    # 4. Marcadores dos Nós (GATEs e POIs)
    for i, name in enumerate(node_names):
        is_gate = (types[i] == "GATE")
        marker_color = "#3B82F6" if is_gate else "#10B981"
        line_color = "#93C5FD" if is_gate else "#A7F3D0"
        marker_symbol = "square" if is_gate else "circle"
        marker_size = int(max(24, min(56, 22 + 28 * (pops[i] / max_pop))))
        badge_type = "🚪 PORTÃO" if is_gate else "🏛️ PRAÇA"

        fig.add_trace(
            go.Scatter(
                x=[xs[i]],
                y=[ys[i]],
                mode="markers+text",
                marker=dict(
                    size=marker_size,
                    color=marker_color,
                    symbol=marker_symbol,
                    line=dict(color=line_color, width=3),
                ),
                text=[f"<b>{name}</b><br>👥 {pops[i]} pess."],
                textposition="top center",
                textfont=dict(color="white", size=12, family="sans-serif"),
                hoverinfo="text",
                hovertext=(
                    f"<b>{badge_type}: {name}</b><br>"
                    f"👥 Lotação Atual: <b>{pops[i]} pessoas</b><br>"
                    f"🌟 Atratividade α(t): <b>{alphas[i]:.2f}x</b><br>"
                    f"📍 Posição no Plano: X={xs[i]:.0f}m, Y={ys[i]:.0f}m"
                ),
                name=f"{badge_type} ({name})",
                showlegend=False,
            )
        )

    # 5. Ajustes de Layout e Estilo Cartesiano
    fig.update_layout(
        title=dict(
            text=f"Plano de Circulação Urbana — {step_info.hour_formatted} (Lotação Total: {int(round(step_info.total_population)):,} pess.)",
            font=dict(color="white", size=16),
        ),
        xaxis=dict(
            title="Distância Leste-Oeste (metros a partir do Terreiro)",
            color="white",
            gridcolor="#334155",
            zerolinecolor="#64748B",
            range=[-420, 280],
        ),
        yaxis=dict(
            title="Distância Norte-Sul (metros a partir do Terreiro)",
            color="white",
            gridcolor="#334155",
            zerolinecolor="#64748B",
            scaleanchor="x",
            scaleratio=1,
            range=[-150, 440],
        ),
        plot_bgcolor="#1E293B",
        paper_bgcolor="#0F172A",
        height=580,
        margin=dict(l=40, r=40, t=50, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # 6. Painel Resumo de Fluxos Ativos entre Ruas
    st.markdown("#### 🚶 Tráfego Ativo de Pedestres nas Ruas Conectadas:")
    cols = st.columns(len(active_transfers))
    for col, edge in zip(cols, active_transfers):
        with col:
            st.metric(
                label=f"{edge['u'].split()[0]} ↔ {edge['v'].split()[0]}",
                value=f"{edge['tot']} pess.",
                delta=f"{edge['f_uv']} ➔ | ⬅️ {edge['f_vu']}",
                help=f"Fluxo total entre {edge['u']} e {edge['v']} durante o ciclo de {int(step_minutes)} minutos.",
            )
