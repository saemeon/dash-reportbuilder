# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Tests for HtmlBackend."""

from dash_reportbuilder import (
    CaptionElement,
    HeadingElement,
    HtmlBackend,
    HtmlTemplate,
    ImageElement,
    PageBreakElement,
    ParagraphElement,
    Report,
    example_template_path,
)

TINY_PNG_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


def _export(report: Report, *, template: HtmlTemplate | None = None) -> str:
    backend = HtmlBackend(template=template, title=report.title)
    for item in report.items:
        item.render_into(backend)
    return backend.build_source()


class TestBuildAndStructure:
    """Output is a valid-looking, self-contained HTML document."""

    def test_produces_str(self, sample_report):
        result = _export(sample_report)
        assert isinstance(result, str)

    def test_build_returns_utf8_bytes(self, sample_report):
        backend = HtmlBackend(title="T")
        for item in sample_report.items:
            item.render_into(backend)
        data = backend.build()
        assert isinstance(data, bytes)
        assert data.decode("utf-8").startswith("<!DOCTYPE html>")

    def test_has_doctype_and_html_tags(self, sample_report):
        result = _export(sample_report)
        assert result.startswith("<!DOCTYPE html>")
        assert "<html" in result
        assert "</html>" in result

    def test_title_appears_in_title_and_h1(self):
        report = Report(title="Quarterly Review")
        result = _export(report)
        assert "<title>Quarterly Review</title>" in result
        assert "<h1>Quarterly Review</h1>" in result

    def test_default_style_block_present(self):
        report = Report(title="T")
        result = _export(report)
        assert "<style>" in result
        assert "</style>" in result


class TestElements:
    """Each element type renders to the expected HTML."""

    def test_heading_levels_clamp(self):
        report = Report(title="T")
        report.append(HeadingElement(text="A", level=2))
        report.append(HeadingElement(text="B", level=99))
        result = _export(report)
        assert "<h2>A</h2>" in result
        assert "<h6>B</h6>" in result

    def test_paragraph(self):
        report = Report(title="T")
        report.append(ParagraphElement(text="Hello world"))
        result = _export(report)
        assert "<p>Hello world</p>" in result

    def test_caption_class(self):
        report = Report(title="T")
        report.append(CaptionElement(text="Figure 1"))
        result = _export(report)
        assert '<p class="drb-caption">Figure 1</p>' in result

    def test_image_without_caption(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI))
        result = _export(report)
        assert TINY_PNG_URI in result
        assert "<figcaption>" not in result

    def test_image_with_caption_uses_figure(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI, caption="Chart 1"))
        result = _export(report)
        assert "<figure>" in result
        assert "<figcaption>Chart 1</figcaption>" in result

    def test_image_width_mm(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI, width_mm=120))
        result = _export(report)
        assert 'style="width: 120mm;"' in result

    def test_page_break_div(self):
        report = Report(title="T")
        report.append(PageBreakElement())
        result = _export(report)
        assert '<div class="drb-page-break"></div>' in result


class TestEscaping:
    """User-supplied text is HTML-escaped."""

    def test_paragraph_escapes_html(self):
        report = Report(title="T")
        report.append(ParagraphElement(text="<script>alert(1)</script>"))
        result = _export(report)
        assert "<script>alert(1)</script>" not in result
        assert "&lt;script&gt;" in result

    def test_heading_escapes(self):
        report = Report(title="T")
        report.append(HeadingElement(text="A & B", level=2))
        result = _export(report)
        assert "<h2>A &amp; B</h2>" in result

    def test_title_escapes(self):
        report = Report(title="<evil>")
        result = _export(report)
        assert "<title>&lt;evil&gt;</title>" in result


class TestEscapeHatch:
    """append_raw_html() injects content verbatim."""

    def test_append_raw_html_inserts_verbatim(self):
        backend = HtmlBackend(title="T")
        backend.append_raw_html('<div class="custom">hi</div>')
        result = backend.build_source()
        assert '<div class="custom">hi</div>' in result


class TestTable:
    """add_table() renders a <table>."""

    def test_table_headers_and_rows(self):
        backend = HtmlBackend(title="T")
        backend.add_table(["Year", "Value"], [["2024", "10"], ["2025", "20"]])
        result = backend.build_source()
        assert "<table>" in result
        assert "<th>Year</th>" in result
        assert "<th>Value</th>" in result
        assert "<td>2024</td>" in result
        assert "<td>20</td>" in result


class TestTemplate:
    """HtmlTemplate.template can be a raw string or a path."""

    def test_template_default_uses_primary_color(self):
        template = HtmlTemplate(primary_color="#ff0000")
        result = _export(Report(title="T"), template=template)
        assert "#ff0000" in result

    def test_template_raw_string_replaces_default(self):
        custom = "<style>body { color: rebeccapurple; }</style>"
        template = HtmlTemplate(template=custom)
        result = _export(Report(title="T"), template=template)
        assert custom in result
        # Default style markers should NOT appear
        assert "Calibri" not in result

    def test_template_path_is_read_from_disk(self, tmp_path):
        css_file = tmp_path / "brand.html"
        css_file.write_text("<style>body { background: aqua; }</style>")
        template = HtmlTemplate(template=str(css_file))
        result = _export(Report(title="T"), template=template)
        assert "background: aqua" in result

    def test_example_html_template_loads(self):
        path = example_template_path("html")
        template = HtmlTemplate(template=str(path))
        result = _export(Report(title="T"), template=template)
        assert "--brand-primary" in result


class TestEmptyReport:
    """Empty report still produces a valid document."""

    def test_empty_report_has_no_body_content_beyond_title(self):
        report = Report(title="Empty")
        result = _export(report)
        assert "<h1>Empty</h1>" in result
        # No paragraphs/tables
        assert "<p>" not in result
        assert "<table>" not in result


class TestBackendType:
    """HtmlBackend satisfies the ReportBackend protocol."""

    def test_via_report_export(self):
        from dash_reportbuilder import Report

        report = Report(title="T")
        report.append(HeadingElement(text="H", level=2))
        report.append(ParagraphElement(text="body"))
        backend = HtmlBackend(title=report.title)
        data = report.export(backend)
        assert isinstance(data, bytes)
        text = data.decode("utf-8")
        assert "<h2>H</h2>" in text
        assert "<p>body</p>" in text
