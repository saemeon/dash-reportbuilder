# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Smoke test for the full TypstBackend → PDF pipeline.

Most TypstBackend tests check ``build_source()`` strings; this test
exercises ``build()``, which shells out to the ``typst`` CLI.  Catches
breakage in the source we generate (invalid Typst syntax, missing image
files in the temp dir, etc.) that the source-string tests can't see.

Skipped when the ``typst`` CLI isn't on PATH.
"""

from __future__ import annotations

import shutil

import pytest

from dash_reportbuilder import (
    HeadingElement,
    ImageElement,
    ParagraphElement,
    Report,
    TypstBackend,
    example_template_path,
)
from dash_reportbuilder.export._base import TypstTemplate

TINY_PNG_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"

requires_typst = pytest.mark.skipif(
    shutil.which("typst") is None,
    reason="typst CLI not on PATH; install: https://github.com/typst/typst#installation",
)


@requires_typst
class TestRealTypstCompile:
    """End-to-end PDF generation against the real typst CLI."""

    def test_minimal_report_compiles_to_pdf(self):
        report = Report(title="Smoke Test")
        report.append(HeadingElement(text="Section", level=2))
        report.append(ParagraphElement(text="Body text."))

        backend = TypstBackend(title=report.title)
        data = report.export(backend)

        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF-")
        # Sanity: real PDFs are at least a few KB
        assert len(data) > 500

    def test_report_with_image_compiles(self):
        """Images written to the temp dir must be reachable from the source."""
        report = Report(title="With Image")
        report.append(ImageElement(data_uri=TINY_PNG_URI, caption="Fig 1"))

        backend = TypstBackend(title=report.title)
        data = report.export(backend)

        assert data.startswith(b"%PDF-")

    def test_example_template_compiles(self):
        """The bundled example.typ preamble produces a valid PDF."""
        template = TypstTemplate(template=str(example_template_path("typst")))
        report = Report(title="Branded Smoke")
        report.append(HeadingElement(text="Heading", level=2))
        report.append(ParagraphElement(text="Branded body."))

        backend = TypstBackend(template=template, title=report.title)
        data = report.export(backend)

        assert data.startswith(b"%PDF-")

    def test_compile_failure_raises_with_helpful_message(self):
        """Invalid Typst source surfaces the typst error."""
        backend = TypstBackend(title="Bad")
        backend.append_raw("#unknown_function_that_doesnt_exist()")

        with pytest.raises(RuntimeError, match="Typst compilation failed"):
            backend.build()
