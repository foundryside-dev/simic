"""Atlas exact-records speed tier (spike S3 item 3): the frozen runner's epoch, with fewer syncs.

`train_epoch` and `score` return exactly what `bounded_comparison.train_epoch` and `.score` return
and leave the same training state, bit for bit (tests/unit/test_atlas_fast.py, and the GPU golden
check against rung 4). `bounded_comparison` itself is frozen: its runs are evidence.

What changes, and why it cannot change a record:
- **Value reads move to the end of the epoch.** CE, objective, gains and per-parameter squared-
  gradient sums stay on the device as float32 tensors computed by the same kernels, and are read
  once. Python then accumulates them in the original order, so every float64 total is identical.
- **Divergence checks stay per step.** The objective's finiteness is still checked every step, and
  the per-parameter gradient checks are combined into one check per step. A divergence therefore
  stops at the same step, before the same update, with the same witness.
- **Inputs move to the device once per epoch.** The epoch's order, crops and flips, and the
  normalisation constants, instead of a small host-to-device copy on every step and batch. The
  augmentation and normalisation arithmetic is the kernel's, op for op.
- **Scoring reads once per pass** instead of three times per batch; a non-finite batch still raises
  NonFiniteError, and state, modes and RNG are restored exactly as before.
"""

from __future__ import annotations

import copy
import math
from typing import Any

import torch
from torch import nn

from experiments.bounded_comparison import (
    ArmDivergedError,
    NonFiniteError,
    ScaleAwareSlot,
    parameter_hash,
    strict_json,
    tagged,
    training_state_hash,
)
from experiments.bounded_data import RunSpec
from experiments.kernel_demo import CIFAR_MEAN, CIFAR_STD, CommonFuture, Slot, state_hash

_CONSTANTS: dict[torch.device, tuple[torch.Tensor, torch.Tensor]] = {}


