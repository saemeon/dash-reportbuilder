# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Concrete :class:`~dash_reportbuilder.protocols.ReportBackend` implementations."""

from dash_reportbuilder.backends._docx import DocxBackend
from dash_reportbuilder.backends._html import HtmlBackend
from dash_reportbuilder.backends._pptx import PptxBackend
from dash_reportbuilder.backends._typst import TypstBackend

__all__ = ["DocxBackend", "HtmlBackend", "PptxBackend", "TypstBackend"]
