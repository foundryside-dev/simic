# Kernel Demo ("Simic in 20 minutes") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `experiments/kernel_demo.py` — a single-file tech demo where a learned transformer policy (Aurelia) reads host telemetry, decides when to inject which of four fixed seeds into one slot of an undersized CIFAR-10 CNN, and is trained/scored against matched counterfactual fans — per the LOCKED spec `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 6, commit 98083fd).

**Architecture:** One narrative-ordered Python file (~1200 lines): constants/derive → data + common future → telemetry → host + pathologies → seeds (delta contract) → slot lifecycle → determinism → episode/fan executor → store → policy → learning → modes (`--selftest --preflight --collect --train --eval --report --replay`). A plotting sidecar `experiments/kernel_demo_plots.py`. Tests in `tests/unit/kernel_demo/`.

**Tech Stack:** Python ≥3.14, torch 2.13 (+cu130, already installed), torchvision (added in Task 1), pytest. No other runtime deps.

## Global Constraints (verbatim from the locked spec — every task inherits these)

- **The spec is LOCKED.** Any deviation discovered during implementation is surfaced to the user, never silently patched. The spec file is the tiebreaker for every ambiguity.
- Class 1 determinism: `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`, `cudnn.benchmark=False`, env `CUBLAS_WORKSPACE_CONFIG=:4096:8`, TF32 off both flags. No AMP, no dropout, no gradient clipping anywhere.
- `attn` seed: explicit-matmul attention only — no `F.scaled_dot_product_attention`.
- RNG: every draw from a named `torch.Generator`; `torch.manual_seed` only at process startup. `derive(seed, *labels)` = SHA-256, first 8 bytes.
- Harness constants (frozen block): `tau=0.05`, `tau_eps=1e-6`, `lam=1.0`, `K=3, M=3, F=2`, `horizon=40`, `window=(5,15)`, `t_star=10`, `lr=0.05`, `momentum=0.9` (Nesterov), `wd=5e-4` (no-decay: gains, norm affines, biases), `diverged_R=0.10`, `n_preflight=30`, `n_collect=300`, `n_eval=100`, `fans_per_episode=2`, `alpha=0.05`, `permutation_resamples=10_000`.
- Data: train 45k / val 5k (held from official train) / test = official 10k. Anything that can change the frozen block reads **val**; test unread until after freeze.
- Reward `R_a` = mean accuracy over final 3 epochs; end-state only; zero shaped terms.
- The file is ordered as a narrative and carries the spec's "not Simic" caveat verbatim in its header.
- Commit after every task (pre-commit runs ruff/mypy — code must pass both; the project's pyproject sets line-length and mypy strictness).
- Tests must pass on CPU (CI-safe); CUDA-only tests use `pytest.mark.skipif(not torch.cuda.is_available(), ...)`.

## File Structure

- `experiments/kernel_demo.py` — the deliverable. Single module, sections in this order (section banners `# ── N. NAME ──`): 1 constants+derive, 2 data+future, 3 telemetry, 4 host, 5 seeds, 6 slot/lifecycle, 7 determinism, 8 episode/fan, 9 store, 10 policy, 11 learning, 12 modes/CLI.
- `experiments/kernel_demo_plots.py` — matplotlib-only sidecar; imports FROM kernel_demo, never the reverse.
- `experiments/__init__.py`, `tests/unit/kernel_demo/__init__.py` — empty markers.
- `tests/unit/kernel_demo/test_{derive,data,telemetry,host,seeds,slot,episode,fan,store,policy,learning,eval_stats}.py` — one test file per section.

---

### Task 1: Dependencies, skeleton, derive(), Config

**Files:**
- Modify: `pyproject.toml` (add torchvision)
- Create: `experiments/__init__.py`, `experiments/kernel_demo.py`, `tests/unit/kernel_demo/__init__.py`, `tests/unit/kernel_demo/test_derive.py`

**Interfaces:**
- Produces: `derive(seed: int, *labels: str | int) -> int` (uint64), `make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator`, `@dataclass(frozen=True) Config` holding every Global-Constraints constant plus `d_model=64, n_layers=2, beta_which_frac=0.2, beta_now_div=2.2, warmup_frac=0.3, tune_frac=0.2, batch_size=128, seed_lr=0.05`, `FROZEN_FIELDS: tuple[str, ...]` (every Config field named in the spec's frozen block), `frozen_block_hash(cfg: Config) -> str` (sha256 of sorted field=value lines), `main()` argparse dispatch with the seven modes as subcommands (each initially raising `SystemExit("not implemented: <mode>")`).

- [ ] **Step 1: Add torchvision** — `cd ~/simic && uv add torchvision` then `uv run python -c "import torchvision; print(torchvision.__version__)"`. Expected: a version prints. If uv cannot resolve torchvision for Python 3.14/torch 2.13, STOP and report to the user — do not pin around it.
- [ ] **Step 2: Write the failing tests**

```python
# tests/unit/kernel_demo/test_derive.py
import torch
from experiments.kernel_demo import Config, derive, frozen_block_hash, make_generator

def test_derive_deterministic_and_label_sensitive():
    assert derive(1, "a") == derive(1, "a")
    assert derive(1, "a") != derive(1, "b")
    assert derive(1, "a", 0) != derive(1, "a", 1)
    assert 0 <= derive(123, "x") < 2**64

def test_generator_hermetic():
    a = torch.rand(4, generator=make_generator(derive(7, "g")))
    b = torch.rand(4, generator=make_generator(derive(7, "g")))
    assert torch.equal(a, b)

def test_frozen_hash_moves_with_frozen_fields_only():
    c = Config()
    assert frozen_block_hash(c) == frozen_block_hash(Config())
    import dataclasses
    assert frozen_block_hash(dataclasses.replace(c, lam=2.0)) != frozen_block_hash(c)
```

- [ ] **Step 3: Run** `uv run pytest tests/unit/kernel_demo/test_derive.py -v` — expected FAIL (ImportError).
- [ ] **Step 4: Implement**

```python
# experiments/kernel_demo.py  — section 1
"""Kernel Demo — "Simic in 20 minutes".

Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
exactly what Simic proper rejects (generation from live host state). This
demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis.

Spec (LOCKED, rev 6): docs/superpowers/specs/2026-08-09-kernel-demo-design.md
"""
from __future__ import annotations

import argparse, dataclasses, hashlib, json, math, os
from dataclasses import dataclass, field
import torch

def derive(seed: int, *labels: str | int) -> int:
    payload = ":".join([str(seed), *map(str, labels)]).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

def make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator:
    g = torch.Generator(device=device)
    g.manual_seed(seed % (2**63))
    return g

@dataclass(frozen=True)
class Config:
    # frozen block (spec: "Pre-registered numbers" + harness constants)
    tau: float = 0.05
    tau_eps: float = 1e-6
    lam: float = 1.0
    K: int = 3; M: int = 3; F: int = 2
    horizon: int = 40
    window: tuple[int, int] = (5, 15)
    t_star: int = 10
    lr: float = 0.05; momentum: float = 0.9; wd: float = 5e-4
    seed_lr: float = 0.05
    diverged_R: float = 0.10
    n_preflight: int = 30; n_collect: int = 300; n_eval: int = 100
    fans_per_episode: int = 2
    alpha_level: float = 0.05
    permutation_resamples: int = 10_000
    beta_which_frac: float = 0.2; beta_now_div: float = 2.2
    # non-frozen engineering knobs
    d_model: int = 64; n_layers: int = 2
    warmup_frac: float = 0.3; tune_frac: float = 0.2
    batch_size: int = 128
    run_seed: int = 20260809

FROZEN_FIELDS: tuple[str, ...] = (
    "tau", "tau_eps", "lam", "K", "M", "F", "horizon", "window", "t_star",
    "lr", "momentum", "wd", "seed_lr", "diverged_R", "n_preflight",
    "n_collect", "n_eval", "fans_per_episode", "alpha_level",
    "permutation_resamples", "beta_which_frac", "beta_now_div",
)

def frozen_block_hash(cfg: Config) -> str:
    lines = sorted(f"{k}={getattr(cfg, k)!r}" for k in FROZEN_FIELDS)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()

MODES = ("selftest", "preflight", "collect", "train", "eval", "report", "replay")

def main(argv: list[str] | None = None) -> None:
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

- [ ] **Step 5: Run tests** — expected PASS. Also `uv run python -m experiments.kernel_demo selftest; echo $?` → prints `not implemented: selftest`.
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat(kernel-demo): skeleton, derive(), Config, frozen-block hash"`

---

### Task 2: Data — partition, GPU residency, CommonFuture, augmentation

**Files:**
- Modify: `experiments/kernel_demo.py` (section 2)
- Create: `tests/unit/kernel_demo/test_data.py`

**Interfaces:**
- Consumes: `derive`, `make_generator`, `Config`.
- Produces:
  - `@dataclass DataBundle: train_x: torch.Tensor (uint8 [45000,3,32,32]), train_y: torch.Tensor (int64), val_x/val_y ([5000,...]), test_x/test_y ([10000,...])`; `load_data(cfg, device, subset: int | None = None) -> DataBundle` (torchvision CIFAR10 download to `runs/data`, val = last 5k of the official train split by fixed `derive(cfg.run_seed,"valsplit")` permutation, tensors moved to `device`).
  - `@dataclass CommonFuture: order [E,S] int64 flat sample indices per step-batch start (steps×bs reshaped), crops [E,S,B,2] uint8 offsets 0..8, flips [E,S,B] bool; epochs: int; hash: str` and `CommonFuture.draw(seed: int, n_train: int, epochs: int, cfg) -> CommonFuture` — every tensor from one `make_generator(seed)`; `hash` = sha256 over the three tensors' bytes.
  - `augment(x_u8: Tensor, crops: Tensor, flips: Tensor) -> Tensor` — float32 normalized (CIFAR mean/std constants `CIFAR_MEAN`, `CIFAR_STD`), reflect-pad-4, per-sample crop via advanced indexing, per-sample horizontal flip. Pure function of inputs; consumes no RNG.

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/kernel_demo/test_data.py
import torch
from experiments.kernel_demo import CommonFuture, Config, augment

def test_common_future_deterministic_and_hash_sensitive():
    cfg = Config()
    a = CommonFuture.draw(42, n_train=1000, epochs=3, cfg=cfg)
    b = CommonFuture.draw(42, n_train=1000, epochs=3, cfg=cfg)
    c = CommonFuture.draw(43, n_train=1000, epochs=3, cfg=cfg)
    assert a.hash == b.hash and torch.equal(a.order, b.order)
    assert a.hash != c.hash
    assert a.crops.max() <= 8 and a.crops.min() >= 0

def test_augment_pure_function_no_rng():
    x = torch.randint(0, 256, (4, 3, 32, 32), dtype=torch.uint8)
    crops = torch.tensor([[0, 0], [8, 8], [4, 4], [2, 6]], dtype=torch.uint8)
    flips = torch.tensor([True, False, True, False])
    state = torch.get_rng_state()
    y1 = augment(x, crops, flips)
    y2 = augment(x, crops, flips)
    assert torch.equal(state, torch.get_rng_state())      # no RNG consumed
    assert torch.equal(y1, y2)
    assert y1.shape == (4, 3, 32, 32) and y1.dtype == torch.float32
    # flip is a real flip: flipping flips back
    y3 = augment(x, crops, ~flips)
    assert not torch.equal(y1, y3)
```

- [ ] **Step 2: Run** — expected FAIL (ImportError).
- [ ] **Step 3: Implement**

```python
# section 2 — DATA
CIFAR_MEAN = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1)
CIFAR_STD = torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1)

