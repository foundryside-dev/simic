// Typst design system for the consolidated Simic HLD.
//
// This file owns every typographic and layout decision. The chapter markdown
// under docs/design/ owns the content, and pandoc-typst.typ owns the document
// furniture (cover, colophon, table of contents). Chapter edits therefore never
// require touching this file.
//
// Font stack rationale (verified present via `typst fonts`):
//   body     Libertinus Serif — a Linux Libertine successor with excellent
//            glyph coverage and readable italics; well suited to long-form
//            technical prose at 10.5pt.
//   heading  Lato — a humanist sans with a warmer, less corporate voice than
//            Helvetica clones, giving clear contrast against the serif body.
//   mono     Noto Sans Mono — narrower than DejaVu, so the wide ASCII diagrams
//            and directory trees in this document fit without wrapping.
//   math     New Computer Modern Math — Typst's default; pairs acceptably with
//            Libertinus, both being Latin-Modern-adjacent designs.
//
// ASSUMPTION (flagged for the owner): the project has no stated brand palette.
// The colours below are derived from the Simic guild identity that gives the
// project and its subsystems their names — blue-green — as a deep teal primary
// with a moss-green accent. Replace `primary`/`accent` to rebrand; nothing else
// hardcodes a colour.

// --- Palette --------------------------------------------------------------

#let primary = rgb("#0E4C56") // deep teal: headings, rules, table headers
#let accent = rgb("#2F7D5D") // moss green: accent bars, enum markers
#let ink = rgb("#22282A") // body text — near-black, slightly warm
#let muted = rgb("#5C6A6E") // captions, provenance notes, footer
#let hairline = luma(205) // table and furniture rules
#let code-bg = rgb("#F4F6F6") // code block and inline code fill
#let code-border = rgb("#DCE3E3")

// Contrast against white (WCAG 2.2): primary 10.4:1, ink 13.9:1, muted 5.2:1,
// accent 4.6:1 — all clear of the 4.5:1 floor for normal text.

// --- Font stacks ----------------------------------------------------------

#let font-body = ("Libertinus Serif", "TeX Gyre Termes", "Liberation Serif", "DejaVu Serif")
#let font-head = ("Lato", "TeX Gyre Heros", "Liberation Sans", "DejaVu Sans")
#let font-mono = ("Noto Sans Mono", "DejaVu Sans Mono", "Liberation Mono")

// --- Shared helpers -------------------------------------------------------

// A small grey note used for decomposition provenance under a section heading.
// Invoked from the body as raw Typst by preprocess.py --provenance.
#let provenance-note(body) = block(
  above: 0.4em,
  below: 1.0em,
  text(font: font-head, size: 7.5pt, style: "italic", fill: muted, body),
)

// Places a diagram on a dedicated landscape page, sized to the page rather than
// to the text measure.
//
// The architecture flowchart in 04-architecture.md has sixteen labelled nodes
// and crossing edges. Inline at the 15.5cm text measure its labels render at
// roughly 4pt — present but not readable. A flipped page gives it ~25cm and
// makes it legible, which for the document's central diagram is worth the break
// in reading flow. Called from the body as raw Typst emitted by preprocess.py.
#let diagram-page(path, caption: none, alt: none) = page(
  flipped: true,
  header: none,
  margin: (x: 1.6cm, y: 1.5cm),
)[
  #align(center + horizon)[
    #image(path, height: if caption == none { 100% } else { 94% }, alt: alt)
    #if caption != none {
      v(0.5em)
      text(font: font-head, size: 8.5pt, fill: muted)[#caption]
    }
  ]
]

// Renders the §18 enum markers as INV-01..INV-45 chips instead of 1..45, so the
// document's most-cited list is labelled the way it is cited everywhere else.
#let inv-chip(n) = box(
  fill: primary,
  radius: 2pt,
  inset: (x: 4pt, y: 2.5pt),
  baseline: 0.22em,
  text(
    font: font-head,
    size: 7pt,
    weight: "bold",
    fill: white,
    tracking: 0.03em,
  )[INV-#if n < 10 [0]#n],
)

// --- Main configuration ---------------------------------------------------

