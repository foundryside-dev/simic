# Simic Design System

Design system for **Simic — Counterfactual Generative Morphogenesis**, a research project by tachyon-beep (foundryside.dev). Simic is a lifecycle-driven neural training system: new structure is generated from the live state of a host network, then causally screened against doing nothing. Status: pre-implementation bootstrap — HLD v4.1, Namespec 2.0, locked.

Two surfaces:
1. **Marketing/overview site** (https://simic.foundryside.dev/) — hand-written static HTML, vanilla CSS, **zero JavaScript**, zero external requests. Source: `site/` in the repo.
2. **Design-docs wiki** (https://simic.foundryside.dev/design/) — MkDocs Material projection of `docs/design/`, teal palette, system fonts (`font: false`), light/dark toggle.

Source repo: https://github.com/foundryside-dev/simic — explore it for the canonical HLD chapters, site source (`site/style.css` is the ground truth for every token here), and wiki config (`tools/wiki/mkdocs.yml`).

## CONTENT FUNDAMENTALS

**Voice**: precise, declarative, technical-academic with literary confidence. Long, carefully-punctuated sentences with em dashes and semicolons. British-leaning spelling ("canonicalised", "artefact", "authorised"). No marketing language, no exclamation points, **no emoji ever**.

**Casing**: sentence case everywhere — headings ("The idea", "Why counterfactuals, not a reward function"), nav items ("Why this design"). The wordmark is lowercase `simic`; prose uses "Simic".

**Person**: third person throughout. The system and its domains are the subjects ("Nissa observes and reports"). No "we", no "you". Direct imperatives appear only in obligations ("Do not strip armour to speed the forward motion").

**Signature devices**:
- Domain codenames as actors with one-verb authority: "Momir designs. Elesh conforms. Urabrask compiles."
- Invariant citations inline: `INV-15`, `INV-38`, set in mono accent.
- File paths as authority citations: `docs/design/01-claim.md` §4.
- Bold for the load-bearing clause of a paragraph, em for contrastive stress (*what*, *whether*, *who*).
- Honest hedging is a brand trait: "owner-recalled rather than re-derived", "Nothing on this site describes a running system or a measured result."
- Vivid coined vocabulary: "sedated or lysed", "earning its tenancy", "armour must cite its scar".

**Examples** (verbatim):
> "Doing nothing is a real competitor."
> "Absent signal stays absent and is never a fabricated zero."
> "Nissa sends the photograph directly to the designer. Aurelia sends only the assignment brief."

## VISUAL FOUNDATIONS

**Color**: OKLCH throughout. Blue-green world: hue 225 ("ink") carries all structure — backgrounds, text, borders; hue 175 (teal) carries emphasis — links, accents, active nav, callout spines; hue 85 (amber) is the sole warning color. A callout holds its family's hue on both sides of `light-dark()` — never let the dark side drift off-hue. Both themes come from one palette via `light-dark()`. Max 2 background colors per page (`--color-bg`, `--color-bg-subtle`), plus the two tinted note grounds (`--color-bg-note`, `--color-bg-note-status`). Never pure black/white.

**Theme model — two-state, not three.** The marketing site follows the OS via `color-scheme: light dark` and **has no toggle**: it ships zero JavaScript, so nothing ever sets `data-theme`. The `:root[data-theme]` rules in `site/style.css` are an unreached hook, kept for a future toggle; the diagrams cannot follow them at all (they select via `<picture>`, resolved by the layout engine). Only the **wiki** is three-state — MkDocs Material supplies its own toggle. Do not describe the marketing site as having a theme switcher.

**Type**: system stacks only, on purpose (zero third-party requests — a privacy stance, not an omission). Body `system-ui…`; code/labels `ui-monospace…`. Mono is the brand's display voice: the wordmark, taglines, note labels, invariant chips, table `name` cells are all mono. Fluid heading sizes via `clamp()`. Base 1rem/1.65. h1 tracking -0.02em; mono labels tracked out (+0.04–0.08em) and often uppercase at ~0.78rem.

**Spacing/layout**: 8px-base scale (`--space-1..7` = 4/8/16/24/32/48/72px). Two widths: prose `--measure` 46rem, wide blocks (tables, diagrams, grids) `--page` 62rem. Prose is narrow by default; wide elements opt out.

**Backgrounds**: flat solid colors only. No gradients, no textures, no imagery, no photography. The only "images" are pre-rendered Mermaid diagram SVGs, shipped in light+dark pairs and selected by `<picture>` + `media="screen and (prefers-color-scheme: dark)"` — one variant fetched, and print falls through to the light one. The single exception is `site/assets/social-card.png`, a 1200×630 Open Graph card rendered from `social-card.src.html`; it is a fixed dark artefact and does not track the viewer's theme.

**Borders & radius**: 1px hairline `--color-border` everywhere (h2 top rules, table rows, cards, code); `--color-border-firm` for firmer edges. Radius `4px` (3px on inline code, 2px on focus rings). Callouts and quotes use a 3px left spine (teal = note/canon, amber = status, neutral = plain quote).

**Cards**: `--color-bg-subtle` fill, 1px border, 4px radius, **no shadow anywhere in the system**. Hover: border becomes accent. Grid `auto-fit, minmax(15rem, 1fr)`.

**Interaction states**: hover = color shift only (links darken toward text via `color-mix`; nav/wordmark turn accent). Active nav = heading color + 2px accent underline offset below. No press/scale effects. Focus = 2px accent outline, offset 2.

**Motion**: essentially none. One 120ms ease-out transition (skip link). `prefers-reduced-motion` kills everything. Do not add animation.

**Dark mode**: not an afterthought — every token is a `light-dark()` pair; diagrams ship as light/dark pairs selected by `<picture>`; print falls back to light.

<!-- CORRECTION (2026-08-09, static-site review M6; resolved same day at
     re-export). The paragraphs above are hand-corrected. The upstream SPA
     export's descriptors asserted a three-state toggle on the marketing site. That
     export was re-pulled on 2026-08-09 (see the Index note below) and the
     pulled descriptors were checked against this correction — no three-state
     claim survives on disk. The two facts to preserve if anything regresses:
       1. marketing site is TWO-state (system preference only, zero JS);
          `[data-theme]` is an unreached hook. Only the wiki is three-state.
       2. diagrams select via <picture> + `media="screen and
          (prefers-color-scheme: dark)"`, so they cannot follow `[data-theme]`
          at all, and print falls through to the light variant with no override.
     Verified against site/style.css and site/*.html on 2026-08-09. -->



## ICONOGRAPHY

There is **no icon system**. The site ships zero icon fonts, zero icon SVG sets. The complete iconography:
- **The mark**: a teal diamond, used as favicon and rendered as the `◈` character before the wordmark (`.wordmark::before`, colored accent). This is the closest thing to a logo — there is no wordmark image; the wordmark is live text in mono. One file, two deployed copies kept byte-identical: `site/assets/mark.svg` (marketing) and `tools/wiki/assets/mark.svg` (wiki logo + favicon). Its `#0f9b8e` is a fixed hex, not a token — a favicon cannot use `light-dark()` — and sits between `--teal-600` and `--teal-400`; do not introduce a fourth teal to match it.
- **Unicode as UI glyphs**: `◈` (wordmark), `→` (forward links "Read the architecture →"), `›` (breadcrumbs), `·` (footer separators).
- **Diagrams**: pre-rendered Mermaid SVGs in `assets/diagrams/` (light/dark pairs) — the only illustrations in the brand.
- The wiki (Material theme) uses Material Design icons only for chrome (theme toggle, GitHub link, permalinks); content uses none.

Do not introduce icon sets, emoji, or drawn illustrations. When an icon urge strikes, use a unicode character or plain text.

## Index

> **EXPORT RECOVERED — 2026-08-09.** The upstream Claude Design project
> (`SimicDesignSystem_5a908e`) reappeared in the owner's writable project
> list and all 57 missing source files were pulled verbatim via `DesignSync`
> (PDR-0019's re-export fork; tracker simic-42e575b93c). All 12 bundle
> `sourceHashes` verify (sha256 prefix) against the pulled component
> sources — these are the originals, not a reconstruction. `styles.css` is
> restored to its original four-`@import` form; the token layer now lives in
> `tokens/*.css` as upstream intended. `site/style.css` remains the token
> ground truth: any future divergence resolves toward the site.
>
> The recorded corrections were **re-applied on top of the pull** in the same
> sync (the verbatim pull and the correction pass are separate commits, so
> the diff between them is the divergence record):
>
> | Token | corrected value (matches `site/style.css`) | as pulled (stale) |
> |---|---|---|
> | `--color-bg-note` dark | hue **175** | hue **195** |
> | `--color-bg-note-status` dark | hue **85** | hue **75** |
> | `--color-accent-quiet` | **deleted** (unused; 4.22:1 on `--color-bg`, fails AA) | declared, and allowlisted at `_adherence.oxlintrc.json:124,192` |
>
> `_ds_manifest.json` and `_adherence.oxlintrc.json` carry the same three
> corrections; the manifest's 43 tokens were diffed against `site/style.css`
> (clean — the only differences are `calc()` notation inside three `clamp()`
> values, functionally identical). Namespec 2.0 (ADR-0008) renames were
> applied to pulled specimen copy (canonical sentence, newsroom rule, wiki
> nav, footer version stamps).
>
> **The upstream project is now BEHIND this directory**: it still carries the
> three stale token values, Namespec 1.0 names, and pre-rename diagram SVGs.
> Pushing the corrected tree back upstream (`/design-sync`) is owner-gated
> and has not been done. Until then, do not re-pull over this directory
> without re-applying everything in this note.

- `styles.css` — global entry (imports everything below)
- `tokens/` — `colors.css`, `typography.css`, `spacing.css`, `base.css`
- `assets/` — `mark.svg`, `diagrams/` (6 Mermaid SVGs, light/dark pairs) — sourced from the repo (`site/assets/mark.svg`, `site/assets/diagrams/`), which stays the canonical copy
- `guidelines/` — foundation specimen cards (14 files)
- `components/{content,data,navigation}/` — Masthead, SiteFooter, PageHead, Note, CanonQuote, Spine, CardGrid, DataTable, Split, Diagram (the full inventory `site/style.css` defines — nothing invented)
- `ui_kits/website/` — recreation of the overview page (2 screens, click-through)
- `ui_kits/wiki/` — recreation of a design-docs wiki page (MkDocs Material)
- `_ds_manifest.json` — component/token index (43 tokens, corrected)
- `SKILL.md` — agent skill entry point

**Intentional additions**: none. The component list is exactly the class inventory of `site/style.css`. The wiki surface is stock MkDocs Material (teal/teal, `font: false`) — recreated as a UI kit screen, not as components.

**Fonts note**: no font files exist upstream by explicit design (system stacks only). Nothing was substituted.
