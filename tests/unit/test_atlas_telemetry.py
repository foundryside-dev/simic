"""Atlas telemetry (PDR-0057 G0 item 7): pre-decision features that cannot change training.

Two tiers, both read at a decision point t:
- trunk features, from the no-growth trunk's own records for epochs before t (free);
- probe features, from one forward pass of a throwaway copy materialised from the snapshot at t,
  on a probe split outside fit and dev. Stages run layer by layer: no forward hooks, because the
  kernel host's hooks close over the live host (PyTorch review of the evidence certificate).

Absent features stay absent: each value carries a validity flag and is never imputed as zero (ADR-0006).
"""

from __future__ import annotations

import math
from typing import Any

import pytest
import torch

from experiments import atlas, atlas_telemetry
from experiments.bounded_data import RunSpec

SPEC = RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2")  # a BN host: eval must not touch buffers


@pytest.fixture(scope="module")
def unit() -> atlas.Unit:
    return atlas.Unit.load(SPEC)


@pytest.fixture(scope="module")
def trunk(unit: atlas.Unit) -> atlas.Trunk:
    return unit.trunk(decision_points=(1, 3))


@pytest.fixture(scope="module")
def probe(unit: atlas.Unit) -> atlas_telemetry.Probe:
    return atlas_telemetry.load_probe(SPEC, None)


def _strip(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in r.items() if k != "wall_s"} for r in rs]


def test_cifar_probe_indices_sit_outside_fit_and_dev() -> None:
    perm = torch.randperm(50000, generator=torch.Generator().manual_seed(0))
    probe = set(atlas_telemetry.probe_indices(perm, train_size=4096, dev_size=5000).tolist())
    assert len(probe) == atlas_telemetry.PROBE_SIZE
    assert probe.isdisjoint(perm[:4096].tolist()) and probe.isdisjoint(perm[45000:50000].tolist())
    with pytest.raises(ValueError):
        atlas_telemetry.probe_indices(perm, train_size=40001, dev_size=5000)


def test_smoke_probe_is_independent_of_fit_and_dev(unit: atlas.Unit, probe: atlas_telemetry.Probe) -> None:
    assert not torch.equal(probe.x, unit.dx[: len(probe.x)]) and not torch.equal(probe.x[: len(unit.tx)], unit.tx[: len(probe.x)])
    assert len(probe.sha256) == 64


def test_features_are_deterministic_and_carry_validity(unit: atlas.Unit, trunk: atlas.Trunk, probe: atlas_telemetry.Probe) -> None:
    a = atlas_telemetry.decision_telemetry(unit, trunk, 3, probe)
    b = atlas_telemetry.decision_telemetry(unit, trunk, 3, probe)
    assert a == b
    assert a["schema"] == atlas_telemetry.SCHEMA and a["epoch"] == 3
    assert set(a["features"]) == set(a["valid"])
    for name, value in a["features"].items():
        assert (value is not None and math.isfinite(value)) == a["valid"][name], name
    for stage in (1, 2, 3):
        assert a["valid"][f"probe_stage{stage}_dead_relu"] and 0.0 <= a["features"][f"probe_stage{stage}_dead_relu"] <= 1.0
    assert a["valid"]["probe_ce"] and a["valid"]["slot_effective_rank"]


def test_absent_features_stay_absent_never_zero(unit: atlas.Unit, trunk: atlas.Trunk, probe: atlas_telemetry.Probe) -> None:
    """At t = 1 only one trunk epoch exists: the epoch-over-epoch delta is absent, not zero."""
    t1 = atlas_telemetry.decision_telemetry(unit, trunk, 1, probe)
    assert t1["valid"]["trunk_dev_ce_delta"] is False and t1["features"]["trunk_dev_ce_delta"] is None
    t3 = atlas_telemetry.decision_telemetry(unit, trunk, 3, probe)
    assert t3["valid"]["trunk_dev_ce_delta"] is True


def test_trunk_features_use_only_epochs_before_the_decision(unit: atlas.Unit, trunk: atlas.Trunk, probe: atlas_telemetry.Probe) -> None:
    t1 = atlas_telemetry.decision_telemetry(unit, trunk, 1, probe)
    assert t1["features"]["trunk_dev_ce"] == trunk.records[0]["dev"]["ce"]  # epoch 0 trained before decision 1
    t3 = atlas_telemetry.decision_telemetry(unit, trunk, 3, probe)
    assert t3["features"]["trunk_dev_ce"] == trunk.records[2]["dev"]["ce"]


def test_telemetry_changes_nothing_it_reads(unit: atlas.Unit, trunk: atlas.Trunk, probe: atlas_telemetry.Probe) -> None:
    """Tamiyo-isolation analogue: snapshot, global RNG and every later branch are untouched."""
    snap = trunk.snapshots[1]  # a graft at 1 finishes its lifecycle inside 7 epochs
    before_digest = atlas.snapshot_digest(snap)
    reference = unit.branch(snap, action="conv_light")
    rng = torch.get_rng_state().clone()
    atlas_telemetry.decision_telemetry(unit, trunk, 1, probe)
    assert torch.equal(rng, torch.get_rng_state())
    assert atlas.snapshot_digest(snap) == before_digest
    again = unit.branch(snap, action="conv_light")
    assert _strip(again.records) == _strip(reference.records)


def test_a_probe_does_not_write_into_a_live_host(unit: atlas.Unit, trunk: atlas.Trunk, probe: atlas_telemetry.Probe) -> None:
    """The kernel's saturation hooks close over `self`; the probe must not route through them."""
    live, _slot, _opt = atlas.materialize(trunk.snapshots[3], unit.spec, unit.device)
    live.attach_stat_hooks()
    live.stage_stats["saturation"] = [-1.0, -1.0, -1.0]
    atlas_telemetry.probe_features(live, probe)
    assert live.stage_stats["saturation"] == [-1.0, -1.0, -1.0]