@dataclass
class DataBundle:
    train_x: torch.Tensor; train_y: torch.Tensor
    val_x: torch.Tensor; val_y: torch.Tensor
    test_x: torch.Tensor; test_y: torch.Tensor

def load_data(cfg: Config, device: str, subset: int | None = None) -> DataBundle:
    import torchvision
    root = "runs/data"
    tr = torchvision.datasets.CIFAR10(root, train=True, download=True)
    te = torchvision.datasets.CIFAR10(root, train=False, download=True)
    x = torch.from_numpy(tr.data).permute(0, 3, 1, 2).contiguous()   # uint8 NCHW
    y = torch.tensor(tr.targets, dtype=torch.int64)
    perm = torch.randperm(50_000, generator=make_generator(derive(cfg.run_seed, "valsplit")))
    val_idx, train_idx = perm[45_000:], perm[:45_000]
    if subset is not None:
        train_idx = train_idx[:subset]
    tx = torch.from_numpy(te.data).permute(0, 3, 1, 2).contiguous()
    ty = torch.tensor(te.targets, dtype=torch.int64)
    d = lambda t: t.to(device)
    return DataBundle(d(x[train_idx]), d(y[train_idx]), d(x[val_idx]), d(y[val_idx]), d(tx), d(ty))

@dataclass
class CommonFuture:
    order: torch.Tensor; crops: torch.Tensor; flips: torch.Tensor
    epochs: int; hash: str

    @classmethod
    def draw(cls, seed: int, n_train: int, epochs: int, cfg: Config) -> "CommonFuture":
        g = make_generator(seed)
        bs = cfg.batch_size
        steps = n_train // bs
        order = torch.stack([torch.randperm(n_train, generator=g)[: steps * bs] for _ in range(epochs)])
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
    B = xf.shape[0]
    ar = torch.arange(32, device=dev)
    ys = crops[:, 0].to(dev, torch.int64)[:, None] + ar            # [B,32]
    xs = crops[:, 1].to(dev, torch.int64)[:, None] + ar            # [B,32]
    bi = torch.arange(B, device=dev)[:, None, None]
    out = xp.permute(0, 2, 3, 1)[bi, ys[:, :, None], xs[:, None, :], :].permute(0, 3, 1, 2)
    return torch.where(flips.to(dev)[:, None, None, None], out.flip(-1), out).contiguous()
```

- [ ] **Step 4: Run tests** — expected PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): data partition 45k/5k/10k, CommonFuture, RNG-free GPU augmentation"`

---

### Task 3: TelemetryRecord, collection, Normalizer

**Files:**
- Modify: `experiments/kernel_demo.py` (section 3)
- Create: `tests/unit/kernel_demo/test_telemetry.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `@dataclass(frozen=True) TelemetryRecord` — fields exactly: `epoch: int, train_loss: float, val_loss: float, val_acc: float, train_loss_delta: float, val_loss_delta: float, grad_norm_mean: tuple[float,float,float], grad_norm_var: tuple[float,float,float], act_saturation: tuple[float,float,float], weight_norm: tuple[float,float,float]` (one entry per host stage). `__post_init__` asserts every float finite (`math.isfinite`), raising `TelemetryDivergence` otherwise. NO other fields ever (blindness rule).
  - `class TelemetryDivergence(RuntimeError)`.
  - `record_to_vector(r: TelemetryRecord) -> torch.Tensor` (flat float32, fixed length `TELEMETRY_DIM = 18`, order = field order).
  - `class Normalizer`: `fit(vectors: list[Tensor])` stores per-feature median and IQR (IQR floored at 1e-8); `apply(v) -> Tensor` = `(v - med) / iqr`; `to_json() -> str` / `from_json(s) -> Normalizer`.
  - `collect_stage_stats(host) -> dict` returning per-stage grad-norm mean/var (over that epoch's accumulated per-step grad norms, passed in by the caller), saturation fraction (fraction of post-ReLU activations equal to 0, from the host's stat hooks — Task 4 provides `host.stage_stats`), weight norms. (Implemented as a free function consuming the numbers the episode loop gathers; the record is constructed in one place, `build_record(...)`, in the episode loop of Task 8.)

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_telemetry.py
import dataclasses, math, pytest, torch
from experiments.kernel_demo import (Normalizer, TELEMETRY_DIM, TelemetryDivergence,
                                     TelemetryRecord, record_to_vector)

def _rec(**kw):
    base = dict(epoch=3, train_loss=1.2, val_loss=1.3, val_acc=0.41,
                train_loss_delta=-0.1, val_loss_delta=-0.05,
                grad_norm_mean=(1.0, 2.0, 3.0), grad_norm_var=(0.1, 0.2, 0.3),
                act_saturation=(0.5, 0.4, 0.3), weight_norm=(10.0, 11.0, 12.0))
    base.update(kw)
    return TelemetryRecord(**base)

def test_record_rejects_nonfinite():
    with pytest.raises(TelemetryDivergence):
        _rec(val_loss=float("inf"))
    with pytest.raises(TelemetryDivergence):
        _rec(grad_norm_var=(0.1, float("nan"), 0.3))

def test_blindness_no_forbidden_fields():
    names = {f.name for f in dataclasses.fields(TelemetryRecord)}
    for forbidden in ("pathology_id", "wall_time", "device", "worker", "time"):
        assert not any(forbidden in n for n in names)

def test_vector_roundtrip_and_normalizer():
    v = record_to_vector(_rec())
    assert v.shape == (TELEMETRY_DIM,)
    n = Normalizer(); n.fit([v, v * 2, v * 3])
    out = n.apply(v * 2)
    assert torch.allclose(out, torch.zeros_like(out), atol=1e-6)  # median maps to 0
    n2 = Normalizer.from_json(n.to_json())
    assert torch.allclose(n2.apply(v), n.apply(v))
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement** exactly the interfaces above (median/IQR via `torch.quantile(t, .5/.25/.75, dim=0)`). **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): TelemetryRecord with finiteness+blindness, median/IQR Normalizer"`

