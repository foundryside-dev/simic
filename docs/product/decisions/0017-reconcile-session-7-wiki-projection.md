# PDR-0017 — Reconcile session 7 (ADR-0007 wiki projection regime) into the workspace

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: not required — reconciliation record; the underlying acts
were owner-directed in-session 2026-08-09 (recorded in ADR-0007's
deciders line) and are already committed and pushed.
Related: ADR-0007, simic-dd5a578332 (closed), PDR-0014 (documentation
derivation programme), commits 7a6ed0f and 19e7d48

## Context

A working session on 2026-08-09 landed two pushed commits on top of the
session-6 checkpoint without running `/product-checkpoint`: 7a6ed0f
(canonical Structurizr model of the 14 domains, `docs/design/assets/
model.dsl`, plus ADR-0007) and 19e7d48 (model compiled to SVGs, generated
`reference/` registries scraped from the constitution and contracts, ADRs
staged into the published wiki as `decisions/`, ~87 INV/ADR citations
linkified render-only). Tracker item simic-dd5a578332 was opened and
closed same-day with a verified close reason (strict build, 49 pages,
zero canonical-chapter edits). The session-8 ORIENT found the workspace
trailing this reality.

## The call

Record the session-7 work as an extension of the PDR-0014 documentation
derivation programme, governed by **ADR-0007**: `model.dsl` is canonical
but subordinate to the chapters; wiki `reference/` pages are generated,
never authored; ADRs stay canonical in `docs/adr/` and are projected into
the wiki; citation linkification is presentation-only. No product bet
changed horizon; no new product decision was embedded beyond what ADR-0007
itself records at design tier. The push was owner-directed, so no
authority flag is raised retroactively.

## Rationale

The work is squarely inside the already-decided derivation programme
(PDR-0014: the wiki/site/PDF are derived artifacts of docs/design/), so
it needs a reconciliation record, not a new bet. The gap worth naming is
process, not substance: a session that lands ADR-tier decisions should
close with a checkpoint, or the next session's RESUME starts from a
stale brief — exactly what happened here. One session of drift is cheap;
the pattern would not be.

## Reversal trigger

None for the reconciliation itself (it records history). ADR-0007's own
regime reverses only by superseding ADR — e.g. if generated reference
registries start drifting from the constitution text they scrape, the
generated-never-authored rule gets revisited there, not here.
