// Example branded Typst preamble shipped with dash-reportbuilder.
//
// Pass this file to TypstTemplate(template=Path(...)) to produce a
// branded report.  Edit a copy of this file for your own brand:
//
//     from dash_reportbuilder import example_template_path
//     from dash_reportbuilder.export._base import TypstTemplate
//
//     tpl = TypstTemplate(template=str(example_template_path("typst")))

#let brand-primary = rgb("#2563eb")  // royal blue
#let brand-accent = rgb("#f59e0b")   // amber
#let brand-muted = rgb("#64748b")    // slate
#let brand-bg = rgb("#f8fafc")       // very light gray

// Page setup
#set page(
  paper: "a4",
  margin: (left: 2.5cm, right: 2.5cm, top: 2.5cm, bottom: 2.5cm),
  header: context {
    if counter(page).get().first() > 1 {
      align(right, text(8pt, fill: brand-muted, "Report"))
    }
  },
  footer: context {
    set align(right)
    set text(8pt, fill: brand-muted)
    counter(page).display("1 / 1", both: true)
  },
)

// Body text
#set text(font: "Calibri", size: 11pt, lang: "en")
#set par(justify: true, leading: 0.65em)

// Headings
#show heading.where(level: 1): it => block(
  below: 0.8em,
  text(size: 22pt, weight: "bold", fill: brand-primary, it.body),
)
#show heading.where(level: 2): it => block(
  above: 1.2em,
  below: 0.5em,
  text(size: 14pt, weight: "bold", fill: brand-primary, it.body),
)
#show heading.where(level: 3): it => block(
  above: 1em,
  below: 0.4em,
  text(size: 12pt, weight: "bold", fill: brand-muted, it.body),
)

// Figures (images + captions)
#show figure.caption: it => align(
  left,
  text(size: 10pt, style: "italic", fill: brand-muted, it),
)

// Tables
#set table(stroke: 0.5pt + brand-muted, inset: 6pt)
#show table.cell.where(y: 0): set text(weight: "bold", fill: brand-primary)
