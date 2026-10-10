"""Atlas telemetry (PDR-0057 G0 item 7; Nissa's role, experiment grade): pre-decision features.

Read at a decision point t, before anything is decided there:
- trunk features, from the no-growth trunk's records for epochs before t (free: already recorded);
- probe features, from one forward pass, without gradients, in eval mode, of a throwaway copy
  materialised from the snapshot at t, on a probe split outside fit and dev.

Isolation (INV-34/35 analogue). The probe never touches the trunk, the snapshot or any branch:
- it runs on a fresh copy, and saves and restores the global RNG streams around materialising it;
- it calls each layer's `forward` directly, so no forward hook fires. The kernel host's saturation
  hooks close over the live host, so a hooked probe would write into it (PyTorch review);
- eval mode reads BatchNorm running statistics and never updates them.

Validity (ADR-0006). Every feature carries a validity flag. An absent or non-finite value is
recorded as None with valid False; it is never imputed as zero.

Leakage. The probe split is the fixed CIFAR permutation's positions 40000-40999: outside fit
(0 .. train_size-1, train_size <= 40000) and dev (45000 ..). Smoke data draws an independent probe.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from experiments import atlas
from experiments.bounded_data import RunSpec, _cifar, smoke_split, tensor_hash, validated_spec
from experiments.kernel_demo import derive, make_generator, normalize_u8

SCHEMA = "atlas-telemetry-v0"
PROBE_SIZE = 1000
PROBE_START = 40000
FIT_DEV_RULE = "cifar-fit-dev-v1"


@dataclass(frozen=True)
class Probe:
    x: torch.Tensor
    y: torch.Tensor
    sha256: str
    rule: str


def probe_indices(perm: torch.Tensor, *, train_size: int, dev_size: int) -> torch.Tensor:
    """Positions 40000-40999 of the fit/dev permutation, refused if they could overlap fit or dev."""
    if train_size > PROBE_START or PROBE_START + PROBE_SIZE > 45000 or 45000 + dev_size > len(perm):
        raise ValueError("the probe split must sit strictly between fit and dev in the permutation")
    return perm[PROBE_START : PROBE_START + PROBE_SIZE]


def load_probe(spec: RunSpec, root: Path | None) -> Probe:
    spec = validated_spec(dataclasses.asdict(spec))
    if spec.data == "smoke":
        x, y = smoke_split(dataclasses.replace(spec, data_seed=derive(spec.data_seed, "smoke-probe-v1")), "dev")
        rule = "smoke: independent draw (data_seed derived with 'smoke-probe-v1'), dev size"
    else:
        if root is None:
            raise ValueError("cifar requires a local --data-root")
        cx, cy = _cifar(root, train=True)
        perm = torch.randperm(50000, generator=make_generator(derive(spec.data_seed, FIT_DEV_RULE)))
        idx = probe_indices(perm, train_size=spec.train_size, dev_size=spec.dev_size)
        x, y = cx[idx], cy[idx]
        rule = f"cifar: '{FIT_DEV_RULE}' permutation positions {PROBE_START}-{PROBE_START + PROBE_SIZE - 1}"
    return Probe(x, y, tensor_hash(x, y), rule)


def _run_stage(stage: torch.nn.Sequential, h: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """A kernel stage (conv, norm, relu, conv, norm, relu, pool) through `forward` calls only: no hooks."""
    last_relu = h
    for index, layer in enumerate(stage):
        h = layer.forward(h)
        if index == 5:
            last_relu = h
    return h, last_relu


def _effective_rank(features: torch.Tensor) -> float:
    """exp(entropy) of the normalised singular values of centred, spatially pooled features."""
    centred = features - features.mean(dim=0, keepdim=True)
    s = torch.linalg.svdvals(centred.double())
    total = s.sum()
    if not bool(total > 0):
        return math.nan
    p = s / total
    p = p[p > 0]
    return float(torch.exp(-(p * p.log()).sum()))


def probe_features(host: Any, probe: Probe, batch_size: int = 250) -> dict[str, float]:
    """One eval-mode, gradient-free pass of `host` over the probe split. The host's modes are restored."""
    modes = [(m, m.training) for m in host.modules()]
    device = next(host.parameters()).device
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    pooled: list[torch.Tensor] = []
    logits_all: list[torch.Tensor] = []
    stage_out: dict[int, list[torch.Tensor]] = {1: [], 2: [], 3: []}

    def add(name: str, value: float, n: int) -> None:
        sums[name] = sums.get(name, 0.0) + value
        counts[name] = counts.get(name, 0) + n

    try:
        host.eval()
        with torch.no_grad():
            for offset in range(0, len(probe.y), batch_size):
                h = normalize_u8(probe.x[offset : offset + batch_size].to(device))
                n = len(h)
                for index, stage in enumerate((host.stage1, host.stage2, host.stage3), start=1):
                    h, relu = _run_stage(stage, h)
                    add(f"probe_stage{index}_rms", float(h.pow(2).mean()) * n, n)
                    add(f"probe_stage{index}_dead_relu", float((relu == 0).float().mean()) * n, n)
                    stage_out[index].append(h.mean(dim=(2, 3)).cpu())
                    if index == 2:
                        pooled.append(h.mean(dim=(2, 3)).cpu())  # the slot site's features
                logits = host.fc.forward(torch.flatten(host.gap.forward(h), 1))
                logits_all.append(logits.cpu())
    finally:
        for module, mode in modes:
            module.training = mode
    out = {name: sums[name] / counts[name] for name in sums}
    for index in (1, 2, 3):
        out[f"probe_stage{index}_rms"] = math.sqrt(out[f"probe_stage{index}_rms"])
        per_channel = torch.cat(stage_out[index]).var(dim=0)
        out[f"probe_stage{index}_channel_var_cv"] = (
            float(per_channel.std() / per_channel.mean()) if bool(per_channel.mean() > 0) else math.nan
        )
    logits = torch.cat(logits_all).double()
    y = probe.y.long()
    out["probe_ce"] = float(torch.nn.functional.cross_entropy(logits, y))
    pred = logits.argmax(1)
    out["probe_accuracy"] = float((pred == y).double().mean())
    per_class = torch.stack([(pred[y == c] == c).double().mean() if bool((y == c).any()) else torch.tensor(math.nan) for c in range(10)])
    out["probe_class_accuracy_sd"] = float(per_class[~per_class.isnan()].std()) if int((~per_class.isnan()).sum()) > 1 else math.nan
    confusion = torch.zeros(10, 10, dtype=torch.float64)
    confusion.index_put_((y, pred), torch.ones(len(y), dtype=torch.float64), accumulate=True)
    rows = confusion[confusion.sum(1) > 0]
    p = rows / rows.sum(1, keepdim=True)
    entropy = -(p * torch.where(p > 0, p.log(), torch.zeros_like(p))).sum(1)
    out["probe_confusion_entropy"] = float(entropy.mean())
    out["slot_effective_rank"] = _effective_rank(torch.cat(pooled))
    for index, stage in enumerate((host.stage1, host.stage2, host.stage3), start=1):
        out[f"weight_norm_stage{index}"] = float(torch.sqrt(sum(p.detach().double().pow(2).sum() for p in stage.parameters())))
    return out


