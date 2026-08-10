# 12 — Adversarial Contract-Suite Audit of the Simic-Shaped Decomposition

**Document under audit:** `11-simic-shaped-decomposition.md`
**Audited against:** the `axiom-contract-engineering` 13-entry failure-mode catalogue
**Auditor:** `contract-reviewer` (producer-side sibling: `contract-suite-architect`, which authored the document)
**Date:** 2026-08-10

---

## 0. Pin — read this before comparing line numbers

**The document was being actively rewritten during this audit.** It grew
1,415 → 1,760 → 1,856 lines across three observations (mtimes 07:40, 07:48, 07:49).
§A.2 — the socket sections, one of the four areas I was asked to audit — did not
exist in the version I first read.

I therefore pinned the target and audited the pin:

| | |
|---|---|
| **Pin** | `/tmp/audit-pin.md` |
| **sha256** | `659bb8bc2dfe651d5ff2c4134f592e805acce47d31bfaa3e6502ecf888ccdc09` |
| **Lines** | 1,856 |
| **mtime** | 2026-08-10 07:49:49 +1000 |

**All document-side line citations below are against that pin.** Source-side
citations (`experiments/kernel_demo.py`, `experiments/kernel_demo_plots.py`,
`docs/design/*`, git history, filigree) are stable and were verified at HEAD
(`aa86388`).

Two consequences the requester must hold:

1. **Several findings were overtaken by the designer mid-audit.** §E.7 and §C.10's
   manifest-consumer enumeration were both corrected between my first read and the
   pin. I report those as *confirmed-and-closed* rather than deleting them, because
   the closure is itself the evidence that the correction landed, and because one
   residual survives in each.
2. **A finding marked live here may have been fixed after 07:49:49.** Re-check
   against the current file before acting.

**Re-pin at hand-off.** I re-checked immediately before delivering. The file had moved
again — **1,905 lines**, sha256 `5bc4087bebc5afa79f5380b7c2dd4385f0dc228a2903fe9ac12b2d6f992bd484`
— but the diff against the pin is **additive in the regions that matter**. I
verified anchor by anchor:

| Finding | Anchor | Status at 1,905 lines |
|---|---|---|
| F-1 | `no provenance field to strip` | **Live**, both occurrences |
| F-2 | `mirrored :3397–3400` | **Live**, now at :1253 |
| F-3 | `envelope-shaped` (§A Ugin row) | **Live** |
| F-4 | the `:3425–3660` grep claim | **Live** |
| F-5 | `already built the artifact` | **Live** |
| F-9c | the 8-of-10 forbidden block | **Live** — a `05-leyline-contracts.md:102` citation was added after it, but the block itself is unchanged and still omits `suggested_envelope` and `free_form_designer_message` |

The substantive addition is a new **§D.9**, recording that the sidecar's review-fix
pass closed a third silent-default the analysis had not found (`_finite_points` /
`_gapped` preserving the original epoch index). That is a fair and well-evidenced
positive; I verified it in the source at plots :65–90 and it does not bear on any
finding below.

**All nine of those findings are live against the 1,905-line version**, and the
post-pin revisions produced **two further findings** — F-10 and F-11 — which are
filed against material that did not exist when I pinned. Eleven total.

---

## 1. Method and coverage

I read the document in full at 1,415 lines and re-read the changed and new sections
against the pin. I did **not** read `02-subsystem-catalog.md` or re-derive it — per
the briefing it is treated as a completed input, and its correctness is an
information gap, not an audit target.

Source verification was targeted, not linear, navigating by the document's own
citations. Regions read directly in `experiments/kernel_demo.py`:
`:186–232` (`FROZEN_FIELDS`, `frozen_block_hash`, `config_hash`), `:340–440`
(`TelemetryRecord`, `check_finite`, `record_to_vector`), `:634–760` (`SeedDelta`,
subclasses, `build_seed`, `tau_init`, `split_decay_groups`), `:896–915`
(`FORBIDDEN_RELAXATIONS`), `:1708–1836` (`Policy`, `decide_live`,
`query_teacher_forced`, `_as_float`, `_telemetry_vector_from_dict`), `:2076–2084`
and `:2150–2210` (selftest steps 1, 6, 7), `:2305–2318` (`draw_schedule`),
`:2740–2775` (gates 7–8), `:2840–2915` (`freeze_manifest`), `:2925–3029`
(`run_preflight`), `:3310–3372` (`verdict`, `run_train`), `:3385–3424`
(`_query_dicts`, `_pi_argmax`, `_test_argmax`), `:3425–3660` (`run_eval`),
`:3826–3875` (`run_report`), `:3940–3976` (`run_replay`), `:4035–4060` (exit codes).
`experiments/kernel_demo_plots.py` was read in full at HEAD and at `2b48431`.
`docs/design/02-constitution.md` Appendix B and §5.2–5.4 and
`docs/design/05-leyline-contracts.md` §9.1–9.4 were read in full.

**Catalogue sweep.** All 13 entries were swept.

*Entries producing findings:* #1 (silent defaults — F-2, F-8), #2 (tolerant readers —
F-8), #6 (covert channels — F-9c, the dropped `free_form_designer_message`),
#9 (blinding by ignoring — F-1, which is the *inverse* error: blinding applied to the
wrong record), #10 (dual sources of truth — F-1, F-2, F-3, F-5, F-9),
#11 (unversioned policy — F-3), #12 (silent definition edits — F-7),
#13 (vacuous contract tests — F-4, F-6).

*Entries swept and closed without a finding,* with the closure evidence stated:
#3 (fail-open version gates — `decode_record` :1567–1573 is an equality gate that
raises on any inequality, and the document reports it correctly, including the
governing policy in the error text); #4 (version-in-name-only — `SCHEMA_VERSION = 1`
with no semantic change yet shipped, so the failure mode has no instance);
#5 (compat shims — the one shim in the demo, gate 7's `remedy="report-only"`, is
found and correctly diagnosed by the document at §C.7); #7 (resolver preferences —
the tie-break is pinned to the lowest `SEED_NAMES` index and the document reports the
duplication; the *preference* itself is not smuggled); #8 (hidden resolver state —
`decide_live` and `_query_dicts` are both pure over their arguments, save/restore
`policy.training`, and read no clock, RNG or env; I checked specifically).

*Not assessable:* see §7.

A note on what this audit is not. The document is an advisory paper decomposition
whose stated purpose is to surface contract shapes for Phase A. I have **not** filed
"this would be a big refactor" in any form, per the briefing. Severity below is
strictly **blast radius on Phase A**: how expensive is it to unwind if this shape,
or this claim, is adopted into Leyline.

---

## 2. Findings

---

### FINDING 1: §C.1/§F.7 conflate `TelemetryEnvelope` with the blinded *view*, and prescribe stripping fields the HLD mandates on the envelope

**Severity:** critical
**Catalogue:** #9 (blinding by ignoring — here the inverse error: blinding applied at
the wrong record), #10 (dual sources of truth — two incompatible definitions of one
record class), #1 (absence encoding)
**Document location (pin):** :1189 (§D.4), :1596–1610 (§F.7), :540–548 (§C.1 table)

**Evidence.**

§F.7 (pin :1602–1610) states:

> *Evidence:* `TelemetryRecord` (:358–369) has no provenance field to strip; the
> blind view is the only view (C.1, D.4). This is INV-37 satisfied, and it is the
> property the whole `TelemetryEnvelope` design should inherit.
>
> *Phase-A action:* **keep layer 1 exactly as the demo has it.**

§C.1 (pin :526–531) calls this "the headline positive of the whole document":

> Blinding is **by field absence, not by ignoring**. There is no seed name, arm name,
> pathology id, episode seed, or provenance field anywhere in the dataclass. The
> identity is *not present to be ignored*.

That is a correct and well-evidenced reading of `TelemetryRecord` (`kernel_demo.py`
:357–369, verified — twelve fields, all metrics). **It is the wrong record to
generalise from.** The HLD's `TelemetryEnvelope` — the exact record §C.1 says
`TelemetryRecord` should become — mandates the opposite
(`docs/design/05-leyline-contracts.md` :48–69, read in full):

```text
TelemetryEnvelope
    observation_id      host_state_id      snapshot_id
    region_id           ablated_context    lifecycle_context
    budget_context      temporal_context   validity_mask
    provenance          normalization_manifest    schema_version
```

`provenance` is a field. So are `region_id`, `lifecycle_context` and
`ablated_context`. Three independent authorities confirm this is deliberate:

1. **`05-leyline-contracts.md` :46** — the envelope is "published independently to
   Ugin, Aurelia, Momir, Urborg and Tamiyo **according to access policy**."
   Jin-Gitaxias and Isperia — the two authorities INV-37 blinds — are *not on that
   list*.
2. **`05-leyline-contracts.md` :75** — "Independent publications and **permitted
   per-consumer projections** of one observation share `observation_id` but carry
   distinct `telemetry_id`s." The blinding mechanism is a projection, not envelope
   emptiness.
