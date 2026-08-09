# ADR-0005 — Admission/retention hysteresis: admit strictly above retain (Schmitt trigger)

Date: 2026-08-08 · Status: accepted
Deciders: John (gate adjudication PDR-0007; peer review §2 accepted into the

> **Namespec note (ADR-0008):** this record predates Namespec 2.0 and uses
> Namespec 1.0 names; read it through the concordance in
> [`0008-namespec-2.0.md`](0008-namespec-2.0.md).
wave programme) · Tracker: simic-ed2698fafd

## Context

To prevent install–lyse oscillation, INV-33 pushed toward **shared cost
weights** between admission and retention, and the retention utility
(`../design/domains/augustin.md#continued-tenancy-utility`) differs from
admission only by dropping integration shock. The risk register lists the
oscillation with mitigation "shared cost weights, churn metrics, cooldowns
and pre-registration"
(`../design/programme/risks-and-open-decisions.md`).

That shape is backwards. Shared weights with **no threshold band** mean a
growth sitting near the boundary is admitted and lysed repeatedly as
execution noise moves the estimate — precisely the oscillation the
invariant is trying to prevent. And cooldowns are a **time-domain patch for
a threshold-domain problem**: they suppress the frequency of the
oscillation without removing the instability. (Peer review:
`../concept/reviews/2026-08-08-esper-pivot-peer-review.md` §2.)

## Decision

**Admission and retention thresholds are deliberately asymmetric: the admit
threshold sits strictly above the retain threshold — a Schmitt trigger.**

- Admission (per
  `../design/07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins`)
  requires the conservative margin over no-op to exceed the admission
  threshold \(\theta_{\mathrm{admit}}\).
- Continued tenancy requires only
  \(u_{\mathrm{retain}} \ge \theta_{\mathrm{retain}}\), with
  \(\theta_{\mathrm{retain}} = \theta_{\mathrm{admit}} - \Delta\) and
  \(\Delta > 0\) strictly. A resident growth that drifts modestly below the
  admission bar is not thereby lysed.
- The hysteresis band \(\Delta\) is an **explicit, versioned Augustin
  policy parameter**, carried by `adjudication_policy_version` on both
  `AdmissionDecision` and `MaintenanceDecision`. Its width is **measured
  against observed execution noise** \(\sigma_{\mathrm{exec}}\) from the
  calibration machinery — sized so that noise-driven estimate movement
  cannot cross both thresholds — never picked by feel.
- **Shared weights survive where they are right:** cost *semantics* stay
  shared — \(\lambda, \nu, \xi, \omega\) mean the same thing on both sides
  unless a structural difference is documented (the true content of
  INV-33). The asymmetry lives in the **thresholds**, where it is explicit,
  versioned and measurable — not smuggled into per-side weight differences.
- **Cooldowns are demoted** to a frequency limiter for pathological cases;
  they are not the stability mechanism. Grace-period protection (INV-30)
  is untouched — it protects newborns during declared blend/holding
  windows, a different job.

Interaction with ADR-0004: the hysteresis band governs the **utility**
stage of adjudication. The tail-risk veto (INV-45) is orthogonal and
remains non-tradeable on both sides of the lifecycle; a resident growth
inside the hysteresis band is retained on utility grounds, not exempted
from safety action.

## Displaced constraints

- **INV-33 amended.** Old: *"Selection–retention consistency: shared cost
  terms use shared weights unless a structural difference is documented."*
  New: *"Selection–retention consistency: shared cost terms use shared
  weights unless a structural difference is documented; admission and
  retention thresholds are deliberately asymmetric — the admit threshold
  sits strictly above the retain threshold by a versioned hysteresis band
  sized against measured execution noise."*
- Retention-utility prose in `../design/domains/augustin.md` amended to
  state the threshold relationship.
- Risk-register mitigation for install–lyse oscillation amended
  (`../design/programme/risks-and-open-decisions.md`): threshold hysteresis
  is primary; cooldowns are a frequency limiter only.
- INV-30 (grace-period protection) and INV-45 (lexicographic admission)
  reaffirmed unamended.

## Options considered

- **Status quo: shared thresholds plus cooldowns** — rejected: cooldowns
  reduce how often the boundary growth churns, not whether it churns; the
  instability survives and surfaces as slow install–lyse cycling that
  wastes warrants, QA spend and Sarpadia history on noise.
- **Asymmetric cost weights** (make retention structurally cheaper by
  re-weighting per side) — rejected: it hides the asymmetry inside weight
  differences where it cannot be measured or audited, breaks shared cost
  semantics, and invites exactly the per-side weight drift INV-33 exists
  to prevent.
- **Hysteresis band set by feel** — rejected: an unmeasured band is either
  too narrow (churn persists) or too wide (zombie tenancy); the band is
  only defensible sized against observed \(\sigma_{\mathrm{exec}}\), which
  the calibration machinery already measures.

## Consequences

- The churn metric becomes falsifiable: under a correctly sized band,
  noise-driven install–lyse cycles should approach zero; observed cycling
  indicates the band is narrower than realised \(\sigma_{\mathrm{exec}}\).
- New failure mode to watch: **zombie tenancy** — a band wider than
  necessary shelters marginal residents. Bounded by sizing against
  measured noise and by Emrakul's replacement-pressure detection; the
  band's width is auditable per policy version.
- \(\sigma_{\mathrm{exec}}\) becomes load-bearing for retention policy,
  strengthening the case for the calibration machinery it already feeds
  (Field calibration, INV-43).
- Files updated by this ADR: `../design/domains/augustin.md`,
  `../design/02-constitution.md` (INV-33),
  `../design/programme/risks-and-open-decisions.md`.
- **Reversal trigger:** if measured \(\sigma_{\mathrm{exec}}\) proves
  non-stationary enough that no static band avoids both churn and zombie
  tenancy across a run, the band becomes adaptive (tracked against rolling
  calibration) by a superseding ADR. The strict inequality
  \(\theta_{\mathrm{admit}} > \theta_{\mathrm{retain}}\) survives any such
  revision.
