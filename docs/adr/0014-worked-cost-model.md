# ADR-0014 — Adopt the worked compute cost model (HER accounting, K/N fixed, restructure trigger armed)
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-09 · Status: accepted · **amended by ADR-0016 (2026-08-11)**
Deciders: John (owner: D1 negative-result scope and D2 endpoint family
decided in session; remainder delegated to the cost model per metrics.md) ·
Tracker: simic-642c2c1823

Amends: —
Amended-by: ADR-0016
Supersedes: —
Superseded-by: —

Notes:
- 2026-08-11 (ADR-0016): D1, D2 and K = 1.5 / n = 32 cease to gate; the
  apparatus is mothballed as a costed option. Arithmetic unchanged.
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

The peer review (docs/concept/reviews/2026-08-08-esper-pivot-peer-review.md
§§2, 8) found that a design which makes budgets contractual at every
boundary (INV-23) carried no number anywhere for what fraction of total
training compute the growth machinery consumes. Two drivers compound: the
base host trajectory is the independent statistical unit (INV-32), so power
for the headline claim scales with independently seeded full host runs, not
branches; and the scaffold interaction matrix has eight cells. Eight cells
× usable n × Academy-exact rollouts *is* the programme budget, and it was
parked in an open decision. Three newer decisions had meanwhile become
consumers of the missing numbers: the §28.2 success criterion's K and N
(delegated to this model by the product scoreboard), the anchor-corpus
pricing (ADR-0011), and the exactness-tax measurement (ADR-0013).

## Decision

Adopt the worked cost model as a design chapter,
`programme/cost-model.md`, produced under the counterfactual-statistics
discipline and integrated as follows.

1. **Unit of account.** The **host-equivalent run (HER)** — one complete
   ordinary MVP host training run with no growth machinery, on the declared
   execution-stack identity (INV-05, ADR-0013) — is the common denominator
   for every economy metric in `programme/evaluation.md#2211-economy`.
2. **Every number is a declared placeholder with a named retirement
   path.** The model's product is the iso-surface — the affordability
   boundary — not the point estimates. The companion pre-registration
   (`programme/prereg-cost-model-campaign-1.md`) commits the measurement
   campaign that retires the placeholders, before any measurement runs.
3. **K and N for the §28.2 criterion are fixed:** **K = 1.5, N = 256
   adjudicated pools — which is 32 base trajectories × 8 pools**, always
   stated in that order (n = 32, per INV-32). K = 1.5 is the knee of the
   derived power table: a floor of 2.0 more than doubles the fleet for one
   notch of claim strength; a floor of 1.0 is not "materially higher".
4. **Endpoint family (owner decision, D2).** §28 criterion 2's *rate*
   clause (Momir pools beat the random-search arm) is the **single primary
   confirmatory endpoint**; the *online-cost* clause (versus bounded
   iterative construction) is **descriptive** — reported with a bootstrap
   CI across units, no α spent, n unchanged at 32. The previously implicit
   position — two clauses, one power calculation, no declared family — is
   statistically illegitimate and is closed by this decision.
5. **Negative-result scope (owner decision, D1).** §28's promised negative
   result is kept affordable by **pre-registering the inferiority margin
   the budget buys**: at n = 32 the fleet can conclude "Momir is not
   ≥ 1.5× random search" with 80% power. §28's clause stays literally true
   at that stated, weakened strength. The symmetric refutation
   (n = 185 trajectories, ~6× the confirmatory fleet) was priced and
   explicitly declined; declaring the negative result merely exploratory
   was declined because `01-claim.md` §2.6 (attribution honesty) leans on
   the clause.
6. **Restructure trigger armed.** The QA-restructure threshold is
   **40 HER per admitted growth**, evaluated as (P+1)·h·τ·r/a. The lever is
   named in advance: the tiered Field QA cascade
   (`07-counterfactual-engine.md`, §14.4) — push the modal candidate to
   tiers 1–2, reserve full paired branches for tier-3 survivors — which
   cuts effective pool size in the expensive tier while preserving pool
   composition, complete negative retention (INV-31), and the permanent
   harmful/long-term-regressing fixtures the tail veto needs (ADR-0010,
   INV-45). Pulling the lever is a Phase-E-or-earlier decision, never a
   Phase-K optimisation.
