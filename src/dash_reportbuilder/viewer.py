# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Report viewer component: sortable item list with text editing and export."""

from __future__ import annotations

from typing import Any

import dash
from dash import Input, Output, State, dcc, html
from dash_capture._wizard import build_wizard

from dash_reportbuilder._ids import _new_id
from dash_reportbuilder._js import ensure_assets
from dash_reportbuilder._viewer_callbacks import register_viewer_callbacks
from dash_reportbuilder._viewer_layout import render_item_list
from dash_reportbuilder.store import ReportStore

_BTN_STYLE = {
    "padding": "4px 12px",
    "border": "1px solid #ccc",
    "borderRadius": "4px",
    "background": "#fff",
    "cursor": "pointer",
    "fontSize": "12px",
}


def report_viewer(
    store: ReportStore,
    session_id: str = "default",
    export_formats: list[str] | None = None,
    templates: dict[str, Any] | None = None,
    trigger: str | Any = "Report Builder",
    dialog_style: dict | None = None,
) -> html.Div:
    """Sortable report viewer wrapped in a wizard overlay.

    Opens as a modal dialog triggered by a button click.  Drag-and-drop
    reordering is handled purely in the browser by SortableJS.  The
    current DOM order is read at export time via a clientside callback,
    so no Dash round-trips happen during dragging.

    Parameters
    ----------
    store : ReportStore
        The report store backing this viewer.
    session_id : str
        Session identifier (default ``"default"``).
    export_formats : list[str], optional
        Enabled export formats.  Defaults to ``["docx", "pptx", "typst", "pdf"]``.
    templates : dict, optional
        Export templates keyed by format name.
    trigger : str or component, optional
        Button label or custom Dash component that opens the wizard.
        Defaults to ``"Report Builder"``.
    dialog_style : dict, optional
        CSS overrides for the wizard dialog.

    Returns
    -------
    html.Div
    """
    if export_formats is None:
        export_formats = ["docx", "pptx", "typst", "pdf"]

    ensure_assets()

    uid = _new_id("viewer")
    list_id = f"{uid}_list"
    version_id = f"{uid}_version"
    order_id = f"{uid}_order"
    export_download_id = f"{uid}_dl"
    export_btn_id = f"{uid}_export_btn"
    export_format_id = f"{uid}_export_fmt"
    add_heading_id = f"{uid}_add_h"
    add_paragraph_id = f"{uid}_add_p"
    add_caption_id = f"{uid}_add_cap"
    add_pagebreak_id = f"{uid}_add_pb"
    title_input_id = f"{uid}_title"
    refresh_interval_id = f"{uid}_refresh"

    report = store.get(session_id)

    format_options = []
    fmt_labels = {
        "docx": "Word (.docx)",
        "pptx": "PowerPoint (.pptx)",
        "typst": "Typst (.typ)",
        "pdf": "PDF",
        "html": "HTML (.html)",
    }
    for fmt in export_formats:
        format_options.append({"label": fmt_labels.get(fmt, fmt), "value": fmt})

    body = html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "12px",
        },
        children=[
            # Title
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                children=[
                    html.Label(
                        "Report:", style={"fontWeight": "bold", "fontSize": "14px"}
                    ),
                    dcc.Input(
                        id=title_input_id,
                        value=report.title,
                        style={
                            "flex": "1",
                            "border": "1px solid #ddd",
                            "borderRadius": "3px",
                            "padding": "4px 8px",
                        },
                        debounce=True,
                    ),
                ],
            ),
            # Item list (SortableJS handles visual reordering in the browser)
            html.Div(
                id=list_id,
                className="drb-sortable-list",
                children=render_item_list(report),
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "6px",
                    "minHeight": "60px",
                    "maxHeight": "50vh",
                    "overflowY": "auto",
                },
            ),
            # Add toolbar
            html.Div(
                style={"display": "flex", "gap": "6px", "flexWrap": "wrap"},
                children=[
                    html.Button("+ Heading", id=add_heading_id, style=_BTN_STYLE),
                    html.Button("+ Paragraph", id=add_paragraph_id, style=_BTN_STYLE),
                    html.Button("+ Caption", id=add_caption_id, style=_BTN_STYLE),
                    html.Button("+ Page Break", id=add_pagebreak_id, style=_BTN_STYLE),
                ],
            ),
            # Export toolbar
            html.Div(
                style={"display": "flex", "gap": "8px", "alignItems": "center"},
                children=[
                    dcc.Dropdown(
                        id=export_format_id,
                        options=format_options,
                        value=export_formats[0] if export_formats else None,
                        clearable=False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                    html.Button(
                        "Export",
                        id=export_btn_id,
                        style={**_BTN_STYLE, "fontWeight": "bold"},
                    ),
                    dcc.Download(id=export_download_id),
                ],
            ),
            # Hidden ref for JS to find the order store ID
            html.Span(
                order_id,
                className="drb-order-store-ref",
                style={"display": "none"},
            ),
            # Hidden infra
            dcc.Store(id=version_id, data=0),
            dcc.Store(id=order_id),
            dcc.Interval(id=refresh_interval_id, interval=1000, n_intervals=0),
        ],
    )

    # Wrap in wizard overlay
    default_dialog = {
        "minWidth": "700px",
        "maxWidth": "900px",
        "maxHeight": "85vh",
        "overflowY": "auto",
    }
    wizard = build_wizard(
        wizard_id=uid,
        body=body,
        trigger=trigger,
        title="Report Builder",
        dialog_style={**default_dialog, **(dialog_style or {})},
    )

    # Clientside callback: Export click → read current DOM order → write
    # to order store.  The server-side export callback chains off
    # Input(order_id, "data").  We include Date.now() so the store
    # value always changes, ensuring the server callback fires even if
    # the order hasn't changed since the last export.
    dash.clientside_callback(
        f"""
        function(n_clicks) {{
            if (!n_clicks) return window.dash_clientside.no_update;
            var el = document.getElementById("{list_id}");
            if (!el) return window.dash_clientside.no_update;
            var ids = [];
            el.querySelectorAll(".drb-item").forEach(function(item) {{
                var domId = item.id || "";
                if (domId.startsWith("drb-item-")) {{
                    ids.push(domId.substring(9));
                }}
            }});
            return {{order: ids, ts: Date.now()}};
        }}
        """,
        Output(order_id, "data"),
        Input(export_btn_id, "n_clicks"),
        prevent_initial_call=True,
    )

    # Register all viewer callbacks
    register_viewer_callbacks(
        store=store,
        session_id=session_id,
        list_id=list_id,
        version_id=version_id,
        order_id=order_id,
        export_download_id=export_download_id,
        export_btn_id=export_btn_id,
        export_format_id=export_format_id,
        add_heading_id=add_heading_id,
        add_paragraph_id=add_paragraph_id,
        add_caption_id=add_caption_id,
        add_pagebreak_id=add_pagebreak_id,
        title_input_id=title_input_id,
        refresh_interval_id=refresh_interval_id,
        templates=templates,
        open_input=wizard.open_input,
    )

    return wizard.div
