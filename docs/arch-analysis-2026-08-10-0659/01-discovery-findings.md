# 01 — Discovery Findings

**Scope:** `experiments/` in the Simic repository
**Date:** 2026-08-10
**Method:** Directory scan, symbol extraction, module-docstring reading, spec
cross-reference, git history. No implementation files read in full by the
coordinator (delegated to explorers).

---

## 1. Directory Structure

```
experiments/
├── __init__.py               0 lines   (empty package marker)
├── kernel_demo.py        4,066 lines   (the entire demo)
├── kernel_demo_plots.py    150 lines   (plotting sidecar) ← SUPERSEDED, see below
└── __pycache__/                        (build artifact, cpython-314)
```

**Total at analysis start: 4,216 lines of Python across 3 source files.**

> **VERSION WARNING — the repository moved during this analysis.**
> This tree is as of `2b48431`, HEAD at session start (06:50:45). At **07:19:06** a
> concurrent session committed `853e9ef` *"kernel demo: plotting sidecar refuses to
> invent data (review fix pass)"*, which took `kernel_demo_plots.py` from **150 to
> 425 lines** and added `tests/unit/kernel_demo/test_plots.py` (193 lines, which did
> not exist at `2b48431` — verified with `git cat-file`). Further uncommitted edits
> to both landed at 07:21 (432 and 239 lines respectively).
>
> **`experiments/kernel_demo.py` is unaffected** — unmodified, mtime 06:51,
> `git diff --stat` empty. It is identical in the working tree and in HEAD. So
> 4,066 of the 4,216 analysed lines, and eight of the nine catalog entries, describe
> a stable artifact.
>
> **Only the Plotting Sidecar entry is stale** and is being re-done against the
> working tree with an explicit version anchor. Current repo total is ~4,498 lines.

Organization philosophy is **deliberate single-file monolith**, not accidental.
The module docstring (lines 1–33) declares a 17-section narrative order and states
the intent: *"one file, read top to bottom."* The spec
(`docs/superpowers/specs/2026-08-09-kernel-demo-design.md` line 4) names the target
as "single file, plus optional plotting sidecar", and line 574 gives the rationale:
*"A reader can open the one file and follow the whole loop top-to-bottom."*

This is the organizing principle: **narrative order over module boundaries.**
Section headers are comments (`# section 1 — IDENTITY AND CONFIG`), not packages.

## 2. Entry Points

| Entry point | Location | Purpose |
|---|---|---|
| `main(argv)` | `kernel_demo.py:4004` | Single CLI dispatcher, argparse-based |
| `worker_main(...)` | `kernel_demo.py:3063` | Spawned collection worker process |
| `run_selftest` | `:2061` | `--selftest` check battery (+ `--certify`) |
| `run_preflight` | `:2919` | `--preflight` 8-gate admission battery |
| `run_collect` | `:3132` | `--collect` parallel episode collection |
| `run_train` | `:3340` | `--train` policy training |
| `run_eval` | `:3425` | `--eval` comparator battery + verdict |
| `run_report` | `:3829` | `--report` result tables |
| `run_replay` | `:3925` | `--replay` bitwise replay + divergence localisation |
| plots CLI | `kernel_demo_plots.py` | Standalone; imports `SEED_NAMES`, `FanRecord`, `Store` |

The CLI is the **only** public surface. There is no library API, no HTTP route,
no importable façade beyond what the plotting sidecar consumes.

## 3. Technology Stack

- **Language:** Python, using 3.12+ generics syntax (`def semantic[T: ...]`) and
  PEP 695 type parameters. `__pycache__` shows **CPython 3.14**.
- **Core dependency:** `torch` (+ `torch.nn`). Neural training substrate.
- **Optional dependency:** `matplotlib` (sidecar only — the demo runs without it,
  by explicit design; `kernel_demo_plots.py:4`).
- **Standard library:** `argparse`, `contextlib`, `copy`, `dataclasses`, `enum`,
  `hashlib`, `inspect`, `json`, `math`, `os`, `platform`, `pathlib`, `subprocess`.
- **No framework.** No web server, no ORM, no DI container, no test framework
  imports in the module itself — verification is built in as `--selftest`.
- **Persistence:** JSONL shard files under a store root (default `runs/kernel_demo`).
  No database.
- **Dataset:** CIFAR (loaded via `load_data`, `:279`).

Notable: `inspect` and `hashlib` at module scope signal the self-certifying design
— the code hashes its own source sections and reflects on its own semantic surface.

## 4. Subsystem Identification

The author's own 17-section map (module docstring lines 10–27), consolidated into
**13 cohesive subsystems** and then grouped into **8 explorer scopes**:

| Author section | Lines (approx) | Cohesive subsystem |
|---|---|---|
| 1 identity & config | 44–251 | Identity, config & hashing |
| 7 determinism | 917–989 | Determinism controls |
| 2 data | 252–346 | Data & common-future |
| 3 telemetry | 347–554 | Telemetry & normalization |
| 8 episode | 990–1195 | Episode lifecycle |
| 4 host | 555–637 | Host network |
| 5 seeds | 638–768 | Seed delta contract |
| 6 slot lifecycle | 769–916 | Slot / blending / optimizer |
| 9 fan executor | 1196–1419 | Counterfactual fan executor |
| 10 records & store | 1420–1681 | Record schema & store |
| 11 policy | 1682–1801 | Policy network & deployment |
| 12 learning | 1802–1978 | Policy training objectives |
| 13 --selftest | 1979–2306 | Self-test battery |
| 14 --preflight | 2307–3062 | Gate battery & freeze manifest |
| 15–17 CLI | 3063–4066 | Run orchestration & reporting |

