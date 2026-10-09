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
host and seed tensors, the slot lifecycle, the optimizer state, the global RNG states, and the
replicate future it was trained on. Training draws nothing from the global RNG streams (all
randomness is in the common future, derived per epoch), so the data cursor is the epoch index.
The streams are still captured and restored, because `training_state_sha256` hashes them: an
ambient draw between forks would otherwise change every record's identity (code review W1).
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch

from experiments.atlas_hosts import HostConfig, config_hash
from experiments.atlas_hosts import build as build_config_host
from experiments.bounded_comparison import (
    NON_FINITE_INITIAL,
    NON_FINITE_INITIAL_REASON,
    SCHEMA,
    ArmDivergedError,
    NonFiniteError,
    ScaleAwareSlot,
    append_record,
    attach_seed,
    configure,
    draw_future,
    git_identity,
    parameter_hash,
    read_json,
    runtime,
    score,
    source_identity,
    strict_json,
    train_epoch,
    write_json,
)
from experiments.bounded_data import RunSpec, file_hash, load_fit_dev, tensor_hash
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
    cpu_rng: torch.Tensor
    cuda_rng: torch.Tensor | None
    replicate: int  # the future this state was trained on (code review W2)
    future_from: int  # where that replicate's future was spliced in (0 for replicate 0)


@dataclass
class Span:
    """Epoch records from one trunk or branch, its snapshots, and how it ended."""

    records: list[dict[str, Any]] = field(default_factory=list)
    snapshots: dict[int, Snapshot] = field(default_factory=dict)
    diverged: dict[str, Any] | None = None
    costs: dict[str, int] = field(default_factory=dict)
    replicate: int = 0
    future_hash: str = ""
    future_from: int = 0
    initial_dev: dict[str, Any] | None = None  # trunk and static only: the runner's initial scoring
    birth: dict[str, Any] | None = None  # static only: the birth record the runner writes at arm start


Trunk = Span
Branch = Span


def _clone(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {k: v.detach().clone() for k, v in state.items()}


def take(
    host: Any,
    slot: ScaleAwareSlot,
    opt: torch.optim.SGD,
    costs: dict[str, int],
    epoch: int,
    seed_type: str | None,
    *,
    replicate: int = 0,
    future_from: int = 0,
) -> Snapshot:
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
        cpu_rng=torch.get_rng_state().clone(),
        cuda_rng=torch.cuda.get_rng_state().clone() if any(p.is_cuda for p in host.parameters()) else None,
        replicate=replicate,
        future_from=future_from,
    )


def snapshot_digest(snap: Snapshot) -> str:
    """Content hash of a snapshot: used to prove branches never write through to it."""
    h = hashlib.sha256()
    for tensors in (snap.host, snap.seed or {}):
        for key in sorted(tensors):
            h.update(key.encode())
            h.update(tensor_hash(tensors[key]).encode())
    meta = {k: v for k, v in dataclasses.asdict(snap).items() if k not in ("host", "seed", "optimizer", "cpu_rng", "cuda_rng")}
    h.update(strict_json(meta).encode())
    for rng in (snap.cpu_rng, snap.cuda_rng):
        h.update(b"none" if rng is None else tensor_hash(rng).encode())
    for index, state in sorted(snap.optimizer["state"].items()):
        for key, value in sorted(state.items()):
            h.update(f"{index}:{key}".encode())
            h.update((tensor_hash(value) if isinstance(value, torch.Tensor) else strict_json(value)).encode())
    h.update(strict_json(snap.optimizer["param_groups"]).encode())
    return h.hexdigest()


