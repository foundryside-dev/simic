// Pandoc template producing the consolidated Simic HLD.
//
// Owns the document furniture only — cover page, colophon, table of contents,
// and the front-matter/body page-numbering switch. All typography and element
// styling lives in template.typ.
//
// Used as: pandoc body.md -t typst --template=pandoc-typst.typ
//                         --metadata-file=metadata.yaml --standalone

$if(highlighting-definitions)$
$highlighting-definitions$

$endif$
// Root-relative (typst is invoked with --root at the repository root), because
// the generated .typ is written to tools/pdf/build/ while this template and
// template.typ live in tools/pdf/.
// `provenance-note` and `diagram-page` are imported because the generated body
// calls them directly as raw Typst (emitted by preprocess.py).
#import "/tools/pdf/template.typ": conf, provenance-note, diagram-page, primary, accent, ink, muted, hairline, font-body, font-head, font-mono

#set smartquote(enabled: true)

$for(header-includes)$
$header-includes$

$endfor$
#show: doc => conf(
$if(title)$
  title: [$title$],
  pdf-title: "$title$$if(subtitle)$ — $subtitle$$endif$",
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(shorttitle)$
  shorttitle: [$shorttitle$],
$endif$
$if(doctype)$
  doctype: [$doctype$],
$endif$
$if(version)$
  version: [v$version$],
$endif$
$if(author)$
  authors: (( name: [$author$], affiliation: "", email: "" ),),
  pdf-author: "$author$",
$endif$
$if(keywords)$
  pdf-keywords: "$keywords$",
$endif$
$if(date)$
  date: [$date$],
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
$if(region)$
  region: "$region$",
$endif$
  doc,
)

// =====================================================================
// COVER
// =====================================================================
// A full-bleed teal band across the head of the page, then the title block on
// white. `place` with negative offsets escapes the page margin to reach the trim
// edge: dx -2.8cm and dy -2.6cm are the inside and top margins from conf().
//
// BAND-DEPTH is measured from the physical top of the page and must clear the
// whole reversed-out title block (eyebrow + title + subtitle). It is stated once
// here because the accent stripe below has to sit exactly on the band's edge,
// and because a band that ends short puts white subtitle text on white paper.
#let band-depth = 10.4cm
#let bleed-x = -2.8cm
#let bleed-y = -2.6cm

#page(header: none, footer: none, numbering: none)[
  #place(
    top + left,
    dx: bleed-x,
    dy: bleed-y,
    rect(width: 21cm, height: band-depth, fill: primary),
  )
  #place(
    top + left,
    dx: bleed-x,
    dy: bleed-y + band-depth,
    rect(width: 21cm, height: 0.22cm, fill: accent),
  )

  #set par(justify: false)
  #set text(hyphenate: false)

  // --- Inside the band ---
  #v(0.55cm)
  #text(font: font-head, size: 9pt, weight: "bold", fill: accent.lighten(45%), tracking: 0.22em)[
    $if(doctype)$#upper[$doctype$]$endif$
  ]

  #v(0.5cm)

  #text(font: font-head, size: 52pt, weight: "black", fill: white, tracking: -0.015em)[
    $if(title)$$title$$endif$
  ]

  #v(0.3cm)

  $if(subtitle)$
  #text(font: font-head, size: 17pt, weight: "regular", fill: white.darken(6%))[
    $subtitle$
  ]
  $endif$

  // --- Below the band ---
  // Clears the accent stripe at band-depth; tuned against the rendered cover.
  #v(1.5cm)

  $if(abstract)$
  #block(width: 92%)[
    #set par(leading: 0.78em, justify: false)
    #text(size: 11.5pt, fill: ink.lighten(10%))[$abstract$]
  ]
  $endif$

  #v(1fr)

  // Document-control block: the facts a reader needs to know which artefact
  // they are holding.
  #line(length: 100%, stroke: 0.8pt + primary)
  #v(0.45cm)
  #set text(font: font-head, size: 9.5pt, fill: ink)
  #grid(
    columns: (auto, 1fr),
    column-gutter: 1.1cm,
    row-gutter: 0.45em,
