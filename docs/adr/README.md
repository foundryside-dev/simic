# Architecture Decision Records

Design-doc tiering (PDR-0002, `docs/product/decisions/0002-design-doc-tiering.md`):

- **Tier 0 — Constitution.** The HLD chapters under `docs/design/` (entry:
  `00-INDEX.md`; the locked core is `02-constitution.md`). Constitutional
  constraints — Namespec 2.0, the INV-01..45 invariants, authority boundaries,
  the evidence-routing rule (INV-07/INV-09), the no-op requirement, scaffold withdrawal — change only
  through an ADR that **names the displaced invariant**
  (`../design/ops/repo-structure.md#30-repository-handoff-and-custody` / repo
  discipline in the authority grant).
- **Tier 1 — ADRs** (this directory). Numbered, immutable once accepted;
  supersede, never edit. Absorb change so Tier 0 stays stable.
- **Tier 2 — LLDs** (`docs/design/lld/`, just-in-time, one per subsystem per
  phase). Elaborate, never override. Header template:
  `docs/design/TEMPLATE-lld.md`.
- **Tier 3 — Leyline contracts** (code, Phase A onward). The seam truth;
  prose defers to schemas once they exist.

Citation convention (all tiers): invariants as **INV-nn**, contracts by
**name**, chapters by **path#anchor** — never bare section numbers. See
`docs/design/00-INDEX.md#citation-convention`.

Template: `TEMPLATE.md`. Number sequentially (`NNNN-slug.md`).
