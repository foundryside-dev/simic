# PDR-0012 — Commissioning briefs become repo artifacts; prompt updates delivered as per-pack update briefs

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: within grant (workspace/dispatch artifact); the relay of the
briefs to the in-flight upstream sessions is owner-only and flagged in
current-state.md.
Related: simic-e84fe6737c (closed), PDR-0011 (roster + commissioning queue),
docs/product/commissioning/

## Context

simic-e84fe6737c required updating the five skill-creator prompts (written
against HLD v2.0) for v4.1 section shifts and the execution-regime model. An
exhaustive search — simic, skillpacks (working tree, git history, branches),
esper, esper-lite, all recent home directories — found no prompt files: the
prompts were conversation artifacts in upstream skill-creator sessions.
There was nothing on disk to edit, and the two still-unlanded packs
(axiom-contract-engineering, yzmir-training-state-engineering) are being
built from prompts this project cannot see.

## The call

Commissioning state moves into the product workspace:
`docs/product/commissioning/` now holds (1) a README recording queue state,
the citation discipline (path#anchor + INV-nn, entry `00-INDEX.md`), and
the full v2.0→v4.1 §-shift map; (2) per-pack prompt artifacts. For
**yzmir-training-state-engineering** (still in flight upstream) that is an
**update brief** — a scope addition: the three-regime execution model,
replicate groups, σ_exec fields, decision-aware gates. For
**axiom-contract-engineering** the owner directed in-session (2026-08-08)
that the delta be consolidated into a **full commissioning prompt**
(re-citation plus the v4.1 developments the v2.0 prompt predates:
`tail_veto_results`/ADR-0004, versioned hysteresis band/ADR-0005, ADR-0002
definition lifecycle, and the silent-default failure class front and
centre), and is re-commissioning the pack from it now — superseding the
original in-flight build. The three landed packs need no update — domains
are unchanged. Future commissions author their prompts here first, as
files.

## Rationale

Durable files beat conversation artifacts — the same continuity discipline
the workspace exists for; this failure mode (project-critical prompt text
living only in a chat) is now unrepresentable for future commissions.
Update briefs were chosen over re-authoring full prompts because the
in-flight upstream builds already run on the original prompts; a wholesale
rewrite risks diverging from what is actually being built, while a delta
brief composes with it.

## Reversal trigger

If either in-flight pack lands without having incorporated its brief
(stale §-refs or missing execution-regime scope), the brief is promoted to
a full re-commissioning prompt authored from this directory. PDR-0011's
existing trigger (pack lands with materially different scope than
commissioned) stands unchanged.
