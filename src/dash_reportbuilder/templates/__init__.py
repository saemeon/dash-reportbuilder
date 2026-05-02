# Copyright (c) Simon Niederberger.
# Distributed under the terms of the MIT License.

"""Bundled example template assets.

Use :func:`example_template_path` to locate the bundled file for a given
format, then pass the path into the corresponding ``*Template``::

    from pathlib import Path
    from dash_reportbuilder import (
        DocxBackend,
        DocxTemplate,
        example_template_path,
    )

    template = DocxTemplate(template_path=str(example_template_path("docx")))
    backend = DocxBackend(template=template, title="My Report")
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

_ASSETS = Path(__file__).resolve().parent

_FORMATS: dict[str, str] = {
    "docx": "example.docx",
    "pptx": "example.pptx",
    "typst": "example.typ",
}


def example_template_path(format: Literal["docx", "pptx", "typst"]) -> Path:
    """Return the path to the bundled example template for *format*.

    Parameters
    ----------
    format : {"docx", "pptx", "typst"}
        Output format.

    Returns
    -------
    Path
        Absolute path to the bundled asset inside the installed package.
    """
    if format not in _FORMATS:
        raise ValueError(
            f"Unknown template format: {format!r}. "
            f"Expected one of {sorted(_FORMATS)}."
        )
    return _ASSETS / _FORMATS[format]
