# Kernel Demo ("Simic in 20 minutes") Implementation Plan — rev 3

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This document is self-contained: no task requires any prior plan revision.**

**Goal:** Build `experiments/kernel_demo.py` — a single-file tech demo where a learned transformer policy (Aurelia) reads host telemetry, decides when to inject which of four fixed seeds into one slot of an undersized CIFAR-10 CNN, and is trained/scored against matched counterfactual fans — per the LOCKED spec `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 6, commit 98083fd).

**Architecture:** One narrative-ordered Python file (~1200 lines, aspirational — never compress state-restoration or statistical logic to hit it), sections 1–13; a standalone plotting sidecar; tests in `tests/unit/kernel_demo/`.

**Tech Stack:** Python ≥3.14, torch 2.13.0+cu130 (installed, CUDA verified on 2× RTX 4060 Ti), torchvision 0.28.0+cu130 (added in Task 1), pytest. matplotlib (dev group) for the sidecar only.

**Provenance:** rev 3 = rev 2 (ten-reviewer panel + two external reviews) + the solution-design review + a structural self-containment audit (27 defects). Reviews live under `docs/superpowers/reviews/`.

## Global Constraints (inherited by every task)

- **The spec is LOCKED.** Deviations are surfaced in the Deviations Register, never silent. The spec is the tiebreaker for ambiguity.
- **Reward definition (spec):** `R` = mean accuracy over the final 3 epochs of the horizon (`end_state_R`), end-state only, zero shaped terms. Diverged runs score `cfg.diverged_r = 0.10` in both units.
- Class 1 determinism: `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`, `cudnn.benchmark=False`; `CUBLAS_WORKSPACE_CONFIG=:4096:8` **force-set, hard-fail on a conflicting pre-set value**. TF32 off both flags. No AMP, no dropout, no gradient clipping, no `torch.compile`.
- Explicit-matmul attention everywhere (seed and policy); no `F.scaled_dot_product_attention`.
- RNG ownership: every draw from a named `torch.Generator`; `torch.manual_seed` only at process startup; all `nn.Module` construction inside `rng_scope(gen)`.
- Hashing: one primitive, `state_hash`, signed-zero-canonicalized (see D8). All "bitwise" claims mean *bitwise modulo signed-zero canonicalization*.
- Test-data wall: pre-freeze modes (`selftest`, `preflight`) run `read_test=False` and never touch the test partition (D2). Post-freeze modes record both units per spec.
- `Config` holds all constants; `FROZEN_FIELDS` covers the frozen block incl. policy schedule and gate thresholds; `n_collect` is deliberately unfrozen (spec's extension lever).
- Commit per task; pre-commit ruff (`E,W,F,I,N,UP,B,C4,SIM,RUF`, E501 ignored) + strict mypy — all code blocks below are lint-clean as shown (one statement per line, no lambda assignment, no unused imports, no upper-case field names).
- CPU-green is necessary, **not sufficient for the Class-1 claim** — only GPU phases certify determinism; any change to sections 4/5/6/8/9 after certification voids it until Phase A re-runs.
- Code phase (Tasks 1–18) first; **all GPU work in the Operational Phases after Task 18**; freeze happens only at the certified final commit.

### Plan-authored constants (owner sign-off required at freeze — not spec values)

`tau_eps=1e-6` (spec: "ε a floor", no value) · `policy_lr=1e-3`, `policy_batch_size=64`, `policy_steps=4000`, `warmup_frac=0.3` (policy schedule; frozen, selects the headline checkpoint) · `eval_chunk=1000` (evaluate_acc chunking) · gate multipliers `2.0`/`0.5`/`0.40` etc. (D9) · `fsync_every=20`. `seed_lr=0.05` is spec-derived ("same LR" as host).

## Deviations Register (exhaustive; surfaced, not silent)

| # | Deviation | Rationale |
|---|---|---|
| D1 | Gate 1 = engineering sanity check (frozen empirical thresholds), not a binomial vs 20% | No power at ~7–8 episodes/pathology; headline statistics not spent on a sampler shakedown |
| D2 | Pre-freeze modes never read the test partition, though spec fan-step 7 records both units | The spec's own absolute unit rule outranks fan-step 7 pre-freeze; post-freeze collection records both |
| D3 | `TelemetryRecord` gains `per_class_val_acc_std`, `confusion_entropy` | Spec's pathology table promises a confusion signature for `no_spatial_mix`; its field list omits any. Neutral measurements. **Owner ack required** |
| D4 | `--report` emits canonical JSON/tables; plotting is a standalone sidecar CLI | Acyclic imports |
| D5 | `experiments/` at repo root (vs `ops/repo-structure.md`'s `src/simic/experiments/`) | Spec-pinned placement for a non-Simic standalone demo |
| D6 | "Refuse mixed namespaces" = refuse mixed `manifest_hash` generations in any single number | Multi-namespace presence in one store is normal and required |
| D7 | Host widths 24/64/80 healthy (~162k), pathologies never change stage2 output (64ch/8×8) | 32/64/128 double-conv computes to ~289k (≈2× spec's ~150k); fixed slot interface is a spec pin |
| D8 | `state_hash` canonicalizes signed zero universally; every "bitwise" claim is modulo that | IEEE-754: the STE add flips `−0.0`→`+0.0`, so raw-byte bitwise is unachievable in seed arms by construction; the spec's own null-seed contingency names zero-normalized hashing — promoted to the single primitive |
| D9 | Gate thresholds (2.0× contrast, 0.5× late-density, 0.40 dominance, ≥2 mild wins, 0.5 probe floor) are plan-chosen values | Spec names the gates but not these constants; all are frozen Config fields; owner signs off at freeze |
| D10 | `torch.compile` added to `FORBIDDEN_RELAXATIONS` | Spec's list omits it; a compiled kernel voids deterministic-algorithm guarantees; strengthening only |
| D11 | τ-init measures the seed in `train()` mode (host in `eval()`/no-grad per spec) | Spec pins the host mode only. BN-carrying seeds differ across modes; train-mode calibration is the mode of the first TRAINING step, making "every arm enters at τ" true where it matters |
| D12 | GERMINATED is zero-duration (collapses into TRAINING's first tick) | Spec lists the FSM state; nothing observes a nonzero dwell |
| D13 | Gate-2 probe = 200-step `nn.Linear` + hand-rolled by-episode split, not sklearn | No new dependency |

## File Structure

- `experiments/kernel_demo.py` — sections: 1 constants/derive/rng_scope · 2 data+future · 3 telemetry · 4 host · 5 seeds · 6 slot/lifecycle · 7 determinism+hashing · 8 episode · 9 fan · 10 store · 11 policy · 12 learning · 13 CLI/modes. Sections 1–12 additive per task; **Tasks 13–17 each touch only their own subparser branch of section 13.**
- `experiments/kernel_demo_plots.py` — standalone CLI; imports kernel_demo for dataclasses only.
- `experiments/__init__.py`, `tests/unit/__init__.py`, `tests/unit/kernel_demo/__init__.py`.
- `tests/unit/kernel_demo/`: `conftest.py` (Task 8), `helpers.py` (Task 12), `test_{derive,data,telemetry,host,seeds,slot,determinism,episode,fan,store,policy,learning,selftest,preflight_gates,collect,eval_stats,report}.py`.
- Named artifacts (all under the store root, default `runs/kernel_demo/`): `shards/worker_{id}.jsonl`, `frozen.json` (FreezeManifest), `certified.json` (Phase-A certification), `eval_results.json`, `divergence_report.json`, `logs/worker_{id}.log`, `plots/`.

## Execution Model

**Code phase (Tasks 1–18):** CPU-tested build; `wc -l` checks at Tasks 6/10/14 (~500/~850/~1150, aspirational).

**Operational phases (post-Task-18, strictly ordered, never interleaved with code edits):**
- **Phase A — Certify:** full suite; `selftest --device cuda:0 --certify` (zero skipped steps) writes `certified.json` = `{git_rev, selftest_results, det_mode_cost}`; `wardline scan . --fail-on ERROR`; mypy/ruff; final commit; clean worktree. Any later edit to sections 4/5/6/8/9 returns here.
- **Phase B — Preflight & freeze (user present):** dry-run preflights (`preflight_iter` records; sampler tuning per gate remedies; gate-4's "menu balance" remedy = Task 5 reopen + Phase A re-run, priced not improvised). `preflight --freeze` refuses unless all gates ok ∧ worktree clean ∧ `HEAD == certified.json["git_rev"]`; writes `frozen.json` atomically.
- **Phase C — Collect (overnight):** idempotent; halt-on-divergence.
- **Phase D — Train.** **Phase E — Eval (user present, one-shot, resume-safe).** **Phase F — Report + replay spot-check.**

**Runtime budget (measured, not guessed):** 2.78 s/epoch floor under real Class-1 flags on this hardware. Collection ≈ 300 episodes × ~340 epochs ≈ 79 GPU-h; eval battery ≈ 48k epochs ≈ 37 GPU-h. **VRAM measured ≈ 0.85–1.05 GB/worker → 6 workers/card fits with ~2× margin (15.6 GiB usable).** At 12 workers: collect ≈ 7 h, eval ≈ 3 h — overnight is real at 12 workers and ~2× optimistic at 6. Gate 8 records wall-clock at 1-vs-N workers, yielding the true concurrency factor and the spec-mandated deterministic-mode cost from a run already required.

**After freeze, any behavioral source change creates a new run generation** (new `manifest_hash`); generations never mix in one number.

---

### Task 1: Dependencies, skeleton, derive(), rng_scope, Config

**Files:**
- Modify: `pyproject.toml` — (a) `uv add torchvision` (resolves 0.28.0+cu130); (b) `[tool.pytest.ini_options] pythonpath = ["src", "."]` (without `"."`, no test in this plan can import `experiments.kernel_demo` — empirically verified); (c)
  ```toml
  [[tool.mypy.overrides]]
  module = "torchvision.*"
  ignore_missing_imports = true
  ```
  (torchvision ships no py.typed; strict mypy hard-fails otherwise — verified).
- Create: `experiments/__init__.py`, `experiments/kernel_demo.py`, `tests/unit/__init__.py`, `tests/unit/kernel_demo/__init__.py`, `tests/unit/kernel_demo/test_derive.py`

**Interfaces (Produces):** `derive`, `make_generator`, `rng_scope`, `Config`, `FROZEN_FIELDS`, `frozen_block_hash`, `config_hash`, `SCHEMA_VERSION = 1`, `enable_class1` (stub until Task 7), `main` (subcommands stubbed; **first statement `enable_class1()`**).

- [ ] **Step 1: pyproject edits** as above; verify `uv run python -c "import torchvision; print(torchvision.__version__)"`. STOP and report if unresolvable.
- [ ] **Step 2: Failing tests**

```python
# tests/unit/kernel_demo/test_derive.py
import dataclasses

