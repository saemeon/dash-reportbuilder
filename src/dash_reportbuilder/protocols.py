# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Core protocols for the report-builder pipeline.

Three pieces:

- :class:`ReportElement` — anything that knows how to render itself into a backend.
- :class:`ReportBackend` — exposes generic primitives (``add_image``,
  ``add_heading``, etc.) plus a ``build`` method that finalizes the document.
- :class:`Report` (in :mod:`dash_reportbuilder.model`) — a list of elements.

Concrete backends typically also expose a format-specific escape hatch
(``append_raw`` for text-based backends, ``modify`` for object-based ones).
Elements that need full native control detect the backend with ``isinstance``
and use the escape hatch directly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ReportBackend(Protocol):
    """Backend that builds a report incrementally via generic primitives.

    Concrete backends (``DocxBackend``, ``PptxBackend``, ``TypstBackend``)
    implement these primitives and additionally expose their own raw escape
    hatch for native rendering.
    """

    def add_image(
        self,
        data_uri: str,
        *,
        title: str | None = None,
        caption: str | None = None,
        width_mm: float | None = None,
    ) -> None:
        """Add an image (base64 data-URI) with optional title/caption."""
        ...

    def add_heading(self, text: str, level: int = 1) -> None:
        """Add a heading at the given level (1 = top-level)."""
        ...

    def add_paragraph(self, text: str) -> None:
        """Add a body paragraph."""
        ...

    def add_caption(self, text: str) -> None:
        """Add a caption (centered, italic where supported)."""
        ...

    def add_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Add a simple table."""
        ...

    def add_page_break(self) -> None:
        """Add a page break (no-op where unsupported)."""
        ...

    def build(self) -> bytes:
        """Finalize and return the document as bytes."""
        ...


@runtime_checkable
class ReportElement(Protocol):
    """An item that can be rendered into a report.

    Implementations call methods on the backend.  For native rendering
    (e.g. raw Typst), use ``isinstance`` to narrow the backend type and
    call its escape hatch.
    """

    def render_into(self, backend: ReportBackend) -> None:
        """Render this element using the provided backend."""
        ...
