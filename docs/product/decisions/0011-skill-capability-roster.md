# PDR-0011 — Project skill-capability roster: commissioned packs enabled, commissioning queue reconciled

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner directed installation of the commissioned packs
and the governance/doc packs ("please put the first three into the project as
well as document management and anything else that's relevant"), and
committed the roster himself (commits 03e62c0, 4538481).
Related: simic-e84fe6737c (in-flight skill-pack prompt updates), commits
03e62c0 + 4538481 (.claude/settings.json)

## Context
Three of the five packs commissioned for simic landed in the foundryside
marketplace 2026-08-08: yzmir-counterfactual-statistics (Urabrask/Augustin
statistics), yzmir-structure-synthesis (Momir/Elesh graph generation +
canonicalisation), axiom-tensor-compiler-engineering (Tezzeret). Two
commissioned packs have not yet landed: **axiom-contract-engineering** and
**yzmir-training-state-engineering** (named in simic-e84fe6737c). A
session gap-analysis, run before the tracker was consulted, independently
re-derived the contract-engineering gap — the tracker already knew.

## The call
Project roster (in .claude/settings.json, committed by owner): the three
landed commissioned packs, plus muna-wiki-management (docs/design/ suite
governance), muna-panel-review (hld-review passes), muna-document-designer,
axiom-procedural-architecture (staged-procedure critique of the eleven-verb
pipeline), and axiom-solution-architect (ADR/RTM discipline, pinned at
project level). axiom-distributed-systems deferred until branch fleets leave
one box. Commissioning queue after reconciliation: (1) the two in-flight
packs land first — status check owed; (2) Nissa telemetry / representation
diagnostics remains the one agent domain with zero pack coverage — strongest
next commission; (3) research-artifact release & reporting (NeurIPS
checklist, FAIR, RO-Crate, Model Cards / Reward-Report-style templates) is
deferred to the publication horizon, per two owner-supplied research dumps
evaluated this session.

## Rationale
Packs map one-to-one onto domain disciplines the HLD names; enabling at
project level makes them load for any agent in the repo, not just under the
owner's user config. The queue ordering follows coverage risk: Nissa's
discipline (what to measure inside a live network) has no substitute pack;
publication packaging has partial coverage (counterfactual-statistics owns
the statistical-reporting half) and no near-term consumer.

## Reversal trigger
Disable any pack whose triggering measurably degrades sessions (wrong-skill
invocations, context bloat) — roster is cheap-reversible config. The queue
reopens if either in-flight pack lands with different scope than
commissioned, or if Phase A work surfaces a gap ahead of Nissa telemetry.