---

### Task 4: Host CNN and the four pathologies

**Files:**
- Modify: `experiments/kernel_demo.py` (section 4)
- Create: `tests/unit/kernel_demo/test_host.py`

**Interfaces:**
- Consumes: `derive`, `make_generator`.
- Produces:
  - `PATHOLOGIES = ("under_normalized", "channel_starved", "no_spatial_mix", "mild")`; `DESIGNED_WINNER = {"under_normalized": "norm", "channel_starved": "conv_heavy", "no_spatial_mix": "attn", "mild": "conv_light"}`.
  - `class Host(nn.Module)`: three stages (`stage1/2/3`: Conv-BN-ReLU ×2 + pool each; healthy widths 32/64/128 → GAP → linear(10); ~150k params), **slot site after stage2** — `forward(x, slot: Slot | None)` routes stage2 output through the slot when given. `host.stage_modules() -> list[nn.Module]` (for per-stage stats), `host.feat_channels = 64` (slot width).
  - Pathology wiring inside `build_host(pathology: str, init_seed: int) -> Host`: `under_normalized` → all BN removed (Identity) and init gain ×2; `channel_starved` → widths 32/24/32; `no_spatial_mix` → stage2 convs are 1×1; `mild` → widths 32/48/96. Init from `make_generator(init_seed)` via a local `_init(module, gen)` (kaiming-normal weights drawn with the generator — use `torch.nn.init` equivalents that accept `generator=` or draw with `torch.randn(..., generator=gen)` and copy).
  - `host_init_hash(host) -> str` — sha256 over sorted `state_dict()` tensor bytes (cpu, contiguous).
  - Activation-saturation hooks: `host.attach_stat_hooks()` registers forward hooks storing, per stage, the fraction of zeros in the ReLU output of the stage's last ReLU into `host.stage_stats["saturation"]` (list of 3 floats, overwritten per forward pass; the episode loop averages over an epoch).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_host.py
import torch
from experiments.kernel_demo import PATHOLOGIES, build_host, host_init_hash

def test_all_pathologies_build_and_forward():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        out = h(torch.randn(2, 3, 32, 32), slot=None)
        assert out.shape == (2, 10)

def test_param_count_undersized():
    n = sum(p.numel() for p in build_host("mild", 1).parameters())
    assert 80_000 < n < 250_000

def test_init_hash_is_seed_function():
    assert host_init_hash(build_host("mild", 5)) == host_init_hash(build_host("mild", 5))
    assert host_init_hash(build_host("mild", 5)) != host_init_hash(build_host("mild", 6))

def test_pathology_structure():
    un = build_host("under_normalized", 1)
    assert not any(isinstance(m, torch.nn.BatchNorm2d) for m in un.modules())
    nm = build_host("no_spatial_mix", 1)
    s2convs = [m for m in nm.stage2.modules() if isinstance(m, torch.nn.Conv2d)]
    assert all(m.kernel_size == (1, 1) for m in s2convs)
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): undersized host, four pathologies, init hash, stat hooks"`

---

### Task 5: Seeds — delta contract, τ-init

**Files:**
- Modify: `experiments/kernel_demo.py` (section 5)
- Create: `tests/unit/kernel_demo/test_seeds.py`

**Interfaces:**
- Consumes: `derive`, `make_generator`, `Config`.
- Produces:
  - `SEED_NAMES = ("norm", "attn", "conv_light", "conv_heavy")`.
  - `class SeedDelta(nn.Module)` base: `self.gain = nn.Parameter(torch.zeros(()))`, `forward(h) = self.gain * self.f(h)`, abstract `f(h)`. Subclasses `NormSeed` (`f = GroupNorm(8, C)(h) − h`), `AttnSeed` (LN over channels → 1-head attention over the 8×8=64 spatial positions with explicit `q@k.T/√d` softmax `@v`, output proj; ~5k params), `ConvLightSeed` (depthwise 3×3 + pointwise + BN + ReLU + pointwise), `ConvHeavySeed` (3×3 BN ReLU 3×3 BN, channel bottleneck sized to land ~60k params).
  - `build_seed(name: str, channels: int, init_seed: int) -> SeedDelta` — internals standard-init from `make_generator(init_seed)`, final BN γ=1, gain stays 0 until τ-init.
  - `tau_init(seed: SeedDelta, host_feats: Tensor, cfg: Config) -> float` — under `torch.no_grad()` + `seed.eval()`: compute `f0 = seed.f(host_feats)`, set `gain = cfg.tau * RMS(host_feats) / max(RMS(f0), cfg.tau_eps)`, restore `seed.train()`, return the gain value (logged by the caller).
  - `NO_DECAY_KEYWORDS = ("gain", "bias", "bn", "ln", "norm")` and `split_decay_groups(module) -> tuple[list, list]` (params whose qualified name contains a keyword → no-decay list).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_seeds.py
import pytest, torch
from experiments.kernel_demo import Config, SEED_NAMES, build_seed, split_decay_groups, tau_init

@pytest.mark.parametrize("name", SEED_NAMES)
def test_delta_zero_before_tau_init_and_shape(name):
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(2, 64, 8, 8)
    d = s(h)
    assert d.shape == h.shape
    assert torch.equal(d, torch.zeros_like(d))          # gain==0 exactly

@pytest.mark.parametrize("name", SEED_NAMES)
def test_tau_init_hits_target_rms(name):
    cfg = Config()
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(16, 64, 8, 8)
    g = tau_init(s, h, cfg)
    assert g != 0.0
    ratio = s(h).pow(2).mean().sqrt() / h.pow(2).mean().sqrt()
    assert abs(ratio.item() - cfg.tau) / cfg.tau < 0.05

def test_param_budgets():
    counts = {n: sum(p.numel() for p in build_seed(n, 64, 1).parameters()) for n in SEED_NAMES}
    assert counts["norm"] < 300
    assert 2_000 < counts["attn"] < 12_000
    assert 5_000 < counts["conv_light"] < 20_000
    assert 35_000 < counts["conv_heavy"] < 90_000

def test_no_decay_split_catches_gain_and_norms():
    s = build_seed("conv_heavy", 64, 1)
    decay, no_decay = split_decay_groups(s)
    no_decay_names = {n for n, _ in no_decay}
    assert any("gain" in n for n in no_decay_names)
    assert all("bias" not in n for n, _ in decay)
```

(`split_decay_groups` returns `(named_decay, named_no_decay)` lists of `(name, param)` so the test can inspect names; the optimizer builder in Task 6 strips names.)

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement** (AttnSeed: `h [B,C,8,8] → tokens [B,64,C] → LN → q,k,v = Linear(C, d) with d=16 → softmax(q@k.transpose/√d)@v → Linear(d, C) → back to [B,C,8,8]`; no `F.scaled_dot_product_attention` anywhere). **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): four delta seeds, explicit-matmul attention, tau-init, no-decay split"`

---

### Task 6: Slot lifecycle — STE, α/β schedules, trust region, optimizer contract

**Files:**
- Modify: `experiments/kernel_demo.py` (section 6)
- Create: `tests/unit/kernel_demo/test_slot.py`

**Interfaces:**
- Consumes: `SeedDelta`, `split_decay_groups`, `Config`.
- Produces:
  - `Stage = enum.Enum("Stage", "DORMANT GERMINATED TRAINING BLENDING FOSSILIZING FOSSILIZED")`.
  - `def cosine_ease(p: float) -> float:` `0.5 * (1 - math.cos(math.pi * min(max(p, 0.0), 1.0)))`.
  - `class Slot(nn.Module)`: attrs `stage: Stage = DORMANT`, `seed: SeedDelta | None`, `alpha: float = 0.0`, `beta: float = 0.0`, `last_delta`, `last_h`. `forward(h)`:

