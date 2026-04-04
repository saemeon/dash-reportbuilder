# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

from dash_reportbuilder.export._base import TypstTemplate
from dash_reportbuilder.model import ItemType, Report, ReportItem


def test_export_typst_produces_string(sample_report):
    from dash_reportbuilder.export._typst import export_typst

    result = export_typst(sample_report)
    assert isinstance(result, str)
    assert "= Test Report" in result
    assert 'image("img_1.png"' in result
    assert "== Introduction" in result
    assert "Some text here." in result
    assert "emph[Figure 1]" in result
    assert "#pagebreak()" in result


def test_export_typst_escapes_special_chars():
    from dash_reportbuilder.export._typst import export_typst

    report = Report(title="Report #1")
    report.append(ReportItem(type=ItemType.PARAGRAPH, content="Price: $100 @user"))
    result = export_typst(report)
    assert "\\#1" in result
    assert "\\$100" in result
    assert "\\@user" in result


def test_export_typst_empty_report():
    from dash_reportbuilder.export._typst import export_typst

    report = Report()
    result = export_typst(report)
    assert isinstance(result, str)
    assert "= Untitled Report" in result


def test_export_typst_custom_template():
    from dash_reportbuilder.export._typst import export_typst

    template = TypstTemplate(template='#set text(font: "Arial", size: 12pt)')
    report = Report(title="Custom")
    result = export_typst(report, template=template)
    assert '#set text(font: "Arial"' in result


# --- Additional tests ---

TINY_PNG_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


class TestHeadingLevels:
    """Heading levels map to Typst = prefixes."""

    def test_heading_level_1(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(
            ReportItem(type=ItemType.HEADING, content="Top", meta={"heading_level": 1})
        )
        result = export_typst(report)
        # Level 1 heading: single "=" (but title is also "= T", so check for "= Top")
        assert "\n= Top\n" in result

    def test_heading_level_2(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(
            ReportItem(type=ItemType.HEADING, content="Sub", meta={"heading_level": 2})
        )
        result = export_typst(report)
        assert "== Sub" in result

    def test_heading_level_3(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(
            ReportItem(type=ItemType.HEADING, content="SubSub", meta={"heading_level": 3})
        )
        result = export_typst(report)
        assert "=== SubSub" in result

    def test_heading_default_level_is_2(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.HEADING, content="Default"))
        result = export_typst(report)
        assert "== Default" in result
        assert "=== Default" not in result


class TestImageCaptionMeta:
    """Image with caption in meta emits #emph[...]."""

    def test_image_with_caption(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(
            ReportItem(
                type=ItemType.IMAGE,
                content=TINY_PNG_URI,
                meta={"caption": "Figure 1"},
            )
        )
        result = export_typst(report)
        assert 'image("img_1.png"' in result
        # Caption inside a #figure() block
        assert "Figure 1" in result

    def test_image_without_caption(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        result = export_typst(report)
        assert 'image("img_1.png"' in result
        # No emph line right after the image
        lines = result.split("\n")
        for i, line in enumerate(lines):
            if "img_1.png" in line:
                remaining = [ln for ln in lines[i + 1 :] if ln.strip()]
                if remaining:
                    assert not remaining[0].startswith("#emph")
                break


class TestImageSequentialFilenames:
    """Multiple images get sequential filenames img_1, img_2, ..."""

    def test_three_images(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        result = export_typst(report)
        assert 'image("img_1.png"' in result
        assert 'image("img_2.png"' in result
        assert 'image("img_3.png"' in result

    def test_images_interleaved_with_text(self):
        """Image counter only increments for IMAGE items."""
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        report.append(ReportItem(type=ItemType.PARAGRAPH, content="text"))
        report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
        result = export_typst(report)
        assert 'image("img_1.png"' in result
        assert 'image("img_2.png"' in result
        assert 'image("img_3.png"' not in result


class TestTypstEscaping:
    """Various special characters are escaped."""

    def test_escape_backslash(self):
        from dash_reportbuilder.export._typst import _escape_typst

        assert _escape_typst("a\\b") == "a\\\\b"

    def test_escape_brackets(self):
        from dash_reportbuilder.export._typst import _escape_typst

        result = _escape_typst("[text]")
        assert "\\[" in result
        assert "\\]" in result

    def test_escape_braces(self):
        from dash_reportbuilder.export._typst import _escape_typst

        result = _escape_typst("{code}")
        assert "\\{" in result
        assert "\\}" in result

    def test_escape_angle_brackets(self):
        from dash_reportbuilder.export._typst import _escape_typst

        result = _escape_typst("a < b > c")
        assert "\\<" in result
        assert "\\>" in result

    def test_escape_hash(self):
        from dash_reportbuilder.export._typst import _escape_typst

        assert "\\#" in _escape_typst("#tag")

    def test_escape_dollar(self):
        from dash_reportbuilder.export._typst import _escape_typst

        assert "\\$" in _escape_typst("$100")

    def test_escape_at(self):
        from dash_reportbuilder.export._typst import _escape_typst

        assert "\\@" in _escape_typst("@mention")

    def test_plain_text_unchanged(self):
        from dash_reportbuilder.export._typst import _escape_typst

        assert _escape_typst("Hello world") == "Hello world"


class TestTypstDefaultPreamble:
    """Without a template, the default preamble sets font and size."""

    def test_default_preamble(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        result = export_typst(report)
        assert '#set text(font: "Calibri", size: 11pt)' in result

    def test_custom_font_in_default_preamble(self):
        from dash_reportbuilder.export._typst import export_typst

        template = TypstTemplate(font="Helvetica", font_size="14pt")
        report = Report(title="T")
        result = export_typst(report, template=template)
        assert '#set text(font: "Helvetica", size: 14pt)' in result


class TestCaptionItem:
    """Caption items emit #emph[...]."""

    def test_caption_item(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.CAPTION, content="Source: dataset"))
        result = export_typst(report)
        assert "emph[Source: dataset]" in result


class TestPageBreak:
    """Page break emits #pagebreak()."""

    def test_page_break_ordering(self):
        from dash_reportbuilder.export._typst import export_typst

        report = Report(title="T")
        report.append(ReportItem(type=ItemType.PARAGRAPH, content="Before"))
        report.append(ReportItem(type=ItemType.PAGE_BREAK))
        report.append(ReportItem(type=ItemType.PARAGRAPH, content="After"))
        result = export_typst(report)
        lines = result.split("\n")
        pb_indices = [i for i, ln in enumerate(lines) if ln.strip() == "#pagebreak()"]
        assert len(pb_indices) == 1
        before_idx = next(i for i, ln in enumerate(lines) if "Before" in ln)
        after_idx = next(i for i, ln in enumerate(lines) if "After" in ln)
        assert before_idx < pb_indices[0] < after_idx
