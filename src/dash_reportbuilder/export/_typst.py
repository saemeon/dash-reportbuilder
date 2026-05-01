# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Backwards-compatible ``export_typst`` / ``export_pdf`` shims.

New code should use :class:`dash_reportbuilder.backends.TypstBackend`.
"""

from __future__ import annotations

from dash_reportbuilder.backends._typst import TypstBackend, _escape_typst  # noqa: F401
from dash_reportbuilder.export._base import TypstTemplate
from dash_reportbuilder.model import Report


def export_typst(report: Report, template: TypstTemplate | None = None) -> str:
    """Return the Typst source as a string (legacy API)."""
    backend = TypstBackend(template=template, title=report.title)
    for item in report.items:
        item.render_into(backend)
    return backend.build_source()


def export_pdf(report: Report, template: TypstTemplate | None = None) -> bytes:
    """Compile *report* to PDF bytes (legacy API)."""
    backend = TypstBackend(template=template, title=report.title)
    return report.export(backend)
