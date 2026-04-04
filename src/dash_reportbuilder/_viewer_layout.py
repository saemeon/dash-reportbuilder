# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Pure layout construction for the report viewer — no callbacks."""

from __future__ import annotations

from dash import dcc, html

from dash_reportbuilder.model import ItemType, Report, ReportItem

_ITEM_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "8px",
    "padding": "8px",
    "border": "1px solid #e0e0e0",
    "borderRadius": "4px",
    "background": "#fafafa",
}

_DRAG_HANDLE_STYLE = {
    "cursor": "grab",
    "color": "#999",
    "fontSize": "18px",
    "userSelect": "none",
    "padding": "0 4px",
}

_DELETE_STYLE = {
    "cursor": "pointer",
    "color": "#c00",
    "border": "none",
    "background": "none",
    "fontSize": "16px",
    "padding": "0 4px",
}


def render_item(item: ReportItem) -> html.Div:
    """Render a single report item as a Div with drag handle + content + delete."""
    if item.type == ItemType.IMAGE:
        content = html.Img(
            src=item.content,
            style={"maxWidth": "200px", "maxHeight": "150px"},
        )
    elif item.type == ItemType.PAGE_BREAK:
        content = html.Hr(style={"flex": "1", "margin": "0"})
    else:
        content = dcc.Input(
            id={"type": "drb-text", "index": item.id},
            value=item.content,
            type="text",
            debounce=True,
            style={
                "flex": "1",
                "minHeight": "32px",
                "border": "1px solid #ddd",
                "borderRadius": "3px",
                "padding": "4px 8px",
                "fontWeight": "bold" if item.type == ItemType.HEADING else "normal",
                "fontStyle": "italic" if item.type == ItemType.CAPTION else "normal",
                "fontSize": "16px" if item.type == ItemType.HEADING else "13px",
            },
        )

    type_label = item.type.value.replace("_", " ").title()

    return html.Div(
        id=f"drb-item-{item.id}",
        style=_ITEM_STYLE,
        className="drb-item",
        children=[
            html.Span("\u2261", className="drb-drag-handle", style=_DRAG_HANDLE_STYLE),
            html.Span(
                type_label,
                style={
                    "fontSize": "10px",
                    "color": "#888",
                    "textTransform": "uppercase",
                    "minWidth": "60px",
                },
            ),
            html.Div(content, style={"flex": "1"}),
            html.Button(
                "\u2715",
                id={"type": "drb-delete", "index": item.id},
                style=_DELETE_STYLE,
                title="Remove",
            ),
        ],
    )


def render_item_list(report: Report) -> list:
    """Render all report items as a list of Divs."""
    if not report.items:
        return [
            html.Div(
                "No items yet. Capture a chart to get started.",
                style={"color": "#999", "padding": "24px", "textAlign": "center"},
            )
        ]
    return [render_item(item) for item in report.items]