def trunk_features(records: list[dict[str, Any]], t: int) -> dict[str, float | None]:
    """Free features from the trunk's own records for epochs before t; absent ones are None."""
    before = [r for r in records if r["epoch"] < t]
    last = before[-1] if before else None
    prev = before[-2] if len(before) > 1 else None
    if last is None:
        return dict.fromkeys(
            (
                "trunk_dev_ce",
                "trunk_dev_accuracy",
                "trunk_train_ce",
                "trunk_generalisation_gap",
                "trunk_dev_ce_delta",
                "trunk_grad_norm_max",
            )
        )
    return {
        "trunk_dev_ce": last["dev"]["ce"],
        "trunk_dev_accuracy": last["dev"]["accuracy"],
        "trunk_train_ce": last["train_ce"],
        "trunk_generalisation_gap": last["dev"]["ce"] - last["train_ce"],
        "trunk_dev_ce_delta": None if prev is None else last["dev"]["ce"] - prev["dev"]["ce"],
        "trunk_grad_norm_max": last["gradient_norm_max"]["host"],
    }


def decision_telemetry(unit: atlas.Unit, trunk: atlas.Span, t: int, probe: Probe) -> dict[str, Any]:
    """Every pre-decision feature at decision point t, with validity flags. Changes nothing it reads."""
    if t not in trunk.snapshots:
        raise ValueError(f"no snapshot at decision point {t}")
    cpu = torch.get_rng_state().clone()
    cuda = torch.cuda.get_rng_state().clone() if unit.device.type == "cuda" else None
    try:
        host, _slot, _opt = atlas.materialize(trunk.snapshots[t], unit.spec, unit.device, unit.host_cfg)  # a throwaway copy
        probed = probe_features(host, probe)
    finally:
        torch.set_rng_state(cpu)
        if cuda is not None:
            torch.cuda.set_rng_state(cuda)
    raw: dict[str, float | None] = {**trunk_features(trunk.records, t), **probed}
    features = {k: (v if v is not None and math.isfinite(v) else None) for k, v in sorted(raw.items())}
    return {
        "schema": SCHEMA,
        "epoch": t,
        "host_label": unit.host_label,
        "probe_sha256": probe.sha256,
        "probe_rule": probe.rule,
        "features": features,
        "valid": {k: v is not None for k, v in features.items()},
    }