```python
def forward(self, h: torch.Tensor) -> torch.Tensor:
    if self.stage in (Stage.DORMANT, Stage.GERMINATED) or self.seed is None:
        return h
    hin = h.detach() * (1.0 - self.beta) + h * self.beta   # value == h for all beta
    delta = self.seed(hin)
    self.last_delta, self.last_h = delta, h
    if self.stage is Stage.TRAINING:
        return h + (delta - delta.detach())                # STE: forward value == h
    return h + self.alpha * delta
```

  - `Slot.trust_region_loss(cfg) -> Tensor` = `cfg.lam * last_delta.pow(2).mean() / last_h.detach().pow(2).mean().clamp_min(1e-12)` (0 when not TRAINING).
  - `Slot.epoch_tick(epochs_in_stage, steps_per_epoch)` + `Slot.step_tick(step_in_stage_epoch)` advancing the FSM once per epoch and α/β per step: BLENDING `alpha = cosine_ease((global_blend_step + 1) / (M * steps_per_epoch))`; FOSSILIZING `alpha = 1, beta = cosine_ease((step + 1) / (F * steps_per_epoch))`; FOSSILIZED `alpha = beta = 1` **and** the seed's input stops being detached (β=1 makes `hin` == `h` exactly — same code path).
  - `build_optimizer(host, cfg) -> torch.optim.SGD` (Nesterov, decay/no-decay host groups) and `append_seed_group(opt, seed, cfg)` (two more groups: seed decay / seed no-decay at `cfg.seed_lr`; returns group index range for restore checks).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_slot.py
import torch
from experiments.kernel_demo import (Config, Slot, Stage, append_seed_group,
                                     build_host, build_optimizer, build_seed,
                                     cosine_ease, tau_init)

def _armed_slot(stage):
    cfg = Config()
    slot = Slot()
    slot.seed = build_seed("conv_light", 64, 7)
    h = torch.randn(4, 64, 8, 8, requires_grad=True)
    tau_init(slot.seed, h.detach(), cfg)
    slot.stage = stage
    return cfg, slot, h

def test_training_forward_is_bitwise_host():
    _, slot, h = _armed_slot(Stage.TRAINING)
    assert torch.equal(slot(h), h)                        # STE value-exact

def test_training_isolates_host_gradient():
    _, slot, h = _armed_slot(Stage.TRAINING)
    slot(h).sum().backward()
    assert torch.allclose(h.grad, torch.ones_like(h))     # d(out)/dh == I exactly
    assert slot.seed.gain.grad is not None and slot.seed.gain.grad.abs().item() > 0

def test_blending_gradient_gated_by_alpha_and_beta_zero():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha, slot.beta = 0.5, 0.0
    out = slot(h)
    (out.sum()).backward()
    # host grad = I + alpha * d(delta)/dh, but beta=0 detaches the seed input:
    assert torch.allclose(h.grad, torch.ones_like(h))

def test_trust_region_positive_only_in_training():
    cfg, slot, h = _armed_slot(Stage.TRAINING)
    slot(h)
    assert slot.trust_region_loss(cfg).item() > 0

def test_optimizer_groups_and_seed_append():
    cfg = Config()
    host = build_host("mild", 1)
    opt = build_optimizer(host, cfg)
    n0 = len(opt.param_groups)
    seed = build_seed("norm", 64, 2)
    append_seed_group(opt, seed, cfg)
    assert len(opt.param_groups) == n0 + 2
    no_decay = opt.param_groups[-1]
    assert no_decay["weight_decay"] == 0.0 and no_decay["lr"] == cfg.seed_lr

def test_cosine_ease_endpoints():
    assert cosine_ease(0.0) == 0.0 and abs(cosine_ease(1.0) - 1.0) < 1e-12
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): slot FSM, STE isolation, cosine alpha/beta, trust region, SGD contract"`

---

### Task 7: Determinism — Class 1 knobs, env block, forbidden relaxations

**Files:**
- Modify: `experiments/kernel_demo.py` (section 7)
- Create: `tests/unit/kernel_demo/test_determinism.py`

**Interfaces:**
- Produces:
  - `enable_class1() -> None`: sets `os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")` (must run before first CUDA matmul — `main()` calls it first), `torch.use_deterministic_algorithms(True)`, `torch.backends.cudnn.deterministic = True`, `torch.backends.cudnn.benchmark = False`, `torch.backends.cuda.matmul.allow_tf32 = False`, `torch.backends.cudnn.allow_tf32 = False`.
  - `env_block(device: str, worker_count: int) -> dict` — torch/cuda/cudnn/python versions, GPU name, TF32 flags, worker_count, device_index. `REPLAY_REFUSAL_KEYS = ("torch", "cuda", "cudnn", "python", "gpu_name", "tf32_matmul", "tf32_cudnn")` (worker_count/device_index are provenance only — spec rev 6).
  - `FORBIDDEN_RELAXATIONS: tuple[str, ...]` — the spec list verbatim (disable twin, disable deterministic algorithms, TF32/benchmark/AMP on, clipping or dropout added, fans across devices), printed by selftest.
  - `state_hash(module) -> str` — sha256 over sorted state_dict tensor bytes (shared by twin arm and host assertions; `host_init_hash` becomes an alias).

- [ ] **Step 1: Failing test**

```python
# tests/unit/kernel_demo/test_determinism.py
import torch
from experiments.kernel_demo import REPLAY_REFUSAL_KEYS, enable_class1, env_block

def test_class1_flags_set():
    enable_class1()
    assert torch.backends.cudnn.deterministic and not torch.backends.cudnn.benchmark
    assert not torch.backends.cuda.matmul.allow_tf32
    assert torch.are_deterministic_algorithms_enabled()

def test_env_block_keys_and_refusal_subset():
    e = env_block("cpu", worker_count=4)
    assert set(REPLAY_REFUSAL_KEYS) <= set(e)
    assert "worker_count" in e and "worker_count" not in REPLAY_REFUSAL_KEYS
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): Class 1 determinism knobs, env block, refusal keys"`

---

### Task 8: Episode runner — train epoch, telemetry, snapshot/restore, end-state eval

**Files:**
- Modify: `experiments/kernel_demo.py` (section 8a)
- Create: `tests/unit/kernel_demo/test_episode.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `@dataclass EpisodeCtx: cfg, data: DataBundle, device: str, episode_seed: int, pathology: str, future: CommonFuture, host: Host, opt, slot: Slot, telemetry: list[TelemetryRecord], curves_val: list[float], curves_test: list[float] | None` and `make_episode(cfg, data, device, episode_seed) -> EpisodeCtx` — pathology from `derive(episode_seed, "pathology") % 4`, host from `derive(episode_seed, "host-init")`, future from `derive(episode_seed, "future", 0)`.
  - `train_one_epoch(ctx, epoch: int) -> None` — iterates the future's step batches for `epoch`, `augment`s, forward through `host(x, slot)`, cross-entropy `+ slot.trust_region_loss(cfg)` when TRAINING, per-step grad-norm capture per stage, `slot.step_tick`; then `slot.epoch_tick`, telemetry via `build_record(...)` (evaluating val loss/acc under `no_grad`), appended to `ctx.telemetry`; `ctx.curves_val.append(val_acc)`.
  - `evaluate_acc(host, slot, x_u8, y, device) -> float` (center-crop only: normalize, no aug; batch 1000 chunks, `eval()` mode, restores prior mode).
  - `@dataclass Snapshot: host_state, opt_state, cpu_rng, cuda_rng, epoch` and `take_snapshot(ctx) -> Snapshot` (deep clones: `{k: v.detach().clone() for ...}`, `copy.deepcopy(opt.state_dict())`, RNG states) / `restore_snapshot(ctx, snap) -> None`.
  - `end_state_R(curve: list[float]) -> float` — mean of last 3 entries.
  - `germinate(ctx, seed_name: str) -> float` — builds seed from `derive(ctx.episode_seed, "arm", seed_name)`, `tau_init` on one fixed val batch **under eval/no-grad**, `append_seed_group`, sets `slot.stage = Stage.TRAINING` (GERMINATED collapses into the same tick), returns logged `g`.

- [ ] **Step 1: Failing tests** (CPU, tiny: `subset=512`, horizon 4 — use `dataclasses.replace(Config(), horizon=4, ...)`; build a tiny synthetic DataBundle fixture instead of downloading CIFAR: random uint8 tensors, 512/128/128 samples — `def tiny_bundle(device)` helper inside the test file)

```python
# tests/unit/kernel_demo/test_episode.py
import dataclasses, torch
from experiments.kernel_demo import (Config, end_state_R, make_episode,
                                     restore_snapshot, state_hash, take_snapshot,
                                     train_one_epoch)
from experiments.kernel_demo import DataBundle

