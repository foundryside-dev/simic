<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2210–2291 · amended by ADR-0004 (lexicographic admission), ADR-0005 (retention hysteresis) -->
### 13.11 Augustin — Independent Judge

#### Responsibilities

- consume blinded Urabrask `QualityReport` records;
- apply hard eligibility requirements;
- apply the tail-risk veto before any utility comparison;
- enforce Tamiyo’s active strategic envelope;
- calculate adjudicated utility, risk and uncertainty charges;
- compare surviving candidates against mandatory no-op;
- apply independent admission-audit rules;
- return `ADMIT`, `NO_OP`, `REJECT`, `DEFER` or `REQUIRE_RETEST`;
- issue admission warrants;
- adjudicate continued tenancy of committed structures;
- issue maintenance warrants;
- calibrate thresholds on validation trajectories only;
- and emit explicit decision reasons and policy versions.

#### Lexicographic admission order (ADR-0004)

Admission is a risk judgement before it is a quality judgement. Augustin
adjudicates in three ordered stages, and no later stage can reopen an
earlier one:

1. **Hard eligibility.** Conformance facts from the blinded
   `QualityReport`: identity, compilation, runtime and gradient checks,
   determinism, evidence completeness for the assurance class, budget.
2. **Tail-risk veto.** Augustin estimates, per candidate, the tail of the
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

This order is what justifies the Momir/Augustin split: **Momir optimises
expected value** and can afford to be wrong often, because its errors cost
compute; **Augustin bounds worst case** and must be conservative, because
its errors cost the host. They optimise different functionals of the same
distribution.

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
- \(U_c\) is uncertainty.

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

#### Retention hysteresis (ADR-0005)

Admission and retention thresholds form a Schmitt trigger: admission requires the conservative margin over no-op to exceed \(\theta_{\mathrm{admit}}\); continued tenancy requires only \(u_{\mathrm{retain}} \ge \theta_{\mathrm{retain}}\), with \(\theta_{\mathrm{retain}} = \theta_{\mathrm{admit}} - \Delta\) and \(\Delta > 0\) strictly (INV-33). A resident growth that drifts modestly below the admission bar is not thereby lysed.

The hysteresis band \(\Delta\) is an explicit, versioned Augustin policy parameter, carried by `adjudication_policy_version`, and its width is measured against observed execution noise \(\sigma_{\mathrm{exec}}\) — sized so noise-driven estimate movement cannot cross both thresholds — never picked by feel. Cooldowns are a frequency limiter for pathological cases, not the stability mechanism: they are a time-domain patch and do not remove a threshold-domain instability.

#### Invariants

- Augustin does not execute tests, alter data, call kernels or rerun a branch.
- It cannot see candidate source during adjudication.
- It can select no-op even when Tamiyo allocated budget and Narset commissioned growth.
- Hard Urabrask defects make a candidate ineligible according to the applicable Leyline policy.
- The tail-risk veto is adjudicated before any utility comparison and cannot be traded against measured benefit (INV-45).
- Every veto, and every thin-margin pass, is recorded per candidate in `tail_veto_results` (INV-31).
- Decision thresholds are frozen before confirmatory runs.
- Every warrant is bound to a specific evidence digest, semantic hash, envelope and policy version.

#### Smell

> If Augustin asks for a more favourable minibatch after seeing the evidence, the judge has tampered with the case.

> If a candidate's measured benefit is cited as a reason to soften the veto, the judge has repriced catastrophe.
