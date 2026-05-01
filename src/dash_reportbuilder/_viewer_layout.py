# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Pure layout construction for the report viewer — no callbacks."""

from __future__ import annotations

from dash import dcc, html

from dash_reportbuilder.elements import (
    CaptionElement,
    HeadingElement,
    ImageElement,
    PageBreakElement,
    ParagraphElement,
)
from dash_reportbuilder.model import Report
from dash_reportbuilder.protocols import ReportElement

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


def _classify(item: ReportElement) -> tuple[str, str, str | None]:
    """Return (kind, text, image_src).

    ``kind`` is one of: image, heading, paragraph, caption, page_break, custom.
    ``text`` is the editable text (empty for image/page_break/custom).
    ``image_src`` is the data URI for image items, otherwise None.
    """
    if isinstance(item, ImageElement):
        return "image", "", item.data_uri
    if isinstance(item, HeadingElement):
        return "heading", item.text, None
    if isinstance(item, ParagraphElement):
        return "paragraph", item.text, None
    if isinstance(item, CaptionElement):
        return "caption", item.text, None
    if isinstance(item, PageBreakElement):
        return "page_break", "", None
    return "custom", "", None


def render_item(item: ReportElement) -> html.Div:
    """Render a single report element with drag handle + content + delete."""
    kind, text, image_src = _classify(item)
    item_id = getattr(item, "id", "")

    if kind == "image":
        content = html.Img(
            src=image_src,
            style={"maxWidth": "200px", "maxHeight": "150px"},
        )
    elif kind == "page_break":
        content = html.Hr(style={"flex": "1", "margin": "0"})
    elif kind == "custom":
        content = html.Div(
            f"<{type(item).__name__}>",
            style={"flex": "1", "color": "#666", "fontStyle": "italic"},
        )
    else:
        content = dcc.Input(
            id={"type": "drb-text", "index": item_id},
            value=text,
            type="text",
            debounce=True,
            style={
                "flex": "1",
                "minHeight": "32px",
                "border": "1px solid #ddd",
                "borderRadius": "3px",
                "padding": "4px 8px",
                "fontWeight": "bold" if kind == "heading" else "normal",
                "fontStyle": "italic" if kind == "caption" else "normal",
                "fontSize": "16px" if kind == "heading" else "13px",
            },
        )

    type_label = kind.replace("_", " ").title()

    return html.Div(
        id=f"drb-item-{item_id}",
        style=_ITEM_STYLE,
        className="drb-item",
        children=[
            html.Span("≡", className="drb-drag-handle", style=_DRAG_HANDLE_STYLE),
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
                "✕",
                id={"type": "drb-delete", "index": item_id},
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
