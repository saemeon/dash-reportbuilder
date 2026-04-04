# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Tests for viewer layout rendering (no callbacks / no running Dash app)."""

from dash import dcc, html

from dash_reportbuilder._viewer_layout import render_item, render_item_list
from dash_reportbuilder.model import ItemType, Report, ReportItem

TINY_PNG_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


class TestRenderItemImage:
    """render_item for IMAGE items."""

    def test_image_renders_img_tag(self):
        item = ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI, id="img1")
        div = render_item(item)
        assert isinstance(div, html.Div)
        # Find the Img among children
        imgs = _find_components(div, html.Img)
        assert len(imgs) == 1
        assert imgs[0].src == TINY_PNG_URI

    def test_image_has_delete_button(self):
        item = ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI, id="img1")
        div = render_item(item)
        buttons = _find_components(div, html.Button)
        assert len(buttons) >= 1
        # Delete button has matching index
        delete_btn = [b for b in buttons if getattr(b, "id", None) == {"type": "drb-delete", "index": "img1"}]
        assert len(delete_btn) == 1

    def test_image_has_drag_handle(self):
        item = ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI, id="img1")
        div = render_item(item)
        spans = _find_components(div, html.Span)
        drag_handles = [s for s in spans if getattr(s, "className", None) == "drb-drag-handle"]
        assert len(drag_handles) == 1

    def test_image_div_id(self):
        item = ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI, id="img1")
        div = render_item(item)
        assert div.id == "drb-item-img1"


class TestRenderItemHeading:
    """render_item for HEADING items."""

    def test_heading_renders_input(self):
        item = ReportItem(type=ItemType.HEADING, content="My Heading", id="h1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert len(inputs) == 1
        assert inputs[0].value == "My Heading"

    def test_heading_input_bold(self):
        item = ReportItem(type=ItemType.HEADING, content="Bold", id="h1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert inputs[0].style["fontWeight"] == "bold"

    def test_heading_type_label(self):
        item = ReportItem(type=ItemType.HEADING, content="H", id="h1")
        div = render_item(item)
        spans = _find_components(div, html.Span)
        labels = [s for s in spans if hasattr(s, "children") and s.children == "Heading"]
        assert len(labels) == 1


class TestRenderItemParagraph:
    """render_item for PARAGRAPH items."""

    def test_paragraph_renders_input(self):
        item = ReportItem(type=ItemType.PARAGRAPH, content="Body text", id="p1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert len(inputs) == 1
        assert inputs[0].value == "Body text"

    def test_paragraph_not_bold(self):
        item = ReportItem(type=ItemType.PARAGRAPH, content="Text", id="p1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert inputs[0].style["fontWeight"] == "normal"

    def test_paragraph_not_italic(self):
        item = ReportItem(type=ItemType.PARAGRAPH, content="Text", id="p1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert inputs[0].style["fontStyle"] == "normal"


class TestRenderItemCaption:
    """render_item for CAPTION items."""

    def test_caption_italic(self):
        item = ReportItem(type=ItemType.CAPTION, content="Fig 1", id="c1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert len(inputs) == 1
        assert inputs[0].style["fontStyle"] == "italic"

    def test_caption_type_label(self):
        item = ReportItem(type=ItemType.CAPTION, content="Cap", id="c1")
        div = render_item(item)
        spans = _find_components(div, html.Span)
        labels = [s for s in spans if hasattr(s, "children") and s.children == "Caption"]
        assert len(labels) == 1


class TestRenderItemPageBreak:
    """render_item for PAGE_BREAK items."""

    def test_page_break_renders_hr(self):
        item = ReportItem(type=ItemType.PAGE_BREAK, id="pb1")
        div = render_item(item)
        hrs = _find_components(div, html.Hr)
        assert len(hrs) == 1

    def test_page_break_no_text_input(self):
        item = ReportItem(type=ItemType.PAGE_BREAK, id="pb1")
        div = render_item(item)
        inputs = _find_components(div, dcc.Input)
        assert len(inputs) == 0


class TestRenderItemList:
    """render_item_list behaviour."""

    def test_empty_report_shows_placeholder(self):
        report = Report()
        children = render_item_list(report)
        assert len(children) == 1
        assert isinstance(children[0], html.Div)
        assert "No items" in children[0].children

    def test_single_item(self):
        report = Report()
        report.append(ReportItem(type=ItemType.HEADING, content="H", id="h1"))
        children = render_item_list(report)
        assert len(children) == 1
        assert children[0].id == "drb-item-h1"

    def test_multiple_items_preserves_order(self):
        report = Report()
        report.append(ReportItem(type=ItemType.HEADING, content="A", id="a"))
        report.append(ReportItem(type=ItemType.PARAGRAPH, content="B", id="b"))
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI, id="c"))
        children = render_item_list(report)
        assert len(children) == 3
        assert children[0].id == "drb-item-a"
        assert children[1].id == "drb-item-b"
        assert children[2].id == "drb-item-c"

    def test_all_item_types_render(self):
        """Every ItemType renders without error."""
        report = Report()
        for i, it_type in enumerate(ItemType):
            content = TINY_PNG_URI if it_type == ItemType.IMAGE else f"content-{i}"
            report.append(ReportItem(type=it_type, content=content, id=f"id{i}"))
        children = render_item_list(report)
        assert len(children) == len(ItemType)


# --- Helpers ---


def _find_components(component, comp_type):
    """Recursively find all instances of comp_type within a Dash component tree."""
    found = []
    if isinstance(component, comp_type):
        found.append(component)
    children = getattr(component, "children", None)
    if children is None:
        return found
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if hasattr(child, "children") or isinstance(child, comp_type):
            found.extend(_find_components(child, comp_type))
    return found
