# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Image-zip backend — collects images from a report into a single .zip.

Useful for "give me just the figures" workflows.  Non-image primitives
(headings, paragraphs, tables, page breaks) are silent no-ops.
"""

from __future__ import annotations

import io
import re
import zipfile

from dash_reportbuilder.export._base import decode_data_uri

# Map data-URI mime type to file extension.
_MIME_TO_EXT: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/webp": "webp",
}

_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _sanitize(name: str) -> str:
    """Sanitize *name* for safe use as a zip entry filename."""
    return _FILENAME_RE.sub("_", name).strip("_") or "image"


def _ext_from_data_uri(data_uri: str) -> str:
    """Infer the file extension from a data-URI mime type, defaulting to png."""
    if data_uri.startswith("data:") and ";" in data_uri:
        mime = data_uri[5:].split(";", 1)[0].strip().lower()
        return _MIME_TO_EXT.get(mime, "png")
    return "png"


class ImageZipBackend:
    """Builds a .zip containing every image from the report.

    Implements the :class:`~dash_reportbuilder.protocols.ReportBackend`
    protocol.  Only :meth:`add_image` produces output; the other
    primitives are silently ignored on the assumption that this backend
    is used purely for asset extraction.

    Filenames default to ``image_001.png``, ``image_002.png``, … and
    are taken from the ``title`` argument when provided (sanitized).

    Elements that want full control over what lands in the zip can use
    :meth:`add_raw` to write arbitrary bytes under a chosen filename.
    """

    def __init__(self) -> None:
        self._entries: list[tuple[str, bytes]] = []
        self._counter = 0
        self._used_names: set[str] = set()

    # ------------------------------------------------------------------
    # Generic primitives
    # ------------------------------------------------------------------

    def add_image(
        self,
        data_uri: str,
        *,
        title: str | None = None,
        caption: str | None = None,
        width_mm: float | None = None,
    ) -> None:
        # caption + width_mm are intentionally ignored — they're only
        # meaningful in document-style backends.
        self._counter += 1
        ext = _ext_from_data_uri(data_uri)
        if title:
            base = _sanitize(title)
        else:
            base = f"image_{self._counter:03d}"

        # Disambiguate collisions: foo, foo_2, foo_3, …
        name = f"{base}.{ext}"
        if name in self._used_names:
            i = 2
            while f"{base}_{i}.{ext}" in self._used_names:
                i += 1
            name = f"{base}_{i}.{ext}"
        self._used_names.add(name)

        self._entries.append((name, decode_data_uri(data_uri)))

    def add_heading(self, text: str, level: int = 1) -> None:
        return None

    def add_paragraph(self, text: str) -> None:
        return None

    def add_caption(self, text: str) -> None:
        return None

    def add_table(self, headers: list[str], rows: list[list[str]]) -> None:
        return None

    def add_page_break(self) -> None:
        return None

    # ------------------------------------------------------------------
    # Native escape hatch
    # ------------------------------------------------------------------

    def add_raw(self, filename: str, data: bytes) -> None:
        """Add an arbitrary file to the zip under *filename*."""
        if filename in self._used_names:
            raise ValueError(f"Duplicate filename in zip: {filename!r}")
        self._used_names.add(filename)
        self._entries.append((filename, data))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def build(self) -> bytes:
        """Return the .zip as bytes."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, data in self._entries:
                zf.writestr(name, data)
        return buf.getvalue()
