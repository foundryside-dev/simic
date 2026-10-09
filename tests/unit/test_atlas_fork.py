"""Atlas fork core (PDR-0057 G0, item 2): branches forked from a snapshot replay the frozen runner bitwise.

The atlas trains one no-op trunk per unit, snapshots it at decision points, and forks every
action (and a no-op twin) from the snapshot. These tests pin it to `bounded_comparison.train`:
the trunk is the no_growth arm, a forked no-op continues the trunk, and a forked germination
is the scheduled arm, record for record (wall time aside).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from experiments import atlas
from experiments import bounded_comparison as runner
from experiments.bounded_data import RunSpec

SPEC = RunSpec(epochs=7, host="under_normalized", seed_type="norm", lifecycle="v2")


def _strip(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "wall_s"}


def _epochs(root: Path, arm: str) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in (root / "training.jsonl").read_text().splitlines()]
    return [_strip(r) for r in rows if r["kind"] == "epoch" and r["arm"] == arm]


@pytest.fixture(scope="module")
def reference(tmp_path_factory: pytest.TempPathFactory) -> dict[int, Path]:
    """The frozen runner at two graft epochs; both share the no_growth arm."""
    roots = {}
    for graft_epoch in (0, 2):
        roots[graft_epoch] = tmp_path_factory.mktemp(f"ref{graft_epoch}") / "run"
        runner.train(RunSpec(**{**SPEC.__dict__, "graft_epoch": graft_epoch}), roots[graft_epoch])
    return roots


@pytest.fixture(scope="module")
def unit() -> atlas.Unit:
    return atlas.Unit.load(SPEC)


@pytest.fixture(scope="module")
def trunk(unit: atlas.Unit) -> atlas.Trunk:
    return unit.trunk(decision_points=(0, 1, 2, 4))


def test_trunk_is_the_no_growth_arm(reference: dict[int, Path], trunk: atlas.Trunk) -> None:
    assert trunk.diverged is None
    assert [_strip(r) for r in trunk.records] == _epochs(reference[2], "no_growth")


@pytest.mark.parametrize("t", [0, 2, 4])
def test_forked_noop_continues_the_trunk_bitwise(unit: atlas.Unit, trunk: atlas.Trunk, t: int) -> None:
    branch = unit.branch(trunk.snapshots[t], action=None)
    assert branch.diverged is None
    assert [_strip(r) for r in branch.records] == [_strip(r) for r in trunk.records[t:]]


@pytest.mark.parametrize("t", [0, 2])
def test_forked_germination_is_the_scheduled_arm(reference: dict[int, Path], unit: atlas.Unit, trunk: atlas.Trunk, t: int) -> None:
    branch = unit.branch(trunk.snapshots[t], action="norm")
    expected = _epochs(reference[t], "scheduled")
    # The runner labels the scheduled arm's pre-germination epochs "scheduled"; the trunk's are "no_growth".
    prefix = [{**_strip(r), "arm": "scheduled"} for r in trunk.records[:t]]
    assert prefix + [_strip(r) for r in branch.records] == expected


def test_snapshot_after_germination_rebuilds_seed_groups_before_loading_momentum(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    """A second decision point inside a grafted branch: the fork must re-append seed groups first."""
    whole = unit.branch(trunk.snapshots[1], action="norm", snapshot_at=(3,))
    resumed = unit.branch(whole.snapshots[3], action=None)
    assert [_strip(r) for r in resumed.records] == [_strip(r) for r in whole.records[2:]]


def test_snapshots_are_independent_of_later_training(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    """Running a branch must not mutate the snapshot it came from (deep copies, not live references)."""
    before = atlas.snapshot_digest(trunk.snapshots[2])
    unit.branch(trunk.snapshots[2], action="norm")
    assert atlas.snapshot_digest(trunk.snapshots[2]) == before


def test_branch_refuses_unknown_action(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    with pytest.raises(ValueError):
        unit.branch(trunk.snapshots[0], action="not-a-seed")


def test_golden_comparator_reports_the_first_disagreement() -> None:
    from experiments.atlas_golden import first_difference

    a = [{"epoch": 0, "x": 1}, {"epoch": 1, "x": 2}]
    assert first_difference(a, [dict(r) for r in a]) is None
    assert first_difference(a, a[:1]) == {"reason": "length", "got": 2, "want": 1}
    changed = [a[0], {"epoch": 1, "x": 3}]
    assert first_difference(a, changed) == {"reason": "record", "index": 1, "epoch": 1, "keys": ["x"]}


# --- Code-review additions (W1-W3, M1-M3) ---


def test_branch_costs_equal_the_runners_arm_costs(reference: dict[int, Path], unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    summaries = json.loads((reference[2] / "complete.json").read_text())["summaries"]
    assert trunk.costs == summaries["no_growth"]["costs"]
    assert unit.branch(trunk.snapshots[2], action="norm").costs == summaries["scheduled"]["costs"]


def test_trunk_records_the_runners_initial_scoring(reference: dict[int, Path], trunk: atlas.Trunk) -> None:
    rows = [json.loads(line) for line in (reference[2] / "training.jsonl").read_text().splitlines()]
    start = next(r for r in rows if r["kind"] == "arm_start" and r["arm"] == "no_growth")
    assert trunk.initial_dev == start["initial_dev"]


def test_record_hashes_do_not_depend_on_ambient_global_rng(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    """W1: training_state_sha256 folds in the global RNG state, so a fork must restore it."""
    first = unit.branch(trunk.snapshots[2], action="norm")
    import torch

    torch.rand(1)  # ambient draw between forks
    second = unit.branch(trunk.snapshots[2], action="norm")
    assert [_strip(r) for r in second.records] == [_strip(r) for r in first.records]


def test_a_snapshot_inside_a_replicate_continues_that_replicate(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    """W2: a snapshot remembers the future it was trained on; re-forking continues it, and a mismatch is refused."""
    parent = unit.branch(trunk.snapshots[1], action="norm", replicate=1, snapshot_at=(3,))
    child = unit.branch(parent.snapshots[3], action=None)
    assert child.replicate == 1 and child.future_hash == parent.future_hash
    assert [_strip(r) for r in child.records] == [_strip(r) for r in parent.records[2:]]
    with pytest.raises(ValueError, match="replicate"):
        unit.branch(parent.snapshots[3], action=None, replicate=2)


def test_branch_refuses_a_germination_the_lifecycle_cannot_finish(unit: atlas.Unit) -> None:
    """M1: the runner's own rule (whole lifecycle plus a coupled epoch after germination)."""
    late = unit.trunk(decision_points=(5,))
    with pytest.raises(ValueError):
        unit.branch(late.snapshots[5], action="norm")
    assert unit.branch(late.snapshots[5], action=None).diverged is None  # waiting is always legal


