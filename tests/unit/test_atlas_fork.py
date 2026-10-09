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
