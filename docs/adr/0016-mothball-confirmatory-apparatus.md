# ADR-0016 — Mothball the confirmatory apparatus: K/N and the eight-cell fleet become a costed option, not a gate
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-11 · Status: accepted
Deciders: John (owner sign-off 2026-08-11, "PDR-0039 is endorsed") ·
Tracker: — (arises from `docs/concept/reviews/2026-08-11-morphogenesis-concept-panel.md`)

Amends: ADR-0014
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

PDR-0039 positions Simic as an engineering programme rather than a confirmatory
research study, on the owner's ratification. ADR-0014 is the record that made
the confirmatory claim gating: it fixed $K_{\text{floor}} = 1.5$ and $n = 32$
base trajectories × 8 pools, declared the rate clause the single primary
endpoint (D2), pre-registered the negative margin (D1), and adopted the
two-corners-at-32 / six-interactions-at-16 allocation. Those constants were
consumed by `01-claim.md#28-success-criteria` criterion 2 and by
`docs/product/metrics.md`'s north-star.

Three verified defects in that apparatus (concept panel, 2026-08-11) also bear
on this, though they are corroborating rather than causal — the reason for the
change is the positioning decision, not the defects:

- The single primary endpoint has **no defined success predicate**.
  `05-leyline-contracts.md#914-qualityreport` states outright that
  `QualityReport` "does not contain `ADMIT` or `REJECT`", and it carries no
  threshold, horizon selector or decision rule. $p_R$ is therefore the rate of
  an undefined event, and $K$, $n$ and the power claim are arithmetic on it.
- `cost-model.md#h-k-and-n-for-the-headline-criterion` derives per-$K$ values of
  $sd_d$ (0.241 / 0.292 / 0.323) and then applies the constant **0.292** to
  every row of the operating-characteristics table. Correcting it moves
  $P(\text{abandon} \mid K_{\text{true}} = 1.0)$ from 0.153 to **0.458**. The
  error runs in the design's favour; 80% power for the declared negative needs
  $n \approx 73$, not 32.
- `TestPlan` declares no control-arm size. With
  $P(\text{arm hit}) = 1 - (1-q)^K$, a three-candidate Momir arm against a
  one-candidate random arm yields $K = 2.71$ from a generator exactly as good
  as random search.

## Decision

**The confirmatory apparatus is mothballed with its costings intact.** It is a
study the owner may commission, not a gate the programme must pass.

1. **ADR-0014 D1 and D2 cease to gate.** The pre-registered negative margin and
   the single-primary-endpoint declaration are suspended. They are not
   withdrawn: if the apparatus is re-commissioned they resume as written, with
   the corrections in (4) applied first.
2. **$K = 1.5$ / $n = 32$ stops being the north-star.** Criterion 2 becomes one
   member of the *optional study* class under
   `01-claim.md#28-success-criteria` §28.1.
3. **The eight-cell allocation** (two corners at $n = 32$, six interactions at
   $n = 16$) becomes an optional study. Success criteria 15 and 16 split
   accordingly: 15 (independent withdrawal without losing declared invariants)
   stays an acceptance gate; 16 (interpreting the fully withdrawn corner
   against interaction controls) becomes optional.
4. **Three repairs are prerequisites of re-commissioning, not of continuing.**
   Any future confirmatory campaign must first: define the hit predicate once,
   weight-free, and make the four documents cite rather than restate it;
   recompute the operating-characteristics table with per-$K$ $sd_d$ and name
   D1's alternative; and declare per-arm candidate counts with arm-size
   matching, re-deriving the between-pool variance component that forced class
   rotation introduces.
5. **`programme/cost-model.md` is unchanged and remains a design chapter.** Its
   arithmetic is the price list for the mothballed option and for every
   engineering-class measurement that survives. Nothing in it is deleted.

## Displaced constraints

**None constitutional.** No INV-nn is amended, displaced or weakened. This is
deliberate and is the load-bearing property of the decision: the invariants that
protect the programme from self-deception are scar-derived, not
publication-derived (`01-claim.md#26-the-empirical-driver`), and every one of
them stands unchanged — INV-05, INV-06, INV-07, INV-09, INV-15, INV-16, INV-24,
INV-31, INV-32, INV-37, INV-38.

INV-15/INV-16 (mandatory no-op at policy utility exactly zero) is the one most
likely to be argued as "confirmatory statistics" by a later reader. It is not.
The mandatory no-op is the instrument itself, and it is now directly load-bearing
for `01-claim.md#28-success-criteria` criterion 18.

## Options considered

- **Delete the apparatus outright.** Lost: the sizing work is the price list. A
  future re-commissioning would have to redo it, and the mothballed form costs
  nothing to keep.
- **Keep it gating and fix the three defects.** Lost: it does not address the
  positioning. It also buys an instrument whose modal outcome is INCONCLUSIVE
  at 0.845/0.846 for the two most likely truths, at $n \approx 73$ rather than
  32 for the negative — roughly double the fleet for a claim the owner has said
  was never career-bearing.
- **Reduce $n$ and keep the claim.** Lost: an underpowered confirmatory claim is
  worse than no confirmatory claim, and would be the exact over-read failure the
  predecessor record documents.

## Consequences

- The programme's gating evidence becomes the acceptance class of
  `01-claim.md#28-success-criteria`, headed by criterion 18 — that the paired
  branch difference resolves an intervention effect above branch-divergence
  noise. That is answerable at Phase D, before Momir exists.
- `docs/product/metrics.md`'s north-star row still reads $K = 1.5$ / $n = 32$
  and must change. It cannot be edited from a `main`-based branch without
  reverting the PDR-0035/0038 grant widening; sequencing is PR #13 first
  (PDR-0039, "Downstream").
- `programme/prereg-cost-model-campaign-1.md` keeps its measurement instruments.
  Those that retire engineering-class placeholders (the exactness tax $\tau$,
  the QA horizon $h$, Elesh/Urabrask rejection rates) remain live and become
  *more* important, since they now serve acceptance rather than a fleet.
  Those that exist only to size the confirmatory fleet ($p_R$, $\rho$) are
  mothballed with it.
- A reviewer who sees ADR-0014 without this record will believe the programme
  is making a confirmatory claim. ADR-0014's header must point here.

## Reversal trigger

If `01-claim.md#28-success-criteria` criterion 18 passes, **and** a headroom
measurement reports non-zero off-menu headroom over the reference population,
**and** the owner wants a venue claim, the apparatus returns to DECIDE with the
(4) repairs as entry conditions. It was mothballed rather than deleted
specifically so that this is a re-commissioning and not a redesign.
