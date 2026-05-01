# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Backwards-compatible ``export_pptx`` shim.

New code should use :class:`dash_reportbuilder.backends.PptxBackend`.
"""

from __future__ import annotations

from dash_reportbuilder.backends._pptx import PptxBackend
from dash_reportbuilder.export._base import PptxTemplate
from dash_reportbuilder.model import Report


def export_pptx(report: Report, template: PptxTemplate | None = None) -> bytes:
    """Export *report* to .pptx bytes (legacy API)."""
    backend = PptxBackend(template=template)
    return report.export(backend)
