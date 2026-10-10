"""Static arm with train-mode tau calibration (simic-e3803e8200): born at tau on BatchNorm hosts.

The frozen runner's `attach_seed` reads the host's slot features for tau under `host.eval()`. At
step zero a BatchNorm host's running statistics are untrained, so its eval-mode slot features are
a small fraction of their train-mode size and the static seed is born far below tau. In the Fleet
C1 pilot the realised ratio at birth was 0.0013-0.0018 against tau = 0.05 on `mild`,
`channel_starved` and `no_spatial_mix`, and 0.0500 on `under_normalized`, which has no
BatchNorm. The graft is unaffected: it is born after an epoch, on trained statistics.

`attach_static_train_calibrated` is `attach_seed(static=True)` with one change: the host features
for tau are read in train mode, the mode of the first training step, under no_grad, and every
host buffer, module mode and hook statistic is restored afterwards. On a host without BatchNorm
the two read the same features, so the arm is the registered static arm bit for bit. The frozen
runner and the registered `static` arm are unchanged.
"""

from __future__ import annotations

import copy
from typing import Any

import torch

from experiments.bounded_comparison import (
    ScaleAwareSlot,
    optimizer_host_hash,
    parameter_hash,
    realised_ratio_at_birth,
    tagged,
)
from experiments.bounded_data import RunSpec, tensor_hash
from experiments.kernel_demo import Stage, append_seed_group, build_seed, derive, normalize_u8, state_hash, tau_init

CALIBRATION_MODE = "train"


def _train_mode_slot_features(host: Any, calibration: torch.Tensor) -> torch.Tensor:
    """The host's slot features in train mode, without gradients; buffers, modes and hook stats restored."""
    saved = [(buffer, buffer.detach().clone()) for buffer in host.buffers()]
    modes = [(module, module.training) for module in host.modules()]
    prior_stats = copy.deepcopy(getattr(host, "stage_stats", None))
    try:
        host.train()
        with torch.no_grad():
            return host.forward_to_slot(normalize_u8(calibration))  # type: ignore[no-any-return]
    finally:
        for buffer, value in saved:
            buffer.copy_(value)
        for module, mode in modes:
            module.training = mode
        if prior_stats is not None:
            host.stage_stats = prior_stats


def attach_static_train_calibrated(
    host: Any, slot: ScaleAwareSlot, opt: torch.optim.SGD, spec: RunSpec, fit_x: torch.Tensor
) -> dict[str, Any]:
    """`attach_seed(..., static=True)`, with tau calibrated on train-mode host features."""
    if slot.seed is not None or slot.stage is not Stage.DORMANT:
        raise RuntimeError("one lifetime germination attempt allowed")
    seed = build_seed(spec.seed_type, 64, derive(spec.seed, "seed-body-init")).to(fit_x.device)
    body_before = parameter_hash(seed, body_only=True)
    buffers_before = state_hash(seed)
    host_before, opt_before = state_hash(host), optimizer_host_hash(opt)
    calibration = fit_x[: spec.batch_size]
    features = _train_mode_slot_features(host, calibration)
    tau_init(seed, features, spec.kernel_config())  # sets seed.gain; the birth record reads it back
    realised = realised_ratio_at_birth(host, seed, calibration)
    append_seed_group(opt, seed, spec.kernel_config())
    if state_hash(host) != host_before or optimizer_host_hash(opt) != opt_before:
        raise RuntimeError("germination changed host weights/buffers or optimizer history")
    if parameter_hash(seed, body_only=True) != body_before:
        raise RuntimeError("calibration changed seed body parameters")
    slot.seed = seed
    slot.stage = Stage.FOSSILIZED
    slot.alpha = slot.beta = 1.0
    return {
        "body_init_sha256": body_before,
        "seed_before_calibration_sha256": buffers_before,
        "seed_birth_sha256": state_hash(seed),
        "gain_at_birth": float(seed.gain.detach()),
        "calibration_examples": len(calibration),
        "calibration_inputs_sha256": tensor_hash(calibration),
        "realised_ratio_at_birth": tagged(realised),
        "calibration_prefix_forward_examples": len(calibration),
        "calibration_seed_forward_examples": len(calibration),
        "host_unchanged_sha256": host_before,
        "host_optimizer_preserved_sha256": opt_before,
        "stage": slot.stage.value,
        "alpha": slot.alpha,
        "beta": slot.beta,
        "calibration_mode": CALIBRATION_MODE,
    }
