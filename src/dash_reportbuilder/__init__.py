# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Capture, assemble, and export reports from Plotly Dash applications."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dash-reportbuilder")
except PackageNotFoundError:
    __version__ = "unknown"

from dash_reportbuilder.capture import get_version, report_action
from dash_reportbuilder.export._base import DocxTemplate, PptxTemplate, TypstTemplate
from dash_reportbuilder.model import ItemType, Report, ReportItem
from dash_reportbuilder.store import FileStore, MemoryStore, ReportStore
from dash_reportbuilder.viewer import report_viewer

__all__ = [
    # model
    "Report",
    "ReportItem",
    "ItemType",
    # store
    "ReportStore",
    "MemoryStore",
    "FileStore",
    # capture integration
    "report_action",
    "get_version",
    # viewer
    "report_viewer",
    # templates
    "DocxTemplate",
    "PptxTemplate",
    "TypstTemplate",
]