import torch

from experiments.kernel_demo import (
    Config,
    config_hash,
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
    make_generator(2**64 - 1)  # full uint64, no mask


def test_rng_scope_isolates_and_reproduces():
    before = torch.get_rng_state()
    with rng_scope(make_generator(derive(9, "scope"))):
        torch.nn.Linear(4, 4)
    assert torch.equal(before, torch.get_rng_state())

    def build() -> torch.Tensor:
        with rng_scope(make_generator(derive(9, "build"))):
            return torch.nn.Linear(8, 8).weight

    assert torch.equal(build(), build())


def test_frozen_hash_covers_policy_and_gate_knobs_but_not_n_collect():
    c = Config()
    assert frozen_block_hash(c) == frozen_block_hash(Config())
    for f in ("lam", "policy_lr", "warmup_frac", "gate4_dominance_max"):
        changed = dataclasses.replace(c, **{f: getattr(c, f) * 2})
        assert frozen_block_hash(changed) != frozen_block_hash(c)
    more = dataclasses.replace(c, n_collect=400)  # spec's extension lever
    assert frozen_block_hash(more) == frozen_block_hash(c)


def test_config_hash_stable_within_process():
    assert config_hash() == config_hash()
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
import inspect
from collections.abc import Iterator
from dataclasses import dataclass

import torch

SCHEMA_VERSION = 1


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
    g.manual_seed(seed)  # full uint64 is accepted; do NOT mask (seed aliasing)
    return g


@contextlib.contextmanager
def rng_scope(gen: torch.Generator) -> Iterator[None]:
    # nn.Module constructors draw from the GLOBAL stream in reset_parameters();
    # this scope reroutes those draws to the named generator and restores the
    # process-global stream afterwards.
    prior = torch.get_rng_state()
    torch.set_rng_state(gen.get_state())
    try:
        yield
    finally:
        gen.set_state(torch.get_rng_state())
        torch.set_rng_state(prior)


@dataclass(frozen=True)
class Config:
    # frozen: lifecycle + reward
    tau: float = 0.05
    tau_eps: float = 1e-6          # plan-authored (spec names no value)
    lam: float = 1.0
    stage_k: int = 3
    stage_m: int = 3
    stage_f: int = 2
    horizon: int = 40
    window: tuple[int, int] = (5, 15)  # inclusive both ends
    t_star: int = 10
    lr: float = 0.05
    momentum: float = 0.9
    wd: float = 5e-4
    seed_lr: float = 0.05
    diverged_r: float = 0.10
    fans_per_episode: int = 2
    # frozen: statistics
    n_preflight: int = 30
    n_eval: int = 100
    alpha_level: float = 0.05
    permutation_resamples: int = 10_000
    beta_which_frac: float = 0.2
    beta_now_div: float = 2.2
    # frozen: gate thresholds (D9 — plan-chosen, owner sign-off at freeze)
    gate1_min_mild_noop_wins: int = 2
    gate2_probe_min_acc: float = 0.5
    gate3_contrast_mult: float = 2.0
    gate4_dominance_max: float = 0.40
    gate5_rms_band: float = 2.0
    gate6_late_density_mult: float = 0.5
    # frozen: policy training schedule (plan-authored; selects the checkpoint)
    policy_lr: float = 1e-3
    policy_batch_size: int = 64
    policy_steps: int = 4000
    warmup_frac: float = 0.3
    # NOT frozen
    n_collect: int = 300            # spec's "extend collection pre-eval" lever
    d_model: int = 64
    n_layers: int = 2
    tune_frac: float = 0.2
    batch_size: int = 128
    eval_chunk: int = 1000          # plan-authored
    fsync_every: int = 20           # plan-authored durability cadence
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


def _semantic_sources() -> list[object]:
    # Populated as the named objects come to exist (Tasks 4-7, 14 extend this
    # list in place); config_hash covers the semantic surface whose edits
    # change behavior without moving frozen_block_hash.
    return list(_SEMANTIC_SURFACE)


_SEMANTIC_SURFACE: list[object] = [derive]


def config_hash() -> str:
    h = hashlib.sha256()
    for obj in _semantic_sources():
        h.update(inspect.getsource(obj).encode())
    return h.hexdigest()


MODES = ("selftest", "preflight", "collect", "train", "eval", "report", "replay")


def enable_class1() -> None:  # real body lands in Task 7
    pass


def main(argv: list[str] | None = None) -> None:
    enable_class1()  # MUST be the first statement of every process
    ap = argparse.ArgumentParser(prog="kernel_demo")
    sub = ap.add_subparsers(dest="mode", required=True)
    for m in MODES:
        p = sub.add_parser(m)
        p.add_argument("--store", default="runs/kernel_demo")
        p.add_argument("--device", default="cuda:0")
        p.add_argument("--subset", type=int, default=None)  # dev-speed flag
        if m == "replay":
            p.add_argument("fan_id")
    args = ap.parse_args(argv)
    raise SystemExit(f"not implemented: {args.mode}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run** — PASS; `uv run python -m experiments.kernel_demo selftest` → `not implemented: selftest`.
- [ ] **Step 6: Commit.**

---

### Task 2: Data — partition, GPU residency, CommonFuture, augmentation

**Files:** modify section 2; create `tests/unit/kernel_demo/test_data.py`.

**Interfaces:**
- Consumes: `derive`, `make_generator`, `Config`.
- Produces: `CIFAR_MEAN`, `CIFAR_STD`; `split_indices(run_seed) -> (train_idx 45k, val_idx 5k)` (pure, download-free); `DataBundle` (six tensor fields, one per line); `load_data(cfg, device, subset=None)` (CIFAR10 → `runs/data`; official 10k test untouched; named `to_device` helper, no lambda); `CommonFuture` (`order` int64 **[E, S*B]** flat indices, `crops` uint8 [E,S,B,2] 0–8, `flips` bool [E,S,B], `epochs`, `hash`; `draw(seed, n_train, epochs, cfg)` — one generator); `augment(x_u8, crops, flips)` (float32 normalize → reflect-pad-4 → per-sample crop by advanced indexing → per-sample flip; pure, RNG-free).

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
    assert a.order.shape == (3, steps * cfg.batch_size)  # [E, S*B]
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

- [ ] **Step 2: FAIL.** **Step 3: Implement**

```python
# section 2 — DATA
CIFAR_MEAN = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1)
CIFAR_STD = torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1)


@dataclass
class DataBundle:
    train_x: torch.Tensor
    train_y: torch.Tensor
    val_x: torch.Tensor
    val_y: torch.Tensor
    test_x: torch.Tensor
    test_y: torch.Tensor


def split_indices(run_seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    perm = torch.randperm(50_000, generator=make_generator(derive(run_seed, "valsplit")))
    return perm[:45_000], perm[45_000:]


def load_data(cfg: Config, device: str, subset: int | None = None) -> DataBundle:
    import torchvision

    root = "runs/data"
    tr = torchvision.datasets.CIFAR10(root, train=True, download=True)
    te = torchvision.datasets.CIFAR10(root, train=False, download=True)
    x = torch.from_numpy(tr.data).permute(0, 3, 1, 2).contiguous()
    y = torch.tensor(tr.targets, dtype=torch.int64)
    train_idx, val_idx = split_indices(cfg.run_seed)
    if subset is not None:
        train_idx = train_idx[:subset]
    tx = torch.from_numpy(te.data).permute(0, 3, 1, 2).contiguous()
    ty = torch.tensor(te.targets, dtype=torch.int64)

    def to_device(t: torch.Tensor) -> torch.Tensor:
        return t.to(device)

    return DataBundle(
        to_device(x[train_idx]), to_device(y[train_idx]),
        to_device(x[val_idx]), to_device(y[val_idx]),
        to_device(tx), to_device(ty),
    )


@dataclass
class CommonFuture:
    order: torch.Tensor
    crops: torch.Tensor
    flips: torch.Tensor
    epochs: int
    hash: str

    @classmethod
    def draw(cls, seed: int, n_train: int, epochs: int, cfg: Config) -> CommonFuture:
        g = make_generator(seed)
        bs = cfg.batch_size
        steps = n_train // bs
        order = torch.stack(
            [torch.randperm(n_train, generator=g)[: steps * bs] for _ in range(epochs)]
        )
        crops = torch.randint(0, 9, (epochs, steps, bs, 2), generator=g, dtype=torch.uint8)
        flips = torch.rand(epochs, steps, bs, generator=g) < 0.5
        h = hashlib.sha256()
        for t in (order, crops, flips):
            h.update(t.numpy().tobytes())
        return cls(order, crops, flips, epochs, h.hexdigest())


def augment(x_u8: torch.Tensor, crops: torch.Tensor, flips: torch.Tensor) -> torch.Tensor:
    dev = x_u8.device
    xf = x_u8.to(torch.float32).div(255.0)
    xf = (xf - CIFAR_MEAN.to(dev)) / CIFAR_STD.to(dev)
    xp = torch.nn.functional.pad(xf, (4, 4, 4, 4), mode="reflect")
    n = xf.shape[0]
    ar = torch.arange(32, device=dev)
    ys = crops[:, 0].to(dev, torch.int64)[:, None] + ar
    xs = crops[:, 1].to(dev, torch.int64)[:, None] + ar
    bi = torch.arange(n, device=dev)[:, None, None]
    out = xp.permute(0, 2, 3, 1)[bi, ys[:, :, None], xs[:, None, :], :].permute(0, 3, 1, 2)
    return torch.where(flips.to(dev)[:, None, None, None], out.flip(-1), out).contiguous()
```

(`augment` was executed and verified correct — shape, crop-axis mapping, flip, zero RNG use — by review.)

- [ ] **Step 4: PASS.** **Step 5: Commit.**

---

### Task 3: TelemetryRecord, collection helpers, Normalizer

**Files:** modify section 3; create `tests/unit/kernel_demo/test_telemetry.py`.

**Interfaces (Produces):**
- `class TelemetryDivergence(RuntimeError)`.
- `@dataclass(frozen=True) TelemetryRecord` — exactly: `epoch: int`, `train_loss: float`, `val_loss: float`, `val_acc: float`, `train_loss_delta: float`, `val_loss_delta: float`, `grad_norm_mean: tuple[float, float, float]`, `grad_norm_var: tuple[float, float, float]`, `act_saturation: tuple[float, float, float]`, `weight_norm: tuple[float, float, float]`, `per_class_val_acc_std: float`, `confusion_entropy: float` (D3). `__post_init__` asserts every value finite else `TelemetryDivergence`. No other field, ever (blindness rule: every field a deterministic function of host state + logical epoch; no wall-clock/device/worker/pathology).
- `TELEMETRY_DIM = 20`; `EPOCH_FEATURE_IDX = 0`; `record_to_vector(r) -> Tensor[20]` (field order, epoch first; tuples flattened in stage order).
- `confusion_stats(logits, labels, n_classes=10) -> tuple[float, float]` — per-class accuracy std; entropy of the pooled off-diagonal confusion distribution.
- `class Normalizer` — per-feature median/IQR (IQR floored 1e-8): `fit(vectors)`, `apply(v)`, `to_json()`, `from_json(s)`, `Normalizer.identity()` classmethod (no-op, for tests).
- `build_record(...)` — the one construction site: takes epoch, losses/accs, per-stage grad-norm accumulations, saturation means (from `host.stage_stats`), weight norms, confusion stats; returns `TelemetryRecord`. Called only by the episode loop (Task 8).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_telemetry.py
import dataclasses

import pytest
import torch

from experiments.kernel_demo import (
    EPOCH_FEATURE_IDX,
    Normalizer,
    TELEMETRY_DIM,
    TelemetryDivergence,
    TelemetryRecord,
    confusion_stats,
    record_to_vector,
)


def _rec(**kw):
    base = dict(
        epoch=3, train_loss=1.2, val_loss=1.3, val_acc=0.41,
        train_loss_delta=-0.1, val_loss_delta=-0.05,
        grad_norm_mean=(1.0, 2.0, 3.0), grad_norm_var=(0.1, 0.2, 0.3),
        act_saturation=(0.5, 0.4, 0.3), weight_norm=(10.0, 11.0, 12.0),
        per_class_val_acc_std=0.05, confusion_entropy=2.1,
    )
    base.update(kw)
    return TelemetryRecord(**base)


def test_record_rejects_nonfinite():
    with pytest.raises(TelemetryDivergence):
        _rec(val_loss=float("inf"))
    with pytest.raises(TelemetryDivergence):
        _rec(grad_norm_var=(0.1, float("nan"), 0.3))


def test_blindness_no_forbidden_fields():
    names = {f.name for f in dataclasses.fields(TelemetryRecord)}
    for forbidden in ("pathology", "wall", "device", "worker", "time"):
        assert not any(forbidden in n for n in names)


def test_vector_epoch_first_and_normalizer_roundtrip():
    v = record_to_vector(_rec())
    assert v.shape == (TELEMETRY_DIM,)
    assert v[EPOCH_FEATURE_IDX] == 3.0
    n = Normalizer()
    n.fit([v, v * 2, v * 3])
    assert torch.allclose(n.apply(v * 2), torch.zeros(TELEMETRY_DIM), atol=1e-6)
    n2 = Normalizer.from_json(n.to_json())
    assert torch.allclose(n2.apply(v), n.apply(v))


def test_confusion_stats_separate_uniform_from_structured():
    labels = torch.arange(10).repeat(50)
    perfect = torch.nn.functional.one_hot(labels, 10).float() * 10
    confused = perfect.clone()
    wrong = torch.nn.functional.one_hot(torch.full((50,), 5), 10).float() * 10
    confused[labels == 3] = wrong
    std_p, _ = confusion_stats(perfect, labels)
    std_c, ent_c = confusion_stats(confused, labels)
    assert std_c > std_p
    assert ent_c < 2.0  # concentrated confusion → low off-diagonal entropy
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 4: Host CNN and the four pathologies — fixed 64-wide slot interface

**Files:** modify section 4; create `tests/unit/kernel_demo/test_host.py`.

**Interfaces (Produces):**
- `PATHOLOGIES = ("under_normalized", "channel_starved", "no_spatial_mix", "mild")`; `DESIGNED_WINNER = {"under_normalized": "norm", "channel_starved": "conv_heavy", "no_spatial_mix": "attn", "mild": "conv_light"}`.
- `class Host(nn.Module)` — 3 stages (Conv-BN-ReLU ×2 + `MaxPool2d(2)`), `nn.AdaptiveAvgPool2d(1)` GAP (the documented deterministic-backward case), `Linear(→10)`. **Healthy widths 24/64/80 ≈ 162k params** (D7). **Slot after stage2's pool → slot input `[B, 64, 8, 8]` for every pathology.** Pathologies change internal capacity only: `under_normalized` = same widths, BN→Identity, init gain ×2; `channel_starved` = stage2 internally 24→24 then 24→64; `no_spatial_mix` = stage2 all-1×1 (24→64); `mild` = stages 1/3 reduced to 20/72 (≈142k). `host.feat_channels == 64` constant; `host.forward_to_slot(x)` (stops at slot site — how `germinate` obtains τ-init features); `host.forward(x, slot: "Slot | None")` (PEP 563 forward reference; Task 6 defines `Slot`; only `slot is None`/`slot(h)` used at runtime); `host.attach_stat_hooks()` → `host.stage_stats["saturation"]` (per-stage zero-fraction of the last ReLU, overwritten per forward; the episode loop averages per epoch); `host.stage_modules()`.
- `build_host(pathology, init_seed) -> Host` — inside `rng_scope(make_generator(init_seed))`; appends `Host`'s class source to `_SEMANTIC_SURFACE`.
- `host_init_hash(host) -> str` — **standalone here** (sorted state_dict bytes, sha256); Task 7 rebinds it to the zero-normalized `state_hash`.

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
        assert 80_000 < n < 250_000, (p, n)  # all four, not one representative


def test_slot_interface_invariant_all_pathologies():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        feats = h.forward_to_slot(torch.randn(2, 3, 32, 32))
        assert feats.shape == (2, 64, 8, 8), p
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

**Interfaces (Produces):**
- `SEED_NAMES = ("norm", "attn", "conv_light", "conv_heavy")`.
- `class SeedDelta(nn.Module)` — `self.gain = nn.Parameter(torch.zeros(()))`; `forward(h) = self.gain * self.f(h)`; abstract `f`. Subclasses at C=64 (reviewer-computed): `NormSeed` `f = GroupNorm(8, 64)(h) − h` (129p); `AttnSeed` LN → explicit single-head qkv/out `Linear(64,16)`×3 + `Linear(16,64)`, no SDPA (~4.2k); `ConvLightSeed` depthwise 3×3 + pointwise **mid=64** + BN + ReLU + pointwise (8,897 — mid=16/32 would fail the budget floor at 2,657/4,737); `ConvHeavySeed` 3×3-BN-ReLU-3×3-BN, **bottleneck Cb=52** (60,137; valid band [31,77]). Internals standard-init; final BN γ=1; only the gain carries τ.
- `build_seed(name, channels, init_seed) -> SeedDelta` — inside `rng_scope`; appends each seed class source to `_SEMANTIC_SURFACE`.
- `tau_init(seed, host_feats, cfg) -> float` — caller supplies `host_feats` from `host.forward_to_slot` under `host.eval()`/`no_grad` (host BN protection, spec); the measurement runs the seed **in `train()` mode under `no_grad`** (D11 — the mode of the first TRAINING step; seed BN buffers mutated by the fixed measurement batch are deterministic birth state); `g = cfg.tau * rms(host_feats) / max(rms(f0), cfg.tau_eps)`; sets and returns `g`.
- `split_decay_groups(module) -> (decay: list[tuple[str, Tensor]], no_decay: list[tuple[str, Tensor]])` — **rule: `param.ndim <= 1 or name.endswith("gain") → no-decay`** (coextensive with the spec's gain/affines/biases list; robust to `nn.Sequential` integer names, where substring rules silently mis-file BN affines).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_seeds.py
import pytest
import torch

from experiments.kernel_demo import (
    Config,
    SEED_NAMES,
    build_seed,
    split_decay_groups,
    tau_init,
)


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
    s.train()  # measure in the SAME mode tau_init calibrated (D11)
    with torch.no_grad():
        ratio = s(h).pow(2).mean().sqrt() / h.pow(2).mean().sqrt()
    assert abs(ratio.item() - cfg.tau) / cfg.tau < 0.05


def test_param_budgets_pinned():
    counts = {
        n: sum(p.numel() for p in build_seed(n, 64, 1).parameters())
        for n in SEED_NAMES
    }
    assert counts["norm"] < 300
    assert 2_000 < counts["attn"] < 12_000
    assert 5_000 < counts["conv_light"] < 20_000
    assert 35_000 < counts["conv_heavy"] < 90_000


def test_no_decay_rule_catches_sequential_bn_affines():
    s = build_seed("conv_heavy", 64, 1)
    decay, no_decay = split_decay_groups(s)
    assert any(n.endswith("gain") for n, _ in no_decay)
    assert any(isinstance(m, torch.nn.BatchNorm2d) for m in s.modules())
    for n, p in decay:
        assert p.ndim > 1, f"1-d param {n} leaked into decay group"
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 6: Slot lifecycle — STE, α/β schedules, trust region, optimizer contract

**Files:** modify section 6; create `tests/unit/kernel_demo/test_slot.py`.

**Interfaces (Produces):**
- `Stage` — `enum.Enum` with members `DORMANT, GERMINATED, TRAINING, BLENDING, FOSSILIZING, FOSSILIZED` (GERMINATED zero-duration, D12).
- `cosine_ease(p: float) -> float` = `0.5 * (1 - math.cos(math.pi * clamp01(p)))`.
- `class Slot(nn.Module)` — attrs `stage=Stage.DORMANT`, `seed: SeedDelta | None = None`, `alpha=0.0`, `beta=0.0`, `last_delta`, `last_h`. Forward:

```python
def forward(self, h: torch.Tensor) -> torch.Tensor:
    if self.stage in (Stage.DORMANT, Stage.GERMINATED) or self.seed is None:
        return h
    # hin is VALUE-equal to h for every beta, but bitwise-equal only at
    # beta in {0, 1}; FOSSILIZING's fractional beta is a numerically-close,
    # non-bitwise blend by design (post-TRAINING, outside every bitwise
    # assertion window).
    hin = h.detach() * (1.0 - self.beta) + h * self.beta
    delta = self.seed(hin)
    self.last_delta = delta
    self.last_h = h
    if self.stage is Stage.TRAINING:
        return h + (delta - delta.detach())  # STE: forward value == h
    return h + self.alpha * delta
```

- `Slot.trust_region_loss(cfg) -> Tensor` = `cfg.lam * last_delta.pow(2).mean() / last_h.detach().pow(2).mean().clamp_min(1e-12)` when TRAINING else 0. λ=1.0 sits inside the stability bound λ < 1/seed_lr ≈ 20; stationary point `Δ* = −(∂L/∂Δ)·‖h‖²/(2λ)`.
- `Slot.rms_ratio() -> float` — `RMS(last_delta)/RMS(last_h)`; **the named owner of `ArmResult.rms_ratio_blend_entry`**, read by the fan executor at the first BLENDING step (gate 5's only input).
- `Slot.step_tick(...)`/`Slot.epoch_tick(...)` — per spec: TRAINING `stage_k` epochs; BLENDING `stage_m` epochs, α = `cosine_ease((blend_step+1)/(stage_m*steps_per_epoch))` per optimizer step; FOSSILIZING `stage_f` epochs, α=1, β cosine 0→1 per step; FOSSILIZED α=β=1. `Slot.alpha_beta_log: list[tuple[float, float]]` — appended once per epoch tick (epoch-end values); **the data source for the report's α/β trajectory plot** (carried into `ArmResult`).
- `build_optimizer(host, cfg) -> torch.optim.SGD` — Nesterov, `cfg.lr/momentum`, decay + no-decay groups via `split_decay_groups`. Constant LR is load-bearing twice: no scheduler state in snapshots, and `lr_scheduler` captures `base_lrs` positionally at construction so a group appended at germination would mismatch — constant LR removes the class structurally.
- `append_seed_group(opt, seed, cfg)` — two groups (decay/no-decay) at `cfg.seed_lr`, fresh momentum.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_slot.py
import torch

from experiments.kernel_demo import (
    Config,
    Slot,
    Stage,
    append_seed_group,
    build_host,
    build_optimizer,
    build_seed,
    cosine_ease,
    tau_init,
)


def _armed_slot(stage: Stage) -> tuple[Config, Slot, torch.Tensor]:
    cfg = Config()
    slot = Slot()
    slot.seed = build_seed("conv_light", 64, 7)
    h = torch.randn(4, 64, 8, 8, requires_grad=True)
    tau_init(slot.seed, h.detach(), cfg)
    slot.stage = stage
    return cfg, slot, h


def test_training_forward_is_value_exact_host():
    _, slot, h = _armed_slot(Stage.TRAINING)
    assert torch.equal(slot(h), h)


def test_training_isolates_host_gradient_but_trains_seed():
    _, slot, h = _armed_slot(Stage.TRAINING)
    slot(h).sum().backward()
    assert torch.allclose(h.grad, torch.ones_like(h))
    g = slot.seed.gain.grad
    assert g is not None and g.abs().item() > 0


def test_blending_trains_seed_while_host_gradient_isolated():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha, slot.beta = 0.5, 0.0
    slot(h).sum().backward()
    assert torch.allclose(h.grad, torch.ones_like(h))  # beta=0: input detached
    g = slot.seed.gain.grad
    assert g is not None and g.abs().item() > 0  # BLENDING must TRAIN the seed


def test_trust_region_positive_only_in_training():
    cfg, slot, h = _armed_slot(Stage.TRAINING)
    slot(h)
    assert slot.trust_region_loss(cfg).item() > 0


def test_rms_ratio_reads_last_forward():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha = 0.01
    slot(h)
    assert slot.rms_ratio() > 0


def test_optimizer_groups_and_seed_append():
    cfg = Config()
    host = build_host("mild", 1)
    opt = build_optimizer(host, cfg)
    n0 = len(opt.param_groups)
    append_seed_group(opt, build_seed("norm", 64, 2), cfg)
    assert len(opt.param_groups) == n0 + 2
    assert opt.param_groups[-1]["weight_decay"] == 0.0
    assert opt.param_groups[-1]["lr"] == cfg.seed_lr


def test_cosine_ease_endpoints():
    assert cosine_ease(0.0) == 0.0
    assert abs(cosine_ease(1.0) - 1.0) < 1e-12
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit + `wc -l` (~500).**

---

### Task 7: Determinism — Class 1 knobs, zero-normalized hashing, env block

**Files:** modify section 7; create `tests/unit/kernel_demo/test_determinism.py`.

**Interfaces (Produces):**
- `enable_class1()` (real body): `CUBLAS_WORKSPACE_CONFIG` — if unset, set `:4096:8`; if set to anything else, `raise RuntimeError` (a tolerated stray value is a silent Class-1 relaxation); then deterministic algorithms, cudnn flags, TF32 off ×2.
- `state_hash(module) -> str` — sorted `state_dict()`, `.detach().cpu().contiguous()`, **`torch.where(v == 0, zeros, v)`** (D8), sha256 over key + bytes. `host_init_hash` is rebound to this (Task 4's standalone version retired).
- `env_block(device, worker_count) -> dict` (torch/cuda/cudnn/python versions, GPU name, TF32 flags, worker_count, device_index); `REPLAY_REFUSAL_KEYS` (worker_count/device_index provenance-only — the composition of worker_count-in-key + single-worker replay was a proven deadlock).
- `FORBIDDEN_RELAXATIONS: tuple[str, ...]` — spec list + `torch.compile` (D10).
- `_SEMANTIC_SURFACE` extended with `Slot`, `state_hash`.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_determinism.py
import pytest
import torch

from experiments.kernel_demo import (
    REPLAY_REFUSAL_KEYS,
    enable_class1,
    env_block,
    state_hash,
)


def test_class1_flags_set(monkeypatch):
    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    enable_class1()
    assert torch.backends.cudnn.deterministic
    assert not torch.backends.cudnn.benchmark
    assert not torch.backends.cuda.matmul.allow_tf32
    assert torch.are_deterministic_algorithms_enabled()


def test_enable_class1_rejects_stray_cublas_config(monkeypatch):
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    with pytest.raises(RuntimeError, match="CUBLAS_WORKSPACE_CONFIG"):
        enable_class1()


def test_state_hash_canonicalizes_signed_zero():
    m1 = torch.nn.Linear(2, 2)
    m2 = torch.nn.Linear(2, 2)
    m2.load_state_dict(m1.state_dict())
    with torch.no_grad():
        m1.bias[0] = 0.0
        m2.bias[0] = -0.0
    assert state_hash(m1) == state_hash(m2)


def test_env_block_keys_and_refusal_subset():
    e = env_block("cpu", worker_count=4)
    assert set(REPLAY_REFUSAL_KEYS) <= set(e)
    assert "worker_count" in e and "worker_count" not in REPLAY_REFUSAL_KEYS
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 8: Episode runner — epoch loop, snapshot, germination

**Files:** modify section 8; create `tests/unit/kernel_demo/conftest.py`, `tests/unit/kernel_demo/test_episode.py`.

**Interfaces:**
- Consumes (itemized): `Config`, `DataBundle`, `CommonFuture`, `augment`, `TelemetryRecord`/`TelemetryDivergence`/`build_record`/`confusion_stats`, `Host`/`build_host`, `Slot`/`Stage`, `build_seed`/`tau_init`, `build_optimizer`/`append_seed_group`, `state_hash`, `derive`/`make_generator`/`rng_scope`.
- Produces:
  - `@dataclass EpisodeCtx`: `cfg, data, device, episode_seed, pathology, future, host, opt, slot, telemetry: list, curves_val: list, curves_test: list | None, read_test: bool` (`curves_test is None` iff `read_test=False` — one convention, no empty-list ambiguity).
  - `make_episode(cfg, data, device, episode_seed, read_test=False) -> EpisodeCtx` — pathology `derive(seed,"pathology") % 4`; host `derive(seed,"host-init")` in `rng_scope`; future `derive(seed,"future",0)`; fresh DORMANT `Slot`; `build_optimizer`.
  - `train_one_epoch(ctx, epoch)` — reshapes `future.order[epoch]` to `(steps, batch)`; per step: `augment` → `host(x, slot)` → CE (+ `slot.trust_region_loss` in TRAINING) → step; per-stage grad-norm accumulation; `slot.step_tick`; epoch end: `slot.epoch_tick`, val eval under no_grad, `build_record` appended (a `TelemetryDivergence` propagates to the caller — Task 9 owns the divergence conventions), `curves_val.append`, `curves_test.append` iff `read_test`.
  - `evaluate_acc(host, slot, x, y, device, chunk)` — eval-mode, chunked (`cfg.eval_chunk`), prior mode restored.
  - `@dataclass Snapshot`: `host_state: dict` (deep-cloned tensors incl. BN buffers), `opt_state: dict` (deepcopy; **always the 2-group never-germinated base state** — snapshots are taken only on the base path; Task 9's arm-local materialization is what makes this sufficient), `cpu_rng`, `cuda_rng`, `epoch`.
  - `take_snapshot(ctx) -> Snapshot`. (There is **no `restore_snapshot`** — arm-local materialization replaced in-place restore; arms are built fresh from snapshot values.)
  - `germinate(ctx, seed_name) -> float` — seed at `channels=ctx.host.feat_channels` from `derive(episode_seed,"arm",seed_name)` in `rng_scope`; τ-init features via `ctx.host.forward_to_slot(fixed_val_batch)` under `host.eval()`/`no_grad`; `append_seed_group`; `slot.seed = seed; slot.stage = Stage.TRAINING`; returns `g`.
  - `end_state_R(curve) -> float` — mean of the final 3 entries (the spec's reward).
- `conftest.py`:

```python
# tests/unit/kernel_demo/conftest.py
import torch

from experiments.kernel_demo import DataBundle


def make_tiny_bundle(device: str = "cpu") -> DataBundle:
    # INVARIANT: intentionally seeded with a hardcoded literal — every call
    # returns byte-identical data; fan/episode reproducibility tests depend
    # on it. Do NOT parametrize the seed or "improve" this helper.
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

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_episode.py
import dataclasses

import torch

from experiments.kernel_demo import (
    Config,
    SEED_NAMES,
    end_state_R,
    germinate,
    make_episode,
    state_hash,
    take_snapshot,
    train_one_epoch,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = dataclasses.replace(Config(), horizon=4, batch_size=64, stage_k=1, stage_m=1, stage_f=1)


def _run_hash(seed: int) -> str:
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", seed)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    return state_hash(ctx.host)


def test_same_seed_same_episode_cpu_bitwise():
    assert _run_hash(11) == _run_hash(11)
    assert _run_hash(11) != _run_hash(12)


def test_snapshot_captures_restorable_state():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
    train_one_epoch(ctx, 0)
    snap = take_snapshot(ctx)
    h_at_snap = state_hash(ctx.host)
    train_one_epoch(ctx, 1)  # ctx moves on; snapshot must not
    fresh = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
    fresh.host.load_state_dict(snap.host_state)
    assert state_hash(fresh.host) == h_at_snap


def test_germinate_leaves_host_bn_stats_bitwise_unchanged():
    for name in SEED_NAMES:
        ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
        train_one_epoch(ctx, 0)
        before = state_hash(ctx.host)
        germinate(ctx, name)  # tau-init runs host in eval/no_grad
        assert state_hash(ctx.host) == before, name


def test_read_test_wall():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 22, read_test=False)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    assert ctx.curves_test is None


def test_tiny_bundle_byte_identical_across_calls():
    a, b = make_tiny_bundle(), make_tiny_bundle()
    assert torch.equal(a.train_x, b.train_x)
    assert torch.equal(a.val_y, b.val_y)


def test_end_state_r():
    assert end_state_R([0.1, 0.2, 0.3, 0.4, 0.5]) == (0.3 + 0.4 + 0.5) / 3
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 9: Fan executor — arm-local materialization, twin, null-seed, diverged conventions

**Files:** modify section 9; create `tests/unit/kernel_demo/test_fan.py`.

**Interfaces:**
- Consumes (itemized): Task 8's API (`EpisodeCtx`, `make_episode`, `train_one_epoch`, `Snapshot`, `take_snapshot`, `germinate`, `end_state_R`), `state_hash`, `Stage`, `Slot`, `build_optimizer`, `Config`.
- Produces:
  - `class TwinDivergence(RuntimeError)` — carries `first_bad_epoch: int`.
  - `@dataclass ArmResult`: `name: str`, `status: str` ("ok"|"diverged"), `r_val: float`, `r_test: float | None`, `curve_val: list[float]`, `curve_test: list[float] | None`, `init_seed: int`, `g_at_init: float | None`, `rms_ratio_blend_entry: float | None` (from `Slot.rms_ratio()` at the first BLENDING step), `hash_after_training: str | None` (every arm), `host_hashes: list[str] | None` (noop/nullseed arms), `alpha_beta_log: list[tuple[float, float]] | None` (from `Slot.alpha_beta_log` — the α/β plot's data source).
  - `@dataclass BaseTrace`: `host_hashes: list[str]`, `curve_val: list[float]`, `curve_test: list[float] | None`, `snapshots: dict[int, Snapshot]` (captured at the scheduled fan epochs during the single base pass), `status: str`, `diverged_at: int | None`.
  - `run_base(ctx, cfg, fan_epochs: tuple[int, ...]) -> BaseTrace` — **a thin wrapper over the same inner loop `run_arm` uses** (one loop, two call sites — base/twin drift is structurally impossible). Base divergence: status recorded, `r_noop = cfg.diverged_r`, hashes kept to the divergence epoch, fans scheduled after it are skipped (recorded).
  - `run_arm(cfg, data, device, episode_seed, pathology, future, snap, arm_name, read_test) -> ArmResult` — **arm-local materialization**: fresh host (same init seed, then `load_state_dict(snap.host_state)`), fresh DORMANT `Slot`, fresh 2-group optimizer loading `snap.opt_state` (loaded on a fresh 2-group optimizer *before* any `append_seed_group`, so `load_state_dict`'s unconditional group-count check can never fire), RNG states restored; `arm_name` ∈ `SEED_NAMES` germinates, `"noop"` doesn't, `"nullseed"` germinates `conv_light` **then `seed.gain.data.zero_()` and `gain.requires_grad_(False)`** (germinate τ-inits nonzero — the explicit zeroing is the step an implementer would otherwise miss); runs `snap.epoch → horizon`. Divergence (`TelemetryDivergence`/non-finite loss): `status="diverged"`, `r = cfg.diverged_r` both units, curves truncated. Records `host_hashes` per epoch for noop/nullseed, `hash_after_training` for all arms.
  - `run_fan(cfg, data, device, episode_seed, pathology, future, snap, base: BaseTrace, read_test, include_nullseed=False) -> tuple[list[ArmResult], dict]` — sequential: 4 seed arms + twin (= `run_arm(..., "noop")`; its `host_hashes` must equal `base.host_hashes[snap.epoch:]`, else `TwinDivergence(first_bad_epoch)`); `include_nullseed` adds the null-seed arm (collection wires it on a 1-in-10 subsample — Task 15). Cross-arm assertion: every finite arm's `hash_after_training == ` the twin's hash at that epoch (non-finite Δ ⇒ arm divergence, not a harness abort). **Null-seed mismatch while the twin holds is a HARD STOP** — the zero-normalized hash *is* the spec's value-exact check; there is no weaker fallback, curves are never a comparand.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_fan.py
import dataclasses

import pytest
import torch

import experiments.kernel_demo as kd
from experiments.kernel_demo import (
    Config,
    TwinDivergence,
    make_episode,
    run_arm,
    run_base,
    run_fan,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = dataclasses.replace(
    Config(), horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3)
)
FAN_EPOCH = 2


def _base(seed: int = 31):
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", seed)
    trace = run_base(ctx, CFG, fan_epochs=(FAN_EPOCH,))
    return ctx, trace


def test_twin_matches_base_bitwise():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    arms, meta = run_fan(
        CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, base, False
    )
    assert meta["twin_ok"]
    assert {a.name for a in arms} == {"norm", "attn", "conv_light", "conv_heavy", "noop"}


def test_corrupted_base_hashes_trip_twin_with_epoch():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    bad = dataclasses.replace(base, host_hashes=[*base.host_hashes[:3], "dead", *base.host_hashes[4:]])
    with pytest.raises(TwinDivergence) as ei:
        run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, bad, False)
    assert ei.value.first_bad_epoch == 3


def test_two_arms_from_one_snapshot_no_optimizer_leakage():
    # The class three reviewers hit: arm 1's seed groups must not touch arm 2.
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "conv_heavy", False)
    noop = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "noop", False)
    assert noop.host_hashes == base.host_hashes[FAN_EPOCH:]


def test_nullseed_arm_reproduces_base_hashes_exactly():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    res = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "nullseed", False)
    assert res.host_hashes == base.host_hashes[FAN_EPOCH:]  # hash lists, never curves


def test_cross_arm_assertion_fires_on_injected_corruption(monkeypatch):
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    real = kd.state_hash
    calls = {"n": 0}

    def corrupt_third(module):
        calls["n"] += 1
        return "corrupt" if calls["n"] == 3 else real(module)

    monkeypatch.setattr(kd, "state_hash", corrupt_third)
    with pytest.raises((AssertionError, TwinDivergence)):
        run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, base, False)
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 10: Fan records and the store — schema, shards, split walls, durability

**Files:** modify section 10; create `tests/unit/kernel_demo/test_store.py`.

**Interfaces (Produces):**
- `class SplitViolation(RuntimeError)`.
- `@dataclass FanRecord`: `schema_version: int`, `kind: str` ∈ {`fan`, `refan`, `policy_run`, `preflight_iter`, `extension_event`, `void_event`}, `episode_seed: int`, `seed_namespace: str` ∈ {dev, preflight, train, eval}, `split_role: str` ∈ {preflight, train, tune, eval}, `pathology_id: str`, `fan_epoch: int | None`, `refan_k: int | None`, `schedule_id: str` (= sha256 of `("uniform-no-replacement", cfg.window, cfg.fans_per_episode)` canonical string — now defined), `policy_checkpoint_id: str | None`, `iteration: int | None` (preflight_iter counter), `config_hash: str`, `frozen_block_hash: str`, `manifest_hash: str | None` (None pre-freeze), `common_future_hash: str`, `host_init_hash: str`, `env: dict`, `arms: list[dict]` (ArmResult-as-dict), `telemetry: list[dict]`, `decisions: list[dict] | None` (**policy_run payload**: per-epoch `{epoch, p, action}` + `germination_epoch`), `gate_results: dict | None` (**preflight_iter payload**), `fan_id: str`.
- `fan_id` = sha256 over the **full identity tuple** `(episode_seed, fan_epoch, kind, refan_k, policy_checkpoint_id, iteration)` — comparator runs and preflight iterations are distinct identities. **`Store.merge()` asserts uniqueness for `kind ∈ {fan, refan}` records within one `manifest_hash` generation** (the duplication backstop) — event/policy_run/preflight kinds are exempt from the collision assert but still carry unique ids.
- `encode_record(r) -> str` / `decode_record(line) -> FanRecord` — JSON; non-finite → `null` recursively; tuples become lists (consumers take dicts/lists); **`decode_record` asserts `schema_version == SCHEMA_VERSION`** and refuses otherwise with a message naming the migration rule: **post-collection schema changes are additive-only** (decoder fills absent new fields with `None`); a non-additive bump pre-collection wipes scratch stores; a non-additive bump post-collection is an owner decision (re-collect vs. translate), never silent.
- `class Store(root)`: `shard_path(worker_id)` → `shards/worker_{id}.jsonl`; `append(worker_id, record)` (write + flush; **`os.fsync` every `cfg.fsync_every` records and on close** — durability target: host-level failure loses ≤ fsync_every records, process crash loses none); `merge() -> list[FanRecord]` sorted `(episode_seed, fan_epoch, kind, refan_k)`; `load(split_role, kinds=("fan",))` filter.
- `load_for_training(store) -> list[FanRecord]` — returns train+tune fans; **re-checks every record it yields** and raises `SplitViolation` on `split_role == "eval"` or `kind != "fan"` (the guard is on the yield path, not vacuously behind the filter). `_assert_trainable(records)` is the shared check, callable directly.
- `train_tune_split` happens **at collection time**: `split_role = "tune" if derive(episode_seed, "tune-split") % 5 == 0 else "train"` — recorded per episode, never re-split downstream.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_store.py
import dataclasses

import pytest

from experiments.kernel_demo import (
    SCHEMA_VERSION,
    SplitViolation,
    Store,
    _assert_trainable,
    decode_record,
    encode_record,
    load_for_training,
    make_fan_record,
)


def _rec(episode_seed=1, fan_epoch=5, split_role="train", kind="fan", **kw):
    # make_fan_record derives fan_id from the identity tuple — tests never
    # hardcode fan_id.
    return make_fan_record(
        kind=kind, episode_seed=episode_seed, seed_namespace="train",
        split_role=split_role, pathology_id="mild", fan_epoch=fan_epoch,
        refan_k=None, schedule_id="s", policy_checkpoint_id=None,
        iteration=None, config_hash="c", frozen_block_hash="f",
        manifest_hash=None, common_future_hash="h", host_init_hash="i",
        env={"torch": "2.13"},
        arms=[{
            "name": "noop", "status": "ok", "r_val": 0.4, "r_test": None,
            "curve_val": [0.1, float("nan")], "curve_test": None,
            "init_seed": 0, "g_at_init": None, "rms_ratio_blend_entry": None,
            "hash_after_training": None, "host_hashes": None,
            "alpha_beta_log": None,
        }],
        telemetry=[{"epoch": 1, "grad_norm_mean": [1.0, 2.0, 3.0]}],
        decisions=None, gate_results=None, **kw,
    )


def test_nonfinite_roundtrips_as_null_and_tuples_as_lists():
    line = encode_record(_rec())
    assert "NaN" not in line
    r = decode_record(line)
    assert r.arms[0]["curve_val"][1] is None
    assert r.telemetry[0]["grad_norm_mean"] == [1.0, 2.0, 3.0]


def test_decode_refuses_wrong_schema_version():
    line = encode_record(_rec()).replace(
        f'"schema_version": {SCHEMA_VERSION}', '"schema_version": 999'
    )
    with pytest.raises(ValueError, match="schema_version"):
        decode_record(line)


def test_shards_merge_content_ordered_and_unique(tmp_path):
    s = Store(tmp_path)
    s.append(1, _rec(episode_seed=9, fan_epoch=7))
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=9))
    got = [(r.episode_seed, r.fan_epoch) for r in s.merge()]
    assert got == [(2, 5), (2, 9), (9, 7)]


def test_merge_rejects_duplicate_fan_identity(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=5))  # same identity, other shard
    with pytest.raises(ValueError, match="duplicate fan_id"):
        s.merge()


def test_comparator_policy_runs_do_not_collide(tmp_path):
    s = Store(tmp_path)
    a = _rec(kind="policy_run", split_role="eval", policy_checkpoint_id="trained")
    b = _rec(kind="policy_run", split_role="eval", policy_checkpoint_id="random")
    assert a.fan_id != b.fan_id
    s.append(0, a)
    s.append(0, b)
    assert len(s.merge()) == 2  # no false duplicate trip


def test_split_wall_fires_on_the_yield_path(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(split_role="train"))
    s.append(0, _rec(episode_seed=3, split_role="eval"))
    ok = load_for_training(s)
    assert all(r.split_role in ("train", "tune") for r in ok)
    with pytest.raises(SplitViolation):
        _assert_trainable([_rec(episode_seed=4, split_role="eval")])
    with pytest.raises(SplitViolation):
        _assert_trainable([_rec(episode_seed=5, kind="refan")])
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit + `wc -l` (~850).**

---

### Task 11: Policy — trunk, factored head, deployment rule, masks

**Files:** modify section 11; create `tests/unit/kernel_demo/test_policy.py`.

**Interfaces (Produces):**
- `class Policy(nn.Module)` — built in `rng_scope(gen)`. Embed MLP `TELEMETRY_DIM → d_model → d_model` (GELU); learned positional embedding (`horizon` slots); 2 hand-rolled blocks — **explicit-matmul self-attention (single head, attention dim = d_model = 64, no biases in projections, causal mask) + MLP ratio 4** — head `Linear(d_model, 5)`: `[:, 0]` NOW logit, `[:, 1:]` seed logits. Named submodules `policy.now_head`/`policy.seed_head` (test-addressable). Param count ~108k.
- `Policy.forward(tokens [B,T,20], lengths [B]) -> (p_logit [B], seed_logits [B,4])` — hidden state at `lengths−1`.
- `decide_live(policy, normalizer, telemetry, epoch, cfg) -> tuple[bool, str | None]` — outside the **inclusive** window `[5, 15]` returns `(False, None)`; else **normalize first, then mask (if any), then forward**; fires iff `sigmoid(p_logit) > 0.5` (deterministic — no sampling slot at eval); seed = argmax (deterministic tie-break: lowest index).
- `schedule_only_mask(t) -> Tensor` — **`[..., EPOCH_FEATURE_IDX]`** (correct on 1-D and [B,T,D]; a dim-0 implementation zeroes the batch axis and silently corrupts the schedule-only comparator).
- `query_teacher_forced(policy, normalizer, telemetry_prefix, cfg) -> tuple[float, dict[str, float]]` — `(p, {seed: π})` at the prefix's last epoch.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_policy.py
import torch

from experiments.kernel_demo import (
    Config,
    EPOCH_FEATURE_IDX,
    Normalizer,
    Policy,
    TELEMETRY_DIM,
    decide_live,
    make_generator,
    schedule_only_mask,
)
from tests.unit.kernel_demo.test_telemetry import _rec


def _rec_at(epoch: int):
    return _rec(epoch=epoch)


def test_shapes_and_determinism():
    pol = Policy(Config(), make_generator(1))
    x = torch.randn(3, 7, TELEMETRY_DIM)
    lengths = torch.tensor([7, 5, 2])
    p1, s1 = pol(x, lengths)
    p2, s2 = pol(x, lengths)
    assert p1.shape == (3,) and s1.shape == (3, 4)
    assert torch.equal(p1, p2)


def test_causality_future_tokens_do_not_leak():
    pol = Policy(Config(), make_generator(1))
    x = torch.randn(1, 7, TELEMETRY_DIM)
    lengths = torch.tensor([4])
    p_a, s_a = pol(x, lengths)
    x2 = x.clone()
    x2[0, 5:] += 100.0
    p_b, s_b = pol(x2, lengths)
    assert torch.equal(p_a, p_b) and torch.equal(s_a, s_b)


def test_policy_param_count_pinned():
    n = sum(p.numel() for p in Policy(Config(), make_generator(1)).parameters())
    assert 70_000 < n < 130_000


def test_schedule_only_mask_batched_and_1d():
    v = torch.arange(TELEMETRY_DIM, dtype=torch.float32)
    m = schedule_only_mask(v)
    assert m[EPOCH_FEATURE_IDX] == v[EPOCH_FEATURE_IDX]
    assert m.abs().sum() == v[EPOCH_FEATURE_IDX].abs()
    x = torch.randn(2, 7, TELEMETRY_DIM)
    mx = schedule_only_mask(x)
    assert torch.equal(mx[..., EPOCH_FEATURE_IDX], x[..., EPOCH_FEATURE_IDX])
    others = [i for i in range(TELEMETRY_DIM) if i != EPOCH_FEATURE_IDX]
    assert mx[..., others].abs().sum() == 0


def test_decide_live_window_boundaries_inclusive():
    pol = Policy(Config(), make_generator(1))
    nz = Normalizer.identity()
    tele = [_rec_at(e) for e in range(20)]
    for epoch, allowed in [(4, False), (5, True), (15, True), (16, False)]:
        fire, _ = decide_live(pol, nz, tele[: epoch + 1], epoch, Config())
        if not allowed:
            assert fire is False
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 12: Learning — objectives, frozen temperatures, warm-up, tune checkpointing

**Files:** modify section 12; create `tests/unit/kernel_demo/helpers.py`, `test_learning.py`.

**Interfaces (Produces):**
- `fan_to_example(rec, normalizer) -> dict` — `{tokens [T,20] normalized, length, r: Tensor[4] (val units, SEED_NAMES order, diverged already 0.10), r_noop: float}`; consumes decoded dicts/lists.
- `measure_fan_density(records, unit="val") -> dict` — keys `best_minus_second`, `best_minus_noop` (within-fan means).
- **Temperature mapping (pre-registered, recorded in the FreezeManifest):** `beta_which = cfg.beta_which_frac * density["best_minus_second"]`; `beta_now = density["best_minus_noop"] / cfg.beta_now_div`.
- `warmup_schedule(step, total_steps, warmup_frac) -> bool` — pure; `False` during warm-up (J_now disabled).
- `policy_loss(policy, batch, cfg, *, beta_which, beta_now, enable_now, mask_fn=None) -> Tensor` — **takes both temperatures explicitly** (a single scalar cannot honor the two-key mapping):

```python
def policy_loss(policy, batch, cfg, *, beta_which, beta_now, enable_now, mask_fn=None):
    tokens, lengths, r, r_noop = batch          # [B,T,20], [B], [B,4], [B]
    if mask_fn is not None:
        tokens = mask_fn(tokens)                # masks apply POST-normalization
    p_logit, seed_logits = policy(tokens, lengths)
    pi = seed_logits.softmax(-1)
    j_which = (pi * r).sum(-1)
    ent_pi = -(pi * pi.clamp_min(1e-8).log()).sum(-1)
    loss = -(j_which + beta_which * ent_pi)
    if enable_now:
        p = torch.sigmoid(p_logit)
        adv_mix = (pi.detach() * r).sum(-1)     # sg[pi] — spec §Learning
        j_now = p * adv_mix + (1 - p) * r_noop
        ent_p = -(
            p * p.clamp_min(1e-8).log()
            + (1 - p) * (1 - p).clamp_min(1e-8).log()
        )
        loss = loss - (j_now + beta_now * ent_p)
    return loss.mean()
```

- `train_policy(records, cfg, normalizer, gen, *, frozen_density, steps=None, mask_fn=None) -> tuple[Policy, dict]` — asserts records trainable (`_assert_trainable`); derives both betas from `frozen_density` via the mapping (never recomputes density from `records`); `steps` defaults `cfg.policy_steps` (tests pass small values — the <60 s target is a consequence of the step count, never a wall-clock assertion); Adam(`cfg.policy_lr`), batches `cfg.policy_batch_size` drawn by `gen`; `enable_now = warmup_schedule(step, steps, cfg.warmup_frac)`; tune-scored checkpointing (records arrive pre-split into train/tune roles; never re-split); returns `(best policy, {"curve": [...], "beta_which": ..., "beta_now": ...})`.
- `sign_flip_pvalue(lifts, n, seed) -> float` (one-sided, `(count+1)/(n+1)`).
- `money_chart_permutation_pvalue(pathologies, picks, designed, n, seed) -> tuple[int, float]` — classes-matched count (modal pick per pathology class vs designed winner; **deterministic lexicographic tie-break**) + permutation p (shuffle pathology labels).
- `helpers.py`: `synthetic_fans(n, seed)` (plants feature→winner rule; assigns train/tune roles by the episode rule), `synthetic_holdout(records)` (the tune-role episodes — a genuine holdout under the split actually used), `synthetic_agreement(policy, records) -> float`, `synthetic_batch(seed)` (one collated batch), `adversarial_batch_with_divergent_arm(seed)` (one arm at 0.10, others ~0.70 — the N10 regime).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_learning.py
import dataclasses

import pytest
import torch

from experiments.kernel_demo import (
    Config,
    Normalizer,
    Policy,
    SplitViolation,
    make_generator,
    money_chart_permutation_pvalue,
    policy_loss,
    sign_flip_pvalue,
    train_policy,
    warmup_schedule,
)
from tests.unit.kernel_demo.helpers import (
    adversarial_batch_with_divergent_arm,
    synthetic_agreement,
    synthetic_batch,
    synthetic_fans,
    synthetic_holdout,
)

DENSITY = {"best_minus_second": 0.05, "best_minus_noop": 0.08}


def test_policy_learns_synthetic_mapping_on_true_holdout():
    recs = synthetic_fans(n=120, seed=5)
    pol, info = train_policy(
        recs, Config(), Normalizer.identity(), make_generator(0),
        frozen_density=DENSITY, steps=600,
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

    def head_grads(enable_now):
        loss = policy_loss(
            pol, batch, cfg, beta_which=0.01, beta_now=0.036, enable_now=enable_now
        )
        return torch.autograd.grad(loss, pol.seed_head.parameters())

    for a, b in zip(head_grads(False), head_grads(True), strict=True):
        assert torch.allclose(a, b, atol=1e-6)  # WHICH trains at 1x regardless of p


def test_now_head_gradient_alive_with_divergent_arm_present():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    batch = adversarial_batch_with_divergent_arm(seed=3)
    loss = policy_loss(pol, batch, cfg, beta_which=0.01, beta_now=0.036, enable_now=True)
    grads = torch.autograd.grad(loss, pol.now_head.parameters(), allow_unused=True)
    assert any(g is not None and g.abs().sum() > 0 for g in grads)


def test_train_policy_rejects_untrainable_records():
    recs = synthetic_fans(n=10, seed=1)
    recs[3] = dataclasses.replace(recs[3], kind="refan")
    with pytest.raises(SplitViolation):
        train_policy(recs, Config(), Normalizer.identity(), make_generator(0),
                     frozen_density=DENSITY, steps=10)


def test_money_chart_permutation_four_classes():
    # Two classes at 10/10 give P(both rows match under shuffle) ~ 0.33 —
    # mathematically incapable of clearing 0.05; four classes are required.
    paths = [c for c in "abcd" for _ in range(10)]
    picks = [w for w in "wxyz" for _ in range(10)]
    designed = dict(zip("abcd", "wxyz", strict=True))
    obs, p = money_chart_permutation_pvalue(paths, picks, designed, n=4000, seed=3)
    assert obs == 4 and p < 0.05


def test_sign_flip_pvalue_calibration():
    # Fixed-seed form of a 5%-flaky property: valid while the permutation
    # draw order is untouched. On failure, investigate the draw-order
    # change — do not reseed to green.
    g = torch.Generator().manual_seed(1)
    null_lifts = torch.randn(100, generator=g) * 0.01
    assert sign_flip_pvalue(null_lifts, n=2000, seed=2) > 0.05
    assert sign_flip_pvalue(null_lifts + 0.02, n=2000, seed=2) < 0.01
```

- [ ] **Steps 2–4: FAIL → implement → PASS.** **Step 5: Commit.**

---

### Task 13: `--selftest`

**Files:** CLI section, selftest branch only; create `test_selftest.py`.

`run_selftest(cfg, device, certify=False) -> dict`, in order (each PASS/FAIL; GPU-only steps report `"skipped"` on CPU — **Phase A requires zero skipped**):
1. Print `FORBIDDEN_RELAXATIONS`.
2. **Per-seed determinism probe (GPU):** forward+backward each seed type under the flags; a missing-deterministic-kernel `RuntimeError` is a hard failure (grouped conv/GroupNorm coverage verified on this build, not assumed).
3. Smoke episode (tiny config, `read_test=False`): base → fan → twin holds; null-seed arm reproduces base hashes (hard stop on mismatch).
4. τ-init RMS check: all four seeds against a real host batch (restored from rev 1 — it was silently dropped).
5. Slot-site signed-zero scan (`forward_to_slot` output contains no exact −0.0 over a representative batch).
6. Blindness grep of the telemetry section + `nn.init.` grep of sections 4/5/11 (those calls take no `generator=` and bypass `rng_scope` discipline).
7. Store checks: JSON round-trip incl. non-finite; split wall; duplicate-identity assert; `schema_version` refusal.
8. Partition check: 45k/5k/10k, disjoint (via `split_indices` + counts).
9. `rng_scope` global-stream isolation.
10. Deterministic-mode cost measured (timed epoch, flags on vs. off on a throwaway copy) and printed.
`--certify` (GPU, all steps passed, none skipped): writes `certified.json` = `{git_rev, results, det_mode_cost}` — **the artifact `preflight --freeze` checks HEAD against.**

- [ ] Test: `test_selftest_runs_clean_cpu()` asserts `result["ok"]` and that GPU-only steps are marked skipped (not failed). Implement; PASS; commit.

---

### Task 14: `--preflight` — gates, refans, FreezeManifest

**Files:** CLI section, preflight branch only; create `test_preflight_gates.py`.

**Interfaces (Produces):**
- `draw_schedule(episode_seed, cfg) -> tuple[int, int]` — 2 ordered epochs, uniform without replacement, inclusive window.
- `run_collection_episode(cfg, data, device, episode_seed, namespace, store, worker_id, read_test) -> None` — base (`BaseTrace`, snapshots at scheduled epochs), two fans (`include_nullseed = derive(episode_seed, "nullseed-subsample") % 10 == 0` — **the 1-in-10 subsample wired into the collection path, not only selftest**), records appended with `split_role` from the tune rule.
- `run_refan(cfg, data, device, episode_seed, fan_epoch, k, store, worker_id) -> None` — future `derive(episode_seed, "refan", k)`, `k` recorded, **5 real arms incl. a fresh no-op under the new future** (the base tail is not a valid comparand; the twin is re-based), `kind="refan"`, excluded from training.
- Gates 1–8, thresholds from Config (never literals), unit = first fan per episode, all val units:
  1. `gate1_noop_sanity` — ≥ `cfg.gate1_min_mild_noop_wins` mild no-op wins (5-arm val-argmax); modal in no targeted pathology (D1). *Remedy: sampler.*
  2. `gate2_signal` — (a) 200-step linear probe telemetry→pathology, by-episode split (D13), > `cfg.gate2_probe_min_acc`; (b) probe telemetry→val-argmax (4-seed) vs majority-class; contingency table vs `DESIGNED_WINNER`. *Remedy: sampler.*
  3. `gate3_contrast` — both fan-density keys > `cfg.gate3_contrast_mult` × refan floor. *Remedy: averaging window, horizon.*
  4. `gate4_dominance` — no seed val-argmax > `cfg.gate4_dominance_max` overall, none majority in every pathology. *Remedy: sampler / menu balance — **menu balance = Task 5 reopen + Phase A re-run, priced, not a knob.*
  5. `gate5_magnitude` — per-seed mean `rms_ratio_blend_entry` within `cfg.gate5_rms_band`. *Remedy: τ, λ, seed_lr — never the sampler.*
  6. `gate6_horizon` — late-epoch density ≥ `cfg.gate6_late_density_mult` × early. *Remedy: horizon, window.*
  7. `gate7_now_vs_later` — report-only: `P(A(t_late) > A(t_early))`, mean gap.
  8. `gate8_pressure` (GPU) — twin at 1 worker vs full count, same episode seed; **records wall-clock at both counts** (→ the measured concurrency factor for the runtime table) and the outcome + contingency (`--replay` runs at the recorded worker_count if it fired).
- `run_preflight(cfg, data, device, store_root, freeze=False) -> dict` — dry-run by default: gates printed, `preflight_iter` record appended (`iteration`, `gate_results`, `config_hash`, git rev), normalizer fitted and shown, no artifact. `--freeze`: refuses unless all gates ok ∧ worktree clean ∧ `HEAD == certified.json["git_rev"]`; writes `frozen.json` atomically (temp+rename): `{frozen_block_hash, config_hash, git_rev, certified_rev, spec_rev: "98083fd", normalizer, fan_density (both keys), beta_which, beta_now, schedule_id, data_split_id, gate_results, gate8_outcome, det_mode_cost, concurrency_factor, plan_authored_constants (echoed for owner sign-off), manifest_hash}` with `manifest_hash` = sha256 over the canonical serialization of the rest. `_SEMANTIC_SURFACE` extended with the gate functions.

- [ ] Tests: each gate has a passing AND a failing synthetic fixture (gate 4: 8/10 conv_heavy wins → not ok; gate 1: zero mild no-op wins → not ok; gate 5: ratios (0.04, 0.05, 0.06, 0.30) → not ok); freeze refusal on failing gates and on a stubbed dirty worktree / HEAD mismatch. Implement; PASS; commit + `wc -l` (~1150).

---

### Task 15: `--collect` — idempotent process workers with a halt channel

**Files:** CLI section, collect branch only; create `test_collect.py`.

**Interfaces (Produces):**
- `run_collect(cfg, store_root, devices, n_workers_per_device, limit=None, extend=0)`:
  - Refuses without `frozen.json` whose `frozen_block_hash` matches live Config, `config_hash` matches live source, **and `gate_results` all ok**.
  - **Idempotent:** target seeds `derive(run_seed,"train",i)` for `i < n_collect + recorded extensions`; skips episode_seeds already in the merged shards (crash-resume and smoke-then-full are both safe; scratch `--store` for smoke also valid). `--extend N` allowed only while no eval-namespace record exists; writes an `extension_event` record.
  - Workers: `multiprocessing.get_context("spawn")`, module-level `worker_main`; each: `enable_class1()` → `torch.cuda.set_device` → load data once → episodes → own shard; stdout/stderr → `logs/worker_{id}.log`; one heartbeat line per episode (seed, epochs, elapsed).
  - **Halt channel:** shared `multiprocessing.Event`; `TwinDivergence` → `write_divergence_report(store_root, ...)` (schema: `{episode_seed, arm_name, first_bad_epoch, config_hash, frozen_block_hash, manifest_hash, env_block, host_init_hash}`) → event set → **all workers stop between episodes**; pre-halt shards remain valid. Parent join reports clean/halted/crashed per worker; exits nonzero unless all clean.

- [ ] Tests (CPU, tiny bundle via injection hook): 2×2 episodes → 4 episodes/8 fans, roles from the tune rule; **re-invocation collects zero new episodes**; injected divergence sets the event, sibling stops early, report exists with required keys. Implement; PASS; commit.

---

### Task 16: `--train` and `--eval`

**Files:** CLI section, train + eval branches only; create `test_eval_stats.py`.

**Interfaces (Produces):**
- `run_train(cfg, store_root)` — loads manifest; **betas from the manifest** (collection-density recomputation printed as diagnostic only, asserted unused); `load_for_training`; trains `trained` + `schedule_only` (same records, `mask_fn=schedule_only_mask` post-normalization) at `cfg.policy_steps`; saves checkpoints keyed by state-dict hash; prints tune curves. Bad-curve levers, pre-stated and recorded if used: `--extend` (pre-eval only) or shrink trunk (`d_model`/`n_layers`, non-frozen).
- `run_eval(cfg, data, device, store_root, resume=False, void_prereg=False)`:
  - **One-shot guard:** refuses if `eval_results.json` exists; `--void-preregistration` overrides AND writes a `void_event` record (permanent, visible).
  - **Crash-resume without double-counting:** `--resume-eval` skips grid fans / comparator runs whose fan_ids already exist (idempotent, like collect) — a crashed eval is completed, not restarted-and-double-counted.
  - Refuses on manifest mismatch or incomplete collection (merged train episodes < `n_collect` + extensions).
  - Battery: `cfg.n_eval` shared eval seeds (`derive(run_seed,"eval",i)`) × comparators {trained, random (uniform epoch in window via `derive(episode_seed,"random-null")`, uniform seed, always acts), schedule-only, fixed-epoch (trained WHICH forced at `t_star`)} — each episode a `policy_run` record with the `decisions` payload; lift = `r_chosen_test − r_noop_test`, never-germinate = 0.
  - Statistics: one-sided sign-flip permutation (trained-vs-0; paired trained-vs-schedule-only); germination rate beside every p.
  - Frozen grid: 2 forced fans per eval episode at `derive(episode_seed,"evalgrid")`-drawn epochs (schedule distribution) → 200 grid fans, `read_test=True`; teacher-forced agreement vs test-argmax over the 4 seed arms; nulls = majority-class + schedule-only; ~30 refans → Σp² ceiling (test units, labeled lower bound, Wilson CI, context only); falsifier = telemetry-history derangement across pathology classes; restraint regret (last grid point + labeled per-point); WHEN contrast restricted + unrestricted; chosen-seed marginal; **per-grid-point `(p, A)` stored** (the realized-p-by-sign(A) diagnostic's data); power note (MDE from manifest density at N=100 / 200 points).
  - Output: `eval_results.json`, atomic; all records `split_role="eval"` + `manifest_hash`.
- `verdict(results, cfg) -> dict[str, bool]` — the five pre-registered booleans, pure.
- `wilson_interval(k, n, alpha) -> tuple[float, float]`.

- [ ] Tests (synthetic): `wilson_interval` vs a known value; derangement never maps a class to itself; restricted/unrestricted WHEN on a 6-episode fixture with 2 never-germinates; `verdict` on all-pass and lift-fail fixtures; one-shot refusal; resume skips existing fan_ids; incomplete-collection refusal. Implement; PASS; commit.

---

### Task 17: `--report`, `--replay`, plotting sidecar

**Files:** CLI section, report + replay branches only; create `experiments/kernel_demo_plots.py`, `test_report.py`.

**Interfaces (Produces):**
- `run_report(cfg, store_root)` — canonical JSON + aligned tables (D4): lift table with germination rates; agreement vs nulls + ceiling-as-context; money chart + falsifier + chosen-seed marginal + diverged-excluded companion; observed diverged-arm end-state accuracies beside the 0.10 convention; per-seed failure rates; fan density + `P(val-argmax = test-argmax)`; restraint regret both forms; realized p by sign(A) (from the stored per-point pairs); tune curve; temperatures in force; det-mode cost + concurrency factor (from the manifest). Refusal: mixed `manifest_hash` in any single number (D6).
- `kernel_demo_plots.py` — standalone CLI (`--results`, `--store`, `--out`); arm curves (spike-then-crash = max exceeds end-state by >0.05), α/β trajectories (from `ArmResult.alpha_beta_log`), money-chart trio, tune curve, RMS-at-blend-entry.
- `run_replay(cfg, fan_id, store_root, device)` — locates the record via merge; refuses on `REPLAY_REFUSAL_KEYS` env mismatch, `config_hash` mismatch, `manifest_hash` mismatch; runs single-worker, **or at the recorded worker_count if the manifest's gate-8 contingency fired**; re-derives, forces the fan, asserts recorded `r_val` per finite arm; localises via `host_init_hash` on mismatch ("diverged at seeding" vs "diverged at kernel selection").

- [ ] Tests: table renders on Task 16's fixture; mixed-manifest refusal; replay refusal on doctored env and doctored config_hash. `uv add --group dev matplotlib`. Implement; PASS; commit.

---

### Task 18: Narrative pass and final CPU verification

- [ ] **Step 1:** Top-to-bottom read; section docstrings quoting their spec decisions; confirm Tasks 13–17 touched only their own subparser branches; `wc -l` sanity (aspirational).
- [ ] **Step 2:** `uv run pytest tests/unit/kernel_demo -v`; `uv run mypy src experiments`; `uv run ruff check experiments tests` — all clean.
- [ ] **Step 3:** Update filigree `simic-4a44ed57c9`.
- [ ] **Step 4:** Commit. → Operational Phases.

---

## Spec-coverage cross-check (mechanically spot-checked, not self-certified)

Forward: every spec section named in rev 6 maps to a task (§determinism→1/7/13; §data/unit-wall→2/8; §telemetry→3/11; §pathologies→4/14; §seeds/τ→5; §lifecycle→6; §fan/twin/null-seed→9; §record/store/replay→10/17; §action/deployment→11; §learning→12; §preflight/freeze→14; §collection→15; §eval/pre-registration→16; §report→17; caveat header→1/18). Reverse: the nine orphans found by review are all now owned (null-seed subsample→14/15; halt-all-workers→15; det-mode cost→13/14; config_hash→1/7; policy_run payload→10/16; preflight_iter payload→10/14; α/β data source→6/9/17; realized-p storage→16; rms_ratio owner→6/9). This table was produced by checking the review's orphan list against rev 3 line by line; it is a record of that check, not a proof of completeness.

## Operational Phases (post-code; GPU; never interleaved with code edits)

- [ ] **Phase A — Certify:** full suite; `selftest --device cuda:0 --certify` (zero skips) → `certified.json`; `wardline scan . --fail-on ERROR` (exit 2 = wardline error → report per dogfooding rule); mypy/ruff; final commit; clean tree.
- [ ] **Phase B — Preflight & freeze (user present):** dry runs (subset first); sampler tuning per remedies; gate table surfaced; `preflight --freeze` at the certified commit → `frozen.json` (incl. plan-authored constants echoed for owner sign-off).
- [ ] **Phase C — Collect (overnight):** smoke `--limit 4` (idempotency makes the full run safe), then `collect --devices cuda:0,cuda:1 --workers 6` (VRAM-verified; gate 8's measured concurrency factor may adjust). Morning: logs, heartbeats, zero divergence reports, episode count.
- [ ] **Phase D — Train:** tune curves inspected; pre-stated levers if bad.
- [ ] **Phase E — Eval (user present, ONE SHOT):** collection-complete check → `eval` once; crash → `--resume-eval` completes without double-counting.
- [ ] **Phase F — Report:** `report`, sidecar plots, one `replay` spot-check. Deliver the headline numbers with nulls and the falsifier.
