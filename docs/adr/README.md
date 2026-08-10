# Architecture Decision Records

Design-doc tiering (PDR-0002, `docs/product/decisions/0002-design-doc-tiering.md`):

- **Tier 0 — Constitution.** The HLD chapters under `docs/design/` (entry:
  `00-INDEX.md`; the locked core is `02-constitution.md`). Constitutional
  constraints — Namespec 2.0, the INV-01..45 invariants, authority boundaries,
  the evidence-routing rule (INV-07/INV-09), the no-op requirement, scaffold withdrawal — change only
  through an ADR that **names the displaced invariant**
  (`../design/ops/repo-structure.md#30-repository-handoff-and-custody` / repo
  discipline in the authority grant).
- **Tier 1 — ADRs** (this directory). Numbered; **body immutable once accepted —
  supersede, never edit**; metadata block append-only (ADR-0017, see below).
  Absorb change so Tier 0 stays stable.
- **Tier 2 — LLDs** (`docs/design/lld/`, just-in-time, one per subsystem per
  phase). Elaborate, never override. Header template:
  `docs/design/TEMPLATE-lld.md`.
- **Tier 3 — Leyline contracts** (code, Phase A onward). The seam truth;
  prose defers to schemas once they exist.

Citation convention (all tiers): invariants as **INV-nn**, contracts by
**name**, chapters by **path#anchor** — never bare section numbers. See
`docs/design/00-INDEX.md#citation-convention`.

Template: `TEMPLATE.md`. Number sequentially (`NNNN-slug.md`).

## Metadata and immutability

ADR-0017 draws the immutability line **inside** each record rather than at the
file, because two legitimate needs — forward pointers and later-discovered
reading context — have no home under a whole-file rule, and were already being
met by prohibited edits in seven records.

Every ADR opens with a delimited metadata block:

```text
# ADR-NNNN — Title
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->
Date / Status / Deciders / Tracker
Amends / Amended-by / Supersedes / Superseded-by
Notes: dated lines, each naming its causing record
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->
```

**The four rules:**

1. **One mutable region.** Between the markers is append-only-mutable.
   Everything after `adr-meta:end` is immutable once `Status: accepted` and
   changes only through a new ADR.
2. **Append-only, never rewrite.** Status advances, fields gain entries, Notes
   gain lines. Nothing already written is deleted or reworded — a mistaken note
   is corrected by a later note (INV-36).
3. **No uncaused annotation.** Every cross-reference and every Note names the
   ADR or PDR that caused it. This is the rule that keeps the block from
   becoming a silent-revision channel; enforce it first.
4. **Standing, never substance.** A Note records *that* standing changed and
   *where* to read why. It never restates, qualifies or reinterprets the
   decision. **If it needs a second sentence, write a new ADR.**

Enforcement is currently honour-system. The single boundary makes the mechanical
check cheap — digest the bytes after `adr-meta:end`, flag any change on an
accepted record — and that is the intended home for a legis policy at the git/CI
boundary. Stated plainly so no one assumes a gate that does not yet exist.
