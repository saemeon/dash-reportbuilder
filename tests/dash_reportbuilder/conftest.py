# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Shared test fixtures."""

import pytest

from dash_reportbuilder.model import ItemType, Report, ReportItem

# Valid 1x1 red PNG, base64-encoded
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
TINY_PNG_URI = f"data:image/png;base64,{TINY_PNG_B64}"


@pytest.fixture
def tiny_png_uri():
    return TINY_PNG_URI


@pytest.fixture
def sample_report():
    report = Report(title="Test Report")
    report.append(ReportItem(type=ItemType.HEADING, content="Introduction"))
    report.append(ReportItem(type=ItemType.IMAGE, content=TINY_PNG_URI))
    report.append(ReportItem(type=ItemType.PARAGRAPH, content="Some text here."))
    report.append(ReportItem(type=ItemType.CAPTION, content="Figure 1"))
    report.append(ReportItem(type=ItemType.PAGE_BREAK))
    return report