3. **`02-constitution.md` :272–275** (Appendix B) — "NISSA … **May normalise and
   attach provenance.**" Nissa is *mandated* to attach what §F.7 says the envelope
   must not carry.

And INV-37, as the document itself quotes it (pin :528), constrains **views**:
"source fields are absent from QA and adjudication **views** rather than merely
ignored." A view is a projection of something. §F.7 removes the something.

**Consumption trace.** Phase A implements Leyline contracts first
(`programme/phases.md`), and §F ranks this as action 7 with an explicit *Phase-A
action*. An implementer following it writes `TelemetryEnvelope` with no provenance
and no identity. Three failures follow immediately:

- **INV-08 breaks.** `05-leyline-contracts.md` :73: "The same `observation_id` must
  be referenced by Aurelia's intent, Momir's conditioning input, and the Tolaria
  snapshot later used for counterfactual evaluation. A mismatch fails closed." With
  no identity on the envelope there is nothing to reconcile and the fail-closed
  check cannot be written.
- **INV-13 (bootstrap provenance) breaks**, for the same reason — §A of the document
  itself lists INV-13 as something the demo cannot test, so it is not a gap the
  document is otherwise blind to.
- **The blinded view is never designed at all.** §F.7 asks for "layer 2 (an
  allowlist projection …, so a new field is excluded by default)". A projection over
  a record that already carries nothing excludes nothing. Layer 2 as specified is
  vacuous *given* layer 1 as specified. The two halves of the same recommendation
  contradict each other.

The document is closest to catching this in its own §C.1 table (pin :544), which
asks to **add** `observation_id`, `host_state_id`, `snapshot_id` to the envelope —
identity fields, correctly motivated by INV-08 — four lines after asserting that
"the identity is *not present to be ignored*" is the property to preserve. The
contradiction is internal and visible on one screen.

**The correct reading, and it costs the document nothing.** The demo's
`TelemetryRecord` is not the precursor of `TelemetryEnvelope`. It is the precursor
of the **blinded projection** — and it is an excellent one, precisely because the
demo's single consumer set made the projection and the envelope accidentally
identical. That is a genuine and reusable finding; it is simply attached to the
wrong record.

**Closes:** `blinding-by-construction.md` (layer separation: envelope, per-consumer
projection, canary), `contract-first-boundaries.md` (one record class, one
authority).

**Remediation:** Split the recommendation. `TelemetryEnvelope` carries the HLD's
fields including `provenance` and `observation_id`, authored by Nissa; a separate
`BlindedTelemetryView` type is constructed by allowlist projection with the source
fields *absent from the projected type*, and it is that type — not the envelope —
that Jin-Gitaxias and Isperia consume. §F.7's "keep layer 1 exactly as the demo has
it" then becomes true of the view and false of the envelope, which is the actual
lesson.

---

### FINDING 2: `_query_dicts`'s non-finite guard admits the exact case it was written to catch — a live defect in shipped code, certified as closed by §D.8

**Severity:** critical
**Catalogue:** #1 (silent defaults), #10 (dual sources of truth)
**Document location (pin):** :1251 (§D.8 table row), and by inheritance §F.10's
carry-forward list
**Source location:** `experiments/kernel_demo.py` :3397–3400

> **Elevated from high to critical, and reclassified.** I originally filed this as a
> documentation defect — a guard *certified* as equivalent when it is weaker — and
> explicitly declined to claim the case occurs. **The coordinator executed it and it
> does.** It is therefore a defect in shipped code that the document certifies as a
> satisfaction, which is strictly worse than either alone. Coordinator's run:
>
> ```
> decide_live guard   (logits):        passes = False   ← correctly rejects
> _query_dicts guard  (post-sigmoid):  passes = True    ← admits it
> p = 0.0  ->  p > 0.5 = False         ← reads as restraint, lift exactly 0
> ```
>
> This finding goes to the author as a **code** finding. Everything else in this
> audit is a document finding.

**Evidence.** §D.8 is the document's "INV-38 — failure visibility; no silent
fallback" section, a table of eight mechanisms presented as *satisfactions*. Row
five (pin :1251):

> | Non-finite logits raise rather than reading as restraint | `:1774–1777`, **mirrored** `:3397–3400` |

They are not mirrored. `decide_live` (`kernel_demo.py` :1774) checks the **logits**:

```python
if not (torch.isfinite(p_logit).all() and torch.isfinite(seed_logits).all()):
    raise RuntimeError("decide_live: policy produced non-finite logits")
```

`_query_dicts` (`kernel_demo.py` :3397), which is the function on every live path,
checks the **post-activation values**:

```python
p  = float(torch.sigmoid(p_logit[0]))      # :3393
pi = torch.softmax(seed_logits[0], dim=-1) # :3394
if not (math.isfinite(p) and bool(torch.isfinite(pi).all())):
    raise RuntimeError("_query_dicts: policy produced non-finite output")
```

`sigmoid(-inf) == 0.0` and `sigmoid(+inf) == 1.0`. **Both are finite.** A
`p_logit` of `±inf` with finite `seed_logits` passes `_query_dicts` unchallenged
and fails `decide_live`. The two guards are not the same guard.

**Consumption trace.** `_query_dicts` is called at :3562 and :3567 inside
`run_eval`'s comparator loop. Its `p` feeds `fire = p > 0.5` (:3572). A
`p_logit = -inf` yields `p = 0.0`, `fire = False`, `germination_epoch` stays `None`,
and `lift` is set to exactly `0.0` by :3587 (`# never-germinate = 0`). That is
verbatim the outcome the guard's own comment says must never happen — the comment at
:3398–3399 reads *"a non-finite checkpoint would silently read as restraint (lift
exactly 0) on every query. Loud, never that."* The deployed guard does not close the
case its comment describes; the untested one does.

**Which values escape, worked through both heads.** The hole is wider than my first
draft implied, and wider than the `-inf` case the coordinator executed:

| Input | What `_query_dicts` tests | Caught? | Silent behaviour if not |
|---|---|---|---|
| `p_logit = -inf` | `sigmoid(-inf) = 0.0`, finite | **No** | `p > 0.5` False → **lift exactly 0 on every episode** |
| `p_logit = +inf` | `sigmoid(+inf) = 1.0`, finite | **No** | `p > 0.5` True → **germinates in every episode**, at the window's first epoch |
| `p_logit = nan` | `sigmoid(nan) = nan` | Yes | — |
| `seed_logits` carries `-inf` | `softmax` maps it to `0.0`; all finite | **No** | that seed silently unselectable |
| `seed_logits` carries `+inf` | `softmax` → `nan` | Yes | — |

`nan` is caught in both heads; `±inf` is caught in neither, except where softmax
happens to manufacture a `nan`. `decide_live` catches all five, because it tests
*before* the activation rather than after it.

**Both silent directions are catastrophic and they are opposite** — a comparator that
never germinates and one that always does — and neither is distinguishable in the
record from a genuine policy decision, because `decisions` (:3588) stores the
post-sigmoid `p`, never the logit. My first draft named only the restraint direction;
the always-germinate direction is equally reachable and arguably worse, since it
would produce a *plausible* non-zero lift rather than a suspicious run of zeros.

**The document's role, which survives the code fix.** §D.8 lists this guard in a table
of *satisfactions*, on the strength of one word ("mirrored") that a two-line read
falsifies, and §F.10 then carries the D.8 mechanisms forward among "the things the
demo already proved … transplanted". So the defect propagates into Phase A as a
*pattern to copy*, with the finiteness check placed after the lossy transform rather
than before it. **That is the contract lesson and it is independent of the patch:**
a validity guard must sit on the representation it is guarding, not on a
value derived from it — the same rule §C.13 states for the wire and §C.1 states for
`check_finite`.

**This also strengthens the document's own §C.12/§E.2.** §C.12 (pin :1030) reports
that the two resolver twins "already differ structurally — `decide_live` owns the
window guard internally (:1763) while the deployed copy depends on the caller's
`lo <= e <= hi` at :3551." That is one divergence. There are **three**:

| # | `decide_live` (tested, zero production callers) | Inline twin (deployed) |
|---|---|---|
| 1 | Window guard internal, `:1763` | Caller's `lo <= e <= hi`, `:3551` — *reported* |
| 2 | Refuses non-finite **logits**, `:1774` | Refuses non-finite **post-activation**, `:3397` — *unreported* |
| 3 | Tie-break over raw logits: `(logits == logits.max()).nonzero()[0]`, `:1780` | Tie-break over softmax floats: `_pi_argmax`, `:3416–3420` — *unreported* |

Divergence 3 is narrower but real: `_pi_argmax` selects the lowest `SEED_NAMES` index
among entries exactly equal to `max(pi.values())` in Python-float space. Softmax is
monotone, so the *argmax* agrees; but two distinct logits can collapse to the same
float32 probability, creating a tie in `pi` that does not exist in `logits`. The
tie-break sets are therefore not provably identical, which is exactly what "keep the
two in lockstep" (:3568–3571) asks a human to guarantee by eye.

