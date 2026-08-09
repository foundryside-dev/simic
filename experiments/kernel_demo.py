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
import copy
import enum
import hashlib
import inspect
import math
import os
import platform
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn

SCHEMA_VERSION = 1

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
    tune_frac: float = 0.2
    batch_size: int = 128
    eval_chunk: int = 1000  # plan-authored
    fsync_every: int = 20  # plan-authored durability cadence
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
        sat = ctx.host.stage_stats.get("saturation", [0.0, 0.0, 0.0])
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
