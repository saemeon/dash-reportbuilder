# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Callback registration for the report viewer."""

from __future__ import annotations

from typing import Any

import dash
from dash import ALL, Input, Output, State, dcc

from dash_reportbuilder._viewer_layout import render_item_list
from dash_reportbuilder.backends import (
    DocxBackend,
    HtmlBackend,
    ImageZipBackend,
    PptxBackend,
    TypstBackend,
)
from dash_reportbuilder.capture import _bump_version, get_version
from dash_reportbuilder.elements import (
    CaptionElement,
    HeadingElement,
    PageBreakElement,
    ParagraphElement,
)
from dash_reportbuilder.store import ReportStore


def register_viewer_callbacks(
    *,
    store: ReportStore,
    session_id: str,
    list_id: str,
    version_id: str,
    order_id: str,
    export_download_id: str,
    export_btn_id: str,
    export_format_id: str,
    add_heading_id: str,
    add_paragraph_id: str,
    add_caption_id: str,
    add_pagebreak_id: str,
    title_input_id: str,
    refresh_interval_id: str,
    templates: dict[str, Any] | None = None,
    open_input: Input | None = None,
) -> None:
    """Register all viewer callbacks."""
    # ---- Arm/disarm polling when wizard opens/closes ----
    if open_input is not None:

        @dash.callback(
            Output(refresh_interval_id, "disabled"),
            open_input,
        )
        def arm_polling(is_open):
            return not is_open

    # ---- Refresh: re-render list when version changes ----
    # The version is only bumped on structural changes (add/delete),
    # never on drag-reorder, so this won't undo drag order.
    @dash.callback(
        Output(list_id, "children"),
        Input(version_id, "data"),
    )
    def refresh_viewer(version):
        report = store.get(session_id)
        return render_item_list(report)

    # ---- Polling: detect external additions (e.g. from capture action) ----
    # We track the item count to avoid re-rendering after drag reorder.
    # Only triggers a re-render when the number of items changes (add/delete),
    # not when the order changes — preserving the user's drag order in the DOM.
    _last_item_count: dict[str, int] = {"count": len(store.get(session_id).items)}

    @dash.callback(
        Output(version_id, "data"),
        Input(refresh_interval_id, "n_intervals"),
        State(version_id, "data"),
    )
    def poll_version(n_intervals, last_version):
        report = store.get(session_id)
        current_count = len(report.items)
        if current_count == _last_item_count["count"]:
            return dash.no_update
        _last_item_count["count"] = current_count
        current = get_version(store)
        return current

    # ---- Delete item ----
    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input({"type": "drb-delete", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def delete_item(n_clicks_list):
        if not any(n_clicks_list):
            return dash.no_update
        triggered = dash.ctx.triggered_id
        if triggered is None:
            return dash.no_update
        item_id = triggered["index"]
        report = store.get(session_id)
        report.remove(item_id)
        store.put(session_id, report)
        return _bump_version(store)

    # ---- Update text item ----
    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input({"type": "drb-text", "index": ALL}, "value"),
        prevent_initial_call=True,
    )
    def update_text(values):
        triggered = dash.ctx.triggered_id
        if triggered is None:
            return dash.no_update
        item_id = triggered["index"]
        prop_ids = dash.ctx.inputs_list[0]
        for prop_info, val in zip(prop_ids, values, strict=False):
            if prop_info["id"]["index"] == item_id:
                report = store.get(session_id)
                report.update_item(item_id, text=val or "")
                store.put(session_id, report)
                return dash.no_update
        return dash.no_update

    # ---- Add text items ----
    def _add(element) -> int:
        report = store.get(session_id)
        report.add(element)
        store.put(session_id, report)
        return _bump_version(store)

    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input(add_heading_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def add_heading(n):
        if not n:
            return dash.no_update
        return _add(HeadingElement(text="Section Title", level=2))

    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input(add_paragraph_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def add_paragraph(n):
        if not n:
            return dash.no_update
        return _add(ParagraphElement(text=""))

    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input(add_caption_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def add_caption(n):
        if not n:
            return dash.no_update
        return _add(CaptionElement(text=""))

    @dash.callback(
        Output(version_id, "data", allow_duplicate=True),
        Input(add_pagebreak_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def add_pagebreak(n):
        if not n:
            return dash.no_update
        return _add(PageBreakElement())

    # ---- Update title ----
    @dash.callback(
        Output(title_input_id, "id"),
        Input(title_input_id, "value"),
        prevent_initial_call=True,
    )
    def update_title(title):
        report = store.get(session_id)
        report.title = title or "Untitled Report"
        store.put(session_id, report)
        return dash.no_update

    # ---- Export ----
    # Two-step chain:
    #   1. Clientside (in viewer.py): Export click → reads DOM order
    #      → writes to order_id store
    #   2. Server (here): order_id change → reorder + export
    @dash.callback(
        Output(export_download_id, "data"),
        Input(order_id, "data"),
        State(export_format_id, "value"),
        prevent_initial_call=True,
    )
    def export_report(order_data, fmt):
        if not order_data:
            return dash.no_update
        # order_data is {order: [...ids], ts: timestamp}
        dom_order = (
            order_data.get("order") if isinstance(order_data, dict) else order_data
        )
        if not dom_order:
            return dash.no_update
        report = store.get(session_id)
        if not report.items:
            return dash.no_update

        # Apply the DOM order to the report before exporting
        report.reorder(dom_order)
        store.put(session_id, report)

        template = (templates or {}).get(fmt)

        if fmt == "docx":
            backend = DocxBackend(template=template, title=report.title)
            data = report.export(backend)
            return dcc.send_bytes(data, f"{report.title}.docx")
        elif fmt == "pptx":
            backend = PptxBackend(template=template)
            data = report.export(backend)
            return dcc.send_bytes(data, f"{report.title}.pptx")
        elif fmt == "typst":
            backend = TypstBackend(template=template, title=report.title)
            for item in report.items:
                item.render_into(backend)
            return dcc.send_string(backend.build_source(), f"{report.title}.typ")
        elif fmt == "pdf":
            backend = TypstBackend(template=template, title=report.title)
            data = report.export(backend)
            return dcc.send_bytes(data, f"{report.title}.pdf")
        elif fmt == "html":
            backend = HtmlBackend(template=template, title=report.title)
            for item in report.items:
                item.render_into(backend)
            return dcc.send_string(backend.build_source(), f"{report.title}.html")
        elif fmt == "images":
            backend = ImageZipBackend()
            data = report.export(backend)
            return dcc.send_bytes(data, f"{report.title}.zip")
        return dash.no_update