def tiny_bundle(device="cpu"):
    g = torch.Generator().manual_seed(0)
    mk = lambda n: (torch.randint(0, 256, (n, 3, 32, 32), generator=g, dtype=torch.uint8).to(device),
                    torch.randint(0, 10, (n,), generator=g).to(device))
    tx, ty = mk(512); vx, vy = mk(128); ex, ey = mk(128)
    return DataBundle(tx, ty, vx, vy, ex, ey)

CFG = dataclasses.replace(Config(), horizon=4, batch_size=64)

def test_same_seed_same_episode_cpu_bitwise():
    b = tiny_bundle()
    h1 = _run(b, 11); h2 = _run(b, 11); h3 = _run(b, 12)
    assert h1 == h2 and h1 != h3

def _run(bundle, seed):
    ctx = make_episode(CFG, bundle, "cpu", seed)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    return state_hash(ctx.host)

def test_snapshot_restore_roundtrip_bitwise():
    ctx = make_episode(CFG, tiny_bundle(), "cpu", 21)
    train_one_epoch(ctx, 0)
    snap = take_snapshot(ctx)
    before = state_hash(ctx.host)
    train_one_epoch(ctx, 1)
    restore_snapshot(ctx, snap)
    assert state_hash(ctx.host) == before
    train_one_epoch(ctx, 1)
    h_a = state_hash(ctx.host)
    restore_snapshot(ctx, snap); train_one_epoch(ctx, 1)
    assert state_hash(ctx.host) == h_a                     # replayable from snapshot

def test_end_state_R():
    assert end_state_R([0.1, 0.2, 0.3, 0.4, 0.5]) == (0.3 + 0.4 + 0.5) / 3
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement** (BN buffers are in `state_dict()`, so the hash covers them; `restore_snapshot` reloads host + optimizer + both RNG states and truncates `ctx.telemetry`/`ctx.curves_val` to `snap.epoch`). **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): episode runner, bitwise snapshot/restore, end-state reward"`

---

### Task 9: Fan executor — arms, twin, null-seed, diverged convention

**Files:**
- Modify: `experiments/kernel_demo.py` (section 8b)
- Create: `tests/unit/kernel_demo/test_fan.py`

**Interfaces:**
- Consumes: Task 8's episode API.
- Produces:
  - `class TwinDivergence(RuntimeError)` (carries `first_bad_epoch: int`).
  - `@dataclass ArmResult: name: str, status: str ("ok"|"diverged"), R_val: float, R_test: float, curve_val: list[float], curve_test: list[float], init_seed: int, g_at_init: float | None, rms_ratio_blend_entry: float | None`.
  - `run_arm(ctx, snap, arm_name: str, cfg) -> ArmResult` — restores snapshot; `arm_name` in `SEED_NAMES` germinates; `"noop"` doesn't; `"nullseed"` germinates `conv_light` then freezes `gain` at 0 (`gain.requires_grad_(False)`); runs remaining epochs; per-epoch: on `TelemetryDivergence` or non-finite loss → `status="diverged"`, curve truncated, `R = cfg.diverged_R` (both units). Records per-epoch **host-state hash list** when `arm_name in ("noop","nullseed")`.
  - `run_fan(ctx, snap, base_hashes: list[str], cfg) -> tuple[list[ArmResult], dict]` — arms sequentially: 4 seeds + noop-twin. Twin: compares its per-epoch hashes to `base_hashes[snap.epoch:]`; mismatch raises `TwinDivergence(first_bad_epoch)`. Cross-arm assertion: after TRAINING's K epochs, every finite seed arm's host hash equals the twin's hash at that epoch (assert, conditioned on finiteness). Second return: `{"host_hash_after_training": ..., "twin_ok": True}`.
  - `run_base(ctx, cfg) -> list[str]` — runs the no-op base to horizon recording per-epoch host hashes + val/test curves (this IS the no-op arm).

- [ ] **Step 1: Failing tests** (CPU tiny config as Task 8; horizon 6, K=1, M=1, F=1 via `dataclasses.replace`)

```python
# tests/unit/kernel_demo/test_fan.py
import dataclasses, pytest, torch
from experiments.kernel_demo import Config, TwinDivergence, make_episode, run_arm, run_base, run_fan, take_snapshot
from tests.unit.kernel_demo.test_episode import tiny_bundle

CFG = dataclasses.replace(Config(), horizon=6, K=1, M=1, F=1, batch_size=64, window=(1, 3))

def _episode_with_base(seed=31):
    ctx = make_episode(CFG, tiny_bundle(), "cpu", seed)
    hashes, curves = run_base(ctx, CFG)
    return ctx, hashes

def test_twin_matches_base_bitwise():
    ctx, hashes = _episode_with_base()
    # rebuild ctx to fan from epoch 2
    ctx2 = make_episode(CFG, tiny_bundle(), "cpu", 31)
    for e in range(2):
        from experiments.kernel_demo import train_one_epoch
        train_one_epoch(ctx2, e)
    snap = take_snapshot(ctx2)
    arms, meta = run_fan(ctx2, snap, hashes, CFG)
    assert meta["twin_ok"]
    assert {a.name for a in arms} == {"norm", "attn", "conv_light", "conv_heavy", "noop"}

def test_corrupted_base_hashes_trip_twin():
    ctx, hashes = _episode_with_base()
    ctx2 = make_episode(CFG, tiny_bundle(), "cpu", 31)
    from experiments.kernel_demo import train_one_epoch
    for e in range(2):
        train_one_epoch(ctx2, e)
    snap = take_snapshot(ctx2)
    bad = list(hashes); bad[3] = "deadbeef"
    with pytest.raises(TwinDivergence) as ei:
        run_fan(ctx2, snap, bad, CFG)
    assert ei.value.first_bad_epoch == 3

def test_nullseed_arm_reproduces_base():
    ctx, hashes = _episode_with_base()
    ctx2 = make_episode(CFG, tiny_bundle(), "cpu", 31)
    from experiments.kernel_demo import train_one_epoch
    for e in range(2):
        train_one_epoch(ctx2, e)
    snap = take_snapshot(ctx2)
    res = run_arm(ctx2, snap, "nullseed", CFG)
    # bitwise claim is empirical (spec contingency): assert value-exact curves at minimum
    base_ctx = make_episode(CFG, tiny_bundle(), "cpu", 31)
    _, base_curves = run_base(base_ctx, CFG)
    assert res.curve_val == pytest.approx(base_curves[2:], abs=0)
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** If the null-seed bitwise hash check fails while the twin holds, implement the spec's pre-stated contingency (value-exact comparison for null-seed only) and note it in the code comment with the spec citation. **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): fan executor, twin arm, null-seed arm, diverged convention 0.10"`

---

### Task 10: Fan records and the store — schema, shards, merge, split walls

**Files:**
- Modify: `experiments/kernel_demo.py` (section 9)
- Create: `tests/unit/kernel_demo/test_store.py`

**Interfaces:**
- Consumes: `ArmResult`, `env_block`, `frozen_block_hash`.
- Produces:
  - `SCHEMA_VERSION = 1`. `@dataclass FanRecord`: `schema_version, kind ("fan"|"refan"|"policy_run"|"preflight_iter"), episode_seed, seed_namespace ("dev"|"preflight"|"train"|"eval"), split_role ("preflight"|"train"|"tune"|"eval"), pathology_id, fan_epoch, refan_k (int|None), schedule_id, policy_checkpoint_id (str|None), config_hash, frozen_block_hash, common_future_hash, host_init_hash, env: dict, arms: list[ArmResult-as-dict], telemetry: list[dict], fan_id (sha256 of episode_seed:fan_epoch:kind:refan_k)`.
  - `encode_record(r) -> str` — JSON with non-finite floats mapped to `None` recursively (`_json_safe`); `decode_record(line) -> FanRecord`.
  - `class Store`: `Store(root: Path)`; `shard_path(worker_id)`; `append(worker_id, record)` (one `f.write(line + "\n"); f.flush()` per record); `merge() -> list[FanRecord]` sorted by `(episode_seed, fan_epoch, kind, refan_k)`; `load(split_role: str, kinds=("fan",)) -> list[FanRecord]` asserting every returned record matches and **raising `SplitViolation` if a caller requests `train` and any record with `split_role="eval"` matches the filter path** (defensive double-wall); `train_tune_split(records, cfg) -> tuple[list, list]` — 80/20 **by episode_seed** via `derive(episode_seed, "tune-split") % 5 == 0`.
  - `class SplitViolation(RuntimeError)`.

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_store.py
import math
from pathlib import Path
from experiments.kernel_demo import Store, decode_record, encode_record

