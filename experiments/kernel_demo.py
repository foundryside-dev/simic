"""Kernel Demo — "Simic in 20 minutes".

Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
exactly what Simic proper rejects (generation from live host state). This
demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis.

Spec (LOCKED, rev 6.2): docs/superpowers/specs/2026-08-09-kernel-demo-design.md

Narrative order (one file, read top to bottom):
  1  identity & config   — semantic surface, config_hash, frozen block, derive/rng
  2  data                — CIFAR splits, GPU residency, CommonFuture, augment
  3  telemetry           — TelemetryRecord (blind by construction), Normalizer
  4  host                — undersized CNN, four pathologies, fixed 64-wide slot
  5  seeds               — delta contract, tau-init (D11), decay groups
  6  slot lifecycle      — STE, alpha/beta schedules, trust region, optimizer
  7  determinism         — Class 1 knobs, zero-normalized state_hash (D8), env
  8  episode             — epoch loop, snapshot, germination (D12)
  9  fan executor        — arm-local materialization, twin, null-seed
  10 records & store     — schema, shards, split walls, durability
  11 policy              — trunk, factored head, deployment rule, masks
  12 learning            — objectives, frozen temperatures, warm-up, tune ckpt
  13 --selftest          — check battery, --certify artifact
  14 --preflight         — gates 1-8, refans, FreezeManifest
  15 --collect           — idempotent spawn workers, halt channel
  16 --train / --eval    — comparator battery, frozen grid, verdict
  17 --report / --replay — tables (D4/D6), bitwise replay with localisation

Plots live in the standalone sidecar kernel_demo_plots.py (never on the
semantic surface).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import enum
import hashlib
import inspect
import json
import math
import os
import platform
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

import torch
from torch import nn

# section 1 — IDENTITY AND CONFIG
# 2 (spec rev 6.2, pre-data): per-arm telemetry, cost and horizon-influence
# fields added to the arm payload. Additive, and no store existed at the bump.
SCHEMA_VERSION = 2

_SEMANTIC_SURFACE: list[Callable[..., object]] = []


def semantic[T: Callable[..., object]](obj: T) -> T:
    # Import-time registration, exactly once per process. NEVER call from a
    # factory: call-time registration made config_hash depend on call order
    # (rev 3 defect — a worker mid-episode and a fresh parent disagreed).
    _SEMANTIC_SURFACE.append(obj)
    return obj


_SEMANTIC_CONSTANTS: dict[str, object] = {}


def semantic_const[T](name: str, value: T) -> T:
    # Behavior-changing module constants that are neither Config fields nor
    # source-hashable classes/functions. Registered at definition, import
    # time — same discipline as @semantic, same reason. Register only plain
    # Python values (tuples/dicts/ints/strs) — never tensors or other objects
    # whose repr truncates or reads global state. Register a constant iff
    # changing its value changes computed numbers or gate outcomes;
    # documentation-only lists (FORBIDDEN_RELAXATIONS, MODES) and
    # independently-recorded identities (SCHEMA_VERSION — already in every
    # record) stay out.
    if name in _SEMANTIC_CONSTANTS:
        raise ValueError(f"semantic_const duplicate: {name}")
    _SEMANTIC_CONSTANTS[name] = value
    return value


_NON_SEMANTIC: dict[str, str] = {
    # name -> stated reason a public symbol is NOT on the semantic surface.
    # Default for new public classes/functions is @semantic; entry here is
    # the explicit opt-out (test_every_public_symbol_is_classified enforces).
    "Config": "field values covered by frozen_block_hash; unfrozen fields are licensed operational levers",
    "semantic": "hash mechanism — an edit changes every hash by construction",
    "semantic_const": "hash mechanism",
    "config_hash": "hash mechanism",
    "frozen_block_hash": "hash mechanism",
    "main": "CLI orchestration; every semantic step it dispatches is independently on the surface",
}


@semantic
def derive(seed: int, *labels: str | int) -> int:
    h = hashlib.sha256()
    h.update(seed.to_bytes(8, "big"))
    for label in labels:
        part = str(label).encode()
        h.update(len(part).to_bytes(4, "big"))
        h.update(part)
    return int.from_bytes(h.digest()[:8], "big")


@semantic
def make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator:
    g = torch.Generator(device=device)
    # full uint64 is accepted; do NOT mask (seed aliasing). CPU and CUDA
    # generators produce different streams for the same seed — all current
    # call sites use the CPU default; do not assume cross-device comparability.
    g.manual_seed(seed)
    return g


@semantic
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
    tau_eps: float = 1e-6  # plan-authored (spec names no value)
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
    preflight_refans: int = 12  # gate-3 noise-floor refans (plan-authored, owner sign-off at freeze)
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
    n_collect: int = 300  # spec's "extend collection pre-eval" lever
    d_model: int = 64
    n_layers: int = 2
    eval_chunk: int = 1000  # plan-authored
    fsync_every: int = 20  # plan-authored durability cadence
    # Frozen beyond the spec's frozen-block list: both are trajectory-defining
    # (batch_size shapes every gradient step; run_seed derives the data split
    # and every episode population) and no other hash covers them — outside
    # FROZEN_FIELDS an edit would pass every refusal gate silently.
    batch_size: int = 128
    run_seed: int = 20260809


FROZEN_FIELDS: tuple[str, ...] = (
    "tau",
    "tau_eps",
    "lam",
    "stage_k",
    "stage_m",
    "stage_f",
    "horizon",
    "window",
    "t_star",
    "lr",
    "momentum",
    "wd",
    "seed_lr",
    "diverged_r",
    "fans_per_episode",
    "preflight_refans",
    "n_preflight",
    "n_eval",
    "alpha_level",
    "permutation_resamples",
    "beta_which_frac",
    "beta_now_div",
    "gate1_min_mild_noop_wins",
    "gate2_probe_min_acc",
    "gate3_contrast_mult",
    "gate4_dominance_max",
    "gate5_rms_band",
    "gate6_late_density_mult",
    "policy_lr",
    "policy_batch_size",
    "policy_steps",
    "warmup_frac",
    "batch_size",
    "run_seed",
)


def frozen_block_hash(cfg: Config) -> str:
    lines = sorted(f"{k}={getattr(cfg, k)!r}" for k in FROZEN_FIELDS)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def config_hash() -> str:
    h = hashlib.sha256()
    for src in sorted(inspect.getsource(obj) for obj in _SEMANTIC_SURFACE):
        h.update(src.encode())
    for name in sorted(_SEMANTIC_CONSTANTS):
        h.update(f"{name}={_SEMANTIC_CONSTANTS[name]!r}".encode())
    return h.hexdigest()


MODES = ("selftest", "preflight", "collect", "train", "eval", "report", "replay")


# section 2 — DATA
CIFAR_MEAN_RGB = semantic_const("CIFAR_MEAN_RGB", (0.4914, 0.4822, 0.4465))
CIFAR_STD_RGB = semantic_const("CIFAR_STD_RGB", (0.2470, 0.2435, 0.2616))
CIFAR_MEAN = torch.tensor(CIFAR_MEAN_RGB).view(1, 3, 1, 1)
CIFAR_STD = torch.tensor(CIFAR_STD_RGB).view(1, 3, 1, 1)


@semantic
@dataclass
class DataBundle:
    train_x: torch.Tensor
    train_y: torch.Tensor
    val_x: torch.Tensor
    val_y: torch.Tensor
    test_x: torch.Tensor
    test_y: torch.Tensor


@semantic
def split_indices(run_seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    perm = torch.randperm(50_000, generator=make_generator(derive(run_seed, "valsplit")))
    return perm[:45_000], perm[45_000:]


@semantic
def data_split_id(cfg: Config) -> str:
    train_idx, val_idx = split_indices(cfg.run_seed)
    h = hashlib.sha256()
    for idx in (train_idx, val_idx):
        arr = idx.numpy().tobytes()
        h.update(len(arr).to_bytes(8, "big"))
        h.update(arr)
    return h.hexdigest()


@semantic
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
        to_device(x[train_idx]),
        to_device(y[train_idx]),
        to_device(x[val_idx]),
        to_device(y[val_idx]),
        to_device(tx),
        to_device(ty),
    )


@semantic
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
        if steps == 0:
            raise ValueError(f"n_train={n_train} < batch_size={bs}: zero steps per epoch (subset too small)")
        order = torch.stack([torch.randperm(n_train, generator=g)[: steps * bs] for _ in range(epochs)])
        crops = torch.randint(0, 9, (epochs, steps, bs, 2), generator=g, dtype=torch.uint8)
        flips = torch.rand(epochs, steps, bs, generator=g) < 0.5
        h = hashlib.sha256()
        for t in (order, crops, flips):
            h.update(t.numpy().tobytes())
        return cls(order, crops, flips, epochs, h.hexdigest())


@semantic
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


# section 3 — TELEMETRY
class TelemetryDivergence(RuntimeError):  # noqa: N818
    pass


TELEMETRY_DIM = semantic_const("TELEMETRY_DIM", 20)
EPOCH_FEATURE_IDX = semantic_const("EPOCH_FEATURE_IDX", 0)


@semantic
@dataclass(frozen=True)
class TelemetryRecord:
    epoch: int
    train_loss: float
    val_loss: float
    val_acc: float
    train_loss_delta: float
    val_loss_delta: float
    grad_norm_mean: tuple[float, float, float]
    grad_norm_var: tuple[float, float, float]
    act_saturation: tuple[float, float, float]
    weight_norm: tuple[float, float, float]
    per_class_val_acc_std: float
    confusion_entropy: float

    def __post_init__(self) -> None:
        def check_finite(val: object) -> None:
            if isinstance(val, float):
                if not (val == val and val != float("inf") and val != float("-inf")):
                    raise TelemetryDivergence(f"Non-finite value: {val}")
            elif isinstance(val, tuple):
                for item in val:
                    if not (item == item and item != float("inf") and item != float("-inf")):
                        raise TelemetryDivergence(f"Non-finite value in tuple: {item}")
            elif isinstance(val, int):
                pass

        check_finite(self.train_loss)
        check_finite(self.val_loss)
        check_finite(self.val_acc)
        check_finite(self.train_loss_delta)
        check_finite(self.val_loss_delta)
        check_finite(self.grad_norm_mean)
        check_finite(self.grad_norm_var)
        check_finite(self.act_saturation)
        check_finite(self.weight_norm)
        check_finite(self.per_class_val_acc_std)
        check_finite(self.confusion_entropy)


@semantic
def record_to_vector(r: TelemetryRecord) -> torch.Tensor:
    values = [
        float(r.epoch),
        r.train_loss,
        r.val_loss,
        r.val_acc,
        r.train_loss_delta,
        r.val_loss_delta,
        r.grad_norm_mean[0],
        r.grad_norm_mean[1],
        r.grad_norm_mean[2],
        r.grad_norm_var[0],
        r.grad_norm_var[1],
        r.grad_norm_var[2],
        r.act_saturation[0],
        r.act_saturation[1],
        r.act_saturation[2],
        r.weight_norm[0],
        r.weight_norm[1],
        r.weight_norm[2],
        r.per_class_val_acc_std,
        r.confusion_entropy,
    ]
    return torch.tensor(values, dtype=torch.float32)


@semantic
def confusion_stats(logits: torch.Tensor, labels: torch.Tensor, n_classes: int = 10) -> tuple[float, float]:
    with torch.no_grad():
        preds = torch.argmax(logits, dim=1)
        confusion = torch.zeros(n_classes, n_classes, device=logits.device, dtype=torch.float32)
        for i in range(n_classes):
            mask = labels == i
            if mask.sum() == 0:
                continue
            pred_i = preds[mask]
            for j in range(n_classes):
                confusion[i, j] = (pred_i == j).sum().float()
        total_per_class = confusion.sum(dim=1, keepdim=True)
        total_per_class = torch.clamp(total_per_class, min=1e-8)
        accuracy_per_class = confusion.diagonal() / total_per_class.squeeze()
        std = float(accuracy_per_class.std())
        off_diag = confusion.clone()
        off_diag.fill_diagonal_(0)
        off_diag_sum = off_diag.sum()
        if off_diag_sum > 0:
            off_diag = off_diag / off_diag_sum
            entropy = float(-(off_diag[off_diag > 0] * torch.log(off_diag[off_diag > 0])).sum())
        else:
            entropy = 0.0
    return std, entropy


@semantic
class Normalizer:
    medians: torch.Tensor
    iqrs: torch.Tensor

    def __init__(self, medians: torch.Tensor | None = None, iqrs: torch.Tensor | None = None) -> None:
        if medians is None:
            self.medians = torch.zeros(TELEMETRY_DIM, dtype=torch.float32)
        else:
            self.medians = medians
        if iqrs is None:
            self.iqrs = torch.ones(TELEMETRY_DIM, dtype=torch.float32)
        else:
            self.iqrs = iqrs

    def fit(self, vectors: list[torch.Tensor]) -> None:
        stacked = torch.stack(vectors)
        self.medians = torch.median(stacked, dim=0).values
        q1 = torch.quantile(stacked, 0.25, dim=0)
        q3 = torch.quantile(stacked, 0.75, dim=0)
        iqrs = q3 - q1
        self.iqrs = torch.clamp(iqrs, min=1e-8)

    def apply(self, v: torch.Tensor) -> torch.Tensor:
        return (v - self.medians) / self.iqrs

    def to_json(self) -> str:
        import json

        return json.dumps(
            {
                "medians": self.medians.tolist(),
                "iqrs": self.iqrs.tolist(),
            }
        )

    @classmethod
    def from_json(cls, s: str) -> Normalizer:
        import json

        data = json.loads(s)
        return cls(
            medians=torch.tensor(data["medians"], dtype=torch.float32),
            iqrs=torch.tensor(data["iqrs"], dtype=torch.float32),
        )

    @classmethod
    def identity(cls) -> Normalizer:
        return cls(
            medians=torch.zeros(TELEMETRY_DIM, dtype=torch.float32),
            iqrs=torch.ones(TELEMETRY_DIM, dtype=torch.float32),
        )


_NON_SEMANTIC["TelemetryDivergence"] = "exception class — no computation depends on its definition"


@semantic
def build_record(
    epoch: int,
    train_loss: float,
    val_loss: float,
    val_acc: float,
    train_loss_delta: float,
    val_loss_delta: float,
    grad_norm_mean: tuple[float, float, float],
    grad_norm_var: tuple[float, float, float],
    act_saturation: tuple[float, float, float],
    weight_norm: tuple[float, float, float],
    per_class_val_acc_std: float,
    confusion_entropy: float,
) -> TelemetryRecord:
    return TelemetryRecord(
        epoch=epoch,
        train_loss=train_loss,
        val_loss=val_loss,
        val_acc=val_acc,
        train_loss_delta=train_loss_delta,
        val_loss_delta=val_loss_delta,
        grad_norm_mean=grad_norm_mean,
        grad_norm_var=grad_norm_var,
        act_saturation=act_saturation,
        weight_norm=weight_norm,
        per_class_val_acc_std=per_class_val_acc_std,
        confusion_entropy=confusion_entropy,
    )


# section 4 — HOST
PATHOLOGIES = semantic_const(
    "PATHOLOGIES",
    ("under_normalized", "channel_starved", "no_spatial_mix", "mild"),
)
DESIGNED_WINNER = semantic_const(
    "DESIGNED_WINNER",
    {
        "under_normalized": "norm",
        "channel_starved": "conv_heavy",
        "no_spatial_mix": "attn",
        "mild": "conv_light",
    },
)


@semantic
class Host(nn.Module):
    # All pathology wiring lives here (constructor + private helpers) so an edit to any
    # pathology's shape moves config_hash — build_host below is construction plumbing only.
    def __init__(self, pathology: str) -> None:
        super().__init__()
        if pathology not in PATHOLOGIES:
            raise ValueError(f"unknown pathology: {pathology}")
        self.pathology = pathology
        w1, w2, w3 = 24, 64, 80
        if pathology == "mild":
            w1, w3 = 20, 72
        use_bn = pathology != "under_normalized"
        gain = 2.0 if pathology == "under_normalized" else 1.0
        s2_kernel, s2_pad = (1, 0) if pathology == "no_spatial_mix" else (3, 1)
        s2_mid = 24 if pathology == "channel_starved" else w2
        self.stage1 = self._make_stage(3, w1, w1, 3, 1, use_bn, gain)
        self.stage2 = self._make_stage(w1, s2_mid, w2, s2_kernel, s2_pad, use_bn, gain)
        self.stage3 = self._make_stage(w2, w3, w3, 3, 1, use_bn, gain)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(w3, 10)
        self.feat_channels = 64
        self.stage_stats: dict[str, list[float]] = {}

    def _make_stage(
        self,
        in_ch: int,
        mid_ch: int,
        out_ch: int,
        kernel_size: int,
        padding: int,
        use_bn: bool,
        gain: float,
    ) -> nn.Sequential:
        conv1 = nn.Conv2d(in_ch, mid_ch, kernel_size, padding=padding, bias=False)
        conv2 = nn.Conv2d(mid_ch, out_ch, kernel_size, padding=padding, bias=False)
        if gain != 1.0:
            with torch.no_grad():
                conv1.weight.mul_(gain)
                conv2.weight.mul_(gain)
        norm1: nn.Module = nn.BatchNorm2d(mid_ch) if use_bn else nn.Identity()
        norm2: nn.Module = nn.BatchNorm2d(out_ch) if use_bn else nn.Identity()
        return nn.Sequential(conv1, norm1, nn.ReLU(), conv2, norm2, nn.ReLU(), nn.MaxPool2d(2))

    def forward_to_slot(self, x: torch.Tensor) -> torch.Tensor:
        h = self.stage1(x)
        return cast(torch.Tensor, self.stage2(h))  # slot site: [B, 64, 8, 8] for every pathology

    def forward(self, x: torch.Tensor, slot: Slot | None = None) -> torch.Tensor:
        h = self.forward_to_slot(x)
        if slot is not None:
            h = slot(h)
        h = self.stage3(h)
        h = self.gap(h)
        h = torch.flatten(h, 1)
        return cast(torch.Tensor, self.fc(h))

    def stage_modules(self) -> tuple[nn.Sequential, nn.Sequential, nn.Sequential]:
        return self.stage1, self.stage2, self.stage3

    def attach_stat_hooks(self) -> None:
        self.stage_stats["saturation"] = [0.0, 0.0, 0.0]
        for idx, stage in enumerate(self.stage_modules()):
            last_relu = stage[5]  # conv, norm, relu, conv, norm, relu, pool
            last_relu.register_forward_hook(self._saturation_hook(idx))

    def _saturation_hook(self, idx: int) -> Callable[[nn.Module, tuple[torch.Tensor, ...], torch.Tensor], None]:
        def hook(_module: nn.Module, _inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:
            self.stage_stats["saturation"][idx] = float((output == 0).float().mean().item())

        return hook


@semantic
def build_host(pathology: str, init_seed: int) -> Host:
    with rng_scope(make_generator(init_seed)):
        return Host(pathology)


# section 5 — SEEDS
SEED_NAMES = semantic_const("SEED_NAMES", ("norm", "attn", "conv_light", "conv_heavy"))


@semantic
class SeedDelta(nn.Module):
    # Delta contract: the seed's contribution is gain * f(h); gain is born 0.0
    # (exact zero delta before tau_init) and is the ONLY parameter carrying tau.
    def __init__(self) -> None:
        super().__init__()
        self.gain = nn.Parameter(torch.zeros(()))

    def f(self, h: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        return self.gain * self.f(h)


@semantic
class NormSeed(SeedDelta):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.gn = nn.GroupNorm(8, channels)

    def f(self, h: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.gn(h) - h)


@semantic
class AttnSeed(SeedDelta):
    # Explicit single-head attention over the 8x8 spatial tokens — no SDPA
    # (spec: keep the arithmetic visible and deterministic).
    def __init__(self, channels: int) -> None:
        super().__init__()
        d = 16
        self.scale = d**-0.5
        self.ln = nn.LayerNorm(channels)
        self.q = nn.Linear(channels, d)
        self.k = nn.Linear(channels, d)
        self.v = nn.Linear(channels, d)
        self.out = nn.Linear(d, channels)

    def f(self, h: torch.Tensor) -> torch.Tensor:
        b, c, hh, ww = h.shape
        x = h.flatten(2).transpose(1, 2)  # [B, HW, C]
        x = self.ln(x)
        q, k, v = self.q(x), self.k(x), self.v(x)
        attn = torch.softmax(q @ k.transpose(1, 2) * self.scale, dim=-1)
        y = self.out(attn @ v)  # [B, HW, C]
        return cast(torch.Tensor, y.transpose(1, 2).reshape(b, c, hh, ww))


@semantic
class ConvLightSeed(SeedDelta):
    def __init__(self, channels: int) -> None:
        super().__init__()
        mid = 64  # mid=16/32 would fail the budget floor (2,657 / 4,737 params)
        self.body = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1, groups=channels, bias=False),
            nn.Conv2d(channels, mid, 1, bias=False),
            nn.BatchNorm2d(mid),
            nn.ReLU(),
            nn.Conv2d(mid, channels, 1, bias=False),
        )

    def f(self, h: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.body(h))


@semantic
class ConvHeavySeed(SeedDelta):
    def __init__(self, channels: int) -> None:
        super().__init__()
        cb = 52  # bottleneck; valid band [31, 77]
        self.body = nn.Sequential(
            nn.Conv2d(channels, cb, 3, padding=1, bias=False),
            nn.BatchNorm2d(cb),
            nn.ReLU(),
            nn.Conv2d(cb, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),  # standard init: final BN gamma = 1
        )

    def f(self, h: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.body(h))


@semantic
def build_seed(name: str, channels: int, init_seed: int) -> SeedDelta:
    classes: dict[str, Callable[[int], SeedDelta]] = {
        "norm": NormSeed,
        "attn": AttnSeed,
        "conv_light": ConvLightSeed,
        "conv_heavy": ConvHeavySeed,
    }
    if name not in classes:
        raise ValueError(f"unknown seed: {name}")
    with rng_scope(make_generator(init_seed)):
        return classes[name](channels)


@semantic
def tau_init(seed: SeedDelta, host_feats: torch.Tensor, cfg: Config) -> float:
    # D11: calibrate in train() mode — the mode of the first TRAINING step. Seed
    # BN buffers mutated by the fixed measurement batch are deterministic birth
    # state. The caller supplies host_feats from host.forward_to_slot under
    # host.eval()/no_grad (host BN protection).
    seed.train()
    with torch.no_grad():
        f0 = seed.f(host_feats)
        rms_h = float(host_feats.pow(2).mean().sqrt())
        rms_f0 = float(f0.pow(2).mean().sqrt())
        g = cfg.tau * rms_h / max(rms_f0, cfg.tau_eps)
        seed.gain.fill_(g)
    return g


@semantic
def split_decay_groups(
    module: nn.Module,
) -> tuple[list[tuple[str, torch.Tensor]], list[tuple[str, torch.Tensor]]]:
    # ndim <= 1 catches biases and all norm affines even under nn.Sequential's
    # integer names (where substring rules silently mis-file BN affines);
    # endswith("gain") catches the tau-carrying scalar explicitly.
    decay: list[tuple[str, torch.Tensor]] = []
    no_decay: list[tuple[str, torch.Tensor]] = []
    for name, param in module.named_parameters():
        if param.ndim <= 1 or name.endswith("gain"):
            no_decay.append((name, param))
        else:
            decay.append((name, param))
    return decay, no_decay


# section 6 — SLOT LIFECYCLE
@semantic
class Stage(enum.Enum):
    DORMANT = "dormant"
    GERMINATED = "germinated"  # zero-duration (D12): germinate() sets TRAINING directly
    TRAINING = "training"
    BLENDING = "blending"
    FOSSILIZING = "fossilizing"
    FOSSILIZED = "fossilized"


@semantic
def cosine_ease(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return 0.5 * (1.0 - math.cos(math.pi * p))


@semantic
class Slot(nn.Module):
    # alpha gates forward contribution, beta gates gradient coupling; both are
    # harness schedules (spec FSM). Transitions happen once per epoch
    # (epoch_tick); the per-step ramps advance in step_tick.
    def __init__(self) -> None:
        super().__init__()
        self.stage = Stage.DORMANT
        self.seed: SeedDelta | None = None
        self.alpha = 0.0
        self.beta = 0.0
        self.last_delta: torch.Tensor | None = None
        self.last_h: torch.Tensor | None = None
        # Appended once per epoch_tick (epoch-end values); the data source for
        # the report's alpha/beta trajectory plot (carried into ArmResult).
        self.alpha_beta_log: list[tuple[float, float]] = []
        # Sampled by step_tick at the first BLENDING step (gate 5's only input);
        # rms_ratio() is the named owner of the measurement, this is its capture.
        self.rms_ratio_blend_entry: float | None = None
        self._blend_step = 0
        self._fossil_step = 0
        self._epochs_in_stage = 0

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        if self.stage in (Stage.DORMANT, Stage.GERMINATED) or self.seed is None:
            return h
        # hin is VALUE-equal to h for every beta, but bitwise-equal only at
        # beta in {0, 1}; FOSSILIZING's fractional beta is a numerically-close,
        # non-bitwise blend by design (post-TRAINING, outside every bitwise
        # assertion window).
        hin = h.detach() * (1.0 - self.beta) + h * self.beta
        delta = cast(torch.Tensor, self.seed(hin))
        self.last_delta = delta
        self.last_h = h
        if self.stage is Stage.TRAINING:
            return h + (delta - delta.detach())  # STE: forward value == h
        return h + self.alpha * delta

    def trust_region_loss(self, cfg: Config) -> torch.Tensor:
        # lam = 1.0 sits inside the stability bound lam < 1/seed_lr ~= 20;
        # stationary point Delta* = -(dL/dDelta) * ||h||^2 / (2 lam).
        if self.stage is not Stage.TRAINING or self.last_delta is None or self.last_h is None:
            return torch.zeros(())
        return cfg.lam * self.last_delta.pow(2).mean() / self.last_h.detach().pow(2).mean().clamp_min(1e-12)

    def rms_ratio(self) -> float:
        # The named owner of ArmResult.rms_ratio_blend_entry, read by the fan
        # executor at the first BLENDING step (gate 5's only input).
        if self.last_delta is None or self.last_h is None:
            raise RuntimeError("rms_ratio before any armed forward")
        rms_d = self.last_delta.detach().pow(2).mean().sqrt()
        rms_h = self.last_h.detach().pow(2).mean().sqrt().clamp_min(1e-12)
        return float(rms_d / rms_h)

    def step_tick(self, cfg: Config, steps_per_epoch: int) -> None:
        # Called once per optimizer step, after opt.step().
        if self.seed is None:
            return
        if self.stage is Stage.BLENDING:
            if self._blend_step == 0:
                self.rms_ratio_blend_entry = self.rms_ratio()
            total = cfg.stage_m * steps_per_epoch
            self.alpha = cosine_ease((self._blend_step + 1) / total)
            self._blend_step += 1
        elif self.stage is Stage.FOSSILIZING:
            total = cfg.stage_f * steps_per_epoch
            self.beta = cosine_ease((self._fossil_step + 1) / total)
            self._fossil_step += 1

    def epoch_tick(self, cfg: Config) -> None:
        if self.stage is Stage.DORMANT or self.seed is None:
            return
        self._epochs_in_stage += 1
        if self.stage is Stage.TRAINING and self._epochs_in_stage >= cfg.stage_k:
            self.stage = Stage.BLENDING
            self._epochs_in_stage = 0
            self._blend_step = 0
        elif self.stage is Stage.BLENDING and self._epochs_in_stage >= cfg.stage_m:
            self.stage = Stage.FOSSILIZING
            self._epochs_in_stage = 0
            self._fossil_step = 0
            self.alpha = 1.0
        elif self.stage is Stage.FOSSILIZING and self._epochs_in_stage >= cfg.stage_f:
            self.stage = Stage.FOSSILIZED
            self.alpha = 1.0
            self.beta = 1.0
        self.alpha_beta_log.append((self.alpha, self.beta))


@semantic
def build_optimizer(host: Host, cfg: Config) -> torch.optim.SGD:
    # Constant LR is load-bearing twice: no scheduler state in snapshots, and
    # lr_scheduler captures base_lrs positionally at construction so a group
    # appended at germination would mismatch — constant LR removes the class
    # structurally.
    decay, no_decay = split_decay_groups(host)
    return torch.optim.SGD(
        [
            {"params": [p for _, p in decay], "weight_decay": cfg.wd},
            {"params": [p for _, p in no_decay], "weight_decay": 0.0},
        ],
        lr=cfg.lr,
        momentum=cfg.momentum,
        nesterov=True,
    )


@semantic
def append_seed_group(opt: torch.optim.SGD, seed: SeedDelta, cfg: Config) -> None:
    # Two groups (decay/no-decay) at cfg.seed_lr, fresh momentum.
    decay, no_decay = split_decay_groups(seed)
    opt.add_param_group({"params": [p for _, p in decay], "lr": cfg.seed_lr, "weight_decay": cfg.wd})
    opt.add_param_group({"params": [p for _, p in no_decay], "lr": cfg.seed_lr, "weight_decay": 0.0})


# section 7 — DETERMINISM (Class 1)
FORBIDDEN_RELAXATIONS: tuple[str, ...] = (
    # Spec list (each voids the Class 1 claim and the headline) + D10.
    # Documentation-only (printed by --selftest): deliberately NOT a
    # semantic_const — see the semantic_const comment above.
    "disabling the twin arm",
    "disabling deterministic algorithms",
    "enabling TF32",
    "enabling cudnn.benchmark",
    "enabling AMP",
    "adding gradient clipping",
    "adding dropout",
    "running fans across devices",
    "torch.compile (D10: compiled kernels void deterministic-algorithm guarantees)",
)


@semantic
def enable_class1() -> None:
    # MUST be the first statement of every process (main() and every worker).
    val = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if val is None:
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    elif val != ":4096:8":
        # A tolerated stray value is a silent Class-1 relaxation.
        raise RuntimeError(f"CUBLAS_WORKSPACE_CONFIG={val!r} (expected unset or ':4096:8')")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


@semantic
def state_hash(module: nn.Module) -> str:
    # Zero-normalized (D8): -0.0 and +0.0 hash identically; a signed zero is a
    # value-identical state that must not fail the bitwise-identity assertions.
    h = hashlib.sha256()
    sd = module.state_dict()
    for name in sorted(sd):
        v = sd[name].detach().cpu().contiguous()
        v = torch.where(v == 0, torch.zeros_like(v), v)
        arr = v.numpy().tobytes()
        h.update(name.encode())
        h.update(len(arr).to_bytes(8, "big"))
        h.update(arr)
    return h.hexdigest()


# Rebinds Task 4's standalone version (retired) to the zero-normalized hash;
# stays on the semantic surface by identity with state_hash.
host_init_hash = state_hash

REPLAY_REFUSAL_KEYS = semantic_const(
    "REPLAY_REFUSAL_KEYS",
    (
        # worker_count/device_index are provenance-only: the composition of
        # worker_count-in-key + single-worker replay was a proven deadlock.
        "torch_version",
        "cuda_version",
        "cudnn_version",
        "python_version",
        "gpu_name",
        "tf32_matmul",
        "tf32_cudnn",
    ),
)


@semantic
def env_block(device: str, worker_count: int) -> dict[str, object]:
    dev = torch.device(device)
    is_cuda = dev.type == "cuda"
    return {
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),  # type: ignore[no-untyped-call]
        "python_version": platform.python_version(),
        "gpu_name": torch.cuda.get_device_name(dev) if is_cuda else "cpu",
        "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
        "tf32_cudnn": torch.backends.cudnn.allow_tf32,
        # Provenance only, NOT a replay-refusal key: CPU GEMM reductions are
        # thread-count-dependent (policy training runs on CPU), so record it.
        "torch_num_threads": torch.get_num_threads(),
        "worker_count": worker_count,
        "device_index": dev.index,
    }


# section 8 — EPISODE
@semantic
def normalize_u8(x_u8: torch.Tensor) -> torch.Tensor:
    # Eval-path normalization: same mean/std as augment, no crop/flip.
    dev = x_u8.device
    xf = x_u8.to(torch.float32).div(255.0)
    return (xf - CIFAR_MEAN.to(dev)) / CIFAR_STD.to(dev)


@semantic
@dataclass
class EpisodeCtx:
    cfg: Config
    data: DataBundle
    device: str
    episode_seed: int
    pathology: str
    future: CommonFuture
    host: Host
    opt: torch.optim.SGD
    slot: Slot
    telemetry: list[TelemetryRecord]
    curves_val: list[float]
    curves_test: list[float] | None  # None iff read_test=False — one convention, no empty-list ambiguity
    read_test: bool


@semantic
def make_episode(cfg: Config, data: DataBundle, device: str, episode_seed: int, read_test: bool = False) -> EpisodeCtx:
    pathology = PATHOLOGIES[derive(episode_seed, "pathology") % 4]
    host = build_host(pathology, derive(episode_seed, "host-init")).to(device)
    host.attach_stat_hooks()
    future = CommonFuture.draw(derive(episode_seed, "future", 0), data.train_x.shape[0], cfg.horizon, cfg)
    slot = Slot().to(device)
    opt = build_optimizer(host, cfg)
    return EpisodeCtx(
        cfg=cfg,
        data=data,
        device=device,
        episode_seed=episode_seed,
        pathology=pathology,
        future=future,
        host=host,
        opt=opt,
        slot=slot,
        telemetry=[],
        curves_val=[],
        curves_test=[] if read_test else None,
        read_test=read_test,
    )


@semantic
def evaluate_acc(host: Host, slot: Slot, x: torch.Tensor, y: torch.Tensor, device: str, chunk: int) -> float:
    prior_h, prior_s = host.training, slot.training
    host.eval()
    slot.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, x.shape[0], chunk):
            xb = normalize_u8(x[i : i + chunk].to(device))
            yb = y[i : i + chunk].to(device)
            logits = host(xb, slot)
            correct += int((logits.argmax(1) == yb).sum())
    host.train(prior_h)
    slot.train(prior_s)
    return correct / x.shape[0]


@semantic
def train_one_epoch(ctx: EpisodeCtx, epoch: int) -> None:
    cfg = ctx.cfg
    order = ctx.future.order[epoch].reshape(-1, cfg.batch_size)
    steps_per_epoch = order.shape[0]
    ctx.host.train()
    ctx.slot.train()
    ce_sum = 0.0
    sat_sum = [0.0, 0.0, 0.0]
    step_grad_norms: tuple[list[float], list[float], list[float]] = ([], [], [])
    for s in range(steps_per_epoch):
        idx = order[s]
        x = augment(ctx.data.train_x[idx], ctx.future.crops[epoch, s], ctx.future.flips[epoch, s])
        y = ctx.data.train_y[idx]
        logits = ctx.host(x, ctx.slot)
        ce = torch.nn.functional.cross_entropy(logits, y)
        loss = ce + ctx.slot.trust_region_loss(cfg)  # trust term self-gates on TRAINING
        ctx.opt.zero_grad(set_to_none=True)
        loss.backward()  # type: ignore[no-untyped-call]
        for i, stage in enumerate(ctx.host.stage_modules()):
            sq = 0.0
            for p in stage.parameters():
                if p.grad is not None:
                    sq += float(p.grad.pow(2).sum())
            step_grad_norms[i].append(sq**0.5)
        ctx.opt.step()
        ctx.slot.step_tick(cfg, steps_per_epoch)
        ce_sum += float(ce.detach())
        sat = ctx.host.stage_stats["saturation"]  # KeyError = hooks never attached — loud, never silent zeros
        for i in range(3):
            sat_sum[i] += sat[i]
    ctx.slot.epoch_tick(cfg)
    train_loss = ce_sum / steps_per_epoch
    # val eval under no_grad (full per-class stats need the full logits)
    prior = ctx.host.training
    ctx.host.eval()
    ctx.slot.eval()
    with torch.no_grad():
        chunks = []
        loss_sum = 0.0
        for i in range(0, ctx.data.val_x.shape[0], cfg.eval_chunk):
            xb = normalize_u8(ctx.data.val_x[i : i + cfg.eval_chunk])
            yb = ctx.data.val_y[i : i + cfg.eval_chunk]
            lg = ctx.host(xb, ctx.slot)
            loss_sum += float(torch.nn.functional.cross_entropy(lg, yb, reduction="sum"))
            chunks.append(lg)
        val_logits = torch.cat(chunks)
        val_loss = loss_sum / ctx.data.val_y.shape[0]
        val_acc = float((val_logits.argmax(1) == ctx.data.val_y).float().mean())
        std, ent = confusion_stats(val_logits, ctx.data.val_y)
    ctx.host.train(prior)
    ctx.slot.train(prior)

    def _mean_var(norms: list[float]) -> tuple[float, float]:
        t = torch.tensor(norms, dtype=torch.float64)
        return float(t.mean()), float(t.var(unbiased=False))

    gm0, gv0 = _mean_var(step_grad_norms[0])
    gm1, gv1 = _mean_var(step_grad_norms[1])
    gm2, gv2 = _mean_var(step_grad_norms[2])
    weight_norm = tuple(float(sum(float(p.detach().pow(2).sum()) for p in stage.parameters()) ** 0.5) for stage in ctx.host.stage_modules())
    prev = ctx.telemetry[-1] if ctx.telemetry else None
    record = build_record(
        epoch=epoch,
        train_loss=train_loss,
        val_loss=val_loss,
        val_acc=val_acc,
        train_loss_delta=train_loss - prev.train_loss if prev else 0.0,
        val_loss_delta=val_loss - prev.val_loss if prev else 0.0,
        grad_norm_mean=(gm0, gm1, gm2),
        grad_norm_var=(gv0, gv1, gv2),
        act_saturation=(sat_sum[0] / steps_per_epoch, sat_sum[1] / steps_per_epoch, sat_sum[2] / steps_per_epoch),
        weight_norm=(weight_norm[0], weight_norm[1], weight_norm[2]),
        per_class_val_acc_std=std,
        confusion_entropy=ent,
    )  # a TelemetryDivergence propagates to the caller — Task 9 owns the divergence conventions
    ctx.telemetry.append(record)
    ctx.curves_val.append(val_acc)
    if ctx.read_test:
        assert ctx.curves_test is not None
        ctx.curves_test.append(evaluate_acc(ctx.host, ctx.slot, ctx.data.test_x, ctx.data.test_y, ctx.device, cfg.eval_chunk))


@semantic
@dataclass
class Snapshot:
    # opt_state is ALWAYS the 2-group never-germinated base state — snapshots
    # are taken only on the base path; Task 9's arm-local materialization is
    # what makes this sufficient. There is no restore_snapshot: arms are built
    # fresh from snapshot values.
    host_state: dict[str, torch.Tensor]
    opt_state: dict[str, object]
    cpu_rng: torch.Tensor
    cuda_rng: torch.Tensor | None
    epoch: int


@semantic
def take_snapshot(ctx: EpisodeCtx) -> Snapshot:
    dev = torch.device(ctx.device)
    return Snapshot(
        host_state={k: v.detach().clone() for k, v in ctx.host.state_dict().items()},
        opt_state=copy.deepcopy(ctx.opt.state_dict()),
        cpu_rng=torch.get_rng_state(),
        cuda_rng=torch.cuda.get_rng_state(dev) if dev.type == "cuda" else None,
        epoch=len(ctx.telemetry),
    )


@semantic
def germinate(ctx: EpisodeCtx, seed_name: str) -> float:
    cfg = ctx.cfg
    if ctx.slot.stage is not Stage.DORMANT:
        # Defense-in-depth on the one sanctioned influence-raising path: a
        # second germination would append duplicate optimizer param groups
        # and orphan the prior seed silently.
        raise RuntimeError(f"germinate refused: slot is {ctx.slot.stage.name}, not DORMANT")
    seed = build_seed(seed_name, ctx.host.feat_channels, derive(ctx.episode_seed, "arm", seed_name)).to(ctx.device)
    prior = ctx.host.training
    ctx.host.eval()  # host BN protection (spec): tau-init must not touch host state
    with torch.no_grad():
        fixed_val_batch = normalize_u8(ctx.data.val_x[: cfg.batch_size])
        feats = ctx.host.forward_to_slot(fixed_val_batch)
    ctx.host.train(prior)
    g = tau_init(seed, feats, cfg)
    append_seed_group(ctx.opt, seed, cfg)
    ctx.slot.seed = seed
    ctx.slot.stage = Stage.TRAINING  # GERMINATED is zero-duration (D12)
    return g


@semantic
def end_state_R(curve: list[float]) -> float:  # noqa: N802 — spec names the reward R
    if len(curve) < 3:
        raise ValueError(f"end_state_R needs >= 3 entries, got {len(curve)}")
    return sum(curve[-3:]) / 3.0


# section 9 — FAN EXECUTOR
class TwinDivergence(RuntimeError):  # noqa: N818
    def __init__(self, first_bad_epoch: int) -> None:
        # Absolute epoch index in the episode's numbering, NOT an offset from
        # snap.epoch.
        super().__init__(f"twin diverged from base at epoch {first_bad_epoch}")
        self.first_bad_epoch = first_bad_epoch


_NON_SEMANTIC["TwinDivergence"] = "exception class — no computation depends on its definition"


@semantic
@dataclass
class ArmResult:
    name: str
    status: str  # "ok" | "diverged"
    r_val: float
    r_test: float | None
    curve_val: list[float]
    curve_test: list[float] | None
    init_seed: int
    g_at_init: float | None
    rms_ratio_blend_entry: float | None
    hash_after_training: str | None  # host hash at the end of the STE TRAINING stage (every arm)
    host_hashes: list[str] | None  # noop/nullseed arms only
    alpha_beta_log: list[tuple[float, float]] | None
    # --- spec rev 6.2 (pre-data, additive). Nothing in the frozen battery
    # reads any of these: no gate arithmetic and no verdict boolean moves.
    #
    # The POST-decision 20-dim trajectory of this arm — the host observed
    # while the graft integrates. curve_val already carries one scalar per
    # epoch; this carries the other nineteen (grad-norm mean/var, saturation,
    # weight norms, per-class spread, confusion entropy), which is what any
    # decision ABOUT AN ALREADY-GRAFTED HOST needs, and what makes divergence
    # diagnosable rather than merely counted.
    #
    # HARD RULE: the learner never reads this. fan_to_example consumes
    # FanRecord.telemetry (the PRE-decision base history) and arm scalars
    # only; arm telemetry on the training path is a time-travel channel that
    # would silently invalidate the headline. Enforced by --selftest's
    # learner_ignores_arm_telemetry step and by test_arm_recording.py.
    telemetry: list[dict[str, object]] | None
    # Cost accounting — the denominator the "supervision economics" claim
    # otherwise lacks. Provenance only: never a replay comparand (wall-clock
    # differs between record and replay by construction), never learner input.
    wall_s: float | None
    peak_mem_bytes: int | None  # CUDA only; None on CPU — absent, not zero
    # Influence at the horizon, beside rms_ratio_blend_entry's single sample
    # at BLENDING entry: does an embodied graft's influence grow, hold or
    # decay under joint training? Measured on the last forward of the run —
    # an eval-mode val/test batch, where blend entry samples a training batch.
    g_at_horizon: float | None
    rms_ratio_horizon: float | None


@semantic
@dataclass
class BaseTrace:
    host_hashes: list[str]
    curve_val: list[float]
    curve_test: list[float] | None
    snapshots: dict[int, Snapshot]  # captured at the scheduled fan epochs during the single base pass
    status: str
    diverged_at: int | None


@semantic
def _run_span(
    ctx: EpisodeCtx,
    start: int,
    fan_epochs: tuple[int, ...] = (),
    snapshots: dict[int, Snapshot] | None = None,
    hash_capture_epoch: int | None = None,
) -> tuple[list[str], str, int | None, str | None]:
    # THE inner loop — run_base and run_arm both call this (one loop, two call
    # sites: base/twin drift is structurally impossible). Snapshots are taken
    # BEFORE the fan epoch trains, so an arm running snap.epoch -> horizon
    # produces hashes aligned with base.host_hashes[snap.epoch:].
    hashes: list[str] = []
    status = "ok"
    diverged_at: int | None = None
    hash_after_training: str | None = None
    for epoch in range(start, ctx.cfg.horizon):
        if snapshots is not None and epoch in fan_epochs:
            snapshots[epoch] = take_snapshot(ctx)
        try:
            train_one_epoch(ctx, epoch)
        except TelemetryDivergence:
            status = "diverged"
            diverged_at = epoch
            break
        h = state_hash(ctx.host)
        hashes.append(h)
        if epoch == hash_capture_epoch:
            hash_after_training = h
    return hashes, status, diverged_at, hash_after_training


@semantic
def run_base(ctx: EpisodeCtx, cfg: Config, fan_epochs: tuple[int, ...]) -> BaseTrace:
    # Base divergence: status recorded, hashes kept to the divergence epoch,
    # fans scheduled after it are skipped (snapshot point never reached);
    # r_noop = cfg.diverged_r is applied by the caller.
    snapshots: dict[int, Snapshot] = {}
    hashes, status, diverged_at, _ = _run_span(ctx, 0, fan_epochs, snapshots)
    return BaseTrace(
        host_hashes=hashes,
        curve_val=ctx.curves_val,
        curve_test=ctx.curves_test,
        snapshots=snapshots,
        status=status,
        diverged_at=diverged_at,
    )


@semantic
def run_arm(
    cfg: Config,
    data: DataBundle,
    device: str,
    episode_seed: int,
    pathology: str,
    future: CommonFuture,
    snap: Snapshot,
    arm_name: str,
    read_test: bool,
    delta_dir: Path | None = None,
) -> ArmResult:
    # Arm-local materialization: everything is built fresh from snapshot
    # values; nothing is restored in place, so no state leaks between arms.
    host = build_host(pathology, derive(episode_seed, "host-init")).to(device)
    host.attach_stat_hooks()
    host.load_state_dict(snap.host_state)
    slot = Slot().to(device)
    opt = build_optimizer(host, cfg)
    # Loaded on a fresh 2-group optimizer BEFORE any append_seed_group, so
    # load_state_dict's unconditional group-count check can never fire. The
    # deepcopy keeps snap immune to in-place momentum-buffer updates.
    opt.load_state_dict(copy.deepcopy(snap.opt_state))
    torch.set_rng_state(snap.cpu_rng)
    if snap.cuda_rng is not None:
        torch.cuda.set_rng_state(snap.cuda_rng, torch.device(device))
    ctx = EpisodeCtx(
        cfg=cfg,
        data=data,
        device=device,
        episode_seed=episode_seed,
        pathology=pathology,
        future=future,
        host=host,
        opt=opt,
        slot=slot,
        telemetry=[],
        curves_val=[],
        curves_test=[] if read_test else None,
        read_test=read_test,
    )
    g_at_init: float | None = None
    if arm_name in SEED_NAMES:
        g_at_init = germinate(ctx, arm_name)
    elif arm_name == "nullseed":
        germinate(ctx, "conv_light")
        assert slot.seed is not None
        # germinate tau-inits the gain NONZERO — the explicit zeroing is the
        # step an implementer would otherwise miss. The null-seed arm proves
        # the machinery: germinated, trained, bitwise-identical host.
        slot.seed.gain.data.zero_()
        slot.seed.gain.requires_grad_(False)
        g_at_init = 0.0
    elif arm_name != "noop":
        raise ValueError(f"unknown arm: {arm_name}")
    dev = torch.device(device)
    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats(dev)  # arms run SEQUENTIALLY within a fan, so the peak is this arm's
    t0 = time.perf_counter()
    hashes, status, _, hash_after_training = _run_span(ctx, snap.epoch, hash_capture_epoch=snap.epoch + cfg.stage_k - 1)
    wall_s = time.perf_counter() - t0
    peak_mem = int(torch.cuda.max_memory_allocated(dev)) if dev.type == "cuda" else None
    if status == "ok":
        r_val = end_state_R(ctx.curves_val)
        r_test = end_state_R(ctx.curves_test) if ctx.curves_test is not None else None
    else:
        r_val = cfg.diverged_r
        r_test = cfg.diverged_r if read_test else None
    keep_hashes = arm_name in ("noop", "nullseed")
    # Horizon influence: last_delta/last_h are set by every armed forward, so
    # after the run they hold the final eval-mode batch. Guarded rather than
    # assumed — an arm with no seed owes no measurement.
    g_at_horizon: float | None = None
    rms_ratio_horizon: float | None = None
    if slot.seed is not None:
        g_at_horizon = float(slot.seed.gain.detach())
        if slot.last_delta is not None and slot.last_h is not None:
            rms_ratio_horizon = slot.rms_ratio()
        # The trained Delta module: the only artefact of this campaign that is
        # an actual generated structure, and the corpus early Momir needs.
        # Written to a fan_id-keyed SIDECAR, never into the JSONL — so
        # Store.merge()'s decode/sort/duplicate path is untouched.
        if delta_dir is not None:
            delta_dir.mkdir(parents=True, exist_ok=True)
            path = delta_dir / f"{arm_name}.pt"
            tmp = path.with_suffix(".pt.tmp")
            torch.save({k: v.detach().cpu() for k, v in slot.seed.state_dict().items()}, tmp)
            os.replace(tmp, path)  # atomic
    return ArmResult(
        name=arm_name,
        status=status,
        r_val=r_val,
        r_test=r_test,
        curve_val=ctx.curves_val,
        curve_test=ctx.curves_test,
        # Provenance must name the stream actually drawn from: the nullseed
        # arm germinates a conv_light module (gain zeroed afterwards), so its
        # init came from conv_light's generator, not a "nullseed" stream.
        init_seed=derive(episode_seed, "arm", "conv_light" if arm_name == "nullseed" else arm_name),
        g_at_init=g_at_init,
        rms_ratio_blend_entry=slot.rms_ratio_blend_entry,
        hash_after_training=hash_after_training,
        host_hashes=hashes if keep_hashes else None,
        alpha_beta_log=slot.alpha_beta_log if slot.seed is not None else None,
        telemetry=[dataclasses.asdict(t) for t in ctx.telemetry],
        wall_s=wall_s,
        peak_mem_bytes=peak_mem,
        g_at_horizon=g_at_horizon,
        rms_ratio_horizon=rms_ratio_horizon,
    )


@semantic
def run_fan(
    cfg: Config,
    data: DataBundle,
    device: str,
    episode_seed: int,
    pathology: str,
    future: CommonFuture,
    snap: Snapshot,
    base: BaseTrace,
    read_test: bool,
    include_nullseed: bool = False,
    delta_dir: Path | None = None,
) -> tuple[list[ArmResult], dict[str, object]]:
    # Twin FIRST: it is the harness-integrity check; a broken twin fails the
    # fan before any seed arm spends compute.
    twin = run_arm(cfg, data, device, episode_seed, pathology, future, snap, "noop", read_test)
    expected = base.host_hashes[snap.epoch :]
    twin_hashes = twin.host_hashes or []
    for i in range(min(len(twin_hashes), len(expected))):
        if twin_hashes[i] != expected[i]:
            raise TwinDivergence(snap.epoch + i)
    if len(twin_hashes) != len(expected):
        raise TwinDivergence(snap.epoch + min(len(twin_hashes), len(expected)))
    meta: dict[str, object] = {"twin_ok": True}
    arms: list[ArmResult] = [twin]
    for name in SEED_NAMES:
        arms.append(run_arm(cfg, data, device, episode_seed, pathology, future, snap, name, read_test, delta_dir=delta_dir))
    # Cross-arm value-exactness: through the STE TRAINING stage every finite
    # arm's host is bitwise-identical to the twin's (non-finite delta shows up
    # as arm divergence, not a harness abort).
    k_idx = cfg.stage_k - 1
    twin_hash_at = twin_hashes[k_idx] if 0 <= k_idx < len(twin_hashes) else None
    for a in arms:
        if a.status == "ok" and a.hash_after_training is not None and twin_hash_at is not None:
            assert a.hash_after_training == twin_hash_at, (a.name, "post-TRAINING host hash mismatch vs twin")
    if include_nullseed:
        ns = run_arm(cfg, data, device, episode_seed, pathology, future, snap, "nullseed", read_test)
        arms.append(ns)
        # HARD STOP, unconditionally: delta==0 must reproduce the base
        # bitwise — INCLUDING mirroring a base divergence at the same epoch.
        # The zero-normalized hash IS the spec's value-exact check; there is
        # no weaker fallback, curves are never a comparand, and a diverged
        # nullseed must never be downgraded to an ordinary diverged-arm
        # record (the harness-integrity instrument reporting a result).
        if ns.status != twin.status or (ns.host_hashes or []) != expected:
            raise RuntimeError(
                "null-seed mismatch vs base while the twin holds — value-exactness broken "
                f"(nullseed status={ns.status!r}, twin status={twin.status!r})"
            )
        meta["nullseed_ok"] = True
    return arms, meta


# section 10 — RECORDS AND STORE
class SplitViolation(RuntimeError):  # noqa: N818
    pass


_NON_SEMANTIC["SplitViolation"] = "exception class — no computation depends on its definition"

RECORD_KINDS = ("fan", "refan", "policy_run", "preflight_iter", "extension_event", "void_event")
SEED_NAMESPACES = ("dev", "preflight", "train", "eval")
SPLIT_ROLES = ("preflight", "train", "tune", "eval")


@semantic
@dataclass
class FanRecord:
    schema_version: int
    kind: str
    episode_seed: int
    seed_namespace: str
    split_role: str
    pathology_id: str
    fan_epoch: int | None
    refan_k: int | None
    schedule_id: str
    policy_checkpoint_id: str | None
    iteration: int | None
    config_hash: str
    frozen_block_hash: str
    manifest_hash: str | None  # None pre-freeze
    common_future_hash: str
    host_init_hash: str
    env: dict[str, object]
    arms: list[dict[str, object]]
    telemetry: list[dict[str, object]]
    decisions: list[dict[str, object]] | None  # policy_run payload
    gate_results: dict[str, object] | None  # preflight_iter payload
    fan_id: str


@semantic
def fan_identity(
    episode_seed: int,
    fan_epoch: int | None,
    kind: str,
    refan_k: int | None,
    policy_checkpoint_id: str | None,
    iteration: int | None,
) -> str:
    # The FULL identity tuple — resume/idempotency skip-sets key on this.
    ident = json.dumps([episode_seed, fan_epoch, kind, refan_k, policy_checkpoint_id, iteration])
    return hashlib.sha256(ident.encode()).hexdigest()


@semantic
def make_fan_record(
    *,
    kind: str,
    episode_seed: int,
    seed_namespace: str,
    split_role: str,
    pathology_id: str,
    fan_epoch: int | None,
    refan_k: int | None,
    schedule_id: str,
    policy_checkpoint_id: str | None,
    iteration: int | None,
    config_hash: str,
    frozen_block_hash: str,
    manifest_hash: str | None,
    common_future_hash: str,
    host_init_hash: str,
    env: dict[str, object],
    arms: list[dict[str, object]],
    telemetry: list[dict[str, object]],
    decisions: list[dict[str, object]] | None,
    gate_results: dict[str, object] | None,
) -> FanRecord:
    # The sole constructor tests and production use. fan_id is derived from
    # the FULL identity tuple — comparator runs and preflight iterations are
    # distinct identities. iteration and policy_checkpoint_id must come from
    # store state / content identity, never wall-clock or process-local
    # counters, so a resumed run reconstructs identical fan_ids.
    if kind not in RECORD_KINDS:
        raise ValueError(f"unknown record kind: {kind}")
    if seed_namespace not in SEED_NAMESPACES:
        raise ValueError(f"unknown seed_namespace: {seed_namespace}")
    if split_role not in SPLIT_ROLES:
        raise ValueError(f"unknown split_role: {split_role}")
    return FanRecord(
        schema_version=SCHEMA_VERSION,
        kind=kind,
        episode_seed=episode_seed,
        seed_namespace=seed_namespace,
        split_role=split_role,
        pathology_id=pathology_id,
        fan_epoch=fan_epoch,
        refan_k=refan_k,
        schedule_id=schedule_id,
        policy_checkpoint_id=policy_checkpoint_id,
        iteration=iteration,
        config_hash=config_hash,
        frozen_block_hash=frozen_block_hash,
        manifest_hash=manifest_hash,
        common_future_hash=common_future_hash,
        host_init_hash=host_init_hash,
        env=env,
        arms=arms,
        telemetry=telemetry,
        decisions=decisions,
        gate_results=gate_results,
        fan_id=fan_identity(episode_seed, fan_epoch, kind, refan_k, policy_checkpoint_id, iteration),
    )


@semantic
def make_schedule_id(cfg: Config) -> str:
    s = f"uniform-no-replacement|{cfg.window!r}|{cfg.fans_per_episode}"
    return hashlib.sha256(s.encode()).hexdigest()


@semantic
def train_tune_split(episode_seed: int) -> str:
    # Decided at COLLECTION time, recorded per episode, never re-split
    # downstream.
    return "tune" if derive(episode_seed, "tune-split") % 5 == 0 else "train"


@semantic
def _sanitize_json(v: object) -> object:
    # Non-finite -> null recursively; tuples -> lists (consumers take
    # dicts/lists).
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, (list, tuple)):
        return [_sanitize_json(x) for x in v]
    if isinstance(v, dict):
        return {k: _sanitize_json(val) for k, val in v.items()}
    return v


@semantic
def encode_record(r: FanRecord) -> str:
    return json.dumps(_sanitize_json(dataclasses.asdict(r)))


@semantic
def decode_record(line: str) -> FanRecord:
    data = json.loads(line)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"schema_version {data.get('schema_version')!r} != {SCHEMA_VERSION}: refusing to decode. "
            "Post-collection schema changes are ADDITIVE-ONLY (the decoder fills absent new fields with "
            "None); a non-additive bump pre-collection wipes scratch stores; a non-additive bump "
            "post-collection is an owner decision (re-collect vs. translate), never silent."
        )
    kwargs = {f.name: data.get(f.name) for f in dataclasses.fields(FanRecord)}
    return FanRecord(**kwargs)


@semantic
class Store:
    def __init__(self, root: str | os.PathLike[str], fsync_every: int = 20) -> None:
        self.root = Path(root)
        (self.root / "shards").mkdir(parents=True, exist_ok=True)
        self.fsync_every = fsync_every
        self._handles: dict[int, TextIO] = {}
        self._counts: dict[int, int] = {}

    def shard_path(self, worker_id: int) -> Path:
        return self.root / "shards" / f"worker_{worker_id}.jsonl"

    def append(self, worker_id: int, record: FanRecord) -> None:
        # Durability target: host-level failure loses <= fsync_every records,
        # process crash loses none (flush on every append).
        fh = self._handles.get(worker_id)
        if fh is None:
            fh = open(self.shard_path(worker_id), "a", encoding="utf-8")  # noqa: SIM115 — long-lived shard handle, closed in close()
            self._handles[worker_id] = fh
            self._counts[worker_id] = 0
        fh.write(encode_record(record) + "\n")
        fh.flush()
        self._counts[worker_id] += 1
        if self._counts[worker_id] % self.fsync_every == 0:
            os.fsync(fh.fileno())

    def close(self) -> None:
        for fh in self._handles.values():
            fh.flush()
            os.fsync(fh.fileno())
            fh.close()
        self._handles.clear()
        self._counts.clear()

    def merge(self) -> list[FanRecord]:
        records: list[FanRecord] = []
        for p in sorted((self.root / "shards").glob("worker_*.jsonl")):
            with open(p, encoding="utf-8") as fh:
                lines = [ln for ln in fh if ln.strip()]
            for i, line in enumerate(lines):
                try:
                    records.append(decode_record(line))
                except json.JSONDecodeError:
                    if i == len(lines) - 1:
                        # Torn FINAL line = host crash mid-append; the record
                        # was never durable (this is the "loses <= fsync_every
                        # records" contract, not corruption). Skip LOUDLY so
                        # the store stays readable. A torn interior line is
                        # corruption and still raises.
                        print(f"WARNING: skipping torn final line of {p} (host crash mid-append)", flush=True)
                        continue
                    raise
        # Duplication backstop: fan/refan identities must be unique within one
        # manifest_hash generation; event/policy_run/preflight kinds are exempt
        # from the collision assert but still carry unique ids.
        seen: set[tuple[str | None, str]] = set()
        for r in records:
            if r.kind in ("fan", "refan"):
                key = (r.manifest_hash, r.fan_id)
                if key in seen:
                    raise ValueError(f"duplicate fan_id {r.fan_id} (manifest {r.manifest_hash!r})")
                seen.add(key)
        # None coalesces to -1 so event records (fan_epoch=None) sort before
        # that episode's fans instead of raising TypeError. The trailing
        # discriminators (checkpoint, iteration, fan_id) make merged order
        # canonical even for kinds the leading key cannot separate (an
        # episode's 4 policy_run comparators, repeated preflight_iters) —
        # shard-file/append order must never leak into consumers.
        records.sort(
            key=lambda r: (
                r.episode_seed,
                -1 if r.fan_epoch is None else r.fan_epoch,
                r.kind,
                -1 if r.refan_k is None else r.refan_k,
                r.policy_checkpoint_id or "",
                -1 if r.iteration is None else r.iteration,
                r.fan_id,
            )
        )
        return records

    def load(self, split_role: str, kinds: tuple[str, ...] = ("fan",)) -> list[FanRecord]:
        return [r for r in self.merge() if r.split_role == split_role and r.kind in kinds]


@semantic
def _assert_trainable(records: list[FanRecord]) -> None:
    for r in records:
        if r.split_role == "eval":
            raise SplitViolation(f"eval-split record {r.fan_id} on the training path")
        if r.kind != "fan":
            raise SplitViolation(f"kind={r.kind!r} record {r.fan_id} on the training path")


@semantic
def load_for_training(store: Store) -> list[FanRecord]:
    records = [r for r in store.merge() if r.split_role in ("train", "tune") and r.kind == "fan"]
    # The guard is on the yield path, not vacuously behind the filter.
    _assert_trainable(records)
    return records


# section 11 — POLICY
@semantic
class _PolicyBlock(nn.Module):
    # Hand-rolled: explicit-matmul single-head self-attention (attention dim =
    # d_model, no biases in projections, causal mask) + MLP ratio 4, pre-LN.
    def __init__(self, d: int) -> None:
        super().__init__()
        self.scale = d**-0.5
        self.ln1 = nn.LayerNorm(d)
        self.q = nn.Linear(d, d, bias=False)
        self.k = nn.Linear(d, d, bias=False)
        self.v = nn.Linear(d, d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, x: torch.Tensor, causal_mask: torch.Tensor) -> torch.Tensor:
        h = self.ln1(x)
        q, k, v = self.q(h), self.k(h), self.v(h)
        att = q @ k.transpose(1, 2) * self.scale
        att = att.masked_fill(causal_mask, float("-inf"))
        att = torch.softmax(att, dim=-1)
        x = x + self.proj(att @ v)
        x = x + self.mlp(self.ln2(x))
        return x


@semantic
class Policy(nn.Module):
    # now_head/seed_head are separate named submodules (test-addressable);
    # together they are the conceptual Linear(d_model, 5) head — [:, 0] NOW
    # logit, [:, 1:] seed logits — with identical arithmetic capacity.
    def __init__(self, cfg: Config, gen: torch.Generator) -> None:
        super().__init__()
        d = cfg.d_model
        with rng_scope(gen):
            self.embed = nn.Sequential(nn.Linear(TELEMETRY_DIM, d), nn.GELU(), nn.Linear(d, d))
            self.pos = nn.Parameter(torch.randn(cfg.horizon, d) * 0.02)
            self.blocks = nn.ModuleList([_PolicyBlock(d) for _ in range(cfg.n_layers)])
            self.ln_f = nn.LayerNorm(d)
            self.now_head = nn.Linear(d, 1)
            self.seed_head = nn.Linear(d, 4)

    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        b, t, _ = tokens.shape
        x = self.embed(tokens) + self.pos[:t]
        causal_mask = torch.triu(torch.ones(t, t, dtype=torch.bool, device=tokens.device), diagonal=1)
        for blk in self.blocks:
            x = blk(x, causal_mask)
        x = self.ln_f(x)
        h_last = x[torch.arange(b, device=tokens.device), (lengths - 1).to(tokens.device)]
        p_logit = cast(torch.Tensor, self.now_head(h_last)).squeeze(-1)
        seed_logits = cast(torch.Tensor, self.seed_head(h_last))
        return p_logit, seed_logits


@semantic
def schedule_only_mask(t: torch.Tensor) -> torch.Tensor:
    # Index the FEATURE axis ([..., EPOCH_FEATURE_IDX]) — correct on 1-D and
    # [B,T,D]; a dim-0 implementation zeroes the batch axis and silently
    # corrupts the schedule-only comparator.
    m = torch.zeros_like(t)
    m[..., EPOCH_FEATURE_IDX] = t[..., EPOCH_FEATURE_IDX]
    return m


@semantic
def _policy_tokens(policy: Policy, normalizer: Normalizer, telemetry: list[TelemetryRecord]) -> torch.Tensor:
    dev = next(policy.parameters()).device
    vecs = [normalizer.apply(record_to_vector(r)) for r in telemetry]
    return torch.stack(vecs).unsqueeze(0).to(dev)  # [1, T, TELEMETRY_DIM]


@semantic
def decide_live(
    policy: Policy,
    normalizer: Normalizer,
    telemetry: list[TelemetryRecord],
    epoch: int,
    cfg: Config,
    mask_fn: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> tuple[bool, str | None]:
    lo, hi = cfg.window
    if epoch < lo or epoch > hi:
        # Outside the trained decision window p is pure extrapolation.
        return (False, None)
    tokens = _policy_tokens(policy, normalizer, telemetry)  # normalize first...
    if mask_fn is not None:
        tokens = mask_fn(tokens)  # ...then mask (if any), then forward
    prior = policy.training
    policy.eval()
    with torch.no_grad():
        p_logit, seed_logits = policy(tokens, torch.tensor([tokens.shape[1]]))
    policy.train(prior)
    if not (torch.isfinite(p_logit).all() and torch.isfinite(seed_logits).all()):
        # NaN > 0.5 is False: a non-finite checkpoint would silently read as
        # "never germinate, lift 0" across every episode. Loud, never that.
        raise RuntimeError("decide_live: policy produced non-finite logits")
    if float(torch.sigmoid(p_logit[0])) > 0.5:  # deterministic — no sampling slot at eval
        logits = seed_logits[0]
        best = int((logits == logits.max()).nonzero()[0])  # deterministic tie-break: lowest index
        return (True, SEED_NAMES[best])
    return (False, None)


@semantic
def query_teacher_forced(
    policy: Policy, normalizer: Normalizer, telemetry_prefix: list[TelemetryRecord], cfg: Config
) -> tuple[float, dict[str, float]]:
    tokens = _policy_tokens(policy, normalizer, telemetry_prefix)
    prior = policy.training
    policy.eval()
    with torch.no_grad():
        p_logit, seed_logits = policy(tokens, torch.tensor([tokens.shape[1]]))
        p = float(torch.sigmoid(p_logit[0]))
        pi = torch.softmax(seed_logits[0], dim=-1)
    policy.train(prior)
    return p, {name: float(pi[i]) for i, name in enumerate(SEED_NAMES)}


# section 12 — LEARNING
@semantic
def _as_float(v: object) -> float:
    # Loud on None (a serialized non-finite) and on anything non-numeric —
    # never a silent default.
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"expected a number, got {v!r}")
    return float(v)


@semantic
def _telemetry_vector_from_dict(d: dict[str, object]) -> torch.Tensor:
    # Decoded-dict twin of record_to_vector — the field order MUST mirror it.
    def f(key: str) -> float:
        return _as_float(d[key])

    def f3(key: str) -> list[float]:
        v = d[key]
        if not isinstance(v, (list, tuple)) or len(v) != 3:
            raise ValueError(f"expected a 3-vector for {key}, got {v!r}")
        return [_as_float(x) for x in v]

    values = [
        f("epoch"),
        f("train_loss"),
        f("val_loss"),
        f("val_acc"),
        f("train_loss_delta"),
        f("val_loss_delta"),
        *f3("grad_norm_mean"),
        *f3("grad_norm_var"),
        *f3("act_saturation"),
        *f3("weight_norm"),
        f("per_class_val_acc_std"),
        f("confusion_entropy"),
    ]
    return torch.tensor(values, dtype=torch.float32)


@semantic
def fan_to_example(rec: FanRecord, normalizer: Normalizer) -> dict[str, object]:
    # Consumes decoded dicts/lists. r is in VAL units, SEED_NAMES order;
    # diverged arms already carry cfg.diverged_r (0.10) from run_arm.
    vecs = [normalizer.apply(_telemetry_vector_from_dict(d)) for d in rec.telemetry]
    tokens = torch.stack(vecs)
    by_name = {str(a["name"]): a for a in rec.arms}
    r = torch.tensor([_as_float(by_name[n]["r_val"]) for n in SEED_NAMES], dtype=torch.float32)
    return {
        "tokens": tokens,
        "length": tokens.shape[0],
        "r": r,
        "r_noop": _as_float(by_name["noop"]["r_val"]),
    }


@semantic
def measure_fan_density(records: list[FanRecord], unit: str = "val") -> dict[str, float]:
    if not records:
        raise ValueError("no fan records")
    key = {"val": "r_val", "test": "r_test"}[unit]
    best_minus_second: list[float] = []
    best_minus_noop: list[float] = []
    for rec in records:
        by_name = {str(a["name"]): a for a in rec.arms}
        rs = sorted((_as_float(by_name[n][key]) for n in SEED_NAMES), reverse=True)
        best_minus_second.append(rs[0] - rs[1])
        best_minus_noop.append(rs[0] - _as_float(by_name["noop"][key]))
    return {
        "best_minus_second": sum(best_minus_second) / len(best_minus_second),
        "best_minus_noop": sum(best_minus_noop) / len(best_minus_noop),
    }


@semantic
def warmup_schedule(step: int, total_steps: int, warmup_frac: float) -> bool:
    # False during warm-up (J_now disabled). Pure.
    return step >= round(total_steps * warmup_frac)


@semantic
def policy_loss(
    policy: Policy,
    batch: tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor],
    cfg: Config,
    *,
    beta_which: float,
    beta_now: float,
    enable_now: bool,
    mask_fn: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> torch.Tensor:
    # Takes BOTH temperatures explicitly — a single scalar cannot honor the
    # two-key mapping (beta_which from best_minus_second, beta_now from
    # best_minus_noop).
    tokens, lengths, r, r_noop = batch  # [B,T,20], [B], [B,4], [B]
    if mask_fn is not None:
        tokens = mask_fn(tokens)  # masks apply POST-normalization
    p_logit, seed_logits = cast(tuple[torch.Tensor, torch.Tensor], policy(tokens, lengths))
    pi = seed_logits.softmax(-1)
    j_which = (pi * r).sum(-1)
    ent_pi = -(pi * pi.clamp_min(1e-8).log()).sum(-1)
    loss = -(j_which + beta_which * ent_pi)
    if enable_now:
        p = torch.sigmoid(p_logit)
        adv_mix = (pi.detach() * r).sum(-1)  # sg[pi] — spec §Learning
        j_now = p * adv_mix + (1 - p) * r_noop
        ent_p = -(p * p.clamp_min(1e-8).log() + (1 - p) * (1 - p).clamp_min(1e-8).log())
        loss = loss - (j_now + beta_now * ent_p)
    return loss.mean()


@semantic
def _collate_examples(examples: list[dict[str, object]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    t_max = 0
    for e in examples:
        t_max = max(t_max, int(cast(int, e["length"])))
    tokens = torch.zeros(len(examples), t_max, TELEMETRY_DIM)
    lengths = torch.zeros(len(examples), dtype=torch.int64)
    for j, e in enumerate(examples):
        et = e["tokens"]
        assert isinstance(et, torch.Tensor)
        tokens[j, : et.shape[0]] = et
        lengths[j] = et.shape[0]
    r = torch.stack([cast(torch.Tensor, e["r"]) for e in examples])
    r_noop = torch.tensor([_as_float(e["r_noop"]) for e in examples])
    return tokens, lengths, r, r_noop


@semantic
def train_policy(
    records: list[FanRecord],
    cfg: Config,
    normalizer: Normalizer,
    gen: torch.Generator,
    *,
    frozen_density: dict[str, float],
    steps: int | None = None,
    mask_fn: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> tuple[Policy, dict[str, object]]:
    _assert_trainable(records)
    # Temperature mapping (pre-registered, recorded in the FreezeManifest);
    # betas come from frozen_density, NEVER recomputed from `records`.
    beta_which = cfg.beta_which_frac * frozen_density["best_minus_second"]
    beta_now = frozen_density["best_minus_noop"] / cfg.beta_now_div
    total_steps = cfg.policy_steps if steps is None else steps
    # Records arrive pre-split into train/tune roles; never re-split.
    train_ex = [fan_to_example(r, normalizer) for r in records if r.split_role == "train"]
    tune_ex = [fan_to_example(r, normalizer) for r in records if r.split_role == "tune"]
    if not train_ex:
        raise ValueError("no train-role records")
    policy = Policy(cfg, gen)
    opt = torch.optim.Adam(policy.parameters(), lr=cfg.policy_lr)
    eval_every = max(1, total_steps // 10)
    curve: list[float] = []
    best_score = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    tune_batch = _collate_examples(tune_ex) if tune_ex else None
    for step in range(total_steps):
        idxs = torch.randint(len(train_ex), (cfg.policy_batch_size,), generator=gen)
        batch = _collate_examples([train_ex[int(i)] for i in idxs])
        enable_now = warmup_schedule(step, total_steps, cfg.warmup_frac)
        loss = policy_loss(policy, batch, cfg, beta_which=beta_which, beta_now=beta_now, enable_now=enable_now, mask_fn=mask_fn)
        opt.zero_grad(set_to_none=True)
        loss.backward()  # type: ignore[no-untyped-call]
        opt.step()
        if tune_batch is not None and ((step + 1) % eval_every == 0 or step == total_steps - 1):
            with torch.no_grad():
                score = float(
                    policy_loss(policy, tune_batch, cfg, beta_which=beta_which, beta_now=beta_now, enable_now=True, mask_fn=mask_fn)
                )
            curve.append(score)
            if score < best_score:  # tune-scored checkpointing
                best_score = score
                best_state = {k: v.detach().clone() for k, v in policy.state_dict().items()}
    if best_state is not None:
        policy.load_state_dict(best_state)
    return policy, {"curve": curve, "beta_which": beta_which, "beta_now": beta_now}


@semantic
def sign_flip_pvalue(lifts: torch.Tensor, n: int, seed: int) -> float:
    # One-sided; (count+1)/(n+1).
    g = make_generator(seed)
    obs = float(lifts.mean())
    signs = torch.randint(0, 2, (n, lifts.numel()), generator=g, dtype=torch.float32) * 2 - 1
    means = (signs * lifts.reshape(1, -1)).mean(-1)
    count = int((means >= obs).sum())
    return (count + 1) / (n + 1)


@semantic
def money_chart_permutation_pvalue(
    pathologies: list[str], picks: list[str], episodes: list[int], designed: dict[str, str], n: int, seed: int
) -> tuple[int, float]:
    # Classes-matched count: modal pick per pathology class vs designed
    # winner, deterministic LEXICOGRAPHIC tie-break. Permutation unit is the
    # EPISODE (spec rev 6.1, pre-data amendment): pathology is an
    # episode-level attribute and the grid points of one episode carry
    # correlated picks, so labels are shuffled across EPISODES and every
    # point of an episode moves together — point-level shuffling would
    # under-disperse the null (variance low by up to the cluster size).
    def matched(paths: list[str]) -> int:
        count = 0
        for cls in sorted(designed):
            cls_picks = [pk for pa, pk in zip(paths, picks, strict=True) if pa == cls]
            if not cls_picks:
                continue
            tally: dict[str, int] = {}
            for pk in cls_picks:
                tally[pk] = tally.get(pk, 0) + 1
            top = max(tally.values())
            modal = min(pk for pk, c in tally.items() if c == top)
            if modal == designed[cls]:
                count += 1
        return count

    obs = matched(pathologies)
    ep_order: list[int] = []
    ep_path: dict[int, str] = {}
    for e, pa in zip(episodes, pathologies, strict=True):
        if e not in ep_path:
            ep_order.append(e)
            ep_path[e] = pa
        elif ep_path[e] != pa:
            raise ValueError(f"episode {e} carries two pathology labels — clustering broken")
    g = make_generator(seed)
    ge = 0
    m = len(ep_order)
    for _ in range(n):
        perm = torch.randperm(m, generator=g)
        remap = {ep_order[j]: ep_path[ep_order[int(perm[j])]] for j in range(m)}
        if matched([remap[e] for e in episodes]) >= obs:
            ge += 1
    return obs, (ge + 1) / (n + 1)


# section 13 — SELFTEST
def _tiny_bundle_for_selftest(device: str) -> DataBundle:
    # Deterministic synthetic CIFAR-shaped data (hardcoded literal seed — the
    # smoke episode must be byte-identical across selftest invocations).
    g = torch.Generator().manual_seed(0)

    def mk(n: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.randint(0, 256, (n, 3, 32, 32), generator=g, dtype=torch.uint8)
        y = torch.randint(0, 10, (n,), generator=g)
        return x.to(device), y.to(device)

    tx, ty = mk(512)
    vx, vy = mk(128)
    ex, ey = mk(128)
    return DataBundle(tx, ty, vx, vy, ex, ey)


def _selftest_telemetry_stub(epoch: int, poison: bool = False) -> TelemetryRecord:
    # Two well-separated synthetic records for the learner-blindness check;
    # `poison` makes every field wildly different so any leak is visible.
    v = 9.0 if poison else 1.0
    return build_record(
        epoch=epoch,
        train_loss=v,
        val_loss=v,
        val_acc=0.9 if poison else 0.1,
        train_loss_delta=v,
        val_loss_delta=v,
        grad_norm_mean=(v, v, v),
        grad_norm_var=(v, v, v),
        act_saturation=(v, v, v),
        weight_norm=(v, v, v),
        per_class_val_acc_std=v,
        confusion_entropy=v,
    )


def _section_source(number: int) -> str:
    src = Path(__file__).read_text(encoding="utf-8")
    marker = f"# section {number} "
    start = src.index(marker)
    nxt = src.find("# section ", start + len(marker))
    return src[start:nxt] if nxt != -1 else src[start:]


@semantic
def run_selftest(cfg: Config, device: str, certify: bool = False, store_root: str = "runs/kernel_demo") -> dict[str, object]:
    import tempfile
    import time

    is_cuda = torch.device(device).type == "cuda"
    steps: dict[str, dict[str, object]] = {}

    def record(name: str, fn: Callable[[], dict[str, object]], gpu_only: bool = False) -> None:
        if gpu_only and not is_cuda:
            steps[name] = {"status": "skipped", "reason": "GPU-only step on CPU"}
            return
        try:
            detail = fn()
            steps[name] = {"status": "pass", **detail}
        except Exception as exc:  # loud in the table, not a crash of the table
            steps[name] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}

    # 1. Forbidden relaxations — printed, recorded.
    print("FORBIDDEN_RELAXATIONS:")
    for item in FORBIDDEN_RELAXATIONS:
        print(f"  - {item}")
    steps["forbidden_relaxations"] = {"status": "pass", "items": list(FORBIDDEN_RELAXATIONS)}

    # 2. Per-seed determinism probe (GPU): forward+backward under the flags; a
    # missing-deterministic-kernel RuntimeError is a hard failure (grouped
    # conv/GroupNorm coverage verified on this build, not assumed).
    def determinism_probe() -> dict[str, object]:
        enable_class1()
        for name in SEED_NAMES:
            seed = build_seed(name, 64, 1).to(device)
            h = torch.randn(4, 64, 8, 8, generator=make_generator(derive(cfg.run_seed, "probe", name))).to(device)
            seed.gain.data.fill_(1.0)
            out = seed(h)
            out.sum().backward()
        return {"seeds": list(SEED_NAMES)}

    record("determinism_probe", determinism_probe, gpu_only=True)

    # 3. Smoke episode: base -> fan -> twin holds; null-seed arm reproduces
    # base hashes (run_fan hard-stops on mismatch).
    def smoke_episode() -> dict[str, object]:
        tiny = dataclasses.replace(cfg, horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3))
        bundle = _tiny_bundle_for_selftest(device)
        ctx = make_episode(tiny, bundle, device, derive(cfg.run_seed, "selftest-smoke"))
        trace = run_base(ctx, tiny, fan_epochs=(2,))
        if trace.status != "ok":
            raise RuntimeError(f"smoke base diverged at {trace.diverged_at}")
        arms, meta = run_fan(
            tiny, bundle, device, ctx.episode_seed, ctx.pathology, ctx.future, trace.snapshots[2], trace, False, include_nullseed=True
        )
        if not meta.get("twin_ok") or not meta.get("nullseed_ok"):
            raise RuntimeError(f"smoke fan integrity: {meta}")
        return {"arms": [a.name for a in arms], "twin_ok": True, "nullseed_ok": True}

    record("smoke_episode", smoke_episode)

    # 4. Tau-init RMS check: all four seeds against a real host batch.
    def tau_init_rms() -> dict[str, object]:
        host = build_host("mild", derive(cfg.run_seed, "selftest-tau-host")).to(device)
        x = _tiny_bundle_for_selftest(device).val_x[: cfg.batch_size]
        host.eval()
        with torch.no_grad():
            feats = host.forward_to_slot(normalize_u8(x))
        ratios: dict[str, float] = {}
        for name in SEED_NAMES:
            seed = build_seed(name, 64, derive(cfg.run_seed, "selftest-tau", name)).to(device)
            tau_init(seed, feats, cfg)
            seed.train()
            with torch.no_grad():
                ratio = float(seed(feats).pow(2).mean().sqrt() / feats.pow(2).mean().sqrt())
            ratios[name] = ratio
            if abs(ratio - cfg.tau) / cfg.tau > 0.05:
                raise RuntimeError(f"tau-init RMS off target for {name}: {ratio:.5f} vs {cfg.tau}")
        return {"ratios": ratios}

    record("tau_init_rms", tau_init_rms)

    # 5. Slot-site signed-zero scan.
    def signed_zero_scan() -> dict[str, object]:
        host = build_host("mild", derive(cfg.run_seed, "selftest-zero-host")).to(device)
        x = _tiny_bundle_for_selftest(device).val_x
        host.eval()
        with torch.no_grad():
            out = host.forward_to_slot(normalize_u8(x))
        neg_zero = int((torch.signbit(out) & (out == 0)).sum())
        if neg_zero:
            raise RuntimeError(f"{neg_zero} exact -0.0 values at the slot site")
        return {"checked": int(out.numel())}

    record("signed_zero_scan", signed_zero_scan)

    # 6. Blindness check (TelemetryRecord field names) + nn.init. grep of
    # sections 4/5/11 (those calls take no generator= and bypass rng_scope).
    def blindness_and_init_grep() -> dict[str, object]:
        names = {f.name for f in dataclasses.fields(TelemetryRecord)}
        for forbidden in ("pathology", "wall", "device", "worker", "time"):
            if any(forbidden in n for n in names):
                raise RuntimeError(f"blindness violation: {forbidden!r} in TelemetryRecord fields")
        needle = "nn." + "init."  # split so this section's own source never matches
        for sec in (4, 5, 11):
            if needle in _section_source(sec):
                raise RuntimeError(f"nn.init. call in section {sec}")
        return {"fields": sorted(names)}

    record("blindness_and_init_grep", blindness_and_init_grep)

    # 7. Store checks: round-trip incl. non-finite; split wall; duplicate
    # identity; schema_version refusal.
    def store_checks() -> dict[str, object]:
        def rec(episode_seed: int, split_role: str = "train", kind: str = "fan") -> FanRecord:
            return make_fan_record(
                kind=kind,
                episode_seed=episode_seed,
                seed_namespace="dev",
                split_role=split_role,
                pathology_id="mild",
                fan_epoch=5,
                refan_k=None,
                schedule_id="selftest",
                policy_checkpoint_id=None,
                iteration=None,
                config_hash="selftest",
                frozen_block_hash="selftest",
                manifest_hash=None,
                common_future_hash="selftest",
                host_init_hash="selftest",
                env={},
                arms=[{"name": "noop", "status": "ok", "r_val": 0.4, "curve_val": [0.1, float("nan")]}],
                telemetry=[],
                decisions=None,
                gate_results=None,
            )

        line = encode_record(rec(1))
        decoded = decode_record(line)
        curve = decoded.arms[0]["curve_val"]
        if not (isinstance(curve, list) and curve[1] is None):
            raise RuntimeError("non-finite did not round-trip as null")
        try:
            decode_record(line.replace(f'"schema_version": {SCHEMA_VERSION}', '"schema_version": 999'))
            raise RuntimeError("schema_version refusal did not fire")
        except ValueError:
            pass
        try:
            _assert_trainable([rec(2, split_role="eval")])
            raise RuntimeError("split wall did not fire")
        except SplitViolation:
            pass
        with tempfile.TemporaryDirectory() as tmp:
            s = Store(tmp)
            s.append(0, rec(3))
            s.append(1, rec(3))
            try:
                s.merge()
                raise RuntimeError("duplicate-identity assert did not fire")
            except ValueError:
                pass
            s.close()
        return {}

    record("store_checks", store_checks)

    # 8. Partition check: 45k/5k/10k, disjoint.
    def partition_check() -> dict[str, object]:
        train_idx, val_idx = split_indices(cfg.run_seed)
        if train_idx.numel() != 45_000 or val_idx.numel() != 5_000:
            raise RuntimeError(f"bad split sizes: {train_idx.numel()}/{val_idx.numel()}")
        if bool(torch.isin(train_idx, val_idx).any()):
            raise RuntimeError("train/val overlap")
        return {"train": 45_000, "val": 5_000, "test": 10_000}

    record("partition_check", partition_check)

    # 9. rng_scope global-stream isolation.
    def rng_scope_isolation() -> dict[str, object]:
        before = torch.get_rng_state()
        with rng_scope(make_generator(123)):
            torch.randn(64)
        if not torch.equal(before, torch.get_rng_state()):
            raise RuntimeError("rng_scope leaked into the global stream")
        return {}

    record("rng_scope_isolation", rng_scope_isolation)

    # 10. Deterministic-mode cost: timed epoch, flags on vs off; the flags-off
    # leg runs in a THROWAWAY subprocess (fresh interpreter, nothing written
    # to any store) — a scoped measurement exception to FORBIDDEN_RELAXATIONS,
    # never a relaxation of the live process.
    det_mode_cost: dict[str, float] | None = None

    def det_cost() -> dict[str, object]:
        nonlocal det_mode_cost
        import subprocess
        import sys

        tiny = dataclasses.replace(cfg, horizon=1, batch_size=64)
        bundle = _tiny_bundle_for_selftest(device)
        enable_class1()
        ctx = make_episode(tiny, bundle, device, derive(cfg.run_seed, "selftest-cost"))
        t0 = time.perf_counter()
        train_one_epoch(ctx, 0)
        if is_cuda:
            torch.cuda.synchronize(torch.device(device))
        on_s = time.perf_counter() - t0
        script = (
            "import time, dataclasses, torch\n"
            "import experiments.kernel_demo as k\n"
            f"tiny = dataclasses.replace(k.Config(), horizon=1, batch_size=64)\n"
            f"bundle = k._tiny_bundle_for_selftest({device!r})\n"
            f"ctx = k.make_episode(tiny, bundle, {device!r}, k.derive(tiny.run_seed, 'selftest-cost'))\n"
            "t0 = time.perf_counter()\n"
            "k.train_one_epoch(ctx, 0)\n"
            f"torch.cuda.synchronize(torch.device({device!r}))\n"
            "print(time.perf_counter() - t0)\n"
        )
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
        off_s = float(out.stdout.strip().splitlines()[-1])
        det_mode_cost = {"flags_on_s": on_s, "flags_off_s": off_s, "slowdown": on_s / off_s if off_s > 0 else float("inf")}
        print(f"deterministic-mode cost: on={on_s:.3f}s off={off_s:.3f}s slowdown={det_mode_cost['slowdown']:.2f}x")
        return dict(det_mode_cost)

    record("det_mode_cost", det_cost, gpu_only=True)

    # 11. Learner blindness to POST-decision arm telemetry (rev 6.2). The
    # arm trajectory exists in the store for offline study only; if it ever
    # reached fan_to_example the policy would be reading the future of the
    # decision it is being trained to make. Poison it and require the
    # learner's input to be bit-identical.
    def learner_ignores_arm_telemetry() -> dict[str, object]:
        base_tele = [dataclasses.asdict(t) for t in [_selftest_telemetry_stub(e) for e in range(3)]]
        arms: list[dict[str, object]] = [
            {"name": n, "status": "ok", "r_val": 0.5, "r_test": None, "telemetry": base_tele} for n in ("noop", *SEED_NAMES)
        ]
        rec = make_fan_record(
            kind="fan",
            episode_seed=1,
            seed_namespace="dev",
            split_role="train",
            pathology_id="mild",
            fan_epoch=3,
            refan_k=None,
            schedule_id="selftest",
            policy_checkpoint_id=None,
            iteration=None,
            config_hash="selftest",
            frozen_block_hash="selftest",
            manifest_hash=None,
            common_future_hash="selftest",
            host_init_hash="selftest",
            env={},
            arms=arms,
            telemetry=base_tele,
            decisions=None,
            gate_results=None,
        )
        nz = Normalizer.identity()
        clean = fan_to_example(rec, nz)
        poisoned_tele = [dataclasses.asdict(t) for t in [_selftest_telemetry_stub(e, poison=True) for e in range(3)]]
        for a in rec.arms:
            a["telemetry"] = poisoned_tele
        dirty = fan_to_example(rec, nz)
        if not torch.equal(cast(torch.Tensor, clean["tokens"]), cast(torch.Tensor, dirty["tokens"])):
            raise RuntimeError("learner input moved when ARM telemetry changed — post-decision leakage into training")
        if not torch.equal(cast(torch.Tensor, clean["r"]), cast(torch.Tensor, dirty["r"])):
            raise RuntimeError("learner rewards moved when ARM telemetry changed")
        return {"checked": ["tokens", "r"]}

    record("learner_ignores_arm_telemetry", learner_ignores_arm_telemetry)

    failed = [n for n, s in steps.items() if s["status"] == "fail"]
    skipped = [n for n, s in steps.items() if s["status"] == "skipped"]
    ok = not failed
    result: dict[str, object] = {"ok": ok, "steps": steps, "failed": failed, "skipped": skipped}
    if certify:
        # Phase A requires zero skipped: GPU, all steps run, all passed.
        if not is_cuda or failed or skipped:
            raise RuntimeError(f"--certify refused: cuda={is_cuda}, failed={failed}, skipped={skipped}")
        import subprocess

        git_rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        root = Path(store_root)
        root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"git_rev": git_rev, "results": steps, "det_mode_cost": det_mode_cost}, indent=2)
        tmp_path = root / "certified.json.tmp"
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, root / "certified.json")  # the artifact preflight --freeze checks HEAD against
        result["certified"] = str(root / "certified.json")
    return result


# section 14 — PREFLIGHT
@semantic
def draw_schedule(episode_seed: int, cfg: Config, label: str = "schedule") -> tuple[int, int]:
    # 2 ordered epochs, uniform WITHOUT replacement, inclusive window.
    # label distinguishes independent draws over the same distribution
    # (collection uses "schedule"; the frozen eval grid uses "evalgrid").
    lo, hi = cfg.window
    g = make_generator(derive(episode_seed, label))
    perm = torch.randperm(hi - lo + 1, generator=g)[: cfg.fans_per_episode]
    a, b = sorted(int(lo + i) for i in perm)  # unpack pins fans_per_episode == 2 loudly
    return a, b


@semantic
def run_collection_episode(
    cfg: Config,
    data: DataBundle,
    device: str,
    episode_seed: int,
    namespace: str,
    store: Store,
    worker_id: int,
    read_test: bool,
    *,
    manifest_hash: str | None = None,
    worker_count: int = 1,
    schedule_label: str = "schedule",
    skip_fan_ids: frozenset[str] = frozenset(),
) -> None:
    if namespace == "preflight":
        split_role = "preflight"
    elif namespace == "eval":
        split_role = "eval"
    else:
        split_role = train_tune_split(episode_seed)  # recorded at collection time, never re-split
    fan_epochs = draw_schedule(episode_seed, cfg, schedule_label)
    ctx = make_episode(cfg, data, device, episode_seed, read_test)
    host_init = state_hash(ctx.host)
    trace = run_base(ctx, cfg, fan_epochs=fan_epochs)
    env = env_block(device, worker_count)
    # The 1-in-10 null-seed subsample wired into the COLLECTION path, not only
    # selftest.
    include_nullseed = derive(episode_seed, "nullseed-subsample") % 10 == 0
    for fe in fan_epochs:
        if fan_identity(episode_seed, fe, "fan", None, None, None) in skip_fan_ids:
            continue  # crash-resume: this fan is already durable in a shard; re-appending would duplicate its fan_id
        snap = trace.snapshots.get(fe)
        if snap is None:
            continue  # scheduled after a base divergence; recorded in the void_event below
        # Delta-weight sidecar, keyed by the fan identity this fan will record.
        # Recomputed here rather than threaded from make_fan_record so the
        # weights land under the SAME id even if the fan later fails to append.
        arms, _meta = run_fan(
            cfg,
            data,
            device,
            episode_seed,
            ctx.pathology,
            ctx.future,
            snap,
            trace,
            read_test,
            include_nullseed=include_nullseed,
            delta_dir=Path(store.root) / "deltas" / fan_identity(episode_seed, fe, "fan", None, None, None),
        )
        store.append(
            worker_id,
            make_fan_record(
                kind="fan",
                episode_seed=episode_seed,
                seed_namespace=namespace,
                split_role=split_role,
                pathology_id=ctx.pathology,
                fan_epoch=fe,
                refan_k=None,
                schedule_id=make_schedule_id(cfg),
                policy_checkpoint_id=None,
                iteration=None,
                config_hash=config_hash(),
                frozen_block_hash=frozen_block_hash(cfg),
                manifest_hash=manifest_hash,
                common_future_hash=ctx.future.hash,
                host_init_hash=host_init,
                env=env,
                arms=[dataclasses.asdict(a) for a in arms],
                telemetry=[dataclasses.asdict(t) for t in ctx.telemetry[:fe]],
                decisions=None,
                gate_results=None,
            ),
        )
    if trace.status == "diverged":
        if fan_identity(episode_seed, None, "void_event", None, None, None) in skip_fan_ids:
            return  # crash-resume: the divergence is already on record
        skipped = [fe for fe in fan_epochs if fe not in trace.snapshots]
        store.append(
            worker_id,
            make_fan_record(
                kind="void_event",
                episode_seed=episode_seed,
                seed_namespace=namespace,
                split_role=split_role,
                pathology_id=ctx.pathology,
                fan_epoch=None,
                refan_k=None,
                schedule_id=make_schedule_id(cfg),
                policy_checkpoint_id=None,
                iteration=None,
                config_hash=config_hash(),
                frozen_block_hash=frozen_block_hash(cfg),
                manifest_hash=manifest_hash,
                common_future_hash=ctx.future.hash,
                host_init_hash=host_init,
                env=env,
                arms=[],
                telemetry=[],
                decisions=None,
                gate_results={
                    "event": "base_divergence",
                    "diverged_at": trace.diverged_at,
                    "skipped_fan_epochs": skipped,
                },
            ),
        )


@semantic
def run_refan(
    cfg: Config,
    data: DataBundle,
    device: str,
    episode_seed: int,
    fan_epoch: int,
    k: int,
    store: Store,
    worker_id: int,
    *,
    namespace: str = "preflight",
    read_test: bool = False,
    manifest_hash: str | None = None,
) -> None:
    ctx = make_episode(cfg, data, device, episode_seed, read_test)
    host_init = state_hash(ctx.host)
    try:
        for e in range(fan_epoch):
            train_one_epoch(ctx, e)
    except TelemetryDivergence:
        # The base replay diverges deterministically — crashing here would
        # brick preflight/eval at the same epoch on every retry. Record the
        # void (complete history; refan_k makes the identity distinct from
        # the episode's own base-divergence void_event) and skip this refan.
        store.append(
            worker_id,
            make_fan_record(
                kind="void_event",
                episode_seed=episode_seed,
                seed_namespace=namespace,
                split_role="preflight" if namespace == "preflight" else "eval",
                pathology_id=ctx.pathology,
                fan_epoch=fan_epoch,
                refan_k=k,
                schedule_id=make_schedule_id(cfg),
                policy_checkpoint_id=None,
                iteration=None,
                config_hash=config_hash(),
                frozen_block_hash=frozen_block_hash(cfg),
                manifest_hash=manifest_hash,
                common_future_hash="",
                host_init_hash=host_init,
                env=env_block(device, 1),
                arms=[],
                telemetry=[],
                decisions=None,
                gate_results={"event": "refan_base_divergence", "diverged_at": len(ctx.telemetry)},
            ),
        )
        return
    snap = take_snapshot(ctx)
    future_k = CommonFuture.draw(derive(episode_seed, "refan", k), data.train_x.shape[0], cfg.horizon, cfg)
    # 5 real arms incl. a FRESH no-op under the new future — the base tail is
    # not a valid comparand; the twin is re-based (measured, not compared).
    arms = [run_arm(cfg, data, device, episode_seed, ctx.pathology, future_k, snap, name, read_test) for name in ("noop", *SEED_NAMES)]
    store.append(
        worker_id,
        make_fan_record(
            kind="refan",
            episode_seed=episode_seed,
            seed_namespace=namespace,
            split_role="preflight" if namespace == "preflight" else "eval",
            pathology_id=ctx.pathology,
            fan_epoch=fan_epoch,
            refan_k=k,
            schedule_id=make_schedule_id(cfg),
            policy_checkpoint_id=None,
            iteration=None,
            config_hash=config_hash(),
            frozen_block_hash=frozen_block_hash(cfg),
            manifest_hash=manifest_hash,
            common_future_hash=future_k.hash,
            host_init_hash=host_init,
            env=env_block(device, 1),
            arms=[dataclasses.asdict(a) for a in arms],
            telemetry=[dataclasses.asdict(t) for t in ctx.telemetry],
            decisions=None,
            gate_results=None,
        ),
    )


@semantic
@dataclass
class GateResult:
    ok: bool
    reason: str | None
    detail: dict[str, object]
    remedy: str


@semantic
def _arm_by_name(rec: FanRecord) -> dict[str, dict[str, object]]:
    return {str(a["name"]): a for a in rec.arms}


@semantic
def _all_arms_diverged(records: list[FanRecord]) -> bool:
    arms = [a for r in records for a in r.arms]
    return bool(arms) and all(a.get("status") == "diverged" for a in arms)


@semantic
def _first_fans(records: list[FanRecord]) -> list[FanRecord]:
    # Gate unit: the FIRST fan per episode (lowest fan_epoch) — one unit per
    # trajectory, no pseudo-replication.
    best: dict[int, FanRecord] = {}
    for r in records:
        if r.kind != "fan" or r.fan_epoch is None:
            continue
        cur = best.get(r.episode_seed)
        if cur is None or (cur.fan_epoch is not None and r.fan_epoch < cur.fan_epoch):
            best[r.episode_seed] = r
    return [best[k] for k in sorted(best)]


@semantic
def _val_argmax(rec: FanRecord, include_noop: bool) -> str:
    names = [*SEED_NAMES, "noop"] if include_noop else list(SEED_NAMES)
    by = _arm_by_name(rec)
    best_name, best_r = names[0], float("-inf")
    for n in names:  # ties break to the first name in SEED_NAMES(+noop) order
        r = _as_float(by[n]["r_val"])
        if r > best_r:
            best_r, best_name = r, n
    return best_name


@semantic
def gate1_noop_sanity(records: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "sampler"
    first = _first_fans(records)
    if not first:
        return GateResult(False, "no fan records", {}, remedy)
    if _all_arms_diverged(first):
        return GateResult(False, "all arms diverged", {}, remedy)
    mild = [r for r in first if r.pathology_id == "mild"]
    wins = sum(1 for r in mild if _val_argmax(r, include_noop=True) == "noop")
    bad_modal: list[str] = []
    for path in PATHOLOGIES:
        if path == "mild":
            continue
        grp = [r for r in first if r.pathology_id == path]
        if not grp:
            continue
        tally: dict[str, int] = {}
        for r in grp:
            w = _val_argmax(r, include_noop=True)
            tally[w] = tally.get(w, 0) + 1
        top = max(tally.values())
        modal = min(n for n, c in tally.items() if c == top)
        if modal == "noop":
            bad_modal.append(path)  # D1: no-op modal in a TARGETED pathology
    ok = wins >= cfg.gate1_min_mild_noop_wins and not bad_modal
    reason = None if ok else f"mild no-op wins {wins} < {cfg.gate1_min_mild_noop_wins} or no-op modal in {bad_modal}"
    return GateResult(ok, reason, {"mild_noop_wins": wins, "noop_modal_in": bad_modal}, remedy)


@semantic
def gate2_signal(records: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "sampler"
    first = _first_fans(records)
    if not first:
        return GateResult(False, "no fan records", {}, remedy)
    xs: list[torch.Tensor] = []
    y_path: list[int] = []
    y_win: list[int] = []
    hold_mask: list[bool] = []
    contingency: dict[str, dict[str, int]] = {}
    for r in first:
        xs.append(torch.stack([_telemetry_vector_from_dict(d) for d in r.telemetry]).mean(0))
        y_path.append(PATHOLOGIES.index(r.pathology_id))
        w = _val_argmax(r, include_noop=False)
        y_win.append(SEED_NAMES.index(w))
        hold_mask.append(derive(r.episode_seed, "probe-split") % 5 == 0)  # D13: by-EPISODE split
        contingency.setdefault(r.pathology_id, {})
        contingency[r.pathology_id][w] = contingency[r.pathology_id].get(w, 0) + 1
    x = torch.stack(xs)
    yp, yw = torch.tensor(y_path), torch.tensor(y_win)
    hold = torch.tensor(hold_mask)
    if not bool(hold.any()) or bool(hold.all()):
        return GateResult(False, "degenerate probe split", {"holdout": int(hold.sum())}, remedy)

    def probe_acc(y: torch.Tensor, label: str) -> float:
        with rng_scope(make_generator(derive(cfg.run_seed, "gate2-probe", label))):
            probe = nn.Linear(TELEMETRY_DIM, 4)
        opt = torch.optim.Adam(probe.parameters(), lr=0.05)
        xt, yt = x[~hold], y[~hold]
        for _ in range(200):
            loss = torch.nn.functional.cross_entropy(probe(xt), yt)
            opt.zero_grad(set_to_none=True)
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
        with torch.no_grad():
            preds = cast(torch.Tensor, probe(x[hold])).argmax(1)
        return float((preds == y[hold]).float().mean())

    path_acc = probe_acc(yp, "pathology")
    win_acc = probe_acc(yw, "winner")
    counts = torch.bincount(yw[hold], minlength=4)
    majority = float(counts.max()) / float(counts.sum())
    ok = path_acc > cfg.gate2_probe_min_acc and win_acc > majority
    reason = (
        None if ok else f"path probe {path_acc:.2f} (min {cfg.gate2_probe_min_acc}) / winner probe {win_acc:.2f} vs majority {majority:.2f}"
    )
    detail: dict[str, object] = {
        "path_acc": path_acc,
        "win_acc": win_acc,
        "majority": majority,
        "contingency": contingency,
        "designed": dict(DESIGNED_WINNER),
    }
    return GateResult(ok, reason, detail, remedy)


@semantic
def gate3_contrast(records: list[FanRecord], refans: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "averaging window, horizon"
    density = measure_fan_density(_first_fans(records))
    # Refan noise floor: a refan replays the SAME base prefix and snapshot and
    # re-runs the same arms under a re-drawn future, so per-arm
    # |R_a^fan - R_a^refan| at the same (episode, epoch) is exactly the
    # future-resampling noise of R. (The density statistic computed ON refans
    # is NOT a floor — it has the same expectation as the fan density itself,
    # which would make this gate structurally unpassable.)
    by_point: dict[tuple[int, int | None], FanRecord] = {(r.episode_seed, r.fan_epoch): r for r in records if r.kind == "fan"}
    diffs: list[float] = []
    for rf in refans:
        fan = by_point.get((rf.episode_seed, rf.fan_epoch))
        if fan is None:
            continue
        fan_by, rf_by = _arm_by_name(fan), _arm_by_name(rf)
        for n in ("noop", *SEED_NAMES):
            diffs.append(abs(_as_float(fan_by[n]["r_val"]) - _as_float(rf_by[n]["r_val"])))
    if not diffs:
        return GateResult(False, "no refans paired with fans for the noise floor", {"density": density}, remedy)
    noise = sum(diffs) / len(diffs)
    floor = dict.fromkeys(density, noise)
    checks = {k: density[k] > cfg.gate3_contrast_mult * floor[k] for k in density}
    ok = all(checks.values())
    failing = [k for k, v in checks.items() if not v]
    reason = None if ok else f"density not > {cfg.gate3_contrast_mult}x refan noise floor for {failing}"
    return GateResult(ok, reason, {"density": density, "floor": floor}, remedy)


@semantic
def gate4_dominance(records: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "sampler / menu balance — menu balance = Task 5 reopen + Phase A re-run, priced, not a knob"
    first = _first_fans(records)
    if not first:
        return GateResult(False, "no fan records", {}, remedy)
    if _all_arms_diverged(first):
        return GateResult(False, "all arms diverged", {}, remedy)
    wins: dict[str, int] = dict.fromkeys(SEED_NAMES, 0)
    per_path: dict[str, dict[str, int]] = {}
    for r in first:
        w = _val_argmax(r, include_noop=False)
        wins[w] += 1
        per_path.setdefault(r.pathology_id, {})
        per_path[r.pathology_id][w] = per_path[r.pathology_id].get(w, 0) + 1
    frac = {n: wins[n] / len(first) for n in SEED_NAMES}
    over = [n for n, f in frac.items() if f > cfg.gate4_dominance_max]
    majority_everywhere = [n for n in SEED_NAMES if all(per_path[p].get(n, 0) > 0.5 * sum(per_path[p].values()) for p in per_path)]
    ok = not over and not majority_everywhere
    reason = None if ok else f"dominance: {over} over {cfg.gate4_dominance_max}; majority everywhere: {majority_everywhere}"
    return GateResult(ok, reason, {"win_frac": frac, "per_pathology": per_path}, remedy)


@semantic
def gate5_magnitude(records: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "tau, lambda, seed_lr — never the sampler"
    lo, hi = cfg.tau / cfg.gate5_rms_band, cfg.tau * cfg.gate5_rms_band
    means: dict[str, float] = {}
    out_of_band: list[str] = []
    for name in SEED_NAMES:
        vals: list[float] = []
        for r in records:
            if r.kind != "fan":
                continue
            a = _arm_by_name(r).get(name)
            v = None if a is None else a.get("rms_ratio_blend_entry")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append(float(v))
        if not vals:
            means[name] = float("nan")
            out_of_band.append(name)  # no measurement is a failure, not a pass
            continue
        m = sum(vals) / len(vals)
        means[name] = m
        if not (lo <= m <= hi):
            out_of_band.append(name)
    ok = not out_of_band
    reason = None if ok else f"mean rms_ratio_blend_entry outside [{lo:.4f}, {hi:.4f}] for {out_of_band}"
    return GateResult(ok, reason, {"means": means, "band": [lo, hi]}, remedy)


@semantic
def gate6_horizon(records: list[FanRecord], cfg: Config) -> GateResult:
    remedy = "horizon, window"
    lo, hi = cfg.window
    mid = (lo + hi) / 2
    fans = [r for r in records if r.kind == "fan" and r.fan_epoch is not None]
    early = [r for r in fans if r.fan_epoch is not None and r.fan_epoch <= mid]
    late = [r for r in fans if r.fan_epoch is not None and r.fan_epoch > mid]
    if not early or not late:
        return GateResult(False, "no early or no late fans", {"early": len(early), "late": len(late)}, remedy)
    de, dl = measure_fan_density(early), measure_fan_density(late)
    checks = {k: dl[k] >= cfg.gate6_late_density_mult * de[k] for k in de}
    ok = all(checks.values())
    failing = [k for k, v in checks.items() if not v]
    reason = None if ok else f"late density < {cfg.gate6_late_density_mult}x early for {failing}"
    return GateResult(ok, reason, {"early": de, "late": dl}, remedy)


@semantic
def gate7_now_vs_later(records: list[FanRecord], cfg: Config) -> GateResult:
    # Report-only: never blocks.
    by_ep: dict[int, list[FanRecord]] = {}
    for r in records:
        if r.kind == "fan" and r.fan_epoch is not None:
            by_ep.setdefault(r.episode_seed, []).append(r)
    gaps: list[float] = []
    for recs in by_ep.values():
        if len(recs) < 2:
            continue
        recs = sorted(recs, key=lambda r: r.fan_epoch or 0)

        def best(rec: FanRecord) -> float:
            by = _arm_by_name(rec)
            return max(_as_float(by[n]["r_val"]) for n in SEED_NAMES)

        gaps.append(best(recs[-1]) - best(recs[0]))
    detail: dict[str, object] = {
        "pairs": len(gaps),
        "p_later_better": (sum(1 for g in gaps if g > 0) / len(gaps)) if gaps else None,
        "mean_gap": (sum(gaps) / len(gaps)) if gaps else None,
    }
    return GateResult(True, None, detail, "report-only")


@semantic
def gate8_pressure(cfg: Config, data: DataBundle, device: str, worker_count: int) -> GateResult:
    remedy = "worker count"
    if torch.device(device).type != "cuda":
        return GateResult(True, "skipped (GPU-only)", {"skipped": True, "concurrency_factor": None}, remedy)
    import subprocess
    import sys
    import time

    tiny = dataclasses.replace(cfg, horizon=4, stage_k=1, stage_m=1, stage_f=1, batch_size=64)
    es = derive(cfg.run_seed, "gate8")

    def run_once() -> tuple[str, float]:
        t0 = time.perf_counter()
        ctx = make_episode(tiny, data, device, es)
        trace = run_base(ctx, tiny, fan_epochs=(1,))
        arm = run_arm(tiny, data, device, es, ctx.pathology, ctx.future, trace.snapshots[1], "noop", False)
        torch.cuda.synchronize(torch.device(device))
        return (arm.host_hashes or [""])[-1], time.perf_counter() - t0

    h_solo, t_solo = run_once()
    # Siblings must apply COLLECTION-shaped pressure: full GPU-resident data
    # (not the ~1.5MB selftest bundle) and long-running episodes, and the
    # pressured leg must actually overlap them — each sibling touches a ready
    # sentinel after its bundle is resident, and the parent waits for all
    # sentinels before timing the pressured run.
    import tempfile

    ready_dir = Path(tempfile.mkdtemp(prefix="gate8_ready_"))
    sibling_template = (
        "import dataclasses, pathlib, torch\n"
        "import experiments.kernel_demo as k\n"
        "k.enable_class1()\n"
        "tiny = dataclasses.replace(k.Config(), horizon=4, stage_k=1, stage_m=1, stage_f=1, batch_size=64)\n"
        f"bundle = k.load_data(k.Config(), {device!r})\n"
        "pathlib.Path({ready!r}).touch()\n"
        f"ctx = k.make_episode(tiny, bundle, {device!r}, k.derive(tiny.run_seed, 'gate8-sibling'))\n"
        "k.run_base(ctx, tiny, fan_epochs=())\n"
    )
    procs = []
    ready_files = []
    for i in range(max(0, worker_count - 1)):
        ready = str(ready_dir / f"ready_{i}")
        ready_files.append(ready)
        procs.append(subprocess.Popen([sys.executable, "-c", sibling_template.format(ready=ready)]))
    deadline = time.monotonic() + 300.0
    while not all(Path(r).exists() for r in ready_files):
        if time.monotonic() > deadline or any(p.poll() not in (None, 0) for p in procs):
            for p in procs:
                p.terminate()
            return GateResult(False, "gate8 siblings failed to become resident", {"worker_count": worker_count}, remedy)
        time.sleep(0.5)
    h_pressured, t_pressured = run_once()  # timed while siblings run
    for p in procs:
        p.terminate()  # pressure measured; full sibling episodes need not finish
    for p in procs:
        p.wait()
    match = h_pressured == h_solo
    concurrency_factor = t_pressured / t_solo if t_solo > 0 else float("inf")
    reason = None if match else "twin hash changed under worker pressure"
    detail: dict[str, object] = {
        "solo_s": t_solo,
        "pressured_s": t_pressured,
        "concurrency_factor": concurrency_factor,  # the measured factor for the runtime table
        "worker_count": worker_count,
        "sibling_data": "full load_data bundle, ready-file synchronized",
        "match": match,
    }
    return GateResult(match, reason, detail, remedy)


def _git_rev() -> str:
    import subprocess

    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _worktree_clean() -> bool:
    import subprocess

    out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    return out.stdout.strip() == ""


@semantic
def dataclass_gates_ok(gates: dict[str, dict[str, object]]) -> bool:
    return all(bool(g["ok"]) for g in gates.values())


@semantic
def freeze_manifest(
    cfg: Config,
    store_root: str,
    gates: dict[str, dict[str, object]],
    normalizer: Normalizer,
    fan_density: dict[str, float],
    det_mode_cost: dict[str, float] | None,
    concurrency_factor: float | None,
    gate8_outcome: dict[str, object] | None,
    *,
    n_train: int | None = None,
) -> dict[str, object]:
    not_ok = [name for name, g in gates.items() if not g["ok"]]
    if not_ok:
        raise RuntimeError(f"freeze refused: gates not ok: {not_ok}")
    if not _worktree_clean():
        raise RuntimeError("freeze refused: worktree dirty")
    certified_path = Path(store_root) / "certified.json"
    if not certified_path.exists():
        raise RuntimeError("freeze refused: no certified.json (run selftest --certify first)")
    certified = json.loads(certified_path.read_text(encoding="utf-8"))
    head = _git_rev()
    if head != certified["git_rev"]:
        raise RuntimeError(f"freeze refused: HEAD {head} != certified rev {certified['git_rev']}")
    manifest: dict[str, object] = {
        "frozen_block_hash": frozen_block_hash(cfg),
        "config_hash": config_hash(),
        "git_rev": head,
        "certified_rev": certified["git_rev"],
        "spec_rev": "rev6.2 (rev6.1 + 2026-08-10 pre-data amendment: per-arm telemetry, cost and horizon-influence recording)",
        "normalizer": json.loads(normalizer.to_json()),
        "fan_density": fan_density,
        "beta_which": cfg.beta_which_frac * fan_density["best_minus_second"],
        "beta_now": fan_density["best_minus_noop"] / cfg.beta_now_div,
        "schedule_id": make_schedule_id(cfg),
        "data_split_id": data_split_id(cfg),
        # Freezing against a --subset preflight must be detectable: gates,
        # normalizer and density were calibrated on THIS many train images.
        "n_train": n_train,
        "gate_results": gates,
        "gate8_outcome": gate8_outcome,
        "det_mode_cost": det_mode_cost,
        "concurrency_factor": concurrency_factor,
        # Echoed for owner sign-off at freeze.
        "plan_authored_constants": {
            "tau_eps": cfg.tau_eps,
            "preflight_refans": cfg.preflight_refans,
            "gate1_min_mild_noop_wins": cfg.gate1_min_mild_noop_wins,
            "gate2_probe_min_acc": cfg.gate2_probe_min_acc,
            "gate3_contrast_mult": cfg.gate3_contrast_mult,
            "gate4_dominance_max": cfg.gate4_dominance_max,
            "gate5_rms_band": cfg.gate5_rms_band,
            "gate6_late_density_mult": cfg.gate6_late_density_mult,
            "policy_lr": cfg.policy_lr,
            "policy_batch_size": cfg.policy_batch_size,
            "policy_steps": cfg.policy_steps,
            "warmup_frac": cfg.warmup_frac,
            "eval_chunk": cfg.eval_chunk,
            "fsync_every": cfg.fsync_every,
        },
    }
    manifest["manifest_hash"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "frozen.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(tmp, root / "frozen.json")  # atomic
    return manifest


@semantic
def run_preflight(
    cfg: Config, data: DataBundle, device: str, store_root: str, freeze: bool = False, gate8_workers: int = 6
) -> dict[str, object]:
    store = Store(store_root, cfg.fsync_every)
    merged = store.merge()
    # Episode completeness is fan-level, not any-record-level: a crash between
    # an episode's two fans must resume the missing fan (existing fan_ids
    # skipped inside run_collection_episode), not drop it silently.
    pf = [r for r in merged if r.seed_namespace == "preflight"]
    pf_fan_counts: dict[int, int] = {}
    pf_voided: set[int] = set()
    for r in pf:
        if r.kind == "fan":
            pf_fan_counts[r.episode_seed] = pf_fan_counts.get(r.episode_seed, 0) + 1
        elif r.kind == "void_event":
            pf_voided.add(r.episode_seed)
    pf_existing = frozenset(r.fan_id for r in pf)
    for i in range(cfg.n_preflight):
        es = derive(cfg.run_seed, "preflight", i)
        if es in pf_voided or pf_fan_counts.get(es, 0) >= cfg.fans_per_episode:
            continue
        try:
            run_collection_episode(cfg, data, device, es, "preflight", store, worker_id=0, read_test=False, skip_fan_ids=pf_existing)
        except TwinDivergence as td:
            # Same localisation artifact worker_main writes — a twin abort
            # must never surface as a bare traceback without its report.
            write_divergence_report(store_root, cfg, es, "noop", td.first_bad_epoch, None, device, 1)
            raise
    merged = store.merge()
    # A void_event with refan_k set is a completed-but-diverged refan: skip it
    # too, or every preflight invocation re-runs it and re-appends the void.
    have_refans = {(r.episode_seed, r.refan_k) for r in merged if r.kind == "refan" or (r.kind == "void_event" and r.refan_k is not None)}
    for k in range(cfg.preflight_refans):  # these supply gate 3's noise floor
        es = derive(cfg.run_seed, "preflight", k % cfg.n_preflight)
        if (es, k) not in have_refans:
            run_refan(cfg, data, device, es, draw_schedule(es, cfg)[0], k, store, worker_id=0)
    merged = store.merge()
    fans = [r for r in merged if r.kind == "fan" and r.seed_namespace == "preflight"]
    refans = [r for r in merged if r.kind == "refan"]
    normalizer = Normalizer()
    vecs = [_telemetry_vector_from_dict(d) for r in fans for d in r.telemetry]
    if vecs:
        normalizer.fit(vecs)
    print(f"normalizer: {normalizer.to_json()}")
    density = measure_fan_density(_first_fans(fans))
    gates: dict[str, GateResult] = {
        "gate1_noop_sanity": gate1_noop_sanity(fans, cfg),
        "gate2_signal": gate2_signal(fans, cfg),
        "gate3_contrast": gate3_contrast(fans, refans, cfg),
        "gate4_dominance": gate4_dominance(fans, cfg),
        "gate5_magnitude": gate5_magnitude(fans, cfg),
        "gate6_horizon": gate6_horizon(fans, cfg),
        "gate7_now_vs_later": gate7_now_vs_later(fans, cfg),
        # gate8_workers defaults to collect's per-device worker default; the
        # certified worker_count is recorded in gate8_outcome.detail.
        "gate8_pressure": gate8_pressure(cfg, data, device, worker_count=gate8_workers),
    }
    # gate_results payloads store plain dicts, never dataclass instances.
    gate_dicts = {name: dataclasses.asdict(g) for name, g in gates.items()}
    for name, g in gates.items():
        print(f"{name:22s} {'OK  ' if g.ok else 'FAIL'} {g.reason or ''}  [remedy: {g.remedy}]")
    iteration = len([r for r in merged if r.kind == "preflight_iter"])  # derived from store state
    store.append(
        0,
        make_fan_record(
            kind="preflight_iter",
            episode_seed=cfg.run_seed,
            seed_namespace="preflight",
            split_role="preflight",
            pathology_id="all",
            fan_epoch=None,
            refan_k=None,
            schedule_id=make_schedule_id(cfg),
            policy_checkpoint_id=None,
            iteration=iteration,
            config_hash=config_hash(),
            frozen_block_hash=frozen_block_hash(cfg),
            manifest_hash=None,
            common_future_hash="",
            host_init_hash="",
            env={"git_rev": _git_rev()},
            arms=[],
            telemetry=[],
            decisions=None,
            gate_results=cast(dict[str, object], gate_dicts),
        ),
    )
    store.close()
    result: dict[str, object] = {
        "gates": gate_dicts,
        "density": density,
        "iteration": iteration,
        "normalizer": json.loads(normalizer.to_json()),
    }
    if freeze:
        certified_path = Path(store_root) / "certified.json"
        # Tier-1 read (ADR-0015): certified.json is our own artefact. freeze_manifest
        # refuses without it, so an absent file is a caller error and a MISSING KEY is
        # corruption — both must be loud. An explicit null value is a recorded absence
        # (CPU run, no measurement) and is legitimate; that distinction is the whole
        # point of ADR-0002 P2, and `.get()` erased it.
        if not certified_path.exists():
            raise RuntimeError("freeze refused: no certified.json (run selftest --certify first)")
        certified = json.loads(certified_path.read_text(encoding="utf-8"))
        det_cost_recorded = certified["det_mode_cost"]
        g8 = gate_dicts["gate8_pressure"]
        concurrency = cast(dict[str, object], g8["detail"]).get("concurrency_factor")
        result["manifest"] = freeze_manifest(
            cfg,
            store_root,
            gate_dicts,
            normalizer,
            density,
            cast("dict[str, float] | None", det_cost_recorded),
            cast("float | None", concurrency),
            g8,
            n_train=int(data.train_x.shape[0]),
        )
    return result


# section 15 — COLLECT
@semantic
def write_divergence_report(
    store_root: str,
    cfg: Config,
    episode_seed: int,
    arm_name: str,
    first_bad_epoch: int,
    manifest_hash: str | None,
    device: str,
    worker_count: int,
) -> str:
    pathology = PATHOLOGIES[derive(episode_seed, "pathology") % 4]
    host = build_host(pathology, derive(episode_seed, "host-init"))
    report = {
        "episode_seed": episode_seed,
        "arm_name": arm_name,
        "first_bad_epoch": first_bad_epoch,
        "config_hash": config_hash(),
        "frozen_block_hash": frozen_block_hash(cfg),
        "manifest_hash": manifest_hash,
        "env_block": env_block(device, worker_count),
        "host_init_hash": state_hash(host),
    }
    path = Path(store_root) / f"divergence_{episode_seed}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return str(path)


def worker_main(
    worker_id: int,
    device: str,
    cfg: Config,
    store_root: str,
    seeds: list[int],
    halt: object,  # multiprocessing.Event (spawn-context type is not importable statically)
    data_loader: Callable[[Config, str, int | None], DataBundle],
    episode_runner: Callable[..., None],
    manifest_hash: str | None,
    worker_count: int,
    log_dir: str,
    skip_fan_ids: frozenset[str] = frozenset(),
) -> None:
    enable_class1()  # MUST be the first statement of every process
    dev = torch.device(device)
    if dev.type == "cuda":
        torch.cuda.set_device(dev)
    import time

    log_path = Path(log_dir) / f"worker_{worker_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        data = data_loader(cfg, device, None)  # load once, resident per process
        # Tier-1 read (ADR-0015): a MISSING key is a corrupt manifest and must be
        # loud — `.get()` here made an absent key satisfy the very guard below.
        # An explicit null still means "not calibrated against a specific n".
        manifest_n = json.loads((Path(store_root) / "frozen.json").read_text(encoding="utf-8"))["n_train"]
        if manifest_n not in (None, int(data.train_x.shape[0])):
            # The manifest's gates/normalizer/density were calibrated on a
            # different data size (--subset preflight?) — collecting against
            # it would silently mix calibrations.
            raise RuntimeError(f"collect refused: n_train mismatch (manifest {manifest_n}, live {int(data.train_x.shape[0])})")
        store = Store(store_root, cfg.fsync_every)
        try:
            for es in seeds:
                if halt.is_set():  # type: ignore[attr-defined]
                    print(f"worker={worker_id} halting between episodes", flush=True)
                    break
                t0 = time.perf_counter()
                try:
                    episode_runner(
                        cfg,
                        data,
                        device,
                        es,
                        "train",
                        store,
                        worker_id,
                        False,
                        manifest_hash=manifest_hash,
                        worker_count=worker_count,
                        skip_fan_ids=skip_fan_ids,
                    )
                except TwinDivergence as td:
                    write_divergence_report(store_root, cfg, es, "noop", td.first_bad_epoch, manifest_hash, device, worker_count)
                    halt.set()  # type: ignore[attr-defined]
                    print(f"worker={worker_id} TwinDivergence episode={es} epoch={td.first_bad_epoch}: HALT", flush=True)
                    break
                print(
                    f"heartbeat worker={worker_id} episode={es} epochs={cfg.horizon} elapsed={time.perf_counter() - t0:.1f}s",
                    flush=True,
                )
        finally:
            store.close()


_NON_SEMANTIC["worker_main"] = "process orchestration; every semantic step it dispatches is independently on the surface"
_NON_SEMANTIC["write_divergence_report"] = "diagnostic artifact writer; every hash it records is computed by functions on the surface"


@semantic
def run_collect(
    cfg: Config,
    store_root: str,
    devices: list[str],
    n_workers_per_device: int,
    limit: int | None = None,
    extend: int = 0,
    *,
    data_loader: Callable[[Config, str, int | None], DataBundle] = load_data,
    episode_runner: Callable[..., None] = run_collection_episode,
) -> dict[str, object]:
    import multiprocessing

    frozen_path = Path(store_root) / "frozen.json"
    if not frozen_path.exists():
        raise RuntimeError("collect refused: no frozen.json (run preflight --freeze first)")
    manifest = json.loads(frozen_path.read_text(encoding="utf-8"))
    if manifest["frozen_block_hash"] != frozen_block_hash(cfg):
        raise RuntimeError("collect refused: frozen_block_hash mismatch (live Config differs from the manifest)")
    if manifest["config_hash"] != config_hash():
        raise RuntimeError("collect refused: config_hash mismatch (live source differs from the manifest)")
    if not dataclass_gates_ok(manifest["gate_results"]):
        raise RuntimeError("collect refused: manifest gate_results not all ok")
    manifest_hash = cast(str, manifest["manifest_hash"])
    store = Store(store_root, cfg.fsync_every)
    merged = store.merge()
    ext_events = [r for r in merged if r.kind == "extension_event"]
    if extend:
        if any(r.seed_namespace == "eval" for r in merged):
            raise RuntimeError("--extend refused: eval-namespace records exist (pre-registration would be voided)")
        store.append(
            0,
            make_fan_record(
                kind="extension_event",
                episode_seed=cfg.run_seed,
                seed_namespace="train",
                split_role="train",
                pathology_id="all",
                fan_epoch=None,
                refan_k=None,
                schedule_id=make_schedule_id(cfg),
                policy_checkpoint_id=None,
                iteration=len(ext_events),  # derived from store state
                config_hash=config_hash(),
                frozen_block_hash=frozen_block_hash(cfg),
                manifest_hash=manifest_hash,
                common_future_hash="",
                host_init_hash="",
                env={},
                arms=[],
                telemetry=[],
                decisions=None,
                gate_results={"event": "extension", "n": extend},
            ),
        )
        store.close()
        store = Store(store_root, cfg.fsync_every)
        merged = store.merge()
        ext_events = [r for r in merged if r.kind == "extension_event"]
    extensions = 0
    for r in ext_events:
        n = (r.gate_results or {}).get("n")
        if isinstance(n, int):
            extensions += n
    targets = [derive(cfg.run_seed, "train", i) for i in range(cfg.n_collect + extensions)]
    if limit is not None:
        targets = targets[:limit]
    # Episode completeness is fan-level, not any-record-level: a crash between
    # an episode's two fans must resume the missing fan (existing fan_ids are
    # skipped inside run_collection_episode, so nothing is double-appended),
    # not silently drop it from the collection forever.
    fan_counts: dict[int, int] = {}
    voided: set[int] = set()
    existing_ids: set[str] = set()
    for r in merged:
        if r.seed_namespace != "train":
            continue
        existing_ids.add(r.fan_id)
        if r.kind == "fan":
            fan_counts[r.episode_seed] = fan_counts.get(r.episode_seed, 0) + 1
        elif r.kind == "void_event":
            voided.add(r.episode_seed)
    done = voided | {es for es, c in fan_counts.items() if c >= cfg.fans_per_episode}
    todo = [es for es in targets if es not in done]
    store.close()
    slots = [(d, w) for d in devices for w in range(n_workers_per_device)]
    statuses: dict[int, str] = {}
    halted = False
    if todo:
        ctx_mp = multiprocessing.get_context("spawn")
        halt = ctx_mp.Event()
        log_dir = str(Path(store_root) / "logs")
        procs = []
        for wid, (device, _w) in enumerate(slots):
            seeds = todo[wid :: len(slots)]
            p = ctx_mp.Process(
                target=worker_main,
                args=(
                    wid,
                    device,
                    cfg,
                    store_root,
                    seeds,
                    halt,
                    data_loader,
                    episode_runner,
                    manifest_hash,
                    len(slots),
                    log_dir,
                    frozenset(existing_ids),
                ),
            )
            p.start()
            procs.append(p)
        for p in procs:
            p.join()
        halted = halt.is_set()
        for wid, p in enumerate(procs):
            statuses[wid] = "crashed" if p.exitcode != 0 else ("halted" if halted else "clean")
    ok = not halted and all(s != "crashed" for s in statuses.values())
    return {"collected": len(todo), "workers": statuses, "halted": halted, "ok": ok}


# section 16 — TRAIN AND EVAL
AGREEMENT_MARGIN = semantic_const("AGREEMENT_MARGIN", 0.15)  # "+15 points (test units)", pre-registered
N_EVAL_REFANS = semantic_const("N_EVAL_REFANS", 30)  # ceiling estimate sample size

# Behavior-bearing: shapes comparator identities and the whole eval battery —
# on the semantic surface like its section-16 neighbours.
EVAL_COMPARATORS = semantic_const("EVAL_COMPARATORS", ("trained", "random", "schedule_only", "fixed_epoch"))


@semantic
def wilson_interval(k: int, n: int, alpha: float) -> tuple[float, float]:
    from statistics import NormalDist

    if n == 0:
        return (0.0, 1.0)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (center - half, center + half)


@semantic
def class_derangement(classes: list[str], seed: int) -> dict[str, str]:
    # Deterministic rotation by a seed-derived nonzero shift: always a
    # derangement (no class maps to itself), always a permutation.
    ordered = sorted(set(classes))
    n = len(ordered)
    if n < 2:
        raise ValueError("derangement needs >= 2 classes")
    shift = 1 + derive(seed, "derangement") % (n - 1)
    return {c: ordered[(ordered.index(c) + shift) % n] for c in ordered}


@semantic
def when_contrast(episodes: list[dict[str, object]]) -> dict[str, float | None]:
    # episodes carry the per-episode WHEN-contrast series in "lift"
    # (trained_live - fixed_epoch at eval) and trained-live's germination
    # flag. Unrestricted = mean over ALL episodes (a never-germinating
    # trained side contributes 0 - fixed_epoch's lift — the restraint
    # confound the spec names); restricted = mean over episodes where
    # trained-live germinated.
    if not episodes:
        return {"unrestricted_mean": 0.0, "restricted_mean": None, "germination_rate": 0.0}
    lifts = [_as_float(e["lift"]) for e in episodes]
    germ = [bool(e["germinated"]) for e in episodes]
    acted = [lift for lift, g in zip(lifts, germ, strict=True) if g]
    return {
        "unrestricted_mean": sum(lifts) / len(episodes),
        # A conditional mean over zero acted episodes is UNDEFINED — None,
        # never a silent 0.0 (the germination_rate beside it disambiguates).
        "restricted_mean": sum(acted) / len(acted) if acted else None,
        "germination_rate": len(acted) / len(episodes),
    }


@semantic
def verdict(results: dict[str, object], cfg: Config) -> dict[str, bool]:
    # The five pre-registered booleans (spec: Pre-registered numbers). Pure.
    lift = cast(dict[str, object], results["lift"])
    agreement = cast(dict[str, object], results["agreement"])
    money = cast(dict[str, object], results["money_chart"])
    falsifier = cast(dict[str, object], results["falsifier"])
    return {
        "lift_positive": _as_float(lift["trained_mean"]) > 0 and _as_float(lift["trained_p"]) < cfg.alpha_level,
        "beats_schedule_only": _as_float(lift["paired_vs_schedule_only_p"]) < cfg.alpha_level,
        "agreement_beats_null": _as_float(agreement["teacher_forced"]) >= _as_float(agreement["majority_null"]) + AGREEMENT_MARGIN,
        "money_chart": int(_as_float(money["matched"])) >= 3 and _as_float(money["p"]) < cfg.alpha_level,
        "falsifier_collapses": _as_float(falsifier["deranged_agreement"]) <= _as_float(falsifier["null_ci_hi"]),
    }


@semantic
def _recorded_extensions(merged: list[FanRecord]) -> int:
    total = 0
    for r in merged:
        if r.kind == "extension_event":
            n = (r.gate_results or {}).get("n")
            if isinstance(n, int):
                total += n
    return total


@semantic
def run_train(cfg: Config, store_root: str) -> dict[str, object]:
    root = Path(store_root)
    manifest = json.loads((root / "frozen.json").read_text(encoding="utf-8"))
    if manifest["frozen_block_hash"] != frozen_block_hash(cfg) or manifest["config_hash"] != config_hash():
        raise RuntimeError("train refused: manifest mismatch (live Config/source differ from frozen.json)")
    store = Store(store_root, cfg.fsync_every)
    records = load_for_training(store)
    normalizer = Normalizer.from_json(json.dumps(manifest["normalizer"]))
    frozen_density = cast(dict[str, float], manifest["fan_density"])
    # Calibration (normalizer, fan_density, betas) is read from frozen.json;
    # the records are read from the append-only shard store. Those are two
    # independent reads of a mutable file and an immutable log, and nothing
    # upstream ties them together: the manifest check above compares the
    # manifest to the LIVE cfg/source, and load_for_training filters on
    # split_role/kind only. freeze_manifest overwrites frozen.json in place,
    # so a re-freeze silently re-points calibration at a new generation while
    # the records keep their old stamp. Refuse rather than train a policy
    # under one generation's feature scaling on another generation's data.
    manifest_gen = cast(str, manifest["manifest_hash"])
    # None is included deliberately: a pre-freeze record reaching the training
    # split is the same defect wearing a different value, and must not sort
    # itself out of the refusal.
    stale = sorted({str(r.manifest_hash) for r in records if r.manifest_hash != manifest_gen})
    if stale:
        raise RuntimeError(
            f"train refused: records carry superseded manifest generations {stale} but frozen.json is "
            f"{manifest_gen[:12]} — re-collect under the current manifest, or restore the matching frozen.json"
        )
    # Betas come from the MANIFEST density; the collection recomputation is a
    # printed diagnostic only — asserted unused by construction (train_policy
    # receives frozen_density, never `records`-derived density).
    print(f"collection-density diagnostic (UNUSED for betas): {measure_fan_density(records)}")
    assert abs(cast(float, manifest["beta_which"]) - cfg.beta_which_frac * frozen_density["best_minus_second"]) < 1e-9
    assert abs(cast(float, manifest["beta_now"]) - frozen_density["best_minus_noop"] / cfg.beta_now_div) < 1e-9
    pol_dir = root / "policies"
    pol_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, object] = {}
    for name, mask_fn in (("trained", None), ("schedule_only", schedule_only_mask)):
        gen = make_generator(derive(cfg.run_seed, "policy", name))
        # Deliberate: the policy trains on CPU (deterministic per env_block's
        # recorded thread count) and is moved to CUDA only at eval — benign at
        # d_model=64; the env pins make any numerics drift refusable.
        policy, info = train_policy(records, cfg, normalizer, gen, frozen_density=frozen_density, mask_fn=mask_fn)
        ckpt_id = state_hash(policy)  # checkpoints keyed by state-dict hash
        torch.save(policy.state_dict(), pol_dir / f"{name}_{ckpt_id}.pt")
        (pol_dir / f"{name}.json").write_text(
            json.dumps({"checkpoint_id": ckpt_id, "beta_which": info["beta_which"], "beta_now": info["beta_now"], "curve": info["curve"]}),
            encoding="utf-8",
        )
        print(f"{name}: checkpoint {ckpt_id[:12]} tune curve {info['curve']}")
        out[name] = {"checkpoint_id": ckpt_id, "curve": info["curve"]}
    return out


@semantic
def _load_policy(cfg: Config, store_root: str, name: str) -> tuple[Policy, str]:
    root = Path(store_root) / "policies"
    meta = json.loads((root / f"{name}.json").read_text(encoding="utf-8"))
    policy = Policy(cfg, make_generator(0))
    policy.load_state_dict(torch.load(root / f"{name}_{meta['checkpoint_id']}.pt", weights_only=True))
    return policy, cast(str, meta["checkpoint_id"])


@semantic
def _query_dicts(policy: Policy, normalizer: Normalizer, tele: list[dict[str, object]], mask: bool) -> tuple[float, dict[str, float]]:
    vecs = [normalizer.apply(_telemetry_vector_from_dict(d)) for d in tele]
    tokens = torch.stack(vecs).unsqueeze(0).to(next(policy.parameters()).device)
    if mask:
        tokens = schedule_only_mask(tokens)
    prior = policy.training
    policy.eval()
    with torch.no_grad():
        p_logit, seed_logits = policy(tokens, torch.tensor([tokens.shape[1]]))
    policy.train(prior)
    # Check the LOGITS, exactly as decide_live does at its own forward — never
    # the squashed outputs. sigmoid(±inf) is 0.0/1.0 and softmax over a row
    # whose only non-finite entry is -inf is finite, so the old post-squash
    # check passed the one corruption it most needed to catch: an isolated
    # ±inf on now_head reads as confident restraint (p=0.0, lift exactly 0) or
    # confident germination on EVERY episode. NaN, and inf in the shared trunk
    # or on seed_head, do surface as NaN after squashing — but relying on that
    # left the now_head hole open, which is the silent-default class this
    # project exists to make unrepresentable.
    if not (torch.isfinite(p_logit).all() and torch.isfinite(seed_logits).all()):
        raise RuntimeError("_query_dicts: policy produced non-finite logits")
    p = float(torch.sigmoid(p_logit[0]))
    pi = torch.softmax(seed_logits[0], dim=-1)
    return p, {name: float(pi[i]) for i, name in enumerate(SEED_NAMES)}


@semantic
def _test_argmax(rec: FanRecord) -> str:
    by = _arm_by_name(rec)
    best_name, best_r = SEED_NAMES[0], float("-inf")
    for n in SEED_NAMES:
        r = _as_float(by[n]["r_test"])
        if r > best_r:
            best_r, best_name = r, n
    return best_name


@semantic
def _pi_argmax(pi: dict[str, float]) -> str:
    # Deterministic tie-break: LOWEST INDEX in SEED_NAMES order — the same
    # rule decide_live implements and tests pin ("norm" before "attn");
    # min() over names was a different (alphabetical) rule.
    best = max(pi.values())
    return next(n for n in SEED_NAMES if pi[n] == best)


@semantic
def run_eval(
    cfg: Config, data: DataBundle, device: str, store_root: str, resume: bool = False, void_prereg: bool = False
) -> dict[str, object]:
    root = Path(store_root)
    results_path = root / "eval_results.json"
    store = Store(store_root, cfg.fsync_every)
    if results_path.exists():
        if not void_prereg:
            raise RuntimeError(
                "eval refused: eval_results.json exists (one-shot). --void-preregistration overrides AND writes a permanent void_event."
            )
        merged0 = store.merge()
        store.append(
            0,
            make_fan_record(
                kind="void_event",
                episode_seed=cfg.run_seed,
                seed_namespace="eval",
                split_role="eval",
                pathology_id="all",
                fan_epoch=None,
                refan_k=None,
                schedule_id=make_schedule_id(cfg),
                policy_checkpoint_id=None,
                iteration=len([r for r in merged0 if r.kind == "void_event"]),
                config_hash=config_hash(),
                frozen_block_hash=frozen_block_hash(cfg),
                manifest_hash=None,
                common_future_hash="",
                host_init_hash="",
                env={"git_rev": _git_rev()},
                arms=[],
                telemetry=[],
                decisions=None,
                gate_results={"event": "void_preregistration"},
            ),
        )
    manifest = json.loads((root / "frozen.json").read_text(encoding="utf-8"))
    if manifest["frozen_block_hash"] != frozen_block_hash(cfg) or manifest["config_hash"] != config_hash():
        raise RuntimeError("eval refused: manifest mismatch (live Config/source differ from frozen.json)")
    if manifest["n_train"] not in (None, int(data.train_x.shape[0])):
        # Tier-1 read (ADR-0015): a missing key is corruption, and this guard
        # protects the ONE-SHOT eval — `.get()` let an absent key wave it through.
        # A --subset eval against a full-data manifest (or vice versa) would
        # burn the one-shot on the wrong data — refuse before anything runs.
        raise RuntimeError(f"eval refused: n_train mismatch (manifest {manifest.get('n_train')}, live {int(data.train_x.shape[0])})")
    manifest_hash = cast(str, manifest["manifest_hash"])
    merged = store.merge()
    # A base divergence before the first fan epoch legitimately yields a
    # void_event-only episode; it counts as COLLECTED (complete history —
    # the episode was processed and its outcome recorded). Counting only
    # kind=="fan" made eval permanently unreachable after any such episode,
    # since --extend raises `required` by the same n.
    # Fan-level completeness, mirroring collect's done-set: an episode counts
    # only when voided OR carrying its full fan complement — episode-presence
    # alone would silently accept a half-collected episode (crash between the
    # two fan appends + operator never re-running collect).
    tr_fan_counts: dict[int, int] = {}
    tr_voided: set[int] = set()
    for r in merged:
        if r.seed_namespace != "train":
            continue
        if r.kind == "fan":
            tr_fan_counts[r.episode_seed] = tr_fan_counts.get(r.episode_seed, 0) + 1
        elif r.kind == "void_event":
            tr_voided.add(r.episode_seed)
    train_eps = tr_voided | {es for es, c in tr_fan_counts.items() if c >= cfg.fans_per_episode}
    required = cfg.n_collect + _recorded_extensions(merged)
    if len(train_eps) < required:
        raise RuntimeError(f"eval refused: incomplete collection ({len(train_eps)} train episodes < {required})")
    normalizer = Normalizer.from_json(json.dumps(manifest["normalizer"]))
    trained_pol, trained_id = _load_policy(cfg, store_root, "trained")
    sched_pol, sched_id = _load_policy(cfg, store_root, "schedule_only")
    trained_pol.to(device)
    sched_pol.to(device)
    existing = {r.fan_id for r in merged}  # crash-resume: completed, never double-counted
    lo, hi = cfg.window
    per_comp: dict[str, list[dict[str, object]]] = {c: [] for c in EVAL_COMPARATORS}
    comp_ckpt = {
        "trained": f"trained:{trained_id}",
        "random": "random-null",
        "schedule_only": f"schedule_only:{sched_id}",
        "fixed_epoch": f"fixed_epoch:{trained_id}",
    }
    for i in range(cfg.n_eval):
        es = derive(cfg.run_seed, "eval", i)
        needed = [c for c in EVAL_COMPARATORS if fan_identity(es, None, "policy_run", None, comp_ckpt[c], None) not in existing]
        r_noop_test: float | None = None
        noop_init: str | None = None
        if needed:
            noop_ctx = make_episode(cfg, data, device, es, read_test=True)
            # lift = r_test - r_noop_test is only a counterfactual if both arms
            # started from the SAME host. The fan path gets that structurally
            # (run_fan hands every arm one snap object) and audits it with the
            # twin; the lift path reconstructs two hosts from one seed and, up
            # to now, only assumed they matched. build_host's scoped generator
            # makes the assumption true today — so check it rather than trust
            # it, and find out the epoch it stops being true.
            noop_init = state_hash(noop_ctx.host)
            try:
                for e in range(cfg.horizon):
                    train_one_epoch(noop_ctx, e)
                assert noop_ctx.curves_test is not None
                r_noop_test = end_state_R(noop_ctx.curves_test)
            except TelemetryDivergence:
                r_noop_test = cfg.diverged_r
        for comp in EVAL_COMPARATORS:
            fid = fan_identity(es, None, "policy_run", None, comp_ckpt[comp], None)
            if fid in existing:
                rec = next(r for r in merged if r.fan_id == fid)
                # Loud on a malformed record: silently defaulting a missing
                # summary to "never germinated, lift 0" is the silent-zero scar.
                if not rec.decisions:
                    raise RuntimeError(f"policy_run {fid} has no decisions payload — corrupt record, refusing to resume")
                summary = rec.decisions[-1]
                for key in ("germination_epoch", "lift", "chosen"):
                    if key not in summary:
                        raise RuntimeError(f"policy_run {fid} summary missing {key!r} — corrupt record, refusing to resume")
                per_comp[comp].append(
                    {
                        "episode_seed": es,
                        "germinated": summary["germination_epoch"] is not None,
                        "lift": _as_float(summary["lift"]),
                        "chosen": summary["chosen"],
                    }
                )
                continue
            assert r_noop_test is not None
            ctx = make_episode(cfg, data, device, es, read_test=True)
            # Capture host identity HERE, mirroring run_collection_episode's
            # `host_init = state_hash(ctx.host)` immediately after make_episode.
            # It cannot be taken at the append site below: by then ctx.host has
            # run cfg.horizon epochs and may carry a germinated seed, so the
            # hash would name the final state, not the start the lift is
            # measured from.
            host_init = state_hash(ctx.host)
            if noop_init is not None and host_init != noop_init:
                # RuntimeError, not assert: -O must not be able to disable the
                # one check standing between a mismatched pair and a lift
                # number that looks perfectly ordinary.
                raise RuntimeError(
                    f"eval refused: comparator {comp!r} episode {es} started from a different host than its "
                    f"no-op baseline ({host_init[:12]} vs {noop_init[:12]}) — lift would not be a counterfactual"
                )
            decisions: list[dict[str, object]] = []
            germination_epoch: int | None = None
            chosen: str | None = None
            status = "ok"
            rnd_epoch = lo + derive(es, "random-null") % (hi - lo + 1)
            rnd_seed = SEED_NAMES[derive(es, "random-null", "seed") % 4]
            try:
                for e in range(cfg.horizon):
                    if germination_epoch is None and lo <= e <= hi:
                        p = 0.0
                        fire = False
                        action: str | None = None
                        if comp == "random":
                            fire = e == rnd_epoch  # uniform epoch in window, uniform seed, always acts
                            p = 1.0 if fire else 0.0
                            action = rnd_seed if fire else None
                        elif comp == "fixed_epoch":
                            fire = e == cfg.t_star  # trained WHICH forced at t_star
                            if fire:
                                p, pi = _query_dicts(trained_pol, normalizer, [dataclasses.asdict(t) for t in ctx.telemetry], False)
                                action = _pi_argmax(pi)
                        else:
                            pol = trained_pol if comp == "trained" else sched_pol
                            mask = comp == "schedule_only"
                            p, pi = _query_dicts(pol, normalizer, [dataclasses.asdict(t) for t in ctx.telemetry], mask)
                            # Deterministic deployment rule — the inline twin of
                            # the unit-tested decide_live (p > 0.5, tie-break =
                            # lowest SEED_NAMES index via _pi_argmax). Keep the
                            # two in lockstep: decide_live is the tested owner.
                            fire = p > 0.5
                            action = _pi_argmax(pi) if fire else None
                        decisions.append({"epoch": e, "p": p, "action": action})
                        if fire and action is not None:
                            germinate(ctx, action)
                            germination_epoch = e
                            chosen = action
                    train_one_epoch(ctx, e)
                assert ctx.curves_test is not None
                r_test = end_state_R(ctx.curves_test)
                r_val = end_state_R(ctx.curves_val)
            except TelemetryDivergence:
                status = "diverged"
                r_test = cfg.diverged_r
                r_val = cfg.diverged_r
            lift = (r_test - r_noop_test) if germination_epoch is not None else 0.0  # never-germinate = 0
            decisions.append({"germination_epoch": germination_epoch, "chosen": chosen, "lift": lift, "r_noop_test": r_noop_test})
            store.append(
                0,
                make_fan_record(
                    kind="policy_run",
                    episode_seed=es,
                    seed_namespace="eval",
                    split_role="eval",
                    pathology_id=ctx.pathology,
                    fan_epoch=None,
                    refan_k=None,
                    schedule_id=make_schedule_id(cfg),
                    policy_checkpoint_id=comp_ckpt[comp],
                    iteration=None,
                    config_hash=config_hash(),
                    frozen_block_hash=frozen_block_hash(cfg),
                    manifest_hash=manifest_hash,
                    common_future_hash=ctx.future.hash,
                    host_init_hash=host_init,
                    env=env_block(device, 1),
                    arms=[{"name": chosen or "noop", "status": status, "r_val": r_val, "r_test": r_test}],
                    telemetry=[dataclasses.asdict(t) for t in ctx.telemetry],
                    decisions=decisions,
                    gate_results=None,
                ),
            )
            per_comp[comp].append({"episode_seed": es, "germinated": germination_epoch is not None, "lift": lift, "chosen": chosen})
        # frozen grid: 2 forced fans per eval episode at evalgrid-drawn epochs.
        # Resume is per-fan (skip_fan_ids), not per-episode: re-running a
        # partially-recorded episode without the skip set would append a
        # duplicate fan_id and fail every later merge().
        grid_epochs = draw_schedule(es, cfg, "evalgrid")
        grid_missing = [fe for fe in grid_epochs if fan_identity(es, fe, "fan", None, None, None) not in existing]
        base_voided = fan_identity(es, None, "void_event", None, None, None) in existing
        if grid_missing and not base_voided:
            try:
                run_collection_episode(
                    cfg,
                    data,
                    device,
                    es,
                    "eval",
                    store,
                    0,
                    True,
                    manifest_hash=manifest_hash,
                    schedule_label="evalgrid",
                    skip_fan_ids=frozenset(existing),
                )
            except TwinDivergence as td:
                # Same localisation artifact worker_main writes on twin abort.
                write_divergence_report(store_root, cfg, es, "noop", td.first_bad_epoch, manifest_hash, device, 1)
                raise
        refan_done = (
            fan_identity(es, grid_epochs[0], "refan", 0, None, None) in existing
            or fan_identity(es, grid_epochs[0], "void_event", 0, None, None) in existing  # diverged base, already voided
        )
        if i < N_EVAL_REFANS and not refan_done:
            run_refan(cfg, data, device, es, grid_epochs[0], 0, store, 0, namespace="eval", read_test=True, manifest_hash=manifest_hash)
    store.close()
    merged = Store(store_root, cfg.fsync_every).merge()
    grid = [r for r in merged if r.kind == "fan" and r.seed_namespace == "eval"]
    eval_refans = [r for r in merged if r.kind == "refan" and r.seed_namespace == "eval"]
    # teacher-forced agreement on the grid, vs majority-class and schedule-only nulls
    hits = 0
    sched_hits = 0
    picks: list[str] = []
    paths: list[str] = []
    ep_ids: list[int] = []
    per_point: list[dict[str, float]] = []
    argmaxes: list[str] = []
    for g in grid:
        am = _test_argmax(g)
        argmaxes.append(am)
        paths.append(g.pathology_id)
        ep_ids.append(g.episode_seed)
        p_g, pi_g = _query_dicts(trained_pol, normalizer, g.telemetry, False)
        pick = _pi_argmax(pi_g)
        picks.append(pick)
        hits += pick == am
        _p_s, pi_s = _query_dicts(sched_pol, normalizer, g.telemetry, True)
        sched_hits += _pi_argmax(pi_s) == am
        by = _arm_by_name(g)
        advantage = max(_as_float(by[n]["r_test"]) for n in SEED_NAMES) - _as_float(by["noop"]["r_test"])
        per_point.append({"p": p_g, "A": advantage})  # the realized-p-by-sign(A) diagnostic's data
    n_grid = len(grid)
    agreement = hits / n_grid if n_grid else 0.0
    sched_null = sched_hits / n_grid if n_grid else 0.0
    majority_null = (max(argmaxes.count(n) for n in SEED_NAMES) / n_grid) if n_grid else 0.0
    # falsifier: telemetry-history derangement across pathology classes
    mapping = class_derangement(list(PATHOLOGIES), cfg.run_seed)
    donors: dict[str, list[FanRecord]] = {}
    for g in sorted(grid, key=lambda r: r.fan_id):
        donors.setdefault(g.pathology_id, []).append(g)
    deranged_hits = 0
    deranged_n = 0
    for g in sorted(grid, key=lambda r: r.fan_id):
        pool = donors.get(mapping[g.pathology_id], [])
        if not pool:
            continue
        donor = pool[deranged_n % len(pool)]
        _p, pi_d = _query_dicts(trained_pol, normalizer, donor.telemetry, False)
        deranged_hits += _pi_argmax(pi_d) == _test_argmax(g)
        deranged_n += 1
    deranged_agreement = deranged_hits / deranged_n if deranged_n else 0.0
    # Falsifier null CI at the EPISODE count, not the grid-point count (spec
    # rev 6.1): the 2-per-episode clustering means n_grid points carry only
    # n_episodes' worth of independent information — a point-count CI is too
    # tight and the falsifier gate would be miscalibrated-strict.
    n_units = len({r.episode_seed for r in grid})
    null_ci = wilson_interval(round(majority_null * n_units), n_units, cfg.alpha_level) if n_units else (0.0, 1.0)
    # ceiling: refan-vs-fan argmax stability, Sum p^2 estimator (labeled lower bound)
    matches = 0
    pairs = 0
    for rf in eval_refans:
        twin_fan = next((g for g in grid if g.episode_seed == rf.episode_seed and g.fan_epoch == rf.fan_epoch), None)
        if twin_fan is None:
            continue
        matches += _test_argmax(rf) == _test_argmax(twin_fan)
        pairs += 1
    ceiling = matches / pairs if pairs else 0.0
    ceiling_ci = wilson_interval(matches, pairs, cfg.alpha_level) if pairs else (0.0, 1.0)
    # statistics
    trained_lifts = torch.tensor([_as_float(e["lift"]) for e in per_comp["trained"]], dtype=torch.float64)
    sched_lifts = torch.tensor([_as_float(e["lift"]) for e in per_comp["schedule_only"]], dtype=torch.float64)
    trained_p = sign_flip_pvalue(trained_lifts, cfg.permutation_resamples, derive(cfg.run_seed, "signflip-trained"))
    paired_p = sign_flip_pvalue(trained_lifts - sched_lifts, cfg.permutation_resamples, derive(cfg.run_seed, "signflip-paired"))
    obs_matched, money_p = money_chart_permutation_pvalue(
        paths, picks, ep_ids, dict(DESIGNED_WINNER), cfg.permutation_resamples, derive(cfg.run_seed, "money")
    )
    # Diverged-excluded companion (spec: report) — the money chart recomputed
    # on grid fans where all four seed arms finished, showing whether the
    # diagonal is driven by diagnosis or by divergence-avoidance.
    keep = [i for i, g in enumerate(grid) if all(str(_arm_by_name(g)[n]["status"]) == "ok" for n in SEED_NAMES)]
    if keep:
        nd_matched, nd_p = money_chart_permutation_pvalue(
            [paths[i] for i in keep],
            [picks[i] for i in keep],
            [ep_ids[i] for i in keep],
            dict(DESIGNED_WINNER),
            cfg.permutation_resamples,
            derive(cfg.run_seed, "money-nodiv"),
        )
    else:
        nd_matched, nd_p = 0, 1.0
    # restraint regret: what never-germinating left on the table. Headline =
    # the episode's LAST grid point; the spec ALSO requires every grid point
    # reported separately, labeled as containing option value.
    regrets: list[float] = []
    regret_grid_points: list[dict[str, object]] = []
    for e_summary in per_comp["trained"]:
        if e_summary["germinated"]:
            continue
        es_r = cast(int, e_summary["episode_seed"])
        ep_grid = [g for g in grid if g.episode_seed == es_r]
        if not ep_grid:
            continue
        for g_rec in ep_grid:
            by_g = _arm_by_name(g_rec)
            regret_grid_points.append(
                {
                    "episode_seed": es_r,
                    "fan_epoch": g_rec.fan_epoch,
                    "regret": max(0.0, max(_as_float(by_g[n]["r_test"]) for n in SEED_NAMES) - _as_float(by_g["noop"]["r_test"])),
                }
            )
        last = max(ep_grid, key=lambda g: g.fan_epoch or 0)
        by = _arm_by_name(last)
        # Regret vs fan-optimal-WITH-no-op: when no-op is the fan optimum,
        # never-germinating left nothing on the table — regret 0, never
        # negative (a negative entry would credit restraint instead of
        # measuring what it cost).
        regrets.append(max(0.0, max(_as_float(by[n]["r_test"]) for n in SEED_NAMES) - _as_float(by["noop"]["r_test"])))
    chosen_marginal: dict[str, int] = {}
    for e_summary in per_comp["trained"]:
        c = e_summary.get("chosen")
        if isinstance(c, str):
            chosen_marginal[c] = chosen_marginal.get(c, 0) + 1
    # Gate 3's paired refan noise floor (all keys carry the same value); a
    # frozen manifest always has it — freeze refuses on any failed gate, and
    # a passing gate3 recorded its floor. KeyError here is loud, as intended.
    g3_detail = cast(dict[str, object], cast(dict[str, dict[str, object]], manifest["gate_results"])["gate3_contrast"]["detail"])
    sigma_r_floor = next(iter(cast(dict[str, float], g3_detail["floor"]).values()))
    # The WHEN contrast is trained_live - fixed_epoch per episode (spec),
    # paired by eval seed — NOT trained's own lift alone.
    when_eps: list[dict[str, object]] = [
        {"germinated": t["germinated"], "lift": _as_float(t["lift"]) - _as_float(f["lift"])}
        for t, f in zip(per_comp["trained"], per_comp["fixed_epoch"], strict=True)
    ]
    z_power = 1.645 + 0.842  # one-sided alpha=0.05, power 0.8
    results: dict[str, object] = {
        "manifest_hash": manifest_hash,
        "lift": {
            "trained_mean": float(trained_lifts.mean()) if trained_lifts.numel() else 0.0,
            "trained_p": trained_p,
            "paired_vs_schedule_only_p": paired_p,
            "per_comparator": {
                c: {
                    "mean_lift": (sum(_as_float(e["lift"]) for e in v) / len(v)) if v else 0.0,
                    "germination_rate": (sum(1 for e in v if e["germinated"]) / len(v)) if v else 0.0,
                }
                for c, v in per_comp.items()
            },
        },
        "agreement": {"teacher_forced": agreement, "majority_null": majority_null, "schedule_only_null": sched_null},
        "money_chart": {
            "matched": obs_matched,
            "p": money_p,
            "excluding_diverged": {"matched": nd_matched, "p": nd_p, "n_points": len(keep)},
        },
        "falsifier": {"deranged_agreement": deranged_agreement, "null_ci_hi": null_ci[1], "derangement": mapping},
        "ceiling": {"estimate": ceiling, "wilson_ci": ceiling_ci, "pairs": pairs, "label": "lower bound, test units"},
        "when_contrast": when_contrast(when_eps),
        "restraint_regret": {
            "last_grid_point_mean": (sum(regrets) / len(regrets)) if regrets else 0.0,
            "last_grid_point": regrets,
            "per_grid_point": regret_grid_points,
            "label": "per-grid-point regret contains option value (a later grid point could still have acted)",
        },
        "chosen_seed_marginal": chosen_marginal,
        "per_grid_point": per_point,
        "power_note": {
            # MDE needs an SD, not a mean effect-size gap: gate 3's paired
            # refan floor is E|R - R'| for iid draws, so sd(R) = floor*sqrt(pi)/2.
            # A LOWER anchor — it carries future-resampling noise only.
            "mde_lift_at_n_eval": z_power * (sigma_r_floor * math.sqrt(math.pi) / 2.0) / (cfg.n_eval**0.5),
            # Episode count, not grid-point count (spec rev 6.1): the grid's
            # 2-per-episode clustering caps its independent information.
            "mde_agreement_at_grid": z_power * 0.5 / (cfg.n_eval**0.5),
            "density_source": "gate 3 refan noise floor (sd from E|R-R'|; lower anchor, future-resampling only)",
        },
    }
    results["verdict"] = verdict(results, cfg)
    tmp = results_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(results, indent=2), encoding="utf-8")
    os.replace(tmp, results_path)  # atomic
    return results


# section 17 — REPORT AND REPLAY
@semantic
def run_report(cfg: Config, store_root: str) -> dict[str, object]:
    root = Path(store_root)
    results = json.loads((root / "eval_results.json").read_text(encoding="utf-8"))
    store = Store(store_root, cfg.fsync_every)
    merged = store.merge()
    # D6: refuse mixed manifest_hash inside any single number.
    hashes = {r.manifest_hash for r in merged if r.seed_namespace == "eval" and r.manifest_hash is not None}
    if results.get("manifest_hash") is not None:
        hashes.add(results["manifest_hash"])
    if len(hashes) > 1:
        raise RuntimeError(f"report refused: mixed manifest_hash in a single number: {sorted(map(str, hashes))}")
    manifest_path = root / "frozen.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    fans = [r for r in merged if r.kind in ("fan", "refan")]
    # observed diverged-arm end-state accuracies, printed beside the 0.10
    # convention (the convention is a measurement claim, so the measurement is
    # shown); per-seed failure rates.
    diverged_end_states: list[float] = []
    seed_counts: dict[str, int] = dict.fromkeys(SEED_NAMES, 0)
    seed_failures: dict[str, int] = dict.fromkeys(SEED_NAMES, 0)
    g_values: dict[str, list[float]] = {n: [] for n in SEED_NAMES}
    g_horizon: dict[str, list[float]] = {n: [] for n in SEED_NAMES}
    rms_horizon: dict[str, list[float]] = {n: [] for n in SEED_NAMES}
    arm_seconds: dict[str, list[float]] = {n: [] for n in ("noop", *SEED_NAMES)}
    val_eq_test_hits = 0
    val_eq_test_n = 0

    def _num(a: dict[str, object], key: str) -> float | None:
        v = a.get(key)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    for r in fans:
        for a in r.arms:
            name = str(a["name"])
            if name in arm_seconds:
                w = _num(a, "wall_s")
                if w is not None:
                    arm_seconds[name].append(w)
            if name in seed_counts:
                for key, sink in (("g_at_horizon", g_horizon), ("rms_ratio_horizon", rms_horizon)):
                    hv = _num(a, key)
                    if hv is not None:
                        sink[name].append(hv)
                seed_counts[name] += 1
                gv = a.get("g_at_init")
                if isinstance(gv, (int, float)) and not isinstance(gv, bool):
                    g_values[name].append(float(gv))
                if a.get("status") == "diverged":
                    seed_failures[name] += 1
                    curve = a.get("curve_val")
                    if isinstance(curve, list) and curve:
                        last = curve[-1]
                        if isinstance(last, (int, float)):
                            diverged_end_states.append(float(last))
        if r.seed_namespace == "eval" and r.kind == "fan":
            by = _arm_by_name(r)
            if all(by[n].get("r_test") is not None for n in SEED_NAMES):
                val_best = max(SEED_NAMES, key=lambda n: _as_float(by[n]["r_val"]))
                val_eq_test_hits += val_best == _test_argmax(r)
                val_eq_test_n += 1
    per_grid = cast(list[dict[str, object]], results.get("per_grid_point", []))
    pos = [_as_float(pt["p"]) for pt in per_grid if _as_float(pt["A"]) > 0]
    neg = [_as_float(pt["p"]) for pt in per_grid if _as_float(pt["A"]) <= 0]
    report: dict[str, object] = {
        "manifest_hash": results.get("manifest_hash"),
        "lift_table": results["lift"],
        "agreement": {**cast(dict[str, object], results["agreement"]), "ceiling_as_context": results.get("ceiling")},
        "money_chart": results["money_chart"],
        "falsifier": results["falsifier"],
        "chosen_seed_marginal": results.get("chosen_seed_marginal", {}),
        "diverged_observed": {
            "convention_r": cfg.diverged_r,
            "observed_end_state_acc": diverged_end_states,
            "n": len(diverged_end_states),
        },
        "per_seed_failure_rates": {n: (seed_failures[n] / seed_counts[n] if seed_counts[n] else 0.0) for n in SEED_NAMES},
        # Spec report list: "RMS(Δ)/RMS(h) at blend entry + g at germination".
        "g_at_germination": {n: ({"mean": sum(v) / len(v), "min": min(v), "max": max(v)} if v else None) for n, v in g_values.items()},
        # rev 6.2: does an embodied graft's influence grow, hold or decay
        # under joint training? Beside g_at_germination, which is its birth
        # value. Absent measurements are absent, never zero.
        "influence_at_horizon": {
            n: (
                {
                    "g_mean": (sum(g_horizon[n]) / len(g_horizon[n])) if g_horizon[n] else None,
                    "rms_ratio_mean": (sum(rms_horizon[n]) / len(rms_horizon[n])) if rms_horizon[n] else None,
                    "n": len(g_horizon[n]),
                }
                if g_horizon[n] or rms_horizon[n]
                else None
            )
            for n in SEED_NAMES
        },
        # rev 6.2: the denominator of the supervision-economics claim — what
        # one counterfactual arm costs against the no-op it is compared to.
        "arm_cost_seconds": {n: ({"mean": sum(v) / len(v), "n": len(v)} if v else None) for n, v in arm_seconds.items()},
        "fan_density": manifest.get("fan_density"),
        "p_val_argmax_eq_test_argmax": (val_eq_test_hits / val_eq_test_n) if val_eq_test_n else None,
        "restraint_regret": results.get("restraint_regret"),
        "realized_p_by_sign": {
            "mean_p_when_A_positive": (sum(pos) / len(pos)) if pos else None,
            "mean_p_when_A_nonpositive": (sum(neg) / len(neg)) if neg else None,
            "n_positive": len(pos),
            "n_nonpositive": len(neg),
        },
        "when_contrast": results.get("when_contrast"),
        "temperatures_in_force": {"beta_which": manifest.get("beta_which"), "beta_now": manifest.get("beta_now")},
        "det_mode_cost": manifest.get("det_mode_cost"),
        "concurrency_factor": manifest.get("concurrency_factor"),
        "verdict": results.get("verdict"),
    }
    tune_path = root / "policies" / "trained.json"
    if tune_path.exists():
        report["tune_curve"] = json.loads(tune_path.read_text(encoding="utf-8")).get("curve")
    # Aligned tables (D4).
    lift = cast(dict[str, object], results["lift"])
    print(f"{'comparator':16s} {'mean lift':>10s} {'germ rate':>10s}")
    for comp, row in cast(dict[str, dict[str, float]], lift["per_comparator"]).items():
        print(f"{comp:16s} {row['mean_lift']:>10.4f} {row['germination_rate']:>10.2f}")
    ag = cast(dict[str, object], report["agreement"])
    print(
        f"{'agreement':16s} {_as_float(ag['teacher_forced']):>10.3f}  majority {_as_float(ag['majority_null']):.3f}  schedule-only {_as_float(ag['schedule_only_null']):.3f}"
    )
    mc = cast(dict[str, object], report["money_chart"])
    print(f"{'money chart':16s} matched {mc['matched']}/4  p={_as_float(mc['p']):.4f}")
    print(f"{'verdict':16s} {report['verdict']}")
    return report


@semantic
def run_replay(cfg: Config, fan_id: str, store_root: str, device: str) -> dict[str, object]:
    root = Path(store_root)
    store = Store(store_root, cfg.fsync_every)
    merged = store.merge()
    rec = next((r for r in merged if r.fan_id == fan_id), None)
    if rec is None:
        raise RuntimeError(f"replay refused: fan_id {fan_id} not found in the merged store")
    manifest_path = root / "frozen.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    # Replay runs single-worker, or at the recorded worker_count if the
    # manifest's gate-8 contingency fired (worker pressure changed the twin).
    worker_count = 1
    if manifest is not None:
        # Tier-1 reads (ADR-0015): frozen.json is optional for replay, but if it
        # EXISTS its keys are not. `.get("gate8_outcome") or {}` plus
        # `.get("ok", True)` meant a corrupt manifest silently replayed
        # single-worker — i.e. exactly the contingency path the gate-8 finding
        # exists to honour would have been skipped without a word.
        g8 = cast(dict[str, object], manifest["gate8_outcome"] or {})
        if g8 and not g8["ok"]:
            wc = rec.env["worker_count"]  # provenance the record always carries
            worker_count = wc if isinstance(wc, int) else 1
    live_env = env_block(device, worker_count)
    bad_env = [k for k in REPLAY_REFUSAL_KEYS if rec.env.get(k) != live_env.get(k)]
    if bad_env:
        raise RuntimeError(f"replay refused: env mismatch on {bad_env} (recorded vs live)")
    if rec.config_hash != config_hash():
        raise RuntimeError("replay refused: config_hash mismatch (live semantic surface differs from the record)")
    # Config is _NON_SEMANTIC, so a frozen-constant edit moves NEITHER hash
    # above — without this check it would masquerade as a KERNEL SELECTION
    # divergence below (config drift misattributed as GPU nondeterminism).
    if rec.frozen_block_hash != frozen_block_hash(cfg):
        raise RuntimeError("replay refused: frozen_block_hash mismatch (live Config differs from the record)")
    if manifest is not None and rec.manifest_hash is not None and rec.manifest_hash != manifest["manifest_hash"]:
        raise RuntimeError("replay refused: manifest_hash mismatch")
    if manifest is not None and manifest["data_split_id"] not in (None, data_split_id(cfg)):
        raise RuntimeError("replay refused: data_split_id mismatch (live run_seed/split differs from the manifest)")
    if rec.kind != "fan" or rec.fan_epoch is None:
        raise RuntimeError(f"replay supports kind='fan' records, got {rec.kind!r}")
    # Replay under the RECORDED observation mode: collection fans carry no
    # r_test (read_test=False), eval-grid fans do — inserting test-set passes
    # the original run never executed is a record/replay path asymmetry.
    read_test = any(a.get("r_test") is not None for a in rec.arms)
    data = load_data(cfg, device)
    if manifest is not None and manifest["n_train"] not in (None, int(data.train_x.shape[0])):
        raise RuntimeError("replay refused: n_train mismatch (record was collected against a different data size)")
    ctx = make_episode(cfg, data, device, rec.episode_seed, read_test=read_test)
    # Localisation anchors the record already carries: check the re-derived
    # inputs BEFORE blaming the kernel branch.
    if ctx.pathology != rec.pathology_id:
        raise RuntimeError("replay mismatch: diverged at PATHOLOGY DERIVATION (episode seed population moved)")
    if rec.common_future_hash and ctx.future.hash != rec.common_future_hash:
        raise RuntimeError("replay mismatch: diverged at FUTURE DERIVATION (common_future_hash differs)")
    live_init = state_hash(ctx.host)
    if live_init != rec.host_init_hash:
        # Localisation: the host was wrong before any kernel ran.
        raise RuntimeError("replay mismatch: diverged at SEEDING (host_init_hash differs)")
    trace = run_base(ctx, cfg, fan_epochs=(rec.fan_epoch,))
    snap = trace.snapshots[rec.fan_epoch]
    include_nullseed = any(a["name"] == "nullseed" for a in rec.arms)
    arms, _meta = run_fan(
        cfg, data, device, rec.episode_seed, ctx.pathology, ctx.future, snap, trace, read_test, include_nullseed=include_nullseed
    )
    recorded = {str(a["name"]): a for a in rec.arms}
    # A status flip (recorded ok, replays diverged — or vice versa) is the
    # STRONGEST replay divergence: nondeterminism changed whether an arm
    # NaN'd. Check it before the value comparison, which only sees ok/ok.
    flipped = [a.name for a in arms if a.name in recorded and a.status != recorded[a.name].get("status")]
    if flipped:
        raise RuntimeError(f"replay mismatch: arm STATUS flipped (ok<->diverged) for {flipped}")
    # Value comparison is on r_val ONLY. The rev-6.2 provenance fields
    # (wall_s, peak_mem_bytes) differ between record and replay by
    # construction and are never replay comparands.
    mismatched = [
        a.name
        for a in arms
        if a.name in recorded
        and a.status == "ok"
        and recorded[a.name].get("status") == "ok"
        and a.r_val != _as_float(recorded[a.name]["r_val"])
    ]
    if mismatched:
        # Seeding + anchors verified above, so the divergence is in the branch.
        raise RuntimeError(f"replay mismatch: diverged at KERNEL SELECTION for arms {mismatched}")
    return {"fan_id": fan_id, "ok": True, "arms_verified": [a.name for a in arms if a.status == "ok"]}


def main(argv: list[str] | None = None) -> None:
    enable_class1()  # MUST be the first statement of every process
    ap = argparse.ArgumentParser(prog="kernel_demo")
    sub = ap.add_subparsers(dest="mode", required=True)
    for m in MODES:
        p = sub.add_parser(m)
        p.add_argument("--store", default="runs/kernel_demo")
        p.add_argument("--device", default="cuda:0")
        if m in ("preflight", "eval"):
            # Dev-speed flag ONLY where it is honored — a flag that parses
            # everywhere but is silently ignored (collect, replay) is the scar.
            p.add_argument("--subset", type=int, default=None)
        if m == "selftest":
            p.add_argument("--certify", action="store_true")
        if m == "preflight":
            p.add_argument("--freeze", action="store_true")
            # Gate 8 must pressure-test the concurrency collect will actually
            # run (collect's per-device default), not a hardcoded stand-in.
            p.add_argument("--workers", type=int, default=6)
        if m == "collect":
            p.add_argument("--devices", default="cuda:0")
            p.add_argument("--workers", type=int, default=6)
            p.add_argument("--limit", type=int, default=None)
            p.add_argument("--extend", type=int, default=0)
        if m == "eval":
            p.add_argument("--resume-eval", action="store_true")
            p.add_argument("--void-preregistration", action="store_true")
        if m == "replay":
            p.add_argument("fan_id")
    args = ap.parse_args(argv)
    cfg = Config()
    if args.mode == "selftest":
        result = run_selftest(cfg, args.device, certify=args.certify, store_root=args.store)
        for name, step in cast(dict[str, dict[str, object]], result["steps"]).items():
            print(f"{name:28s} {step['status']}")
        raise SystemExit(0 if result["ok"] else 1)
    if args.mode == "preflight":
        data = load_data(cfg, args.device, args.subset)
        out = run_preflight(cfg, data, args.device, args.store, freeze=args.freeze, gate8_workers=args.workers)
        raise SystemExit(0 if dataclass_gates_ok(cast(dict[str, dict[str, object]], out["gates"])) else 1)
    if args.mode == "collect":
        result_c = run_collect(cfg, args.store, args.devices.split(","), args.workers, limit=args.limit, extend=args.extend)
        print(result_c)
        raise SystemExit(0 if result_c["ok"] else 1)
    if args.mode == "train":
        print(run_train(cfg, args.store))
        raise SystemExit(0)
    if args.mode == "eval":
        data = load_data(cfg, args.device, args.subset)
        result_e = run_eval(cfg, data, args.device, args.store, resume=args.resume_eval, void_prereg=args.void_preregistration)
        print(json.dumps(result_e.get("verdict"), indent=2))
        raise SystemExit(0)
    if args.mode == "report":
        run_report(cfg, args.store)
        raise SystemExit(0)
    if args.mode == "replay":
        print(run_replay(cfg, args.fan_id, args.store, args.device))
        raise SystemExit(0)
    raise SystemExit(f"not implemented: {args.mode}")


if __name__ == "__main__":
    main()
