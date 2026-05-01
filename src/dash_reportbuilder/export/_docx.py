# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Backwards-compatible ``export_docx`` shim.

New code should use :class:`dash_reportbuilder.backends.DocxBackend`.
"""

from __future__ import annotations

from dash_reportbuilder.backends._docx import DocxBackend
from dash_reportbuilder.export._base import DocxTemplate
from dash_reportbuilder.model import Report


def export_docx(report: Report, template: DocxTemplate | None = None) -> bytes:
    """Export *report* to .docx bytes (legacy API)."""
    backend = DocxBackend(template=template, title=report.title)
    return report.export(backend)