def _rec(episode_seed=1, fan_epoch=5, split_role="train", kind="fan"):
    from experiments.kernel_demo import FanRecord
    return FanRecord(schema_version=1, kind=kind, episode_seed=episode_seed,
        seed_namespace="train", split_role=split_role, pathology_id="mild",
        fan_epoch=fan_epoch, refan_k=None, schedule_id="s", policy_checkpoint_id=None,
        config_hash="c", frozen_block_hash="f", common_future_hash="h",
        host_init_hash="i", env={"torch": "2.13"},
        arms=[{"name": "noop", "status": "ok", "R_val": 0.4, "R_test": 0.41,
               "curve_val": [0.1, float("nan")], "curve_test": [0.1, 0.2],
               "init_seed": 0, "g_at_init": None, "rms_ratio_blend_entry": None}],
        telemetry=[], fan_id="x")

def test_nonfinite_roundtrips_as_null():
    line = encode_record(_rec())
    assert "NaN" not in line
    r = decode_record(line)
    assert r.arms[0]["curve_val"][1] is None

def test_shards_merge_content_ordered(tmp_path):
    s = Store(tmp_path)
    s.append(1, _rec(episode_seed=9, fan_epoch=7))
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=9))
    got = [(r.episode_seed, r.fan_epoch) for r in s.merge()]
    assert got == [(2, 5), (2, 9), (9, 7)]

def test_split_wall(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(split_role="train"))
    s.append(0, _rec(episode_seed=3, split_role="eval"))
    assert all(r.split_role == "train" for r in s.load("train"))
    assert all(r.split_role == "eval" for r in s.load("eval"))
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): provenance-complete fan records, sharded store, split walls"`

---

### Task 11: Policy — embedding, causal transformer, factored head, deployment rule

**Files:**
- Modify: `experiments/kernel_demo.py` (section 10)
- Create: `tests/unit/kernel_demo/test_policy.py`

**Interfaces:**
- Consumes: `TELEMETRY_DIM`, `Normalizer`, `Config`, `make_generator`.
- Produces:
  - `class Policy(nn.Module)`: `__init__(cfg, gen: torch.Generator)` — embed MLP `TELEMETRY_DIM → d_model → d_model` (GELU), learned positional embedding (`horizon` slots), `nn.TransformerEncoder`-free hand-rolled 2 blocks (explicit-matmul self-attention with causal mask + MLP; reuse the AttnSeed pattern — keeps SDPA out and stays narrative-consistent), head `Linear(d_model, 5)` split as `[:, 0]` = NOW logit, `[:, 1:]` = seed logits. All weights drawn from `gen`.
  - `forward(tokens: Tensor [B,T,TELEMETRY_DIM], lengths: Tensor [B]) -> tuple[p_logit [B], seed_logits [B,4]]` — reads the hidden state at position `lengths-1` (the decision epoch).
  - `decide_live(policy, normalizer, telemetry: list[TelemetryRecord], epoch: int, cfg) -> tuple[bool, str | None]` — returns `(False, None)` outside `cfg.window`; else `(sigmoid(p_logit) > 0.5, argmax seed name if firing)`. Deterministic, no sampling.
  - `query_teacher_forced(policy, normalizer, telemetry_prefix, cfg) -> tuple[float, dict[str, float]]` — `(p, {seed: π})` at the prefix's last epoch.
  - `schedule_only_mask(vec: Tensor) -> Tensor` — zeroes every feature except the epoch-index feature (its index exported as `EPOCH_FEATURE_IDX`); the schedule-only comparator is `Policy` trained with this mask applied in its dataloader (Task 12 takes a `mask_fn`).

- [ ] **Step 1: Failing tests**

```python
# tests/unit/kernel_demo/test_policy.py
import torch
from experiments.kernel_demo import (Config, EPOCH_FEATURE_IDX, Policy, TELEMETRY_DIM,
                                     make_generator, schedule_only_mask)

def test_shapes_and_determinism():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    x = torch.randn(3, 7, TELEMETRY_DIM)
    L = torch.tensor([7, 5, 2])
    p1, s1 = pol(x, L); p2, s2 = pol(x, L)
    assert p1.shape == (3,) and s1.shape == (3, 4)
    assert torch.equal(p1, p2)

def test_causality_future_tokens_do_not_leak():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    x = torch.randn(1, 7, TELEMETRY_DIM)
    L = torch.tensor([4])                      # decision at position 3
    p_a, s_a = pol(x, L)
    x2 = x.clone(); x2[0, 5:] += 100.0         # perturb only future positions
    p_b, s_b = pol(x2, L)
    assert torch.equal(p_a, p_b) and torch.equal(s_a, s_b)

def test_schedule_only_mask_keeps_epoch_only():
    v = torch.arange(TELEMETRY_DIM, dtype=torch.float32)
    m = schedule_only_mask(v)
    assert m[EPOCH_FEATURE_IDX] == v[EPOCH_FEATURE_IDX]
    assert m.abs().sum() == v[EPOCH_FEATURE_IDX].abs()
```

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement** (causality: either build with a `[T,T]` upper-triangular `-inf` mask in the attention, or (simpler and exactly causal) run the trunk per-prefix — with T ≤ 15 decision epochs, batch-by-length is affordable; choose the mask; the test proves it either way). **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): telemetry transformer policy, factored head, deployment + teacher-forced queries"`

---

### Task 12: Learning — objectives, temperatures, warm-up, train/tune, checkpoint

**Files:**
- Modify: `experiments/kernel_demo.py` (section 11)
- Create: `tests/unit/kernel_demo/test_learning.py`

**Interfaces:**
- Consumes: `Policy`, `Store`, `Normalizer`, `FanRecord`.
- Produces:
  - `fan_to_example(rec: FanRecord, normalizer) -> dict` — `{tokens [T,DIM] normalized, length, R: Tensor[4] (val units, SEED_NAMES order, diverged→0.10 already applied upstream), R_noop: float}`.
  - `measure_fan_density(records) -> dict` — within-fan `mean(R_best − R_second)` and `mean(R_best − R_noop)` in **val units** (pre-flight/gate use) — takes a `unit="val"|"test"` argument, default `"val"`.
  - `policy_loss(policy, batch, cfg, fan_density: float, enable_now: bool, mask_fn=None) -> Tensor`:

```python
def policy_loss(policy, batch, cfg, fan_density, enable_now, mask_fn=None):
    tokens, lengths, R, R_noop = batch          # [B,T,D], [B], [B,4], [B]
    if mask_fn is not None:
        tokens = mask_fn(tokens)
    p_logit, seed_logits = policy(tokens, lengths)
    pi = seed_logits.softmax(-1)
    b_which = cfg.beta_which_frac * fan_density
    b_now = fan_density / cfg.beta_now_div
    j_which = (pi * R).sum(-1)
    ent_pi = -(pi * pi.clamp_min(1e-8).log()).sum(-1)
    loss = -(j_which + b_which * ent_pi)
    if enable_now:
        p = torch.sigmoid(p_logit / 1.0)        # temperature folded into b_now below
        adv_mix = (pi.detach() * R).sum(-1)     # sg[pi] — spec §Learning
        j_now = p * adv_mix + (1 - p) * R_noop
        ent_p = -(p * p.clamp_min(1e-8).log() + (1 - p) * (1 - p).clamp_min(1e-8).log())
        loss = loss - (j_now + b_now * ent_p)
    return loss.mean()
```

  - `train_policy(records, cfg, normalizer, gen, mask_fn=None, log: list | None = None) -> tuple[Policy, dict]` — train/tune split by episode, Adam(1e-3) on the policy (policy optimizer is NOT the host SGD contract; it is offline learning), warm-up phase (`warmup_frac` of total steps) with `enable_now=False`, then joint; after every epoch evaluate `J_which + J_now` on tune; keep best checkpoint (`copy.deepcopy(state_dict)`); returns `(policy_with_best_weights, {"curve": [...], "best_step": int, "fan_density": float})`.
  - `sign_flip_pvalue(lifts: Tensor, n: int, seed: int) -> float` (one-sided, `(count(null >= obs)+1)/(n+1)`).
  - `money_chart_permutation_pvalue(pathologies: list[str], picks: list[str], designed: dict, n, seed) -> tuple[int, float]` — observed rows-matched count and permutation p (shuffle pathology labels, recompute per-row modal pick vs designed winner, count ≥ observed).

- [ ] **Step 1: Failing tests** (synthetic fans — no GPU, no episodes: build 60 fake `FanRecord`s where telemetry feature 2 perfectly indicates which seed has R=0.6 vs 0.4, and R_noop=0.5 in 1/4 of them)

