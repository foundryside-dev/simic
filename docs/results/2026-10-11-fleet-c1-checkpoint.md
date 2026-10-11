# Fleet C1 checkpoint — 2026-10-11

**For John (PDR-0057: "G1, the screen and λ go to John before items 7–9 are built"). Nothing
launches from this note.**

Both fleets finished cleanly and were each analysed once, in the registered order:
- [Fleet C1](2026-10-11-fleet-c1.md): 768 seeds × 4 hosts, analysed at 14:48;
- [Fleet C1-S](2026-10-11-fleet-c1s.md): the BatchNorm hosts with the static arm born at τ,
  analysed at 17:47.

The [combined tables](2026-10-11-fleet-c1s/checkpoint-tables.md) are rendered from both reports.

## The readings

| Gate | Reading | Registered consequence (PDR-0057) |
|---|---|---|
| G1 on `under_normalized` (existence) | `non_inferior` to 2×. The graft (+129 parameters) beat uniform widening at every step: −0.071 at 2× | `c1: supported_at_bounded_scale` |
| G1 on `mild` (the honest, non-designed host) | `inconclusive`. Uniform 1.25× was ahead of the graft by 0.012; both lower bounds are above 0, and the upper bound is 0.0201 against a 0.02 margin | "Anything short of `non_inferior` on `mild` narrows C1 to designed pathologies, the expected result". Under D3, every `inconclusive` comes to you with stop on the menu |
| Deficit screen | One host passes: `under_normalized`, +0.142. The three BatchNorm hosts fail with the corrected arm too: +0.020, +0.004, −0.001 | "Fewer than two passing hosts means the host set is rebuilt or the pathway stops (John)" |
| λ | 0.0271 nats per doubling of parameters, pooled; point estimate | Frozen for every later gate |

Read together:
- **What holds.** At bounded scale, a targeted fix beats spending parameters uniformly where the
  host lacks a function. On `under_normalized` that function is normalisation.
- **What does not.** Where the host has no such gap, it doesn't: the honest host had nothing to
  repair. On `channel_starved`, the designed static (1.46× parameters) earned nothing over no
  growth, while 1.25× uniform widening was ahead of the graft by about 0.01. That last point is
  exploratory.
- **The static arm.** The defect did not change the screen's outcome: on the BatchNorm hosts,
  corrected minus registered is within ±0.009.

## The decision

PDR-0057 registered two options at this screen count, and they are yours.

### 1. Stop the controller pathway here

What it leaves:
- C1 published, narrowed to designed pathologies;
- a clean negative on "several repairable deficits exist at this scale" (four hosts, 768 seeds
  each);
- λ frozen;
- the hosts, the uniform scale-up comparators and λ, ready to use as a bar for any other
  approach. Sultai's "equal capability at about half the parameters" is one.

Cost: none.

### 2. Rebuild the host set

- **What it would be.** In practice, this is PDR-0057's parametric host family (pathology class,
  stage, severity, base width), brought forward. PDR-0057 costs that at about 35 hours of fleet
  time plus the family engineering, "only by a fresh decision".
- **A cheaper first step.** A screen-only pilot: no growth and corrected static on each candidate
  host. Fleet C1-S trained three static arms per seed in 28 s per seed per GPU. On that basis,
  eight candidate hosts at 192 seeds each is roughly 4 hours on two GPUs. That is an estimate,
  not a plan.
- **The circularity.** Building hosts until two pass the screen is the designed-winner problem
  PDR-0057 already names. It says Fleet A on designed hosts makes a `go` "weakly informative on
  its own", and that the real tests are G2′ and G5. A rebuild is only worth doing as the family
  G2′ and G5 need anyway, designed so G5's report hosts stay unseen. It is not a way to clear the
  two-host bar.
- **Sequencing.** It would be a new study: a sketch to you first (PDR-0053), seeds from the
  reserved host-family range (15001+), and the screen's criteria unchanged.

### Outside the registered options

Running Fleet A on `under_normalized` alone would need a new PDR. G2's split between
between-host and within-host headroom does not exist with one host. PDR-0057 also already found
no detectable per-seed timing headroom on a single host.

### What else this settles

- **The static-arm remedies** from the
  [diagnosis](2026-10-11-static-norm-divergence.md#what-this-means): (a) keep and disclose,
  (b) a guarded arm, (c) a different norm seed. They matter less than they did this morning.
  - Fleet C1's static arm diverged 0/768 on `under_normalized`.
  - The corrected arm diverged 0/2,304 on the BatchNorm hosts, at the 30× larger birth.
  - They matter only if the pathway continues.
- **The BatchNorm birth fix** (`simic-e3803e8200`) is a source change. The checkpoint doesn't
  need it, and it waits on the decision above.

## My recommendation

**Rebuild, as the host family, starting with the screen-only pilot.** I'd frame it as building
the family G5 needs, not as clearing the two-host bar.

The pattern here suggests where to look: the one host that passed lacks a function, while the
capacity-shaped pathologies were matched by uniform widening. So candidates should vary
missing-function pathologies by stage and severity. That is a hypothesis to screen, not a
finding.

The work also survives a Sultai win. Hosts with measured, graded deficits, priced against
uniform scale-up, are what a headroom learner trains on, whichever builder fills the site.

If your spare time is better spent on Sultai, stopping here is a clean place to stop. The
result is published and the comparators are ready for Sultai to use.