def splice_future(base: CommonFuture, replacement: CommonFuture, from_epoch: int) -> CommonFuture:
    """Epochs before `from_epoch` from `base`, the rest from `replacement`, hashed like `draw_future`."""
    if base.epochs != replacement.epochs or not 0 <= from_epoch <= base.epochs:
        raise ValueError("futures must share a horizon, and the splice point must lie within it")
    parts = [torch.cat([getattr(base, n)[:from_epoch], getattr(replacement, n)[from_epoch:]]) for n in ("order", "crops", "flips")]
    h = hashlib.sha256()
    for t in parts:
        h.update(t.numpy().tobytes())
    return CommonFuture(parts[0], parts[1], parts[2], base.epochs, h.hexdigest())


def make_host(spec: RunSpec, host_cfg: HostConfig | None, device: torch.device) -> Any:
    """The kernel host for `spec.host`, or a config-built host (scaled or reference, `atlas_hosts`)."""
    init = derive(spec.seed, "host-init")
    return (build_host(spec.host, init) if host_cfg is None else build_config_host(host_cfg, init)).to(device)


def materialize(
    snap: Snapshot, spec: RunSpec, device: torch.device, host_cfg: HostConfig | None = None
) -> tuple[Any, ScaleAwareSlot, torch.optim.SGD]:
    """Rebuild host, slot and optimizer from a snapshot. Seed groups are appended before momentum loads."""
    cfg = spec.kernel_config()
    host = make_host(spec, host_cfg, device)
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
    torch.set_rng_state(snap.cpu_rng)
    if snap.cuda_rng is not None:
        torch.cuda.set_rng_state(snap.cuda_rng)
    return host, slot, opt


