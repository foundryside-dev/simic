# PDR-0020 — Record the Namespec 2.0 adoption and its cascade

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: the underlying decision is owner-authored — John directed the
Namespec 2.0 plan (prompts/namespec.md) as the session goal on 2026-08-09;
this PDR records its product-tier consequences.
Related: ADR-0008 (the architecture-tier decision), ADR-0003 (partially
superseded), simic-d8369760b9 (tracker), PDR-0006 (clean seam)

## Context

The owner directed a final consistency pass over the conceptual design and a
locked replacement naming constitution: Namespec 2.0 supersedes Namespec 1.0
in its entirety. Eight of fourteen codenames change (Sarpadia→Urborg,
Tamiyo→Ugin, Narset→Aurelia, Tezzeret→Urabrask, Urabrask→Jin-Gitaxias,
Augustin→Isperia, Kasmina→Wrenn, Oona→Tamiyo), and the thematic framing
becomes load-bearing: a Phyrexian industrial synthesis core
(Momir→Elesh→Urabrask→Jin-Gitaxias) inside a governance cage. Mechanics,
invariants, contracts and authority boundaries are unchanged. The cascade
was executed in the same session: ADR-0008, the constitution rewrite, every
design chapter and domain file, the appendices, root docs, the Structurizr
model and mermaid diagrams (re-rendered), the site, the wiki build inputs,
the product workspace, and the open tracker titles.

## The call

Record the adoption at product tier; no bet changes horizon. The Now bet
(design hardening, hld-review burn-down) continues under the new names.
Two product artifacts changed beyond mechanical renaming:

- `roadmap.md`'s Phase A bullet now marks the namespec-ADR work item as done
  (ADR-0008) — the remaining Phase A scope is unchanged.
- `vision.md`'s repo-discipline line now cites Namespec 2.0. This is a
  factual-reference update inside the restated HLD discipline, not a change
  to the authority grant, whose scope and reserved actions are untouched.

Timing note: with no code on disk (Phase A ahead), this was the last point
at which a total rename cost only documentation effort. The same change
after Phase A would have carried package, telemetry and test migration.

## Rationale

The rename resolves on new terms the naming ambiguity the peer review
flagged (simic-3a17fe545d): Tamiyo leaves the strategic role entirely, and
the two names that would otherwise have collided with the predecessor's
vocabulary (Urabrask, Tamiyo) are bounded by the clean seam (PDR-0006,
ADR-0003) plus the historical-interpretation rule and banners in ADR-0008.
The product scoreboard (metrics.md) is unaffected: the burn-down counts the
same items under new titles.

## Reversal trigger

Per ADR-0008: owner ruling only, before Phase A writes package names to
disk; after Phase A, reversal requires a new ADR with a migration plan.
Naming churn is pure cost — absent an owner ruling this stands unrevisited.
