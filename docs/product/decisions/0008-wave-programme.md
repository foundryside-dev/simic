# PDR-0008 — The burn-down runs as six region-based waves, stamped as tracker labels

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: requested by owner ("lay out the work program that starts
with 44f1"); layout and labels within the standing grant (prioritize/dispatch).
Related: PDR-0007, PDR-0009, wave:* labels in filigree

## Context
After the gate, 36 tasks were ready at once with no structure beyond priority.
Most are edits to the same design document; unsequenced parallel work would
collide, and the critical path (lexicographic admission → hysteresis →
uncertainty reconciliation) needed to stay visible.

## The call
Six waves, grouped by HLD region so each wave is one coherent editing pass,
stamped as filigree labels (pick up work with `filigree list --label=wave:N-…`):
- **wave:0-decks** — enabling work: consistency fixes, prompt updates,
  doc-tiering (done), HLD decomposition (done), §27.1 ADR.
- **wave:1-augustin** — the admission restructure: lexicographic keystone plus
  its dependents and the same-region judgement/evidence items. Critical path.
- **wave:2-momir** — generation: candidate ladder, ancestry drop,
  180-on-one-host, critic ADR + specs, esper-selector control.
- **wave:3-narset** — control loop: dense supervision, varying stub,
  channel harms, unfreeze protocol, cadence stability.
- **wave:4-leyline** — contracts and invariants closure: §9 shapes,
  RegionReport, blinding authority, invariant/test coverage. Phase A on-ramp.
- **wave:5-scoreboard** — narrative and criteria last, so the claim describes
  the system as amended: §2 re-motivation, two gates/ΔU_reference headline,
  retrieval-hit-rate, cost model (K/N producer), staleness crossing.
CI-skeleton design (simic-4da299ff46) runs as a parallel track. Waves are
guidance labels, not dependency edges; only real edit/logic dependencies got
edges.

## Rationale
Region grouping minimises edit collisions and lets parallel sessions own whole
waves; scoreboard-last prevents rewriting the claim twice; the only hard
ordering (admission chain) is enforced by real dependencies, not labels.

## Reversal trigger
If the 2026-08-31 burn-down date fires with waves unfinished, the next DECIDE
re-plans per PDR-0005. If wave grouping proves wrong in practice (cross-wave
edit collisions recurring), restructure the labels by a superseding PDR.
