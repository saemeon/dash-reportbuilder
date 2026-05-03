# dash-reportbuilder

Capture, assemble, and export reports from Plotly Dash applications.
Three export targets: Word (`.docx`), PowerPoint (`.pptx`), Typst source / PDF,
plus self-contained HTML and image-only ZIP.

## Installation

```bash
pip install dash-reportbuilder[docx,pptx]
```

The optional `docx` and `pptx` extras pull in `python-docx` and
`python-pptx`. The `typst` and `html` backends require no extras.
PDF compilation needs the `typst` CLI on `$PATH`.

## Quick start

```python
from dash_reportbuilder import (
    DocxBackend,
    HeadingElement,
    ImageElement,
    ParagraphElement,
    Report,
)

report = Report(title="Q1")
report.add(HeadingElement("Intro", level=2))
report.add(ParagraphElement("Some prose."))
report.add(ImageElement(data_uri="data:image/png;base64,..."))

data: bytes = report.export(DocxBackend(title=report.title))
```

## Architecture

```
ReportElement  ──render_into──▶  ReportBackend  ──build──▶  bytes
(knows what)                     (knows how to format)
        ▲
        │
   Report (a list of elements)
```

- **Elements** know what to render. They call generic primitives on the
  backend (`add_heading`, `add_image`, …), or reach for the backend's
  format-native escape hatch.
- **Backends** know how to format. Each exposes the same generic surface
  plus a backend-specific escape hatch (`append_raw`, `modify`, …).
- **`Report`** is just a list with light reordering helpers.

See the [user guide](user_guide.md) for more, and the
[API reference](api/index.md) for the full surface.
