# Kernel demo — enhancement analysis (cold read of `experiments/`)

**Date:** 2026-08-10 · **Status:** **Tier 1 IMPLEMENTED** under owner-approved
spec rev 6.2 (2026-08-10) — see the Fan record section of the spec, and
`tests/unit/kernel_demo/test_arm_recording.py`. Verified additive:
`frozen_block_hash` is byte-identical to the pre-amendment value
(`4a82c72cb491b285…`) while `config_hash` moved, so the change requires a
re-`--certify` and nothing else. Tier 2 is registered in
`docs/superpowers/specs/2026-08-10-kernel-demo-exploratory-register.md`.
Tier 3 remains a proposal for a successor experiment.
**Read:** `experiments/kernel_demo.py` (4,066 lines), `experiments/kernel_demo_plots.py` (432),
spec rev 6.1 (`docs/superpowers/specs/2026-08-09-kernel-demo-design.md`)
**Occasion:** implementation merged (PR #9), Operational Phases A–F not yet run
(`simic-7c42fc9c0b` READY). No store exists. **This is the last moment when
recording changes are free.**

## The axis that sorts every proposal

The demo makes one distinction load-bearing, so this analysis adopts it:

> **Does the change alter what gets *collected*, or only what gets *computed*
> from what was collected?**

That line is enforced in code, not by convention. `config_hash()`
(`kernel_demo.py:231`) hashes the source text of every `@semantic` object;
`run_collect` (`:3149-3152`) and `run_eval` (`:3463`) refuse on any mismatch;
`freeze_manifest` (`:2863-2871`) refuses on a dirty worktree or on
`HEAD != certified_rev`. So:

| Tier | What it is | When it is possible | Risk to the headline |
|---|---|---|---|
| **1** | Adds a **recorded field**. Nothing reads it. | **Only before `--selftest --certify`.** | None, if it touches no gate and no frozen field |
| **2** | Reads the store **offline**, after the fact | Forever | None |
| **3** | Changes the experiment (menu, slots, hosts) | Not this experiment | Would void five SME panels' sign-off |

Tier 1 is the whole urgency of this document. Tier 3 items are named honestly
as **Experiment 2**, not as enhancements — the spec says of its scope pins
"agreed, do not widen," and proposing menu growth or a second slot as an edit
to this demo would read as scope creep against a locked design.

---

## Tier 1 — land before `--certify`, or lose for this campaign

### 1.0 This is a spec amendment. Route it as one.

The spec enumerates the per-arm payload verbatim: *"per-arm `{name, init_seed,
status, R_val, R_test, curve}`, telemetry context."* Everything in 1.1–1.4 adds
fields to that list, so it changes a **locked** record schema — not an
implementation detail. Do not land it as a quiet widening of a signed-off
contract.

The mechanism already exists: **rev 6.1 was itself an owner-approved pre-data
amendment**, justified as "no store exists, so the change is statistically
free." Tier 1 is the same argument with a smaller blast radius. Propose it as
**rev 6.2 — pre-data, additive-only, touching no `FROZEN_FIELDS` entry, moving
no gate arithmetic and no verdict boolean** — and take owner sign-off before
`--certify`. A record-schema change to a locked spec is load-bearing, which is
exactly what stays outside standing autonomy.

### 1.1 Per-arm telemetry trajectory *(the highest-value item)*

**What the store will contain today.** `run_collection_episode` records
`ctx.telemetry[:fe]` (`:2377`) — the **pre-decision** history of the base run —
plus, per arm, the fields of `ArmResult` (`:1207-1221`): `r_val`, `r_test`,
`curve_val`, `curve_test`, `g_at_init`, `rms_ratio_blend_entry`, hashes,
`alpha_beta_log`.

**What is discarded.** `run_arm` builds a full `EpisodeCtx` and drives
`_run_span → train_one_epoch`, which appends a 20-dimensional `TelemetryRecord`
per epoch (`:1119-1133`). Those records exist in memory for every arm and are
thrown away when `run_arm` returns. `ArmResult` has no telemetry field.

**Be precise about the gap:** a post-decision trajectory *does* survive — as
`curve_val`, one scalar (val accuracy) per epoch. What is lost is the
**19 diagnostic dimensions**: grad-norm mean/variance per stage, activation
saturation, weight norms, per-class accuracy spread, confusion entropy —
measured *while the graft integrates*.

**Why it is the best item.** Every post-commit half of Simic needs exactly that
vector and cannot be studied without it:

- **Wrenn continued tenancy** and **Emrakul decay/lysis** decide about a host
  *that already carries a graft*. The mandatory-no-op invariant applies to
  continued-tenancy cases, and Simic today has **zero** empirical support for
  it. Deciding anything from a modified host requires the modified host's
  telemetry.
- **Nissa** observes the ablated host post-embodiment — this is the same
  vector, on the post-graft trajectory.
- **Divergence diagnosis**: a diverged arm currently reports `status` and a
  truncated accuracy curve. The 20-dim signature in the epochs *before* the
  NaN is what makes divergence predictable rather than merely counted — and
  that feeds 2.1 below.

**Cost, measured not guessed.** 475 bytes/record JSON-serialized
(non-decorative float precision); ≤ `horizon − fan_epoch` ≈ 30 records/arm;
~6 arms/fan → ~86 KB/fan → **~51 MB over 600 collection fans**, ~70 MB with the
eval grid and refans. `run_arm`'s own memory peak is unchanged — the records
already exist there.

**The real memory cost is in `Store.merge()`, not in `run_arm`.** `merge()`
decodes every record into Python objects before sorting, and it is called from
`run_preflight`, `run_train`, `run_eval` (twice), `run_report` and `run_replay`.
Measured: **1,922 bytes resident per decoded telemetry dict**, ×144,000 records
at collect+eval scale ≈ **277 MB resident** on top of everything else, every
time `merge()` runs. Affordable on this machine, but verify it at eval scale
before freeze rather than assuming. **Fallback if it bites:** move arm
telemetry to the same `fan_id`-keyed sidecar as 1.2, leaving the JSONL as the
index — at the cost of the single-store durability and torn-final-line
contract, which is why in-record is the default recommendation.

**Diff shape:** add `telemetry: list[dict] | None` to `ArmResult`; populate from
`ctx.telemetry` in `run_arm`. `arms=[dataclasses.asdict(a) …]` carries it
automatically. **No gate arithmetic and no verdict boolean moves** — gates read
only `r_val`/`r_test`/`status`/`rms_ratio_blend_entry` from arms. (`run_report`
additionally reads `g_at_init` and `curve_val`; both are untouched.)

> **Mandatory guard, not optional.** `fan_to_example` (`:1840-1852`) — the
> learner's only input constructor — must continue to read `rec.telemetry`
> (pre-decision) and never arm-level telemetry. Post-decision telemetry inside
> the training path is a time-travel channel that would silently invalidate the
> headline. Add a test asserting it, in the same commit that adds the field.

### 1.2 Trained Δ-module weights, in a sidecar

`run_arm` discards the trained seed module. Those weights are the **only
artifact in the whole campaign that is an actual generated structure** — i.e.
the literal training corpus for early Momir, and the substrate for "what did
the winning Δ converge to, and is it close to a known operator?"

Measured: 73,500 params across the four seeds = **294 KB/fan fp32** →
~180 MB collection, ~250 MB with eval. Write to a `fan_id`-keyed sidecar
directory (`runs/<store>/deltas/<fan_id>/<arm>.pt`), **never into the JSONL** —
the store's merge/sort/duplicate-detection path stays untouched.

### 1.3 Per-arm cost accounting

The demo's stated claim is "the counterfactual-fan **supervision economics**,"
and the store will have no denominator. Wall-clock exists only as an
episode-granularity `heartbeat` line in a worker log (`:3119-3122`).

Record per arm: wall seconds, and (GPU) peak allocated bytes. Same blindness
guard as 1.1 — this lives on `ArmResult`, not `TelemetryRecord`, so the
`--selftest` blindness grep (`:2154-2163`) still passes by construction, and
the learner must not read it.

This turns "a fan costs about 5× a no-op run" from a hallway estimate into the
input Simic's cost model and fleet sizing actually need
(`docs/design/programme/cost-model.md`).

### 1.4 End-of-run influence measurement

`rms_ratio_blend_entry` samples `RMS(Δ)/RMS(h)` once, at the first BLENDING
step (`:842-844`). Also capture `g` and the RMS ratio **at the horizon**. Two
floats per arm; answers "does an embodied graft's influence grow, hold, or
decay under joint training?" — which is the empirical question underneath
Emrakul's decay schedule and Wrenn's influence-raising warrant.

### 1.5 A pre-data exploratory register

`run_eval` is one-shot and enforces it (`:3431-3435`); every Tier-2 study below
is, by construction, post-hoc unless it is declared **now**. Commit a short
`docs/superpowers/specs/2026-08-10-kernel-demo-exploratory-register.md` listing
the offline studies, each marked exploratory, before `--certify`. Cost: one
file. Effect: the follow-up studies become legitimate secondary analysis rather
than fishing, and the headline stays clean.

**Sequencing.** 1.1–1.4 move `config_hash`; none move `frozen_block_hash` (they
touch no `FROZEN_FIELDS` entry). Land **1.1–1.5 together, in one commit, and
include the register file** — `freeze_manifest` refuses when
`HEAD != certified["git_rev"]` (`:2870`), so a register committed *after*
`--certify` makes freeze refuse and burns a re-certify cycle. Order: owner
signs rev 6.2 → one commit → `--selftest --certify` → `--preflight --freeze`.
Bumping `SCHEMA_VERSION` to 2 is free and honest — there is no store to decode.

---

## Tier 2 — free forever; the studies the store will already support

### 2.1 Tail-risk predictability and the price of a veto
Simic's lexicographic admission invariant says the tail-risk veto is
adjudicated **before** any utility comparison and that "the assurance class
owns the veto operating point." There is currently no evidence that such an
operating point is even findable. From the store: predict `status == "diverged"`
from pre-decision telemetry + seed identity; report the ROC, and at each
operating point the **foregone benefit** (mean `R_best − R_noop` on the fans the
veto would have blocked). That is Isperia's veto priced empirically, from data
you are about to collect anyway.

*Power caveat, stated in advance:* this study's resolution is set by the
realized divergence rate, which is unknown pre-data. Report the observed rate
beside the ROC so a thin positive class reads as **"underpowered below X"**,
never as "tail risk is unpredictable."

### 2.2 Retrieval as a policy conditioner (the MVP's L0 rung)
`simic-03de2210b6` puts the MVP at "retrieval over the fixed five." Test it
offline: k-NN over normalized telemetry into the fan store, conditioning the
WHICH head on retrieved precedent, scored against the same tune split. Answers
whether ancestry retrieval earns its complexity before Urborg's retrieval path
is designed around the assumption that it does.

### 2.3 Provider-blind adjudication costs nothing (or does)
Dual provider blindness is "by construction — fields absent, not ignored."
Construct the blinded view offline by dropping `name` from the arm dicts, and
train a judge on (telemetry, arm curve) → `R` with and without seed identity.
The accuracy delta is the empirical price of blinding — a Leyline contract
decision currently made on principle alone.

### 2.4 Horizon truncation — how short can a QA branch be?
Already fully enabled by `curve_val` alone, no Tier-1 change needed. Branch QA
is Jin-Gitaxias's dominant cost in Simic. Measure rank correlation between
`R` at the horizon and `R` truncated at epoch `t`, per pathology. If arms are
correctly ranked at half the horizon, the fan cost halves.

### 2.5 Fan-width economics
Rank quality as a function of arms actually run (subsample K of 4 + no-op).
Cheap here, and the direct precursor to the Experiment-2 question below.

---

## Tier 3 — this is Experiment 2, not an enhancement

Each of these touches `SEED_NAMES`/`DESIGNED_WINNER` (`:634`, `:543`), gate 4's
dominance threshold, the money chart's 4-row structure (`:1990`), or the β
calibration. Propose them as a **successor experiment with this store as its
baseline**.

**3.1 Menu scaling — the load-bearing one.** The demo's headline claim is the
inversion of the sparse-bandit regime: "full counterfactual labels at every
measured decision point." That inversion holds *only while the action space is
enumerable*. Simic's is generative and therefore is not. Experiment 2 should
measure the **decay curve**: with a menu of N ≈ 16 parameterized variants and K
arms actually run per decision, how does policy quality fall as K/N falls? The
answer determines whether Simic needs a learned value model (predict `R`
without running the arm), and how good it must be. This is the highest-
information follow-up available, and 2.5 is its pilot.

**3.2 Sequential grafts.** One decision on a virgin host is not a lifecycle.
Does a policy trained on virgin-host fans transfer to an already-grafted host?
Directly derisks non-stationarity in the Simic loop, and needs 1.1's per-arm
telemetry as its input — another reason 1.1 is Tier 1.

**3.3 A retirement arm.** Nothing in the demo ever removes anything. An
"un-graft at a late epoch" arm gives Emrakul and the continued-tenancy no-op
their first measurement.

**3.4 One held-out host family, at eval only, reported as context.** The
cheapest external-validity number available. Must be framed as a separate
post-hoc study — the scope pins forbid it inside the frozen battery.

---

## What I would *not* change

The determinism contract, the twin/null-seed integrity arms, the diverged-arm
0.10 convention and its recorded rationale, the val/test unit wall, the
episode-level permutation null (rev 6.1), and the refusal-heavy store are the
strongest parts of this design. The `_as_float` / `require_number` discipline
in both files — loud on `None`, never a silent default — is the esper-lite scar
correctly healed. None of the above should be traded for any enhancement here.

## Bottom line

Take owner sign-off on **rev 6.2** and land **1.1–1.5 in one commit before
`--certify`** (~70 MB of telemetry, ~250 MB of weights, four small fields, one
register file, one guard test). Everything in Tier 2 then follows for free
after the headline, with no further spec motion. Tier 3 is the next
experiment, and 3.1 is the one that decides whether Simic's supervision model
survives contact with a generative action space.