```python
# tests/unit/kernel_demo/test_learning.py
import torch
from experiments.kernel_demo import (Config, Normalizer, sign_flip_pvalue,
                                     money_chart_permutation_pvalue, train_policy)
from tests.unit.kernel_demo.helpers import synthetic_fans   # written in this task

def test_policy_learns_synthetic_mapping():
    cfg = Config()
    recs = synthetic_fans(n=120, seed=5)
    pol, info = train_policy(recs, cfg, Normalizer.identity(), torch.Generator().manual_seed(0))
    acc = synthetic_agreement(pol, recs[-24:])   # helper: pick == planted winner
    assert acc > 0.6                              # >> 0.25 chance

def test_sign_flip_pvalue_calibration():
    g = torch.Generator().manual_seed(1)
    null_lifts = torch.randn(100, generator=g) * 0.01
    p = sign_flip_pvalue(null_lifts, n=2000, seed=2)
    assert p > 0.05                                # no effect → not significant
    p2 = sign_flip_pvalue(null_lifts + 0.02, n=2000, seed=2)
    assert p2 < 0.01                               # clear effect → significant

def test_money_chart_permutation_null():
    paths = ["a"] * 10 + ["b"] * 10
    picks = ["x"] * 10 + ["y"] * 10
    designed = {"a": "x", "b": "y"}
    obs, p = money_chart_permutation_pvalue(paths, picks, designed, n=2000, seed=3)
    assert obs == 2 and p < 0.05
```

(`tests/unit/kernel_demo/helpers.py` provides `synthetic_fans` — fabricated `FanRecord`s with a plantable telemetry→winner rule — and `synthetic_agreement`; `Normalizer.identity()` is a classmethod added in this task returning a no-op normalizer.)

- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS (the learning test is the slowest unit test; keep it < 60 s by capping steps).
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): offline full-information objectives, warm-up, tune checkpointing, permutation tests"`

---

### Task 13: `--selftest`

**Files:**
- Modify: `experiments/kernel_demo.py` (section 12, selftest + shared runtime setup)
- Create: `tests/unit/kernel_demo/test_selftest.py`

**Interfaces:**
- Produces: `run_selftest(cfg, device) -> dict` wired to the CLI. Contents, in order (each prints PASS/FAIL, function returns `{"ok": bool, ...}`):
  1. `enable_class1()`; print `FORBIDDEN_RELAXATIONS`.
  2. Smoke episode on `device` with `dataclasses.replace(cfg, horizon=8, K=1, M=1, F=1)` and a 2k-sample data subset: base run → fan at epoch 3 → twin holds; null-seed arm reproduces base (value-exact minimum, bitwise reported).
  3. Blindness grep: `inspect.getsource` of the telemetry section scanned for `time.time|datetime.now|monotonic|os.environ|hostname` — fail on hit.
  4. JSON round-trip of a record containing NaN/Inf curves.
  5. Store split-wall check (write train+eval records to a temp store, assert `load("train")` excludes eval).
  6. τ-init RMS check on all four seeds against a real host batch.
- CLI: `python -m experiments.kernel_demo selftest [--device cuda:0]`.

- [ ] **Step 1: Failing test** — `test_selftest_runs_clean_cpu()` calling `run_selftest(cfg, "cpu")`, asserting `result["ok"]`.
- [ ] **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS. Then run the real thing on GPU: `uv run python -m experiments.kernel_demo selftest --device cuda:0`. Expected: all PASS. If the twin trips on GPU but held on CPU, the Class 1 knob set is incomplete — debug THAT (it is the exact failure the twin exists to catch); do not weaken the check.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): --selftest (twin smoke, blindness grep, split walls, tau-init check)"`

---

### Task 14: `--preflight` — gates 1–8, refans, freeze

**Files:**
- Modify: `experiments/kernel_demo.py` (section 12, preflight)
- Create: `tests/unit/kernel_demo/test_preflight_gates.py` (gate logic on synthetic inputs only — the real preflight is a GPU run)

**Interfaces:**
- Produces:
  - `draw_schedule(episode_seed, cfg) -> tuple[int, int]` — 2 ordered epochs uniform-without-replacement from `range(window[0], window[1]+1)` via `derive(episode_seed, "schedule")`.
  - `run_collection_episode(cfg, data, device, episode_seed, namespace, split_role, store, worker_id) -> None` — base run (recording hashes + both unit curves), two fans at the scheduled epochs, records appended.
  - `run_refan(cfg, data, device, episode_seed, fan_epoch, k, ...) -> FanRecord` — future re-drawn `derive(episode_seed, "refan", k)`, 5 real arms including fresh no-op, `kind="refan"`.
  - Gate functions, each `(records, cfg) -> GateResult(ok: bool, detail: dict, remedy: str)`, unit of analysis = first fan per episode:
    - `gate1_noop_sanity` — no-op is val-argmax (5-arm argmax incl. noop, val units) in ≥2 mild episodes AND modal winner in no targeted pathology. Remedy `"sampler"`.
    - `gate2_signal` — (a) logistic probe (implemented as a 1-layer `nn.Linear` trained 200 steps) telemetry→pathology with GroupShuffleSplit by episode (hand-rolled: episodes shuffled by `derive`, 70/30); accuracy > 0.5. (b) probe telemetry→val-argmax(4-seed) vs majority-class rate; plus contingency table pathology × val-argmax printed against `DESIGNED_WINNER`. Remedy `"sampler"`.
    - `gate3_contrast` — `measure_fan_density(unit="val")` vs refan noise floor (from the preflight refans): density > 2× floor. Remedy `"averaging window, horizon"`.
    - `gate4_dominance` — no seed >40% of val-argmax overall, none a majority in every pathology. Remedy `"sampler/menu balance"`.
    - `gate5_magnitude` — max/min of mean `rms_ratio_blend_entry` per seed ≤ 2. Remedy `"tau, lam, seed_lr — never the sampler"`.
    - `gate6_horizon` — val fan density at late epochs ≥ 0.5× early. Remedy `"horizon, window"`.
    - `gate7_now_vs_later` — report-only: `P(A(t_late) > A(t_early))`, mean gap (A = best-seed R_val − R_noop_val per fan).
    - `gate8_pressure` — GPU-only: twin at 1 worker vs full count on one episode seed; report + contingency note.
  - `run_preflight(cfg, data, device, store) -> dict` — 30 preflight-namespace episodes (+10 refans on a subset), all gates, fits + saves `Normalizer` and writes `runs/kernel_demo/frozen.json` = `{frozen_block_hash, normalizer, fan_density_val, schedule_id, git_rev, gate_results, iteration}` — the **freeze artifact**; each invocation while unfrozen appends a `preflight_iter` record.

- [ ] **Step 1: Failing tests** — gate logic on hand-built record lists (e.g., `gate4` fed 10 fans where conv_heavy wins 8 → `ok=False`; `gate1` fed mild fans where noop never wins → `ok=False`; `gate5` fed rms ratios (0.04, 0.05, 0.06, 0.30) → `ok=False`). Concrete asserts per gate, synthetic records via Task 12's helpers.
- [ ] **Step 2: Run** — FAIL. **Step 3: Implement gates + preflight driver.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): preflight gates 1-8, refans, freeze artifact"`
- [ ] **Step 6 (GPU, manual):** `uv run python -m experiments.kernel_demo preflight --device cuda:0` on the subset flag first, then full. Iterate the sampler per gate remedies until all gates pass. **This is the pathology-tuning loop the spec licenses — sampler changes only, logged as preflight_iter records.** Surface the gate table to the user before freezing. Expected wall-clock: ~1–2 h.

---

### Task 15: `--collect` — process workers

**Files:**
- Modify: `experiments/kernel_demo.py` (section 12, collect)
- Create: `tests/unit/kernel_demo/test_collect.py`

**Interfaces:**
- Produces: `run_collect(cfg, store_root, devices: list[str], n_workers_per_device: int) -> None` — asserts `frozen.json` exists and its `frozen_block_hash` matches the live `Config` (refuses otherwise); splits `cfg.n_collect` episode seeds (`derive(run_seed, "train", i)`) across `multiprocessing.get_context("spawn")` workers; each worker: `enable_class1()`, pins its device, loads data once, loops `run_collection_episode(...)` into its own shard; parent joins and prints per-worker counts. `worker_main(args_tuple)` module-level (spawn-picklable). A `--limit N` flag for smoke runs.
- Test (CPU): `run_collect` with 2 workers × 2 episodes on the tiny bundle path (inject via a `_data_loader` hook attribute settable in tests) produces 4 episodes × 2 fans = 8 fan records across 2 shards, merge is content-ordered, all `split_role="train"`.