def _check_end_state(
    slot: ScaleAwareSlot, opt: torch.optim.SGD, base_params: int, *, fully_coupled_steps: int, learned: dict[str, bool]
) -> None:
    """The runner's end-of-run integrity checks (code reviews M2): coupling, optimizer ownership, learning."""
    params = [p for group in opt.param_groups for p in group["params"]]
    if len({id(p) for p in params}) != len(params):
        raise RuntimeError("duplicate optimizer membership")
    installed = base_params + (0 if slot.seed is None else sum(p.numel() for p in slot.seed.parameters()))
    if sum(p.numel() for p in params) != installed:
        raise RuntimeError("optimizer does not own exactly the installed parameters")
    if slot.seed is not None and (slot.stage is not Stage.FOSSILIZED or slot.alpha != 1.0 or slot.beta != 1.0 or fully_coupled_steps == 0):
        raise RuntimeError("incomplete final topology/coupling")
    if not learned["host"]:
        raise RuntimeError("host did not learn/update")
    if slot.seed is not None and not learned["seed"]:
        raise RuntimeError("seed body/gain did not learn/update")


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
    provenance: dict[str, Any] = field(default_factory=dict)
    cpu_rng: torch.Tensor | None = None  # the streams configure() pinned; every trunk starts from them
    cuda_rng: torch.Tensor | None = None
    host_cfg: HostConfig | None = None  # None: the kernel host for spec.host (legacy, rung-4 golden)

    @classmethod
    def load(cls, spec: RunSpec, data_root: Path | None = None, *, host_cfg: HostConfig | None = None) -> Unit:
        configure(spec)
        tx, ty, dx, dy, provenance = load_fit_dev(spec, data_root)
        device = torch.device(spec.device)
        tx, ty, dx, dy = (t.to(device) for t in (tx, ty, dx, dy))
        future = draw_future(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
        cuda_rng = torch.cuda.get_rng_state().clone() if device.type == "cuda" else None
        return cls(spec, tx, ty, dx, dy, future, device, provenance, torch.get_rng_state().clone(), cuda_rng, host_cfg)

    @property
    def host_label(self) -> str:
        return f"kernel-{self.spec.host}" if self.host_cfg is None else f"atlas-{self.host_cfg.name}-{config_hash(self.host_cfg)[:12]}"

    def _require_slot(self) -> None:
        """Seeds are built for the 64-channel stage-2 site; a scaled host has no slot."""
        if self.host_cfg is not None and self.host_cfg.w2 != 64:
            raise ValueError(f"host {self.host_cfg.name} has no 64-channel slot site; it is a no-growth comparator")

    def _fresh_costs(self) -> dict[str, int]:
        return {
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

    def _restore_pinned_rng(self) -> None:
        assert self.cpu_rng is not None
        torch.set_rng_state(self.cpu_rng)
        if self.cuda_rng is not None:
            torch.cuda.set_rng_state(self.cuda_rng)

    def static(self, seed_type: str) -> Span:
        """The runner's static arm: the seed attached fully coupled at birth, trained from step zero."""
        if seed_type not in SEED_NAMES:
            raise ValueError(f"seed_type must be one of {SEED_NAMES}")
        self._require_slot()
        self._restore_pinned_rng()
        spec = dataclasses.replace(self.spec, seed_type=seed_type)
        host = make_host(spec, self.host_cfg, self.device)
        slot = ScaleAwareSlot(spec)
        opt = build_optimizer(host, spec.kernel_config())
        birth = attach_seed(host, slot, opt, spec, self.tx, static=True)
        costs = self._fresh_costs()
        costs["seed_dev_examples"] = len(self.dy)
        costs["calibration_examples"] = birth["calibration_examples"]
        try:
            initial_dev: dict[str, Any] = score(host, slot, self.dx, self.dy, spec.batch_size)
        except NonFiniteError:
            failed = Span(costs=costs, future_hash=self.future.hash, initial_dev=dict(NON_FINITE_INITIAL), birth=birth)
            gain = float(slot.seed.gain.detach()) if slot.seed is not None else math.nan
            failed.diverged = {
                "epoch": 0,
                "step": 0,
                "reason": NON_FINITE_INITIAL_REASON,
                "stage": slot.stage.value,
                "witness": {"seed_present": True, "gain_min": gain, "gain_max": gain},
                "birth": birth,
            }
            return failed
        span = self._run(
            host,
            slot,
            opt,
            costs,
            start=0,
            germinate=None,
            seed_type=seed_type,
            snapshot_at=(),
            future=self.future,
            replicate=0,
            future_from=0,
            arm="static",
        )
        span.initial_dev, span.birth = initial_dev, birth
        return span

    def trunk(self, decision_points: tuple[int, ...]) -> Trunk:
        self._restore_pinned_rng()
        host = make_host(self.spec, self.host_cfg, self.device)
        slot = ScaleAwareSlot(self.spec)
        opt = build_optimizer(host, self.spec.kernel_config())
        costs = self._fresh_costs()
        try:
            initial_dev: dict[str, Any] = score(host, slot, self.dx, self.dy, self.spec.batch_size)
        except NonFiniteError:  # The runner's non-finite birth: a recorded divergence, not an abort (code review M3).
            failed = Span(costs=costs, future_hash=self.future.hash, initial_dev=dict(NON_FINITE_INITIAL))
            failed.diverged = {
                "epoch": 0,
                "step": 0,
                "reason": NON_FINITE_INITIAL_REASON,
                "stage": slot.stage.value,
                "witness": {"seed_present": False},
                "birth": None,
            }
            return failed
        span = self._run(
            host,
            slot,
            opt,
            costs,
            start=0,
            germinate=None,
            seed_type=None,
            snapshot_at=decision_points,
            future=self.future,
            replicate=0,
            future_from=0,
        )
        span.initial_dev = initial_dev
        return span

    def future_for(self, replicate: int, from_epoch: int) -> CommonFuture:
        """Replicate r of the future from `from_epoch` on. Replicate 0 is the common future itself.

        Each replicate draws from `derive(seed, "common-future", r)` with `draw_future`'s per-epoch
        generators, so replicates are prefix-stable across horizons like the common future.
        """
        if type(replicate) is not int or replicate < 0:
            raise ValueError("replicate must be a non-negative integer")
        if replicate == 0:
            return self.future
        drawn = draw_future(derive(self.spec.seed, "common-future", replicate), len(self.ty), self.spec.epochs, self.spec.kernel_config())
        return splice_future(self.future, drawn, from_epoch)

    def branch(self, snap: Snapshot, action: str | None, snapshot_at: tuple[int, ...] = (), replicate: int | None = None) -> Branch:
        """Fork from a snapshot: `action` is a seed type to germinate now, or None to keep waiting.

        `replicate` redraws the future from the snapshot on. A snapshot taken inside a replicate
        already carries that replicate's past, so it can only continue it.
        """
        if action is not None and action not in SEED_NAMES:
            raise ValueError(f"action must be None (no-op) or one of {SEED_NAMES}")
        if action is not None:
            self._require_slot()
        if action is not None:  # the runner's own rule: the whole lifecycle plus a coupled epoch fit (code review M1)
            dataclasses.replace(self.spec, graft_epoch=snap.epoch).validate()
        rep = snap.replicate if replicate is None else replicate
        if snap.replicate != 0 and rep != snap.replicate:
            raise ValueError(f"replicate mismatch: the snapshot was trained on replicate {snap.replicate}")
        future_from = snap.future_from if snap.replicate != 0 else snap.epoch
        future = self.future_for(rep, future_from)
        host, slot, opt = materialize(snap, self.spec, self.device, self.host_cfg)
        return self._run(
            host,
            slot,
            opt,
            dict(snap.costs),
            start=snap.epoch,
            germinate=action,
            seed_type=snap.seed_type,
            snapshot_at=snapshot_at,
            future=future,
            replicate=rep,
            future_from=0 if rep == 0 else future_from,
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
        future: CommonFuture,
        replicate: int,
        future_from: int,
        arm: str | None = None,
    ) -> Span:
        """`train()`'s arm body from `start`, germinating `germinate` before `start` trains."""
        spec, tx, ty, dx, dy = self.spec, self.tx, self.ty, self.dx, self.dy
        span = Span(costs=costs, replicate=replicate, future_hash=future.hash, future_from=future_from)
        base_params = sum(p.numel() for p in host.parameters())
        host_before = parameter_hash(host)

        def seed_hashes() -> tuple[str, float] | None:
            return None if slot.seed is None else (parameter_hash(slot.seed, body_only=True), float(slot.seed.gain.detach()))

        seed_before = seed_hashes()
        grads = {"host": 0.0, "seed_body": 0.0, "seed_gain": 0.0}
        for epoch in range(start, spec.epochs):
            if epoch in snapshot_at:
                span.snapshots[epoch] = take(host, slot, opt, costs, epoch, seed_type, replicate=replicate, future_from=future_from)
            action = "GERMINATE" if germinate is not None and epoch == start else "WAIT"
            birth = None
            if action == "GERMINATE":
                assert germinate is not None
                birth = attach_seed(host, slot, opt, dataclasses.replace(spec, seed_type=germinate), tx, static=False)
                seed_before = (birth["body_init_sha256"], birth["gain_at_birth"])
                seed_type = germinate
                costs["calibration_examples"] += birth["calibration_examples"]
            params = base_params + (0 if slot.seed is None else sum(p.numel() for p in slot.seed.parameters()))
            fully_coupled = slot.seed is not None and slot.alpha == slot.beta == 1.0
            metrics = None
            try:
                metrics = train_epoch(host, slot, opt, spec, future, tx, ty, epoch)
                dev = score(host, slot, dx, dy, spec.batch_size)
            except ArmDivergedError as stop:
                span.diverged = {
                    "epoch": stop.epoch,
                    "step": stop.step,
                    "reason": stop.reason,
                    "stage": stop.stage,
                    "witness": stop.witness,
                    "birth": birth,  # the runner keeps the birth record on a germination-epoch divergence (code review W3)
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
                    "birth": birth,
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
                    "arm": arm if arm is not None else ("scheduled" if seed_type is not None else "no_growth"),
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
        if span.diverged is None:
            for record in span.records:
                for name in grads:
                    grads[name] = max(grads[name], record["gradient_norm_max"][name])
            after = seed_hashes()
            learned = {
                "host": parameter_hash(host) != host_before and grads["host"] > 0,
                "seed": after is not None
                and seed_before is not None
                and after[0] != seed_before[0]
                and after[1] != seed_before[1]
                and grads["seed_body"] > 0
                and grads["seed_gain"] > 0,
            }
            _check_end_state(slot, opt, base_params, fully_coupled_steps=costs["fully_coupled_optimizer_steps"], learned=learned)
        return span


# --- Unit records (PDR-0057 G0, item 5) ---

ATLAS_SCHEMA = "atlas-v0"
NOOP = "noop"
LATE_EPOCHS = 3
CHANCE_CE = math.log(10)  # a diverged branch scores chance-level CE; it is never dropped (PDR-0057)


def _plain(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "wall_s"}


def _late_ce(span: Span, epochs: int) -> float | None:
    if span.diverged is not None:
        return None
    late = [r["dev"]["ce"] for r in span.records if r["epoch"] >= epochs - LATE_EPOCHS]
    if len(late) != LATE_EPOCHS:
        raise RuntimeError("a completed branch must cover the late window")
    return float(sum(late) / LATE_EPOCHS)


def _check_plan(spec: RunSpec, decision_points: tuple[int, ...], actions: tuple[str, ...], replicates: tuple[int, ...]) -> None:
    if not decision_points or list(decision_points) != sorted(set(decision_points)):
        raise ValueError("decision points must be non-empty, sorted and distinct")
    for t in decision_points:  # the runner's own rule: the whole lifecycle plus a coupled epoch fit after t
        dataclasses.replace(spec, graft_epoch=t).validate()
    if not actions or len(set(actions)) != len(actions) or any(a not in SEED_NAMES for a in actions):
        raise ValueError(f"actions must be distinct seed types from {SEED_NAMES}")
    if 0 not in replicates or len(set(replicates)) != len(replicates) or any(type(r) is not int or r < 0 for r in replicates):
        raise ValueError("replicates must be distinct non-negative integers including 0 (the no-op twin check)")


def run_unit(
    spec: RunSpec,
    output: Path,
    data_root: Path | None,
    *,
    decision_points: tuple[int, ...],
    actions: tuple[str, ...],
    replicates: tuple[int, ...],
) -> dict[str, Any]:
    """One seed: a no-op trunk, then every (decision point, replicate, no-op or action) branch."""
    _check_plan(spec, decision_points, actions, replicates)
    if output.exists():
        raise FileExistsError("output must be a fresh directory")
    unit = Unit.load(spec, data_root)
    output.mkdir(parents=True)
    write_json(
        output / "manifest.json",
        {
            "schema": ATLAS_SCHEMA,
            "spec": dataclasses.asdict(spec),
            "plan": {"decision_points": list(decision_points), "actions": list(actions), "replicates": list(replicates)},
            "late_epochs": LATE_EPOCHS,
            "data": unit.provenance,
            "source": source_identity(),
            "git": git_identity(),
            "runtime": runtime(spec),
            "common_future_sha256": unit.future.hash,
            "host_init_seed": derive(spec.seed, "host-init"),
            "seed_body_init_seed": derive(spec.seed, "seed-body-init"),
        },
    )
    trunk = unit.trunk(decision_points)
    with (output / "trunk.jsonl").open("x") as fh:
        for record in trunk.records:
            append_record(fh, record)
    count = 0
    with (output / "branches.jsonl").open("x") as fh:
        for t in decision_points:
            if t not in trunk.snapshots:
                continue  # the trunk diverged before t; recorded in complete.json
            for replicate in replicates:
                for action in (NOOP, *actions):
                    branch = unit.branch(trunk.snapshots[t], action=None if action == NOOP else action, replicate=replicate)
                    final = branch.records[-1]["dev"] if branch.diverged is None else None
                    append_record(
                        fh,
                        {
                            "schema": ATLAS_SCHEMA,
                            "decision_epoch": t,
                            "replicate": replicate,
                            "action": action,
                            "status": "completed" if branch.diverged is None else "diverged",
                            "late_ce": _late_ce(branch, spec.epochs),
                            "final_dev": final,
                            "diverged": branch.diverged,
                            "costs": branch.costs,
                            "future_sha256": branch.future_hash,
                            "records": branch.records,
                        },
                    )
                    count += 1
    completion = {
        "schema": ATLAS_SCHEMA,
        "status": "complete",
        "branches": count,
        "trunk": {"diverged": trunk.diverged, "epochs": len(trunk.records)},
        "artifacts": {name: file_hash(output / name) for name in ("manifest.json", "trunk.jsonl", "branches.jsonl")},
    }
    write_json(output / "complete.json", completion)
    return completion


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def verify_unit(root: Path) -> dict[str, Any]:
    """Refuse a unit missing a no-op or an action, with a duplicate branch, or whose no-op twin left the trunk."""
    manifest, completion = read_json(root / "manifest.json"), read_json(root / "complete.json")
    plan = manifest["plan"]
    trunk = {r["epoch"]: _plain(r) for r in _jsonl(root / "trunk.jsonl")}
    rows = _jsonl(root / "branches.jsonl")
    keys = [(r["decision_epoch"], r["replicate"], r["action"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate branch key")
    trunk_diverged = completion["trunk"]["diverged"] is not None
    reached = [t for t in plan["decision_points"] if t in trunk or not trunk_diverged]
    expected = {(t, r, a) for t in reached for r in plan["replicates"] for a in (NOOP, *plan["actions"])}
    missing_noop = {k for k in expected - set(keys) if k[2] == NOOP}
    if missing_noop:
        raise ValueError(f"missing no-op branch: {sorted(missing_noop)}")
    if set(keys) != expected:
        raise ValueError(f"branch set differs from the plan: missing {sorted(expected - set(keys))}, extra {sorted(set(keys) - expected)}")
    for row in rows:
        completed = row["status"] == "completed"
        if (
            row["status"] not in ("completed", "diverged")
            or completed != (row["late_ce"] is not None)
            or completed == (row["diverged"] is not None)
        ):
            raise ValueError(f"inconsistent status for branch {row['decision_epoch'], row['replicate'], row['action']}")
        if completed and not math.isfinite(row["late_ce"]):
            raise ValueError("a completed branch must have a finite late CE")
        if row["action"] == NOOP and row["replicate"] == 0:
            twin = [_plain(r) for r in row["records"]]
            if twin != [trunk[r["epoch"]] for r in twin if r["epoch"] in trunk] or (
                completed and len(twin) != len(trunk) - row["decision_epoch"]
            ):
                raise ValueError(f"no-op twin at epoch {row['decision_epoch']} does not continue the trunk")
    return {"branches": len(rows), "decision_points": reached, "noop_twin_matches_trunk": True, "trunk_diverged": trunk_diverged}


def effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each action's late CE minus its own (decision point, replicate) no-op; a diverged action scores chance CE."""
    noops = {(r["decision_epoch"], r["replicate"]): r for r in rows if r["action"] == NOOP}
    out = []
    for row in rows:
        if row["action"] == NOOP:
            continue
        noop = noops[(row["decision_epoch"], row["replicate"])]
        scored = row["late_ce"] if row["late_ce"] is not None else CHANCE_CE
        value = None if noop["late_ce"] is None else scored - noop["late_ce"]  # no zero to measure against: never imputed
        out.append(
            {
                "decision_epoch": row["decision_epoch"],
                "replicate": row["replicate"],
                "action": row["action"],
                "effect": value,
                "diverged": row["status"] == "diverged",
                "noop_diverged": noop["late_ce"] is None,
            }
        )
    return out
