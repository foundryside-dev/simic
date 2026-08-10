# Concept panel: counterfactual generative morphogenesis

**Date:** 2026-08-11 · **Corpus reviewed:** `docs/design/`, `docs/adr/`, `docs/product/` at `50501e1`

**Composition and method.** Eleven critique lenses (statistics, reward, morphogenesis,
governor, synthesis, contracts, determinism, architecture, systems, product,
claim-skeptic), each finding put through adversarial verification with citation
checking and a best-counterargument pass; five forward-design angles producing
fifteen proposals; three judges scoring proposals on evidential strength,
feasibility for one person on spare time, and strategic optionality; one
completeness critic auditing what the eleven lenses missed.

**Counts, honestly.** 43 critique findings survived verification, plus 3
completeness-critic gap findings. 3 were killed at verification (2 refuted on the
corpus's own text, 1 as already-tracked under simic-b75a7c2742). At least six more
were self-killed by panelists before verification and named as such in their lens
summaries — the systems lens dropped two leads, morphogenesis dropped its
multi-growth question, contracts dropped a resolver-semantics finding, claim-skeptic
rated and dropped two reframings. **These counts do not sum to a denominator** — the
raised total is not recoverable from the material, so no hit-rate is quoted.

The ratio that *is* recoverable is the informative one: **2 findings survived
CONFIRMED; 41 were narrowed.** Read that carefully, because it is the panel's
single largest signal and it is easy to misread in both directions. It does not
mean the panel found nothing. It means the verifier repeatedly found that the
corpus already contained the mechanism a panelist claimed was missing — but
contained it *unstated*, *mis-cited*, or *declared in one chapter and contradicted
in another*. The structural architecture held up under eleven adversarial lenses.
The declaration layer did not.

That distinction is not documentation hygiene. For a corpus whose evidentiary
standing rests on pre-registration, an unstated rule has no force — the verifier on
S1 put it exactly: *"in a pre-registration, an unstated rule is post-hoc
discretion."* Nine of the findings below are of the form "the corpus clearly
intends X and nowhere says X," and in a confirmatory programme that is a defect
with the same consequence as not intending it.

---

## Verdict in one page

**1. The single primary confirmatory endpoint has no defined success predicate, and
every sizing number in the programme is arithmetic on it.** (S6, CONFIRMED,
CRITICAL.) `01-claim.md#28-success-criteria` says "useful canonical growth";
`programme/evaluation.md` says "positive-evidence growth";
`cost-model.md#h-k-and-n-for-the-headline-criterion` and
`prereg-cost-model-campaign-1.md` M2 say "positive certified evidence per
`QualityReport`"; `docs/product/metrics.md` says "admission-worthy canonical
growth." No document defines any of them.

The packet contained a contradiction here — S15's verifier held that M2's
"per `QualityReport`" already pins the endpoint pre-veto and reduces S6 to a
copy-edit. It does not, and the check is mechanical. `QualityReport.candidate_reports[]`
(`05-leyline-contracts.md#914-qualityreport`) carries validity booleans
(`structural_reference_valid`, `runtime_valid`, `finite_outputs_and_gradients`), raw
measurements (`measured_task_trajectories`, `measured_costs`, `measured_shock`,
`uncertainty`) and test status (`hard_defects[]`, `escalation_required`) — and no
threshold, no horizon selector, and no decision rule. The chapter states outright
that it "establishes facts and test status. It does not contain `ADMIT` or
`REJECT`." Computing a boolean "positive" from that record requires choosing which
measurement (`evaluation.md` lists six trajectory quantities), at which horizon
(`risks-and-open-decisions.md#275-qa-horizon-and-evidence-floor`, open), under which
decision rule — all three policy, and
`risks-and-open-decisions.md#276-jin-gitaxias-isperia-contract` explicitly leaves
"which measurements are raw, which are certified derived facts" open. The phrase
names a rule that does not exist at that layer. S6 stands; S15 survives only as the
smaller, separate defect that `metrics.md`'s north-star row carries a stale
post-veto gloss.

Consequence: p_R is the rate of an undefined event, and K = 1.5, n = 32, the 80%
power claim and ADR-0014 D1's negative margin are all functions of it. If M2 and the
confirmatory fleet run under different predicates, K/N are invalid and the fleet is
re-run. Fixable in a page, before campaign 1, and it is the cheapest high-value edit
in this report.

**2. The programme's declared fallback outcome — the clean negative that makes a
spare-time moonshot rational — is not deliverable at n = 32, and the modal outcome
has no pre-committed response.** (S2, CONFIRMED, HIGH; with S36.) ADR-0014 D1 and
`cost-model.md#h-k-and-n-for-the-headline-criterion` state that the fleet concludes
"Momir is not ≥ 1.5× random search" with 80% power, without naming the alternative K
at which that holds. At K_true = 1.0 — Momir equals random search, the alternative
any reader assumes — the corpus's own operating-characteristics table gives 0.153,
and the correctly-computed value (using the per-K sd_d derived three paragraphs
above, rather than the constant 0.292 the table actually uses) is 0.458. 80% power
requires K_true ≈ 0.7, i.e. the alternative "Momir is 30% *worse* than random
search," or n ≈ 58–73. Note the sub-error runs in the design's favour: the negative
prospects are three times better than the corpus documents, and still not 80%.

Compounding it: the same table puts INCONCLUSIVE at 0.845 and 0.846 for K_true = 1.0
and 2.0 — both of the two most likely truths — and no artifact anywhere records what
the owner does when the CI straddles K_floor. The word "inconclusive" appears exactly
once in `docs/`, in that table. Every reversal trigger across all 38 PDRs resolves to
re-plan, re-date, re-scope, demote, restructure or escalate; not one fires on evidence
about the claim.

**3. The headline result is manufacturable from an undeclared parameter.** (P4
sub-change 1.) With equal per-candidate quality, P(arm hit) = 1 − (1 − q)^K. At the
declared q = 0.10, a three-candidate Momir arm against a one-candidate random arm
yields K = 2.71 from a generator that is exactly as good as random search. No artifact
declares the counts: `ProposalBatchRequest.candidate_count` declares Momir's arm,
`TestPlan.control_artifacts[]` declares no control-arm size, and
`cost-model.md#a-declared-parameters` sets P = 12 against a 13-class pool list. A
measured K > 1.5 therefore has an alternative explanation the corpus cannot rule out
from its own records — which makes the headline unattributable *whichever way it
lands*. One contract line fixes it. Arm-size matching does force per-pool class
rotation, which introduces a between-pool variance component that must be re-derived
before n locks; that is a real design cost and the only one in this item.

**4. Nothing measures the pivot's own denominator before the money is spent.**
`cost-model.md#d-the-amortisation-bar` states that ΔU_reference "is the quantity the
bar is denominated in" and that this "is why it is load-bearing rather than one metric
among thirteen." It has no row in the declared-parameter table, no placeholder, no
retirement path, and appears in `programme/evaluation.md` as one unadorned bullet with
no floor, no power calculation and no n. All three judges converged on the same
response: measure the *prize* — the headroom a search oracle over the L1 envelope finds
above the best menu entry — on the kernel-demo substrate, for approximately zero HER,
before Phase A finishes (P1; top pick for two judges, 9/9/10). The increment over the
tracked simic-b75a7c2742 is worth stating precisely: ADR-0014 D2 has already spent the
α on the rate clause, so promoting ΔU_reference now costs a fleet re-sizing, not a
criterion re-wording.

**5. The corpus's own novelty claim will not survive review, and the defensible
contribution is the instrument, not the generator.** (S40, S42, P10.)
`01-claim.md#26-the-empirical-driver` names "generated (not selected) structure" as
one of three irreducible contributions. Generating structure from a training
network's live state is a dense published line — Net2Net and network morphism,
GradMax (ICLR 2022), Firefly (NeurIPS 2020), Self-Expanding Neural Networks, AdaLoRA
(ICLR 2023) for the L1 form specifically, Gstack (NeurIPS 2024) at scale. What the
panel could not find published is the *counterfactual adjudication*: every growth
criterion in that literature is a cheap one-step surrogate validated
end-of-pipeline, never against the causal effect of the insertion measured in a
matched no-growth continuation. The corpus cites zero external work anywhere.
Caveat the panel flagged against itself: the negative half of that search was six
queries, so it is absence of evidence, and the transposition sits inside an
established genre (NAS zero-cost-proxy calibration) rather than in empty territory.

---

## Part 1 — Theory critique

### 1.1 What threatens the counterfactual-supervision claim

The premise is that paired branches cancel ordinary-training variance, so the
between-branch difference *is* the intervention effect. Four findings put unpriced or
uncancelled terms inside that difference, and one asks whether it is resolvable at all.

**G2 — no contract declares the growth's optimiser, and cross-arm identity stops at
data and RNG.** The host side is pinned exhaustively: `TrainingRunSpec` declares
`host_optimizer_definition`, `scheduler_definition`, `dtype_and_precision_policy`,
`determinism_policy`; `Snapshot` carries `host_optimizer_state`. The growth side has
`maturity_mode` and `maturity_budget` — a mode and a spend cap. In nursery mode, which
`06-growth-model.md#112-one-shot-and-nursery-modes` declares the default ecological
configuration, the embodied function depends on a learning rate, schedule and weight
decay that no record in the corpus declares and no reviewer could recover. Separately,
INV-06 requires paired branches to share "identical future minibatches and equivalent
random streams," and INV-04's chapter list of same-ness conditions is
mainline-versus-branch. Neither reaches the class of quantity computed once per step
across *all* parameters of one model — global gradient-norm clipping being the
standard member. Whether the norm is taken over host ∪ growth or host alone has no
answer anywhere, and the two produce different host-parameter updates in the candidate
arm only.

Concede the strongest counter, which is the one that beat S19: the intervention is the
artefact as executed, so a global-scalar shift caused by the growth is arguably part of
the effect rather than error in measuring it. Accept that at the level. What survives is
*ranking* — the induced perturbation scales with the growth's gradient magnitude, which
correlates with its capacity, and capacity is already priced separately as λC_c in
`domains/isperia.md#admission-utility`. Inside a single pool the same property is either
double-charged or mis-attributed, in the comparison Isperia acts on and ΔU_reference is
computed from. `domains/tolaria.md` already names kernel-selection and RNG-stream rules
across a topology change as an LLD deliverable; optimiser-level aggregation is the third
place a topology change perturbs a matched pair and is named nowhere.

**S22 — no invariant pins learned-component versions across a confirmatory campaign.**
If a learned component upstream of the pool (Momir's critic, Jin-Gitaxias's field
surrogate, Aurelia's policy) is refit *during* a campaign on measurements from
trajectories in that campaign, it carries information between base host trajectories
and couples them — breaking the between-unit independence the headline CI and the n = 32
sizing assume. INV-32 does not reach it: it constrains where a *branch* sits in a split,
and learned parameters are not branches. The existing freeze rule is Isperia-only
(`domains/isperia.md`, "Decision thresholds are frozen before confirmatory runs"). Fix:
freeze learned components across a confirmatory campaign, refit only between campaigns,
record a training-trajectory manifest alongside `GrowthRecord.split_membership`. Note
the verifier dropped the within-trajectory framing — ΔU is measured in matched branches
rather than predicted, and the pre-registration aggregates to one number per unit before
any test, so within-unit dependence cannot inflate n or bias the point estimate. The
claim is between-unit independence only.

**S8 — the labels Momir learns from lose resolution as Momir improves, and nothing
measures it.** Sibling-vs-sibling ordering within a pool is a declared Momir objective
(`programme/learning.md`, "pairwise and listwise ranking over complete candidate
neighbourhoods") whose resolution no endpoint in `programme/evaluation.md` measures. The
only signal-to-noise instrument the programme declares — campaign 1's M1 d_z(H) curve —
measures candidate-versus-no-op effect, which grows as candidates improve, while the
within-pool spread contracts. A healthy d_z(H) is compatible with a pool in which no pair
of Momir candidates is separable. This is the structural analogue of the predecessor's
class-(1) failure — signal present, optimiser cannot receive it — but it is materially
weaker than the panelist claimed: `07-counterfactual-engine.md#141-candidate-pool` makes
reference seeds, analytic controls and the harmful fixtures *permanent* pool members, so
Momir's load-bearing objectives (ΔU_no-op, ΔU_parent, ΔU_reference) are measured against
fixed-quality anchors whose margins grow rather than shrink. What remains is a
metric-completeness gap on a secondary signal, and any statistic must key to evidence
uncertainty U_c, not σ_exec, since `07-counterfactual-engine.md` zeroes the execution
component under the Academy-exact profile.

| # | Narrowed claim (verifier) | Fix · artifact |
|---|---|---|
| S27 · MED | INV-04's branch-only-shortcut clause demands a "measured error" and routes it nowhere; a declared shortcut is not a rung on any `ScaffoldState` axis, so Leyline cannot detect one, and it gets no decision-aware withdrawal gate | Name the parity-approximation error as the surviving non-execution component of σ_exec, explicitly not zeroed under `ACADEMY_EXACT`; add a shortcut identifier to `BranchResult`, `ScaffoldState`-visible · `07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins` |
| S19 · MED | INV-21 states a genuinely numeric conformance predicate and declares no tolerance, and unlike INV-05 after ADR-0013 carries no pointer to where one lives — an undefined predicate on a hard Stage-1 admission gate | Bind INV-21 to Leyline's numerical contract in ADR-0013's style; state whether the conformance residual has an evidentiary home · `02-constitution.md`, `domains/leyline.md` |
| S5 · MED | The anchor corpus's unique contribution — policy-independent counterfactual labels — has support only on the never-intervened spine, because (e)'s free-no-op mechanism requires the no-op arm to be the base seed's own all-no-op trajectory. Unstated in (e); ADR-0011's caveat does not say the conditioning path is always the null one | Two one-line amendments: the free-no-op saving requires a single already-paid chain; the chain chosen is the null one · `cost-model.md#e-anchor-corpus-pricing`, ADR-0011 |
| S30 · LOW | Bare specification gap: the corpus does not state whether `Snapshot.fixed_future_minibatch_sequence` is the deterministic continuation of the same snapshot's `dataloader_cursor` or drawn independently. No cost line, no free canary, no estimand consequence attaches | One clarifying sentence at Tolaria LLD · `domains/tolaria.md` |

### 1.2 What threatens the generated-beats-selected claim

This is the empirical bet, and it is where the panel is most sceptical.

**S39 — the pivot gate may be unidentified at the rungs the MVP funds, and two open
tracker items collide.** ΔU_reference takes its maximum over the reference population R,
which `06-growth-model.md#114-reference-seed-bootstrap-and-scaffold-withdrawal` defines
to include attention-derived cells. Neither the Level 1 envelope nor Level 2's grammar
contains an attention operator; Level 3's whitelisted-DAG rung is where it first becomes
expressible, and `programme/phases.md` excludes it from the MVP. So ΔU_reference is not
matched on function class to the generator at the rungs the MVP can afford. The
counterargument lands partly — Level 2 already covers normalisation placement, low-rank
factorisation and gating pattern, so only attention is cleanly outside, and
`07-counterfactual-engine.md#141-candidate-pool` admits only *compatible* reference seeds,
so the max is not always over all six.

The genuinely untracked increment is a collision between two priority-1 open items.
simic-b75a7c2742 proposes promoting ΔU_reference to the headline criterion.
simic-03de2210b6 proposes starting the MVP at "L0 retrieval over the fixed five," where
Momir's output is a member of R and ΔU_reference ≤ 0 identically. Adopt both as written
and the headline success criterion is non-positive by construction at the MVP rung.
Neither item's body mentions the other. The fix is cheap and need not precede the fleet:
INV-31 and the ordered-neighbourhood retention rule guarantee every reference seed's
per-state utility is stored, so a level-restricted max and a winning-reference-class
breakdown are computable post hoc. Land it as a reporting requirement beside
"reference-frontier utility improvement" in `programme/evaluation.md`.

**S43 — the corpus's inference from a low retrieval hit rate is non-identified in the
direction that flatters the design.** `cost-model.md#d-the-amortisation-bar` reads a low ν
with positive ΔU_reference as "the strongest available result for the pivot." But ν is
not identified: its measurement basis is an open decision
(`risks-and-open-decisions.md#278-retrieval-similarity` asks whether retrieval is by
telemetry distance, learned embeddings, gradient alignment, functional effect, task
context, lineage or a calibrated mixture); it is not yet a listed metric
(simic-6c02a142b6 is the open request to add it); if keyed on canonical-hash recurrence
then Elesh's sound-but-incomplete canonicalisation depresses it (simic-0b259d9d6c), *and*
Momir's mandated stochastic latent diversity depresses it by construction rather than by
defect; and ν is 0.0 by cold start until Phase G. All four confounds push ν down, so the
low-ν branch — the branch the design hopes for — is the non-identified one. The
symmetric half is sound: a high ν does indicate convergence toward the library regime.
Do not add a Momir hash-stability test, which would contradict `domains/momir.md`'s
diversity mandate; condition the interpretive sentence on a stated measurement procedure
and an archive-maturity threshold.

| # | Narrowed claim (verifier) | Fix · artifact |
|---|---|---|
| S40 · MED | The design corpus contains no related-work positioning of any kind — a grep across `docs/design/`, `docs/adr/`, `docs/product/` returns zero named external papers. It names the right comparator *classes* but never instantiates them, so ΔU_reference is denominated against microcell *shapes* and no growth *criterion*. The "irreducible" claim itself survives: its stated comparison class is ESPER/ESPER LITE retrofittability, not the published field | Name the family and its instances; state whether the "analytic controls" clause admits growth-criterion baselines into R · new `docs/design/00-related-work.md`, `06-growth-model.md#114-reference-seed-bootstrap-and-scaffold-withdrawal` |
| S34 · MED | `C_retrieval` appears once corpus-wide, inside (d)'s formula, with no parameter row, placeholder or retirement path — violating the chapter's own opening rule. Since ∂/∂ν of the per-use term is exactly C_retrieval − C_admit, "the bar softens exactly as ν rises" states a direction no declared quantity supports, and `domains/urborg.md` requires a retrieved growth to re-pass Elesh, Urabrask, QA *and* adjudication | Add a C_retrieval row derived from a declared re-qualification pool shape, or withdraw the directional claim from `cost-model.md` and ADR-0014. Do **not** add a staleness tolerance on prior QA evidence |
| S10 · MED | Naming and claim-scope defect, not an instrument defect: nine sites apply "design prior" to an axis whose content is the Urborg ancestry channel alone, while the corpus's operationally precise sites already say "Momir ancestry" | Rename the field and restate `01-claim.md#28-success-criteria` criterion 15 as ancestry-channel withdrawal; file the fixed L1 envelope under `appendices/scaffold-pattern.md` F.6, which it predates and was never filed against |
| S21 · MED | "Functional diversity" is load-bearing in five places — mode-collapse mitigation, a Momir domain invariant, a Momir test, a candidate-design metric, a training objective — and the corpus defines no measure: no probe, no output space, no distance, no aggregate, no evaluation point. An undefined objective cannot be optimised; an undefined test cannot run | Name the statistic and its evaluation point; the data is already bought, since every pool arm produces a `BranchResult` with activation and gradient trajectories · `programme/evaluation.md` |

### 1.3 What threatens the statistical spine

The spine is well built — the unit of analysis is right, the D_eff algebra is correct
and correctly applied, and the winner's-curse sizing rule and blinded interim are
textbook. The defects are in the plumbing between the correct pieces. S6 and S2 are in
the verdict; the rest:

**S1 — n scales as ≈ 3/p_R, and the one rule that would repair it omits p_R.** The
confirmatory fleet size is inversely proportional to a declared placeholder that
campaign 1's M2 is commissioned to measure: p_R = 0.05 → n ≈ 65, and power at n = 32
falls to 0.50. The corpus provides the repair route —
`prereg-cost-model-campaign-1.md`'s retirement map states K/N are provisional until M2,
and ADR-0014's reversal trigger commits that "K/N must be re-derived before any
confirmatory unit runs" — but that trigger enumerates only h and ρ, and the closed-form
sizing rule pre-commits only the 80% UCL of sd_d. p_R, the more leveraged of the two
flagged parameters (halving it doubles n; the ρ trigger fires at a ~30% power cost), has
no sizing rule and no trigger row. Add p_R to the trigger list, extend the sizing rule to
the 80% *lower* confidence limit of p̂_R (n ≥ ~3.2/p_R^LCL at K_true = 3, K_floor = 1.5 —
noting SE(p̂_R) ≈ 0.054 from the 12-unit pilot already implies n ≈ 59 from a point
estimate of exactly 0.10), and state the effect frame in one sentence, because
ratio-stable and difference-stable effects give *opposite* re-sizes and cross exactly at
p_R = 0.10.

| # | Narrowed claim (verifier) | Fix · artifact |
|---|---|---|
| S3 · MED | No artifact pre-specifies which of the two n = 32 corner cells supplies the primary confirmatory endpoint. The choice is load-bearing, not bookkeeping: the scaffolded corner runs Momir under `REFERENCE_ANCESTRY` against a random arm with none, conflating generation quality with the ancestry scaffold. The α-inflation figures and the fleet-cost half of the original finding are dropped | Name the confirmatory corner and add it to the enumerated "Locked at launch" list; declare the other descriptive — the move ADR-0014 D4 already made for the online-cost clause · ADR-0014 D7, `cost-model.md#b-fleet-arithmetic--why-branches-do-not-buy-power` |
| S4 · MED | ρ is declared and instrumented as a *level* ICC ("ICC of pool outcomes") but consumed as the deflator of the *paired-difference* SD, which requires ρ_d. ρ_d is never measured, and (a) and prereg M3 name two disagreeing estimators for one symbol. ADR-0014's ρ trigger is keyed on a quantity absent from the calculation it protects — but is redundant, since `prereg-cost-model-campaign-1.md`'s sizing-discipline rule (fleet sized at the 80% UCL of the M4 estimate, never its point estimate) already covers the failure mode unconditionally | Split ρ into ρ_level and ρ_d; state only ρ_d enters the sd_d path; re-key or delete the ρ trigger; reconcile M2's "random-only pools" with M4's "the same pools" |
| S41 · MED | Campaign 1's M2 does not declare whether random candidates are instantiated one-shot with random weights or receive nursery maturation. Random θ inside a low-rank residual is near-certain to yield no positive evidence (p_R → 0); random structure with nursery-fitted weights is a genuine competitor. The floor is δ − (K_floor − 1)·p_R, so the choice moves the absolute bar monotonically, in the direction favourable to the hypothesis | Declare the control arm's maturation mode and seed policy before M2 runs; record in `ScaffoldState` (INV-39) · `prereg-cost-model-campaign-1.md` |
| S7 · LOW | ADR-0014 D1 and its two echoes cite `01-claim.md#28-success-criteria`'s negative clause as what the inferiority margin keeps true, but that clause names analytic construction, retrieval, bounded online optimisation and static over-provisioning — not random search, which the same chapter enumerates separately. The correctly-worded version already exists in the prereg | Drafting propagation, not re-pricing: bring ADR-0014, `cost-model.md` and PDR-0026 into line with the prereg's wording; state once that the four named comparators remain descriptive at n = 32 |
| S35 · MED | Two residues: ADR-0014 D1's "stays literally true at that stated, weakened strength" describes a different *claim shape*, not a weakening — the clause requires *dominance*, and a failure-to-establish at a floor is consistent with Momir being 1.4× better. Separately, criterion 17's static-host frontier comparison has no metric family and no budget line, and is the one comparator that cannot be an in-pool candidate | Replace D1's sentence with the honest form; add a static-host arm (~60–100 HER, no matched branches, no blinding, runnable after the fleet) or strike criterion 17 |

### 1.4 What threatens the governance apparatus

The lexicographic ordering, non-tradeability, containment accountability and the
Momir/Isperia split are correct and the panel added nothing to them. Two findings sit on
axes nobody had audited.

**S14 — ADR-0004 gave the assurance class the veto operating point without revisiting who
authors that field.** INV-45 assigns the assurance class ownership of the tail-risk veto's
operating point. `assurance_class` remains an Aurelia-authored `GrowthIntent` field
(`05-leyline-contracts.md#93-growthintent`, line 90; `02-constitution.md`'s
evidence-routing rule classifies it as a benign scope field), and no record upstream bounds
the choice: `StrategicEnvelope` has `permitted_grammar_profiles[]` but no
permitted-assurance-classes analogue, and the resolver's enumerated duties never mention
the field — so "the resolver cannot invent a more permissive request" has nothing to bind
against here. ADR-0004's own "Files updated" list names six files and includes neither the
`GrowthIntent` contract nor the Ugin/Aurelia authority tests. The exposure is on ADR-0004's
own reasoning: it rejected raising ξ because "a tunable weight on catastrophe is Goodhart
bait of exactly the class the pivot exists to eliminate," and an RL-refined Aurelia
selecting the class selects that weight.

Two parts of the original claim do not survive and should not be repeated: the veto
operating point *is* a constant common factor across arms of the headline comparison (all
arms share one pool at one host state under one `GrowthRequest`), and Ugin selecting
`admissibility_policy_id` is stated design intent, not the same breach. The best defence is
that `risk_ceiling` sits in `region_allocations[]` undefined and is the obvious intended
clamp — which concedes the slot exists and is empty.

**S16 — `CONTAINMENT_CATASTROPHE` is bound to accountability and to no control action.**
ADR-0010 makes a containment a defect report against the admitting
`adjudication_policy_version`, and the repair is a human ADR. Every lever a post-containment
clamp would need already exists — per-region `cooldown`, `risk_ceiling`,
`max_interventions`, Ugin's "embargoes or emergency restrictions", the assurance class's
ownership of the veto operating point — and no rule connects a containment to any of them,
and no latency bound governs the interval. The realised harm is economic and evidentiary,
not a safety-property violation: Tolaria's mechanical detect-and-contain still fires on
every subsequent breach, so the failure mode is repeated contained admissions burning
bounded confirmatory compute. Critically, the repair must be a *pre-registered,
deterministic, stateful clause of* `adjudication_policy_version` — not the out-of-band,
governor-owned suspension the panelist proposed, which would make the effective policy
history-dependent mid-cell and contaminate the paired design worse than the containments it
prevents.

| # | Narrowed claim (verifier) | Fix · artifact |
|---|---|---|
| S24 · MED | Provider blindness is documented as a *construction* guarantee it cannot deliver, and tested by an assertion that cannot detect the gap. For the permanent enumerated reference-control class, provider class is recoverable from mandated non-source fields — Jin-Gitaxias must execute the structure, and Isperia's view carries `canonical_semantic_hash` plus `measured_costs`/`parameter_cost`/`measured_latency`, any of which fingerprints a five-member set. INV-20 and INV-37 are **not** jointly unsatisfiable, and salting the hash closes nothing | State that the guarantee is source-*label* absence; add a positive control — a classifier on the adjudication view must fail to recover provider class above chance, with a matched negative control on `research_view` that succeeds · `07-counterfactual-engine.md#147-dual-provider-blindness`, `programme/evaluation.md#219-isperia-adjudication-tests` |
| S13 · LOW | `GrowthRequest` carries `permitted_blend_policy_class` and `permitted_evaluation_horizons[]` as adjacent resolved fields with no coupling rule, and INV-30's grace period is stated without reference to the horizon that certified the growth. `u_admit`'s evidence-uncertainty term already charges "horizon extrapolation" but nothing sizes that charge against the declared protected window | Make the declared window an input to U_c and record window-length-vs-certified-horizon in the `AdmissionDecision`; not a hard invariant ceiling |
| S17 · LOW | Citation-precision defect: three sites cite INV-31 ("complete negative retention") as authority for recording thin-margin veto *passes*, and INV-31 enumerates six negatives only. Not a retention gap — `domains/urborg.md#151-required-records` already mandates near-miss records by name, and `tail_veto_results` is non-nullable | Repoint the three citations at `domains/urborg.md#151-required-records` and the `AdmissionDecision` contract. No invariant amendment |
| S15 · LOW | `docs/product/metrics.md`'s north-star row and PDR-0005 describe the endpoint as "admission-worthy" — a post-veto, post-utility property — while the operational endpoint is measured at the `QualityReport` boundary | Restate the row in the operational phrasing; note the supersession in PDR-0005's lineage (see verdict item 1 for why this is the *smaller* half of the endpoint problem) |

---

## Part 2 — Engineering findings

**S23 — absence encoding stops at `TelemetryEnvelope`.** `validity_mask` occurs at exactly
one place in the entire Leyline suite (`05-leyline-contracts.md`, line 65), while ADR-0015
assigns Tier 2 to "Telemetry readings, QA measurements, branch outcomes, candidate
evaluations" and fixes the posture as an explicit invalid marker, "never a fabricated
default." ADR-0006 gives that marker its discriminating property: a `validity_mask=false`
field is *unreadable as a value*. The narrowed defect is precise and survives: per-candidate
evidence incompleteness has no typed home. `evidence_completeness` sits at report level
while `candidate_reports[]` is the per-candidate record, and Isperia's Stage-1 hard
eligibility is adjudicated per candidate — so one report-level field cannot say "candidate 3's
long horizon was never observed while 1, 2 and 4 completed." The only per-candidate channel
is the untyped `hard_defects[]` string list, whose semantics
`risks-and-open-decisions.md#276-jin-gitaxias-isperia-contract` explicitly leaves open.

This is a defence-in-depth gap, not a live bypass: reaching an admission additionally
requires the producer to mis-set completeness. But the refutation cannot be completed
without endorsing doctrine-by-convention, which ADR-0015 and ADR-0006 each rejected by name
for this exact defect class. Use the chapter's existing `| null` idiom and ADR-0015's own
named marker, not a new wrapper type, and add a rule that a branch truncated at horizon h
emits no readable value beyond h.

**S18 and S11 — the canonical-hash story is undeclared, and the two proposed fixes are
different shapes.** S18: the corpus under-declares `canonical_semantic_hash`'s preimage and
leaves `equivalence_class_id` wholly undefined (the field occurs once corpus-wide). Under
the value-inclusive reading that Elesh's own canonicalisation rule implies, Wrenn's
invariant "the embodied canonical semantic hash matches Isperia's selected hash and
Jin-Gitaxias's tested hash" is unsatisfiable in nursery mode — the default configuration —
because maturation changes the embodied weights while `GrowthRecord` keeps one
`canonical_growth_spec` and a separate `maturation_history`. INV-22 covers the branch path;
nursery is uncovered. S11 reaches the same hole from maturation and asks for an Elesh
re-canonicalisation event before QUALIFYING.

**These are not the same fix and the owner must pick one.** S18 scopes INV-20 and the Wrenn
check to the *birth* spec, accounting matured state in `maturation_history`. S11 mints a new
canonical identity at the maturation edge. The discriminator: does anything downstream need
to *name* the matured object — as an Urborg retrieval key, a warrant binding, or the subject
of the QUALIFYING re-adjudication that `06-growth-model.md` mandates? If yes, the event is
required. If matured state is only ever accounted in history, scoping the invariant
suffices. Both verifiers agree this is an identity/contract gap, not a safety gap: the
matured form does pass a full QA-plus-adjudication state before any influence is raised.

**G1 — continued-tenancy QA is mandatory and in MVP scope, and the cost model has no term
for it.** The sharpest single piece of evidence in the packet: INV-15 reads "every admission
**and continued-tenancy case** includes a measured no-intervention alternative," and
`cost-model.md#c-per-admitted-growth-cost-stack` restates it as "every admission case
includes a measured no-intervention alternative (**INV-15**)" — the clause that generates the
missing cost is the clause that is gone. Everything needed to price it exists: Emrakul
schedules periodic continued-tenancy QA, `MaintenanceDecision` is produced from a maintenance
`QualityReport`, INV-27 requires a maintenance warrant, and `programme/evaluation.md` names
"maintenance costs" as an Economy metric. The chapter's own precedent makes this a defect
rather than a scoping choice: rent μ is a *smaller* post-commit cost and got a declared
parameter plus an explicit "excluded by declaration, not by oversight." Tenancy QA is a
per-resident-per-period *stock* cost in the dominant (branch) class — it grows with the
programme's success — and got nothing. Do not fold it into the 40-HER trigger; the named
lever is the tiered Field QA cascade, which cannot touch a post-commit cost.

**G3 — five runtime-only constitutional detectors have no producer and land in Phase K.**
`ops/observability.md` lists twelve smell-event types; seven are reachable by Phase A's
import-lint and authority tests or by schema invalidity. The other five —
`SOURCE_BLINDING_BREACH`, `OBSERVATION_IDENTITY_MISMATCH`, `REQUEST_CHANNEL_COLLUSION`,
`BOOTSTRAP_SCAFFOLD_LEAK`, `TELEMETRY_MEDIATION_ATTEMPT` — are statements about what a
specific consumer actually received on a specific decision. Each string occurs exactly once
in the repository. None has a producer, though `EventEnvelope` carries a mandatory `producer`
field, and Tamiyo cannot be it (disconnecting Tamiyo must change nothing). They are scheduled
in Phase K while the confirmatory fleet needs only F, G and H — so every measurement the
claim rests on completes before the runtime detector layer exists, and these are precisely
the runtime counterparts of the checks S24 and S25 found vacuous.

| # | Narrowed claim (verifier) | Fix · artifact |
|---|---|---|
| S31 · HIGH | `ops/migration.md` is a live, post-ADR-0008-edited chapter still instructing repair-in-place migration from esper-lite. Three instructions are prohibited by locked records: compatibility aliases and "removal dates for old aliases" against `docs/product/vision.md`'s "No legacy / backwards-compat / shim code" and ADR-0008's "no legacy aliases"; `LegacyTamiyoController` survived the same Namespec 2.0 pass that named it. Phase A's "establish versioning and compatibility" bullet has this chapter as its only elaboration. The "no phase builds the lifecycle" claim does **not** survive | Rewrite as a per-subsystem reuse-posture table (port / reimplement-from-spec / read-only reference / drop); delete the alias instructions; change Phase I's "calibrate sedation, decay and lysis execution" to implement-then-calibrate |
| S20 · MED | INV-24 enumerates seven fail-closed version classes and omits canonicaliser version, though `CanonicalGrowthSpec` carries `canonicalizer_version` immediately adjacent to `grammar_version`. A canonicaliser-only bump has no declared re-baselining event where ADR-0013 established exactly that discipline for the execution-stack pin. Not an invisible ν collapse — the version is stamped per record | Add canonicaliser version to INV-24's list; declare the hash-comparability rule. Skip the migration-map apparatus |
| S26 · LOW | INV-24 asserts fail-closed behaviour across seven axes and the corpus nowhere enumerates them per axis, so `programme/evaluation.md`'s "version incompatibility failures" test line has nothing to be written against. The mandate, failure posture and module are all assigned; nothing connects them | A seven-row table: per axis, the version-bearing field, the checking consumer, the failure mode · `05-leyline-contracts.md` |
| S25 · LOW | Differential Aurelia/Momir envelope content is **NOT** contract-legal — four sites require the same `TelemetryEnvelope`. Two statement-level defects survive: `05-leyline-contracts.md`'s envelope-id clause does not cross-reference that requirement, and the INV-07 test is stated at `observation_id` granularity so it would not fail on a content divergence | Cross-reference the field-identity requirement; strengthen the test to envelope-content equality · `programme/evaluation.md#213-observation-routing-and-assignment-brief-tests` |
| S12 · MED | `cost-model.md` excludes nursery maturation and re-qualification *without declaring the exclusion*, breaking its own stated discipline and the exclusion-by-declaration pattern it applies to rent. Separately the corpus disagrees on the default maturation mode: `06-growth-model.md` declares nursery default while `risks-and-open-decisions.md` still lists it open | A declaration paragraph plus a reconciliation, not new arithmetic; neither omitted term moves any number materially, and neither belongs in the trigger inequality |
| S28 · MED | ADR-0013's re-baselining event does not state whether measurements and labels collected under a prior stack identity remain poolable. Concrete exposure is ADR-0011's 168-HER anchor corpus, whose only staleness mechanism is *periodic* refresh rather than event-driven on a pin move. The `ScaffoldState`-axis and τ-misclassification framings do not survive | Require the poolability determination for prior-stack labels to be recorded in the re-baselining event; amend ADR-0011's consequences |
| S29 · MED | τ is a correct within-device quantity, not a conflation. The surviving defect is one line: `prereg-cost-model-campaign-1.md`'s re-tightening trigger fires the CPU-lab device class automatically off a τ threshold when the entire consequence lands in wall-clock, the dimension the model declares itself blind to — and it is an outlier against ADR-0013 and `phases.md`, which both say the operating point is *chosen*, not defaulted | Report M5's already-collected CPU-vs-GPU timing as a named quantity; re-denominate the trigger in projected wall-clock; make the switch a recorded decision |
| S33 · LOW | The fifteen open design decisions are a second design-debt register the burn-down does not count, and the file does not distinguish decisions closable by deliberation from those retired by a later measurement. One genuine field-level gap: the raw-vs-certified-derived distinction appears nowhere else in `docs/design/`, so `QualityReport.candidate_reports[]` carries no provenance marker for it. Phase A is **not** blocked — placeholder-plus-`schema_version` is the corpus's own pattern | Tag each entry closable-by-deliberation or retired-by-⟨measurement, phase⟩; open tracker items for those bearing on a contract surface |
| S32 · MED | The programme measures Momir-vs-control candidate quality repeatedly before the fleet, but none of those gates carries a numeric threshold, none compares against the random arm the headline is denominated in (Stage 1F is reference-relative), and none is wired to the fleet launch decision. ADR-0014's triggers gate on precision and configuration, never on effect. The winner-take-all sub-claim is wrong — it is the standard diversity-*inducing* oracle loss | Put a number and a fleet-launch consequence on `programme/curriculum.md` Stage 1F, expressed against the random arm — **not** a futility boundary in campaign 1, which runs before Momir's bootstrap curriculum and would fire on an untrained Momir |
| S9 · LOW | `cost-model.md#d-the-amortisation-bar` identifies λ_cost with `u_admit`'s λ and multiplies it by an HER-denominated quantity, silently requiring C_c ("compute and latency cost") to be HER-denominated too — a unit isperia.md never states and which fuses compute with latency. λ_cost appears in no parameter table, status table or locked/reversible list | Declare C_c's unit and its disjointness from C_admit; add a λ_cost row with a retirement path; de-collide R (reference set vs Esper reuse factor) *inside one displayed equation*, and μ/ν across the two chapters |
| S36 · MED | Inconclusive is the modal fleet outcome (0.845/0.846 below K = 3) and no artifact records what the owner does when the CI straddles K_floor. The word appears once in `docs/`. The *stated* consequence does not follow — the "Locked at launch" list already forbids the post-hoc moves that would destroy confirmatory status | Add a third band with a pre-committed response. Note "extend to the 185-trajectory fleet" is currently *prohibited* as post-hoc; it is legitimate only if pre-committed now as a two-stage design with explicit α accounting · `docs/product/metrics.md` |
| S37 · MED | Not an absent category — the inherited taxonomy's reversibility test is general — but an **unresolved collision**: `vision.md`'s grant affirmatively permits "EXTEND runs, or ADD runs at its own discretion," and the operating model states the grant, not the default, is the actual authority. An affirmative specific permission is not cured by a general default | One line: bound the run-authorization and experiment-value clauses to **exploratory** work, and name the pre-registered n / K_floor / endpoint family / stopping rule as reserved once data exists |
| S38 · LOW | PDR-0034's session-count limb does not state whether the zero-closure session in which it was authored counts toward "fourth consecutive," so for a one-session window the count is unstated. The trigger's *dated* limb is unambiguous and backstops it deterministically, so the bet cannot drift silently to the date | Name the first session that counts; state the running count in the burn-down row |

---

## Part 3 — Value: pivot and enhancement options

Three judges scored fifteen proposals: **E** = evidential strength, **F** = feasibility for
one person on spare time, **S** = strategic value and optionality. Rows ordered by mean; the
mean is used for ordering only. Where judges split, the split is published rather than
averaged.

| # | Proposal | E | F | S | Adjudicated verdict |
|---|---|---|---|---|---|
| P1 | Headroom probe: measure the prize before building the machine | 9 | 9 | 10 | **ADOPT** — with the control repaired |
| P13 | Metrology gate: Phase D′ kill gate on hand-built growths | 8 | 6 | 9 | **ADOPT_WITH_CHANGES** — unbundle; G2 first |
| P14 | Boundaries-first Phase A with declared contract maturity | 5 | 9 | 9 | **ADOPT** — minus the metric clause |
| P9 | Unbundle campaign 1 by phase-earliest; h is a Phase-D measurement | 7 | 8 | 7 | **ADOPT** — one record with P13 |
| P11 | Widen campaign 1 M1 into a mid-training intervention zoo | 8 | 6 | 8 | **ADOPT_WITH_CHANGES** — keep the kill-switch, drop the zoo |
| P4 | Fix the estimator: matched arms, audit-split scoring, continuous scale | 8 | 5 | 8 | **ADOPT_WITH_CHANGES** — split it |
| P7 | Run the pivot question on the demo substrate: the generation arm | 6 | 8 | 7 | **ADOPT_WITH_CHANGES** — merge into P2 |
| P6 | Give the anchor corpus the sizing discipline the fleet already has | 6 | 7 | 7 | **ADOPT** |
| P2 | Experiment 2 becomes the pivot gate: a generated arm in every fan | 7 | 6 | 6 | **ADOPT_WITH_CHANGES** — gated on P1 |
| P5 | Derive D and the analysis plan instead of asserting them | 6 | 7 | 6 | **ADOPT_WITH_CHANGES** — take the factorial half |
| P15 | Schedule on the attention/compute asymmetry | 5 | 8 | 6 | **ADOPT_WITH_CHANGES** — minus the metric demotion |
| P10 | GCCS: counterfactual metrology for growth criteria | 7 | **3** | 7 | **SPLIT — see below** |
| P8 | Re-goal the burn-down: blocking-set-empty | **3** | **9** | **4** | **CONTESTED — owner decision** |
| P12 | Ship the decision corpus as a benchmark | 4 | 4 | 5 | **INVESTIGATE** — schema half only |
| P3 | One confirmatory cell, no interaction matrix, corpus deferred | **2** | 5 | 4 | **REJECT** as timed; one free increment |

### The proposals that carry the value

**P1 — headroom probe (ADOPT, with a required repair).** Fork the kernel demo, add a
parameterised search over the L1 envelope and two compound off-menu pathologies composed
from `Host.__init__`'s already-orthogonal knobs, and measure the headroom of a search
oracle above the menu-argmax, re-measured on a fresh common future to correct the
winner's curse. One overnight, ~0 HER against the programme budget, no `FROZEN_FIELDS`
touched. It puts an upper bound on the one quantity the corpus's central inequality has
no value for, before Phase A finishes, and it is the input every other empirical proposal
inherits.

**The control as written does not discriminate, and this must be fixed before it runs.**
P1 nominates the on-menu class as its positive control while defining it as the class
where `DESIGNED_WINNER` is already tuned to win, then predicts ≈0 headroom there, then
predicts real gains for the same class, then concedes that a null there makes the probe
uninformative. On-menu ≈ 0 *and* off-menu ≈ 0 is exactly the signature of a search too
weak everywhere. The repair is already in the packet: take P7's pre-registered
hand-authored oracle delta as a VOID gate, or run on-menu against a menu with that
pathology's designed winner removed, where a working search *must* recover the removed
gain. Without a positive-expectation control the decisive negative P1 advertises is not
obtainable.

Read it as a decision instrument, not as evidence: PDR-0029's non-citability rule stands,
a search oracle is an upper bound on any generator so a positive is permissive only, and
the off-menu class is owner-designed so the compounds must be pre-registered as
compositions of already-calibrated knobs, never chosen adversarially.

**P14 + P9 + P13 — start the programme.** P14 splits Phase A into boundaries (blocked by
nothing, permanent, empirically independent) and fields (whose content is a Phase D–H
measurement), with a declared draft/provisional/locked maturity per record class policed
by INV-24's fail-closed typed compatibility. It is mostly ratification of the owner's own
`current-state.md` analysis; the increment is the maturity mechanism and the
deliberation/measurement tagging. P9 releases campaign 1's instruments at their
phase-earliest — M5 and M6 at Phase B, M7 at Phase C, M1 at Phase D — which moves h, the
parameter that swings the per-intervention numbers fivefold and that the cost model says
it cannot be closed tighter than, months upstream of the decisions it governs. P13 adds
pre-committed kill thresholds and, in its G2, the sharpest single question anyone asked:
does argmax over the reference population *move* across host states? If one reference cell
is optimal everywhere, ΔU_reference has nothing to be positive about and selection wins by
construction — and it is answerable with six hand-authored cells, no Momir, no Elesh, no
Urborg.

**P4 — the estimator fixes.** Split it. Sub-change 1 (declare per-arm counts, require
matching) is verdict item 3 and lands now as a contract line. Sub-change 3 (make the
primary endpoint a continuous per-unit margin on the weight-free ΔL-versus-no-op scale,
demote the rate ratio to descriptive) is the only proposal that makes the *promised*
negative deliverable — at a latent-normal control tail of 0.10 the asymptotic relative
efficiency of the binarised endpoint is 0.34, so the negative that needs n ≈ 73 on the
binary scale lands at n ≈ 25. Its epistemics are right: the 0.34 is declared a prior and
the adoption rule is a *measured* variance ratio from a new M4b with a pre-stated
threshold. Sub-change 2 (score on the audit split rather than the screen split) uses
machinery `07-counterfactual-engine.md#142-data-separation` built for exactly this, on
branches that already ran.

**P10 — publish the split, not the mean (7 / 3 / 7).** The judges answered different
questions. Evidential and strategic judged the *result* and both found it rare and
valuable: it is the only proposal where a null is worth as much as a hit, and it is
Momir-independent, so it survives the branch where the generative bet fails — which is
the branch the corpus's own table makes most likely. Feasibility judged the *build* and
the fatal is specific and checkable: faithfully reimplementing four published growth
criteria on a foreign envelope, including a natural-gradient/Fisher expansion score,
priced at "3–5 spare-time weeks," is a research task with an open-ended debugging tail
grafted onto a programme that has not started building. Both are right. The adjudicated
verdict is the carve-out the feasibility judge named *while* rejecting the full study —
which captures the defensive value the other two scored it for: **take
the related-work chapter and the Phase-F control-naming line now** — hours of work,
capturing the defensive value against the novelty exposure in verdict item 5 — and treat
the full calibration study as a separate bet gated on Phase D existing. One design repair
if it ever runs: these criteria are argmax-selectors within their own families, so each
must construct its own candidate rather than be scored over a pool it would never have
proposed.

**P8 — contested three ways (3 / 9 / 4), and it is an owner decision.** The diagnosis is
correct and worth acting on: the burn-down is a stock target with an uncontrolled inflow,
the project's own chosen improvement method is that inflow, and this panel is about to
make the metric materially worse as a direct consequence of the owner doing the work well.
The feasibility judge rated it 9 because it *returns* attention, the only proposal that
does. The strategic judge rated it 4 and rejected it because its unique content is a
goalpost move PDR-0034 exists specifically to prevent — and applied the same constraint
consistently by carving the identical clause out of P14. The evidential judge rated it 3
because its one claimed empirical payload is confounded. The consistent resolution: take
P14's composition tagging and P8's intake-triage rule, apply the triage to this panel's
own output as its first act, and leave the target and the date alone unless the owner
rules that PDR-0034 binds the date only.

### Owner decisions where proposals and findings conflict

These are not for a panel to resolve. Each names the constraint that would discriminate.

**A. n is pulled three ways by three verified positions, and it is locked at launch.**
S1 and S2 say n = 32 is too small (p_R below ~0.07 gives under 70% power; the negative
needs 58–73). P3 says buy fewer cells. P4 says the *scale* is wrong, so n = 32 stands and
even over-delivers. **Discriminator: M4b's measured variance ratio between the binary and
continuous endpoint scales.** If ≤ 0.44, P4 wins and n = 32 buys a stronger claim than
currently priced. If not, S1/S2 govern and n must rise before the fleet locks. P3 is
orthogonal — it is about cells, not n — but its saving evaporates under S1/S2.

**B. S4 and S1 give opposite instructions for the same trigger list.** S4 recommends
deleting or re-keying ADR-0014's ρ trigger as redundant against the UCL-of-sd_d rule;
S1 recommends adding p_R to that same list. Both cannot be executed as written.
**Discriminator: sd_d subsumes p_R's effect on the variance but not on the margin** —
δ − (K_floor − 1)·p_R is an explicit function of p_R — so S1's extension is required and
S4's deletion is safe for the ρ row only. Implement one without seeing the collision and
the owner will believe the job is done.

**C. The canonical-hash story has two incompatible fixes (S18 vs S11).** Scope INV-20 and
the Wrenn check to the birth spec with matured state in `maturation_history`, or mint a new
canonical identity at the maturation edge. **Discriminator: does anything downstream need
to *name* the matured object** — Urborg retrieval key, warrant binding, the subject of the
QUALIFYING re-adjudication? If yes, the event is required; if matured state is only
accounted in history, scoping suffices.

**D. Adopting S37 reprices half of Part 3.** S37 asks for an evidentiary-one-way-door class
in `vision.md`'s escalate list, reserving any launch or extension of a confirmatory campaign
to the owner. It is correct on its own terms. It also converts P1, P2, P7, P11 and P13 from
compute-cost to owner-attention-cost — the binding constraint. Not an argument against S37;
an interaction the owner should price before adopting both.

**E. P13 and P9 restructure the same record and cannot both land as written.** P13's KILLS
line is campaign 1 as a standalone record; P9's entire content is splitting that record.
**Discriminator: does the metrology gate consume M1's d_z(H) curve as an input** (it must,
if its own branch horizons are chosen rather than assumed) **or produce it as an output?**
If input, P9 runs first and P13 absorbs the remainder — also the strictly better ordering.
Either way it must be ONE new record: `prereg-cost-model-campaign-1.md`'s own header
requires amendments be new records, never edits (INV-36), and P13's collision with that file's own scope clause
("produces no evidence about Momir's quality") must be resolved in that record, because a
kill threshold is a decision-bearing output.

**F. P3 vs P5, and P3 vs P6.** P5's zero-HER precision gain requires all eight scaffold
cells; P3 deletes six. **Discriminator: are `01-claim.md#28-success-criteria` criteria 15
and 16 first-stage or second-stage deliverables?** Separately, P3 defers the anchor corpus
past the fleet while P6 stages it. **Discriminator: does the anchored calibration reading
gate anything before Phase H?** If it does, P6 dominates, because P3 buys only delay while
P6 buys a decision point.

**G. The largest one: what should be true at write-up if Momir loses?** Keep
`01-claim.md`'s current headline and the work is a generation result carrying the novelty
exposure of verdict item 5, with its value concentrated in a branch the corpus's own table
says arrives 84.5% inconclusive. Adopt P10's reframing and the durable contribution becomes
the measurement standard, the generative bet becomes an extension of it, and a Momir null
stops being a programme-level failure. These are not compatible framings and the choice
should be recorded before Phase E, not discovered at write-up.

---

## What the panel did NOT find

Areas examined that came back clean. This is where **not** to spend.

- **Determinism machinery.** RNG-stream alignment across structurally different candidates
  is already a named Tolaria LLD deliverable and covered by closed simic-d1bdc7173f;
  divergence localisation exists as both a named harness and a reported metric. The
  determinism lens found nothing in the replay machinery itself — all four of its findings
  are about *accounting around* it.
- **Phase-ladder over-design.** The architecture lens went looking for gold-plating and found
  the opposite. The ladder already defers Ugin to Phase J, Emrakul to Phase I and Tamiyo to
  Phase K, with the MVP inventory stubbing them; the armour is scar-justified under
  `03-principles.md`'s own rule. Its two substantial findings are *unbuilt scope*, not excess.
- **Contract authority.** Sixteen of twenty record classes have exactly one named producer.
  `LifecycleCommand`'s two writers are phase-partitioned by INV-29 with an explicit
  `authority` field, and `EventEnvelope`'s many writers are disambiguated by `producer` — both
  designed. The four that name no author are the tracked orchestration gap simic-c912a35aa7.
- **The governor's core.** Lexicographic ordering, non-tradeability, containment
  accountability and the QA/judgement split are correct as specified; the governor lens added
  nothing to them and its findings are all on adjacent, un-audited axes.
- **The growth mechanism.** The lifecycle, the authority split at each transition, and the
  three-identity chain are stronger than most morphogenetic designs. The findings are at the
  seams, not the mechanism.
- **Three of the predecessor's four failure classes.** Instruments-that-lied is covered by the
  Field-calibration gates and INV-43/INV-44; fail-open seams by INV-24 and INV-38; over-reads
  by INV-31/INV-32 and the evidence/judgement split. Only class (1) recurs, and in the
  narrowed form of S8.
- **Generator self-approval.** The smell catalogue and Elesh's "does not consume task reward
  or future utility" invariant close the generator-grades-its-own-work and
  verifier-consumes-reward modes cleanly. No violation found.

**Where the panel itself is thin** — the completeness critic's own gaps, kept separate from
G1–G3, which are substantive findings placed in Parts 1 and 2 by subject:

- No lens audited **Tamiyo, Emrakul or Ugin** in depth. They are deferred to Phases I–K and
  every lens deprioritised them accordingly; that is a defensible allocation and an
  acknowledged blind spot.
- The **Aurelia→Momir channel bit-rate could not be bounded**, because `reason_code`
  cardinality, `tactical_deadline` resolution and the intent→request fan-in are nowhere
  declared. That undeclared cardinality is worth adding to simic-ca29f34fb4 as a sub-task
  rather than as a new finding.
- The claim-skeptic's **literature search was six queries**, and the negative half ("nobody
  validates a growth criterion against a matched counterfactual") is absence of evidence.
  Verdict item 5's positive half — how Gstack, GradMax and When-To-Grow are each actually
  evaluated — is verified; the negative half is not.
- **Nobody read the 60KB prior peer review in full.** Novelty was checked against 54
  tracker-item titles plus six full bodies, so a finding could still duplicate an untitled
  argument inside that document.
- **Nothing is implemented**, so every consumption trace in this report is a reading of a
  contract shape plus its stated consumer, never observed behaviour. S23 and S24 both assume
  the Phase A contracts will be authored from `05-leyline-contracts.md` as written; if the
  Phase A LLD already intends per-field validity or a salted blinded hash, both collapse to
  documentation drift, and that is worth checking before spending on either.

---

## Killed findings

Raised and refuted or found already-tracked. Recorded so they are not re-raised.

| Lens | Finding | Disposition |
|---|---|---|
| governor | The near-miss instrument is degenerate under Academy-exact deployment — it correlates a statistic with itself | **REFUTED.** Rests on reading "post-commit" as "after install/blend"; in this corpus it is a term of art naming the COMMITTED transition, four states downstream of QUALIFYING where the QA branch and veto live. Post-commit shock is measured on the live trajectory past the branch's common future. Urborg's own failure-code taxonomy splits QA-window codes from post-decision live-host codes. Also conflates *deterministic* with *already measured* — under that logic every measurement in a deterministic system is degenerate. Consequence fails independently: Isperia adjudication is Phase F, so no veto calibration was ever scheduled for Phases A–D |
| systems | The pre-registered test narrows the five-way claim to Momir-vs-random, leaving the corpus's own irreducible bet untested by the primary endpoint | **ALREADY_TRACKED — simic-b75a7c2742**, whose body states the thesis nearly verbatim. Two factual overstatements besides: reference, retrieval and analytic controls *are* measured on all 256 adjudicated pools (they are permanent blinded pool members), so the contrast is descriptive rather than nonexistent; and criterion 2 was never meant to carry all five comparators alone. The one residue worth attaching to that item is carried in verdict item 4 |
| systems | Design-debt burn-down stall is a Shifting-the-Burden archetype | **REFUTED.** The asymmetry premise is false — the design-debt track carries *more* structure than the demo's decision queue (six `wave:*` labels with a named dependency-critical path since PDR-0008). The "treats the symptom" premise is false — PDR-0034's reversal trigger is a rules-level intervention on allocation, and the roadmap conditions both other Now bets on this one. The archetype requires an atrophy mechanism, and none is named; two bets contending for one spare-time slot is resource contention |

---

## Recommended next actions

Ordered. Each names the artifact it lands in.

### Before Phase A

1. **Define the hit predicate once**, weight-free — matched-branch ΔL against the
   zero-anchored no-op (INV-15/INV-16) with a declared CI rule — and make the other three
   documents cite it rather than restate it. Add `adjudication_policy_version` to the
   placeholder-retirement table with the rule that M2's p_R is void if it differs from the
   fleet's. → `programme/evaluation.md`, `01-claim.md#28-success-criteria`,
   `cost-model.md#h-k-and-n-for-the-headline-criterion`, `prereg-cost-model-campaign-1.md`,
   `docs/product/metrics.md`. *(S6; verdict 1.)*
2. **Declare per-arm candidate counts and require arm-size matching** in every pool; re-derive
   the between-pool variance component the forced class rotation introduces. →
   `07-counterfactual-engine.md#141-candidate-pool`, `TestPlan` in `05-leyline-contracts.md`.
   *(P4 sub-1; verdict 3.)*
3. **Repair the sizing rules as one record** (INV-36 — new record, never an edit): add p_R to
   ADR-0014's reversal-trigger list, extend the sizing discipline to the 80% *lower* limit of
   p̂_R, state the effect frame, and re-key the ρ row per owner decision B. → new ADR +
   `prereg-cost-model-campaign-1.md` amendment. *(S1, S4.)*
4. **Correct ADR-0014 D1's power sentence** to name its alternative, publish
   P(abandon | K = 1) = 0.46 as the headline negative operating characteristic, recompute the
   operating-characteristics table with the per-K sd_d, and price the n ≈ 58–73 option
   explicitly so the owner takes or declines it as they did the 185. → new ADR,
   `cost-model.md#h-k-and-n-for-the-headline-criterion`. *(S2; verdict 2.)*
5. **Name the confirmatory corner** and add it to the enumerated "Locked at launch" list;
   declare the other corner descriptive. → ADR-0014 D7,
   `cost-model.md#b-fleet-arithmetic--why-branches-do-not-buy-power`. *(S3.)*
6. **Split Phase A** into boundaries and fields with declared per-record contract maturity;
   start the package skeleton and forbidden-import checks, which are blocked by nothing. →
   `programme/phases.md`, `05-leyline-contracts.md`, new PDR. *(P14, minus the metric clause.)*
7. **Add per-candidate absence encoding** to the evidence path using the chapter's `| null`
   idiom and ADR-0015's named marker, with the rule that a branch truncated at horizon h emits
   no readable value beyond h. → `05-leyline-contracts.md#913-branchresult`,
   `#914-qualityreport`. *(S23.)*
8. **Bound `assurance_class`**: add an assurance-class floor to `region_allocations[]` (or
   define `risk_ceiling` to serve as it) and add the authority test "Aurelia cannot obtain a
   looser assurance class than the envelope resolves." → `05-leyline-contracts.md#91-strategicenvelope`,
   `programme/evaluation.md#2112-ugin-and-aurelia-authority-tests`. *(S14.)*
9. **One declaration pass, one commit** — the statement-level defects, which are most of this
   report: S4's ρ split, S9's λ and symbol collisions, S12's maturation exclusion, S17/S24/S26
   citation repointing, S19's INV-21 tolerance binding, S20's canonicaliser row in INV-24,
   S25's envelope field-identity cross-reference, S28's poolability clause, S31's
   `ops/migration.md` rewrite, S33's open-decision tagging, S37's exploratory-scope clause,
   G1's tenancy-cost declaration, G2's growth-optimisation policy, G3's smell-event producers.
   Also: create `docs/design/00-related-work.md` and extend Phase F's control line to name the
   growth-criterion baselines *(P10 carve-out)*.
10. **Resolve the canonical-hash story** per owner decision C, then implement one of S18 or
    S11 — not both. → `05-leyline-contracts.md#98-canonicalgrowthspec`,
    `06-growth-model.md#112-one-shot-and-nursery-modes`.

### Before the fleet runs

11. **Run P1** with the control repaired (oracle-delta VOID gate or designed-winner removal),
    pipelined against items 1–9 so it costs no owner attention. Header must carry the
    non-citability scope.
12. **Decide E, then execute the early measurements** — M5/M6 at Phase B, M7 at Phase C, M1 at
    Phase D — as one new record. *(P9/P13.)*
13. **Add M4b and M9** to campaign 1 and decide n on the measured variance ratio per owner
    decision A. *(P4.)*
14. **Stage the anchor corpus** 8-then-size, with the consumer split argued in ADR-0011's own
    language. *(P6.)*
15. **Adopt the 2³ factorial analysis plan** for the eight cells — zero runs, zero contracts
    changed, six confirmatory-grade contrasts instead of two corner readings — and record why
    the resolution-IV half-fraction is unavailable (it aliases main effects with the two-way
    interactions INV-41 requires measured). *(P5, factorial half only.)*
16. **Run the instrument falsifier** — one deliberately strong hand-built intervention against
    the mandatory no-op across nested horizons — as the earliest test of the paired-branch
    premise itself. *(P11 reduced, or P13's G1.)*
17. **Give Stage 1F a number** expressed against the random arm, wired to the fleet-launch
    decision. → `programme/curriculum.md`. *(S32.)*
18. **Freeze learned components across a confirmatory campaign** and record the
    training-trajectory manifest. → `02-constitution.md`, `GrowthRecord`. *(S22.)*

### Eventually

19. **The merged generation arm** (P2 + P7 as one experiment, taking P7's held-out pathology
    and oracle gate with P2's three-reference estimand and leakage discipline), gated on P1
    reporting non-zero off-menu headroom, with a *capped* training budget declared before the
    loop starts.
20. **The full GCCS calibration study**, once Phase D exists and the criteria can be
    implemented honestly, with own-family construction pre-registered. *(P10.)*
21. **The `release_view` schema decision** at Phase F, when record shapes are locked and the
    data is real. The release itself stays on `vision.md`'s escalate list. *(P12.)*
22. **Price continued-tenancy QA** with a cadence parameter and its own INV-15 no-op arm, and
    carry it into the amortisation bar's "Simic, per use" bracket. → `cost-model.md`. *(G1.)*

### Decisions no panel can make

Owner decisions **A–G** in Part 3 are the ones that cannot be resolved by evidence the panel
has. Two of them gate work above: **A** gates item 13 and reprices item 3; **E** gates item 12.
**G** — what should be true at write-up if Momir loses — gates nothing mechanically and
determines everything about how the programme reads. It should be recorded before Phase E.

One further decision the panel surfaced without resolving: **B**, **C** and **D** each involve
two individually-correct findings whose fixes collide. In every case the collision is invisible
if either finding is implemented alone.
