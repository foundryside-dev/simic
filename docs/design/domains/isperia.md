<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2210–2291 · amended by ADR-0004 (lexicographic admission), ADR-0005 (retention hysteresis), ADR-0010 (containment accountability) -->
### 13.11 Isperia — Independent Judge

#### Responsibilities

- consume blinded Jin-Gitaxias `QualityReport` records;
- apply hard eligibility requirements;
- apply the tail-risk veto before any utility comparison;
- enforce Ugin’s active strategic envelope;
- calculate adjudicated utility, risk and uncertainty charges;
- compare surviving candidates against mandatory no-op;
- apply independent admission-audit rules;
- return `ADMIT`, `NO_OP`, `REJECT`, `DEFER` or `REQUIRE_RETEST`;
- issue admission warrants;
- adjudicate continued tenancy of committed structures;
- issue maintenance warrants;
- calibrate thresholds on validation trajectories only;
- own containment accountability: adjudicate every emergency containment back to the warrant and policy version that admitted the growth (ADR-0010);
- re-adjudicate the historical corpus under candidate policy versions (retrospective sweeps — analysis records only, INV-36);
- and emit explicit decision reasons and policy versions.

#### Lexicographic admission order (ADR-0004)

Admission is a risk judgement before it is a quality judgement. Isperia
adjudicates in three ordered stages, and no later stage can reopen an
earlier one:

1. **Hard eligibility.** Conformance facts from the blinded
   `QualityReport`: identity, compilation, runtime and gradient checks,
   determinism, evidence completeness for the assurance class, budget.
2. **Tail-risk veto.** Isperia estimates, per candidate, the tail of the
   intervention-outcome distribution — the catastrophic case, not the
   expectation — from certified evidence (integration shock, instability,
   numerical events, trajectory behaviour). A candidate whose tail estimate
   breaches the veto threshold is out of contention, and **no measured
   benefit can offset the veto** (INV-45). The assurance class owns the
   veto operating point, and the threshold is priced against current
   snapshot distance: the further the trajectory sits from its last
   snapshot, the more a rollback costs, the tighter the veto.
3. **Utility competition.** `u_admit` ranks the survivors against
   mandatory no-op.

No-op never faces the veto — no intervention carries no intervention tail
risk — so it survives every stage by construction. A pool whose every
candidate is vetoed resolves to `NO_OP` (or `DEFER`/`REQUIRE_RETEST` under
policy), never to a least-bad survivor.

This order is what justifies the Momir/Isperia split: **Momir optimises
expected value** and can afford to be wrong often, because its errors cost
compute; **Isperia bounds worst case** and must be conservative, because
its errors cost the host. They optimise different functionals of the same
distribution.

<!-- hld: added 2026-08-09 (simic-66c357e06a, peer review) -->
#### The veto's training signal

The veto's one true-positive signal — a containment rollback (ADR-0010) —
is rare **by construction**: if the veto works, rollbacks approach zero,
which starves exactly the thing that would improve it. Two substitutes
keep the signal alive, both cheap:

- **Permanent harmful fixtures.** The deliberately harmful and
  long-term-regressing candidates in the QA pool (`07-counterfactual-engine.md`)
  are permanent members, not a curriculum stage — the veto is continuously
  exercised against known-bad structure for as long as the system runs.
- **Near-misses.** A candidate that passed the veto with a thin margin and
  then produced large integration shock *without* triggering containment is
  recorded as a near-miss: the join of its `tail_veto_results` margin
  (INV-31) with its post-commit shock outcome in Urborg. Near-misses are
  dense where rollbacks are sparse, and they are the same distribution's
  shoulder, so they carry most of the usable signal. They are analysis
  records over immutable history (INV-36), never retroactive verdicts.

#### Admission utility

For a candidate \(c\) that survived eligibility and the tail-risk veto,
state \(s\), and horizon \(H\):

