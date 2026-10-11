# Training-regime design review — brief for the panel (2026-10-11)

**Scope (John, relayed by his assistant).** A design review only, while the controller pathway is
on a reversible defer ([`defer-record.md`](defer-record.md)).
- **Not allowed:** implementation, test or training launches, GPU use, spending, access grants,
  merging or deployment.
- **Thresholds:** none is retuned after results.
- **Sultai keeps GPU priority.**

**Starting point:** host-family proposal revision 3 (draft PR #45, `b6e01ec`), `proposal.md` and
`panel-review.md` in `docs/product/spikes/2026-10-11-host-family/`.

## What the panel is asked to review

1. **Convergence and training duration.** Is the 10-epoch, 4,096-example, constant-lr endpoint
   measuring the hosts before convergence, at a data or generalisation limit, or at an
   optimisation limit? What training duration or schedule would let capacity and intervention
   effects be judged?
2. **Compute-matched comparators.** Uniform scale-up, static and graft at matched parameters,
   parameter-steps or FLOPs. Which comparator answers the founding claim? What does "matched"
   mean once horizon changes?
3. **Intervention capacity against effect thresholds.** Can a ≤ 1.10× injection reach the frozen
   0.05-nat bar in principle? What does that imply for any future design, without retuning the
   bar?
4. **How natural the impairments are.** All of Simic's hosts carry authored handicaps from step 0
   (D3). What would a host with an emergent bottleneck look like, and can one be identified
   before any intervention is measured?
5. **The original Esper-lite closed loop, including keep or cull (L7).** Does any proposed future
   experiment address the founding loop (L1–L7, host-family proposal §1), or only synthetic
   compensation?

**Deliverable:**
- a reviewed recommendation, with sources and unresolved disagreements;
- the **smallest discriminating future experiments**, each with:
  - its question;
  - its arms;
  - pre-specified stop criteria;
  - a budget in GPU-hours, from measured bases;
  - a decision gate, with what each outcome would lead to;
  - whether it reaches the founding loop or only synthetic compensation.

**Separate observed evidence from hypotheses.** Never use low pairwise correlations to claim
independence.

## Observed evidence (index)

All of it is published or finished-and-analysed.

**Results:**
- `docs/results/2026-10-11-fleet-c1.md`, `-fleet-c1s.md`, `-fleet-c1-checkpoint.md`, each with an
  evidence folder holding a per-arm summary (`arms-summary.jsonl.gz`, which includes dev CE by
  epoch);
- `docs/results/2026-10-09-rung4-timing-horizon.md` and `…/tables/per-epoch.jsonl.gz` (train and
  dev CE per epoch to 20 epochs, `under_normalized`);
- `docs/results/2026-10-09-graft-capture-v2.md`, `-positive-control-v2.md`,
  `2026-10-08-bounded-screen-v1.md`;
- `docs/results/2026-10-11-static-norm-divergence.md`.

**Exploratory convergence tables, new for this review:** [`evidence/convergence.md`](evidence/convergence.md),
made by [`evidence/convergence.py.txt`](evidence/convergence.py.txt) on CPU from finished,
already-analysed records. Train CE is measured on augmented batches in train mode, so the
train–dev gap understates the true generalisation gap. What the tables show, descriptively:
- **The BatchNorm hosts** (`channel_starved`, `no_spatial_mix`, `mild`) at epoch 9:
  - train CE is about 1.05–1.09 and dev CE about 1.23–1.29;
  - the gap is +0.16 to +0.22 nats, up from about +0.10 at epoch 3;
  - dev CE is still falling about 0.03 nats per epoch;
  - 2× uniform widening lowers train and dev CE by similar amounts, so the gap stays about the
    same.
- **`under_normalized`** at epoch 9:
  - the train–dev gap is about 0 (−0.008 to +0.014);
  - dev CE is still falling 0.035–0.045 nats per epoch.
- **Rung 4's 20-epoch cell on `under_normalized`:**
  - dev CE at epoch 19 is 1.354 for no growth, 1.313 for static, and 1.266 for the scheduled
    graft;
  - the gap grows to +0.06 to +0.10;
  - the dev slope slows to about −0.01 nats per epoch.

**Configuration:**
- `experiments/kernel_demo.py`: training loop; lr 0.05 constant with Nesterov 0.9 (`:877-890`);
  weight decay 5e-4 (`:153`); augmentation (`:319-343`); seeds (`:637-734`); hosts (`:546-603`);
- `experiments/atlas_hosts.py`;
- `docs/prereg/fleet-c1.json` (batch 32, 10 epochs, 4,096 fit and 5,000 dev examples).

**The claims and the gates:**
- `docs/product/decisions/0057-controller-training-pathway.md`;
- `docs/product/vision.md`;
- the host-family proposal §1 (L1–L7 from the original HLD at
  `/mnt/data/archive/esper.old@8d69bec`), §2 (drift), §3 (evidence), §11 (option D sketch).

**Earlier Simic disagreements to respect:** `docs/product/spikes/2026-10-11-host-family/panel-review.md`.

**Cost bases** (published records):
- conservative, about 9.3 s per arm-seed per GPU;
- fitted, about 11 s fixed per unit plus 5.1 s per arm.

Both are for 10 epochs at 4,096 examples. Per-arm time scales roughly with the number of
optimizer steps.