**Closes:** `silent-default-elimination.md` (fail-loud parsing; the guard must sit
before the lossy transform), `deterministic-resolution.md` (one resolver).

**Remediation:** Correct the §D.8 row to state that the deployed path checks a
strictly weaker condition, and move the row out of the satisfactions table. Add
divergences 2 and 3 to §C.12's structural-drift list — they make the document's own
recommendation 3 ("one resolver, versioned") substantially stronger, since the
manual-lockstep request has already failed twice more than reported.

---

### FINDING 3: §A's Ugin presence call rests on stated evidence that does not support it, and contradicts §A.2.3's own better account

**Severity:** high
**Catalogue:** #11 (unversioned policy — the misclassification is of a *policy*
record as an *envelope* record), #10 (two accounts of one call)
**Document location (pin):** :68 (§A table, Ugin row), :91–101 (correction 2),
:268–309 (§A.2.3)

This is one of the two upgrades I was asked to check specifically.

**Evidence.** The §A table (pin :68) justifies `partial` as:

> `FROZEN_FIELDS` (:188–223) plus `n_collect`/`horizon`/`window`/`fans_per_episode`
> are envelope-shaped: they grant and constrain without instructing.

I read `FROZEN_FIELDS` (`kernel_demo.py` :186–221 — the citation `:188–223` is itself
off by two at both ends). It has 35 entries. Classified against
`StrategicEnvelope`'s actual field list (`05-leyline-contracts.md` :14–39):

| Class | Fields | Envelope-shaped? |
|---|---|---|
| Training hyperparameters | `lr`, `momentum`, `wd`, `seed_lr`, `batch_size`, `policy_lr`, `policy_batch_size`, `policy_steps`, `warmup_frac` | **No** — these instruct, they do not grant |
| Blend/stage mechanics | `tau`, `tau_eps`, `lam`, `stage_k`, `stage_m`, `stage_f` | **No** — Wrenn/Elesh mechanics |
| Adjudication thresholds | `alpha_level`, `permutation_resamples`, `beta_which_frac`, `beta_now_div`, `gate1_…`–`gate6_…`, `diverged_r` | **No** — these are the *referenced policy record*. `StrategicEnvelope` carries `admissibility_policy_id`, an **id**, not the thresholds |
| Genuinely grant-shaped | `horizon`, `window`, `t_star`, `fans_per_episode`, `n_preflight`, `n_eval` | **Yes** — 6 of 35 |

So roughly six of thirty-five fields are envelope-shaped, and the largest single
group — the gate and verdict thresholds — is the one category `StrategicEnvelope`
deliberately does **not** inline. Calling the block "envelope-shaped" and saying it
"grants and constrains without instructing" is not supportable: nine of its fields
are learning rates and batch sizes, which instruct and nothing else.

**The verdict survives; the evidence does not.** §A.2.3 (pin :268–309), which did not
exist when the §A table was written, relocates the Ugin socket to `draw_schedule`
(:2307) plus the frozen `cfg.window` — and that account is sound. I verified
`draw_schedule` directly: uniform-without-replacement over an inclusive declared
window, seed-derived, label-separated. A declared window inside which timing is
chosen genuinely is grant-and-constrain. **Ugin-`partial` is defensible on §A.2.3's
grounds and not on §A's.** The document now carries two incompatible justifications
for one call, and a Phase-A reader who stops at the table gets the wrong one.

**Consumption trace.** The document's own §A "cannot test" column and §F ranking are
downstream of these calls. Worse, an implementer reading "FROZEN_FIELDS is
envelope-shaped" may model `StrategicEnvelope` as a flat frozen-constants block —
which would put adjudication thresholds inside the envelope, breaking the
`admissibility_policy_id` indirection that lets admission policy version
independently of resource grants. That is a wrong Leyline record shape, and it is
expensive to unwind after records exist.

**By contrast, the Elesh upgrade holds.** I checked it clause by clause against
`02-constitution.md` :282–285, read in full: "ELESH / Makes designs structurally
legal and canonical. / May reject malformed structure. / Must not judge task
utility." All three verified in source: `SeedDelta` (:638) fixes
`forward(h) = gain * f(h)` with `gain` born `zeros(())`; `build_seed` raises
`ValueError` on an unknown name (:729) — literally "may reject malformed structure";
`tau_init` (:735) canonicalises magnitude and judges nothing. The document's own
limiting language ("what is missing is the *step*, because nothing arrives
unconformed") is accurate and the "cannot test" column correctly carries the
deflation. **Elesh-`partial` is confirmed.**

**Closes:** `versioned-policy-parameters.md` (policy records are referenced by id,
not inlined into grants).

**Remediation:** Replace the §A table's Ugin evidence cell with §A.2.3's
(`draw_schedule` :2307 + frozen `cfg.window`), and delete the `FROZEN_FIELDS`
claim or restate it as "six of its thirty-five fields are grant-shaped; the
remainder are training config and adjudication policy, the latter belonging to
`admissibility_policy_id`, not to the envelope."

---

### FINDING 4: §E.1's load-bearing evidence sentence is false — the grep it reports as empty returns a hit, in the same function

**Severity:** medium
**Catalogue:** #13-adjacent (a claim stated as mechanically verified that mechanical
verification refutes)
**Document location (pin):** :1316–1319

This is the §E.1 item I was asked to adjudicate.

**Evidence.** §E.1 is billed as "the most instructive item in the document." Its
central empirical claim (pin :1316–1319):

> Nothing hashes the two prefixes and compares them — grep over :3425–3660 for
> `state_hash|host_init|host_hashes|TwinDivergence` returns **no comparison at all,
> only two empty-string literals.**

Run against HEAD:

```
$ awk 'NR>=3425 && NR<=3660' experiments/kernel_demo.py \
    | grep -n "state_hash\|host_init\|host_hashes\|TwinDivergence"
3454:  host_init_hash="",
3606:  host_init_hash="",
3637:  except TwinDivergence as td
```

Three hits, not two. `TwinDivergence` **is** present in the cited range, at :3637.

**Is the argument sound anyway?** Yes — and I want to be precise, because I was
invited to call it a narrative imposed on a long function and it is not quite that
either.

*The mechanism claim is correct and I verified every link independently:*

- `run_eval`'s comparator records are written `kind="policy_run"` with
  `fan_epoch=None` (:3592, :3597 — verified).
- `run_replay` refuses exactly that: `if rec.kind != "fan" or rec.fan_epoch is None:
  raise` (:3957–3958 — verified). The comparator records fail the guard twice over,
  as the document says.
- The baseline is an independently constructed episode (`noop_ctx = make_episode(...)`,
  :3512) and each comparator builds another (:3542); `lift = r_test - r_noop_test`
  (:3587) differences two separately executed episodes.
- `host_init_hash=""` at :3606 means no prefix anchor is recorded.

*The framing is decoration.* "Four authorities, one function" and the
authority-collapse reading do no work the mechanism claim does not already do. The
defect is: **two independently executed episodes are differenced with no recorded
anchor binding their common prefix, and the resulting records are structurally
excluded from the one tool that would check.** That is a contract finding, complete,
and it stands whether or not `run_eval` is described as collapsing four authorities.
The document's own §E.1 precision note (preserved from the coordinator) and its
honest severity framing ("an unverified assumption, not a known error") are the
strongest parts of the section.

So: not a narrative imposed on an ordinary long function — there is a real, specific,
verified defect underneath. But the authority-collapse layer is presentation, and the
sentence carrying the section's empirical weight is wrong.

**Why :3637 matters rather than being a nitpick.** The hit is `except TwinDivergence`
guarding the eval-*grid* path (`run_collection_episode` at :3624). That is exactly
the distinction the document's own precision note draws — grid fans are replayable,
comparator records are not. The grep result does not undercut the finding; it
*is* the finding, misreported as an absence. A reader who reruns the grep to check
the document will find the claim false and may discard the section wholesale.

**Closes:** `contract-testing.md` (a stated mechanical check must reproduce).

**Remediation:** Restate as: "grep over :3425–3660 returns two `host_init_hash=""`
literals and one `TwinDivergence` handler at :3637 — and that handler guards the
eval *grid* path, not the comparator path. No hash comparison exists on the
comparator path at all."

---

### FINDING 5: §A.2.3 tells a downstream reader that filigree `simic-76fc6e6618` is already built, when the artifact it points at is a different artifact in a different role

**Severity:** medium
**Catalogue:** #10 (one requirement, two referents)
**Document location (pin):** :282–309, with an explicit relay instruction at :309

**Evidence.** I retrieved the issue via `mcp__filigree__issue_get`. The document's
verbatim quote is accurate, as are P1 / `hld-review` / `wave:3-narset`. The issue
asks that the **Ugin stub** — the budget allocator — vary, so that "Aurelia learns
envelope-conditional behaviour from the start."

