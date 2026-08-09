# Kernel Demo ("Simic in 20 minutes") Implementation Plan — rev 2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `experiments/kernel_demo.py` — a single-file tech demo where a learned transformer policy (Aurelia) reads host telemetry, decides when to inject which of four fixed seeds into one slot of an undersized CIFAR-10 CNN, and is trained/scored against matched counterfactual fans — per the LOCKED spec `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 6, commit 98083fd).

**Architecture:** One narrative-ordered Python file (~1200 lines, aspirational — never compress state-restoration or statistical logic to hit it): constants/derive → data + common future → telemetry → host + pathologies → seeds (delta contract) → slot lifecycle → determinism → episode/fan executor → store → policy → learning → modes. A standalone plotting sidecar `experiments/kernel_demo_plots.py` (own CLI; reads outputs, never called by the main file). Tests in `tests/unit/kernel_demo/`.

**Tech Stack:** Python ≥3.14, torch 2.13.0+cu130 (installed, CUDA verified on 2× RTX 4060 Ti), torchvision 0.28 (added in Task 1), pytest. No other runtime deps.

**Plan provenance (rev 2):** ten-reviewer panel (reality, architecture, QA, systems, solution, python, test-suite, pytorch, training-config, nn-arch) plus two owner-relayed external reviews. All accepted findings are folded in; the register below records every deliberate deviation from the spec's letter.

## Global Constraints (inherited by every task)

