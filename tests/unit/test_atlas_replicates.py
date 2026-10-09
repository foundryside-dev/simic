"""Atlas replicate futures (PDR-0057 G0, item 4).

A replicate r re-draws the data order and augmentation for epochs from the decision point on.
Replicate 0 is today's common future, bitwise. Earlier epochs are shared by every replicate, so
a branch's pre-decision history is identical across replicates and only its future differs.
"""

from __future__ import annotations

from typing import Any

import pytest
import torch

from experiments import atlas
from experiments.bounded_data import RunSpec

SPEC = RunSpec(epochs=7, host="under_normalized", seed_type="norm", lifecycle="v2")


def _strip(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "wall_s"}


@pytest.fixture(scope="module")
def unit() -> atlas.Unit:
    return atlas.Unit.load(SPEC)


@pytest.fixture(scope="module")
def trunk(unit: atlas.Unit) -> atlas.Trunk:
    return unit.trunk(decision_points=(1, 3))


def test_replicate_zero_is_the_common_future_bitwise(unit: atlas.Unit) -> None:
    same = unit.future_for(replicate=0, from_epoch=1)
    assert same.hash == unit.future.hash
    for name in ("order", "crops", "flips"):
        assert torch.equal(getattr(same, name), getattr(unit.future, name))


@pytest.mark.parametrize("from_epoch", [1, 3])
def test_replicates_share_the_past_and_redraw_the_future(unit: atlas.Unit, from_epoch: int) -> None:
    one, two = unit.future_for(1, from_epoch), unit.future_for(2, from_epoch)
    for name in ("order", "crops", "flips"):
        base, a, b = getattr(unit.future, name), getattr(one, name), getattr(two, name)
        assert torch.equal(a[:from_epoch], base[:from_epoch])
        assert torch.equal(b[:from_epoch], base[:from_epoch])
        assert not torch.equal(a[from_epoch:], base[from_epoch:])
        assert not torch.equal(a[from_epoch:], b[from_epoch:])
    assert len({unit.future.hash, one.hash, two.hash}) == 3


def test_replicate_draw_is_deterministic(unit: atlas.Unit) -> None:
    assert unit.future_for(1, 3).hash == unit.future_for(1, 3).hash


def test_replicate_does_not_depend_on_the_horizon(unit: atlas.Unit) -> None:
    """Prefix stability survives replication: a longer run replays a shorter one's replicate."""
    longer = atlas.Unit.load(RunSpec(**{**SPEC.__dict__, "epochs": 9}))
    short, long = unit.future_for(1, 3), longer.future_for(1, 3)
    for name in ("order", "crops", "flips"):
        assert torch.equal(getattr(long, name)[: SPEC.epochs], getattr(short, name))


def test_branch_replicate_zero_equals_the_plain_branch(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    plain = unit.branch(trunk.snapshots[1], action="norm")
    rep0 = unit.branch(trunk.snapshots[1], action="norm", replicate=0)
    assert [_strip(r) for r in rep0.records] == [_strip(r) for r in plain.records]
    assert rep0.replicate == 0


def test_branch_replicate_changes_only_the_future(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    rep0 = unit.branch(trunk.snapshots[1], action=None, replicate=0)
    rep1 = unit.branch(trunk.snapshots[1], action=None, replicate=1)
    assert rep1.replicate == 1 and rep1.future_hash != rep0.future_hash
    assert rep1.records[0]["epoch"] == 1
    assert rep1.records[0]["training_state_sha256"] != rep0.records[0]["training_state_sha256"]


def test_replicate_must_be_non_negative(unit: atlas.Unit, trunk: atlas.Trunk) -> None:
    with pytest.raises(ValueError):
        unit.future_for(-1, 1)
    with pytest.raises(ValueError):
        unit.branch(trunk.snapshots[1], action=None, replicate=-1)
