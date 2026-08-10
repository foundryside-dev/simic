# 04 — Final Report: Architecture Analysis of `experiments/`

**Target:** the Simic kernel demo — `experiments/kernel_demo.py` (4,066 lines) and
`experiments/kernel_demo_plots.py` (433 lines)
**Date:** 2026-08-10
**Version anchor:** `kernel_demo.py` analysed at `2b48431`, byte-identical through
`aa86388` (`git diff HEAD` empty, mtime 06:51, verified three times). The sidecar was
rewritten upstream mid-analysis and is anchored to `aa86388`.
**Method:** 8 parallel explorers over line-range partitions, an independent contract
audit, two validation passes, a quality consolidation, and coordinator adjudication of
every inter-agent conflict.

---

## Contents

1. [Verdict](#1-verdict)
2. [What the system is](#2-what-the-system-is)
3. [What holds](#3-what-holds)
4. [Findings, ranked by blast radius](#4-findings-ranked-by-blast-radius)
5. [The cheap fixes](#5-the-cheap-fixes)
6. [What this says about Phase A](#6-what-this-says-about-phase-a)
7. [How the analysis itself went wrong](#7-how-the-analysis-itself-went-wrong)
8. [Limitations](#8-limitations)

---

## 1. Verdict

**This is a well-built experimental instrument with one live code defect, a
verification asymmetry at its headline claim, and a cluster of constraints enforced by
comment rather than by mechanism.**

The register that fits, borrowed from the contract audit's own closing assessment:
**worth fixing, not worth distrusting.** That applies to the demo as much as to the
documents about it.

Three things are true simultaneously and the report is wrong if it drops any of them:

- The certification battery is **genuinely falsifiable and demonstrably so** — gates 1–6
  each have an executable *failing* fixture, and the refusal chain is closed end to end.
- The demo's **pre-registered prediction is hash-protected**: `DESIGNED_WINNER` is a
  `semantic_const`, so the prediction it might be embarrassed by cannot be silently
  edited after results exist.
- The **finiteness guard on the live decision path does not guard the case it was
  written to catch**, and the eval path assumes a property the fan path re-verifies on
  every fan.

---

## 2. What the system is

A single-file harness proving the substrate loop that Simic is built on: train an
undersized host, snapshot it, fan out matched counterfactual branches with a measured
no-op arm, certify the evidence through an 8-gate battery, learn a policy from the
recorded fans, and adjudicate against a pre-registered verdict.

It is **deliberately not Simic** (module docstring, lines 3–7): the seed menu is fixed
and human-authored, which is exactly what Simic proper rejects. The single-file layout
is a **locked spec decision** (rev 6.1) and the read-top-to-bottom property is the
point — monolith-shaped findings are by design and are not reported as debt.

Two things about it are unusual enough to name. It is **self-certifying**: 109 objects
carry an `@semantic` decorator feeding a `config_hash` over their own source, and four
CLI modes refuse on mismatch. And it is **determinism-first by construction rather than
by seeding**: `torch.manual_seed` is never called; the design simply never depends on
the global RNG stream, verified across 80 pathology × seed × stage combinations with a
positive control.

Architecture, verified mechanically rather than asserted: the identity spine has **no
outbound dependencies** and is depended on by everything except the sidecar; **Records &
Store is a verified leaf** typed against primitives rather than against other
subsystems' dataclasses; **Host/Seeds/Slot depends only on the spine**. The one cycle in
the catalog — Certification Battery ↔ Run Orchestration & CLI — is genuine and correctly
declared on all four half-edges.

---

## 3. What holds

This section is first deliberately. A reviewer on this analysis flagged, correctly, that
"report reads as a takedown" was a live and rising risk. The artifact is better verified
than most, and the positives below are evidence, not courtesy.

**The certification battery is falsifiable, and that is demonstrated rather than
argued.** Gates 1–6 each have an executable *failing* fixture
(`test_preflight_gates.py:140/154/161/212/221/228`); three of four freeze refusals are
tested. The refusal chain is closed: a failed gate blocks freeze, collect re-checks,
train and eval each refuse on manifest mismatch, and `main` exits non-zero. Verdict
thresholds all live in `FROZEN_FIELDS` or `semantic_const`, so post-hoc tuning
invalidates `config_hash` and every downstream artifact. Eval is one-shot; re-running
demands `--void-preregistration`, which writes a permanent append-only event.

**The rev 6.1 amendment is defended against regression, not merely implemented.**
`test_learning.py:91` asserts the two-labels-per-episode `ValueError`, then bounds
`0.4 < p < 0.6` on a cluster-preserving fixture. The band is the point: the episode-level
null has exactly two label assignments (p≈0.5) while a point-level shuffle lands near
1/6. **The assertion was constructed to discriminate between the two schemes**, so it
would fail on a regression to point-level shuffling. `sign_flip_pvalue` is comparably
strong, tested in both directions with a comment instructing "do not reseed to green".

**The pre-registered prediction is hash-protected.** `DESIGNED_WINNER` — `under_normalized→norm`,
`channel_starved→conv_heavy`, `no_spatial_mix→attn`, `mild→conv_light` — is a
`semantic_const` hashed into `config_hash`, consumed as the comparand by the money
test's permutation analysis and reported against observed winners. The prediction the
demo might be embarrassed by **cannot be silently edited after the results are in.**

**Blinding is by construction, not by ignoring.** `TelemetryRecord` (:358–369) contains
no seed name, arm name, pathology, episode seed or provenance field. The identity is not
present to be ignored — which is the property the parent project's invariants require,
achieved here by field absence.

**The counterfactual machinery is genuinely matched.** Arms rebuild from snapshot
*values* rather than sharing restored objects; one precomputed `CommonFuture` is passed
by reference to every arm and indexed by absolute epoch, so common random numbers are
enforced structurally rather than by re-seeding; the no-op arm is really executed and
doubles as the bitwise twin; arm identity enters only inside an `rng_scope`, so a seed
class with more parameters cannot shift the shared stream.

**The grouped-statistics wall holds end to end.** `train_tune_split` is deterministic on
episode identity, stamped once before any fan exists, inherited by every fan, and never
recomputed. The learning path enforces it **by index bound, not by convention** —
`torch.randint(len(train_ex), ...)` puts tune examples outside the index space.

**Temperatures are frozen by signature.** `train_policy(frozen_density=...)` is a
required keyword-only parameter with no default, so recomputation is impossible *by
signature*. The cheapest "illegal states unrepresentable" in the codebase.

**The suite is green and real.** 129 passed, zero skips, on a machine where
`torch.cuda.is_available()` is True — so the green is not skip-green, and
`test_collect.py` genuinely spawns workers to test the collect assembly end to end.

**The author caught a silent-default class that eight reviewers missed.**
`_finite_points`/`_gapped` preserve the original epoch index and emit `nan` at gaps,
because dropping nulls and replotting at contiguous x *"would silently relabel the epoch
axis"*. No explorer reported it. The relevance to Phase A is not the fix but **the
reflex** — the silent-default class is already what this author reaches for first.

---

## 4. Findings, ranked by blast radius

### F1 — The finiteness guard admits the case it exists to catch *(live code defect)*

**The only defect in shipped code in this analysis.** `_query_dicts` (:3397) — the
function on every live path — tests finiteness **after** the squashing transform:

| Input | Test | Caught? | Silent behaviour |
|---|---|---|---|
| `p_logit = -inf` | `sigmoid(-inf) = 0.0` | **No** | never germinates → lift exactly 0 every episode |
| `p_logit = +inf` | `sigmoid(+inf) = 1.0` | **No** | **germinates every episode** at the window's first epoch |
| `seed_logits` has `-inf` | softmax → 0.0, finite | **No** | that seed silently unselectable |
| `nan` (either head) | propagates | Yes | — |

Confirmed by execution for the `-inf` row; the rest is arithmetic. The comment three
lines below says: *"a non-finite checkpoint would silently read as restraint (lift
exactly 0) on every query. Loud, never that."* The always-germinate direction is
arguably worse, producing a *plausible* non-zero lift rather than a suspicious run of
zeros. Neither is recoverable from the record: `decisions` (:3588) stores post-sigmoid
`p`, never the logit.

`decide_live` (:1774) tests the raw logits and is correct — **but it is dead code**, with
its only caller in the test suite. So the tested implementation is the right one and the
untested copy is what runs.

**The contract lesson:** a finiteness guard is a validity check on a contract field and
must run on the field the contract carries — the logit — not on a derived presentation
of it. Checking after a transform that maps the invalid domain into the valid range is
the numeric form of a tolerant reader.

**Fix now, pre-data.** `config_hash` covers source text, so patching invalidates every
recorded hash and makes `run_train` refuse. No store exists yet — free today, expensive
after collection starts. Same reasoning as the rev 6.1 pre-data amendment.

### F2 — The lift path assumes what the fan path verifies

The fan path is verified twice: `TwinDivergence` at runtime and `--replay` post hoc. The
comparator loop (:3512–3588) has **neither**. It builds independent episodes via
`make_episode` and differences two separately executed runs.

Common random numbers *are* genuinely shared — `make_episode` is a pure function of the
episode seed, so both episodes see the same data and the same future, and there is no
global stream to drift. So the correct statement is not "unmatched" but: **the property
the fan path re-verifies on every fan, the lift path assumes.**

The sharpest evidence is what is *not* recorded: every fan stores
`host_init_hash = state_hash(ctx.host)`, but `policy_run` records **deliberately write
`""`** (:3454, :3606). The field that would let an auditor confirm both episodes started
from the same host is not merely unchecked — it is not stored. And `policy_run` records
fail the `--replay` guard twice over (`kind != "fan"`, `fan_epoch is None`).

**Scope: 2 of 5 verdict booleans.** `lift_positive` and `beats_schedule_only` rest on
the unverified path. The eval *grid* runs through the fan executor with full twin,
cross-arm and null-seed verification, so `agreement_beats_null`, `money_chart` and
`falsifier_collapses` are properly matched. **What is weakly guaranteed is the lift
magnitude, not the diagnostic claim.**

**Fix, and its ordering is load-bearing.** Hash `noop_ctx.host` at construction and store
it in place of `""`. Do this *before* widening the replay filter — `policy_run` records
currently carry `host_init_hash=""`, and the SEEDING guard (:3974) is unconditional, so
widening the filter first would make every such replay raise "diverged at SEEDING" when
the real problem is that the field was never recorded.

### F3 — CPU freeze hole

`--device` defaults to `cuda:0`, but neither `run_preflight` nor `freeze_manifest`
asserts it. Certify on GPU, then `preflight --freeze --device cpu` at the same clean
HEAD, and you get a frozen manifest with a **vacuous gate 8** (`ok=True,
"skipped (GPU-only)"`) and CPU-computed gates, with no refusal. Reachable by a
two-command sequence. **The mechanism test costs 18 microseconds and needs no fixture.**

### F4 — "A pass that isn't"

Five independent instances, one theme: gate 8 skip-as-pass on CPU; selftest step 1
printing and recording an unconditional pass while asserting nothing; `wilson_interval`
returning `(0.0, 1.0)` at n=0; `verdict()` returning five booleans and **never ANDing
them**; `eval` exiting 0 regardless of verdict while selftest/preflight/collect all gate
their exit codes. This cluster attacks the certification *headline* rather than any
single number. (Gate 7's always-pass is excluded — it is pinned as deliberate at
`test_gate7_is_report_only:236`.)

### F5 — One rule, two implementations, and the tested one is dead

`decide_live` vs the inline twin at :3562–3573. They already differ **three** ways:
window guard, finiteness layer (F1), and logit-vs-softmax tie-break which agrees only by
monotonicity. The author knows and asks for manual lockstep. **Sequencing constraint:**
consolidating onto `decide_live` puts `record_to_vector` back on the live path, which
*activates* the currently-latent vectorizer twin — so the twin-equality test must land
**before** the consolidation, and both are `@semantic`, so the whole thing lands at a
re-freeze boundary in one commit.

### F6 — Re-freeze decouples calibration from records

`manifest_hash` hashes measured, run-varying values, so re-running `preflight --freeze`
on the *identical commit* yields a different hash. `freeze_manifest` overwrites
unconditionally; `run_train` then reads normalizer and betas from manifest B while
training on manifest-A records, checking only `frozen_block_hash` and `config_hash`.
`run_report`'s mixed-manifest refusal does not catch it — its comparison set is built
from eval-namespace records only. High reachability: both freeze preconditions are met
by simply re-running preflight.

**Fix:** split policy identity from evidence identity — **and retarget the consumers.**
The split alone fixes the train path and leaves the report path and a double-count
broken, because `run_report`'s D6 check and `Store.merge`'s dedup key ask *calibration*
questions, not *execution* questions.

### F7 — Store durability: a silent-loss step before the brick

`merge()` does repair a torn *final* line, and a test covers it. The defect is one step
out: `append` writes the newline as a **suffix**, so a resume-append fuses onto the
unterminated partial line; `merge()` then **silently drops the newly written record**
behind the identical benign warning, and the next append makes the line interior and the
store unreadable. Exposure is **availability plus a silent-loss step, not validity** —
preflight crashes fail-closed on a pre-existing tear, and eval refuses on an episode-count
shortfall. Appends are atomic against concurrent writers (`O_APPEND` + flush-per-append,
measured: 8 processes × 300 appends × 14 KB, 2,400/2,400 valid) — **on Linux with a local
filesystem; NFS does not provide this.**

### F8 — Load-bearing constraints that live only in comments

Five instances, one fix: `FORBIDDEN_RELAXATIONS` is documentation-only and never hashed;
the seed parameter-budget floor is a comment with no `numel` check (measured menu spread
129 / 4,337 / 8,897 / 60,137 params — **466×**, bearing directly on whether gate 4
measures seed *design* or seed *capacity*); `enable_class1()` is unenforced for importing
consumers; the vectorizer field-order contract is a comment; `SEED_NAMES` index→name
correspondence is unpinned, with `Linear(d, 4)` a bare literal.

**Frame it as a coverage gap, not a discipline failure.** The demo enforces exactly the
constraint where post-hoc editing would be *fraud* (`DESIGNED_WINNER`, hashed) and leaves
unenforced the two where it would be an *honest mistake*. That contrast is the finding.

### F9 — The CLI boundary is untested

`main` is never invoked by any test. So the dead `--resume-eval` flag, the unexercised
`--void-preregistration` ordering, `eval`-exits-0, and untested `--extend` are **one gap
with four symptoms**, not four oversights. Phase functions are tested directly by keyword
argument; the boundary is not.

### F10 — Identity bound in some places and not others

`host_init_hash=""` on comparator records; `manifest_hash` as a run identity doing a
policy identity's job; `policy_checkpoint_id` recorded but **never refused on** (16
occurrences, zero comparisons); `certified.json` omitting `config_hash`, so the
certificate binds code via worktree-clean + HEAD equality alone.

### F11 — `run_eval` is a 400-line function with seven responsibilities

The locked single-*file* decision does not cover a single oversized *function*. Clean
seam available: statistics (:3651–3818) separate from the execution loop (:3507–3646).
Related: the file is 4,066 lines against the spec's own "≲1200" target — 3.4×, with
section 14 alone contributing ~560.

---

## 5. The cheap fixes

Several high-blast-radius gaps have measured, trivial remedies. These belong at the top
of any remediation list because cost is not what is holding them open.

| Fix | Cost | Closes |
|---|---|---|
| Gate-8 CPU-skip test | **18 µs**, no fixture (`data=None` returns before use) | F3 |
| `freeze_manifest` missing-certificate test | **0.5 ms**; fourth sibling of a family where three exist | F4 |
| Hash `noop_ctx.host`, store in `host_init_hash` | one hash, one comparison | F2 |
| Guard the logit, not the sigmoid | one line — **do it pre-data** | F1 |
| Tie `Linear(d, len(SEED_NAMES))` | one line (arity only; does *not* close reordering) | F8 |
| Twin-equality test over a shared fixture | one test — **must precede F5's consolidation** | F5 |

---

## 6. What this says about Phase A

Full treatment in [`11-simic-shaped-decomposition.md`](11-simic-shaped-decomposition.md)
(2,160 lines) and its audit in [`12-contract-suite-audit.md`](12-contract-suite-audit.md).
The four results that matter most:

1. **The demo contains a complete, tested output contract for a component that does not
   exist yet.** `SeedDelta` fixes the whole thing in the abstract base — `gain` born
   `zeros(())`, `f()` raising `NotImplementedError`, `forward = gain * f(h)` — and all
   four subclasses satisfy an identical execution-verified shape contract. That is the
   Momir output contract, already written.

2. **The Momir socket is fed by literally the field INV-09 declares schema-invalid.**
   `build_seed(name, ...)` takes a chosen operator name; `preferred_operator` is verbatim
   on `GrowthIntent`'s forbidden block (`05-leyline-contracts.md:102`). A direct
   identification, not an analogy. Consequence: with a fixed menu, *designing* and
   *selecting* collapse — choosing **is** designing — and filling the socket splits them,
   at which point a fixed-width `Linear(d, 4)` over `SEED_NAMES` does not survive.

3. **Conformance already exists without a domain to own it.** `tau_init` drives four
   structurally dissimilar seeds to a measured `rms_ratio = 0.0500` exactly, against
   `rms(f0)` spanning ~18×. That is canonicalisation on the constitution's own words, and
   it does not judge utility. Elesh is *partial*, not absent.

4. **`TelemetryRecord` is the blinded-projection precursor, not the envelope.** The
   demo's single consumer set made the two accidentally identical. The demo's blind record
   is *authored* blind rather than *derived* blind — so it has no allowlist projection and
   cannot have one, because there is no envelope to project from.

---

## 7. How the analysis itself went wrong

Recorded because it is reusable, and because a report that hides its own process is
asking to be trusted on faith.

**Four defects originated with the coordinator, not the explorers:** no version anchor was
recorded at the start (the repo moved underneath the analysis and it was caught by
accident, via an unexplained line-count discrepancy); the first validator was given four
jobs and ran 80 minutes silently before being respawned with two; a containment-based
validation remedy was relayed as though it were source-verified, which would have encoded
four backwards dependency arrows; and the range partition cut **9 of 15 boundaries
mid-section** against the author's own section map — which was in the module docstring the
discovery document had already quoted.

They share one shape: **a checkable thing resolved by judgement because checking felt
unnecessary.** But the second half belongs with the first. All four surfaced *and* were
corrected inside the analysis, three because an explorer pushed back on a coordinator
instruction and the pushback was taken on evidence rather than rank. A coordinator who
defended the partition would have shipped a phantom dependency cycle. **This is a process
that caught itself four times, not one that failed four times** — and the difference is
entirely that the corrections came from agents willing to contradict the instruction they
were given.

Three method notes worth carrying forward:

- **Convergence is evidence of existence, not of reachability.** Two explorers and the
  coordinator independently rated the vectorizer twin a top finding; one grep on the
  caller set showed it is latent, because both callers are dead. Independent agreement
  raised confidence the coupling was real — which it is — and nobody checked whether
  anything traverses it.
- **A containment-based catalog check can locate a broken edge but cannot orient it.**
  Three of eight asymmetries inverted under source check. Every asymmetry needs one source
  read before a remedy is chosen.
- **Text grep manufactures phantom dependency edges.** Single-letter and common local
  names (`x`, `f`, `p`, `data`, `cfg`) matched inside function bodies and comment prose;
  three agents hit this independently. Attribute-level AST restricted to module-level
  symbols is the test that separates them — **sufficient for this codebase**, which is a
  single module with no dynamic dispatch in the walked ranges, and not a general recipe:
  it would still miss `getattr`, `**kwargs` forwarding and string-keyed dispatch.

One more, mechanical and easy to miss: **a merge race in an audit workflow preferentially
drops late-arriving evidence, and late-arriving evidence skews positive** — gaps are found
early by reading, defences are found late by checking whether something is tested. A merge
at 07:34 shipped a catalog missing the single strongest positive finding in the analysis
for half an hour.

---

## 8. Limitations

1. **No end-to-end run backs any severity rating.** No `--selftest`, `--preflight`,
   `--collect` or `--eval` was executed. The only runtime verification is the test suite
   (129 passed, zero skips, CUDA available) plus targeted micro-execution of isolated
   components. Severity *ordering* is graded Moderate for this reason; F6-above-F2 is the
   ranking most likely to be wrong, since an operator who never re-freezes never sees F6.
2. **The host-hash experiment remains unrun.** It is the only outstanding item that could
   change a finding's severity rather than its coverage tag: hash both hosts at
   construction and observe whether the lift path's prefixes actually agree.
3. **Dependency-matrix re-validation was in flight** when the diagrams were generated. A
   prior pass found 8 asymmetries (2 critical); all were fixed and re-derived by three
   independent AST walks, but the confirming pass had not returned.
4. **A known partition defect** — 9 of 15 boundaries cut mid-section. One phantom edge was
   caught and removed. The 1142 boundary is a confirmed *section-internal* case: the
   Fan Executor ↔ Data edge is real at citation level but intra-section under the author's
   map, so it **inflates apparent coupling** without hiding anything or inverting a
   direction.
5. **One entry (Plotting Sidecar) was analysed against a moving target** — the file was
   rewritten upstream mid-analysis and the entry was re-done against `aa86388`.
6. **Coverage ≠ correctness.** A `[COVERED]` tag means someone decided a behaviour was
   intended, not that the intent is sound.

---

## Companion documents

| Document | Lines | Contents |
|---|---|---|
| [`02-subsystem-catalog.md`](02-subsystem-catalog.md) | 974 | 9 subsystems, evidence-cited, AST-derived dependencies |
| [`03-diagrams.md`](03-diagrams.md) | 280 | C4 Context / Container / Component (rendered + inspected); host-hash experiment result |
| [`05-quality-assessment.md`](05-quality-assessment.md) | 485 | 11 root-cause clusters, cheap-fix table, coverage picture |
| [`11-simic-shaped-decomposition.md`](11-simic-shaped-decomposition.md) | 2,160 | Domain sockets, contract suite, Phase A lessons |
| [`12-contract-suite-audit.md`](12-contract-suite-audit.md) | 1,251 | Adversarial audit of the above, 11 findings |
| [`00-coordination.md`](00-coordination.md) | 1,304 | Every adjudication, every correction, full audit trail |