$$
u_{\mathrm{admit}}(c,s,H)
=
\mathcal{L}_{\mathrm{no-op}}(s,H)
-
\mathcal{L}_{c}(s,H)
-
\lambda C_c
-
\mu S_c
-
\nu P_c
-
\xi R_c
-
\omega U_c,
$$

where:

- \(C_c\) is compute and latency cost;
- \(S_c\) is integration shock;
- \(P_c\) is parameter and memory cost;
- \(R_c\) is **expected** policy risk — tail risk is expressible only
  through the stage-2 veto, never as a utility charge (ADR-0004);
- \(U_c\) is **evidence** uncertainty — incompleteness for the assurance
  class, horizon extrapolation, and data-role shift in what was measured.
  Execution and surrogate noise is priced exactly once, in the decision
  bound's \(\kappa\sigma_{\mathrm{exec}}\)
  (`../07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins`),
  never here: the two coefficients cover disjoint, pre-registered sources
  (simic-01f9ee1160).

The no-op candidate has policy utility exactly zero.

#### Continued-tenancy utility

For a resident growth:

$$
u_{\mathrm{retain}}(c,s,H)
=
G_{c:\mathrm{no-op}}(s,H)
-
\lambda C_c
-
\nu P_c
-
\xi R_c
-
\omega U_c.
$$

Installation shock is omitted because a resident growth is no longer integrating. Shared cost terms use shared weights unless a difference is structurally justified and pre-registered — the asymmetry between admission and retention lives in the thresholds, never in per-side weights.

<!-- hld: added 2026-08-09 (simic-e2ae14c8bd, peer review) -->
The formalism's similarity to admission must not be read as parity of evidence. Admission's \(G_{c:\mathrm{no-op}}\) is measured on matched branches from one snapshot over one future — the intervention effect, cleanly. Tenancy's honest counterfactual — the host that never received the growth — no longer exists: measuring it would mean running a parallel no-op branch for the entire tenure, a permanent doubling of training cost per committed growth. What the re-adaptation branch actually measures is **replaceability at horizon \(H\)**, a different and weaker quantity dominated by the choice of \(H\) (§2.4 in `../01-claim.md`). **Maintenance decisions operate under an explicitly weaker evidentiary standard than admission decisions**, and the machinery leans accordingly: the retention threshold sits below the admission threshold (ADR-0005), and Emrakul is biased toward `SEDATE` over `LYSE` for epistemic reasons as much as safety ones — the reversible act is what a judge may take when the evidence cannot fully support the irreversible one.

