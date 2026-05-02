# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Capture, assemble, and export reports from Plotly Dash applications."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dash-reportbuilder")
except PackageNotFoundError:
    __version__ = "unknown"

from dash_reportbuilder.capture import get_version, report_action
from dash_reportbuilder.elements import (
    CaptionElement,
    HeadingElement,
    ImageElement,
    PageBreakElement,
    ParagraphElement,
    element_from_dict,
    register_element_type,
)
from dash_reportbuilder.backends import (
    DocxBackend,
    HtmlBackend,
    ImageZipBackend,
    PptxBackend,
    TypstBackend,
)
from dash_reportbuilder.export._base import (
    DocxTemplate,
    HtmlTemplate,
    PptxTemplate,
    TypstTemplate,
)
from dash_reportbuilder.model import Report
from dash_reportbuilder.protocols import ReportBackend, ReportElement
from dash_reportbuilder.store import FileStore, MemoryStore, ReportStore
from dash_reportbuilder.templates import example_template_path
from dash_reportbuilder.viewer import report_viewer

__all__ = [
    # model + protocols
    "Report",
    "ReportElement",
    "ReportBackend",
    # elements
    "HeadingElement",
    "ParagraphElement",
    "ImageElement",
    "CaptionElement",
    "PageBreakElement",
    "element_from_dict",
    "register_element_type",
    # store
    "ReportStore",
    "MemoryStore",
    "FileStore",
    # capture integration
    "report_action",
    "get_version",
    # viewer
    "report_viewer",
    # backends
    "DocxBackend",
    "PptxBackend",
    "TypstBackend",
    "HtmlBackend",
    "ImageZipBackend",
    # templates
    "DocxTemplate",
    "PptxTemplate",
    "TypstTemplate",
    "HtmlTemplate",
    "example_template_path",
]
