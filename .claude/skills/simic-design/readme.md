# Simic Design System

Design system for **Simic — Counterfactual Generative Morphogenesis**, a research project by tachyon-beep (foundryside.dev). Simic is a lifecycle-driven neural training system: new structure is generated from the live state of a host network, then causally screened against doing nothing. Status: pre-implementation bootstrap — HLD v4.1, Namespec 1.0, locked.

Two surfaces:
1. **Marketing/overview site** (https://simic.foundryside.dev/) — hand-written static HTML, vanilla CSS, **zero JavaScript**, zero external requests. Source: `site/` in the repo.
2. **Design-docs wiki** (https://simic.foundryside.dev/design/) — MkDocs Material projection of `docs/design/`, teal palette, system fonts (`font: false`), light/dark toggle.

Source repo: https://github.com/foundryside-dev/simic — explore it for the canonical HLD chapters, site source (`site/style.css` is the ground truth for every token here), and wiki config (`tools/wiki/mkdocs.yml`).

## CONTENT FUNDAMENTALS

**Voice**: precise, declarative, technical-academic with literary confidence. Long, carefully-punctuated sentences with em dashes and semicolons. British-leaning spelling ("canonicalised", "artefact", "authorised"). No marketing language, no exclamation points, **no emoji ever**.

**Casing**: sentence case everywhere — headings ("The idea", "Why counterfactuals, not a reward function"), nav items ("Why this design"). The wordmark is lowercase `simic`; prose uses "Simic".

**Person**: third person throughout. The system and its domains are the subjects ("Nissa observes and reports"). No "we", no "you". Direct imperatives appear only in obligations ("Do not strip armour to speed the forward motion").

**Signature devices**:
- Domain codenames as actors with one-verb authority: "Momir designs. Elesh conforms. Tezzeret compiles."
- Invariant citations inline: `INV-15`, `INV-38`, set in mono accent.
- File paths as authority citations: `docs/design/01-claim.md` §4.
- Bold for the load-bearing clause of a paragraph, em for contrastive stress (*what*, *whether*, *who*).
- Honest hedging is a brand trait: "owner-recalled rather than re-derived", "Nothing on this site describes a running system or a measured result."
- Vivid coined vocabulary: "sedated or lysed", "earning its tenancy", "armour must cite its scar".

**Examples** (verbatim):
> "Doing nothing is a real competitor."
> "Absent signal stays absent and is never a fabricated zero."
> "Nissa sends the photograph directly to the designer. Narset sends only the assignment brief."

## VISUAL FOUNDATIONS

**Color**: OKLCH throughout. Blue-green world: hue 225 ("ink") carries all structure — backgrounds, text, borders; hue 175 (teal) carries emphasis — links, accents, active nav, callout spines; hue 85 (amber) is the sole warning color. Both themes come from one palette via `light-dark()`; `color-scheme: light dark` follows the OS, `[data-theme]` overrides. Max 2 background colors per page (`--color-bg`, `--color-bg-subtle`), plus tinted note backgrounds. Never pure black/white.

**Type**: system stacks only, on purpose (zero third-party requests — a privacy stance, not an omission). Body `system-ui…`; code/labels `ui-monospace…`. Mono is the brand's display voice: the wordmark, taglines, note labels, invariant chips, table `name` cells are all mono. Fluid heading sizes via `clamp()`. Base 1rem/1.65. h1 tracking -0.02em; mono labels tracked out (+0.04–0.08em) and often uppercase at ~0.78rem.

**Spacing/layout**: 8px-base scale (`--space-1..7` = 4/8/16/24/32/48/72px). Two widths: prose `--measure` 46rem, wide blocks (tables, diagrams, grids) `--page` 62rem. Prose is narrow by default; wide elements opt out.

**Backgrounds**: flat solid colors only. No gradients, no textures, no imagery, no photography. The only "images" are pre-rendered Mermaid diagram SVGs, shipped in light+dark pairs and swapped with the color tokens.

**Borders & radius**: 1px hairline `--color-border` everywhere (h2 top rules, table rows, cards, code); `--color-border-firm` for firmer edges. Radius `4px` (3px on inline code, 2px on focus rings). Callouts and quotes use a 3px left spine (teal = note/canon, amber = status, neutral = plain quote).

**Cards**: `--color-bg-subtle` fill, 1px border, 4px radius, **no shadow anywhere in the system**. Hover: border becomes accent. Grid `auto-fit, minmax(15rem, 1fr)`.

**Interaction states**: hover = color shift only (links darken toward text via `color-mix`; nav/wordmark turn accent). Active nav = heading color + 2px accent underline offset below. No press/scale effects. Focus = 2px accent outline, offset 2.

**Motion**: essentially none. One 120ms ease-out transition (skip link). `prefers-reduced-motion` kills everything. Do not add animation.

**Dark mode**: not an afterthought — every token is a `light-dark()` pair; diagrams swap variants; print forces light.

## ICONOGRAPHY

There is **no icon system**. The site ships zero icon fonts, zero icon SVG sets. The complete iconography:
- **The mark**: a teal diamond (`assets/mark.svg`, `#0f9b8e`), used as favicon and rendered as the `◈` character before the wordmark (`.wordmark::before`, colored accent). This is the closest thing to a logo — there is no wordmark image; the wordmark is live text in mono.
- **Unicode as UI glyphs**: `◈` (wordmark), `→` (forward links "Read the architecture →"), `›` (breadcrumbs), `·` (footer separators).
- **Diagrams**: pre-rendered Mermaid SVGs in `assets/diagrams/` (light/dark pairs) — the only illustrations in the brand.
- The wiki (Material theme) uses Material Design icons only for chrome (theme toggle, GitHub link, permalinks); content uses none.

Do not introduce icon sets, emoji, or drawn illustrations. When an icon urge strikes, use a unicode character or plain text.

## Index

- `styles.css` — global entry (imports everything below)
- `tokens/` — `colors.css`, `typography.css`, `spacing.css`, `base.css`
- `assets/` — `mark.svg`, `diagrams/` (6 Mermaid SVGs, light/dark pairs)
- `guidelines/` — foundation specimen cards
- `components/site/` — Masthead, SiteFooter, PageHead, Note, CanonQuote, Spine, CardGrid, DataTable, Split, Diagram (the full inventory `site/style.css` defines — nothing invented)
- `ui_kits/website/` — recreation of the overview page
- `ui_kits/wiki/` — recreation of a design-docs wiki page (MkDocs Material)
- `SKILL.md` — agent skill entry point

**Intentional additions**: none. The component list is exactly the class inventory of `site/style.css`. The wiki surface is stock MkDocs Material (teal/teal, `font: false`) — recreated as a UI kit screen, not as components.

**Fonts note**: no font files exist upstream by explicit design (system stacks only). Nothing was substituted.
