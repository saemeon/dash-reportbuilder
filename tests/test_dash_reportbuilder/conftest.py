# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Shared test fixtures."""

import pytest

from dash_reportbuilder.elements import (
    CaptionElement,
    HeadingElement,
    ImageElement,
    PageBreakElement,
    ParagraphElement,
)
from dash_reportbuilder.model import Report

# Valid 1x1 red PNG, base64-encoded
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
TINY_PNG_URI = f"data:image/png;base64,{TINY_PNG_B64}"


@pytest.fixture
def tiny_png_uri():
    return TINY_PNG_URI


@pytest.fixture
def sample_report():
    report = Report(title="Test Report")
    report.append(HeadingElement(text="Introduction", level=2))
    report.append(ImageElement(data_uri=TINY_PNG_URI))
    report.append(ParagraphElement(text="Some text here."))
    report.append(CaptionElement(text="Figure 1"))
    report.append(PageBreakElement())
    return report