7. **Scaffold-cell allocation (closes §27.15 as amended).** Two corner
   cells (fully scaffolded, fully withdrawn) at n = 32; the six
   intermediate cells at n = 16 with their MDE declared (2.19× the
   random-arm rate — an interpretability instrument, not a confirmatory
   claim). §27.15's text is amended to reference the model rather than
   struck.
8. **Anchor-corpus pricing corrected (amends ADR-0011's cost reading).**
   Branches are tails, not full runs (mean ≈ 0.5 HER), and the no-op arm
   is the base seed's own spine, already paid: C = seeds × (1 + D_samp ×
   A × 0.5). A 24-seed / 4-decision / 3-action corpus is **168 HER**, not
   312. ADR-0011's phrase "every branch runs to end-of-run" describes
   trajectory completeness, not incremental compute. (The no-op arm
   remains a real, separately paid branch in the QA pool stack —
   INV-15/INV-16; the two cases must not be blurred.)
9. **Observation-cadence floor recommended.** `ablated_context` costs an
   extra forward pass per observation (~⅓ of a training step): per-step
   cadence is +33% of all host training, permanently, on mainline and
   every branch. The model recommends a declared floor of φ ≥ 25 steps in
   the `TelemetryEnvelope` profile, with per-step ablation an explicitly
   budgeted diagnostic regime. Economy, not correctness — INV-34 is
   unaffected.
10. **Chapter split authorized.** Integrating the model body into
    `programme/evaluation.md` would breach the ~600-line chapter budget;
    per the index's size discipline the model lands as its own chapter,
    `programme/cost-model.md`, with `evaluation.md` §22.11 and
    `risks-and-open-decisions.md` §27.15 pointing at it.

## Consequences

- The programme budget is **order 10³ HER** (≈ 960 Academy CPU-lab at
  placeholders; ≈ 2 300 in `CALIBRATED_STOCHASTIC` at r = 5) — robust at
  order-of-magnitude, not at two significant figures. Per admitted growth:
  1.0–5.2 HER at placeholders, with the 40-HER threshold **live** (crossed
  at h > 0.154 for P = 12, r = 5 — and the breaching combination is the one
  the design otherwise steers toward, since a healthy abstaining judge
  lowers the admission rate and raises cost per admit; cost per
  *adjudicated pool* is therefore reported alongside cost per admitted
  growth).
- The model is **provisional by construction until §27.5 closes**: the QA
  horizon h is its most leveraged parameter and is owned by that open
  decision. The single highest-value measurement in the programme is the
  multi-horizon pilot (campaign 1, M1) that closes both.
- The amortisation bar is the **full un-amortised bespoke cost**: the
  predecessor's library reuse factor is measured at R ≳ 10² (13-entry
  catalogue, thousands of germinations per run), so Esper's amortised
  per-use validation cost is ≈ 0. The bar softens exactly as the Urborg
  retrieval hit rate ν rises, making ν an economic endpoint, not merely a
  quality metric — a high ν means Simic converges toward Esper and Esper
  was right; a low ν with positive ΔU_reference is the strongest available
  result for the pivot.
- Confirmatory sizing discipline is pre-committed: when the pilot returns
  a measured sd_d, the fleet is sized at its 80% upper confidence limit,
  never the point estimate, and the effect floor comes from this model,
  never from the pilot's observed effect.

## Reversal trigger

Re-open this ADR if: campaign 1's M1 places the QA-horizon optimum at
h ≥ 0.10 (the per-admit numbers rise fivefold and the tiered-cascade lever
must be evaluated immediately); or the measured ρ exceeds 0.45 (n = 32 is
then underpowered by ≥ 30% and K/N must be re-derived before any
confirmatory unit runs); or §27.5 closes in a way that contradicts the
nested-horizon assumption (pools would pay Σ H, not max H, and the entire
(c) stack re-prices).
