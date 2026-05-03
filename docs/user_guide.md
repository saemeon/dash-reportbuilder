# User guide

## Building a report

`Report` is a thin wrapper over a list of elements:

```python
from dash_reportbuilder import (
    HeadingElement,
    ImageElement,
    ParagraphElement,
    Report,
)

report = Report(title="Quarterly review")
report.add(HeadingElement("Intro", level=2))
report.add(ParagraphElement("Some prose body."))
report.add(ImageElement(data_uri="data:image/png;base64,..."))
```

Elements have stable `id` fields, so reordering and updates are easy:

```python
report.reorder([item3.id, item1.id, item2.id])
report.update_item(item1.id, text="New text")
```

## Exporting

Pick a backend and call `export`:

```python
from dash_reportbuilder import DocxBackend, HtmlBackend, TypstBackend

# Word
data: bytes = report.export(DocxBackend(title=report.title))

# Self-contained HTML (images embedded as data URIs)
html: bytes = report.export(HtmlBackend(title=report.title))

# Typst source. PDF requires the `typst` CLI on $PATH.
typst: bytes = report.export(TypstBackend(title=report.title))
```

Backends accept a template object that controls fonts, colors, page
geometry, and (for `.docx` / `.pptx`) a base document whose styles are
preserved:

```python
from dash_reportbuilder import DocxBackend, DocxTemplate, example_template_path

template = DocxTemplate(template_path=str(example_template_path("docx")))
data = report.export(DocxBackend(template=template, title=report.title))
```

## Custom elements

Implement `render_into(backend)` and register the class for FileStore
round-trip:

```python
from dataclasses import dataclass, field
from typing import ClassVar

from dash_reportbuilder import (
    HtmlBackend,
    TypstBackend,
    register_element_type,
)
from dash_reportbuilder.elements import _new_id


@register_element_type
@dataclass
class CalloutElement:
    text: str
    color: str = "#2563eb"
    id: str = field(default_factory=_new_id)
    type: ClassVar[str] = "callout"

    def render_into(self, backend) -> None:
        if isinstance(backend, TypstBackend):
            backend.append_raw(f'#block(fill: rgb("{self.color}"))[{self.text}]')
        elif isinstance(backend, HtmlBackend):
            backend.append_raw_html(
                f'<aside style="background:{self.color}">{self.text}</aside>'
            )
        else:
            backend.add_paragraph(f"[CALLOUT] {self.text}")
```

The `isinstance` checks let the type checker narrow the backend, so
`backend.append_raw(...)` and `backend.append_raw_html(...)` type-check
without casts.

## Persistence

`MemoryStore` and `FileStore` persist reports across requests. The
registry in `register_element_type` is consulted at deserialize time, so
custom elements survive a fresh process:

```python
from dash_reportbuilder import FileStore, Report

store = FileStore("/var/reports")
store.put("session-42", report)

# Later, in a new process:
loaded: Report = FileStore("/var/reports").get("session-42")
```
