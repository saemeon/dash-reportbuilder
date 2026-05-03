# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Tests for ImageZipBackend."""

import io
import zipfile

import pytest

from dash_reportbuilder import (
    CaptionElement,
    HeadingElement,
    ImageElement,
    ImageZipBackend,
    PageBreakElement,
    ParagraphElement,
    Report,
)

# Tiny 1×1 PNG
TINY_PNG_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
# Tiny 1×1 GIF (different mime)
TINY_GIF_URI = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
)
# A trivial inline SVG
TINY_SVG_URI = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciLz4="
)


def _zip_names(data: bytes) -> list[str]:
    return zipfile.ZipFile(io.BytesIO(data)).namelist()


def _zip_contents(data: bytes) -> dict[str, bytes]:
    z = zipfile.ZipFile(io.BytesIO(data))
    return {n: z.read(n) for n in z.namelist()}


def _export(report: Report) -> bytes:
    backend = ImageZipBackend()
    return report.export(backend)


class TestBuild:
    def test_returns_bytes(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI))
        data = _export(report)
        assert isinstance(data, bytes)
        assert data[:2] == b"PK"

    def test_empty_report_makes_empty_zip(self):
        data = _export(Report(title="Empty"))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert zf.namelist() == []


class TestFilenames:
    def test_default_names_are_sequential(self):
        report = Report(title="T")
        for _ in range(3):
            report.append(ImageElement(data_uri=TINY_PNG_URI))
        names = _zip_names(_export(report))
        assert names == ["image_001.png", "image_002.png", "image_003.png"]

    def test_title_used_as_filename(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="My Chart"))
        names = _zip_names(_export(report))
        assert names == ["My_Chart.png"]

    def test_title_sanitized_of_unsafe_chars(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="A/B: C*D? <evil>"))
        names = _zip_names(_export(report))
        # Only one file, no slashes/colons/etc.
        assert len(names) == 1
        for ch in '/\\:*?<>"':
            assert ch not in names[0]

    def test_duplicate_titles_disambiguate(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="Chart"))
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="Chart"))
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="Chart"))
        names = _zip_names(_export(report))
        assert names == ["Chart.png", "Chart_2.png", "Chart_3.png"]


class TestMimeDetection:
    def test_png(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI))
        assert _zip_names(_export(report)) == ["image_001.png"]

    def test_gif(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_GIF_URI))
        assert _zip_names(_export(report)) == ["image_001.gif"]

    def test_svg(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_SVG_URI))
        assert _zip_names(_export(report)) == ["image_001.svg"]

    def test_unknown_mime_defaults_to_png(self):
        report = Report(title="T")
        report.append(ImageElement(data_uri="data:image/bogus;base64,iVBORw0KGgo="))
        assert _zip_names(_export(report)) == ["image_001.png"]


class TestNonImageElementsIgnored:
    """Headings, paragraphs, captions, page breaks produce no zip entries."""

    def test_only_image_elements_appear(self):
        report = Report(title="Mixed")
        report.append(HeadingElement(text="H", level=2))
        report.append(ParagraphElement(text="some prose"))
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="A"))
        report.append(CaptionElement(text="cap"))
        report.append(PageBreakElement())
        report.append(ImageElement(data_uri=TINY_PNG_URI, title="B"))
        names = _zip_names(_export(report))
        assert names == ["A.png", "B.png"]


class TestImageBytes:
    """Image bytes round-trip through the zip unchanged."""

    def test_bytes_preserved(self):
        from dash_reportbuilder.export._base import decode_data_uri

        report = Report(title="T")
        report.append(ImageElement(data_uri=TINY_PNG_URI))
        data = _export(report)
        contents = _zip_contents(data)
        assert contents["image_001.png"] == decode_data_uri(TINY_PNG_URI)


class TestEscapeHatch:
    """add_raw() lets elements drop arbitrary files into the zip."""

    def test_add_raw(self):
        backend = ImageZipBackend()
        backend.add_raw("manifest.txt", b"hello")
        backend.add_image(TINY_PNG_URI, title="Chart")
        contents = _zip_contents(backend.build())
        assert contents["manifest.txt"] == b"hello"
        assert "Chart.png" in contents

    def test_add_raw_duplicate_filename_raises(self):
        backend = ImageZipBackend()
        backend.add_raw("a.txt", b"1")
        with pytest.raises(ValueError, match="Duplicate"):
            backend.add_raw("a.txt", b"2")
