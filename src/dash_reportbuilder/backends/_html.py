# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""HTML backend — produces a single-file, self-contained HTML document.

Images are embedded as base64 data-URIs, so the output is portable.
Elements that need full HTML control can use :meth:`append_raw_html`.
"""

from __future__ import annotations

import html
from pathlib import Path

from dash_reportbuilder.export._base import HtmlTemplate

_DEFAULT_STYLE = """\
<style>
  body {{
    font-family: {font};
    font-size: {font_size};
    line-height: 1.55;
    color: #1f2937;
    max-width: {page_max_width};
    margin: 2em auto;
    padding: 0 1em;
  }}
  h1, h2, h3 {{ color: {primary_color}; }}
  h1 {{ font-size: 2em; margin: 0.6em 0 0.4em; }}
  h2 {{ font-size: 1.4em; margin: 1.2em 0 0.4em; }}
  h3 {{ font-size: 1.1em; color: #64748b; margin: 1em 0 0.3em; }}
  p {{ margin: 0.6em 0; }}
  figure {{ margin: 1em 0; text-align: center; }}
  figure img {{ max-width: 100%; height: auto; }}
  figcaption {{
    font-size: 0.9em;
    color: #64748b;
    font-style: italic;
    margin-top: 0.4em;
    text-align: left;
  }}
  .drb-caption {{
    font-size: 0.9em;
    color: #64748b;
    font-style: italic;
    text-align: center;
    margin: 0.4em 0;
  }}
  .drb-page-break {{ page-break-after: always; }}
  table {{
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 0.4em 0.6em;
    text-align: left;
  }}
  th {{
    background: {primary_color};
    color: white;
    font-weight: bold;
  }}
</style>
"""


class HtmlBackend:
    """Builds a self-contained HTML document.

    Implements the :class:`~dash_reportbuilder.protocols.ReportBackend`
    protocol.  Images are embedded as base64 data-URIs, so the output
    file is portable.

    Elements that need full HTML control can use the
    :meth:`append_raw_html` escape hatch.

    Parameters
    ----------
    template : HtmlTemplate, optional
        Head/style settings.  When ``template.template`` is set (path or
        raw string), it replaces the default ``<style>`` block.
    title : str, optional
        Document title (used in ``<title>`` and as the top-level heading).
    """

    def __init__(
        self,
        template: HtmlTemplate | None = None,
        *,
        title: str | None = None,
    ) -> None:
        self.template = template or HtmlTemplate()
        self.title = title

        self._head_extra: list[str] = []
        self._body_lines: list[str] = []

        t = self.template
        if t.template:
            tmpl_path = Path(t.template)
            if tmpl_path.exists():
                self._head_extra.append(tmpl_path.read_text(encoding="utf-8"))
            else:
                self._head_extra.append(t.template)
        else:
            self._head_extra.append(
                _DEFAULT_STYLE.format(
                    font=t.font,
                    font_size=t.font_size,
                    primary_color=t.primary_color,
                    page_max_width=t.page_max_width,
                )
            )

        if title:
            self._body_lines.append(f"<h1>{html.escape(title)}</h1>")

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

        style = ""
        if width_mm:
            style = f' style="width: {width_mm}mm;"'

        if caption:
            self._body_lines.append("<figure>")
            self._body_lines.append(
                f'  <img src="{html.escape(data_uri, quote=True)}"{style} />'
            )
            self._body_lines.append(
                f"  <figcaption>{html.escape(caption)}</figcaption>"
            )
            self._body_lines.append("</figure>")
        else:
            self._body_lines.append(
                f'<img src="{html.escape(data_uri, quote=True)}"{style} />'
            )

    def add_heading(self, text: str, level: int = 1) -> None:
        lvl = max(1, min(6, level))
        self._body_lines.append(f"<h{lvl}>{html.escape(text)}</h{lvl}>")

    def add_paragraph(self, text: str) -> None:
        self._body_lines.append(f"<p>{html.escape(text)}</p>")

    def add_caption(self, text: str) -> None:
        self._body_lines.append(
            f'<p class="drb-caption">{html.escape(text)}</p>'
        )

    def add_table(self, headers: list[str], rows: list[list[str]]) -> None:
        self._body_lines.append("<table>")
        self._body_lines.append("  <thead><tr>")
        for h in headers:
            self._body_lines.append(f"    <th>{html.escape(h)}</th>")
        self._body_lines.append("  </tr></thead>")
        self._body_lines.append("  <tbody>")
        for row in rows:
            self._body_lines.append("    <tr>")
            for cell in row:
                self._body_lines.append(f"      <td>{html.escape(str(cell))}</td>")
            self._body_lines.append("    </tr>")
        self._body_lines.append("  </tbody>")
        self._body_lines.append("</table>")

    def add_page_break(self) -> None:
        self._body_lines.append('<div class="drb-page-break"></div>')

    # ------------------------------------------------------------------
    # Native escape hatch
    # ------------------------------------------------------------------

    def append_raw_html(self, source: str) -> None:
        """Inject raw HTML into the body.

        Lets elements use HTML/CSS features that aren't exposed via the
        generic primitives (custom layouts, embedded SVG, scripts, etc.).
        The string is inserted verbatim — the caller is responsible for
        escaping any user-provided content.
        """
        self._body_lines.append(source)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def build_source(self) -> str:
        """Return the full HTML document as a string."""
        head = "\n".join(self._head_extra)
        body = "\n".join(self._body_lines)
        title = html.escape(self.title) if self.title else "Report"
        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            f"  <title>{title}</title>\n"
            f"{head}\n"
            "</head>\n"
            "<body>\n"
            f"{body}\n"
            "</body>\n"
            "</html>\n"
        )

    def build(self) -> bytes:
        """Return the HTML document as UTF-8 bytes."""
        return self.build_source().encode("utf-8")
