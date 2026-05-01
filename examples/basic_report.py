"""Basic example: capture charts and build a report.

Run with:
    uv run python dash-reportbuilder/examples/basic_report.py
"""

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html

from dash_capture import capture_graph, plotly_strategy
from dash_reportbuilder import MemoryStore, report_action, report_viewer

app = Dash(__name__)
store = MemoryStore()

# --- Sample figures ---

fig1 = go.Figure(
    data=go.Scatter(
        x=np.arange(50),
        y=np.cumsum(np.random.randn(50)),
        mode="lines+markers",
        name="Random walk",
    ),
    layout=go.Layout(title="Random Walk", template="plotly_white"),
)

fig2 = go.Figure(
    data=go.Bar(
        x=["A", "B", "C", "D", "E"],
        y=[23, 45, 12, 67, 34],
        marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
    ),
    layout=go.Layout(title="Categories", template="plotly_white"),
)

# --- Layout ---

app.layout = html.Div(
    style={
        "maxWidth": "900px",
        "margin": "0 auto",
        "padding": "24px",
        "fontFamily": "sans-serif",
    },
    children=[
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            },
            children=[
                html.H2("Dashboard"),
                report_viewer(store),
            ],
        ),
        html.H4("Chart 1: Random Walk"),
        dcc.Graph(id="graph1", figure=fig1),
        capture_graph(
            "graph1",
            strategy=plotly_strategy(strip_title=True),
            actions=[report_action(store)],
        ),
        html.H4("Chart 2: Categories"),
        dcc.Graph(id="graph2", figure=fig2),
        capture_graph(
            "graph2",
            strategy=plotly_strategy(strip_title=True),
            actions=[report_action(store)],
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True, port=8055)