§A.2.3 then states (pin :289–291):

> `draw_schedule` **is** a randomised allocator within declared bounds on a seed.
> **The demo has already built the artifact the issue is requesting**, and built it
> deterministically.

`draw_schedule` (`kernel_demo.py` :2307) returns two **fan epochs** — the epochs at
which the harness takes counterfactual branches. I traced all three call sites:
:2340 (`run_collection_episode`), :2954 (preflight refans), :3619 (the eval grid).
**None of them is the actor.** `Policy.embed` is `nn.Linear(TELEMETRY_DIM, d)`
(:1716), so the actor's entire input is the 20-float telemetry vector; `draw_schedule`
output never reaches it.

So `draw_schedule` shares the issue's *sampling pattern* (uniform within declared
bounds on a seed) but occupies a different role: it schedules the experimenter's
observation points, it does not grant an actor a budget the actor can read. The
issue's requirement is not satisfied by it in any degree.

**Consumption trace.** §A.2.3 :309 says "Worth relaying to whoever picks up
simic-76fc6e6618." A relay carrying "the demo has already built the artifact the
issue is requesting" tells a P1 owner that a build step is done. It is not done, and
the document's *own next paragraph* proves it is not — "There is no envelope input —
not a constant one, none" (pin :300–301), which I verified.

**The rest of §A.2.3 is excellent and I want that on the record.** The observation
that the issue's remedy is incomplete — that varying the envelope is useless unless
the actor has an input field to read it in, and that the demo proves this because
`TELEMETRY_DIM = 20` admits no such feature — is a genuine, well-evidenced
contribution that goes beyond the issue. It is worth relaying. The overstatement in
front of it is what needs removing.

**Provenance of the error, recorded so the fix is routed correctly.** The coordinator
has since taken ownership: the "already built the artifact `simic-76fc6e6618` asks
for" framing originated in the briefing given to the architect, not in the architect's
own reading, and it was carried forward as instructed. **This is not an architect
error.** It is recorded here because a finding that misattributes its own cause sends
the correction to the wrong place — and because a briefing-level over-read that
survives into a deliverable is the more instructive version of the failure.

**Closes:** `contract-first-boundaries.md` (same shape, different authority ≠ same
contract).

**Remediation:** Replace "has already built the artifact the issue is requesting"
with "has already built the *sampling mechanism* the issue describes, in a different
role — `draw_schedule` allocates the harness's observation points, not an actor's
budget, and its output reaches no policy input. The issue's requirement is
unsatisfied; what the demo contributes is the second half of the remedy."

---

### FINDING 6: §C.3's second production site for a partial `arms` payload is a selftest fixture written to a temp store, and its key set is misdescribed

**Severity:** medium
**Catalogue:** #13 (test artifact cited as production evidence)
**Document location (pin):** :655

**Evidence.** §C.3 states (pin :653–655) that two incompatible shapes are written
into `FanRecord.arms`:

> - full `dataclasses.asdict(ArmResult)` — 12 keys (:2376, :2492)
> - hand-built partials — 4 keys, `{name, status, r_val, r_test}` (**:2188**, :3608)

Line :2188 reads:

```python
arms=[{"name": "noop", "status": "ok", "r_val": 0.4, "curve_val": [0.1, float("nan")]}],
```

Two errors. The key set is `{name, status, r_val, curve_val}` — it contains
`curve_val`, not `r_test`. And it sits inside `run_selftest`'s `store_checks`
closure (`:2169–2192`), constructing a `kind="fan"`, `seed_namespace="dev"` record
that is round-tripped through `encode_record`/`decode_record` and written to a
`tempfile.TemporaryDirectory()` (:2209). Its purpose is to verify that a non-finite
value round-trips as `null` (:2196–2198). It never enters a real store.

**Consumption trace.** The substantive finding — that `arms` is
`list[dict[str, object]]` (:1451) and admits shapes no schema check enforces — is
**correct and important**, and :3608 alone establishes it (verified: four keys,
`{name, status, r_val, r_test}`, written by `run_eval`'s comparator loop into a real
store). Citing a test fixture beside a production write inflates the count of
production divergence sites from one to two, and the misquoted key set would send a
reader to :2188 expecting `r_test` and finding `curve_val`. Since §F.1 ranks payload
typing as the number-one Phase-A action and cites this line, the evidence should be
exact.

There is also a real, unremarked implication in the fixture's favour: `:2188` is
evidence that the *demo's own test suite* constructs a `kind="fan"` record with a
partial arm and the constructor accepts it — which is a sharper demonstration of
§E.8's "the kind/payload correspondence is convention, not contract" than anything
§E.8 currently cites.

**Closes:** `contract-testing.md`.

**Remediation:** Cite `:3608` as the production divergence and re-cite `:2188` under
§E.8 as "the sole constructor accepts a partial `arms` payload on a `kind="fan"`
record — demonstrated by the demo's own selftest fixture at :2188, keys
`{name, status, r_val, curve_val}`."

---

### FINDING 7: §C.7's authority argument quotes Jin-Gitaxias's Appendix B clause up to, and stopping at, the line that constrains it