def _mean_std(device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    if device not in _CONSTANTS:
        _CONSTANTS[device] = (CIFAR_MEAN.to(device), CIFAR_STD.to(device))
    return _CONSTANTS[device]


def _augment(x_u8: torch.Tensor, crops: torch.Tensor, flips: torch.Tensor) -> torch.Tensor:
    """`kernel_demo.augment`, op for op, with the constants and crop/flip tensors already on the device."""
    dev = x_u8.device
    mean, std = _mean_std(dev)
    xf = x_u8.to(torch.float32).div(255.0)
    xf = (xf - mean) / std
    xp = torch.nn.functional.pad(xf, (4, 4, 4, 4), mode="reflect")
    n = xf.shape[0]
    ar = torch.arange(32, device=dev)
    ys = crops[:, 0].to(torch.int64)[:, None] + ar
    xs = crops[:, 1].to(torch.int64)[:, None] + ar
    bi = torch.arange(n, device=dev)[:, None, None]
    out = xp.permute(0, 2, 3, 1)[bi, ys[:, :, None], xs[:, None, :], :].permute(0, 3, 1, 2)
    return torch.where(flips[:, None, None, None], out.flip(-1), out).contiguous()


def _normalize(x_u8: torch.Tensor) -> torch.Tensor:
    """`kernel_demo.normalize_u8`, op for op, with cached device constants."""
    mean, std = _mean_std(x_u8.device)
    xf = x_u8.to(torch.float32).div(255.0)
    return (xf - mean) / std


def _square_sums(params: list[torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-parameter float32 squared-gradient sums (the frozen grad_norm's kernels) and one finiteness flag."""
    grads = [p.grad.detach() for p in params if p.grad is not None]
    if not grads:
        device = params[0].device if params else torch.device("cpu")
        return torch.zeros(0, device=device), torch.ones((), dtype=torch.bool, device=device)
    finite = torch.stack([torch.isfinite(g).all() for g in grads]).all()
    return torch.stack([g.square().sum() for g in grads]), finite


def _norm(sums: list[float]) -> float:
    total = 0.0
    for value in sums:  # the frozen grad_norm's order and float64 accumulation
        total += value
    return math.sqrt(total)


def train_epoch(
    host: Any, slot: ScaleAwareSlot, opt: torch.optim.SGD, spec: RunSpec, future: CommonFuture, x: torch.Tensor, y: torch.Tensor, epoch: int
) -> dict[str, Any]:
    if not isinstance(slot, ScaleAwareSlot):
        raise TypeError("the bounded runner trains through ScaleAwareSlot so every STE step is witnessed")
    host.train()
    slot.train()
    start_stage = slot.stage.value
    used_alpha, used_beta = [], []
    gain_t: list[torch.Tensor] = []
    ste: dict[str, list[Any]] = {"kappa_live": [], "lam_t": [], "gain": [], "clamped": []}
    blend_entry_before = slot.rms_ratio_blend_entry
    device = x.device
    order = future.order[epoch].reshape(-1, spec.batch_size).to(device)
    crops, flips = future.crops[epoch].to(device), future.flips[epoch].to(device)
    ce_t: list[torch.Tensor] = []
    obj_t: list[torch.Tensor] = []
    sums: dict[str, list[torch.Tensor]] = {"host": [], "seed_body": [], "seed_gain": []}

    def gains() -> list[float]:
        return [float(g) for g in gain_t]

    def witness() -> dict[str, Any]:
        if slot.seed is None:
            return {"seed_present": False}
        g = gains()
        record: dict[str, Any] = {"seed_present": True, "gain_min": tagged(min(g)) if g else tagged(float(slot.seed.gain.detach()))}
        record["gain_max"] = tagged(max(g)) if g else record["gain_min"]
        if ste["kappa_live"]:
            record["ste"] = {k: [tagged(v) if isinstance(v, float) else v for v in values] for k, values in ste.items()}
        if blend_entry_before is None and slot.rms_ratio_blend_entry is not None:
            record["rms_ratio_blend_entry"] = tagged(float(slot.rms_ratio_blend_entry))
        return record

    host_params = list(host.parameters())
    for step in range(len(order)):
        idx = order[step]
        used_alpha.append(slot.alpha)
        used_beta.append(slot.beta)
        logits = host(_augment(x[idx], crops[step], flips[step]), slot)
        ce = torch.nn.functional.cross_entropy(logits, y[idx])
        objective = ce + slot.trust_region_loss(spec.kernel_config())
        if slot.seed is not None:
            gain_t.append(slot.seed.gain.detach().clone())
        if slot.last_witness is not None:
            for key in ste:
                ste[key].append(slot.last_witness[key])
        if not bool(torch.isfinite(objective)):
            raise ArmDivergedError(
                epoch=epoch, step=step, reason="non-finite training objective", stage=slot.stage.value, witness=witness()
            )
        opt.zero_grad(set_to_none=True)
        objective.backward()  # type: ignore[no-untyped-call]
        groups = {"host": host_params}
        if slot.seed is not None:
            groups["seed_body"] = [p for n, p in slot.seed.named_parameters() if n != "gain"]
            groups["seed_gain"] = [slot.seed.gain]
        flags = []
        step_sums = {}
        for name, params in groups.items():
            step_sums[name], finite = _square_sums(params)
            flags.append(finite)
        # The frozen loop checks host, then seed body, then gain; any non-finite gradient raises the same error at this step.
        if not bool(torch.stack(flags).all()):
            raise ArmDivergedError(epoch=epoch, step=step, reason="non-finite gradient", stage=slot.stage.value, witness=witness())
        for name, value in step_sums.items():
            sums[name].append(value)
        opt.step()
        slot.step_tick(spec.kernel_config(), len(order))
        ce_t.append(ce.detach())
        obj_t.append(objective.detach())
    epoch_witness = witness()
    slot.epoch_tick(spec.kernel_config())
    # One read for every per-step value; Python accumulates in the frozen order.
    ce_vals = torch.stack(ce_t).tolist() if ce_t else []
    obj_vals = torch.stack(obj_t).tolist() if obj_t else []
    ce_sum, objective_sum = 0.0, 0.0
    for c, o in zip(ce_vals, obj_vals, strict=True):
        ce_sum += c * spec.batch_size
        objective_sum += o * spec.batch_size
    max_grads = {"host": 0.0, "seed_body": 0.0, "seed_gain": 0.0}
    for name, per_step in sums.items():
        for vec in per_step:
            max_grads[name] = max(max_grads[name], _norm(vec.tolist()))
    return {
        "train_ce": ce_sum / len(y),
        "train_objective": objective_sum / len(y),
        "train_examples": len(y),
        "optimizer_steps": len(order),
        "gradient_norm_max": max_grads,
        "stage_used": start_stage,
        "alpha_used_min": min(used_alpha),
        "alpha_used_max": max(used_alpha),
        "beta_used_min": min(used_beta),
        "beta_used_max": max(used_beta),
        "stage_after": slot.stage.value,
        "alpha_after": slot.alpha,
        "beta_after": slot.beta,
        "witness": epoch_witness,
        "host_state_sha256": state_hash(host),
        "host_parameter_sha256": parameter_hash(host),
        "training_state_sha256": training_state_hash(host, slot, opt),
    }


def score(host: nn.Module, slot: Slot, x: torch.Tensor, y: torch.Tensor, batch_size: int) -> dict[str, Any]:
    """The frozen `score`, reading the per-batch sums once at the end instead of three times per batch."""
    if len(y) == 0 or batch_size <= 0:
        raise ValueError("scoring requires examples and a positive batch size")
    modes = [(module, module.training) for root in (host, slot) for module in root.modules()]
    tensors = [(root, {k: v.detach().clone() for k, v in root.state_dict().items()}) for root in (host, slot)]
    rng = torch.get_rng_state().clone()
    prior_stats = copy.deepcopy(getattr(host, "stage_stats", None))
    last_delta, last_h = slot.last_delta, slot.last_h
    losses, corrects, finite = [], [], []
    try:
        host.eval()
        slot.eval()
        with torch.no_grad():
            for offset in range(0, len(y), batch_size):
                logits = host(_normalize(x[offset : offset + batch_size]), slot)
                labels = y[offset : offset + batch_size]
                finite.append(torch.isfinite(logits).all())
                losses.append(torch.nn.functional.cross_entropy(logits, labels, reduction="sum"))
                corrects.append((logits.argmax(1) == labels).sum())
        if not bool(torch.stack(finite).all()):
            raise NonFiniteError("non-finite scoring logits")
        loss = 0.0
        for value in torch.stack(losses).tolist():  # the frozen order and float64 accumulation
            loss += value
        correct = 0
        for value in torch.stack(corrects).tolist():
            correct += int(value)
        if not torch.equal(rng, torch.get_rng_state()):
            raise RuntimeError("evaluation perturbed RNG")
        for root, before in tensors:
            if any(not torch.equal(before[k], v) for k, v in root.state_dict().items()):
                raise RuntimeError("evaluation perturbed weights/buffers")
        result = {"ce": loss / len(y), "accuracy": correct / len(y), "examples": len(y)}
        strict_json(result)
        return result
    finally:
        for root, before in tensors:
            root.load_state_dict(before)
        for module, mode in modes:
            module.training = mode
        torch.set_rng_state(rng)
        slot.last_delta, slot.last_h = last_delta, last_h
        if prior_stats is not None:
            host.stage_stats = prior_stats
