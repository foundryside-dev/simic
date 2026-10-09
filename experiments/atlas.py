"""Counterfactual atlas, fork core (PDR-0057 G0, item 2).

One unit trains a no-op trunk, snapshots it at declared decision points, and forks branches
from those snapshots: germinate a seed type now, or keep waiting. Every branch replays the frozen
bounded runner (`bounded_comparison.train`) bitwise:
- the trunk is the runner's no_growth arm;
- a no-op fork continues the trunk;
- a germination fork at epoch t is the runner's scheduled arm with graft_epoch = t.

The epoch loop is a copy of `train()`'s arm body, kept in step with it by the tests in
`tests/unit/test_atlas_fork.py`. `train()` itself stays frozen (its runs are evidence).

A snapshot is taken at an epoch boundary, before that epoch trains. It holds deep copies of the
host and seed tensors, the slot lifecycle and the optimizer state. Training draws nothing from
the global RNG streams (all randomness is in the common future, which is derived per epoch), so
the cursor is the epoch index and the global streams need no capture.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch

from experiments.bounded_comparison import (
    SCHEMA,
    ArmDivergedError,
    NonFiniteError,
    ScaleAwareSlot,
    attach_seed,
    configure,
    draw_future,
    score,
    strict_json,
    train_epoch,
)
from experiments.bounded_data import RunSpec, load_fit_dev, tensor_hash
from experiments.kernel_demo import (
    SEED_NAMES,
    CommonFuture,
    Stage,
    append_seed_group,
    build_host,
    build_optimizer,
    build_seed,
    derive,
)

LIFECYCLE_FIELDS = ("alpha", "beta", "_blend_step", "_fossil_step", "_epochs_in_stage", "rms_ratio_blend_entry")


@dataclass(frozen=True)
class Snapshot:
    """Training state at an epoch boundary, before `epoch` trains. Every tensor is a private copy."""

    epoch: int
    host: dict[str, torch.Tensor]
    seed: dict[str, torch.Tensor] | None
    seed_type: str | None
    stage: str
    lifecycle: dict[str, Any]
    alpha_beta_log: tuple[tuple[float, float], ...]
    optimizer: dict[str, Any]
    costs: dict[str, int]


@dataclass
class Span:
    """Epoch records from one trunk or branch, its snapshots, and how it ended."""

    records: list[dict[str, Any]] = field(default_factory=list)
    snapshots: dict[int, Snapshot] = field(default_factory=dict)
    diverged: dict[str, Any] | None = None
    costs: dict[str, int] = field(default_factory=dict)


Trunk = Span
Branch = Span


def _clone(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {k: v.detach().clone() for k, v in state.items()}


def take(host: Any, slot: ScaleAwareSlot, opt: torch.optim.SGD, costs: dict[str, int], epoch: int, seed_type: str | None) -> Snapshot:
    if (slot.seed is None) != (seed_type is None):
        raise ValueError("seed_type must name the installed seed, and only when one is installed")
    return Snapshot(
        epoch=epoch,
        host=_clone(host.state_dict()),
        seed=None if slot.seed is None else _clone(slot.seed.state_dict()),
        seed_type=seed_type,
        stage=slot.stage.value,
        lifecycle={name: getattr(slot, name) for name in LIFECYCLE_FIELDS},
        alpha_beta_log=tuple(tuple(pair) for pair in slot.alpha_beta_log),  # type: ignore[misc]
        optimizer=copy.deepcopy(opt.state_dict()),
        costs=dict(costs),
    )


def snapshot_digest(snap: Snapshot) -> str:
    """Content hash of a snapshot: used to prove branches never write through to it."""
    h = hashlib.sha256()
    for tensors in (snap.host, snap.seed or {}):
        for key in sorted(tensors):
            h.update(key.encode())
            h.update(tensor_hash(tensors[key]).encode())
    meta = {k: v for k, v in dataclasses.asdict(snap).items() if k not in ("host", "seed", "optimizer")}
    h.update(strict_json(meta).encode())
    for index, state in sorted(snap.optimizer["state"].items()):
        for key, value in sorted(state.items()):
            h.update(f"{index}:{key}".encode())
            h.update((tensor_hash(value) if isinstance(value, torch.Tensor) else strict_json(value)).encode())
    h.update(strict_json(snap.optimizer["param_groups"]).encode())
    return h.hexdigest()


def materialize(snap: Snapshot, spec: RunSpec, device: torch.device) -> tuple[Any, ScaleAwareSlot, torch.optim.SGD]:
    """Rebuild host, slot and optimizer from a snapshot. Seed groups are appended before momentum loads."""
    cfg = spec.kernel_config()
    host = build_host(spec.host, derive(spec.seed, "host-init")).to(device)
    host.load_state_dict(snap.host)
    slot = ScaleAwareSlot(spec)
    opt = build_optimizer(host, cfg)
    if snap.seed is not None:
        assert snap.seed_type is not None
        seed = build_seed(snap.seed_type, 64, derive(spec.seed, "seed-body-init")).to(device)
        seed.load_state_dict(snap.seed)
        append_seed_group(opt, seed, cfg)  # load_state_dict matches groups by position: append first
        slot.seed = seed
    opt.load_state_dict(copy.deepcopy(snap.optimizer))
    slot.stage = Stage(snap.stage)
    for name, value in snap.lifecycle.items():
        setattr(slot, name, value)
    slot.alpha_beta_log = [tuple(pair) for pair in snap.alpha_beta_log]  # type: ignore[misc]
    return host, slot, opt


@dataclass
class Unit:
    """One seed's data, common future and device: the frame every trunk and branch shares."""

    spec: RunSpec
    tx: torch.Tensor
    ty: torch.Tensor
    dx: torch.Tensor
    dy: torch.Tensor
    future: CommonFuture
    device: torch.device

    @classmethod
    def load(cls, spec: RunSpec, data_root: Path | None = None) -> Unit:
        configure(spec)
        tx, ty, dx, dy, _provenance = load_fit_dev(spec, data_root)
        device = torch.device(spec.device)
        tx, ty, dx, dy = (t.to(device) for t in (tx, ty, dx, dy))
        future = draw_future(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
        return cls(spec, tx, ty, dx, dy, future, device)

    def trunk(self, decision_points: tuple[int, ...]) -> Trunk:
        host = build_host(self.spec.host, derive(self.spec.seed, "host-init")).to(self.device)
        slot = ScaleAwareSlot(self.spec)
        opt = build_optimizer(host, self.spec.kernel_config())
        costs = {
            "host_train_examples": 0,
            "seed_train_examples": 0,
            "host_dev_examples": len(self.dy),  # the runner's initial scoring
            "seed_dev_examples": 0,
            "installed_parameter_epochs": 0,
            "optimizer_parameter_epochs": 0,
            "calibration_examples": 0,
            "optimizer_parameter_steps": 0,
            "fully_coupled_optimizer_steps": 0,
        }
        return self._run(host, slot, opt, costs, start=0, germinate=None, seed_type=None, snapshot_at=decision_points)

    def branch(self, snap: Snapshot, action: str | None, snapshot_at: tuple[int, ...] = ()) -> Branch:
        """Fork from a snapshot: `action` is a seed type to germinate now, or None to keep waiting."""
        if action is not None and action not in SEED_NAMES:
            raise ValueError(f"action must be None (no-op) or one of {SEED_NAMES}")
        host, slot, opt = materialize(snap, self.spec, self.device)
        return self._run(
            host, slot, opt, dict(snap.costs), start=snap.epoch, germinate=action, seed_type=snap.seed_type, snapshot_at=snapshot_at
        )

    def _run(
        self,
        host: Any,
        slot: ScaleAwareSlot,
        opt: torch.optim.SGD,
        costs: dict[str, int],
        *,
        start: int,
        germinate: str | None,
        seed_type: str | None,
        snapshot_at: tuple[int, ...],
    ) -> Span:
        """`train()`'s arm body from `start`, germinating `germinate` before `start` trains."""
        spec, tx, ty, dx, dy = self.spec, self.tx, self.ty, self.dx, self.dy
        span = Span(costs=costs)
        base_params = sum(p.numel() for p in host.parameters())
        for epoch in range(start, spec.epochs):
            if epoch in snapshot_at:
                span.snapshots[epoch] = take(host, slot, opt, costs, epoch, seed_type)
            action = "GERMINATE" if germinate is not None and epoch == start else "WAIT"
            birth = None
            if action == "GERMINATE":
                assert germinate is not None
                birth = attach_seed(host, slot, opt, dataclasses.replace(spec, seed_type=germinate), tx, static=False)
                seed_type = germinate
                costs["calibration_examples"] += birth["calibration_examples"]
            params = base_params + (0 if slot.seed is None else sum(p.numel() for p in slot.seed.parameters()))
            fully_coupled = slot.seed is not None and slot.alpha == slot.beta == 1.0
            metrics = None
            try:
                metrics = train_epoch(host, slot, opt, spec, self.future, tx, ty, epoch)
                dev = score(host, slot, dx, dy, spec.batch_size)
            except ArmDivergedError as stop:
                span.diverged = {
                    "epoch": stop.epoch,
                    "step": stop.step,
                    "reason": stop.reason,
                    "stage": stop.stage,
                    "witness": stop.witness,
                }
                break
            except NonFiniteError as error:
                assert metrics is not None
                span.diverged = {
                    "epoch": epoch,
                    "step": spec.train_size // spec.batch_size,
                    "reason": str(error),
                    "stage": metrics["stage_after"],
                    "witness": metrics["witness"],
                }
                break
            costs["host_train_examples"] += len(ty)
            costs["seed_train_examples"] += len(ty) if slot.seed is not None else 0
            costs["host_dev_examples"] += len(dy)
            costs["seed_dev_examples"] += len(dy) if slot.seed is not None else 0
            costs["installed_parameter_epochs"] += params
            costs["optimizer_parameter_epochs"] += sum(p.numel() for group in opt.param_groups for p in group["params"])
            costs["optimizer_parameter_steps"] += params * metrics["optimizer_steps"]
            costs["fully_coupled_optimizer_steps"] += metrics["optimizer_steps"] if fully_coupled else 0
            span.records.append(
                {
                    "schema_version": SCHEMA,
                    "kind": "epoch",
                    "arm": "scheduled" if seed_type is not None else "no_growth",
                    "epoch": epoch,
                    "requested_action": action,
                    "executed_action": action,
                    "action_legal": True,
                    "birth": birth,
                    "installed_parameters": params,
                    "seed_executed_train_examples": len(ty) if slot.seed is not None else 0,
                    "dev": dev,
                    "wall_s": 0.0,
                    **metrics,
                }
            )
        return span
