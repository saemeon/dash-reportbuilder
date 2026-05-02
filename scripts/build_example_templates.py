"""Generate the bundled example.docx and example.pptx templates.

Run this once and commit the outputs.  The generated files are loaded
by users via :func:`dash_reportbuilder.example_template_path`.

Usage:
    uv run --active python scripts/build_example_templates.py
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PPTXColor
from pptx.util import Inches as PPTXInches
from pptx.util import Pt as PPTXPt

# ---------------------------------------------------------------------------
# Brand definition (kept in lockstep with example.typ)
# ---------------------------------------------------------------------------

BRAND_PRIMARY = RGBColor(0x25, 0x63, 0xEB)  # royal blue
BRAND_ACCENT = RGBColor(0xF5, 0x9E, 0x0B)  # amber
BRAND_MUTED = RGBColor(0x64, 0x74, 0x8B)  # slate
BODY_FONT = "Calibri"

OUT_DIR = Path(__file__).resolve().parent.parent / "src/dash_reportbuilder/templates"


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------


def build_docx() -> Path:
    doc = Document()

    # Body style
    body = doc.styles["Normal"]
    body.font.name = BODY_FONT
    body.font.size = Pt(11)

    # Heading styles
    for lvl, size in [(1, 22), (2, 14), (3, 12)]:
        s = doc.styles[f"Heading {lvl}"]
        s.font.name = BODY_FONT
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = BRAND_PRIMARY if lvl < 3 else BRAND_MUTED

    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Caption style — used by DocxBackend.add_caption via font tweaks
    if "Caption" not in [s.name for s in doc.styles]:
        cap = doc.styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        cap = doc.styles["Caption"]
    cap.font.name = BODY_FONT
    cap.font.size = Pt(10)
    cap.font.italic = True
    cap.font.color.rgb = BRAND_MUTED

    out = OUT_DIR / "example.docx"
    doc.save(out)
    print(f"wrote {out}")
    return out


# ---------------------------------------------------------------------------
# PowerPoint
# ---------------------------------------------------------------------------


def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = PPTXInches(13.333)
    prs.slide_height = PPTXInches(7.5)

    # Apply brand styling to title placeholders across all layouts
    brand_blue = PPTXColor(0x25, 0x63, 0xEB)
    for layout in prs.slide_layouts:
        for shape in layout.placeholders:
            if not shape.has_text_frame:
                continue
            # Title placeholders have idx == 0
            if shape.placeholder_format.idx == 0:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        run.font.name = BODY_FONT
                        run.font.color.rgb = brand_blue
                        run.font.bold = True

    out = OUT_DIR / "example.pptx"
    prs.save(out)
    print(f"wrote {out}")
    return out


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_docx()
    build_pptx()