#let conf(
  title: none,
  subtitle: none,
  shorttitle: none,
  doctype: none,
  version: none,
  authors: (),
  date: none,
  // Plain-string variants for PDF/XMP metadata: Typst 0.14 document() wants
  // str, while pandoc hands everything over wrapped in content blocks.
  pdf-title: none,
  pdf-author: none,
  pdf-keywords: none,
  lang: "en",
  region: "GB",
  doc,
) = {
  // Machine-readable metadata — drives the PDF title bar and assistive tech.
  set document(
    title: if pdf-title != none { pdf-title } else { none },
    author: if pdf-author != none { (pdf-author,) } else { () },
    keywords: if pdf-keywords != none { pdf-keywords.split(", ") } else { () },
    date: auto,
  )

  let header-label = if shorttitle != none { shorttitle } else { pdf-title }

  // --- Page geometry ---
  // Asymmetric inner/outer margins on a two-sided layout: the extra inner
  // margin keeps the gutter clear if the document is ever printed and bound.
  set page(
    paper: "a4",
    margin: (top: 2.6cm, bottom: 2.4cm, inside: 2.8cm, outside: 2.3cm),
    binding: left,
    fill: white,
    header: context {
      // `here().page()` is the ABSOLUTE physical page. It must not be confused
      // with `counter(page)`, which this document resets twice (roman front
      // matter, then arabic body) — comparing a reset counter against absolute
      // heading locations silently reports the wrong section in the header.
      let phys = here().page()
      let sections = query(heading.where(level: 2))

      // Suppress on the opening page of each major section, where the section
      // title is already the dominant element.
      let opens-here = sections.any(h => h.location().page() == phys)
      if opens-here { return }

      // Right side of the header tracks the section the reader is inside.
      let prior = sections.filter(h => h.location().page() <= phys)
      let current = if prior.len() > 0 { prior.last().body } else { [] }

      set text(font: font-head, size: 8pt, fill: muted)
      grid(
        columns: (auto, 1fr),
        align: (left, right),
        text(weight: "bold")[#header-label],
        // Long section titles are truncated by the box rather than wrapped.
        box(width: 11cm, clip: true, height: 1em)[
          #align(right)[#current]
        ],
      )
      v(0.25em)
      line(length: 100%, stroke: 0.4pt + hairline)
    },
    footer: context {
      line(length: 100%, stroke: 0.4pt + hairline)
      v(0.3em)
      set text(font: font-head, size: 8pt, fill: muted)
      grid(
        columns: (1fr, auto, 1fr),
        align: (left, center, right),
        [#doctype #version],
        text(weight: "bold", fill: primary)[#counter(page).display()],
        align(right)[#date],
      )
    },
  )

  // --- Body text ---
  set text(
    font: font-body,
    size: 10.5pt,
    fill: ink,
    lang: lang,
    region: region,
    hyphenate: true,
  )

  // Leading and paragraph spacing are deliberately distinct (0.72em vs 0.95em)
  // so paragraph starts are visible without first-line indents.
  set par(
    leading: 0.72em,
    spacing: 0.95em,
    justify: true,
    linebreaks: "optimized",
  )

  // --- Headings ---
  // The chapters carry the v4.1 monolith's own section numbers in their heading
  // text (`## 18.`, `### 13.11`), so Typst adds no numbering of its own —
  // auto-numbering here would double up.
  set heading(numbering: none)
  show heading: set block(sticky: true)
  show heading: set text(font: font-head, fill: primary, hyphenate: false)
  show heading: set par(justify: false)

  // Level 1 — unused by the assembled body (the document-title h1 is stripped
  // and rendered on the cover), styled defensively in case a chapter adds one.
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    block(above: 0pt, below: 1.2em)[
      #line(length: 100%, stroke: 2pt + primary)
      #v(0.5em)
      #text(size: 22pt, weight: "bold")[#it.body]
    ]
  }

  // Level 2 — a major monolith section (§1..§30, appendices). Opens a page and
  // carries the heaviest treatment in the document.
  show heading.where(level: 2): it => {
    pagebreak(weak: true)
    block(above: 0pt, below: 1.1em)[
      #line(length: 100%, stroke: 1.6pt + primary)
      #v(0.55em)
      #text(size: 19pt, weight: "bold")[#it.body]
      #v(0.15em)
      #line(length: 18%, stroke: 2.5pt + accent)
    ]
  }

  // Level 3 — a subsection (§6.1, §13.11). An accent rule to the left of the
  // title keeps the hierarchy readable without another size step.
  //
  // The bar is a block `stroke` rather than a sized rect: a rect with
  // `height: 100%` inside a grid resolves against the page, not the heading,
  // which silently turns every subsection into its own page.
  show heading.where(level: 3): it => {
    block(
      above: 1.7em,
      below: 0.7em,
      breakable: false,
      inset: (left: 9pt),
      stroke: (left: 2.5pt + accent),
      text(size: 13.5pt, weight: "bold")[#it.body],
    )
  }

  // Level 4 — sub-subsection ("Responsibilities", "Invariants" in the domain
  // chapters). Distinguished by weight and colour, not size.
  show heading.where(level: 4): it => {
    block(above: 1.2em, below: 0.5em, breakable: false)[
      #text(size: 11pt, weight: "bold", fill: primary.darken(8%))[#it.body]
    ]
  }

  show heading.where(level: 5): it => {
    block(above: 1.0em, below: 0.4em, breakable: false)[
      #text(size: 10.5pt, weight: "bold", style: "italic", fill: muted.darken(20%))[#it.body]
    ]
  }

  // --- Links ---
  // Relative .md links are reduced to plain text in preprocess.py, so anything
  // that reaches here is a real, resolvable http(s) target.
  show link: it => text(fill: primary.lighten(12%))[#it]

  // --- Code blocks ---
  // Left accent bar rather than a full border: lighter on the page, and it
  // survives page breaks cleanly on the long directory trees and ASCII
  // diagrams in ops/repo-structure.md and 04-architecture.md.
  show raw.where(block: true): it => {
    set text(font: font-mono, size: 8.4pt, fill: ink)
    set par(leading: 0.58em, justify: false)
    block(
      width: 100%,
      fill: code-bg,
      inset: (left: 11pt, right: 10pt, top: 9pt, bottom: 9pt),
      radius: (right: 3pt),
      stroke: (left: 2pt + accent.lighten(35%), rest: 0.5pt + code-border),
      breakable: true,
      above: 1.1em,
      below: 1.1em,
      // Shrink-to-fit. Typst does not wrap raw text, so a long line — the arrow
      // chains in programme/curriculum.md, the wide ASCII diagrams — runs off
      // both page edges instead of being contained. Measuring the block's
      // natural width and scaling down only when it exceeds the measure keeps
      // every line on the page while leaving normal-width blocks untouched.
      //
      // Re-using `it` inside its own show rule is safe: Typst does not re-apply
      // a show rule to the element it is already handling.
      layout(size => {
        let natural = measure(it)
        let ratio = if natural.width > size.width and natural.width > 0pt {
          size.width / natural.width
        } else {
          1.0
        }
        if ratio < 1.0 {
          scale(x: ratio * 100%, y: ratio * 100%, origin: top + left, reflow: true, it)
        } else {
          it
        }
      }),
    )
  }

  // --- Inline code ---
  // `outset` supplies the vertical padding instead of `inset`, which would lift
  // the box off the text baseline. Size is relative so inline code stays in
  // proportion inside footnotes, captions and table cells.
  // The horizontal inset is deliberately tight and there is no stroke: this
  // document sets contract names as inline code constantly, and they are almost
  // always followed by a comma or full stop. Wider padding plus a border reads
  // as a space before the punctuation ("`GrowthIntent` ,").
  show raw.where(block: false): it => {
    box(
      fill: code-bg,
      inset: (x: 1.2pt),
      outset: (y: 2.5pt),
      radius: 1.5pt,
      text(font: font-mono, size: 0.88em, fill: ink.darken(5%), it),
    )
  }

  // --- Tables ---
  set table(
    inset: (x: 7pt, y: 5.5pt),
    // Every table in this document is prose (roles, invariants, mitigations,
    // failure modes), so all columns are left-aligned. Pandoc wraps its tables
    // in `align(center)[...]`, which centres the cell text; postprocess.py
    // strips that wrapper so this setting actually takes effect.
    align: left + top,
    stroke: (x, y) => (
      bottom: if y == 0 { 1.1pt + primary } else { 0.4pt + hairline },
    ),
    fill: (x, y) => {
      if y == 0 { primary.lighten(88%) } else if calc.odd(y) { white } else { luma(249) }
    },
  )

  // Table prose is set smaller and ragged-right: these tables have narrow
  // columns, where justification produces visible rivers.
  show table.cell: set text(size: 8.6pt, hyphenate: true)
  show table.cell: set par(leading: 0.6em, spacing: 0.5em, justify: false, linebreaks: "optimized")
  show table.cell.where(y: 0): set text(weight: "bold", fill: primary, size: 8.6pt)

  // Pandoc wraps every table in a figure; make those break across pages
  // instead of piling up at the foot of one.
  show figure.where(kind: table): set block(breakable: true, width: 100%)
  show figure.where(kind: table): set align(left)
  show figure.caption: set text(font: font-head, size: 8pt, fill: muted)

  // --- Block quotes ---
  show quote.where(block: true): it => block(
    width: 100%,
    inset: (left: 12pt, right: 10pt, top: 7pt, bottom: 7pt),
    fill: primary.lighten(96%),
    stroke: (left: 2.5pt + primary.lighten(45%)),
    radius: (right: 2pt),
    above: 1.1em,
    below: 1.1em,
    text(fill: ink.lighten(8%), it.body),
  )

  // --- Lists ---
  set list(indent: 0.9em, body-indent: 0.55em, spacing: 0.62em, marker: (
    text(fill: accent, weight: "bold")[•],
    text(fill: accent)[–],
    text(fill: muted)[·],
  ))
  set enum(indent: 0.9em, body-indent: 0.55em, spacing: 0.62em, number-align: right + top)
  show enum: set par(justify: true)

  // --- The 45 constitutional invariants ---
  // preprocess.py wraps the §18 list in a `::: {#simic-invariants}` div, which
  // pandoc emits as this Typst label. Numbering becomes INV-01..INV-45 chips so
  // the document's most-cited list is labelled the way it is cited.
  //
  // The label is prefixed because `<invariants>` is pandoc's auto-generated
  // anchor for the "Invariants" heading present in every domain chapter; a rule
  // keyed on that would restyle fourteen unrelated bullet lists.
  show <simic-invariants>: it => {
    set enum(
      numbering: n => inv-chip(n),
      indent: 0pt,
      body-indent: 8pt,
      spacing: 0.85em,
      number-align: left + top,
    )
    block(above: 1.0em, below: 1.0em, it)
  }

  // --- Math ---
  set math.equation(numbering: none)
  show math.equation.where(block: true): set block(above: 1.1em, below: 1.1em)

  // Shrink-to-fit for display equations, for the same reason as raw blocks:
  // Typst does not line-break inside an equation, so anything wider than the
  // measure runs off both page edges.
  //
  // The case that forces this is programme/curriculum.md §16.1, which expresses
  // a four-stage prose progression as a single `$$ \text{...} \rightarrow ... $$`
  // chain roughly 150 characters wide. Scaling keeps it on the page; it does not
  // make it large. Flagged in tools/pdf/README.md as content that would read
  // better as a list than as an equation.
  show math.equation.where(block: true): it => layout(size => {
    let natural = measure(it)
    let ratio = if natural.width > size.width and natural.width > 0pt {
      size.width / natural.width
    } else {
      1.0
    }
    if ratio < 1.0 {
      scale(x: ratio * 100%, y: ratio * 100%, origin: center + horizon, reflow: true, it)
    } else {
      it
    }
  })

  // --- Footnotes ---
  set footnote.entry(separator: line(length: 30%, stroke: 0.5pt + hairline))
  show footnote.entry: set text(size: 8.2pt)

  // --- Terms / definition lists ---
  show terms.item: it => block(breakable: false, below: 0.7em)[
    #text(weight: "bold", fill: primary)[#it.term]
    #block(inset: (left: 1.2em, top: -0.35em))[#it.description]
  ]

  doc
}
