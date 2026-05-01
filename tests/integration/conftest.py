# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Integration test configuration.

These tests require a browser (Chrome + ChromeDriver) and are skipped on CI.
Run locally with:  uv run pytest dash-reportbuilder/tests/integration/ -v
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _skip_on_ci():
    if os.environ.get("CI"):
        pytest.skip("integration tests skipped on CI")