def test_divergence_in_the_germination_epoch_keeps_the_birth_record(
    unit: atlas.Unit, trunk: atlas.Trunk, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W3: the runner attaches the birth record to a divergence in the germination epoch."""
    from experiments.bounded_comparison import ArmDivergedError

    def boom(host: Any, slot: Any, *args: Any) -> dict[str, Any]:
        raise ArmDivergedError(epoch=2, step=0, reason="injected", stage=slot.stage.value)

    monkeypatch.setattr(atlas, "train_epoch", boom)
    branch = unit.branch(trunk.snapshots[2], action="norm")
    assert branch.diverged is not None and branch.diverged["birth"]["gain_at_birth"] is not None


@pytest.mark.parametrize(("host", "seed_type", "lifecycle"), [("mild", "conv_heavy", "v1"), ("channel_starved", "conv_light", "v2")])
def test_bn_hosts_and_seeds_fork_and_resume_bitwise(tmp_path: Path, host: str, seed_type: str, lifecycle: str) -> None:
    """BN host buffers and BN seed buffers survive snapshots at every lifecycle stage."""
    spec = RunSpec(epochs=7, host=host, seed_type=seed_type, lifecycle=lifecycle, graft_epoch=1)
    runner.train(spec, tmp_path / "ref")
    expected = _epochs(tmp_path / "ref", "scheduled")
    unit = atlas.Unit.load(spec)
    trunk = unit.trunk(decision_points=(1,))
    whole = unit.branch(trunk.snapshots[1], action=seed_type, snapshot_at=(3, 5))
    assert [{**_strip(r), "arm": "scheduled"} for r in trunk.records[:1]] + [_strip(r) for r in whole.records] == expected
    for t in (3, 5):  # mid-BLENDING and FOSSILIZED
        resumed = unit.branch(whole.snapshots[t], action=None)
        assert [_strip(r) for r in resumed.records] == [_strip(r) for r in whole.records[t - 1 :]]


# --- Second PyTorch review: the rest of the runner's end-of-run checks (M2) ---


def _seeded_slot(fully_coupled: bool) -> tuple[runner.ScaleAwareSlot, Any]:
    from experiments import kernel_demo

    slot = runner.ScaleAwareSlot(SPEC)
    slot.seed = kernel_demo.build_seed("norm", 64, 3)
    slot.stage = kernel_demo.Stage.FOSSILIZED if fully_coupled else kernel_demo.Stage.BLENDING
    slot.alpha = slot.beta = 1.0
    host = kernel_demo.build_host("under_normalized", 5)
    opt = kernel_demo.build_optimizer(host, SPEC.kernel_config())
    kernel_demo.append_seed_group(opt, slot.seed, SPEC.kernel_config())
    return slot, (host, opt)


def test_end_state_refuses_a_graft_that_never_fully_coupled() -> None:
    slot, (host, opt) = _seeded_slot(True)
    base = sum(p.numel() for p in host.parameters())
    learned = {"host": True, "seed": True}
    atlas._check_end_state(slot, opt, base, fully_coupled_steps=5, learned=learned)
    with pytest.raises(RuntimeError, match="coupl"):
        atlas._check_end_state(slot, opt, base, fully_coupled_steps=0, learned=learned)


@pytest.mark.parametrize("who", ["host", "seed"])
def test_end_state_refuses_a_branch_that_did_not_learn(who: str) -> None:
    slot, (host, opt) = _seeded_slot(True)
    base = sum(p.numel() for p in host.parameters())
    learned = {"host": True, "seed": True, who: False}
    with pytest.raises(RuntimeError, match="learn"):
        atlas._check_end_state(slot, opt, base, fully_coupled_steps=5, learned=learned)


# --- G0 item 6: static arm and config-built hosts ---


def test_static_arm_is_the_runners_static_arm(reference: dict[int, Path], unit: atlas.Unit) -> None:
    static = unit.static(SPEC.seed_type)
    rows = [json.loads(line) for line in (reference[2] / "training.jsonl").read_text().splitlines()]
    start = next(r for r in rows if r["kind"] == "arm_start" and r["arm"] == "static")
    summaries = json.loads((reference[2] / "complete.json").read_text())["summaries"]
    assert static.diverged is None
    assert [_strip(r) for r in static.records] == _epochs(reference[2], "static")
    assert static.initial_dev == start["initial_dev"] and static.birth == start["birth"]
    assert static.costs == summaries["static"]["costs"]


def test_config_built_host_at_scale_one_trains_like_the_kernel_host(trunk: atlas.Trunk) -> None:
    from experiments import atlas_hosts

    same = atlas.Unit.load(SPEC, host_cfg=atlas_hosts.base_config(SPEC.host)).trunk(decision_points=(2,))
    assert [_strip(r) for r in same.records] == [_strip(r) for r in trunk.records]


def test_scaled_host_trains_as_a_no_growth_comparator() -> None:
    from experiments import atlas_hosts

    cfg = atlas_hosts.scaled_config(SPEC.host, 1.25)
    scaled = atlas.Unit.load(SPEC, host_cfg=cfg)
    span = scaled.trunk(decision_points=(2,))
    assert span.diverged is None and len(span.records) == SPEC.epochs
    assert all(r["installed_parameters"] == atlas_hosts.parameter_count(cfg) for r in span.records)
    with pytest.raises(ValueError, match="slot"):
        scaled.branch(span.snapshots[2], action="norm")
    with pytest.raises(ValueError, match="slot"):
        scaled.static("norm")
