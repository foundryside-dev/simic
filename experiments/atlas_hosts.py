"""Atlas hosts (PDR-0057 G0 item 6): uniform scale-up of each pathology, and an unimpaired reference.

`kernel_demo.Host` is @semantic and is not edited. This module rebuilds the same wiring from an
explicit config, so a host's shape is data rather than code:
- at scale 1 every pathology equals the kernel host bitwise, initial draw included
  (`tests/unit/test_atlas_hosts.py`);
- `reference` is the unimpaired host every pathology departs from: BN, 3x3, widths 24/64/80;
- `scaled_config(name, m)` widens every stage by one factor so the parameter count is about m times
  the base, keeping the pathology (BN or not, init gain, stage-2 kernel, the starved middle ratio).

Scaled hosts are no-growth comparators: they carry no slot, so their stage-2 width may move.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass

from torch import nn

from experiments.kernel_demo import PATHOLOGIES, Host, make_generator, rng_scope

WIDTH_STEP = 4  # widths move in multiples of 4: the base widths (20, 24, 64, 72, 80) are all multiples
NAMES = (*PATHOLOGIES, "reference")


@dataclass(frozen=True)
class HostConfig:
    name: str
    w1: int
    w2: int
    w3: int
    s2_mid: int
    use_bn: bool
    gain: float
    s2_kernel: int


def base_config(name: str) -> HostConfig:
    """The kernel's wiring rules (`kernel_demo.Host.__init__`), plus the unimpaired reference."""
    if name not in NAMES:
        raise ValueError(f"unknown host: {name}; expected one of {NAMES}")
    w1, w2, w3 = (20, 64, 72) if name == "mild" else (24, 64, 80)
    return HostConfig(
        name=name,
        w1=w1,
        w2=w2,
        w3=w3,
        s2_mid=24 if name == "channel_starved" else w2,
        use_bn=name != "under_normalized",
        gain=2.0 if name == "under_normalized" else 1.0,
        s2_kernel=1 if name == "no_spatial_mix" else 3,
    )


class AtlasHost(Host):
    """`kernel_demo.Host` built from a config. Reuses the kernel's stage builder and forward."""

    def __init__(self, cfg: HostConfig) -> None:
        nn.Module.__init__(self)  # Host.__init__ hard-codes the kernel's widths; build from the config instead
        self.pathology = cfg.name
        self.config = cfg
        pad = 0 if cfg.s2_kernel == 1 else 1
        self.stage1 = self._make_stage(3, cfg.w1, cfg.w1, 3, 1, cfg.use_bn, cfg.gain)
        self.stage2 = self._make_stage(cfg.w1, cfg.s2_mid, cfg.w2, cfg.s2_kernel, pad, cfg.use_bn, cfg.gain)
        self.stage3 = self._make_stage(cfg.w2, cfg.w3, cfg.w3, 3, 1, cfg.use_bn, cfg.gain)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(cfg.w3, 10)
        self.feat_channels = cfg.w2
        self.stage_stats: dict[str, list[float]] = {}


def build(cfg: HostConfig, init_seed: int) -> AtlasHost:
    """Construction in the kernel's RNG scope, so scale 1 draws the kernel host's exact weights."""
    with rng_scope(make_generator(init_seed)):
        return AtlasHost(cfg)


def parameter_count(cfg: HostConfig) -> int:
    def stage(cin: int, mid: int, out: int, k: int) -> int:
        bn = 2 * (mid + out) if cfg.use_bn else 0
        return cin * mid * k * k + mid * out * k * k + bn

    return (
        stage(3, cfg.w1, cfg.w1, 3) + stage(cfg.w1, cfg.s2_mid, cfg.w2, cfg.s2_kernel) + stage(cfg.w2, cfg.w3, cfg.w3, 3) + cfg.w3 * 10 + 10
    )


def parameter_multiple(cfg: HostConfig, base: HostConfig) -> float:
    return parameter_count(cfg) / parameter_count(base)


def _round(width: float) -> int:
    return max(WIDTH_STEP, round(width / WIDTH_STEP) * WIDTH_STEP)


def scaled_config(name: str, target: float) -> HostConfig:
    """Widen every stage by one factor so the parameter multiple is as close to `target` as widths allow."""
    if not 1.0 < target <= 4.0:
        raise ValueError("target parameter multiple must lie in (1, 4]")
    base = base_config(name)
    best: HostConfig | None = None
    for step in range(1, 2001):  # factor 1.0005 .. 2.0 in fine steps; deterministic
        k = 1 + step / 2000
        cfg = dataclasses.replace(
            base,
            name=f"{name}@x{target:g}",
            w1=_round(base.w1 * k),
            w2=_round(base.w2 * k),
            w3=_round(base.w3 * k),
            s2_mid=_round(base.s2_mid * k),
        )
        if best is None or abs(parameter_multiple(cfg, base) - target) < abs(parameter_multiple(best, base) - target):
            best = cfg
    assert best is not None
    return best


def config_hash(cfg: HostConfig) -> str:
    return hashlib.sha256(json.dumps(dataclasses.asdict(cfg), sort_keys=True).encode()).hexdigest()
