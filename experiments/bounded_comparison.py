"""One-host comparison with final outer scoring in a separate invocation.

Tier-3 ingress: CLI/RunSpec validates numeric ranges; local CIFAR is checked
offline at the data boundary; evaluation verifies JSON, source/runtime and
artifact SHA256 before weights_only checkpoint loading. Tier-1 owned records
fail on missing keys, duplicate JSON keys, non-finite numbers or incompletion.
No learned controller, no full-programme or superiority claim.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TextIO

import torch
from torch import nn

from experiments.bounded_data import RunSpec, file_hash, load_fit_dev, load_outer, tensor_hash, validated_spec
from experiments.kernel_demo import (
    CommonFuture,
    Slot,
    Stage,
    append_seed_group,
    augment,
    build_host,
    build_optimizer,
    build_seed,
    derive,
    make_generator,
    normalize_u8,
    state_hash,
    tau_init,
)

ARMS = ("no_growth", "static", "scheduled")
SCHEMA = 1
REPO = Path(__file__).resolve().parent.parent


def strict_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _bad_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON value: {value}")


def _read_json_text(path: Path) -> str:
    return path.read_text()


def read_json(path: Path) -> dict[str, Any]:
    """Guard JSON syntax/object/finiteness; semantic assurance is verify_run."""
    value = json.loads(_read_json_text(path), object_pairs_hook=_pairs, parse_constant=_bad_constant)
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path.name}")
    strict_json(value)  # Also rejects overflowing 1e999 parsed as infinity.
    return value


def require_keys(value: Any, keys: Iterable[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(key not in value for key in keys):
        raise ValueError(f"missing required evidence: {context}")
    return value


def require_number(value: Any, context: str, *, high: float = math.inf) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= high:
        raise ValueError(f"invalid measured number: {context}")


def validate_metrics(value: Any, examples: int, context: str) -> None:
    metrics = require_keys(value, ("ce", "accuracy", "examples"), context)
    require_number(metrics["ce"], context + ".ce")
    require_number(metrics["accuracy"], context + ".accuracy", high=1.0)
    if type(metrics["examples"]) is not int or metrics["examples"] != examples:
        raise ValueError(f"invalid measured sample count: {context}")


def validate_hash(value: Any, context: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"invalid state identity: {context}")


def validate_summary(summary: Any, spec: RunSpec, arm: str) -> None:
    summary = require_keys(
        summary,
        (
            "arm",
            "initial_dev",
            "final_dev",
            "final_parameters",
            "peak_parameters",
            "development_ce_decreased",
            "host_parameters_changed",
            "seed_body_changed",
            "seed_gain_changed",
            "gradient_norm_max",
            "optimizer_groups",
            "costs",
            "wall_s",
        ),
        arm + " summary",
    )
    if summary["arm"] != arm or summary["host_parameters_changed"] is not True:
        raise ValueError("invalid host update evidence")
    if arm != "no_growth" and (summary["seed_body_changed"] is not True or summary["seed_gain_changed"] is not True):
        raise ValueError("invalid seed update evidence")
    for key in ("initial_dev", "final_dev"):
        validate_metrics(summary[key], spec.dev_size, arm + "." + key)
    gradients = require_keys(summary["gradient_norm_max"], ("host", "seed_body", "seed_gain"), arm + " gradients")
    for name in gradients:
        require_number(gradients[name], arm + "." + name)
    if gradients["host"] <= 0 or (arm != "no_growth" and (gradients["seed_body"] <= 0 or gradients["seed_gain"] <= 0)):
        raise ValueError("missing gradient evidence")
    cost_keys = (
        "host_train_examples",
        "seed_train_examples",
        "host_dev_examples",
        "seed_dev_examples",
        "installed_parameter_epochs",
        "optimizer_parameter_epochs",
        "optimizer_parameter_steps",
        "calibration_examples",
        "fully_coupled_optimizer_steps",
    )
    costs = require_keys(summary["costs"], cost_keys, arm + " costs")
    if any(type(costs[key]) is not int or costs[key] < 0 for key in cost_keys):
        raise ValueError("invalid work count")
    if costs["host_train_examples"] != spec.epochs * spec.train_size:
        raise ValueError("incomplete training work")
    require_number(summary["wall_s"], arm + " wall time")


def validate_record(record: Any, spec: RunSpec, arm: str, kind: str, epoch: int | None) -> None:
    record = require_keys(record, ("schema_version", "arm", "kind", "birth"), "training record")
    if type(record["schema_version"]) is not int or record["schema_version"] != SCHEMA or record["arm"] != arm or record["kind"] != kind:
        raise ValueError("training evidence order/schema mismatch")
    if kind == "arm_start":
        require_keys(record, ("host_initial_parameter_sha256", "initial_dev"), arm + " start")
        validate_hash(record["host_initial_parameter_sha256"], arm + " initial host")
        validate_metrics(record["initial_dev"], spec.dev_size, arm + " initial development")
    else:
        keys = (
            "epoch",
            "requested_action",
            "executed_action",
            "action_legal",
            "installed_parameters",
            "seed_executed_train_examples",
            "dev",
            "wall_s",
            "train_ce",
            "train_objective",
            "train_examples",
            "optimizer_steps",
            "gradient_norm_max",
            "stage_used",
            "stage_after",
            "alpha_used_min",
            "alpha_used_max",
            "beta_used_min",
            "beta_used_max",
            "alpha_after",
            "beta_after",
            "host_state_sha256",
            "host_parameter_sha256",
            "training_state_sha256",
        )
        require_keys(record, keys, arm + " epoch")
        if type(record["epoch"]) is not int or record["epoch"] != epoch:
            raise ValueError("epoch order mismatch")
        action = "GERMINATE" if arm == "scheduled" and epoch == spec.graft_epoch else "WAIT"
        if record["requested_action"] != action or record["executed_action"] != action or record["action_legal"] is not True:
            raise ValueError("action evidence mismatch")
        validate_metrics(record["dev"], spec.dev_size, arm + " development")
        for name in ("train_ce", "train_objective", "wall_s"):
            require_number(record[name], arm + "." + name)
        for name in ("alpha_used_min", "alpha_used_max", "beta_used_min", "beta_used_max", "alpha_after", "beta_after"):
            require_number(record[name], arm + "." + name, high=1.0)
        for name in ("host_state_sha256", "host_parameter_sha256", "training_state_sha256"):
            validate_hash(record[name], arm + "." + name)
        if (
            type(record["train_examples"]) is not int
            or record["train_examples"] != spec.train_size
            or record["optimizer_steps"] != spec.train_size // spec.batch_size
        ):
            raise ValueError("incomplete epoch work")
        gradients = require_keys(record["gradient_norm_max"], ("host", "seed_body", "seed_gain"), arm + " epoch gradients")
        for name in gradients:
            require_number(gradients[name], arm + "." + name)
        Stage(record["stage_used"])
        Stage(record["stage_after"])
    born = (kind == "arm_start" and arm == "static") or (kind == "epoch" and arm == "scheduled" and epoch == spec.graft_epoch)
    if born:
        birth = require_keys(
            record["birth"],
            (
                "body_init_sha256",
                "seed_before_calibration_sha256",
                "seed_birth_sha256",
                "gain_at_birth",
                "calibration_examples",
                "calibration_prefix_forward_examples",
                "calibration_seed_forward_examples",
                "host_unchanged_sha256",
                "host_optimizer_preserved_sha256",
                "stage",
                "alpha",
                "beta",
            ),
            arm + " birth",
        )
        for name in (
            "body_init_sha256",
            "seed_before_calibration_sha256",
            "seed_birth_sha256",
            "host_unchanged_sha256",
            "host_optimizer_preserved_sha256",
        ):
            validate_hash(birth[name], arm + "." + name)
        require_number(birth["gain_at_birth"], arm + " gain")
        if birth["calibration_examples"] != min(spec.batch_size, spec.dev_size):
            raise ValueError("calibration count mismatch")
    elif record["birth"] is not None:
        raise ValueError("unexpected germination evidence")


def digest(value: Any) -> str:
    return hashlib.sha256(strict_json(value).encode()).hexdigest()


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(path: Path, value: dict[str, Any]) -> None:
    # This runner never overwrites accepted evidence, including evaluation.
    if path.exists():
        raise FileExistsError(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("x") as fh:
        fh.write(strict_json(value) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    # link publishes without replacing a concurrently created destination.
    os.link(tmp, path)
    tmp.unlink()
    _fsync_dir(path.parent)


def append_record(fh: TextIO, record: dict[str, Any]) -> None:
    fh.write(strict_json(record) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def runtime(threads: int) -> dict[str, Any]:
    import torchvision

    return {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "threads": threads,
        "device": "cpu",
        "deterministic": torch.are_deterministic_algorithms_enabled(),
        "mkldnn": torch.backends.mkldnn.enabled,
        "default_dtype": str(torch.get_default_dtype()),
    }


def configure_cpu(spec: RunSpec) -> None:
    spec.validate()
    torch.set_num_threads(spec.threads)
    torch.use_deterministic_algorithms(True)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cpu")
    # Pin only the CPU process stream, without initializing a GPU or letting
    # ambient interpreter startup RNG change deterministic trace identities.
    torch.set_rng_state(make_generator(derive(spec.seed, "process-global-cpu")).get_state())


def source_identity() -> dict[str, Any]:
    paths = (
        "experiments/__init__.py",
        "experiments/bounded_comparison.py",
        "experiments/bounded_data.py",
        "experiments/kernel_demo.py",
        "pyproject.toml",
        "uv.lock",
    )
    identity: dict[str, Any] = {name: file_hash(REPO / name) for name in paths}
    return identity


def git_identity() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(["git", "--no-optional-locks", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()

    return {"commit": run("rev-parse", "HEAD"), "status": run("status", "--porcelain=v1", "--untracked-files=all")}


def parameter_hash(module: nn.Module, *, body_only: bool = False) -> str:
    return tensor_hash(*(p for name, p in module.named_parameters() if not body_only or name != "gain"))


def optimizer_host_hash(opt: torch.optim.SGD) -> str:
    """Host group membership, hyperparameters, and momentum before/after append."""
    h = hashlib.sha256()
    for group in opt.param_groups[:2]:
        h.update(strict_json({k: v for k, v in group.items() if k != "params"}).encode())
        for param in group["params"]:
            h.update(tensor_hash(param).encode())
            state = opt.state.get(param, {})
            for key in sorted(state):
                value = state[key]
                h.update(key.encode())
                h.update((tensor_hash(value) if isinstance(value, torch.Tensor) else strict_json(value)).encode())
    return h.hexdigest()


def training_state_hash(host: nn.Module, slot: Slot, opt: torch.optim.SGD) -> str:
    """All trainable tensors/buffers, ordered optimizer history and lifecycle."""
    h = hashlib.sha256()
    h.update(state_hash(host).encode())
    h.update(state_hash(slot).encode())
    lifecycle = {
        "stage": slot.stage.value,
        "alpha": slot.alpha,
        "beta": slot.beta,
        "blend_step": slot._blend_step,
        "fossil_step": slot._fossil_step,
        "epochs_in_stage": slot._epochs_in_stage,
        "alpha_beta_log": slot.alpha_beta_log,
        "rms_ratio_blend_entry": slot.rms_ratio_blend_entry,
    }
    h.update(strict_json(lifecycle).encode())
    for group in opt.param_groups:
        h.update(strict_json({k: v for k, v in group.items() if k != "params"}).encode())
        for param in group["params"]:
            h.update(tensor_hash(param).encode())
            for key, value in sorted(opt.state.get(param, {}).items()):
                h.update(key.encode())
                h.update((tensor_hash(value) if isinstance(value, torch.Tensor) else strict_json(value)).encode())
    h.update(tensor_hash(torch.get_rng_state()).encode())
    return h.hexdigest()


def score(host: nn.Module, slot: Slot, x: torch.Tensor, y: torch.Tensor, batch_size: int) -> dict[str, Any]:
    """Sample-weighted metrics with state/RNG preservation, including buffers."""
    if len(y) == 0 or batch_size <= 0:
        raise ValueError("scoring requires examples and a positive batch size")
    modes = [(module, module.training) for root in (host, slot) for module in root.modules()]
    tensors = [(root, {k: v.detach().clone() for k, v in root.state_dict().items()}) for root in (host, slot)]
    rng = torch.get_rng_state().clone()
    # Forward hooks and Slot diagnostics are state too; restore them exactly.
    prior_stats = copy.deepcopy(getattr(host, "stage_stats", None))
    last_delta, last_h = slot.last_delta, slot.last_h
    loss, correct = 0.0, 0
    try:
        host.eval()
        slot.eval()
        with torch.no_grad():
            for offset in range(0, len(y), batch_size):
                logits = host(normalize_u8(x[offset : offset + batch_size]), slot)
                labels = y[offset : offset + batch_size]
                if not bool(torch.isfinite(logits).all()):
                    raise ValueError("non-finite scoring logits")
                loss += float(torch.nn.functional.cross_entropy(logits, labels, reduction="sum"))
                correct += int((logits.argmax(1) == labels).sum())
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


def attach_seed(host: Any, slot: Slot, opt: torch.optim.SGD, spec: RunSpec, dev_x: torch.Tensor, *, static: bool) -> dict[str, Any]:
    if slot.seed is not None or slot.stage is not Stage.DORMANT:
        raise RuntimeError("one lifetime germination attempt allowed")
    seed = build_seed("conv_light", 64, derive(spec.seed, "seed-body-init"))
    body_before = parameter_hash(seed, body_only=True)
    buffers_before = state_hash(seed)
    host_before, opt_before = state_hash(host), optimizer_host_hash(opt)
    prior = host.training
    host.eval()
    try:
        with torch.no_grad():
            calibration = dev_x[: spec.batch_size]
            features = host.forward_to_slot(normalize_u8(calibration))
        gain = tau_init(seed, features, spec.kernel_config())
    finally:
        host.train(prior)
    append_seed_group(opt, seed, spec.kernel_config())
    if state_hash(host) != host_before or optimizer_host_hash(opt) != opt_before:
        raise RuntimeError("germination changed host weights/buffers or optimizer history")
    if parameter_hash(seed, body_only=True) != body_before:
        raise RuntimeError("calibration changed seed body parameters")
    slot.seed = seed
    slot.stage = Stage.FOSSILIZED if static else Stage.TRAINING
    slot.alpha = slot.beta = 1.0 if static else 0.0
    return {
        "body_init_sha256": body_before,
        "seed_before_calibration_sha256": buffers_before,
        "seed_birth_sha256": state_hash(seed),
        "gain_at_birth": gain,
        "calibration_examples": len(calibration),
        "calibration_prefix_forward_examples": len(calibration),
        "calibration_seed_forward_examples": len(calibration),
        "host_unchanged_sha256": host_before,
        "host_optimizer_preserved_sha256": opt_before,
        "stage": slot.stage.value,
        "alpha": slot.alpha,
        "beta": slot.beta,
    }


def grad_norm(params: Iterable[torch.Tensor]) -> float:
    total = 0.0
    for param in params:
        if param.grad is not None:
            if not bool(torch.isfinite(param.grad).all()):
                raise ValueError("non-finite gradient")
            total += float(param.grad.detach().square().sum())
    return math.sqrt(total)


def train_epoch(
    host: Any, slot: Slot, opt: torch.optim.SGD, spec: RunSpec, future: CommonFuture, x: torch.Tensor, y: torch.Tensor, epoch: int
) -> dict[str, Any]:
    host.train()
    slot.train()
    start_stage = slot.stage.value
    ce_sum, objective_sum = 0.0, 0.0
    max_grads = {"host": 0.0, "seed_body": 0.0, "seed_gain": 0.0}
    used_alpha, used_beta = [], []
    order = future.order[epoch].reshape(-1, spec.batch_size)
    for step, idx in enumerate(order):
        used_alpha.append(slot.alpha)
        used_beta.append(slot.beta)
        logits = host(augment(x[idx], future.crops[epoch, step], future.flips[epoch, step]), slot)
        ce = torch.nn.functional.cross_entropy(logits, y[idx])
        objective = ce + slot.trust_region_loss(spec.kernel_config())
        if not bool(torch.isfinite(objective)):
            raise ValueError("non-finite training objective")
        opt.zero_grad(set_to_none=True)
        objective.backward()  # type: ignore[no-untyped-call]
        max_grads["host"] = max(max_grads["host"], grad_norm(host.parameters()))
        if slot.seed is not None:
            max_grads["seed_body"] = max(max_grads["seed_body"], grad_norm(p for n, p in slot.seed.named_parameters() if n != "gain"))
            max_grads["seed_gain"] = max(max_grads["seed_gain"], grad_norm([slot.seed.gain]))
        opt.step()
        slot.step_tick(spec.kernel_config(), len(order))
        ce_sum += float(ce.detach()) * len(idx)
        objective_sum += float(objective.detach()) * len(idx)
    slot.epoch_tick(spec.kernel_config())
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
        "host_state_sha256": state_hash(host),
        "host_parameter_sha256": parameter_hash(host),
        "training_state_sha256": training_state_hash(host, slot, opt),
    }


def save_checkpoint(path: Path, host: nn.Module, slot: Slot, arm: str, manifest_hash: str) -> None:
    payload = {
        "schema_version": SCHEMA,
        "purpose": "final-inference-only-not-resumable",
        "arm": arm,
        "manifest_sha256": manifest_hash,
        "host": host.state_dict(),
        "seed": None if slot.seed is None else slot.seed.state_dict(),
        "stage": slot.stage.value,
        "alpha": slot.alpha,
        "beta": slot.beta,
    }
    tmp = path.with_suffix(".pt.tmp")
    with tmp.open("xb") as fh:
        torch.save(payload, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.link(tmp, path)
    tmp.unlink()
    _fsync_dir(path.parent)


def train(spec: RunSpec, output: Path, data_root: Path | None = None) -> dict[str, Any]:
    configure_cpu(spec)
    if output.exists():
        raise FileExistsError("output must be a fresh directory; interrupted runs remain incomplete")
    tx, ty, dx, dy, provenance = load_fit_dev(spec, data_root)
    future = CommonFuture.draw(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA,
        "spec": dataclasses.asdict(spec),
        "arms": list(ARMS),
        "host": "kernel-demo-mild",
        "seed_type": "conv_light",
        "data": provenance,
        "source": source_identity(),
        "git": git_identity(),
        "runtime": runtime(spec.threads),
        "common_future_sha256": future.hash,
        "host_init_seed": derive(spec.seed, "host-init"),
        "seed_body_init_seed": derive(spec.seed, "seed-body-init"),
        "process_global_cpu_seed": derive(spec.seed, "process-global-cpu"),
        "checkpoint_rule": "final-epoch-only-all-arms",
        "budget": "equal-examples-and-epochs-not-equal-compute",
        "scaffold_state": {
            "execution": "cpu-pinned-stack",
            "host_distribution": "one-fixed-mild-CNN",
            "design_prior": "one-human-authored-conv_light",
            "counterfactual_anchor": "measured-no-growth",
        },
    }
    write_json(output / "manifest.json", manifest)
    manifest_hash = file_hash(output / "manifest.json")
    summaries = {}
    with (output / "training.jsonl").open("x") as log:
        for arm in ARMS:
            started = time.perf_counter()
            host = build_host("mild", manifest["host_init_seed"])
            slot = Slot()
            opt = build_optimizer(host, spec.kernel_config())
            host_initial = parameter_hash(host)
            base_params = sum(p.numel() for p in host.parameters())
            birth = attach_seed(host, slot, opt, spec, dx, static=True) if arm == "static" else None
            initial_dev = score(host, slot, dx, dy, spec.batch_size)
            append_record(
                log,
                {
                    "schema_version": SCHEMA,
                    "kind": "arm_start",
                    "arm": arm,
                    "host_initial_parameter_sha256": host_initial,
                    "initial_dev": initial_dev,
                    "birth": birth,
                },
            )
            costs = {
                "host_train_examples": 0,
                "seed_train_examples": 0,
                "host_dev_examples": len(dy),
                "seed_dev_examples": len(dy) if arm == "static" else 0,
                "installed_parameter_epochs": 0,
                "optimizer_parameter_epochs": 0,
                "calibration_examples": 0 if birth is None else birth["calibration_examples"],
                "optimizer_parameter_steps": 0,
                "fully_coupled_optimizer_steps": 0,
            }
            history = []
            for epoch in range(spec.epochs):
                action = "GERMINATE" if arm == "scheduled" and epoch == spec.graft_epoch else "WAIT"
                if action == "GERMINATE":
                    birth = attach_seed(host, slot, opt, spec, dx, static=False)
                    costs["calibration_examples"] += birth["calibration_examples"]
                params = base_params + (0 if slot.seed is None else sum(p.numel() for p in slot.seed.parameters()))
                fully_coupled = slot.seed is not None and slot.alpha == slot.beta == 1.0
                epoch_started = time.perf_counter()
                metrics = train_epoch(host, slot, opt, spec, future, tx, ty, epoch)
                dev = score(host, slot, dx, dy, spec.batch_size)
                costs["host_train_examples"] += len(ty)
                costs["seed_train_examples"] += len(ty) if slot.seed is not None else 0
                costs["host_dev_examples"] += len(dy)
                costs["seed_dev_examples"] += len(dy) if slot.seed is not None else 0
                costs["installed_parameter_epochs"] += params
                costs["optimizer_parameter_epochs"] += sum(p.numel() for group in opt.param_groups for p in group["params"])
                costs["optimizer_parameter_steps"] += params * metrics["optimizer_steps"]
                costs["fully_coupled_optimizer_steps"] += metrics["optimizer_steps"] if fully_coupled else 0
                record = {
                    "schema_version": SCHEMA,
                    "kind": "epoch",
                    "arm": arm,
                    "epoch": epoch,
                    "requested_action": action,
                    "executed_action": action,
                    "action_legal": True,
                    "birth": birth if action == "GERMINATE" else None,
                    "installed_parameters": params,
                    "seed_executed_train_examples": len(ty) if slot.seed is not None else 0,
                    "dev": dev,
                    "wall_s": time.perf_counter() - epoch_started,
                    **metrics,
                }
                append_record(log, record)
                history.append(record)
            if arm != "no_growth" and (
                slot.stage is not Stage.FOSSILIZED or slot.alpha != 1.0 or slot.beta != 1.0 or costs["fully_coupled_optimizer_steps"] == 0
            ):
                raise RuntimeError("incomplete final topology/coupling")
            if len({id(p) for group in opt.param_groups for p in group["params"]}) != sum(
                len(group["params"]) for group in opt.param_groups
            ):
                raise RuntimeError("duplicate optimizer membership")
            if sum(p.numel() for group in opt.param_groups for p in group["params"]) != params:
                raise RuntimeError("optimizer does not own all installed parameters")
            body_changed: bool | None = None
            gain_changed: bool | None = None
            if slot.seed is not None:
                assert birth is not None
                body_changed = parameter_hash(slot.seed, body_only=True) != birth["body_init_sha256"]
                gain_changed = float(slot.seed.gain.detach()) != birth["gain_at_birth"]
            summary = {
                "arm": arm,
                "initial_dev": initial_dev,
                "final_dev": history[-1]["dev"],
                "final_parameters": params,
                "peak_parameters": params,
                "development_ce_decreased": history[-1]["dev"]["ce"] < initial_dev["ce"],
                "host_parameters_changed": parameter_hash(host) != host_initial,
                "seed_body_changed": body_changed,
                "seed_gain_changed": gain_changed,
                "gradient_norm_max": {
                    name: max(row["gradient_norm_max"][name] for row in history) for name in ("host", "seed_body", "seed_gain")
                },
                "optimizer_groups": len(opt.param_groups),
                "costs": costs,
                "wall_s": time.perf_counter() - started,
            }
            if not summary["host_parameters_changed"] or summary["gradient_norm_max"]["host"] <= 0:
                raise RuntimeError("host did not learn/update")
            if arm != "no_growth" and (
                not summary["seed_body_changed"]
                or not summary["seed_gain_changed"]
                or summary["gradient_norm_max"]["seed_body"] <= 0
                or summary["gradient_norm_max"]["seed_gain"] <= 0
            ):
                raise RuntimeError("seed body/gain did not learn/update")
            save_checkpoint(output / f"{arm}.pt", host, slot, arm, manifest_hash)
            summaries[arm] = summary
        log.flush()
        os.fsync(log.fileno())
    expected_records = len(ARMS) * (spec.epochs + 1)
    artifacts = {name: file_hash(output / name) for name in ("manifest.json", "training.jsonl", *(f"{arm}.pt" for arm in ARMS))}
    completion = {
        "schema_version": SCHEMA,
        "status": "complete",
        "record_count": expected_records,
        "artifacts": artifacts,
        "summaries": summaries,
    }
    # Completion is the final write. Exceptions retain partial evidence without
    # manufacturing a completed run or retrying another schedule.
    write_json(output / "complete.json", completion)
    return completion


def _read_training_lines(path: Path) -> list[str]:
    return path.read_text().splitlines(keepends=True)


def verify_run(root: Path) -> tuple[dict[str, Any], dict[str, Any], RunSpec]:
    """Assure the declared consumer contract, not arbitrary metadata semantics."""
    complete = read_json(root / "complete.json")
    require_keys(complete, ("schema_version", "status", "record_count", "artifacts", "summaries"), "completion")
    if type(complete["schema_version"]) is not int or complete["schema_version"] != SCHEMA or complete["status"] != "complete":
        raise ValueError("unsupported/incomplete completion record")
    expected_names = {"manifest.json", "training.jsonl", *(f"{arm}.pt" for arm in ARMS)}
    if set(complete["artifacts"]) != expected_names:
        raise ValueError("artifact set mismatch")
    for name, sha in complete["artifacts"].items():
        path = root / name
        if path.is_symlink() or file_hash(path) != sha:
            raise ValueError(f"artifact checksum/path mismatch: {name}")
    manifest = read_json(root / "manifest.json")
    require_keys(
        manifest,
        (
            "schema_version",
            "spec",
            "arms",
            "host",
            "seed_type",
            "data",
            "source",
            "git",
            "runtime",
            "common_future_sha256",
            "host_init_seed",
            "seed_body_init_seed",
            "process_global_cpu_seed",
            "checkpoint_rule",
            "budget",
            "scaffold_state",
        ),
        "manifest",
    )
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != SCHEMA
        or manifest["arms"] != list(ARMS)
        or manifest["source"] != source_identity()
    ):
        raise ValueError("manifest schema/arms/source mismatch")
    if not isinstance(manifest["spec"], dict) or set(manifest["spec"]) != {field.name for field in dataclasses.fields(RunSpec)}:
        raise ValueError("incomplete specification")
    spec = validated_spec(manifest["spec"])
    configure_cpu(spec)
    if manifest["runtime"] != runtime(spec.threads):
        raise ValueError("execution runtime mismatch")
    data = require_keys(
        manifest["data"],
        ("kind", "source_files", "outer_identity", "fit_sha256", "dev_sha256", "fit_size", "dev_size", "data_seed"),
        "data provenance",
    )
    validate_hash(data["fit_sha256"], "fit data")
    validate_hash(data["dev_sha256"], "development data")
    validate_hash(manifest["common_future_sha256"], "common future")
    if data["fit_size"] != spec.train_size or data["dev_size"] != spec.dev_size or data["data_seed"] != spec.data_seed:
        raise ValueError("split specification mismatch")
    if not isinstance(complete["summaries"], dict) or set(complete["summaries"]) != set(ARMS):
        raise ValueError("missing required evidence: summary arm set")
    for arm in ARMS:
        validate_summary(complete["summaries"][arm], spec, arm)
    lines = _read_training_lines(root / "training.jsonl")
    if (
        len(lines) != complete["record_count"]
        or len(lines) != len(ARMS) * (spec.epochs + 1)
        or any(not line.endswith("\n") for line in lines)
    ):
        raise ValueError("training evidence incomplete")
    expected = [(arm, kind, epoch) for arm in ARMS for kind, epoch in [("arm_start", None), *(("epoch", e) for e in range(spec.epochs))]]
    for line, (arm, kind, epoch) in zip(lines, expected, strict=True):
        record = json.loads(line, object_pairs_hook=_pairs, parse_constant=_bad_constant)
        strict_json(record)
        validate_record(record, spec, arm, kind, epoch)
    return manifest, complete, spec


def _read_checkpoint(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=True)


def restore_checkpoint(root: Path, arm: str, manifest_hash: str, spec: RunSpec) -> tuple[Any, Slot]:
    if arm not in ARMS:
        raise ValueError("unknown arm")
    checkpoint = _read_checkpoint(root / f"{arm}.pt")
    if checkpoint["schema_version"] != SCHEMA or checkpoint["arm"] != arm or checkpoint["manifest_sha256"] != manifest_hash:
        raise ValueError("checkpoint identity mismatch")
    host = build_host("mild", derive(spec.seed, "host-init"))
    host.load_state_dict(checkpoint["host"], strict=True)
    slot = Slot()
    if arm != "no_growth":
        slot.seed = build_seed("conv_light", 64, derive(spec.seed, "seed-body-init"))
        slot.seed.load_state_dict(checkpoint["seed"], strict=True)
    elif checkpoint["seed"] is not None:
        raise ValueError("no-growth checkpoint contains a seed")
    slot.stage = Stage(checkpoint["stage"])
    slot.alpha, slot.beta = checkpoint["alpha"], checkpoint["beta"]
    if arm == "no_growth" and (slot.stage is not Stage.DORMANT or slot.alpha != 0 or slot.beta != 0):
        raise ValueError("no-growth checkpoint stage mismatch")
    if arm != "no_growth" and (slot.stage is not Stage.FOSSILIZED or slot.alpha != 1 or slot.beta != 1):
        raise ValueError("incomplete checkpoint coupling")
    if any(not bool(torch.isfinite(t).all()) for model in (host, slot) for t in model.state_dict().values()):
        raise ValueError("non-finite checkpoint state")
    return host, slot


def evaluate(root: Path, data_root: Path | None = None) -> dict[str, Any]:
    if (root / "outer_evaluation.json").exists():
        raise FileExistsError("outer results already exist; evaluation is final and cannot be overwritten")
    verified = verify_run(root)
    manifest, complete, spec = verified
    # All checkpoints validated/materialized before opening outer data.
    models = {arm: restore_checkpoint(root, arm, complete["artifacts"]["manifest.json"], spec) for arm in ARMS}
    x, y, outer_identity = load_outer(spec, data_root, manifest["data"])
    started = time.perf_counter()
    untrained = score(build_host("mild", derive(spec.seed, "host-init")), Slot(), x, y, spec.batch_size)
    scores = {arm: score(host, slot, x, y, spec.batch_size) for arm, (host, slot) in models.items()}
    result = evaluation_record(
        verified, outer_identity, scores, untrained, time.perf_counter() - started, file_hash(root / "complete.json")
    )
    return publish_evaluation(root, result)


def evaluation_record(
    verified: tuple[dict[str, Any], dict[str, Any], RunSpec],
    outer_identity: dict[str, Any],
    scores: dict[str, Any],
    untrained: dict[str, Any],
    wall_s: float,
    completion_hash: str,
) -> dict[str, Any]:
    """Validate measured evidence before it reaches the publication consumer.

    Assurance covers score counts/ranges, identities and finite timing. It
    does not establish scientific superiority or arbitrary metadata meaning.
    """
    _, complete, spec = verified
    spec = validated_spec(dataclasses.asdict(spec))
    artifacts = require_keys(complete, ("artifacts",), "evaluation completion")["artifacts"]
    artifacts = require_keys(artifacts, ("manifest.json",), "evaluation artifacts")
    validate_hash(artifacts["manifest.json"], "evaluation manifest")
    validate_hash(completion_hash, "evaluation completion")
    outer_identity = require_keys(outer_identity, ("outer_sha256", "outer_source_files", "size"), "outer identity")
    validate_hash(outer_identity["outer_sha256"], "outer tensors")
    if type(outer_identity["size"]) is not int or outer_identity["size"] != spec.outer_size:
        raise ValueError("outer evidence sample count mismatch")
    if not isinstance(outer_identity["outer_source_files"], dict):
        raise ValueError("invalid outer source identities")
    for sha in outer_identity["outer_source_files"].values():
        validate_hash(sha, "outer source file")
    if not isinstance(scores, dict) or set(scores) != set(ARMS):
        raise ValueError("incomplete outer score arm set")
    for arm in ARMS:
        validate_metrics(scores[arm], spec.outer_size, arm + " outer score")
    validate_metrics(untrained, spec.outer_size, "untrained outer score")
    require_number(wall_s, "outer wall time")
    return {
        "schema_version": SCHEMA,
        "manifest_sha256": complete["artifacts"]["manifest.json"],
        "completion_sha256": completion_hash,
        "source": source_identity(),
        "runtime": runtime(spec.threads),
        "data": outer_identity,
        "claim_scope": "engineering-smoke-only" if spec.data == "smoke" else "one-prospective-CIFAR-split",
        "untrained_host_score": untrained,
        "heldout_learning_acceptance": {
            arm: scores[arm]["ce"] < untrained["ce"] and scores[arm]["accuracy"] > untrained["accuracy"] for arm in ARMS
        },
        "scores": scores,
        "paired_differences": {
            arm: {
                "ce_minus_no_growth": scores[arm]["ce"] - scores["no_growth"]["ce"],
                "accuracy_minus_no_growth": scores[arm]["accuracy"] - scores["no_growth"]["accuracy"],
            }
            for arm in ("static", "scheduled")
        },
        "scheduled_minus_static": {
            "ce": scores["scheduled"]["ce"] - scores["static"]["ce"],
            "accuracy": scores["scheduled"]["accuracy"] - scores["static"]["accuracy"],
        },
        "wall_s": wall_s,
        "outer_forward_examples": {arm: {"host": spec.outer_size, "seed": 0 if arm == "no_growth" else spec.outer_size} for arm in ARMS},
        "untrained_reference_forward_examples": spec.outer_size,
        "independent_trajectories": 1,
        "superiority_established": False,
    }


def publish_evaluation(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Consume the validated evaluation record; retain exclusive-write refusal."""
    write_json(root / "outer_evaluation.json", record)
    return record


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    training = sub.add_parser("train")
    training.add_argument("--output", type=Path, required=True)
    training.add_argument("--data-root", type=Path)
    for field in dataclasses.fields(RunSpec):
        default = getattr(RunSpec(), field.name)
        if field.name == "data":
            training.add_argument("--data", choices=("smoke", "cifar"), default=default)
        else:
            training.add_argument("--" + field.name.replace("_", "-"), type=type(default), default=default)
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--run", type=Path, required=True)
    evaluation.add_argument("--data-root", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_arguments(argv)
    if args.mode == "train":
        spec = validated_spec({field.name: getattr(args, field.name) for field in dataclasses.fields(RunSpec)})
        result = train(spec, args.output, args.data_root)
        print(strict_json({"status": result["status"], "run": str(args.output), "summaries": result["summaries"]}))
    else:
        print(strict_json(evaluate(args.run, args.data_root)))


if __name__ == "__main__":
    main()
