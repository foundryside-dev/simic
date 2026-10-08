# PDR-0046 — Round 2: a pre-registered positive control on `under_normalized`, and the graft study frozen before it is read

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant. Run authorization: new experiments, each
recorded as a PDR with a pre-committed reading. The owner directed on
2026-10-08: "proceed autonomously with fable reviews".
Related: ADR-0018, PDR-0045 (round 1 reading), `simic-f73351380d`,
`simic-6cb47b3a06` (tooling hardening),
plans [`positive-control-v1`](../../prereg/positive-control-v1.json) and
[`graft-capture-v1`](../../prereg/graft-capture-v1.json)

## Context

Screen v1 showed that the paired instrument resolves, but the graft earned
nothing, and the `mild` host showed no measurable benefit from extra
structure. Before asking whether a graft repairs a deficit, the bounded
ladder needs a configuration where *some* added structure measurably helps.

The kernel demo already ships Esper-style crippled hosts, each paired with a
designed repair seed. An exploratory sweep covered all four (K = 4), with two
seeds each (5001–5002), at the screen-v1 scale:

| Host + seed | Static − no growth (late dev CE) | Added parameters |
|---|---|---|
| `under_normalized` + `norm` | −0.188, −0.177 | 129 |
| `channel_starved` + `conv_heavy` | −0.031, −0.060 | ~60,000 |
| `mild` + `conv_light` | −0.086, +0.071 | 8,897 |
| `no_spatial_mix` + `attn` | +0.102, −0.002 | 4,337 |

Only `under_normalized`/`norm` cleared the floor on both seeds. It is a
structural repair (normalisation), not added capacity. It is also a
best-of-4 selection, so its probe effect is optimistic and is not used for
sizing.

## The call

**Two plans, frozen together, before either study is analysed:**

1. **`positive-control-v1`** (rung 2). Design:
   - 48 units, seeds 2001–2048.
   - One co-primary: static − no growth, as a 95% paired t interval.
   - Floor δ_pc = 0.10, which is 2 × the rung-3 floor, leaving the graft study
     room.
   - Reading rule `positive-control-v1`, detection-first: passes, static
     worse, imprecise, or no effect.

   The scheduled arm trains because the runner always trains all three arms,
   but it is **sealed**: no contrast, no report field, nothing read. If the
   control fails, the declared K of 4 is exhausted and the bounded line
   stops at rung 2. That stop is a result.
2. **`graft-capture-v1`** (rung 3). Design:
   - 48 fresh units, seeds 3001–3048.
   - Every positive-control seed and every exploratory seed is excluded.
   - The screen-v1 contrasts and reading rule, with δ = 0.05.
   - It launches **only if** the positive control reads `control_passes`.

   It is committed now so that nothing in it can depend on the positive
   control's numbers.

**Sizing.** Both studies use a spread of 0.115, the 95% upper confidence
limit on screen v1's static − no growth spread. At n = 48:
- the control needs a true benefit of about 0.147 nats for an 80% chance to
  pass;
- the graft needs about 0.103 nats over no growth for an 80% chance of a
  progress reading.

**Budget:** each study is about 5 CPU-hours on 8 workers, 40–45 minutes
of wall time.

**Machinery.** Both run under the hardened screen tool (`simic-6cb47b3a06`):
- the analysis module is hash-pinned at launch;
- a dirty tree is refused at analysis;
- descriptive contrasts get no verdicts;
- undeclared arms are sealed out of the report;
- plan validation includes exact arm order;
- calibration on fit data is verified, not asserted.

## Disclosures

- δ_pc was set after the exploratory probe was seen. The higher floor makes
  the control harder to pass, which is the conservative direction for the
  decision it gates.
- The exploratory sweep computed graft numbers on this configuration:
  scheduled − no growth was −0.060 and −0.105. Those seeds are excluded and
  the numbers are not used for sizing.
- An owner prior from Esper is that an `attn` + `norm` two-seed combination
  gave large gains at about 1.01× parameter cost, measured with compromised
  telemetry. It did not influence this choice: `norm` was chosen by the
  probe, not the prior. It is banked for a later multi-slot rung.

## Reversal trigger

Any change to either plan after its launch is an amendment, recorded in the
plan's `deviations`. The analysis refuses a changed plan or a changed
analysis module. If the positive control fails, `graft-capture-v1` is not
launched, and this record is superseded by the rung-2 result.

## Pre-launch review amendments (2026-10-08, before any confirmatory unit ran)

An independent statistical review of both plans returned **GO with
amendments** for the positive control. It returned **NO-GO as written** for
the graft study. All the amendments landed in one commit before either study
launched.

**Changes to the graft study:**
- **F1 — new reading rule `graft-capture-v1`.** The v1 rule ranked "static
  wins" first. With static buying ~0.15 nats, it would read a graft that
  captures half the repair the same as one that captures none: at the
  probe's point estimate, `reopen_static_wins` with probability 1.0. The new
  rule names **`partial_capture`** (static beats the graft *and* the graft
  beats no growth). In simulation it reads partial capture at a capture of
  0.5 with probability ≥ 0.97, and static-wins at a capture of 0 with
  probability 0.99.
- **F2 — the sizing is now a table of reading probabilities by capture
  fraction.** The earlier 0.103 figure covered one contrast of a
  conjunction.
- **F3 — static − no growth is added as a descriptive contrast** on the
  graft study's own seeds.

**Changes to the positive control:**
- **F4 — a new `control_fails_below_floor` reading.** It covers a detected
  deficit smaller than δ_pc. It does not launch the graft study and does not
  stop the line; a new PDR decides. Only `control_fails_no_effect` exhausts
  K.
- **F5 — a pass-probability sensitivity table over spread and benefit.**
  Every reading reports the realised sd and the effects needed.
- **F6 — the scheduled arm is sealed in the process.** The runner's stdout,
  which prints every arm, goes to a `.sealed` file. The plan text no longer
  claims more than the code does.
- **F7 — the graft plan's hash is pinned** in the positive control's launch
  record (`linked_plan_sha256`).

**Changes to both:**
- **F8 — per-epoch arm means are reported**, and the static-wins text no
  longer equates a ten-epoch head start with repair quality.
- **F9, F10 — disclosure and predictions.** The plans disclose that the
  positive-control rule code postdates the sweep, and each records an
  expected reading before launch: control passes; graft reads
  `partial_capture`.

The screen-v1 rule (`bounded-screen-v1`) is unchanged, as the historical
record of round 1.
