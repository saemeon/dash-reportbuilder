# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Typst (.typ) backend with PDF compilation."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from dash_reportbuilder.export._base import TypstTemplate, decode_data_uri


def _escape_typst(text: str) -> str:
    """Escape special Typst characters."""
    for ch in ("\\", "#", "$", "@", "<", ">", "[", "]", "{", "}"):
        text = text.replace(ch, "\\" + ch)
    return text


_DEFAULT_PREAMBLE = """\
#set page(margin: {page_margin})
#set text(font: "{font}", size: {font_size})
#set par(justify: true, leading: 0.65em)
#set heading(numbering: none)
#show heading.where(level: 1): it => {{
  set text(size: 24pt, weight: "bold")
  v(1em)
  it
  v(0.5em)
}}
#show heading.where(level: 2): it => {{
  set text(size: 16pt, weight: "bold")
  v(0.8em)
  it
  v(0.3em)
}}
#show figure: it => {{
  set align(center)
  it
  v(0.5em)
}}
"""


class TypstBackend:
    """Builds a Typst document and compiles it to PDF.

    Source is built incrementally as a list of lines.  Images are stored
    in-memory as raw bytes and written to disk alongside the source when
    :meth:`build` is called.

    Elements that need full Typst control can use :meth:`append_raw` to
    inject raw source.

    Parameters
    ----------
    template : TypstTemplate, optional
        Preamble settings.  When ``template.template`` is set (path or
        raw string), it replaces the default preamble.
    title : str, optional
        Top-level heading prepended after the preamble.
    """

    def __init__(
        self,
        template: TypstTemplate | None = None,
        *,
        title: str | None = None,
    ) -> None:
        self.template = template or TypstTemplate()
        self.title = title

        self._lines: list[str] = []
        # Images accumulate as (filename, bytes) tuples for build().
        self._images: list[tuple[str, bytes]] = []
        self._img_counter = 0

        # Preamble
        t = self.template
        if t.template:
            tmpl_path = Path(t.template)
            if tmpl_path.exists():
                self._lines.append(tmpl_path.read_text(encoding="utf-8"))
            else:
                self._lines.append(t.template)
        else:
            self._lines.append(
                _DEFAULT_PREAMBLE.format(
                    font=t.font, font_size=t.font_size, page_margin=t.page_margin
                )
            )
        self._lines.append("")

        if title:
            self._lines.append(f"= {_escape_typst(title)}")
            self._lines.append("")

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
        if title:
            self.add_heading(title, level=3)

        self._img_counter += 1
        fname = f"img_{self._img_counter}.png"
        self._images.append((fname, decode_data_uri(data_uri)))

        width = f"{width_mm}mm" if width_mm else "100%"
        if caption:
            self._lines.append("#figure(")
            self._lines.append(f'  image("{fname}", width: {width}),')
            self._lines.append(f"  caption: [{_escape_typst(caption)}],")
            self._lines.append(")")
        else:
            self._lines.append(f'#align(center, image("{fname}", width: {width}))')
        self._lines.append("")

    def add_heading(self, text: str, level: int = 1) -> None:
        prefix = "=" * level
        self._lines.append(f"{prefix} {_escape_typst(text)}")
        self._lines.append("")

    def add_paragraph(self, text: str) -> None:
        self._lines.append(_escape_typst(text))
        self._lines.append("")

    def add_caption(self, text: str) -> None:
        self._lines.append(f"#align(center, emph[{_escape_typst(text)}])")
        self._lines.append("")

    def add_table(self, headers: list[str], rows: list[list[str]]) -> None:
        n_cols = len(headers)
        cols_spec = ", ".join(["1fr"] * n_cols)
        self._lines.append("#table(")
        self._lines.append(f"  columns: ({cols_spec}),")
        for h in headers:
            self._lines.append(f"  [*{_escape_typst(h)}*],")
        for row in rows:
            for cell in row:
                self._lines.append(f"  [{_escape_typst(str(cell))}],")
        self._lines.append(")")
        self._lines.append("")

    def add_page_break(self) -> None:
        self._lines.append("#pagebreak()")
        self._lines.append("")

    # ------------------------------------------------------------------
    # Native escape hatch
    # ------------------------------------------------------------------

    def append_raw(self, source: str) -> None:
        """Inject raw Typst source.

        Lets elements use Typst features that aren't exposed via the
        generic primitives (custom layouts, math, complex tables, etc.).
        """
        self._lines.append(source)

    # ------------------------------------------------------------------
    # Source / PDF output
    # ------------------------------------------------------------------

    def build_source(self) -> str:
        """Return the full Typst source as a string."""
        return "\n".join(self._lines)

    def build(self) -> bytes:
        """Compile to PDF and return the bytes.

        Requires the ``typst`` CLI on ``PATH``.
        """
        source = self.build_source()
        with tempfile.TemporaryDirectory(prefix="drb_typst_") as tmpdir:
            tmppath = Path(tmpdir)
            for fname, data in self._images:
                (tmppath / fname).write_bytes(data)

            typ_path = tmppath / "report.typ"
            typ_path.write_text(source, encoding="utf-8")

            pdf_path = tmppath / "report.pdf"
            result = subprocess.run(
                ["typst", "compile", str(typ_path), str(pdf_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Typst compilation failed:\n{result.stderr}\n\n"
                    "Make sure the `typst` CLI is installed and on PATH.\n"
                    "Install: https://github.com/typst/typst#installation"
                )
            return pdf_path.read_bytes()
