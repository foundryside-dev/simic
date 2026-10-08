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
    PATHOLOGIES,
    SEED_NAMES,
    CommonFuture,
    Slot,
    Stage,
    append_seed_group,
    augment,
    build_host,
    build_optimizer,
    build_seed,
    derive,
    enable_class1,
    make_generator,
    normalize_u8,
    state_hash,
    tau_init,
)

ARMS = ("no_growth", "static", "scheduled")
SCHEMA = 2  # 2: lifecycle variant + recorded curvature witnesses (docs/bounded-lifecycle-v2.md)
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
    if require_keys(summary, ("status",), arm + " summary")["status"] == "diverged":
        validate_diverged_summary(summary, spec, arm)
        return
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
    costs = validate_costs(summary["costs"], arm)
    if costs["host_train_examples"] != spec.epochs * spec.train_size:
        raise ValueError("incomplete training work")
    require_number(summary["wall_s"], arm + " wall time")


COST_KEYS = (
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


def validate_costs(raw: Any, arm: str) -> dict[str, Any]:
    costs: dict[str, Any] = require_keys(raw, COST_KEYS, arm + " costs")
    if set(costs) != set(COST_KEYS) or any(type(costs[key]) is not int or costs[key] < 0 for key in COST_KEYS):
        raise ValueError("invalid work count")
    return costs


def valid_divergence_step(step: Any, spec: RunSpec) -> bool:
    """0..steps-1 is a training step; steps_per_epoch means the post-epoch scoring pass."""
    return type(step) is int and 0 <= step <= spec.train_size // spec.batch_size


def validate_diverged_summary(summary: Any, spec: RunSpec, arm: str) -> None:
    keys = ("arm", "status", "diverged_epoch", "diverged_step", "diverged_reason", "completed_epochs", "initial_dev", "costs", "wall_s")
    summary = require_keys(summary, keys, arm + " divergence summary")
    if set(summary) != set(keys) or summary["arm"] != arm:
        raise ValueError("divergence summary must carry exactly its declared evidence")
    stop = summary["diverged_epoch"]
    if type(stop) is not int or not 0 <= stop < spec.epochs or summary["completed_epochs"] != stop:
        raise ValueError("divergence summary epoch mismatch")
    if not valid_divergence_step(summary["diverged_step"], spec) or not isinstance(summary["diverged_reason"], str):
        raise ValueError("divergence summary step/reason invalid")
    marker = validate_initial_dev(summary["initial_dev"], spec, arm + ".initial_dev")
    if marker != ((stop, summary["diverged_step"], summary["diverged_reason"]) == (0, 0, NON_FINITE_INITIAL_REASON)):
        raise ValueError("non-finite initial marker must coincide with a divergence at initial scoring")
    # Work is charged for completed epochs only; a partial or unscored epoch is not charged (definitional).
    if validate_costs(summary["costs"], arm)["host_train_examples"] != stop * spec.train_size:
        raise ValueError("divergence summary work mismatch")
    require_number(summary["wall_s"], arm + " wall time")


def _number_or_tag(value: Any) -> bool:
    return value in ("nan", "inf", "-inf") or (type(value) in (int, float) and math.isfinite(value))


def validate_witness(witness: Any, spec: RunSpec, context: str) -> None:
    """Recorded mechanism witnesses (docs/bounded-lifecycle-v2.md); v2's clamp is checked, not trusted."""
    if witness == {"seed_present": False}:
        return
    witness = require_keys(witness, ("seed_present", "gain_min", "gain_max"), context + " witness")
    if witness["seed_present"] is not True or not set(witness) <= {"seed_present", "gain_min", "gain_max", "ste", "rms_ratio_blend_entry"}:
        raise ValueError(context + " witness carries unknown evidence")
    if not all(_number_or_tag(witness[k]) for k in ("gain_min", "gain_max")):
        raise ValueError(context + " witness gain range invalid")
    if "rms_ratio_blend_entry" in witness and not _number_or_tag(witness["rms_ratio_blend_entry"]):
        raise ValueError(context + " witness blend-entry ratio invalid")
    if "ste" in witness:
        table = require_keys(witness["ste"], ("kappa_live", "lam_t", "gain", "clamped"), context + " STE table")
        widths = {len(column) if isinstance(column, list) else -1 for column in table.values()}
        if set(table) != {"kappa_live", "lam_t", "gain", "clamped"} or len(widths) != 1 or widths == {0} or -1 in widths:
            raise ValueError(context + " STE table must be four equal, non-empty columns")
        cfg = spec.kernel_config()
        bound = spec.trust_safety * c_star(cfg) * (1 + 1e-9)
        for kappa, lam_t, gain, clamped in zip(table["kappa_live"], table["lam_t"], table["gain"], table["clamped"], strict=True):
            if not (_number_or_tag(kappa) and _number_or_tag(gain) and type(lam_t) in (int, float) and type(clamped) is bool):
                raise ValueError(context + " STE row invalid")
            if spec.lifecycle == "v1" and (lam_t != cfg.lam or clamped):
                raise ValueError(context + " v1 must never clamp lambda")
            if spec.lifecycle == "v2" and (lam_t > cfg.lam or clamped != (lam_t < cfg.lam)):
                raise ValueError(context + " v2 lambda clamp inconsistent")
            if spec.lifecycle == "v2" and isinstance(kappa, float | int) and kappa * lam_t / cfg.lam > bound:
                raise ValueError(context + " v2 effective curvature exceeds the declared bound")


def validate_record(record: Any, spec: RunSpec, arm: str, kind: str, epoch: int | None) -> None:
    record = require_keys(record, ("schema_version", "arm", "kind", "birth"), "training record")
    if type(record["schema_version"]) is not int or record["schema_version"] != SCHEMA or record["arm"] != arm or record["kind"] != kind:
        raise ValueError("training evidence order/schema mismatch")
    if kind == "diverged":
        require_keys(record, ("epoch", "step", "reason", "stage", "witness"), arm + " divergence")
        validate_witness(record["witness"], spec, arm + " divergence")
        if type(record["epoch"]) is not int or record["epoch"] != epoch or not valid_divergence_step(record["step"], spec):
            raise ValueError("divergence record mismatch")
        if not isinstance(record["reason"], str) or not record["reason"]:
            raise ValueError("divergence record needs a reason")
    elif kind == "arm_start":
        require_keys(record, ("host_initial_parameter_sha256", "initial_dev"), arm + " start")
        validate_hash(record["host_initial_parameter_sha256"], arm + " initial host")
        validate_initial_dev(record["initial_dev"], spec, arm + " initial development")
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
            "witness",
        )
        require_keys(record, keys, arm + " epoch")
        validate_witness(record["witness"], spec, arm + " epoch")
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
    born = (kind == "arm_start" and arm == "static") or (kind in ("epoch", "diverged") and arm == "scheduled" and epoch == spec.graft_epoch)
    if born:
        birth = require_keys(
            record["birth"],
            (
                "body_init_sha256",
                "seed_before_calibration_sha256",
                "seed_birth_sha256",
                "gain_at_birth",
                "calibration_examples",
                "calibration_inputs_sha256",
                "realised_ratio_at_birth",
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
            "calibration_inputs_sha256",
        ):
            validate_hash(birth[name], arm + "." + name)
        require_number(birth["gain_at_birth"], arm + " gain")
        if birth["calibration_examples"] != min(spec.batch_size, spec.train_size):
            raise ValueError("calibration count mismatch")
    elif record["birth"] is not None:
        raise ValueError("unexpected germination evidence")


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


def runtime(spec: RunSpec) -> dict[str, Any]:
    import torchvision

    identity: dict[str, Any] = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "threads": spec.threads,
        "device": spec.device,
        "deterministic": torch.are_deterministic_algorithms_enabled(),
        "mkldnn": torch.backends.mkldnn.enabled,
        "default_dtype": str(torch.get_default_dtype()),
    }
    if spec.device == "cuda":  # Exactness is per SKU, driver and build: record them so replay can refuse a mismatch.
        identity.update(
            {
                "gpu_name": torch.cuda.get_device_name(0),
                "cuda": torch.version.cuda,
                "cudnn": torch.backends.cudnn.version(),  # type: ignore[no-untyped-call]
                "cudnn_deterministic": torch.backends.cudnn.deterministic,
                "cudnn_benchmark": torch.backends.cudnn.benchmark,
                "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
                "tf32_cudnn": torch.backends.cudnn.allow_tf32,
                "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG", ""),
            }
        )
    return identity


