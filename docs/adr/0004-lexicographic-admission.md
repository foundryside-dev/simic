# ADR-0004 — Make admission lexicographic: tail-risk veto before utility comparison

Date: 2026-08-08 · Status: accepted
Deciders: John (gate adjudication PDR-0007; peer review §22 accepted into the
wave programme) · Tracker: simic-ae3caf44f1

## Context

Augustin as specified is a scalar comparator: it computes the admission
utility `u_admit` (`../design/domains/augustin.md#admission-utility`), ranks
eligible candidates, picks the maximum, and checks it clears no-op. That is a
quality judgement. The judge's real question is a risk judgement — not "which
of these is best" but "is any of these going to destroy the host" — and the
document conflated the two under one utility expression.

The eligibility gate
(`../design/04-architecture.md#1010-independent-adjudication`) is the risk
half, and it was binary: hard Urabrask defects make a candidate ineligible,
full stop. But "will this blow up the host" is not a defect flag — it is a
**tail estimate**. A candidate can pass every conformance check and still be
the one that costs a rollback, and the `ξR_c` risk term buried in a weighted
sum cannot express that: a large enough measured benefit will always outweigh
any finite risk charge. The failure mode is constitutional, not parametric —
no re-weighting fixes it. (Peer review:
`../concept/reviews/2026-08-08-esper-pivot-peer-review.md` §22.)

The Tolaria rollback is what makes the asymmetry real. The downside of a bad
admission is not a bad growth — it is losing the trajectory back to the last
snapshot. That loss grows with snapshot distance, which Tolaria already
tracks.

## Decision

**Admission is lexicographic, not scalar. Survive the tail test first;
compete on utility second.** Augustin adjudicates in three ordered stages,
and no later stage can reopen an earlier one:

1. **Hard eligibility** (unchanged): structural/semantic identity,
   compilation conformance, runtime and gradient checks, determinism,
   evidence completeness for the assurance class, budget.
2. **Tail-risk veto** (new): Augustin estimates, per candidate, the tail of
   the intervention-outcome distribution — the probability-weighted
   catastrophic case, not the expectation — from certified Urabrask evidence
   (integration shock, instability, numerical events, trajectory behaviour).
   A candidate whose tail estimate breaches the veto threshold is removed
   from contention. **The veto is not tradeable against utility: no measured
   benefit can offset it.** The assurance class owns the veto operating
   point — this is the class's primary semantics, not merely an
   evidence-completeness dial — and the threshold is priced against current
   snapshot distance: the further the live trajectory sits from its last
   snapshot, the more a rollback costs, the tighter the veto.
3. **Utility competition** (re-scoped): `u_admit` ranks the survivors
   against mandatory no-op exactly as before, with `ξR_c` now pricing
   **expected** risk only. Tail risk lives in stage 2 and nowhere else.

No-op never faces the veto: no intervention carries no intervention tail
risk, so the no-op alternative survives every stage by construction —
INV-15/INV-16 are preserved, and a pool whose every candidate is vetoed
resolves to `NO_OP` (or `DEFER`/`REQUIRE_RETEST` under the applicable
policy), never to "least-bad survivor".

Division of labour this buys: **Momir optimises expected value** and can
afford to be wrong often, because its errors cost compute. **Augustin bounds
worst case** and must be conservative, because its errors cost the host.
They are not redundant models of one quantity; they optimise **different
functionals of the same distribution**.

Boundary discipline: Urabrask **measures** the quantities the tail estimate
consumes; Augustin **forms and applies** the estimate. Evidence–judgement
separation (INV-18) and provider blindness (INV-17) are untouched.

## Displaced constraints

- **INV-45 added** (new constitutional invariant): *Lexicographic
  admission: the tail-risk veto is adjudicated before any utility
  comparison and cannot be traded against measured benefit; the assurance
  class owns the veto operating point.* The invariant set grows 44 → 45; no
  existing invariant is renumbered or displaced.
- **`u_admit` semantics amended** (`../design/domains/augustin.md`): `ξR_c`
  is re-scoped from "policy risk" to **expected-risk price**; worst-case
  risk is expressible only through the stage-2 veto.
- **Eligibility gate amended**
  (`../design/04-architecture.md#1010-independent-adjudication`): the gate
  is no longer the sole risk mechanism; it retains conformance facts and
  cedes tail risk to the veto stage.
- **`AdmissionDecision` contract extended**
  (`../design/05-leyline-contracts.md#915-admissiondecision`): gains
  `tail_veto_results` so every veto (and every thin-margin pass) is
  recorded per candidate — required by complete negative retention (INV-31)
  and by the containment route-back (simic-d6ea02f9a9).
- INV-15, INV-16, INV-17, INV-18 reaffirmed unamended.

## Options considered

- **Keep the scalar form and raise `ξ`** — rejected: any finite weight is
  outbid by a large enough measured benefit; the defect is structural
  (tradeability), not parametric, and a tunable weight on catastrophe is
  Goodhart bait of exactly the class the pivot exists to eliminate.
- **Make tail risk another Urabrask hard-defect flag** — rejected: a tail
  estimate is a judgement under uncertainty, not a conformance fact;
  putting it in Urabrask moves adjudication into the evidence provider and
  violates INV-18. The binary form also gives the assurance class nothing
  to own.
- **Separate veto model outside Augustin (a fourth authority)** — rejected:
  bounding worst case *is* the judge's mandate ("Augustin judges"); a
  standalone veto component would be a second judge, splitting warrant
  accountability that ADR-scoped work on containment (simic-d6ea02f9a9)
  deliberately concentrates in Augustin.

## Consequences

- The Momir/Augustin split now has a defensible justification — different
  functionals of the same distribution — that survives "why do you need two
  models predicting utility."
- The assurance class acquires real semantics: it sets the veto operating
  point, rather than only adjusting evidence-completeness requirements.
- The harm-ceiling guardrail (`../product/metrics.md`) can now bind: its
  ceiling is the veto's declared operating point per assurance class
  (numbers land with the Phase-A policy LLD; the *shape* is fixed here).
- **Harder:** the veto needs a calibrated tail estimator, and its natural
  training signal is rare by construction — if the veto works, rollbacks
  approach zero and starve it. Mitigations (permanent deliberately-harmful
  QA-pool members, near-miss recording) are owned by simic-d6ea02f9a9, not
  this ADR.
- **Seam:** continued-tenancy adjudication keeps its current shape here;
  the retention side is reshaped by the hysteresis item (simic-ed2698fafd)
  and must respect the same non-tradeability principle when it lands.
- Files updated by this ADR: `../design/domains/augustin.md`,
  `../design/04-architecture.md` (§7.4, §10.10),
  `../design/07-counterfactual-engine.md` (§14.4.2),
  `../design/02-constitution.md` (§18 + Appendix B),
  `../design/05-leyline-contracts.md` (§9.15),
  `../design/03-principles.md` (§6.5), invariant-count references
  (`AGENTS.md`, `../design/00-INDEX.md`, `README.md` here).
- **Reversal trigger:** if, at MVP scale, no achievable calibration gives
  the veto a useful operating region — it vetoes everything or nothing
  across the assurance classes — the *stage structure* is reopened by ADR.
  The non-tradeability principle itself survives any such revision: a
  replacement mechanism may change how tail risk is estimated, never
  whether it can be bought off.