- **The spec is LOCKED.** Any deviation discovered during implementation is surfaced to the user, never silently patched. The spec file is the tiebreaker for every ambiguity. Known, surfaced deviations live in the Deviations Register below — nothing else may deviate.
- Class 1 determinism: `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`, `cudnn.benchmark=False`, `CUBLAS_WORKSPACE_CONFIG=:4096:8` **force-set, or hard-fail if the environment pre-set a different value** (never `setdefault`). TF32 off both flags. No AMP, no dropout, no gradient clipping, **no `torch.compile`** (added to the forbidden-relaxations list).
- `attn` seed and the policy trunk: explicit-matmul attention only — no `F.scaled_dot_product_attention`.
- RNG ownership: every draw comes from a named `torch.Generator`; `torch.manual_seed` only at process startup. `nn.Module` constructors consume *global* RNG in `reset_parameters()`, so **all model construction happens inside `rng_scope(gen)`** (Task 1) — the scope swaps the global stream for the named generator's and restores it after.
- Hashing: **one primitive, `state_hash`, which canonicalizes signed zero (−0.0 → +0.0) before hashing.** Rationale: the STE add `h + (Δ − Δ.detach())` flips `−0.0` elements of `h` to `+0.0` (IEEE 754), which is value-invisible but byte-visible; and the spec's null-seed contingency names zero-normalized hashing as its mechanism. All "bitwise" claims in this plan mean *bitwise modulo signed-zero canonicalization*.
- Test-data wall (absolute, from spec rev 6): anything whose result can change the frozen block reads **val**; **test is unread until after freeze**. Concretely: `--selftest` and `--preflight` run with `read_test=False` (`R_test=None` in their records). Collection and eval run post-freeze and record both units per spec.
- Harness constants live in `Config`; the frozen set is `FROZEN_FIELDS` (Task 1) and now includes the policy-training schedule and every gate threshold. `n_collect` is deliberately **not** frozen (the spec's "extend collection pre-eval" lever requires it).
- Commit after every task; pre-commit runs ruff (`E,W,F,I,N,UP,B,C4,SIM,RUF`, only E501 ignored — so no semicolon-joined statements, no lambda assignment, no unused imports) and strict mypy. All plan code blocks are lint-clean as shown.
- Tests pass on CPU (CI-safe). **CPU-green is a necessary logic gate, not a sufficient gate for the Class-1 bitwise claim** — only the GPU phases certify determinism, and any code change to sections 4/5/6/8/9 after a GPU selftest voids that certification until it is re-run.
- Code tasks (1–18) build and CPU-verify everything first. **All GPU work happens in the Operational Phases section after Task 18** — nothing freezes until the code is finished (see Phase B).

## Deviations Register (surfaced, not silent)

| # | Deviation from spec letter | Rationale |
|---|---|---|
| D1 | Gate 1 is an engineering sanity check with pre-stated empirical thresholds, not a binomial test vs 20% | At ~7–8 episodes/pathology a binomial has no power in either direction (cannot reject 20% downward at α=0.05 even on zero wins); headline-scale statistics are not spent on a sampler shakedown. Thresholds are frozen Config fields. |
| D2 | `--selftest`/`--preflight` never read the test partition (`R_test=None` pre-freeze), though spec fan-step 7 says arms record both units | The spec's own absolute unit rule ("test is unread until after freeze") outranks fan-step 7's letter for pre-freeze runs. Post-freeze collection records both units per spec. |
| D3 | `TelemetryRecord` gains two fields the spec's list omits: `per_class_val_acc_std` and `confusion_entropy` | The spec's own pathology table promises a "class-confusion spread" signature for `no_spatial_mix`, but its telemetry list contains no confusion statistic — the policy could never see the signal the experiment assigns to that pathology. Neutral measurements, blindness-rule-compliant. **Flagged for owner acknowledgment.** |
| D4 | `--report` writes canonical JSON/tables only; the plotting sidecar is a standalone CLI reading those outputs | Keeps the import direction acyclic (sidecar imports kernel_demo for dataclasses only; kernel_demo never imports the sidecar). |
| D5 | `experiments/` at repo root, though `ops/repo-structure.md` nests experiments under `src/simic/` | Spec-pinned placement for a deliberately-not-Simic standalone demo. Acknowledged exception, not drift. |
| D6 | Report/eval "refuse mixed namespaces" implemented as "refuse mixed **freeze-manifest hashes** / generations" | A complete store legitimately contains preflight+train+tune+eval records; the real invariant is that no number mixes generations and no train record enters an eval estimand. |
| D7 | Host widths are 24/64/80 (healthy), not a literal reading of "3-stage ~150k" with 32/64/128 | 32/64/128 double-conv is ~289k (computed), ~2× the spec's ~150k. 24/64/80 double-conv = ~162k, and stage2's output is pinned at 64 so the slot interface is constant. Numbers in Task 4. |

## File Structure

- `experiments/kernel_demo.py` — the deliverable. Sections: 1 constants+derive+rng_scope, 2 data+future, 3 telemetry, 4 host, 5 seeds, 6 slot/lifecycle, 7 determinism+hashing, 8 episode, 9 fan, 10 store, 11 policy, 12 learning, 13 modes/CLI. Sections 1–12 are additive per task; **the CLI section is touched by Tasks 13–17 in their own subparser branch only** — never edit another mode's wiring.
- `experiments/kernel_demo_plots.py` — standalone matplotlib CLI; imports FROM kernel_demo (dataclasses only).
- `experiments/__init__.py`, `tests/unit/__init__.py`, `tests/unit/kernel_demo/__init__.py`.
- `tests/unit/kernel_demo/conftest.py` (shared fixtures, from Task 8), `helpers.py` (synthetic fans, from Task 12), and `test_{derive,data,telemetry,host,seeds,slot,determinism,episode,fan,store,policy,learning,selftest,preflight_gates,collect,eval_stats,report}.py`.

## Execution Model

**Code phase (Tasks 1–18):** pure build, CPU-tested, subagent-friendly, one commit per task. Interim line-count checks at Tasks 6/10/14 commits (`wc -l experiments/kernel_demo.py`; budgets ~500/~850/~1150 — aspirational; overruns are addressed by tighter code in the responsible section, never by splitting the file).

**Operational phases (after Task 18, in order; never interleaved with code changes):**

- **Phase A — Certify:** full unit suite; `selftest --device cuda:0` (Class-1 certification); `wardline scan . --fail-on ERROR`; mypy/ruff; final implementation commit; clean worktree.
- **Phase B — Preflight & freeze:** dry-run preflights (unfrozen, `preflight_iter` records, sampler tuning per gate remedies — note: the gate-4 "menu balance" remedy is a **Task 5 reopen** (param-budget tests, Tasks 6–13 re-verification, Phase A re-run), not an in-place knob; price it before reaching for it). When gates pass at the final code commit: `preflight --freeze` writes the FreezeManifest — refused unless all gates `ok`, worktree clean, and HEAD == the Phase-A commit.
- **Phase C — Collect:** overnight, idempotent, resumable, halt-on-twin-divergence (all workers).
- **Phase D — Train:** offline, consumes frozen temperatures.
- **Phase E — Eval:** ONE SHOT, code-guarded.
- **Phase F — Report & replay spot-check.**

**After freeze, any behavioral source change creates a new run generation** (new manifest hash); records from different generations never mix in one number.

---

### Task 1: Dependencies, skeleton, derive(), rng_scope, Config

**Files:**
- Modify: `pyproject.toml` — three edits: add `torchvision` dependency (`uv add torchvision`); change `[tool.pytest.ini_options] pythonpath = ["src"]` to `pythonpath = ["src", "."]` (without this, **no test in this plan can import `experiments.kernel_demo`** — verified empirically); add
  ```toml
  [[tool.mypy.overrides]]
  module = "torchvision.*"
  ignore_missing_imports = true
  ```
  (torchvision ships no py.typed; strict mypy hard-fails otherwise — verified).
- Create: `experiments/__init__.py`, `experiments/kernel_demo.py`, `tests/unit/__init__.py`, `tests/unit/kernel_demo/__init__.py`, `tests/unit/kernel_demo/test_derive.py`

**Interfaces:**
- Produces: `derive(seed: int, *labels: str | int) -> int` (uint64; **length-prefixed encoding**, no delimiter collisions), `make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator` (**no modulo mask** — `manual_seed` accepts full uint64, verified), `rng_scope(gen)` context manager (swaps global RNG state for the generator's; restores both on exit; makes `nn.Module` constructors draw from named streams), `@dataclass(frozen=True) Config`, `FROZEN_FIELDS`, `frozen_block_hash(cfg) -> str`, `main()` with the seven subcommands stubbed. `main()`'s **first statement** is `enable_class1()` (defined Task 7; stub as no-op until then).

- [ ] **Step 1: Add torchvision + pyproject edits** — apply all three pyproject changes above; `uv run python -c "import torchvision; print(torchvision.__version__)"` prints a version. If uv cannot resolve, STOP and report.
- [ ] **Step 2: Write the failing tests**

```python
# tests/unit/kernel_demo/test_derive.py
import dataclasses

import torch

from experiments.kernel_demo import (
    Config,
    derive,
    frozen_block_hash,
    make_generator,
    rng_scope,
)


def test_derive_deterministic_label_sensitive_no_delimiter_collision():
    assert derive(1, "a") == derive(1, "a")
    assert derive(1, "a") != derive(1, "b")
    assert derive(1, "a", 0) != derive(1, "a", 1)
    assert derive(1, "a:b", "c") != derive(1, "a", "b:c")  # length-prefixed
    assert 0 <= derive(123, "x") < 2**64


def test_generator_hermetic_full_range():
    a = torch.rand(4, generator=make_generator(derive(7, "g")))
    b = torch.rand(4, generator=make_generator(derive(7, "g")))
    assert torch.equal(a, b)
    make_generator(2**64 - 1)  # full uint64 accepted, no mask


def test_rng_scope_isolates_global_stream():
    before = torch.get_rng_state()
    with rng_scope(make_generator(derive(9, "scope"))):
        torch.nn.Linear(4, 4)  # constructor draws inside the scope
    assert torch.equal(before, torch.get_rng_state())


def test_rng_scope_reproducible_construction():
    def build():
        with rng_scope(make_generator(derive(9, "build"))):
            return torch.nn.Linear(8, 8)

    w1, w2 = build().weight, build().weight
    assert torch.equal(w1, w2)


def test_frozen_hash_covers_policy_and_gate_knobs():
    c = Config()
    assert frozen_block_hash(c) == frozen_block_hash(Config())
    for f in ("lam", "policy_lr", "warmup_frac", "gate4_dominance_max"):
        changed = dataclasses.replace(c, **{f: getattr(c, f) * 2})
        assert frozen_block_hash(changed) != frozen_block_hash(c)


def test_n_collect_not_frozen():
    c = Config()
    more = dataclasses.replace(c, n_collect=400)  # the spec's extension lever
    assert frozen_block_hash(more) == frozen_block_hash(c)
```

- [ ] **Step 3: Run** `uv run pytest tests/unit/kernel_demo/test_derive.py -v` — FAIL (ImportError).
- [ ] **Step 4: Implement**

```python
# experiments/kernel_demo.py — section 1
"""Kernel Demo — "Simic in 20 minutes".

Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
exactly what Simic proper rejects (generation from live host state). This
demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis.

Spec (LOCKED, rev 6): docs/superpowers/specs/2026-08-09-kernel-demo-design.md
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
from collections.abc import Iterator
from dataclasses import dataclass

import torch


def derive(seed: int, *labels: str | int) -> int:
    h = hashlib.sha256()
    h.update(seed.to_bytes(8, "big"))
    for label in labels:
        part = str(label).encode()
        h.update(len(part).to_bytes(4, "big"))
        h.update(part)
    return int.from_bytes(h.digest()[:8], "big")


def make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator:
    g = torch.Generator(device=device)
    g.manual_seed(seed)  # full uint64 accepted; do NOT mask (seed aliasing)
    return g


@contextlib.contextmanager
def rng_scope(gen: torch.Generator) -> Iterator[None]:
    # nn.Module constructors draw from the GLOBAL stream in reset_parameters();
    # this scope makes those draws come from the named generator instead,
    # and leaves the process-global stream untouched afterwards.
    prior = torch.get_rng_state()
    torch.set_rng_state(gen.get_state())
    try:
        yield
    finally:
        gen.set_state(torch.get_rng_state())
        torch.set_rng_state(prior)


@dataclass(frozen=True)
class Config:
    # --- frozen block: lifecycle + reward ---
    tau: float = 0.05
    tau_eps: float = 1e-6
    lam: float = 1.0
    stage_k: int = 3
    stage_m: int = 3
    stage_f: int = 2
    horizon: int = 40
    window: tuple[int, int] = (5, 15)  # inclusive on BOTH ends
    t_star: int = 10
    lr: float = 0.05
    momentum: float = 0.9
    wd: float = 5e-4
    seed_lr: float = 0.05
    diverged_r: float = 0.10
    fans_per_episode: int = 2
    # --- frozen block: statistics ---
    n_preflight: int = 30
    n_eval: int = 100
    alpha_level: float = 0.05
    permutation_resamples: int = 10_000
    beta_which_frac: float = 0.2
    beta_now_div: float = 2.2
    # --- frozen block: gate thresholds (2x/0.5x are plan-chosen, surfaced) ---
    gate1_min_mild_noop_wins: int = 2
    gate2_probe_min_acc: float = 0.5
    gate3_contrast_mult: float = 2.0
    gate4_dominance_max: float = 0.40
    gate5_rms_band: float = 2.0
    gate6_late_density_mult: float = 0.5
    # --- frozen block: policy training schedule (selects the checkpoint) ---
    policy_lr: float = 1e-3
    policy_batch_size: int = 64
    policy_steps: int = 4000
    warmup_frac: float = 0.3
    # --- NOT frozen ---
    n_collect: int = 300  # spec's "extend collection pre-eval" lever
    d_model: int = 64
    n_layers: int = 2
    tune_frac: float = 0.2
    batch_size: int = 128
    run_seed: int = 20260809


FROZEN_FIELDS: tuple[str, ...] = (
    "tau", "tau_eps", "lam", "stage_k", "stage_m", "stage_f", "horizon",
    "window", "t_star", "lr", "momentum", "wd", "seed_lr", "diverged_r",
    "fans_per_episode", "n_preflight", "n_eval", "alpha_level",
    "permutation_resamples", "beta_which_frac", "beta_now_div",
    "gate1_min_mild_noop_wins", "gate2_probe_min_acc", "gate3_contrast_mult",
    "gate4_dominance_max", "gate5_rms_band", "gate6_late_density_mult",
    "policy_lr", "policy_batch_size", "policy_steps", "warmup_frac",
)


def frozen_block_hash(cfg: Config) -> str:
    lines = sorted(f"{k}={getattr(cfg, k)!r}" for k in FROZEN_FIELDS)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


MODES = ("selftest", "preflight", "collect", "train", "eval", "report", "replay")


def enable_class1() -> None:  # full body lands in Task 7
    pass


def main(argv: list[str] | None = None) -> None:
    enable_class1()  # MUST be the first statement of every process
    ap = argparse.ArgumentParser(prog="kernel_demo")
    sub = ap.add_subparsers(dest="mode", required=True)
    for m in MODES:
        p = sub.add_parser(m)
        p.add_argument("--store", default="runs/kernel_demo")
        if m == "replay":
            p.add_argument("fan_id")
    args = ap.parse_args(argv)
    raise SystemExit(f"not implemented: {args.mode}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests** — PASS. Also `uv run python -m experiments.kernel_demo selftest` → `not implemented: selftest`.
- [ ] **Step 6: Commit.**

---

### Task 2: Data — partition, GPU residency, CommonFuture, augmentation

**Files:**
- Modify: `experiments/kernel_demo.py` (section 2)
- Create: `tests/unit/kernel_demo/test_data.py`

**Interfaces:**
- Consumes: `derive`, `make_generator`, `Config`.
- Produces:
  - `split_indices(run_seed: int) -> tuple[Tensor, Tensor]` — pure function returning (train_idx 45k, val_idx 5k) as a fixed permutation of the official 50k train split; unit-testable without a download.
  - `@dataclass DataBundle` (fields on separate lines: `train_x/train_y` uint8 `[45000,3,32,32]`/int64, `val_x/val_y` `[5000,…]`, `test_x/test_y` `[10000,…]` = the official 10k, untouched); `load_data(cfg, device, subset=None) -> DataBundle` (torchvision CIFAR10 into `runs/data`; uses `split_indices`; a local `def to_device(t)` — **no lambda assignment**, E731 is live in this repo).
  - `@dataclass CommonFuture`: `order` int64 **`[E, S*B]`** (flat per-epoch sample indices — S steps × B batch, reshaped by the consumer), `crops` uint8 `[E,S,B,2]` (offsets 0–8), `flips` bool `[E,S,B]`, `epochs`, `hash` (sha256 over the three tensors' bytes); `CommonFuture.draw(seed, n_train, epochs, cfg)` — all draws from one `make_generator(seed)`.
  - `augment(x_u8, crops, flips) -> Tensor` — float32 normalize (`CIFAR_MEAN/STD`), reflect-pad-4, per-sample crop via advanced indexing, per-sample flip. Pure; consumes no RNG. (This exact implementation was executed and verified correct by review — keep it verbatim from rev 1, minus the lambda.)

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_data.py
import torch

from experiments.kernel_demo import CommonFuture, Config, augment, split_indices


def test_split_indices_partition_invariants():
    tr, va = split_indices(Config().run_seed)
    assert tr.shape == (45_000,) and va.shape == (5_000,)
    assert len(set(tr.tolist()) & set(va.tolist())) == 0
    tr2, va2 = split_indices(Config().run_seed)
    assert torch.equal(tr, tr2) and torch.equal(va, va2)


def test_common_future_deterministic_hash_sensitive_and_shapes():
    cfg = Config()
    a = CommonFuture.draw(42, n_train=1024, epochs=3, cfg=cfg)
    b = CommonFuture.draw(42, n_train=1024, epochs=3, cfg=cfg)
    c = CommonFuture.draw(43, n_train=1024, epochs=3, cfg=cfg)
    assert a.hash == b.hash and torch.equal(a.order, b.order)
    assert a.hash != c.hash
    steps = 1024 // cfg.batch_size
    assert a.order.shape == (3, steps * cfg.batch_size)  # [E, S*B], flat
    assert a.crops.shape == (3, steps, cfg.batch_size, 2)
    assert int(a.crops.max()) <= 8 and int(a.crops.min()) >= 0


def test_augment_pure_function_no_rng():
    x = torch.randint(0, 256, (4, 3, 32, 32), dtype=torch.uint8)
    crops = torch.tensor([[0, 0], [8, 8], [4, 4], [2, 6]], dtype=torch.uint8)
    flips = torch.tensor([True, False, True, False])
    state = torch.get_rng_state()
    y1 = augment(x, crops, flips)
    y2 = augment(x, crops, flips)
    assert torch.equal(state, torch.get_rng_state())
    assert torch.equal(y1, y2)
    assert y1.shape == (4, 3, 32, 32) and y1.dtype == torch.float32
    assert not torch.equal(y1, augment(x, crops, ~flips))
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement** (rev 1's `augment` body verbatim; `load_data` uses `split_indices` and a named `to_device` function). **Step 4: Run** — PASS. **Step 5: Commit.**

---

### Task 3: TelemetryRecord, collection, Normalizer

**Files:** modify section 3; create `tests/unit/kernel_demo/test_telemetry.py`.

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) TelemetryRecord` — fields: `epoch, train_loss, val_loss, val_acc, train_loss_delta, val_loss_delta, grad_norm_mean (3-tuple), grad_norm_var (3-tuple), act_saturation (3-tuple), weight_norm (3-tuple),` **`per_class_val_acc_std: float, confusion_entropy: float`** (Deviations Register D3 — the no_spatial_mix signature the spec's pathology table promises). `__post_init__` asserts all finite → `TelemetryDivergence`. No other fields, ever (blindness rule).
  - `TELEMETRY_DIM = 20`; `EPOCH_FEATURE_IDX = 0`; `record_to_vector(r) -> Tensor[20]` (field order, epoch first).
  - `class Normalizer` (median/IQR; `fit`, `apply`, `to_json`/`from_json`, and `Normalizer.identity()` classmethod for tests).
  - `confusion_stats(logits, labels, n_classes=10) -> tuple[float, float]` — per-class accuracy std and off-diagonal confusion-row entropy (neutral measurements; no argmax-of-pathology anywhere).

- [ ] **Step 1: Failing tests** — rev 1's three tests updated for the two new fields (`TELEMETRY_DIM == 20`), plus:

```python
def test_confusion_stats_separate_uniform_from_structured():
    g = torch.Generator().manual_seed(0)
    labels = torch.arange(10).repeat(50)
    perfect = torch.nn.functional.one_hot(labels, 10).float() * 10
    confused = perfect.clone()
    confused[labels == 3] = torch.nn.functional.one_hot(
        torch.full((50,), 5), 10
    ).float() * 10  # class 3 always mispredicted as 5
    std_p, ent_p = confusion_stats(perfect, labels)
    std_c, ent_c = confusion_stats(confused, labels)
    assert std_c > std_p
    assert ent_c < 2.0  # concentrated confusion, low row entropy
    _ = g  # silence unused warning if fixture unused
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 4: Host CNN and the four pathologies — fixed 64-wide slot interface

**Files:** modify section 4; create `tests/unit/kernel_demo/test_host.py`.

**Interfaces:**
- Produces:
  - `PATHOLOGIES = ("under_normalized", "channel_starved", "no_spatial_mix", "mild")`; `DESIGNED_WINNER = {"under_normalized": "norm", "channel_starved": "conv_heavy", "no_spatial_mix": "attn", "mild": "conv_light"}`.
  - `class Host(nn.Module)` — 3 stages of Conv-BN-ReLU ×2 + `MaxPool2d(2)`; GAP is **`nn.AdaptiveAvgPool2d(1)`** (the documented deterministic-backward case); linear(→10). **Healthy widths 24/64/80** (D7: 32/64/128 double-conv computes to ~289k; 24/64/80 ≈ 162k ≈ spec's ~150k). **The slot sits after stage2's pool**, so slot input is `[B, 64, 8, 8]` for every pathology — **INVARIANT: no pathology may change stage2's output width (64) or spatial size (8×8)**; pathologies alter internal capacity only:
    - `under_normalized`: same widths, all BN → Identity, init gain ×2.
    - `channel_starved`: stage2 internally bottlenecked (conv1 24→24, conv2 24→64) — starved capacity, 64 out.
    - `no_spatial_mix`: stage2 convs 1×1 (24→64 via 1×1s), 64 out.
    - `mild`: stage1/stage3 reduced to 20/72 (stage2 untouched: 20→64, 64→64) ≈ 142k.
  - `host.feat_channels == 64` (constant, all pathologies), `host.forward_to_slot(x) -> Tensor` (stops at the slot site — this is how `germinate` obtains τ-init features; `Host.forward(x, slot)` alone cannot, it returns logits), `host.stage_modules()`, stat hooks, `host_init_hash = state_hash` alias.
  - `build_host(pathology, init_seed) -> Host` — constructed inside `rng_scope(make_generator(init_seed))`.
  - Note: `Slot` is forward-referenced (`slot: "Slot | None"`) under PEP 563 (`from __future__ import annotations`, present since Task 1); Task 6 defines it; `Host.forward` only needs `slot is None` / `slot(h)` at runtime.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_host.py
import torch

from experiments.kernel_demo import PATHOLOGIES, build_host, host_init_hash


def test_all_pathologies_forward_and_param_range():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        out = h(torch.randn(2, 3, 32, 32), slot=None)
        assert out.shape == (2, 10)
        n = sum(q.numel() for q in h.parameters())
        assert 80_000 < n < 250_000, (p, n)  # ALL four, not one representative


def test_slot_interface_invariant_all_pathologies():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        feats = h.forward_to_slot(torch.randn(2, 3, 32, 32))
        assert feats.shape == (2, 64, 8, 8), p  # fixed width AND spatial
        assert h.feat_channels == 64


def test_init_hash_is_seed_function():
    assert host_init_hash(build_host("mild", 5)) == host_init_hash(build_host("mild", 5))
    assert host_init_hash(build_host("mild", 5)) != host_init_hash(build_host("mild", 6))


def test_pathology_structure():
    un = build_host("under_normalized", 1)
    assert not any(isinstance(m, torch.nn.BatchNorm2d) for m in un.modules())
    nm = build_host("no_spatial_mix", 1)
    s2 = [m for m in nm.stage2.modules() if isinstance(m, torch.nn.Conv2d)]
    assert all(m.kernel_size == (1, 1) for m in s2)


def test_construction_does_not_touch_global_rng():
    before = torch.get_rng_state()
    build_host("mild", 7)
    assert torch.equal(before, torch.get_rng_state())
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 5: Seeds — delta contract, τ-init, decay groups

**Files:** modify section 5; create `tests/unit/kernel_demo/test_seeds.py`.

**Interfaces:**
- Produces:
  - `SEED_NAMES = ("norm", "attn", "conv_light", "conv_heavy")`; `class SeedDelta(nn.Module)` (`gain` scalar param init 0 pre-τ; `forward(h) = gain * self.f(h)`; `f` abstract). Pinned architectures at C=64 (reviewer-computed):
    - `NormSeed`: `f = GroupNorm(8, 64)(h) − h` (129 params).
    - `AttnSeed`: LN → explicit-matmul single head, qkv/out `Linear(64,16)`×3 + `Linear(16,64)` (~4.2k). 64 spatial tokens (8×8, guaranteed by Task 4's invariant).
    - `ConvLightSeed`: depthwise 3×3 + pointwise **mid=64** + BN + ReLU + pointwise (8,897 — MobileNet-style mid=16/32 would fail the budget test at 2,657/4,737).
    - `ConvHeavySeed`: 3×3 BN ReLU 3×3 BN with **bottleneck Cb=52** (60,137 ≈ spec's ~60k; valid band Cb∈[31,77]).
  - Internal projections standard-init (inside `rng_scope`), final BN γ=1; only the gain carries τ.
  - `tau_init(seed, host_feats, cfg) -> float` — **caller provides `host_feats` from `host.forward_to_slot` under `host.eval()`/`no_grad`** (host BN protection); the measurement runs the seed **in `train()` mode under `no_grad`** — the mode of its first TRAINING step, so the calibrated ratio is the ratio TRAINING actually starts at (BN-carrying seeds differ between modes; eval-mode calibration would make the RMS test spuriously fail and the equal-entry claim false). Seed BN buffers mutated by the measurement batch are part of birth state (deterministic; same fixed batch every arm). ε-floor on `RMS(f0)`; returns `g` for logging.
  - `split_decay_groups(module) -> tuple[list[tuple[str, Tensor]], list[tuple[str, Tensor]]]` — **rule: `param.ndim <= 1 or name.endswith("gain") → no-decay`** (exactly coextensive with the spec's list — gain, norm affines, biases — and robust to `nn.Sequential` integer names, where a substring rule silently mis-files BN affines).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_seeds.py
import pytest
import torch

from experiments.kernel_demo import Config, SEED_NAMES, build_seed, split_decay_groups, tau_init


@pytest.mark.parametrize("name", SEED_NAMES)
def test_delta_zero_before_tau_init(name):
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(2, 64, 8, 8)
    assert torch.equal(s(h), torch.zeros_like(h))


@pytest.mark.parametrize("name", SEED_NAMES)
def test_tau_init_hits_target_rms_in_training_mode(name):
    cfg = Config()
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(16, 64, 8, 8)
    g = tau_init(s, h, cfg)
    assert g != 0.0
    with torch.no_grad():  # measure in the SAME mode tau_init calibrated:
        s.train()          # train-mode BN, matching the first TRAINING step
        ratio = s(h).pow(2).mean().sqrt() / h.pow(2).mean().sqrt()
    assert abs(ratio.item() - cfg.tau) / cfg.tau < 0.05


def test_param_budgets_pinned():
    counts = {n: sum(p.numel() for p in build_seed(n, 64, 1).parameters()) for n in SEED_NAMES}
    assert counts["norm"] < 300
    assert 2_000 < counts["attn"] < 12_000
    assert 5_000 < counts["conv_light"] < 20_000
    assert 35_000 < counts["conv_heavy"] < 90_000


def test_no_decay_rule_catches_sequential_bn_affines():
    s = build_seed("conv_heavy", 64, 1)
    decay, no_decay = split_decay_groups(s)
    no_decay_names = {n for n, _ in no_decay}
    assert any(n.endswith("gain") for n in no_decay_names)
    bn_weights = [
        n for n, m in s.named_modules() if isinstance(m, torch.nn.BatchNorm2d)
    ]
    assert bn_weights, "fixture must contain BN"
    for n, p in decay:
        assert p.ndim > 1, f"1-d param {n} leaked into decay group"
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 6: Slot lifecycle — STE, α/β schedules, trust region, optimizer contract

**Files:** modify section 6; create `tests/unit/kernel_demo/test_slot.py`.

**Interfaces:** as rev 1, with corrections:
- `Slot.forward` comment corrected: `hin = h.detach()*(1-β) + h*β` is **value-equal to h always, bitwise-equal only at β ∈ {0, 1}** — FOSSILIZING's fractional β is a numerically-close, non-bitwise blend by design (post-TRAINING, outside every bitwise assertion window).
- `Slot.rms_ratio() -> float` — named owner of the blend-entry measurement (`RMS(last_delta)/RMS(last_h)`), called by the fan executor at the first BLENDING step, recorded into `ArmResult.rms_ratio_blend_entry`.
- `build_optimizer(host, cfg)` (SGD Nesterov, decay/no-decay via `split_decay_groups`), `append_seed_group(opt, seed, cfg)`.
- Stage/α/β tick machinery per spec (cosine, per-step).
- Trust-region loss as rev 1 (`cfg.lam * last_delta.pow(2).mean() / last_h.detach().pow(2).mean().clamp_min(1e-12)`).

- [ ] **Step 1: Failing tests** — rev 1's suite plus the missing BLENDING seed-gradient assertion:

```python
def test_blending_trains_the_seed_while_host_gradient_stays_isolated():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha, slot.beta = 0.5, 0.0
    slot(h).sum().backward()
    assert torch.allclose(h.grad, torch.ones_like(h))  # beta=0: input detached
    g = slot.seed.gain.grad
    assert g is not None and g.abs().item() > 0  # BLENDING must TRAIN the seed
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit + `wc -l experiments/kernel_demo.py` (budget ~500).**

---

### Task 7: Determinism — Class 1 knobs, zero-normalized hashing, env block, config_hash

**Files:** modify section 7; create `tests/unit/kernel_demo/test_determinism.py`.

**Interfaces:**
- `enable_class1()` — real body: `CUBLAS_WORKSPACE_CONFIG` **force-set to `:4096:8`; if pre-set to anything else, raise** (a silently-tolerated stray value is a Class-1 relaxation with no error); deterministic algorithms, cudnn flags, TF32 off ×2.
- `state_hash(module) -> str` — sorted `state_dict`, `.detach().cpu().contiguous()`, **signed zero canonicalized** (`torch.where(v == 0, zeros, v)`) before `sha256` over bytes. The single hashing primitive everywhere (twin, cross-arm, null-seed, host_init).
- `env_block(device, worker_count) -> dict`; `REPLAY_REFUSAL_KEYS` (worker_count/device_index provenance-only).
- `FORBIDDEN_RELAXATIONS` — spec list **plus `torch.compile`**.
- `config_hash() -> str` — **defined at last** (was a placeholder in rev 1's records): sha256 over `inspect.getsource` of `derive`, `build_host`, the four seed classes, `Slot`, and the gate functions — the semantic surface whose edits change behavior without moving `frozen_block_hash`. `--replay` and the FreezeManifest both consult it.

- [ ] **Step 1: Failing tests** — rev 1's two, plus:

```python
def test_state_hash_canonicalizes_signed_zero():
    m1, m2 = torch.nn.Linear(2, 2, bias=True), torch.nn.Linear(2, 2, bias=True)
    with torch.no_grad():
        m2.load_state_dict(m1.state_dict())
        m1.bias[0] = 0.0
        m2.bias[0] = -0.0
    assert state_hash(m1) == state_hash(m2)


def test_enable_class1_rejects_stray_cublas_config(monkeypatch):
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    with pytest.raises(RuntimeError, match="CUBLAS_WORKSPACE_CONFIG"):
        enable_class1()


def test_config_hash_moves_with_semantic_source():
    assert config_hash() == config_hash()  # stable within a process
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 8: Episode runner — train epoch, telemetry, snapshot, germination

**Files:** modify section 8; create `tests/unit/kernel_demo/conftest.py`, `tests/unit/kernel_demo/test_episode.py`.

**Interfaces:**
- Consumes (itemized): `Config`, `DataBundle`, `CommonFuture`, `augment`, `TelemetryRecord`/`build_record`/`confusion_stats`, `Host`/`build_host`/`forward_to_slot`, `Slot`/`Stage`, `SeedDelta`/`build_seed`/`tau_init`, `split_decay_groups`/`build_optimizer`/`append_seed_group`, `state_hash`, `derive`/`make_generator`/`rng_scope`.
- Produces:
  - `@dataclass EpisodeCtx`: `cfg, data, device, episode_seed, pathology, future, host, opt, slot, telemetry, curves_val, curves_test, read_test: bool` (the unit-wall switch: pre-freeze modes construct with `read_test=False` and never touch `data.test_*`).
  - `make_episode(cfg, data, device, episode_seed, read_test=False)` — pathology `derive(seed,"pathology") % 4`; host init inside `rng_scope`; `host_init_hash` recorded; future `derive(seed,"future",0)`.
  - `train_one_epoch(ctx, epoch)` — consumes `future.order[epoch]` reshaped to `(S, B)`; CE + trust region during TRAINING; per-step grad-norm capture; `slot.step_tick`/`epoch_tick`; telemetry appended (val eval under no_grad); `curves_test` appended only if `read_test`.
  - `evaluate_acc(host, slot, x, y, device)` — eval-mode, chunked, mode-restored.
  - `@dataclass Snapshot`: `host_state` (deep-cloned tensors incl. BN buffers), `opt_state` (deepcopy of the **base 2-group** optimizer state), `cpu_rng`, `cuda_rng`, `epoch`. Snapshots are taken **only on the never-germinated base path**, so the state is always 2-group/DORMANT — arm-local materialization (Task 9) is what makes this sufficient.
  - `germinate(ctx, seed_name) -> float` — builds the seed at `channels=ctx.host.feat_channels` from `derive(episode_seed,"arm",seed_name)` inside `rng_scope`; τ-init features from `ctx.host.forward_to_slot(fixed_val_batch)` under `host.eval()`/`no_grad`; `append_seed_group`; `slot.stage = TRAINING`; returns `g`.
  - `end_state_R(curve) -> float`.
- `conftest.py` provides `tiny_bundle`:

```python
# tests/unit/kernel_demo/conftest.py
import pytest
import torch

from experiments.kernel_demo import DataBundle


@pytest.fixture
def tiny_bundle() -> DataBundle:
    return make_tiny_bundle()


def make_tiny_bundle(device: str = "cpu") -> DataBundle:
    # INVARIANT: intentionally seeded with a hardcoded literal — every call
    # returns byte-identical data. Fan/episode reproducibility tests depend
    # on this. Do NOT parametrize the seed or "improve" this helper.
    g = torch.Generator().manual_seed(0)

    def mk(n: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.randint(0, 256, (n, 3, 32, 32), generator=g, dtype=torch.uint8)
        y = torch.randint(0, 10, (n,), generator=g)
        return x.to(device), y.to(device)

    tx, ty = mk(512)
    vx, vy = mk(128)
    ex, ey = mk(128)
    return DataBundle(tx, ty, vx, vy, ex, ey)
```

- [ ] **Step 1: Failing tests** — rev 1's bitwise-episode, snapshot-roundtrip, and end_state tests (importing `make_tiny_bundle` from `conftest`, not from another test file; exact `==` for float lists, never `pytest.approx(abs=0)` whose default rel=1e-6 stays live), plus:

```python
def test_tiny_bundle_byte_identical_across_calls():
    a, b = make_tiny_bundle(), make_tiny_bundle()
    assert torch.equal(a.train_x, b.train_x) and torch.equal(a.val_y, b.val_y)


def test_germinate_leaves_host_bn_stats_bitwise_unchanged():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
    train_one_epoch(ctx, 0)
    before = state_hash(ctx.host)
    for name in SEED_NAMES:
        c = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
        train_one_epoch(c, 0)
        germinate(c, name)  # tau-init runs host in eval/no_grad
        assert state_hash(c.host) == before, name


def test_read_test_false_never_populates_test_curve():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 22, read_test=False)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    assert ctx.curves_test == []
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 9: Fan executor — arm-local materialization, twin, null-seed, diverged conventions

**Files:** modify section 9; create `tests/unit/kernel_demo/test_fan.py`.

**Interfaces:**
- Consumes (itemized): Task 8's episode API (`EpisodeCtx`, `make_episode`, `train_one_epoch`, `Snapshot`, `germinate`, `end_state_R`), `state_hash`, `Stage`, `Slot`, `build_optimizer`.
- Produces:
  - `class TwinDivergence(RuntimeError)` (`first_bad_epoch`).
  - `@dataclass ArmResult`: `name, status, R_val, R_test (float | None), curve_val, curve_test (list | None), init_seed, g_at_init, rms_ratio_blend_entry,` **`hash_after_training: str | None`** (every arm), **`host_hashes: list[str] | None`** (noop/nullseed arms — the data path the cross-arm assertion and the null-seed check need).
  - `@dataclass BaseTrace`: `host_hashes, curve_val, curve_test (None pre-freeze), snapshots: dict[int, Snapshot]` — the base run captures snapshots **at the scheduled fan epochs during its single pass** (no prefix re-runs per fan).
  - **Arm-local materialization (the load-bearing fix — three reviewers independently confirmed the alternative raises):** `run_arm(cfg, data, device, episode_seed, pathology, future, snap, arm_name, read_test) -> ArmResult` builds a **fresh** host (same init seed → identical init, then `load_state_dict` from `snap.host_state`), a **fresh DORMANT `Slot`**, and a **fresh 2-group optimizer** loading `snap.opt_state`, restores RNG states, then germinates (or not) and runs the continuation. Nothing mutated by one arm is visible to the next; `Optimizer.load_state_dict`'s unconditional group-count check is never hit because the load always happens on a fresh 2-group optimizer *before* `append_seed_group`.
  - `run_base(ctx, cfg, fan_epochs) -> BaseTrace` — a thin wrapper over the **same** inner epoch loop `run_arm` uses (one loop, two call sites: divergence-by-drift between base and twin is structurally impossible). Handles base-run divergence per convention: record status, `R_noop = cfg.diverged_r`, later scheduled fans skipped (recorded), hashes kept up to the divergence epoch.
  - `run_fan(...) -> tuple[list[ArmResult], dict]` — arms sequential: 4 seeds + twin. Twin = `run_arm(..., "noop")` whose `host_hashes` must equal `base.host_hashes[snap.epoch:]` (zero-normalized `state_hash`); mismatch raises `TwinDivergence(first_bad_epoch)`. Cross-arm assertion at end of TRAINING: every **finite** arm's `hash_after_training` equals the twin's hash at that epoch (a non-finite Δ makes the STE output NaN — that is arm divergence with `status="diverged"`, not a harness abort).
  - Null-seed arm (1-in-10 + selftest): germinates `conv_light`, then **`seed.gain.data.zero_()` and `gain.requires_grad_(False)`** (germinate τ-inits nonzero — the explicit zeroing is the step an implementer would otherwise miss); must reproduce the base bitwise (zero-normalized hash) through the whole horizon. **A mismatch while the twin holds is a HARD STOP — surface and investigate; there is no weaker fallback.** (The spec's "value-exact / zero-normalized hash" contingency *is* this check, since `state_hash` is already zero-normalized; curves are never an acceptable comparand.)
  - Diverged arms: `status="diverged"`, `R = cfg.diverged_r` both units, curves truncated, fan kept.

- [ ] **Step 1: Failing tests** — rev 1's twin-match / corrupted-hash / null-seed tests updated to the new signatures (hash-list comparison for null-seed, `==` exact), plus the two the panel demanded:

```python
def test_two_arms_from_one_snapshot_no_optimizer_corruption():
    # The bug class three reviewers hit: arm 1's seed groups must not leak
    # into arm 2's restore. Fresh materialization per arm makes this pass.
    ctx, base = _episode_with_base()
    snap = base.snapshots[2]
    r1 = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "conv_heavy", False)
    r2 = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "noop", False)
    assert r2.host_hashes == base.host_hashes[2:]  # untouched by arm 1
    assert r1.status in ("ok", "diverged")


def test_cross_arm_assertion_fires_on_injected_corruption(monkeypatch):
    # Negative test: the defense-in-depth assert must actually trip.
    ctx, base = _episode_with_base()
    snap = base.snapshots[2]
    real = experiments.kernel_demo.state_hash

    calls = {"n": 0}

    def corrupt_once(module):
        calls["n"] += 1
        h = real(module)
        return "corrupt" if calls["n"] == 3 else h

    monkeypatch.setattr(experiments.kernel_demo, "state_hash", corrupt_once)
    with pytest.raises((AssertionError, TwinDivergence)):
        run_fan(ctx, snap, base, CFG)
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 10: Fan records and the store — schema, shards, split walls, durability

**Files:** modify section 10; create `tests/unit/kernel_demo/test_store.py`.

**Interfaces:** rev 1's `FanRecord`/`Store`, corrected:
- `FanRecord` fields as rev 1 **plus `manifest_hash: str | None`** (None before freeze; the FreezeManifest hash after — every post-freeze record carries it), `split_role ∈ {preflight, train, tune, eval}` — **train/tune assigned at collection time** by `derive(episode_seed, "tune-split") % 5 == 0 → tune` (the spec's per-episode 80/20; `run_train` loads both roles and never re-splits).
- `Store.append(worker_id, record)` — write + flush; **`os.fsync` every 20 records and on close** (stated durability target: survives host-level failure losing at most ~20 records; a process crash loses none).
- `Store.merge()` — content-ordered; **asserts `fan_id` uniqueness** (the general backstop against smoke-then-full duplication, crash-resume double-writes, and accidental re-invocation).
- `Store.load(split_role, kinds=("fan",))` — filters; the **gradient loaders** are where `SplitViolation` fires: `load_for_training(store)` returns train+tune fans and raises `SplitViolation` if any record it is about to yield has `split_role == "eval"` or `kind in ("refan", "policy_run")` (enforcement at the consumption site, not only the query).
- JSON: non-finite → `null` + status (never bare NaN); tuples decode as lists — `fan_to_example` (Task 12) consumes decoded **dicts/lists**, stated.

- [ ] **Step 1: Failing tests** — rev 1's round-trip/merge tests, plus:

```python
def test_merge_rejects_duplicate_fan_ids(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=5))  # same fan_id, other shard
    with pytest.raises(ValueError, match="duplicate fan_id"):
        s.merge()


def test_split_violation_fires_at_the_training_loader(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(split_role="train"))
    s.append(0, _rec(episode_seed=3, split_role="eval"))
    ok = load_for_training(s)  # filter works on the happy path
    assert all(r.split_role in ("train", "tune") for r in ok)
    bad = _rec(episode_seed=4, split_role="eval")
    with pytest.raises(SplitViolation):
        _assert_trainable([bad])  # the guard itself, exercised directly


def test_nonempty_telemetry_roundtrip_tuples_become_lists(tmp_path):
    r = _rec()
    r.telemetry = [{"epoch": 1, "grad_norm_mean": [1.0, 2.0, 3.0]}]
    out = decode_record(encode_record(r))
    assert out.telemetry[0]["grad_norm_mean"] == [1.0, 2.0, 3.0]
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit + `wc -l` (budget ~850).**

---

### Task 11: Policy — trunk, factored head, deployment rule, masks

**Files:** modify section 11; create `tests/unit/kernel_demo/test_policy.py`.

**Interfaces:** rev 1, corrected and pinned:
- `Policy(cfg, gen)` constructed inside `rng_scope(gen)`. **Pinned hyperparameters:** single head, attention dim = d_model = 64, MLP ratio 4×, no biases in attention projections; explicit-matmul attention with a causal mask. Param count test: 70k–130k (arithmetic lands ~108k).
- `decide_live(policy, normalizer, telemetry, epoch, cfg)` — **window inclusive on both ends (5 ≤ epoch ≤ 15)**, with boundary tests at 4/5/15/16; **normalization order pinned: normalize the record vectors first, then apply any mask** — masking pre-normalization would map zeros to `−med/IQR` instead of the trained representation of "feature absent".
- `schedule_only_mask(t: Tensor) -> Tensor` — **`[..., EPOCH_FEATURE_IDX]` indexing**, correct for 1-D vectors and `[B,T,D]` batches alike (the dim-0 reading silently zeroes the *batch* axis on 3-D input and corrupts the schedule-only comparator — the null the headline must beat).
- `query_teacher_forced(...)` as rev 1.

- [ ] **Step 1: Failing tests** — rev 1's shape/causality tests, plus:

```python
def test_schedule_only_mask_batched():
    x = torch.randn(2, 7, TELEMETRY_DIM)
    m = schedule_only_mask(x)
    assert torch.equal(m[..., EPOCH_FEATURE_IDX], x[..., EPOCH_FEATURE_IDX])
    other = [i for i in range(TELEMETRY_DIM) if i != EPOCH_FEATURE_IDX]
    assert m[..., other].abs().sum() == 0


def test_policy_param_count_pinned():
    n = sum(p.numel() for p in Policy(Config(), make_generator(1)).parameters())
    assert 70_000 < n < 130_000


def test_decide_live_window_boundaries():
    pol, nz = Policy(Config(), make_generator(1)), Normalizer.identity()
    tele = [_rec_at(e) for e in range(20)]
    for epoch, allowed in [(4, False), (5, True), (15, True), (16, False)]:
        fire, _ = decide_live(pol, nz, tele[: epoch + 1], epoch, Config())
        if not allowed:
            assert fire is False  # outside window: never fires, by construction
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 12: Learning — objectives, frozen temperatures, warm-up, tune checkpointing

**Files:** modify section 12; create `tests/unit/kernel_demo/helpers.py`, `test_learning.py`.

**Interfaces:** rev 1, corrected:
- `measure_fan_density(records, unit="val") -> dict` with keys `best_minus_second`, `best_minus_noop`. **Pre-registered temperature mapping (recorded in the FreezeManifest): `β_which = cfg.beta_which_frac × best_minus_second` (discrimination scale); `β_now = best_minus_noop / cfg.beta_now_div` (advantage scale).** `train_policy` takes the **frozen density dict** (from the manifest), never recomputes from its input records — and asserts the temperatures it uses match the manifest.
- `warmup_schedule(step, total_steps, warmup_frac) -> bool` — pure, unit-tested; `train_policy` consumes it.
- `train_policy(records, cfg, normalizer, gen, *, frozen_density, steps=None, mask_fn=None) -> tuple[Policy, dict]` — `steps` defaults to `cfg.policy_steps` (frozen); tests pass a small value (**the <60s target is a consequence of a fixed step count, not a wall-clock assertion**); loads train+tune roles as given (never re-splits); Adam(`cfg.policy_lr`); checkpoint on tune score; returns the tune curve.
- `policy_loss` — rev 1's body verbatim (review-verified against the spec objective term-by-term), with the misleading `/ 1.0` sigmoid comment removed.
- `sign_flip_pvalue(lifts, n, seed)`; `money_chart_permutation_pvalue(pathologies, picks, designed, n, seed)` — **returns (classes-matched count, p)** ("modal pick per pathology class matches designed winner"; interface wording fixed) with a **deterministic tie-break** (lexicographic seed name) for shuffled-label modal ties.
- `helpers.py`: `synthetic_fans(n, seed)` plants a telemetry-feature→winner rule; **`synthetic_holdout(records)` returns the episodes the tune-split assigns to tune** (evaluation on a genuine held-out set — `recs[-24:]` was not guaranteed held out under the episode-keyed split).

- [ ] **Step 1: Failing tests** — rev 1's learning/sign-flip tests corrected, plus the mechanism-isolating tests the panel demanded:

```python
def test_policy_learns_synthetic_mapping_on_true_holdout():
    cfg = Config()
    recs = synthetic_fans(n=120, seed=5)
    pol, info = train_policy(
        recs, cfg, Normalizer.identity(), torch.Generator().manual_seed(0),
        frozen_density={"best_minus_second": 0.05, "best_minus_noop": 0.08},
        steps=600,
    )
    assert synthetic_agreement(pol, synthetic_holdout(recs)) > 0.6


def test_warmup_schedule_boundary():
    assert warmup_schedule(0, 100, 0.3) is False
    assert warmup_schedule(29, 100, 0.3) is False
    assert warmup_schedule(30, 100, 0.3) is True
    assert warmup_schedule(99, 100, 0.3) is True


def test_j_now_stopgrad_leaves_which_gradients_unchanged():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    batch = synthetic_batch(seed=9)
    fd = 0.05

    def grads(enable_now):
        loss = policy_loss(pol, batch, cfg, fan_density=fd, enable_now=enable_now)
        return torch.autograd.grad(loss, pol.seed_head.parameters(), retain_graph=False)

    g_off, g_on = grads(False), grads(True)
    for a, b in zip(g_off, g_on, strict=True):
        assert torch.allclose(a, b, atol=1e-6)  # WHICH trains at 1x regardless of p


def test_now_head_gradient_alive_with_divergent_arm_present():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    batch = adversarial_batch_with_divergent_arm(seed=3)  # helpers.py
    loss = policy_loss(pol, batch, cfg, fan_density=0.05, enable_now=True)
    g = torch.autograd.grad(loss, pol.now_head.parameters(), allow_unused=True)
    assert any(gi is not None and gi.abs().sum() > 0 for gi in g)


def test_train_policy_rejects_wrong_kind_records():
    recs = synthetic_fans(n=10, seed=1)
    recs[3] = dataclasses.replace(recs[3], kind="refan")
    with pytest.raises(SplitViolation):
        train_policy(recs, Config(), Normalizer.identity(),
                     torch.Generator().manual_seed(0),
                     frozen_density={"best_minus_second": 0.05, "best_minus_noop": 0.08},
                     steps=10)


def test_money_chart_permutation_four_classes():
    # Two classes at 10/10 gives P(both rows match under shuffle) ≈ 0.33 —
    # mathematically incapable of clearing 0.05. Four classes are required.
    paths = sum(([c] * 10 for c in "abcd"), [])
    picks = sum(([w] * 10 for w in "wxyz"), [])
    designed = dict(zip("abcd", "wxyz", strict=True))
    obs, p = money_chart_permutation_pvalue(paths, picks, designed, n=4000, seed=3)
    assert obs == 4 and p < 0.05


def test_sign_flip_pvalue_calibration():
    # Fixed-seed version of a 5%-flaky property: valid as long as the
    # permutation draw order is untouched. Do not "fix" a failure here by
    # reseeding — investigate the draw-order change instead.
    g = torch.Generator().manual_seed(1)
    null_lifts = torch.randn(100, generator=g) * 0.01
    assert sign_flip_pvalue(null_lifts, n=2000, seed=2) > 0.05
    assert sign_flip_pvalue(null_lifts + 0.02, n=2000, seed=2) < 0.01
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 13: `--selftest`

**Files:** modify CLI section (selftest branch only); create `test_selftest.py`.

`run_selftest(cfg, device) -> dict`, in order:
1. `enable_class1()` (already ran via `main()`); print `FORBIDDEN_RELAXATIONS`.
2. **Per-seed determinism probe (GPU):** forward+backward each of the four seed types once under the flags; a `RuntimeError` from a missing deterministic kernel is a **hard failure** (grouped conv / GroupNorm coverage on this exact build is verified, not assumed).
3. Smoke episode (tiny config, `read_test=False`): base → fan → twin holds; null-seed reproduces base (zero-normalized hash; mismatch = hard stop).
4. **Slot-site signed-zero scan:** assert no exact `−0.0` in `forward_to_slot` output over a representative batch (the STE flip precondition).
5. Blindness grep (`time.time|datetime.now|monotonic|os.environ|hostname` in the telemetry section) **and `nn.init.` grep** across sections 4/5/11 (those calls take no `generator=` and consume global RNG outside `rng_scope`).
6. JSON round-trip incl. non-finite; store split-wall + duplicate-fan_id checks; partition sizes (45k/5k/10k, disjoint).
7. `rng_scope` global-stream isolation check.
8. Deterministic-mode slowdown measured and printed.

- [ ] Test: `test_selftest_runs_clean_cpu()` (GPU steps skip on CPU with a printed notice — the result dict marks them `"skipped"`, and Phase A requires them non-skipped). Implement; PASS; commit.

---

### Task 14: `--preflight` — gates, refans, FreezeManifest

**Files:** modify CLI section (preflight branch only); create `test_preflight_gates.py`.

**Interfaces:**
- `draw_schedule(episode_seed, cfg) -> tuple[int, int]` — 2 ordered epochs, uniform without replacement over the inclusive window.
- `run_collection_episode(...)` — base (`BaseTrace` with snapshots at the scheduled epochs), two fans, records appended (`read_test` per phase).
- `run_refan(...)` — future `derive(episode_seed,"refan",k)`, 5 real arms incl. fresh no-op, `kind="refan"`, excluded from training.
- Gates 1–8 as `(records, cfg) -> GateResult(ok, detail, remedy)` — thresholds read from `Config` (frozen fields), never literals; unit of analysis = first fan per episode; all in **val units**:
  1. No-op sanity (D1): ≥ `cfg.gate1_min_mild_noop_wins` mild no-op wins; modal in no targeted pathology. *Remedy: sampler.*
  2. (a) probe→pathology, GroupShuffleSplit by episode, > `cfg.gate2_probe_min_acc`; (b) probe→val-argmax vs majority-class + contingency vs `DESIGNED_WINNER`. *Remedy: sampler.*
  3. Fan density (`best_minus_second`, `best_minus_noop`, within-fan) > `cfg.gate3_contrast_mult` × refan floor. *Remedy: averaging window, horizon.*
  4. No seed val-argmax > `cfg.gate4_dominance_max` overall, none majority in every pathology. *Remedy: sampler/menu balance — **menu balance is a Task 5 reopen (param tests, Tasks 6–13 re-verification, Phase A re-run), priced here, not a 1am knob.*
  5. `rms_ratio_blend_entry` within `cfg.gate5_rms_band` across arms. *Remedy: τ, λ, seed_lr — never the sampler.*
  6. Density per fan epoch ≥ `cfg.gate6_late_density_mult` × early. *Remedy: horizon, window.*
  7. Now-vs-later materiality (report-only).
  8. Worker-pressure test (GPU): twin at 1 worker vs full count; **outcome stored in the manifest — `--replay` consults it** for the worker-count contingency.
- `run_preflight(cfg, data, device, store, freeze=False)`:
  - Default: **dry run** — gates evaluated and printed, `preflight_iter` record appended (iteration counter, `config_hash`, git rev), normalizer fitted and shown, **no freeze artifact written**.
  - `--freeze`: **refuses unless** all gates `ok`, the git worktree is clean, and HEAD equals the recorded Phase-A commit. Writes the **FreezeManifest** atomically (temp + rename): `{frozen_block_hash, config_hash, git_rev, spec_rev: "98083fd", normalizer, fan_density (both keys), beta_which, beta_now (the actual frozen values), schedule_id, data_split_id, gate_results, gate8_outcome, pressure_contingency, manifest_hash}` where `manifest_hash` = sha256 over the canonical serialization of everything else. Every post-freeze record carries `manifest_hash`.

- [ ] Tests: gate logic on synthetic records — each gate has a passing and a **failing** fixture (gate 4 fed 8/10 conv_heavy wins → not ok; gate 1 fed zero mild no-op wins → not ok; gate 5 fed ratios (0.04, 0.05, 0.06, 0.30) → not ok); `--freeze` refusal on a failing-gates fixture and on a dirty-worktree stub. Implement; PASS; commit + `wc -l` (budget ~1150).

---

### Task 15: `--collect` — idempotent process workers with a halt channel

**Files:** modify CLI section (collect branch only); create `test_collect.py`.

**Interfaces:**
- `run_collect(cfg, store_root, devices, n_workers_per_device, limit=None)`:
  - Refuses without a FreezeManifest whose `frozen_block_hash` matches live `Config`, whose `config_hash` matches live source, **and whose `gate_results` are all ok**.
  - **Idempotent:** computes the target seed list `derive(run_seed,"train",i)`, then **skips every episode_seed already present in the merged shards** — this is also the crash-resume path, and it makes the smoke-then-full sequence safe. (Smoke runs may also use `--store` pointing at a scratch path; both are stated valid.)
  - `--extend N` appends N episodes beyond `n_collect`, allowed **only before any eval-namespace record exists**, and writes an extension event record.
  - Workers: `multiprocessing.get_context("spawn")`, one process per worker; each calls `enable_class1()` first, `torch.cuda.set_device(device)`, loads data once, writes its own shard, **redirects stdout/stderr to `runs/kernel_demo/logs/worker_{id}.log`**, and emits one heartbeat line per episode (`episode_seed`, epoch span, elapsed) — a hung worker is distinguishable from a slow one at 2am.
  - **Halt channel:** a `multiprocessing.Event`; any `TwinDivergence` sets it, and `write_divergence_report(path, ...)` emits the fixed schema `{episode_seed, arm_name, first_bad_epoch, config_hash, frozen_block_hash, manifest_hash, env_block, host_init_hash}` to a well-known path. All workers check the event between episodes and stop; the parent reports which workers completed what. **Pre-halt shards remain valid** (fan_id uniqueness protects the resume).
  - Parent join distinguishes clean completion / halted / crashed per worker and exits nonzero on anything but clean.
- Worker entry `worker_main(args)` module-level (spawn-picklable).

- [ ] Tests (CPU, tiny bundle via injection hook): 2 workers × 2 episodes → 4 episodes/8 fans across 2 shards, content-ordered, roles ∈ {train, tune} per the episode split; **re-invocation collects zero new episodes (idempotency)**; injected divergence (monkeypatched hash) sets the halt event, sibling worker stops early, divergence report exists with required keys. Implement; PASS; commit.

---

### Task 16: `--train` and `--eval`

**Files:** modify CLI section (train + eval branches only); create `test_eval_stats.py`.

**Interfaces:**
- `run_train(cfg, store_root)` — loads the manifest; consumes its **frozen densities/temperatures** (asserts against recomputation — collection density is printed as a diagnostic only, never used); `load_for_training(store)` (train+tune roles, SplitViolation-guarded); trains `trained` and `schedule_only` (same records, `mask_fn=schedule_only_mask` applied post-normalization) with `steps=cfg.policy_steps`; saves both checkpoints with state-dict-hash ids; prints tune curves. **Pre-stated levers for a bad tune curve: `--extend` collection (pre-eval only) or shrink the trunk (`d_model`/`n_layers` are non-frozen)** — both recorded if used.
- `run_eval(cfg, data, device, store_root)`:
  - **One-shot guard:** refuses if `eval_results.json` exists. Override only via `--void-preregistration`, which itself writes a store event record (visible forever, mirroring the preflight_iter philosophy).
  - Refuses on manifest mismatch, or if merged train-namespace episodes < `n_collect` + recorded extensions (collection incomplete).
  - Battery per spec: 100 shared eval seeds × {trained, random, schedule-only, fixed-epoch}; live rule window-inclusive threshold p>0.5; lift = `R_chosen^test − R_noop^test` paired (eval runs `read_test=True`); sign-flip permutation (10k, one-sided) for trained-vs-0 and paired trained-vs-schedule-only; germination rates beside every p-value.
  - Frozen grid: 2 forced fans per eval episode at `derive(episode_seed, "evalgrid")`-drawn epochs (schedule distribution) → 200 grid fans; teacher-forced agreement vs **test-argmax over the 4 seed arms**; majority-class + schedule-only nulls; ~30 refans → Σp² ceiling (test units, labeled lower bound, Wilson CI, context-only); falsifier = telemetry-history **derangement across pathology classes**; restraint regret (last grid point + labeled per-point); WHEN contrast restricted + unrestricted; chosen-seed marginal + diverged-excluded companion inputs; power note (MDE from manifest density at N=100 and 200 grid points).
  - Everything → `eval_results.json` (atomic write), all records `split_role="eval"` + manifest_hash.
- `verdict(results, cfg) -> dict[str, bool]` — the five pre-registered threshold booleans, pure function.

- [ ] Tests (statistics only, synthetic): Wilson CI against a known value; derangement never maps a class to itself; restricted/unrestricted WHEN contrast on a 6-episode fixture with 2 never-germinates; `verdict` on an all-pass and a lift-fail fixture; one-shot refusal (`eval_results.json` exists → SystemExit); incomplete-collection refusal. Implement; PASS; commit.

---

### Task 17: `--report`, `--replay`, plotting sidecar

**Files:** modify CLI section (report + replay branches only); create `experiments/kernel_demo_plots.py`, `test_report.py`.

**Interfaces:**
- `run_report(cfg, store_root)` — **writes canonical JSON + aligned text tables only** (D4): the full spec §Report list, incl. observed diverged-arm end-state accuracies beside the 0.10 convention, realized-p-by-sign(A), fan density + `P(val-argmax = test-argmax)`, tune curve, temperatures in force, deterministic-mode cost. **Refusal rule (D6): mixed `manifest_hash` values in any single number** — multi-namespace presence is normal.
- `kernel_demo_plots.py` — standalone CLI (`python -m experiments.kernel_demo_plots --results ... --store ... --out runs/kernel_demo/plots/`); imports kernel_demo for dataclasses only; renders arm curves (spike-then-crash = curve max exceeds end-state by >0.05), α/β trajectories, money chart + falsifier + diverged-excluded companions, tune curve, RMS-at-blend-entry.
- `run_replay(cfg, fan_id, store_root, device)` — locates the record via merged shards; refuses on `REPLAY_REFUSAL_KEYS` env mismatch, `config_hash` mismatch, or `manifest_hash` mismatch; **consults the manifest's gate-8 outcome**: runs single-worker normally, at the recorded worker_count if the pressure contingency fired; re-derives, forces the fan, asserts recorded `R_val` per finite arm; on mismatch localises via `host_init_hash` first ("diverged at seeding" vs "diverged at kernel selection").

- [ ] Tests: report table renders on the Task 16 fixture; mixed-manifest refusal raises; replay refusal triggers on a doctored env block and a doctored config_hash. Add matplotlib: `uv add --group dev matplotlib`. Implement; PASS; commit.

---

### Task 18: Narrative pass and final CPU verification

- [ ] **Step 1:** Read top-to-bottom; every section banner gets a 2–5 line "why" docstring quoting its spec decision (caveat header, delta contract, twin non-optionality, the 0.10 rationale, the unit wall, arm-local materialization). Confirm section order and that Tasks 13–17 touched only their own subparser branches. `wc -l` — if far past ~1200, tighten prose/comments in the responsible section; never split the file, never compress state-restoration or statistical logic.
- [ ] **Step 2:** `uv run pytest tests/unit/kernel_demo -v` — all pass. `uv run mypy src experiments && uv run ruff check experiments tests` — clean.
- [ ] **Step 3:** Update filigree `simic-4a44ed57c9` (implementation complete; operational phases pending).
- [ ] **Step 4:** Commit.

---

## Operational Phases (post-code; GPU; the user's machine — never interleave with code edits)

- [ ] **Phase A — Certify:** `uv run python -m experiments.kernel_demo selftest --device cuda:0` with zero skipped steps (per-seed determinism probes included); `wardline scan . --fail-on ERROR` (exit 2 = wardline error → report it, per the dogfooding rule); full suite; final commit; clean worktree. **Any later change to sections 4/5/6/8/9 returns here.**
- [ ] **Phase B — Preflight & freeze (user present):** dry-run preflights on the subset flag, then full; tune the sampler per gate remedies (gate 4's menu-balance remedy = Task 5 reopen + Phase A re-run — priced, not improvised); surface the gate table; `preflight --freeze` at the Phase-A commit writes the FreezeManifest.
- [ ] **Phase C — Collect (overnight):** smoke `--limit 4` (idempotency makes the follow-on full run safe; scratch `--store` also fine), then `collect --devices cuda:0,cuda:1 --workers 3`. Morning check: worker logs, heartbeats, zero divergence reports, episode count.
- [ ] **Phase D — Train:** `train`; inspect tune curves; if bad, the two pre-stated levers (extend pre-eval / shrink trunk), recorded.
- [ ] **Phase E — Eval (user present, ONE SHOT):** confirm collection complete → `eval` runs once; the guard makes a second invocation refuse.
- [ ] **Phase F — Report:** `report`, sidecar plots, one `replay` spot-check of a random fan_id. Deliver the three headline numbers with their nulls and the falsifier result.

## Self-review notes (rev 2)

- All ten panel reviews' accepted findings are incorporated; the two owner-relayed external reviews' blockers are incorporated (freeze ordering → Operational Phases; slot interface → Task 4 invariant; arm materialization → Task 9; test wall → `read_test`; τ-init mode → Task 5; confusion telemetry → D3; FreezeManifest → Task 14; rng_scope → Task 1).
- Deliberate rejections, recorded: the external suggestion to keep post-freeze *collection* test-blind was not adopted (spec fan-step 7 explicitly stores both units post-freeze; the wall protects the pre-freeze phase — D2 covers the difference). The null-seed "value-exact fallback" is not a fallback at all in rev 2 — the zero-normalized hash *is* the primary check, and a mismatch is a hard stop.
- Type/symbol consistency pass done: `state_hash` is the only hashing primitive; `BaseTrace`/`ArmResult` carry every hash the assertions consume; `run_base` returns `BaseTrace` (the rev 1 arity contradiction is gone); `stage_k/m/f` replaced the single-letter `K/M/F` field names (N815 lint); gate thresholds exist only as Config fields.
