# ADR-0011 — The anchor corpus: per-decision counterfactual fan-out on a declared seed set (INV-39 amended)

Date: 2026-08-09 · Status: accepted
Deciders: John (owner-proposed and confirmed, session 11; adversarial
challenge requested and resolved — see tracker comments) ·
Tracker: simic-954f457e50

## Context

The tenancy-evidence closure (simic-e2ae14c8bd) left maintenance decisions
on an explicitly weaker evidentiary standard: the honest counterfactual for
a committed growth — the host that never received it — costs a parallel
no-op branch for the entire tenure, so production tenancy evidence measures
replaceability at horizon \(H\) instead. Separately, Aurelia's timing
policy is the one place the peer review said the counterfactual
cancellation does not reach, and its supervision (§17.2) needs dense causal
labels that an immature policy cannot generate without biasing its own
curriculum. The owner proposed paying the full counterfactual cost on a
small declared host set as training wheels, then generalised it: fork at
decision points, fork per candidate action class, and generate the corpus
without any working policy at all.

## Decision

Adopt the **anchor corpus** as the fourth primary scaffold (Appendix F).

On a **declared anchor host set** (order tens of seeds), a **declared
schedule of decision points** — random or fixed, chosen without a working
Aurelia — each forks a fan-out of full parallel trajectories under the
common-future discipline: the no-op, and a declared **action set** of
reference-seed intervention classes. Every branch runs to end-of-run. All
branches of one seed remain one statistical unit (INV-32).

**Label routing is authority-partitioned** (this resolves the one
constitutional hazard found in review). The fan-out is authority-agnostic
Tolaria mechanics; each authority consumes the corpus through a blinded
view containing only the fields it may act on — the INV-37 pattern applied
to training data. A general rule follows: *any decision an authority is
entitled to make can be anchored — fork at the decision point, run each
entitled alternative to the end, and the branch differences are supervision
for that authority; no authority is ever trained on a signal it cannot
legally express.* Concretely:

- **Aurelia** receives the marginalised slice only: best-over-action-set
  versus no-op — the value of commissioning here-and-now, class-blind
  (INV-09 is preserved at training time, not merely at schema time; seam:
  simic-d176c4ebcd owns the full §17.2 label specification).
- **Per-action detail** goes to telemetry-sufficiency validation (the
  Stage 1B instrument, densified), the Urborg bootstrap precedent and
  Momir conditioning corpus, and Ugin-level class-outcome statistics.
- **The admission fork run to end of tenure** is admission-grade tenancy
  ground truth: Isperia's re-adaptation instrument — including the choice
  of \(H\) — is calibrated against it, converting the weaker tenancy
  standard from assumed to measured.

Honest-evidence caveats are part of the design, not commentary: calibration
claims count **seeds, not branches** (INV-32 — the gate wording is "gross
divergence excluded, error bar measured and carried into \(\omega U_c\)",
never "instrument certified"); labels are **path-conditional** (a decision's
counterfactual is measured given the decisions before it; decision
interactions are unmeasured); tenancy calibration holds on
**bootstrap-scale tenures** and long-horizon validity remains charged as
evidence uncertainty.

### The F.6 declaration

- **Failure mode protected against:** unvalidated tenancy evidence and
  unlabelled commissioning decisions (timing supervision manufactured
  nowhere else; replaceability-at-\(H\) trusted without ground truth).
- **Learn-the-Land regime:** `FULL_DECISION_FANOUT` on the declared anchor
  host set, decision points scheduled or random (policy-independent by
  construction).
- **Controlled relaxation path:** `ADMISSION_ANCHORED` (only the admission
  fork kept for tenure) on sampled subsets, then `UNANCHORED`.
- **Withdrawal gate:** the production instruments are decision-calibrated
  against anchored ground truth within declared limits at seed-level
  counting — gross divergence excluded, error bars measured and carried.
- **Gate owner:** Jin-Gitaxias certifies the calibration evidence; Isperia
  authorises unanchored maintenance evidence per assurance class.
- **Retained reference role:** audit hosts, disputed-tenancy escalation,
  periodic anchor refresh (INV-42).
- **Correlated scaffolds:** execution regime (anchor branches inherit the
  active Tolaria profile) and host distribution (anchor seeds are
  repeated-acquisition hosts); interaction cells declared per INV-41.
- **Ambiguous-case escalation:** disputed or high-stakes tenancy calls
  escalate to an anchored re-measurement on the retained audit hosts.

## Displaced constraints

INV-39 amended.

- Old: "**Declared scaffold state:** every curriculum, QA and confirmatory
  run records its execution, host-distribution and design-prior regimes."
- New: "**Declared scaffold state:** every curriculum, QA and confirmatory
  run records its execution, host-distribution, design-prior and
  counterfactual-anchor regimes. (ADR-0011)"

`ScaffoldState` gains `counterfactual_anchor_regime: FULL_DECISION_FANOUT |
ADMISSION_ANCHORED | UNANCHORED` (plainweave store unseeded — no locked
definition displaced; the shape locks at seeding, simic-357c92664c).
INV-32, INV-37, INV-09, INV-40/41/42 are load-bearing context, unchanged.

## Options considered

- **No anchor corpus (status quo).** Rejected: tenancy calibration would
  have no ground truth ever, and Aurelia's dense labels would be generated
  on-policy by an immature policy — the off-policy bias the reset's whole
  measurement discipline exists to avoid.
- **Anchor only tenancy (original narrow proposal).** Rejected as scope:
  the same forks, run from decision points rather than admissions only,
  serve three consumers for one corpus cost; the owner explicitly
  generalised the proposal.
- **Per-action labels to Aurelia (the naive wiring).** Rejected: teaches
  Aurelia topology preferences it cannot legally express (INV-09) —
  covert-channel pressure on the assignment brief. Resolved by
  authority-partitioned routing above.
- **Every-decision × every-action fan-out.** Rejected: combinatorial
  (decisions × actions full runs per seed); the corpus uses declared,
  sampled decision-point and action-set budgets.

## Consequences

Appendix F gains the fourth primary scaffold row and gate-owner entries;
the constitution's INV-39 and the `ScaffoldState` contract carry the
fourth axis; the curriculum and every "three-axis" citation update to
four; Isperia's tenancy section, §2.4, and §17.2 point at the corpus. The
§22.11 cost model (simic-642c2c1823, comment 20) must price the corpus —
seeds × (1 + sampled decisions × actions) full-length runs at roughly
Phase B–D machinery; the owner pre-accepted this cost for a few-dozen-seed
corpus. Corpus trajectories are ordinary Urborg history (INV-31/36).

Reversal trigger: if the measured corpus cost (§22.11) exceeds what the
declared seed budget can absorb, shrink the action set and decision
sampling before shrinking seeds (n is seeds); if calibration on the corpus
cannot exclude gross divergence, the production instruments do not loosen —
the scaffold stays TIGHT and the pacing plan re-opens by PDR, never by
silently trusting the uncalibrated instrument.
