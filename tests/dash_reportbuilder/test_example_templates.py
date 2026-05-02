# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Tests for the bundled example template assets."""

import pytest

from dash_reportbuilder import (
    DocxBackend,
    DocxTemplate,
    HeadingElement,
    ParagraphElement,
    PptxBackend,
    PptxTemplate,
    Report,
    TypstBackend,
    TypstTemplate,
    example_template_path,
)


class TestExampleTemplatePath:
    """example_template_path() returns existing files for known formats."""

    @pytest.mark.parametrize("fmt", ["docx", "pptx", "typst"])
    def test_known_format_returns_existing_file(self, fmt):
        path = example_template_path(fmt)
        assert path.exists()
        assert path.is_file()

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown template format"):
            example_template_path("xlsx")  # type: ignore[arg-type]

    def test_typst_template_is_text(self):
        path = example_template_path("typst")
        contents = path.read_text(encoding="utf-8")
        assert "brand-primary" in contents

    def test_docx_template_is_zip(self):
        path = example_template_path("docx")
        assert path.read_bytes()[:2] == b"PK"

    def test_pptx_template_is_zip(self):
        path = example_template_path("pptx")
        assert path.read_bytes()[:2] == b"PK"


class TestExampleTemplatesInBackends:
    """The example templates can be passed to each backend without errors."""

    def test_docx_backend_with_example_template(self):
        template = DocxTemplate(template_path=str(example_template_path("docx")))
        backend = DocxBackend(template=template, title="Branded")
        report = Report(title="Branded")
        report.append(HeadingElement(text="Section", level=2))
        report.append(ParagraphElement(text="Body."))
        data = report.export(backend)
        assert data[:2] == b"PK"

    def test_pptx_backend_with_example_template(self):
        template = PptxTemplate(template_path=str(example_template_path("pptx")))
        backend = PptxBackend(template=template)
        report = Report(title="Branded")
        report.append(HeadingElement(text="Slide", level=2))
        data = report.export(backend)
        assert data[:2] == b"PK"

    def test_typst_backend_with_example_template(self):
        template = TypstTemplate(template=str(example_template_path("typst")))
        backend = TypstBackend(template=template, title="Branded")
        report = Report(title="Branded")
        report.append(HeadingElement(text="Section", level=2))
        report.append(ParagraphElement(text="Body."))
        for item in report.items:
            item.render_into(backend)
        source = backend.build_source()
        assert "brand-primary" in source
        assert "Section" in source
