"""
Componentes modulares de interface do Dashboard de Simulação.
"""

from simulacao.components.sidebar import render_sidebar
from simulacao.components.node_cards import render_node_cards
from simulacao.components.cartesian_view import render_cartesian_view
from simulacao.components.markov_view import render_markov_view
from simulacao.components.timeline_view import render_timeline_charts

__all__ = [
    "render_sidebar",
    "render_node_cards",
    "render_cartesian_view",
    "render_markov_view",
    "render_timeline_charts",
]
