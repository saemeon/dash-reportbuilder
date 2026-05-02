# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Shared export helpers and template dataclasses."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field


@dataclass
class DocxTemplate:
    """Template settings for Word export.

    Parameters
    ----------
    template_path : str, optional
        Path to a .docx file to use as base template.  All styles,
        headers, footers, margins, and cover pages from the template
        are preserved — report items are appended after the template
        content.
    font : str
        Body font name.
    font_size_pt : int
        Body font size in points.
    heading_font_size_pt : int
        Heading font size in points.
    image_width_inches : float
        Maximum image width in inches.
    margin_inches : float
        Page margin in inches (applied only when no template_path).
    """

    template_path: str | None = None
    font: str = "Calibri"
    font_size_pt: int = 11
    heading_font_size_pt: int = 14
    image_width_inches: float = 6.0
    margin_inches: float = 1.0


@dataclass
class PptxTemplate:
    """Template settings for PowerPoint export.

    Parameters
    ----------
    template_path : str, optional
        Path to a .pptx file to use as base template.  All slide
        masters, layouts, and theme colors are preserved.
    image_layout_index : int
        Slide layout index for image slides (default 6 = blank).
    """

    template_path: str | None = None
    image_layout_index: int = 6


@dataclass
class HtmlTemplate:
    """Template settings for HTML export.

    Parameters
    ----------
    template : str, optional
        HTML head/style block.  Can be:
        - A path to an .html file (read from disk if it exists; the
          contents are inserted verbatim into ``<head>``)
        - A raw HTML/CSS string (inserted verbatim into ``<head>``)
        When omitted, a sensible default ``<style>`` block is generated
        from the *font*, *font_size*, and *primary_color* fields.
    font : str
        Body font family (CSS).
    font_size : str
        Body font size (CSS, e.g. ``"11pt"``).
    primary_color : str
        Heading / accent color (CSS color).
    page_max_width : str
        Maximum content width (CSS, e.g. ``"800px"``).
    """

    template: str | None = None
    font: str = "Calibri, Helvetica, Arial, sans-serif"
    font_size: str = "11pt"
    primary_color: str = "#2563eb"
    page_max_width: str = "800px"


@dataclass
class TypstTemplate:
    """Template settings for Typst/PDF export.

    Parameters
    ----------
    template : str, optional
        Typst preamble.  Can be:
        - A path to a .typ file (read from disk if it exists)
        - A raw Typst string (used directly)
        When omitted, a sensible default preamble is generated from
        the *font* and *font_size* fields.
    font : str
        Font name used in the default preamble.
    font_size : str
        Font size used in the default preamble (e.g. ``"11pt"``).
    page_margin : str
        Page margin (e.g. ``"2cm"``).  Used only in the default preamble.
    """

    template: str | None = None
    font: str = "Calibri"
    font_size: str = "11pt"
    page_margin: str = "2cm"


def decode_data_uri(data_uri: str) -> bytes:
    """Decode a base64 data-URI to raw bytes."""
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]
    return base64.b64decode(data_uri)