## 5. Architectural Character (hypotheses for explorers to confirm/refute)

Four properties distinguish this from an ordinary training script. Each is a
**hypothesis** based on symbol names and the module docstring — explorers must
verify against implementation.

1. **Self-certifying / spec-bound.** `semantic()` (`:60`) and `semantic_const()`
   (`:71`) register a "semantic surface"; `config_hash()` (`:231`) and
   `frozen_block_hash()` (`:226`) bind configuration to identity. Hypothesis: the
   code can prove which version of itself produced a result.
   **CORRECTED by explorer 7:** `_section_source()` (`:2052`) does **not** hash —
   it slices source text between `# section N` markers and is used solely to grep
   for `nn.init.` in sections 4/5/11 (`:2159–2162`). Hashing is `config_hash()`
   over `inspect.getsource` of the semantic surface, a different mechanism. Note
   also that `certified.json` (`:2297`) records `git_rev` and results but **not**
   `config_hash`, so the certificate's code binding rests on `_worktree_clean()`
   + HEAD equality rather than on the semantic hash.

2. **Determinism spine.** `derive()` (`:101`), `make_generator()` (`:112`),
   `rng_scope()` (`:123`), `enable_class1()` (`:917`), `state_hash()` (`:933`),
   `env_block()` (`:969`). Hypothesis: labelled seed derivation plus scoped RNG
   plus zero-normalized state hashing yields bitwise reproducibility, exposed via
   `--replay`.

3. **Typed failure classes.** `TelemetryDivergence` (`:347`), `TwinDivergence`
   (`:1196`), `SplitViolation` (`:1420`). Hypothesis: distinct failure modes are
   distinguishable rather than collapsed into generic exceptions.

4. **Admission gate battery.** Eight named gates (`gate1_noop_sanity` `:2547`
   through `gate8_pressure` `:2759`), plus `freeze_manifest()` (`:2848`),
   `_git_rev()` (`:2829`), `_worktree_clean()` (`:2835`),
   `write_divergence_report()` (`:3034`). Hypothesis: a run cannot be certified
   unless it passes a pre-registered battery against a clean worktree.

## 6. Relationship to the Parent Project

The demo is **explicitly not** Simic proper. Module docstring lines 3–7:

> *"Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
> exactly what Simic proper rejects (generation from live host state). This demo
> proves the substrate loop and the counterfactual-fan supervision economics, not
> generative morphogenesis."*

Consequences for this analysis:

- The repo's Namespec 2.0 naming constitution and 14-domain vocabulary **do not
  govern** this code. Explorers use the author's own section names.
- The demo is a **falsification instrument** for the parent programme's central
  economic claim, not a prototype of its architecture.
- Governing spec is rev 6.1 (LOCKED). Docstring says "rev 6"; the spec was amended
  to 6.1 on 2026-08-10 (episode-level money null + falsifier CI). **Possible stale
  docstring reference — flagged for the quality pass.**

## 7. Git Context

Recent history is a disciplined spec-driven-development sequence: numbered tasks
(Task 17, Task 18), a review fix wave, an SME role-review wave (pytorch,
determinism, statistics, morphogenesis), then the rev 6.1 pre-data amendment.
Merged to `main` via PR #9 (`2b48431`).

Design and review corpus exists at:
- `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (581 lines, LOCKED rev 6.1)
- `docs/superpowers/plans/2026-08-09-kernel-demo.md`
- Six review documents under `docs/superpowers/reviews/`

## 8. Known Coordinator-Verified Facts

- `_worktree_clean()` (`:2835`) runs `git status --porcelain` and returns True only
  on empty output. **Verified by reading lines 2835–2841.** Implication: this
  analysis workspace, while uncommitted, will make any certified run fail preflight.
- Spec line 560 sets a target of "≲1200 lines"; the file is 4,066 lines — **3.4×
  the stated budget.** Verified by `wc -l` and grep of the spec.

## 9. Gaps and Limitations

- ~~No `tests/` coverage for `experiments/` was located during discovery.~~
  **CORRECTED 2026-08-10 08:05 — this was a coordinator discovery error.**
  An external pytest suite exists at `tests/unit/kernel_demo/`: **20 Python files,
  1,828 LOC**, including `conftest.py`, `helpers.py`, and 17 test modules
  (`test_data`, `test_derive`, `test_determinism`, `test_episode`, `test_eval_stats`,
  `test_fan`, `test_host`, `test_learning`, `test_policy`, `test_preflight_gates`,
  `test_report`, `test_seeds`, `test_selftest`, `test_slot`, `test_store`,
  `test_telemetry`, `test_collect`). Verification is therefore **two-layer**:
  external pytest *plus* in-band `--selftest`, not in-band only.
  Raised by explorer 6; coordinator-verified by `ls` + `wc`. Explorer 7's entry
  states the opposite ("verification is entirely in-band") and **must be amended** —
  it also means explorer 7's coverage conclusions were drawn against only half the
  verification surface.
- The coordinator has not read implementation bodies. All Section 5 claims are
  hypotheses pending explorer verification.
- Runtime behaviour is not observed — this is static analysis only. No run of
  `--selftest` or `--preflight` was performed.