The system has three tiers of evidentiary strength, in strictly decreasing order: **admission** (matched common-future branches — the full counterfactual), **tenancy** (re-adaptation at horizon \(H\) — replaceability, not intrinsic value), and **allocation** (Ugin's aggregate outcomes — no per-decision counterfactual at all). Each authority's decision machinery claims no more than its tier can support.

During bootstrap the tenancy tier is anchored: on the declared anchor host set, every admission's no-op branch runs for the full tenure (the anchor corpus, ADR-0011), and the re-adaptation instrument — including the choice of \(H\) — is calibrated against that ground truth at seed-level counting (INV-32). After the scaffold withdraws, the weaker standard is measured, not assumed.

#### Retention hysteresis (ADR-0005)

Admission and retention thresholds form a Schmitt trigger: admission requires the conservative margin over no-op to exceed \(\theta_{\mathrm{admit}}\); continued tenancy requires only \(u_{\mathrm{retain}} \ge \theta_{\mathrm{retain}}\), with \(\theta_{\mathrm{retain}} = \theta_{\mathrm{admit}} - \Delta\) and \(\Delta > 0\) strictly (INV-33). A resident growth that drifts modestly below the admission bar is not thereby lysed.

The hysteresis band \(\Delta\) is an explicit, versioned Isperia policy parameter, carried by `adjudication_policy_version`, and its width is measured against observed execution noise \(\sigma_{\mathrm{exec}}\) — sized so noise-driven estimate movement cannot cross both thresholds — never picked by feel. Cooldowns are a frequency limiter for pathological cases, not the stability mechanism: they are a time-domain patch and do not remove a threshold-domain instability.

#### Containment accountability (ADR-0010)

A rollback is evidence that a warrant was issued wrongly, and warrants are Isperia's sole output — nothing else in the system could have prevented the admission. Tolaria owns detection and the rollback itself: waiting for adjudication while the host produces NaNs would be absurd. Tolaria acts, then reports. Detect-and-contain is mechanical; accountability is judicial.

Every containment event therefore routes back to the decision, not just to the log. `AdmissionDecision` already carries `evidence_digest`, `selected_semantic_hash`, `adjudication_policy_version` and the per-candidate eligibility and veto results, so the containment record names the warrant that authorised the growth, the policy version in force, and the specific checks that passed and should not have. That is a defect report against a policy, actionable in a way "candidate X was bad" is not.

Blame attaches to the policy version, never to Isperia-the-component. With the initial rule-driven adjudicator this is literally true: a rollback means the declared thresholds were wrong, and the fix is an ADR and a version bump. Retrospective re-adjudication then asks directly: *under the revised policy, would this warrant have issued?* — a regression test for judgement. Containment catastrophes carry their own failure code (`CONTAINMENT_CATASTROPHE`, `urborg.md`); they are never booked as integration shock, because one is a cost and the other is a veto failure.

<!-- hld: added 2026-08-09 (simic-43f5e2264a, peer review) -->
#### Retrospective policy re-adjudication

Isperia's rule-driven policy is the Esper reward function promoted to a versioned, hand-editable artefact — and the promotion pays for itself here. Because `QualityReport` records are immutable, stored in Urborg, and Isperia consumes nothing else, the entire historical corpus can be re-adjudicated under a candidate policy with **zero retraining and zero GPU time**: sweep the declared weights (λ, μ, ν, ξ, ω) across every decision the system has ever made and read off how admission and tenancy history would have changed. This is the direct answer to the pivot's originating failure — a reward whose behaviour could not be tuned even when the signal was provably present — and it is a first-class capability, not an incidental property of the storage layer.

Three uses are named:

- **Policy revision.** Before an `adjudication_policy_version` bump, the candidate policy is swept over the historical corpus and the decision deltas travel with the ADR as evidence.
- **Regression testing judgement.** Every containment (ADR-0010) asks: under the revised policy, would this warrant have issued? A policy fix that does not flip the decision it was written for has not fixed anything.
- **Sensitivity analysis.** The §22.6 metric "policy sensitivity to declared weights" is measured retrospectively over the full corpus rather than estimated from a sample.

Boundaries: re-adjudication produces analysis records, never rewrites — historical decisions stand, and corrections create new records (INV-36). Sweeps consume the same blinded views as live adjudication (INV-17, INV-37). And a sweep is evidence for revising a policy, not a calibration procedure: threshold calibration still binds to validation trajectories only, because weights tuned against the full history are the old overfit reward in a new costume.

#### Invariants

- Isperia does not execute tests, alter data, call kernels or rerun a branch.
- It cannot see candidate source during adjudication.
- It can select no-op even when Ugin allocated budget and Aurelia commissioned growth.
- Hard Jin-Gitaxias defects make a candidate ineligible according to the applicable Leyline policy.
- The tail-risk veto is adjudicated before any utility comparison and cannot be traded against measured benefit (INV-45).
- Every veto, and every thin-margin pass, is recorded per candidate in `tail_veto_results` (INV-31).
- Decision thresholds are frozen before confirmatory runs.
- Every warrant is bound to a specific evidence digest, semantic hash, envelope and policy version.
- Every containment event is adjudicated back to its admitting warrant and `adjudication_policy_version`; the containment defect attaches to the policy version (INV-28).

#### Smell

> If Isperia asks for a more favourable minibatch after seeing the evidence, the judge has tampered with the case.

> If a candidate's measured benefit is cited as a reason to soften the veto, the judge has repriced catastrophe.

> If a containment is filed as integration shock, a veto failure has been repriced as a cost.
