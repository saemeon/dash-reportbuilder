# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Typst source (.typ) generation and PDF compilation."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from dash_reportbuilder.export._base import TypstTemplate, decode_data_uri
from dash_reportbuilder.model import ItemType, Report


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


def export_typst(report: Report, template: TypstTemplate | None = None) -> str:
    """Export *report* to Typst source (.typ).

    When *template* provides a ``template`` string or path, it replaces
    the default preamble.  A template path is read from disk; a string
    is used directly.  The default preamble sets page margins, font,
    paragraph justification, and heading styles.

    Images are referenced as ``image("img_N.png")`` — place them
    alongside the .typ file, or use :func:`export_pdf` which handles
    this automatically.
    """
    t = template or TypstTemplate()

    lines: list[str] = []

    # Preamble
    if t.template:
        tmpl_path = Path(t.template)
        if tmpl_path.exists():
            lines.append(tmpl_path.read_text(encoding="utf-8"))
        else:
            lines.append(t.template)
    else:
        lines.append(
            _DEFAULT_PREAMBLE.format(
                font=t.font, font_size=t.font_size, page_margin=t.page_margin
            )
        )

    lines.append("")

    # Title
    lines.append(f"= {_escape_typst(report.title)}")
    lines.append("")

    img_counter = 0
    for item in report.items:
        if item.type == ItemType.IMAGE:
            img_counter += 1
            fname = f"img_{img_counter}.png"
            caption = item.meta.get("caption")
            if caption:
                # Use Typst figure with caption
                lines.append("#figure(")
                lines.append(f'  image("{fname}", width: 100%),')
                lines.append(f"  caption: [{_escape_typst(caption)}],")
                lines.append(")")
            else:
                lines.append(f'#align(center, image("{fname}", width: 100%))')
            lines.append("")

        elif item.type == ItemType.HEADING:
            level = item.meta.get("heading_level", 2)
            prefix = "=" * level
            lines.append(f"{prefix} {_escape_typst(item.content)}")
            lines.append("")

        elif item.type == ItemType.PARAGRAPH:
            lines.append(_escape_typst(item.content))
            lines.append("")

        elif item.type == ItemType.CAPTION:
            lines.append(f"#align(center, emph[{_escape_typst(item.content)}])")
            lines.append("")

        elif item.type == ItemType.PAGE_BREAK:
            lines.append("#pagebreak()")
            lines.append("")

    return "\n".join(lines)


def export_pdf(report: Report, template: TypstTemplate | None = None) -> bytes:
    """Export *report* to PDF by compiling Typst source.

    Requires the ``typst`` CLI to be on ``PATH``.
    """
    source = export_typst(report, template=template)

    with tempfile.TemporaryDirectory(prefix="drb_typst_") as tmpdir:
        tmppath = Path(tmpdir)

        # Write images
        img_counter = 0
        for item in report.items:
            if item.type == ItemType.IMAGE:
                img_counter += 1
                fname = f"img_{img_counter}.png"
                img_bytes = decode_data_uri(item.content)
                (tmppath / fname).write_bytes(img_bytes)

        # Write source
        typ_path = tmppath / "report.typ"
        typ_path.write_text(source, encoding="utf-8")

        # Compile
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