$if(version)$
    text(fill: muted)[Architecture version], text(weight: "bold")[$version$],
$endif$
$if(namespec)$
    text(fill: muted)[Namespec], [$namespec$],
$endif$
$if(status)$
    text(fill: muted)[Status], [$status$],
$endif$
$if(author)$
    text(fill: muted)[Author], [$author$],
$endif$
$if(date)$
    text(fill: muted)[Date], [$date$],
$endif$
$if(license)$
    text(fill: muted)[Licence], [$license$],
$endif$
  )

  #v(0.5cm)

  $if(notice)$
  #block(width: 100%)[
    #set par(leading: 0.7em, justify: false)
    #text(font: font-head, size: 7.8pt, fill: muted)[$notice$]
  ]
  $endif$
]

// =====================================================================
// COLOPHON + TABLE OF CONTENTS
// =====================================================================
// Front matter is numbered in roman so that body page 1 is the first page of
// actual design content.
#set page(numbering: "i")
#counter(page).update(1)

#{
  set text(font: font-head, size: 9pt, fill: muted)
  set par(justify: false, leading: 0.75em)

  text(size: 11pt, weight: "bold", fill: primary)[About this document]
  v(0.5em)
  line(length: 100%, stroke: 0.5pt + hairline)
  v(0.8em)

  grid(
    columns: (auto, 1fr),
    column-gutter: 1.0cm,
    row-gutter: 0.75em,
    $if(repo)$
    text(weight: "bold")[Repository], link("$repo$")[$repo$],
    $endif$
    $if(site)$
    text(weight: "bold")[Documentation], link("$site$")[$site$],
    $endif$
    $if(license)$
    text(weight: "bold")[Licence], [$license$ — see LICENSE in the repository.],
    $endif$
    text(weight: "bold")[Generated by], [`tools/pdf/build.sh`],
    text(weight: "bold")[Source of truth],
    [
      The chapters under `docs/design/`. This PDF is a generated consolidation
      of those chapters in v4.1 monolith section order per the concordance in
      `docs/design/00-INDEX.md`; it is regenerated from them and is never
      edited by hand.
    ],
    text(weight: "bold")[Citation],
    [
      Cite invariants as *INV-nn*, contracts by name, and chapters by
      path\#anchor. Legacy §-numbers from the v4.1 monolith remain resolvable
      through the concordance but are not used in new text.
    ],
  )
}

#v(1.6cm)

#{
  set text(font: font-head)

  // Outline entry levels mirror heading levels, and the assembled body starts
  // at level 2 (the document-title h1 lives on the cover). So level 2 is a
  // major monolith section and level 3 a subsection; a weight and colour step
  // between them lets the reader tell §13 from §13.11 at a glance.
  //
  // Depth stops at 3 on purpose: the level-4 headings ("Responsibilities",
  // "Invariants", "Smells") repeat in all fourteen domain chapters and would
  // swamp the outline with fifty near-identical lines.
  show outline.entry.where(level: 2): set text(size: 10.5pt, weight: "bold", fill: primary)
  show outline.entry.where(level: 2): set block(above: 1.25em)
  show outline.entry.where(level: 3): set text(size: 9pt, weight: "regular", fill: ink.lighten(12%))
  show outline.entry.where(level: 3): set block(above: 0.36em)

  outline(
    title: [
      #text(size: 20pt, weight: "bold", fill: primary, font: font-head)[Contents]
      #v(0.2em)
      #line(length: 18%, stroke: 2.5pt + accent)
      #v(0.8em)
    ],
    depth: 3,
    indent: 1.1em,
  )
}

// =====================================================================
// BODY
// =====================================================================
#pagebreak(weak: true)
#set page(numbering: "1")
#counter(page).update(1)

$body$

$for(include-after)$

$include-after$
$endfor$