- [ ] **Step 1: Failing test** as above. **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): schedule-driven collection with process workers and shards"`
- [ ] **Step 6 (GPU, manual):** smoke `--limit 4`, then the real overnight run: `uv run python -m experiments.kernel_demo collect --devices cuda:0,cuda:1 --workers 3`. Expected: 300 episodes / 600 fans by morning; twin abort halts everything loudly if determinism breaks.

---

### Task 16: `--train` and `--eval`

**Files:**
- Modify: `experiments/kernel_demo.py` (section 12, train + eval)
- Create: `tests/unit/kernel_demo/test_eval_stats.py`

**Interfaces:**
- Produces:
  - `run_train(cfg, store_root) -> None` — loads `split_role="train"` fans + frozen normalizer, `train_policy` (trained + schedule-only variants — same records, `mask_fn=schedule_only_mask` for the latter), saves `runs/kernel_demo/policy_{trained,schedule_only}.pt` with `policy_checkpoint_id` = state-dict hash; prints tune curves.
  - `run_eval(cfg, data, device, store_root) -> dict` — refuses if any eval record predates the freeze hash; for each of `cfg.n_eval` eval seeds (`derive(run_seed, "eval", i)`) runs, per comparator:
    - `trained` — live episode, `decide_live`; `random` — germinates at `derive(episode_seed,"random-null") % window-span + window[0]`, uniform seed; `schedule_only` — live with masked telemetry; `fixed_epoch` — trained WHICH forced at `t_star`. Every comparator's episode is a `policy_run` record; lift = `R_chosen_test − R_noop_test` (base run = noop; never-germinate → 0.0).
    - Frozen grid: 2 forced fans per eval episode at `draw_schedule(episode_seed ⊕ "evalgrid")` epochs → 200 grid fans (`kind="fan"`, `split_role="eval"`); teacher-forced queries vs **test-argmax over 4 seed arms**; ~30 grid points refanned for the Σp² ceiling (test units).
    - Outputs dict: per-comparator lift vectors + germination rates, `sign_flip_pvalue` for trained-vs-0 and paired trained-vs-schedule-only, agreement vs majority-class null, money-chart rows + `money_chart_permutation_pvalue`, falsifier (derangement of telemetry histories **across pathology classes** — implemented as: group eval grid episodes by pathology, rotate assignments one pathology class forward), restraint regret at last grid point + per-point, WHEN contrast restricted + unrestricted, ceiling + Wilson CI, `P(val-argmax = test-argmax)`, power note inputs (fan density, N). Everything serialized to `runs/kernel_demo/eval_results.json`.
- Tests: statistics-only, synthetic inputs — Wilson CI helper against a known value; derangement helper never maps a pathology class to itself; restricted-vs-unrestricted WHEN contrast computed correctly on a hand-built 6-episode fixture (2 never-germinate); pre-registered thresholds function `verdict(results, cfg) -> dict[str, bool]` returns the five spec threshold booleans on a fixture where all pass and one where lift fails.

- [ ] **Step 1: Failing tests.** **Step 2: Run** — FAIL. **Step 3: Implement.** **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): --train (trained + schedule-only), --eval battery with pre-registered verdicts"`
- [ ] **Step 6 (GPU, manual, ONE SHOT):** `train` on the merged store; then — only after confirming with the user that collection is complete and frozen — `eval` runs ONCE. No peeking, no reruns (spec: evaluated once).

---

### Task 17: `--report`, `--replay`, plotting sidecar

**Files:**
- Modify: `experiments/kernel_demo.py` (section 12, report + replay)
- Create: `experiments/kernel_demo_plots.py`, `tests/unit/kernel_demo/test_report.py`

**Interfaces:**
- Produces:
  - `run_report(cfg, store_root) -> None` — refuses mixed namespaces; prints the full spec §Report list as aligned text tables (lift table with germination rates; agreement vs nulls + ceiling-as-context labeled "Σp² lower bound"; money chart + falsifier twin + chosen-seed marginal + diverged-excluded companion; observed diverged-arm end-state accuracies beside 0.10; fan density + `P(val=test argmax)`; per-seed failure rates; restraint regret both forms; realized p by sign(A); tune curve; entropy temperatures; deterministic-mode cost; power note text with MDE from measured density) and calls the sidecar for PNGs into `runs/kernel_demo/plots/`.
  - `kernel_demo_plots.py`: `plot_arm_curves(records, outdir)` (per-pathology, spike-then-crash highlighted = any arm whose curve max exceeds its end-state by >0.05), `plot_alpha_beta(record, outdir)`, `plot_money_chart(matrix, outdir)` (+ falsifier + diverged-excluded companions), `plot_tune_curve(info, outdir)`, `plot_rms_at_blend_entry(records, outdir)`.
  - `run_replay(cfg, fan_id, store_root, device) -> None` — finds the record, env-block refusal on `REPLAY_REFUSAL_KEYS`, re-derives the episode, forces the fan at the recorded epoch, asserts recorded `R_val` per arm (exact for ok arms), prints PASS/localises via `host_init_hash` on mismatch.
- Test: report formatting helpers on the eval-results fixture from Task 16 (table renders, refusal on mixed namespaces raises); replay refusal triggers on a doctored env block.

- [ ] **Step 1: Failing tests.** **Step 2: Run** — FAIL. **Step 3: Implement** (add `matplotlib` as a dev-group dependency: `uv add --group dev matplotlib`). **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** — `git commit -am "feat(kernel-demo): --report, --replay with env refusal, plotting sidecar"`

---

### Task 18: Narrative pass, wardline gate, final verification

**Files:**
- Modify: `experiments/kernel_demo.py` (comments/docstrings only — zero behavior changes)

- [ ] **Step 1:** Read the file top-to-bottom as the spec's target reader. Every section banner gets a 2–5 line "why" docstring quoting the spec decision it implements (the caveat header, the delta contract, the twin's non-optionality, the 0.10 rationale, the unit wall). Verify the file order matches the spec's narrative order. Check length ≲1200 lines (excluding tests); if over, move only *plotting* out (already out) — do not split the file (scope pin).
- [ ] **Step 2:** `uv run pytest tests/unit/kernel_demo -v` — all pass. `uv run python -m experiments.kernel_demo selftest --device cuda:0` — all PASS.
- [ ] **Step 3:** `wardline scan . --fail-on ERROR` (project rule). Expected exit 0. Fix findings at the boundary if any; exit 2 = wardline error → report it to the user, per the dogfooding rule.
- [ ] **Step 4:** `uv run mypy src experiments && uv run ruff check experiments tests` — clean (pre-commit enforces anyway).
- [ ] **Step 5:** Commit — `git commit -am "feat(kernel-demo): narrative pass, single-file demo complete"`. Update filigree: `filigree update simic-4a44ed57c9 --status <appropriate>` noting implementation complete pending preflight/collect/eval runs.

---

## Execution ordering and the GPU checkpoints

Tasks 1–13 are pure build (CPU-testable, subagent-friendly). Task 13 step 4, Task 14 step 6, Task 15 step 6, and Task 16 step 6 are **GPU checkpoints that need the user's machine and, for preflight tuning and the one-shot eval, the user's presence** — pause and surface results at each. The spec's freeze discipline binds from Task 14 step 6 onward: after freeze, sampler/normalizer/temperature/schedule changes void the run.

## Self-review notes (done)

- Spec coverage: every spec section maps to a task (constants/frozen block → 1; data/unit wall → 2; telemetry/normalizer/blindness → 3; host/pathologies → 4; seeds/τ-init → 5; lifecycle/optimizer → 6; determinism → 7; episode/snapshot → 8; fan/twin/null-seed/0.10 → 9; record/store/shards/replay-refusal-keys → 10, 17; policy/deployment → 11; objectives/warm-up/tune → 12; selftest → 13; gates/refans/freeze/pressure test → 14; collection → 15; comparators/eval/pre-registered verdicts → 16; report/plots/replay → 17; caveat header/narrative → 18 and Task 1's docstring).
- Deliberate deviations from spec lettering, none semantic: GERMINATED collapses into TRAINING's first tick (spec FSM lists it; zero-duration here, noted in code); gate 2's probe is a 200-step linear layer rather than sklearn (no new dependency).
- Type consistency checked: `Config`, `FanRecord`, `ArmResult`, `Snapshot`, `run_*` signatures used identically across tasks; `state_hash` is the single hashing primitive everywhere.