**Severity:** low *(downgraded from medium — the underlying question has since been
ruled, in the document's favour)*
**Catalogue:** #12-adjacent (a definition cited in part where the omitted part governs)
**Document location (pin):** :784–789

> **RULED — the gates are correctly placed; §C.7's reading is upheld.** I raised this
> as an open question for the coordinator, who holds the domain semantics, and it has
> been decided against my concern. The ruling: `02-constitution.md` :49 gives
> Jin-Gitaxias "Dynamic QA, regression, runtime conformance and evidence
> certification" with the anti-pattern "**The admission judge**" — not "any pass/fail
> judgement" — and :83 makes the intended violation concrete ("'Jin-Gitaxias issued
> the admission token' is audibly a Phyrexian hand on a governance lever"). The
> prohibition is on **adjudicating the admission of a candidate**. Gates 1–8 are
> instrument-validity gates asking whether the harness can detect anything at all
> before data is collected; Isperia's adjudication is the separate five-boolean
> `verdict()` at :3313. **No authority finding.** Noted caveat, worth carrying: gate 4
> (dominance) is the closest call, since it observes candidates — but it asks whether
> the *menu* is degenerate, which is experimental-design QA rather than a ruling on a
> candidate.
>
> **What survives is only the quotation hygiene**, and its value is now different: not
> "a reader needs the clause to adjudicate" but "a reader should not have to
> re-litigate a settled question." Hence low.

**Evidence.** §C.7 argues that gate batteries are legitimately Jin-Gitaxias
territory, and grounds it (pin :785–787):

> that is runtime conformance and evidence certification, his by right ("Tests
> artefacts and certifies evidence. May report defects and uncertainty").

`02-constitution.md` :292–295, read in full, is three lines:

```text
JIN-GITAXIAS
Tests artefacts and certifies evidence.
May report defects and uncertainty.
Must not issue a verdict.
```

The quotation ends exactly where the constraining clause begins, with no ellipsis and
no acknowledgement that a third line exists. Every other Appendix B quotation in the
document that I checked — Elesh (pin :89), Wrenn (§C.6), Tamiyo (§E.7) — includes the
"Must not" clause, so the omission is anomalous within the document's own practice.

**Consumption trace, as revised by the ruling.** The argument **does** survive the
full quote — "verdict" narrows to *a verdict on a candidate*, exactly as the document
read it, and INV-18's own wording ("Jin-Gitaxias cannot issue admission or maintenance
warrants") supports the narrowing. The document graded itself "Moderate" and called
the reading "arguable"; it was in fact right, and can now say so at High. §F.6's
carrying `remedy` forward into `QualityReport` stands unaffected.

The residual cost is small but real: the next reader of §C.7 meets a truncated quote
and an author-flagged "arguable", and has no way to know the question has been
settled. That is re-litigation waiting to happen in a document explicitly offered as
a Phase-A input.

**Closes:** `definition-lifecycle.md` (cite a locked definition whole).

**Remediation:** Quote all three lines, record the ruling and its basis
(`02-constitution.md` :49 anti-pattern "The admission judge"; :83), upgrade the
section's own confidence from Moderate to High, and carry the gate-4 caveat. Or, in
the original framing — e.g. "'Must
not issue a verdict' reads, on my interpretation, as *a verdict on a candidate*;
INV-18's own wording ('cannot issue admission or maintenance warrants') supports
that narrowing. A reader who reads it as *any* pass/fail would conclude gates 1–8
are misplaced."

---

### FINDING 8: §D.7 certifies `run_replay` as fail-closed without noting the fail-open branch four lines from the ones it cites

**Severity:** medium
**Catalogue:** #1 (absence encoded as a value), #2 (tolerant reader)
**Document location (pin):** :1226–1236

**Evidence.** §D.7 presents `run_replay` as an INV-05 satisfaction and states (pin
:1233–1236):

> The comparison is fail-closed: `rec.env.get(k) != live_env.get(k)`, so a record
> carrying only `{"git_rev": …}` reads `None` for all seven and is **refused**, not
> admitted (:3943).

That claim is true and I verified it — for the **env keys**. Twenty-eight lines
later, in the same function:

```python
:3971   if rec.common_future_hash and ctx.future.hash != rec.common_future_hash:
:3972       raise RuntimeError("replay mismatch: diverged at FUTURE DERIVATION ...")
:3973   live_init = state_hash(ctx.host)
:3974   if live_init != rec.host_init_hash:
:3975       raise RuntimeError("replay mismatch: diverged at SEEDING ...")
```

The future-derivation check is **truthiness-gated**: `common_future_hash == ""`
silently skips the verification. The host-init check two lines below is
unconditional. Within four lines, two absence-carrying `str` fields get opposite
treatment — one fails open, one fails closed.

**Consumption trace.** Unreachable today, and I checked rather than assumed: every
`common_future_hash=""` write site is a non-`fan` kind — `:2458` (refan void_event),
`:2997` (preflight_iter), `:3178` (extension_event), `:3453` (void_event) — and the
`kind != "fan"` guard at :3957 rejects all of them before :3971. **So the guard is
held shut by a filter fourteen lines upstream, not by its own condition.** That is
precisely the "defence by coincidence" the document names and criticises in §C.3
about `arms`, and precisely the `host_init_hash=""` pathology it makes the centrepiece
of §C.11 and §E.4 — the same field type, the same empty-string sentinel, in the same
codebase, reached by the same reasoning.

The document does not apply its own strongest lens here. A section certifying a
function's fail-closed discipline should either report the one branch that is not,
or state that it is unreachable and why.

**Closes:** `silent-default-elimination.md` (absence is a type, not a falsy value).

**Remediation:** Add to §D.7: "One qualification: the future-derivation check at
:3971 is truthiness-gated on `common_future_hash`, so an empty string skips it
rather than refusing. Unreachable today — every `""` write site is a non-`fan` kind
excluded by :3957 — but it is the same empty-string-as-absence pattern §C.11
reports, and it belongs in §F.4's evidence."

---

### FINDING 9: Residual internal inconsistencies after the mid-audit corrections

**Severity:** low
**Catalogue:** #10 (dual sources of truth, at document scale)
**Document location (pin):** :3, :952–960

Two survivors of otherwise-good corrections:

**(a) The header still carries the superseded LOC.** Pin :3 reads
`experiments/kernel_demo_plots.py` (**151 LOC**), while §E.7's staleness correction
at pin :1415 correctly reads **432 lines** (verified: `wc -l` = 432). The header is
the first line a reader sees and the one most likely to be quoted onward.

**(b) "exactly three places", four rows.** Pin :952 states `manifest_hash` "**is**
compared in exactly three places", and the table immediately below (pin :955–960)
has four rows: `run_replay` :3953–3954, `run_report` :3834–3839,
`kernel_demo_plots.py` :150–152, and `Store.merge` :1636. The fourth is arguably a
dedup key rather than a comparison, but the prose does not say so and the reader
counts four.

**(c) §A.2.1's "verbatim" forbidden-field block is a subset.** Pin :178–182 presents
`GrowthIntent`'s forbidden list as a ```text block and shows eight entries.
`05-leyline-contracts.md` :101–110 has **ten**. The two omitted are
`suggested_envelope` and — more consequentially — **`free_form_designer_message`**,
which is the free-text covert-channel field and therefore catalogue entry #6's
canonical example. §A.2.1's argument is precisely about what the Momir socket must
not be permitted to receive; dropping the free-text field from a quoted prohibition
list weakens the strongest available instance of that argument. Same pattern as
finding 7, lower stakes, and here the fix strengthens the section.

**(d) `FROZEN_FIELDS` line range.** Cited `:188–223` at pin :68; actual `:186–221`
(entries `:187–220`). And see the six-vs-eight gate-threshold correction in §3.1.

**Remediation:** Update the header to 432. Restate (b) as "compared in three places
and used as a dedup key in a fourth." Quote the forbidden block complete, and let
`free_form_designer_message` carry the covert-channel point. Fix the two line ranges.

---

### FINDING 10: the policy/evidence split delivers its stated benefit on the train path only — three of the four `manifest_hash` consumers must be retargeted, and §C.10 records them as "survives, unchanged"

**Severity:** high
**Catalogue:** #11 (unversioned policy — the split is the remedy, and as specified it is
partial)
**Document location:** §C.10's consumer table (pin :955–960), and §F.2's *Phase-A
action*
**Status:** this is a finding **against the freshly-revised section**, whose
confidence was upgraded Moderate → High after my pin.

**Evidence.** §C.10 now enumerates four `manifest_hash` consumers and marks three
"**Yes** — replaying/reporting a specific record wants exactly a run identity" and the
fourth "Unchanged, and this is part of the defect." I verified all four sites and
agree that **nothing breaks**. But "survives the split" and "delivers the split's
purpose" are different claims, and the table asserts the first while §F.2 promises
the second.

The split's stated purpose (pin :926–928): *"re-freezing on the same commit yields the
same policy hash, records stay bound to the calibration that produced them."* Test
each consumer against that purpose, not against breakage:

| Site | What the check is actually asking | Correct key post-split |
|---|---|---|
| `run_replay` :3953–3954 | "Is this the same *execution* I recorded?" | **`manifest_hash`** — correctly unchanged. Replay wants the run identity. |
| `run_report` D6 :3834–3839 | "May I pool these records into one number?" | **`policy_hash`** — validity depends on shared calibration, not shared `concurrency_factor` |
| `kernel_demo_plots.py` :150–152 | "May I pool these into one figure?" | **`policy_hash`** — same question as D6 |
| `Store.merge` :1636 | "Is this fan already counted?" | **`policy_hash`** — and this is the point |

**Consumption trace.** Leave D6 on `manifest_hash` and the operator who re-freezes on
the identical commit — the exact scenario the split exists to make benign — still
cannot run `--report` across the boundary: D6 sees two distinct `manifest_hash`
values among eval-namespace records and refuses. The train path is fixed; the report
path is not. The split's promise is delivered on one of two paths.

`Store.merge` is sharper still. The document's §C.10 and §E.5 identify the dedup key
`(manifest_hash, fan_id)` as *permitting* the same fan under two generations, "double-
counted by `tr_fan_counts` (:3486) and by `load_for_training`" — and file that as
**part of the defect the split is meant to fix**. But the table then records the site
as "Unchanged." Keying it on `(policy_hash, fan_id)` is what makes the duplicate
collide and raise; leaving it on `manifest_hash` leaves the double-count exactly
where §E.5 found it. As specified, the split fixes the calibration binding and does
**not** fix the double-count, while §E.5 presents them as one defect with one remedy.

**This does not refute the coordinator's adjudication or the designer's analysis** —
both are correct that no consumer breaks, and the upgrade to High confidence on *that*
claim is earned. It refutes the narrower proposition that the split needs no further
work at these sites.

**Closes:** `versioned-policy-parameters.md` (every consumer must be classified by
which identity its question depends on).

**Remediation:** Add a fourth column to §C.10's table — "which identity does this
check's question actually depend on?" — and mark D6, the sidecar filter and
`Store.merge` as **retarget to policy hash**, `run_replay` as **keep**. Then §F.2's
Phase-A action becomes "two records *and* a consumer-retargeting pass", which is the
honest scope.

---

### FINDING 11: the new §D.9 praises as a closure the one function the re-done catalog entry flags as carrying an open silent default — and §E.7 under-inherits three further open items from that entry

**Severity:** medium
**Catalogue:** #1 (silent defaults), #10 (two accounts of one artifact)
**Document location:** new §D.9 (current :1259–1284), revised §E.7
**Status:** finding against material added **after** my pin.

**Evidence.** New §D.9 is titled "The codebase caught a silent-default class that
eight reviewers missed" and celebrates `_finite_points` / `_gapped` (plots :65–90) for
preserving the original epoch index. **That praise is correct** — I verified
`_gapped` ranges `points[0][0]` to `points[-1][0]` and back-fills `math.nan`, so the
x axis carries true epoch numbers.

But the re-done catalog entry, which the document has not absorbed, records
(`02-subsystem-catalog.md` :904):

> **`_finite_points` silently drops non-finite values while `require_number` refuses
> them.** Line 78 keeps a value only `if math.isfinite(f)`, so an `inf` in a curve is
> dropped and rendered as a gap indistinguishable from a recorded null.

I confirmed this in source. `_finite_points` (plots :72–79) is:

```python
for i, v in enumerate(curve):
    if v is None:            continue        # null  → gap
    if not isinstance(v, (int, float)) or isinstance(v, bool): raise PlotDataError(...)
    f = float(v)
    if math.isfinite(f):     points.append((i, f))   # non-finite → dropped. No else.
```

Three things follow, and they matter because of *which* document this is:

1. **It is a type-dispatch guard with no fall-through branch** — structurally the
   identical defect to `TelemetryRecord.check_finite`'s missing `else: raise`
   (:372–381), which the document makes the centrepiece of §C.1 and §C.13 and
   escalates into Phase-A recommendation 1 ("a construction guard whose type dispatch
   has no fall-through branch"). The document's own signature finding recurs in the
   function §D.9 holds up as the exemplar, and the document misses it in the second
   place having found it in the first.
2. **It collapses two distinct absences into one rendering** — a recorded `null` and a
   live `inf` both become the same gap. That is the document's own §C.13 lesson
   ("on the wire a diverged measurement and an absent one become the same token")
   reappearing at the render boundary.
3. **`require_number` (plots :48–51) refuses exactly this condition** with the reason
   stated inline. Two validators, one module, opposite policies on the same input
   class — which is the document's §E.3 "dual sources of truth" shape.

**§E.7 also under-inherits.** The revised §E.7 states two of three silent-default
findings are closed and lists `SPIKE_CRASH_MARGIN` as the sole survivor. The re-done
catalog entry carries **four** open concerns the document does not: the `_finite_points`
asymmetry (:904), `split_role` pooling never refused while namespace and manifest are
(:896), `plot_alpha_beta` aborting on a legitimate absence that its sibling
`plot_tune_curve` skips (:903), and no exit-code discipline (:905). At least the first
is squarely in this document's scope.

**Consumption trace.** Low blast radius on Phase A — this is the witness layer, and
none of it becomes a Leyline record. The reason it is worth filing is what it says
about the *correction*: the document re-read the sidecar's source and correctly closed
two findings, but did not re-read the catalog entry that had been re-done against the
same file two hours earlier. Both passes were done; neither saw the other. That is
the same failure mode as the original staleness, inverted.

**Closes:** `silent-default-elimination.md` (no fall-through in a type-dispatch
guard — the document's own recommendation 1).

**Remediation:** Add `_finite_points`'s missing `else` to §E.7's open list and cite it
in §F.1 as a *second* instance of the fall-through pattern — it strengthens
recommendation 1 considerably to show the defect recurring independently in the same
codebase. Soften §D.9's framing from "caught and closed" to "caught the index-shift
class; the same function retains the fall-through the catalog flags at :904."

---

## 3. Verifications requested, and their results

Three items in the briefing asked me to check the requester's or the designer's own
reasoning rather than to find defects. All three are reported here whether or not
they produced a finding.

### 3.1 §F.2 — the freeze-manifest policy/evidence split. **Your reasoning is correct. Your verification was narrower than your conclusion.**

You retired the designer's flagged uncertainty by establishing that `run_train`
(:3343) and `run_eval` (:3462) check only `frozen_block_hash` and `config_hash`,
never `manifest_hash`.

**The premise is verified.** I read both sites directly. `run_train` :3343 and
`run_eval` :3463 (the check is at :3463; :3462 is the `json.loads`) are the identical
pair, and neither consults `manifest_hash`. `run_eval` reads it at :3469 only to
stamp onto records. Threshold tampering is caught by `frozen_block_hash` and code
tampering by `config_hash`. The anti-p-hacking property does not rest on
`manifest_hash`.

*One correction in passing.* The designer's supporting sentence (pin :947–948) reads
"all eight gate thresholds live in `FROZEN_FIELDS` :211–216". Both numbers are wrong:
there are **six** gate-threshold entries, `gate1_min_mild_noop_wins` through
`gate6_late_density_mult`, at **:209–214**. Gates 7 and 8 contribute no threshold —
which is not an oversight but a direct consequence of the document's own §C.7
finding, that gate 7 is report-only and gate 8 is a skip-or-measure. The conclusion is
unaffected; the count is a third instance of the citation drift in finding 9.

**I also verified the part neither of you stated, which the conclusion actually
needs:** that the proposed split would *deliver* a stable policy hash. It would.
`run_preflight` is idempotent on the fan set — it skips episodes already carrying
`fans_per_episode` fans (:2938) and skips existing refans (:2953) — so a second
`preflight --freeze` on the same commit runs no new episodes, fits the `Normalizer`
over the identical vector set (:2956–2961), and recomputes gates 1–7 over identical
fans. The only genuinely run-varying inputs are gate 8's live `concurrency_factor`
and the `gate8_outcome` detail, both of which the document assigns to the *evidence*
half. **So re-freezing on the same commit would yield an identical policy hash.**
The mechanism claim holds.

**Where your two-line check was under-scoped.** "Neither enforcement site checks it"
does not by itself license "splitting it is safe", because `manifest_hash` has other
consumers that a split must be designed around. I found four:
`run_report`'s D6 mixed-manifest refusal (:3834–3839, eval-namespace only),
`run_replay` (:3953–3954), `Store.merge`'s dedup key (:1636), and — new since the
sidecar rewrite — `kernel_demo_plots.py` :150–152.

**The designer reached the same four independently, between my first read and the
pin.** Pin :952–960 now enumerates all of them with a survives-the-split verdict per
row. I checked that analysis and agree with it: all three comparison sites want a
*run* identity, which is what `manifest_hash` correctly is, so they are unaffected
by introducing a separate policy hash alongside it. Note the directions, which the
table does not spell out: under a stable policy hash D6 would stop firing on a
re-freeze (correct — that is the defect being fixed), and `Store.merge`'s dedup
would become *stricter*, since the same `fan_id` under two generations would collide
on a stable key rather than pass.

**Verdict: the split is safe, and the correct framing is the designer's stronger
one — the split is what makes a stable record↔calibration binding possible at all.**
Your adjudication was right, and the upgrade to High confidence is earned on the
claim it is attached to.

**But "no consumer breaks" is not "the split is complete", and §C.10's table asserts
the first where §F.2 promises the second.** Three of the four consumers ask a
*pooling-validity* question, which depends on shared calibration rather than shared
run identity, and left on `manifest_hash` they keep the coupling the split exists to
remove — so the split as specified fixes the train path and neither the report path
nor the double-count §E.5 files under the same defect. **That is finding 10**, and it
is the substantive result of this verification. You asked for a critical finding if
your reasoning was wrong; your reasoning is not wrong, and this is what I found
instead: the scope of the remedy, not the soundness of the premise.

The other residual is finding 9(b), a counting slip in the same table.

### 3.2 The domain-presence calls

- **Elesh absent→partial: confirmed.** Verified clause by clause against
  `02-constitution.md` :282–285 and in source (`SeedDelta` :638, `build_seed`'s
  `ValueError` :729, `tau_init` :735). The document's deflating language is accurate.
- **Ugin absent→partial: verdict survives, stated evidence does not.** See finding 3.
- **Momir / Urabrask / Emrakul genuinely absent: confirmed.** `SEED_NAMES` is a fixed
  four-tuple `semantic_const` (:634) and `build_seed` is a four-entry dict dispatch
  (:721–731) — no generation. Nothing compiles; `FORBIDDEN_RELAXATIONS` (:900–913)
  bans `torch.compile` at :912 with the D10 rationale inline, verified verbatim.
  `Stage` (:769) terminates at `FOSSILIZED` with no seventh member and no transition
  out. **No missed socket.** I specifically looked for a sedation/decay analogue in
  the α/β machinery and found none: `cosine_ease` (:779) is symmetric and could
  support descent, but nothing calls it in that direction, which is exactly what
  §A.2.4 says.
- **The rest of the table:** spot-checked Leyline, Aurelia, Isperia, Tamiyo and
  Jin-Gitaxias against source. All four `partial`/`present` calls are supported.
  Isperia's row is notably well-deflated — `verdict()` never ANDing its five booleans
  (:3319–3325) and `germinate` (:1167) requiring no token are both verified.

### 3.3 §A.2 — are the socket signatures real or retrofitted? **Real, and this is the strongest section in the document.**

I was asked to be sceptical of Momir's, which "rests on the claim that `SeedDelta`'s
output contract is already fully specified and tested."

**The claim holds.** `SeedDelta` (:638) is an abstract base fixing
`forward(h) = gain * f(h)` with `gain = nn.Parameter(torch.zeros(()))`, so the delta
is exactly zero at construction; `f` raises `NotImplementedError`; all four
subclasses take `channels: int` and nothing else (:654, :663, :687, :704 — verified);
`split_decay_groups` keys on `endswith("gain")` (:759), so `gain` really is the sole
τ carrier and the optimizer treats it as such. That is a genuine, executable output
contract for a component that does not exist. Not retrofitted.

The sharpest claim in §A.2.1 — that `name: str` is `preferred_operator` in its purest
form and therefore INV-09 schema-invalid — is **exactly right**, and I checked the
one thing that could have sunk it: `preferred_operator` is listed verbatim in
`GrowthRequest`'s forbidden block (`05-leyline-contracts.md` :102, read in full,
ten entries). The identification is direct, not analogical, as the document claims.

§A.2.5's Urabrask treatment is also precisely sourced: `FORBIDDEN_RELAXATIONS` at
:900–913, "enabling AMP" at :908 and the `torch.compile`/D10 entry at :912, both
verbatim; the "deliberately NOT a `semantic_const`" caveat at :901–903 verified; and
selftest step 1 (:2079–2082) does indeed record an unconditional `"status": "pass"`
while asserting nothing. The self-correction noted at pin :1607 ("I had accepted
'possibly no socket' before checking") is the right instinct and the result is
correct.

The one overstatement in §A.2 is finding 5.

---

## 4. Machine-readable summary

```json
{"summary": {"critical": 2, "high": 2, "med": 5, "low": 2},
 "code_defects": ["F-2"],
 "document_defects": ["F-1","F-3","F-4","F-5","F-6","F-7","F-8","F-9","F-10","F-11"],
 "ruled_by_coordinator": {"F-2": "CONFIRMED by execution; elevated to critical, reclassified as a code defect",
                          "F-7": "underlying authority question RULED in the document's favour; gates 1-8 correctly placed; downgraded to low, quotation hygiene only"},
 "checked": [
   "1-silent-defaults", "2-tolerant-readers", "3-fail-open-version-gates",
   "4-version-in-name-only", "5-compat-shims", "6-covert-channels",
   "7-resolver-preferences", "8-hidden-resolver-state", "9-blinding-by-ignoring",
   "10-dual-sources-of-truth", "11-unversioned-policy",
   "12-silent-definition-edits", "13-vacuous-contract-tests"],
 "findings_by_entry": {
   "1": ["F-2", "F-8", "F-11"], "2": ["F-8"], "6": ["F-9c"], "9": ["F-1"],
   "10": ["F-1", "F-2", "F-3", "F-5", "F-9", "F-11"], "11": ["F-3", "F-10"],
   "12": ["F-7"], "13": ["F-4", "F-6"]},
 "findings_against_post_pin_revisions": ["F-10", "F-11"],
 "verifications_requested": {
   "F.2-policy-evidence-split": "coordinator reasoning CONFIRMED; conclusion was under-scoped, designer independently closed the gap before the pin",
   "elesh-absent-to-partial": "CONFIRMED",
   "ugin-absent-to-partial": "verdict CONFIRMED on §A.2.3 grounds; §A table evidence REFUTED (finding 3)",
   "momir-urabrask-emrakul-absent": "CONFIRMED, no missed socket",
   "E.1-authority-collapse": "mechanism CONFIRMED; framing is decoration; stated grep evidence REFUTED (finding 4)",
   "A.2-socket-signatures": "REAL, not retrofitted; SeedDelta output contract claim CONFIRMED"},
 "overtaken_during_audit": [
   "E.7-witness-layer-staleness (designer self-corrected; residual = header LOC, finding 9a)",
   "C.10-manifest-hash-consumers (designer independently enumerated all four; residual = count slip, finding 9b)"],
 "not_assessable": [
   "02-subsystem-catalog.md correctness — treated as a completed input per briefing; ~40% of the document's citations are inherited from it and were not re-derived",
   "runtime behaviour — no CLI mode executed; no hash, gate outcome or p-value observed",
   "post-07:49:49 document state — target was under active edit; findings may be stale",
   "plainweave definition-lifecycle state — store seeding pending (simic-357c92664c), so catalogue entry 12 could not be checked against baselines for any Leyline definition",
   "whether the eval-path prefix assumption actually holds at runtime — one state_hash call would settle it, as the document itself says"]}
```

---

## 5. Confidence Assessment

**Overall Confidence: High** for findings 1–8; **Moderate** for the severity
*ordering*, which is a judgement about Phase-A cost rather than a verified fact.

| Finding | Confidence | Basis |
|---|---|---|
| F-1 `TelemetryEnvelope` conflation | **High** | Quoted code both sides. `05-leyline-contracts.md` §9.2 read in full including the per-consumer-projection sentence at :75; `02-constitution.md` Appendix B Nissa clause read in full. The contradiction with §C.1's own table is internal and needs no external authority. |
| F-2 non-finite guard | **High** on the divergence; **High** on reachability *(upgraded)* | Both guards read directly at :1774–1777 and :3397–3400; `sigmoid(±inf)` finiteness is arithmetic, not inference. I originally graded reachability Moderate and declined to claim the case occurs. **The coordinator executed it and it does** — `decide_live` rejects, `_query_dicts` admits, `p = 0.0` reads as restraint. The escape table (both heads, five inputs) is mine and is arithmetic; only the `-inf` row was executed. |
| F-3 Ugin evidence | **High** | `FROZEN_FIELDS` read in full at :186–221 and classified field by field against `StrategicEnvelope` :14–39, also read in full. The count (6 of 35) is mechanical. |
| F-4 §E.1 grep | **High** | Reproduced the document's own command over its own range; output pasted verbatim. |
| F-5 `draw_schedule` role | **High** | All three call sites enumerated by grep and read; `Policy.embed` input width read at :1716. Issue text retrieved via `mcp__filigree__issue_get`, not paraphrased. |
| F-6 `:2188` citation | **High** | Line read in context; the enclosing `tempfile.TemporaryDirectory()` at :2209 read. |
| F-7 selective quotation | **High** on the omission; **resolved** on the merits | Appendix B :292–295 read in full. I reported the omission, not a refutation, and referred the substance to the coordinator — who ruled that "verdict" does narrow to *a verdict on a candidate* (`02-constitution.md` :49 anti-pattern "The admission judge"; :83). **The document's reading was right and mine was the open question.** Downgraded to low; only quotation hygiene survives. |
| F-8 `:3971` fail-open | **High** on the branch; **High** on unreachability | Every `common_future_hash=""` write site enumerated by grep and each one's `kind` checked. Unreachability is established, not assumed. |
| F-9 residuals | **High** | Direct comparison; `wc -l` = 432. |
| F-10 split consumer retargeting | **High** on the classification; **Moderate** on severity | All four sites read. The classification rests on "what question is this check asking?", which is interpretive — but D6's own comment ("refuse mixed manifest_hash inside any single number") states the pooling-validity question explicitly, and `Store.merge`'s double-count is the document's own §E.5 finding. |
| F-11 `_finite_points` / §D.9 | **High** | Read plots :65–90 and :38–52 directly; the missing `else` is structural. The catalog's independent statement of the same defect at :904 is corroboration, not my source. |
| §F.2 verification | **High** | Both enforcement sites read; `run_preflight`'s idempotence established from :2938/:2953; all `manifest_hash` occurrences enumerated by grep. |
| Severity ordering | **Moderate** | F-1 above F-2 rests on my judgement that a wrong record *shape* costs more to unwind than a wrong *claim about a guard*. Contestable. |

---

## 6. Risk Assessment

**Implementation Risk of acting on these findings: Low.** Every remediation is a text
change to an advisory document. None touches `experiments/kernel_demo.py`, and none
should — the single-file layout is locked at rev 6.1 and nothing here proposes
otherwise.

**Reversibility: Easy** for the document. **Difficult-to-Irreversible** for the Phase-A
decisions it informs — which is the entire reason the severities are ranked the way
they are.

| Risk | Severity | Likelihood | Note |
|---|---|---|---|
| **F-1 is adopted before it is corrected.** §F.7 is a numbered Phase-A action with an explicit *Phase-A action* line. If `TelemetryEnvelope` is written without provenance or identity, INV-08's fail-closed reconciliation cannot be implemented and the blinded view is never designed. Unwinding costs a schema version on the first record class Phase A writes. | **Critical** | Moderate | The document is explicitly a Phase-A input and recommends landing schema decisions "before the first Leyline record is persisted." |
| **F-2's remediation carries no migration risk, but the underlying code fix does.** Moving the finiteness check before the activation in `_query_dicts` changes when the demo raises. It must not be done casually — `config_hash` covers source text, so editing `_query_dicts` invalidates every recorded hash and makes `run_train` refuse (:3343). | Medium | Low | **I am not recommending the code change.** The finding is against the document's claim. Any code fix is a separate, spec-governed decision. |
| **The audit itself is stale.** The target moved three times during this audit and may have moved again. | Medium | High | Mitigated by the pin in §0. Re-check any finding before acting. |
| **Findings 4–8 are read as discrediting their sections.** They are not. §E.1's mechanism, §D.7's INV-05 reading, §C.3's payload finding and §A.2's socket analysis are all sound; the defects are in stated evidence, not conclusions. | Medium | Moderate | Each finding states explicitly what survives. |
| **Over-correction on F-3.** Ugin-`partial` is *correct*; only the §A table's justification is not. A reader who takes finding 3 as "downgrade Ugin" would lose a sound call. | Low | Low | Stated explicitly in the finding. |

---

## 7. Information Gaps

1. **`02-subsystem-catalog.md` was not re-derived**, per the briefing. Roughly 40% of
   the document's citations are inherited from it and carry its confidence, not mine.
   *Unassessed:* the accuracy of every claim I marked "catalog-verified" rather than
   reading myself.

   **Correction to an earlier draft of this audit.** I had recorded that no
   systematic revalidation of the catalog had been done and recommended commissioning
   one. **That was wrong, and I withdraw it.** The coordinator corrected me and I
   verified the correction directly: `02-subsystem-catalog.md` carries a version
   anchor in its header (:6–10) stating that `kernel_demo.py` was analysed at
   `2b48431` and is unchanged through `aa86388` (`git diff` empty, mtime 06:51),
   covering 8 of 9 entries, and that the Plotting Sidecar entry was **re-done**
   against the current sidecar. The re-done entry (:861–908) describes the 432-line
   file, cites `require_number`/`PlotDataError` correctly, and its confidence note
   records that the author **executed** `pytest tests/unit/kernel_demo/test_plots.py`
   → 16 passed. The catalog is in better shape than the document's inherited warning
   about it, and better than my draft assumed. The residual exposure is narrow and
   stated in finding 11.

   **One genuine residual in the catalog's own labelling**, raised by the coordinator
   and confirmed: the entry carries two different provenance claims for one artifact.
   The header (:9) says the sidecar entry was "re-done against the sidecar **as
   committed at `aa86388`** (07:32)"; the entry's own anchor (:861, :908) says
   "**working tree at 2026-08-10 07:21, uncommitted-modified over `853e9ef`**". The
   **content is identical** — `git diff HEAD` is empty for both files, verified — so
   this is an imprecise label, not stale content. But it is the same class as the
   defect the entry exists to correct, and a reader reconciling the two would not know
   which to trust. One-line fix: name `aa86388` in both places.
2. **Nothing was executed.** No CLI mode was run; no hash, gate outcome, refusal path
   or p-value was observed. *Unassessed:* catalogue entry 11 in its runtime form —
   whether any recorded artifact actually carries a mismatched policy identity today.
3. **Plainweave baselines are unseeded** (simic-357c92664c). *Unassessed:* catalogue
   entry 12 (silent definition edits) against any Leyline definition — I could check
   git history for `kernel_demo.py` but there is no definitional lifecycle state to
   check a *contract* against, because none is registered yet.
4. **Phase A's intended record inventory is unknown to me**, as it was to the
   designer. *Unassessed:* whether finding 1's remediation conflicts with a
   record-granularity decision already made, and whether `05-leyline-contracts.md`'s
   shapes are locked at field granularity.
5. **The document's post-07:49:49 state.** It was under active edit throughout.
   *Unassessed:* everything written after the pin.
6. **I did not read `docs/design/07-counterfactual-engine.md`**, which the document
   lists as an authority. *Unassessed:* whether §C.4/§C.5's `Snapshot` and
   `CommonFuture` readings conflict with it.

---

## 8. Caveats & Required Follow-ups

**What the requester must verify before acting:**

1. **Finding 1 is the one to adjudicate first, and it is a design disagreement, not a
   citation error.** I am asserting that the demo's `TelemetryRecord` is the precursor
   of the *blinded view*, not of `TelemetryEnvelope`, and that §F.7 as written would
   put a wrong record shape into Leyline. The designer may have a reading of INV-37
   under which the envelope itself is blind and per-consumer projections *add* rather
   than remove. If so, that reading needs to be stated and reconciled with
   `05-leyline-contracts.md` :49–69, which lists `provenance` as an envelope field.
   **This is the single finding most worth a round-trip to the architect.**
2. **Finding 3 asks you to change evidence, not a verdict.** Confirm you still want
   Ugin at `partial` — I believe you should — and replace the §A table's cell.
3. **Finding 7 requires your call, not mine.** Whether Jin-Gitaxias's "Must not issue
   a verdict" narrows to *a verdict on a candidate* determines whether gates 1–8 are
   correctly placed. You hold the domain semantics. I report only that the clause was
   omitted from the argument that turns on it.
4. **Re-pin before acting.** The document has moved since 07:49:49 with near
   certainty. Diff against `/tmp/audit-pin.md`
   (`659bb8bc2dfe651d5ff2c4134f592e805acce47d31bfaa3e6502ecf888ccdc09`) and drop any
   finding the designer has already closed — two were closed mid-audit and more may
   be.

**Assumptions this audit rests on:**

- That `experiments/kernel_demo.py` at HEAD (`aa86388`) is the code the document
  describes. Verified for every line I read; **not** verified for lines I took from
  the catalog.
- That the catalog is correct where I did not re-derive it. See gap 1 — this
  assumption is now known to have failed at least once.
- That static reading is sufficient for contract-shape questions. It is, for shapes;
  it is not for reachability, and I have flagged reachability separately in findings
  2 and 8 rather than folding it into severity.

**Limitations of a static sweep.** I cannot confirm that a guard fires, only that it
is written. Findings 2 and 8 are both "the guard does not cover the case its comment
describes" — neither is a demonstration that the case occurs.

**Recommended next steps, in severity order:**

1. **Patch finding 2 in `kernel_demo.py`** — move `_query_dicts`'s finiteness check
   onto `p_logit`/`seed_logits` before the sigmoid and softmax, matching
   `decide_live` :1774. This is the only item here that is a defect in shipped code,
   it is confirmed by execution, and both silent directions are catastrophic.
   **Sequencing caveat:** `config_hash` covers source text, so editing `_query_dicts`
   invalidates every recorded hash and makes `run_train` refuse (:3343). It is
   therefore a pre-data change or a spec-governed one — which is an argument for doing
   it *now*, before Phases A–F collect anything, not later.
2. **Adjudicate finding 1** (envelope vs blinded view) with the architect before any
   Phase-A `TelemetryEnvelope` work. Highest unwind cost of the document findings.
3. **Correct findings 3 and 10** — both are claims that would be transplanted into
   Phase A as patterns to copy, and F-10 scopes the top-ranked recommendation. Correct
   §D.8's "mirrored" row regardless of the patch: the contract lesson (guard the
   representation, not a value derived from it) is what Phase A inherits.
4. **Correct findings 4, 5, 6 and 8** — evidence accuracy in a document explicitly
   offered as a Phase-A input, and findings 4 and 6 are of the class ("cited evidence
   does not say what it is claimed to say") that this analysis has now had corrected
   five times. F-5's correction routes to the briefing, not the architect.
5. **Reconcile the document's §E.7 against the re-done catalog entry** (finding 11).
   Both passes were done independently against the same file; neither absorbed the
   other, so four open concerns sit in the catalog and not in the document. *This
   replaces my earlier recommendation to commission a catalog revalidation pass,
   which I withdraw — the coordinator corrected me and I verified the catalog is
   already anchored and its one stale entry already re-done.*
6. **Fix findings 7 and 9** — record the gates ruling and complete the quote (F-7);
   header LOC, count slip, forbidden-block subset (F-9). All trivial.

**What this audit does not cover:** the statistical validity of the demo's design
(`yzmir-counterfactual-statistics` territory); the correctness of `02-subsystem-catalog.md`;
test-plan design for the Phase-A contract suite (`contract-testing.md` supplies the
fixture inventory and coverage rule, and none of my findings substitutes for it); and
any redesign of the contract suite — that is `contract-suite-architect`'s side, and
findings above sketch remediation direction only.

**A closing note on the document, which the finding count understates.** Eleven
findings against 1,905 lines carrying roughly 150 source citations is a low defect
density, and I found no fabricated mechanism, no invented record, and no citation
pointing at code that does not exist. Ten of the eleven are document defects, and the
most serious of those is a *generalisation* error (F-1) — a correct local observation
carried one step too far — not an evidence problem. §A.2, §C.10 as revised, §D.5 and
the `Snapshot` treatment in §C.4 are genuinely good contract analysis; the designer
self-corrected two of my findings mid-audit without prompting; and on the one
authority question I referred upward (F-7), the document's reading was upheld and my
concern was the thing that did not survive. **This is a document worth fixing rather
than one worth distrusting**, and the same register applies to the demo it analyses.

**One thing changed shape between the first delivery and this one, and it is worth
naming.** F-2 arrived as a documentation finding — a guard *certified* as equivalent
when it is weaker — filed with reachability explicitly disclaimed. Execution turned it
into a confirmed defect in shipped code, with both silent directions live. The lesson
is not about this audit but about the method: a static sweep can locate a guard that
does not cover its own stated case, and it cannot tell you whether that matters. **The
disclaimer was the load-bearing part of the finding**, because it is what prompted
somebody to run it. Findings 8 and 11 carry the same disclaimer — F-8 is held shut by
a `kind` filter fourteen lines upstream, F-11 by whether an `inf` ever reaches a
plotted curve — and neither has been executed. If either is worth the same five
minutes, F-8 is the one I would spend them on.