def configure(spec: RunSpec) -> None:
    spec.validate()
    torch.set_num_threads(spec.threads)
    torch.use_deterministic_algorithms(True)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cpu")  # Tensors are moved explicitly; nothing is created on a GPU implicitly.
    if spec.device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("device cuda requested but no CUDA device is visible")
        enable_class1()  # Deterministic algorithms, cuDNN deterministic, no benchmark, no TF32, fixed cuBLAS workspace.
        torch.cuda.manual_seed_all(derive(spec.seed, "process-global-cuda"))
    # Pin the CPU process stream, without letting ambient interpreter startup RNG change trace identities.
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


def git_identity(repo: Path = REPO) -> dict[str, Any]:
    """The commit and tree status, or the recorded identity of an immutable launch snapshot."""
    marker = repo / "SNAPSHOT.json"
    if marker.is_file():
        snapshot = read_json(marker)
        return {"commit": snapshot["commit"], "status": ""}

    def run(*args: str) -> str:
        return subprocess.run(["git", "--no-optional-locks", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()

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
    if any(p.is_cuda for p in host.parameters()):  # GPU lineage: the CUDA stream is part of the state (GPU probe).
        h.update(tensor_hash(torch.cuda.get_rng_state()).encode())
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
                    raise NonFiniteError("non-finite scoring logits")
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


def realised_ratio_at_birth(host: Any, seed: Any, calibration: torch.Tensor) -> float:
    """Witness for tau: rms(delta)/rms(h) on TRAIN-mode features, all BN buffers restored (simic-e3803e8200)."""
    modules = [host, seed]
    saved = [(buffer, buffer.detach().clone()) for module in modules for buffer in module.buffers()]
    modes = [(m, m.training) for module in modules for m in module.modules()]
    try:
        host.train()
        seed.train()
        with torch.no_grad():
            h = host.forward_to_slot(normalize_u8(calibration))
            return float(seed(h).pow(2).mean().sqrt() / h.pow(2).mean().sqrt().clamp_min(1e-12))
    finally:
        for buffer, value in saved:
            buffer.copy_(value)
        for m, mode in modes:
            m.train(mode)


def attach_seed(host: Any, slot: Slot, opt: torch.optim.SGD, spec: RunSpec, fit_x: torch.Tensor, *, static: bool) -> dict[str, Any]:
    """Germinate once; the gain is calibrated on fit inputs, never development data."""
    if slot.seed is not None or slot.stage is not Stage.DORMANT:
        raise RuntimeError("one lifetime germination attempt allowed")
    seed = build_seed(spec.seed_type, 64, derive(spec.seed, "seed-body-init")).to(fit_x.device)
    body_before = parameter_hash(seed, body_only=True)
    buffers_before = state_hash(seed)
    host_before, opt_before = state_hash(host), optimizer_host_hash(opt)
    prior = host.training
    host.eval()
    try:
        with torch.no_grad():
            calibration = fit_x[: spec.batch_size]
            features = host.forward_to_slot(normalize_u8(calibration))
        tau_init(seed, features, spec.kernel_config())  # sets seed.gain; the birth record reads it back
    finally:
        host.train(prior)
    realised = realised_ratio_at_birth(host, seed, calibration)
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
        "gain_at_birth": float(seed.gain.detach()),  # The stored float32 value, not tau_init's float64 (theory review).
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
    }


class NonFiniteError(ValueError):
    """Raised by every non-finite detector; training converts it into a recorded arm divergence."""


class ArmDivergedError(ValueError):
    """An arm's training became non-finite. Recorded as a measured outcome, never a unit abort (PDR-0047)."""

    def __init__(self, *, epoch: int, step: int, reason: str, stage: str = "", witness: dict[str, Any] | None = None) -> None:
        super().__init__(f"{reason} (epoch {epoch}, step {step})")
        self.epoch, self.step, self.reason = epoch, step, reason
        self.stage = stage
        self.witness: dict[str, Any] = witness if witness is not None else {"seed_present": False}


def draw_future(seed: int, n_train: int, epochs: int, cfg: Any) -> CommonFuture:
    """The run's common future, prefix-stable across horizons (rung-4 statistics review).

    The kernel's CommonFuture.draw takes every epoch's order, then all crops, then all flips
    from one generator, so a 20-epoch draw shares only the order prefix of a 10-epoch one and
    a horizon contrast is paired in name only. Here each epoch draws from its own derived
    generator, so a longer run replays a shorter one bitwise over their shared epochs.
    """
    bs = cfg.batch_size
    steps = n_train // bs
    if steps == 0:
        raise ValueError(f"n_train={n_train} < batch_size={bs}: zero steps per epoch")
    orders, crops, flips = [], [], []
    for epoch in range(epochs):
        g = make_generator(derive(seed, "epoch", epoch))
        orders.append(torch.randperm(n_train, generator=g)[: steps * bs])
        crops.append(torch.randint(0, 9, (steps, bs, 2), generator=g, dtype=torch.uint8))
        flips.append(torch.rand(steps, bs, generator=g) < 0.5)
    order, crop, flip = torch.stack(orders), torch.stack(crops), torch.stack(flips)
    h = hashlib.sha256()
    for t in (order, crop, flip):
        h.update(t.numpy().tobytes())
    return CommonFuture(order, crop, flip, epochs, h.hexdigest())


def c_star(cfg: Any) -> float:
    """Nesterov momentum-SGD stability limit on curvature along one direction (dampening 0)."""
    return float(2 * (1 + cfg.momentum) / (cfg.seed_lr * (1 + 2 * cfg.momentum)))


def tagged(value: float) -> float | str:
    """JSON-safe number: non-finite values become explicit tags, never null or a silent zero."""
    return value if math.isfinite(value) else ("nan" if math.isnan(value) else ("inf" if value > 0 else "-inf"))


class ScaleAwareSlot(Slot):
    """Kernel Slot plus a recorded trust-region witness; v2 clamps lambda so kappa <= s*c* every STE step.

    v1 returns exactly the kernel's trust term. The witness's extra seed forward restores any
    BatchNorm buffers it touches, so recording never changes training.
    """

    def __init__(self, spec: RunSpec) -> None:
        super().__init__()
        self.lifecycle, self.trust_safety = spec.lifecycle, spec.trust_safety
        self.last_witness: dict[str, Any] | None = None

    def _raw_output_energy(self, h: torch.Tensor) -> torch.Tensor:
        """mean(f(h)^2) from a throwaway copy of the seed.

        Restoring buffers in place mid-step would invalidate tensors autograd saved. A copy has
        its own buffers, and train-mode BatchNorm normalises with batch statistics, so the copy
        computes the same f the step used.
        """
        assert self.seed is not None
        with torch.no_grad():
            return copy.deepcopy(self.seed).f(h).pow(2).mean()

    def trust_region_loss(self, cfg: Any) -> torch.Tensor:
        if self.stage is not Stage.TRAINING or self.seed is None or self.last_delta is None or self.last_h is None:
            self.last_witness = None
            return torch.zeros(())
        if self.beta != 0.0:
            raise RuntimeError("STE invariant: beta must be 0 during TRAINING")
        h = self.last_h.detach()
        denominator = h.pow(2).mean().clamp_min(1e-12)
        # The witness and the clamp derive from the same two float64 scalars, so the recorded
        # effective curvature meets the bound exactly; float32 rounded each separately (dry run).
        d_t, s_t = float(denominator), float(self._raw_output_energy(h))
        kappa = 2 * cfg.lam * s_t / d_t  # d_t >= 1e-12; a non-finite s_t stays non-finite and is tagged
        lam_t = cfg.lam
        if self.lifecycle == "v2" and math.isfinite(kappa) and s_t > 0:
            lam_t = min(cfg.lam, self.trust_safety * c_star(cfg) * d_t / (2 * s_t))
            if lam_t < cfg.lam:  # Record the float32 lambda the loss multiplies, rounded toward zero (theory review).
                lam32 = torch.tensor(lam_t, dtype=torch.float32)
                if float(lam32) > lam_t:
                    lam32 = torch.nextafter(lam32, torch.zeros_like(lam32))
                lam_t = float(lam32)
        self.last_witness = {"kappa_live": kappa, "lam_t": lam_t, "clamped": lam_t < cfg.lam, "gain": float(self.seed.gain.detach())}
        loss: torch.Tensor
        if lam_t == cfg.lam:  # Exactly the kernel's expression (v1, or v2 where v1 is safe).
            loss = cfg.lam * self.last_delta.pow(2).mean() / self.last_h.detach().pow(2).mean().clamp_min(1e-12)
        else:
            loss = lam_t * self.last_delta.pow(2).mean() / denominator
        return loss


ARM_STATUSES = ("completed", "diverged")
NON_FINITE_INITIAL = {"status": "non-finite"}  # Explicit marker, never a silent null (ADR-0006).
NON_FINITE_INITIAL_REASON = "non-finite initial scoring"


def validate_initial_dev(initial_dev: Any, spec: RunSpec, context: str) -> bool:
    """Metrics, or the explicit non-finite marker. Returns True for the marker."""
    if initial_dev == NON_FINITE_INITIAL:
        return True
    validate_metrics(initial_dev, spec.dev_size, context)
    return False


def grad_norm(params: Iterable[torch.Tensor]) -> float:
    total = 0.0
    for param in params:
        if param.grad is not None:
            if not bool(torch.isfinite(param.grad).all()):
                raise NonFiniteError("non-finite gradient")
            total += float(param.grad.detach().square().sum())
    return math.sqrt(total)


def train_epoch(
    host: Any, slot: ScaleAwareSlot, opt: torch.optim.SGD, spec: RunSpec, future: CommonFuture, x: torch.Tensor, y: torch.Tensor, epoch: int
) -> dict[str, Any]:
    if not isinstance(slot, ScaleAwareSlot):
        raise TypeError("the bounded runner trains through ScaleAwareSlot so every STE step is witnessed")
    host.train()
    slot.train()
    start_stage = slot.stage.value
    ce_sum, objective_sum = 0.0, 0.0
    max_grads = {"host": 0.0, "seed_body": 0.0, "seed_gain": 0.0}
    used_alpha, used_beta = [], []
    gains: list[float] = []
    ste: dict[str, list[Any]] = {"kappa_live": [], "lam_t": [], "gain": [], "clamped": []}
    blend_entry_before = slot.rms_ratio_blend_entry

    def witness() -> dict[str, Any]:
        if slot.seed is None:
            return {"seed_present": False}
        record: dict[str, Any] = {"seed_present": True, "gain_min": tagged(min(gains)) if gains else tagged(float(slot.seed.gain.detach()))}
        record["gain_max"] = tagged(max(gains)) if gains else record["gain_min"]
        if ste["kappa_live"]:
            record["ste"] = {k: [tagged(v) if isinstance(v, float) else v for v in values] for k, values in ste.items()}
        if blend_entry_before is None and slot.rms_ratio_blend_entry is not None:
            record["rms_ratio_blend_entry"] = tagged(float(slot.rms_ratio_blend_entry))
        return record

    order = future.order[epoch].reshape(-1, spec.batch_size)
    for step, idx in enumerate(order):
        used_alpha.append(slot.alpha)
        used_beta.append(slot.beta)
        logits = host(augment(x[idx], future.crops[epoch, step], future.flips[epoch, step]), slot)
        ce = torch.nn.functional.cross_entropy(logits, y[idx])
        objective = ce + slot.trust_region_loss(spec.kernel_config())
        if slot.seed is not None:
            gains.append(float(slot.seed.gain.detach()))
        if slot.last_witness is not None:
            for key in ste:
                ste[key].append(slot.last_witness[key])
        if not bool(torch.isfinite(objective)):
            raise ArmDivergedError(
                epoch=epoch, step=step, reason="non-finite training objective", stage=slot.stage.value, witness=witness()
            )
        opt.zero_grad(set_to_none=True)
        objective.backward()  # type: ignore[no-untyped-call]
        try:
            max_grads["host"] = max(max_grads["host"], grad_norm(host.parameters()))
            if slot.seed is not None:
                max_grads["seed_body"] = max(max_grads["seed_body"], grad_norm(p for n, p in slot.seed.named_parameters() if n != "gain"))
                max_grads["seed_gain"] = max(max_grads["seed_gain"], grad_norm([slot.seed.gain]))
        except NonFiniteError as error:
            raise ArmDivergedError(epoch=epoch, step=step, reason=str(error), stage=slot.stage.value, witness=witness()) from error
        opt.step()
        slot.step_tick(spec.kernel_config(), len(order))
        ce_sum += float(ce.detach()) * len(idx)
        objective_sum += float(objective.detach()) * len(idx)
    epoch_witness = witness()
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
        "witness": epoch_witness,
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
    configure(spec)
    if output.exists():
        raise FileExistsError("output must be a fresh directory; interrupted runs remain incomplete")
    tx, ty, dx, dy, provenance = load_fit_dev(spec, data_root)  # Provenance hashes are taken on CPU.
    device = torch.device(spec.device)
    tx, ty, dx, dy = (t.to(device) for t in (tx, ty, dx, dy))
    future = draw_future(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA,
        "spec": dataclasses.asdict(spec),
        "arms": list(ARMS),
        "host": f"kernel-demo-{spec.host}",
        "seed_type": spec.seed_type,
        "data": provenance,
        "source": source_identity(),
        "git": git_identity(),
        "runtime": runtime(spec),
        "common_future_sha256": future.hash,
        "host_init_seed": derive(spec.seed, "host-init"),
        "seed_body_init_seed": derive(spec.seed, "seed-body-init"),
        "process_global_cpu_seed": derive(spec.seed, "process-global-cpu"),
        "checkpoint_rule": "final-epoch-only-all-arms",
        "budget": "equal-examples-and-epochs-not-equal-compute",
        "scaffold_state": {
            "execution": "cpu-pinned-stack",
            "host_distribution": f"one-fixed-{spec.host}-CNN",
            "design_prior": f"one-human-authored-{spec.seed_type}",
            "counterfactual_anchor": "measured-no-growth",
        },
    }
    write_json(output / "manifest.json", manifest)
    manifest_hash = file_hash(output / "manifest.json")
    summaries: dict[str, dict[str, Any]] = {}
    record_count = 0
    with (output / "training.jsonl").open("x") as log:
        for arm in ARMS:
            started = time.perf_counter()
            host = build_host(spec.host, manifest["host_init_seed"]).to(device)
            slot = ScaleAwareSlot(spec)
            opt = build_optimizer(host, spec.kernel_config())
            host_initial = parameter_hash(host)
            base_params = sum(p.numel() for p in host.parameters())
            birth = attach_seed(host, slot, opt, spec, tx, static=True) if arm == "static" else None
            birth_divergence: ArmDivergedError | None = None
            try:
                initial_dev: dict[str, Any] = score(host, slot, dx, dy, spec.batch_size)
            except NonFiniteError:  # Flush F1: a non-finite birth is a recorded divergence, not a unit abort.
                initial_dev = dict(NON_FINITE_INITIAL)
                birth_witness: dict[str, Any] = {"seed_present": False}
                if slot.seed is not None:
                    gain = tagged(float(slot.seed.gain.detach()))
                    birth_witness = {"seed_present": True, "gain_min": gain, "gain_max": gain}
                birth_divergence = ArmDivergedError(
                    epoch=0,
                    step=0,
                    reason=NON_FINITE_INITIAL_REASON,
                    stage=slot.stage.value,
                    witness=birth_witness,
                )
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
            record_count += 1
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
            diverged: ArmDivergedError | None = birth_divergence
            for epoch in range(0 if birth_divergence is not None else spec.epochs):
                action = "GERMINATE" if arm == "scheduled" and epoch == spec.graft_epoch else "WAIT"
                if action == "GERMINATE":
                    birth = attach_seed(host, slot, opt, spec, tx, static=False)
                    costs["calibration_examples"] += birth["calibration_examples"]
                params = base_params + (0 if slot.seed is None else sum(p.numel() for p in slot.seed.parameters()))
                fully_coupled = slot.seed is not None and slot.alpha == slot.beta == 1.0
                epoch_started = time.perf_counter()
                metrics = None
                try:
                    metrics = train_epoch(host, slot, opt, spec, future, tx, ty, epoch)
                    dev = score(host, slot, dx, dy, spec.batch_size)
                except ArmDivergedError as stop:
                    diverged = stop
                    break
                except NonFiniteError as error:  # Scoring after the epoch's last step (step == steps per epoch).
                    assert metrics is not None
                    diverged = ArmDivergedError(
                        epoch=epoch,
                        step=spec.train_size // spec.batch_size,
                        reason=str(error),
                        stage=metrics["stage_after"],
                        witness=metrics["witness"],
                    )
                    break
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
                record_count += 1
                history.append(record)
            if diverged is not None:
                append_record(
                    log,
                    {
                        "schema_version": SCHEMA,
                        "kind": "diverged",
                        "arm": arm,
                        "epoch": diverged.epoch,
                        "step": diverged.step,
                        "reason": diverged.reason,
                        "stage": diverged.stage,
                        "witness": diverged.witness,
                        "birth": birth if arm == "scheduled" and diverged.epoch == spec.graft_epoch else None,
                    },
                )
                record_count += 1
                summaries[arm] = {
                    "arm": arm,
                    "status": "diverged",
                    "diverged_epoch": diverged.epoch,
                    "diverged_step": diverged.step,
                    "diverged_reason": diverged.reason,
                    "completed_epochs": len(history),
                    "initial_dev": initial_dev,
                    "costs": costs,
                    "wall_s": time.perf_counter() - started,
                }
                continue
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
                "status": "completed",
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
    arm_status = {arm: summaries[arm]["status"] for arm in ARMS}
    checkpoints = [f"{arm}.pt" for arm in ARMS if arm_status[arm] == "completed"]
    artifacts = {name: file_hash(output / name) for name in ("manifest.json", "training.jsonl", *checkpoints)}
    completion = {
        "schema_version": SCHEMA,
        "status": "complete",
        "record_count": record_count,
        "arm_status": arm_status,
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
    require_keys(complete, ("schema_version", "status", "record_count", "arm_status", "artifacts", "summaries"), "completion")
    arm_status = complete["arm_status"]
    if not isinstance(arm_status, dict) or set(arm_status) != set(ARMS) or any(arm_status[a] not in ARM_STATUSES for a in ARMS):
        raise ValueError("arm status must name every arm as completed or diverged")
    if type(complete["schema_version"]) is not int or complete["schema_version"] != SCHEMA or complete["status"] != "complete":
        raise ValueError("unsupported/incomplete completion record")
    expected_names = {"manifest.json", "training.jsonl", *(f"{arm}.pt" for arm in ARMS if arm_status[arm] == "completed")}
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
    configure(spec)
    if manifest["runtime"] != runtime(spec):
        raise ValueError("execution runtime mismatch")
    data = require_keys(
        manifest["data"],
        (
            "kind",
            "source_files",
            "outer_identity",
            "fit_sha256",
            "dev_sha256",
            "fit_size",
            "dev_size",
            "data_seed",
            "fit_calibration_prefix_sha256",
        ),
        "data provenance",
    )
    validate_hash(data["fit_sha256"], "fit data")
    validate_hash(data["fit_calibration_prefix_sha256"], "fit calibration prefix")
    if manifest["host"] != f"kernel-demo-{spec.host}" or manifest["seed_type"] != spec.seed_type:
        raise ValueError("manifest host/seed type disagree with the specification")
    validate_hash(data["dev_sha256"], "development data")
    validate_hash(manifest["common_future_sha256"], "common future")
    if data["fit_size"] != spec.train_size or data["dev_size"] != spec.dev_size or data["data_seed"] != spec.data_seed:
        raise ValueError("split specification mismatch")
    if not isinstance(complete["summaries"], dict) or set(complete["summaries"]) != set(ARMS):
        raise ValueError("missing required evidence: summary arm set")
    for arm in ARMS:
        if require_keys(complete["summaries"][arm], ("status",), arm + " summary")["status"] != arm_status[arm]:
            raise ValueError("summary status disagrees with arm status")
        validate_summary(complete["summaries"][arm], spec, arm)
    lines = _read_training_lines(root / "training.jsonl")
    expected: list[tuple[str, str, int | None]] = []
    for arm in ARMS:
        expected.append((arm, "arm_start", None))
        if arm_status[arm] == "completed":
            expected += [(arm, "epoch", e) for e in range(spec.epochs)]
        else:
            stop = complete["summaries"][arm]["diverged_epoch"]
            expected += [(arm, "epoch", e) for e in range(stop)] + [(arm, "diverged", stop)]
    if len(lines) != complete["record_count"] or len(lines) != len(expected) or any(not line.endswith("\n") for line in lines):
        raise ValueError("training evidence incomplete")
    records: dict[tuple[str, int | None], dict[str, Any]] = {}
    divergences: dict[str, dict[str, Any]] = {}
    for line, (arm, kind, epoch) in zip(lines, expected, strict=True):
        record = json.loads(line, object_pairs_hook=_pairs, parse_constant=_bad_constant)
        strict_json(record)
        validate_record(record, spec, arm, kind, epoch)
        if kind == "arm_start" and (record["initial_dev"] == NON_FINITE_INITIAL) != (
            arm_status[arm] == "diverged" and complete["summaries"][arm]["diverged_reason"] == NON_FINITE_INITIAL_REASON
        ):
            raise ValueError("arm start's initial scoring disagrees with the arm's divergence summary")
        if kind == "diverged":
            divergences[arm] = record
            summary = complete["summaries"][arm]
            if (record["epoch"], record["step"], record["reason"]) != (
                summary["diverged_epoch"],
                summary["diverged_step"],
                summary["diverged_reason"],
            ):
                raise ValueError("divergence record and summary do not agree")
        else:
            records[(arm, epoch)] = record
        if record["birth"] is not None and record["birth"]["calibration_inputs_sha256"] != data["fit_calibration_prefix_sha256"]:
            raise ValueError("seed calibration inputs are not the recorded fit prefix")
    verify_pairing(records, divergences, spec)
    return manifest, complete, spec


def verify_pairing(records: dict[tuple[str, int | None], dict[str, Any]], divergences: dict[str, dict[str, Any]], spec: RunSpec) -> None:
    """Arms of one unit share the host initialization, and the scheduled arm is the no-growth trajectory until germination."""
    if len({records[(arm, None)]["host_initial_parameter_sha256"] for arm in ARMS}) != 1:
        raise ValueError("pairing broken: arms start from different host initializations")
    for epoch in range(spec.graft_epoch):
        scheduled, baseline = records.get(("scheduled", epoch)), records.get(("no_growth", epoch))
        if (scheduled is None) != (baseline is None):
            raise ValueError(f"pairing broken: only one of scheduled/no growth reached epoch {epoch} before germination")
        if scheduled is None:  # Both stopped before germination: they must have diverged identically.
            fields = ("epoch", "step", "reason")
            if [divergences["scheduled"][f] for f in fields] != [divergences["no_growth"][f] for f in fields]:
                raise ValueError("pairing broken: scheduled and no growth diverged differently before germination")
            break
        if scheduled is not None and baseline is not None and scheduled["training_state_sha256"] != baseline["training_state_sha256"]:
            raise ValueError(f"pairing broken: scheduled diverged from no growth before germination (epoch {epoch})")


def _read_checkpoint(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=True)


def restore_checkpoint(root: Path, arm: str, manifest_hash: str, spec: RunSpec) -> tuple[Any, Slot]:
    if arm not in ARMS:
        raise ValueError("unknown arm")
    checkpoint = _read_checkpoint(root / f"{arm}.pt")
    if checkpoint["schema_version"] != SCHEMA or checkpoint["arm"] != arm or checkpoint["manifest_sha256"] != manifest_hash:
        raise ValueError("checkpoint identity mismatch")
    host = build_host(spec.host, derive(spec.seed, "host-init")).to(spec.device)
    host.load_state_dict(checkpoint["host"], strict=True)
    slot = ScaleAwareSlot(spec)
    if arm != "no_growth":
        slot.seed = build_seed(spec.seed_type, 64, derive(spec.seed, "seed-body-init"))
        slot.seed.to(spec.device)
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
    if any(status != "completed" for status in complete["arm_status"].values()):
        raise ValueError("outer evaluation requires every arm completed; this run has a diverged arm")
    # All checkpoints validated/materialized before opening outer data.
    models = {arm: restore_checkpoint(root, arm, complete["artifacts"]["manifest.json"], spec) for arm in ARMS}
    x, y, outer_identity = load_outer(spec, data_root, manifest["data"])
    x, y = x.to(spec.device), y.to(spec.device)
    started = time.perf_counter()
    untrained = score(build_host(spec.host, derive(spec.seed, "host-init")).to(spec.device), ScaleAwareSlot(spec), x, y, spec.batch_size)
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
        "runtime": runtime(spec),
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
            choices = {"host": PATHOLOGIES, "seed_type": SEED_NAMES}.get(field.name)
            training.add_argument("--" + field.name.replace("_", "-"), type=type(default), default=default, choices=choices)
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
