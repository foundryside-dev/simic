"""Bounded multi-seed screen: frozen decision rules and analysis over real verified runs."""

from __future__ import annotations

import json

import numpy as np
import pytest

from experiments import bounded_comparison as runner
from experiments import bounded_screen as screen
from experiments.bounded_data import RunSpec, file_hash


def test_frozen_preregistration_declares_disjoint_seeds_and_config():
    prereg = screen.load_prereg()
    seeds = screen.unit_seeds(prereg)
    assert len(seeds) == prereg["units"]["count"] == 48
    assert not set(seeds) & {7, 999}
    spec = RunSpec(data="cifar", **prereg["config"])
    spec.validate()


def test_overlapping_exploratory_seed_is_refused():
    prereg = screen.load_prereg()
    prereg["units"]["excluded_seeds"] = [1001]
    with pytest.raises(ValueError, match="overlaps"):
        screen.unit_seeds(prereg)


@pytest.mark.parametrize(
    ("lower", "upper", "verdict"),
    [
        (-0.2, -0.06, "scheduled_better_beyond_floor"),
        (0.01, 0.2, "scheduled_worse"),
        (-0.1, -0.01, "scheduled_better_below_floor"),
        (-0.04, 0.04, "equivalent_within_floor"),
        (-0.04, 0.0, "equivalent_within_floor"),
        (-0.2, 0.2, "inconclusive"),
        (-0.01, 0.09, "inconclusive"),
    ],
)
def test_contrast_verdicts_follow_the_frozen_table(lower, upper, verdict):
    assert screen.contrast_verdict({"lower": lower, "upper": upper}, 0.05) == verdict


def test_paired_interval_and_mde_match_hand_computation():
    diffs = np.array([0.1, -0.1, 0.2, 0.0])
    ci = screen.interval(diffs, 0.95)
    assert ci["mean"] == pytest.approx(0.05)
    assert ci["half_width"] == pytest.approx(3.182446 * np.std(diffs, ddof=1) / 2, rel=1e-5)
    assert screen.mde(0.1, 48, 0.025, 0.8) == pytest.approx(0.0465, abs=0.001)


def test_launch_refuses_dirty_tree_and_exposed_test_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": " M file"})
    with pytest.raises(RuntimeError, match="dirty"):
        screen.launch(tmp_path / "screen", tmp_path, 1)
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    (tmp_path / "cifar-10-batches-py").mkdir()
    (tmp_path / "cifar-10-batches-py" / "test_batch").write_text("")
    with pytest.raises(RuntimeError, match="test_batch"):
        screen.launch(tmp_path / "screen", tmp_path, 1)
    assert not (tmp_path / "screen").exists()


@pytest.fixture(scope="module")
def tiny_screen(tmp_path_factory):
    """Three real verified smoke units plus one missing unit, under a 4-seed pre-registration."""
    base = tmp_path_factory.mktemp("screen")
    prereg = screen.load_prereg()
    prereg["units"].update(first_seed=1, count=4, excluded_seeds=[])
    prereg["endpoint"]["late_epochs"] = [4, 5, 6]
    prereg["decision"]["max_failed_units"] = 1
    prereg_path = base / "prereg.json"
    prereg_path.write_text(json.dumps(prereg))
    root = base / "screen"
    root.mkdir()
    for seed in (1, 2, 3):
        runner.train(RunSpec(seed=seed, epochs=7), root / f"seed-{seed}")
    (root / "launch.json").write_text(json.dumps({"prereg_sha256": file_hash(prereg_path)}))
    return root, prereg_path


def test_analyze_reduces_units_records_failures_and_publishes_once(tiny_screen):
    root, prereg_path = tiny_screen
    report = screen.analyze(root, prereg_path)
    assert report["n_units"] == 3
    assert [f["seed"] for f in report["failures"]] == [4]
    for name in screen.CONTRASTS:
        contrast = report["contrasts"][name]
        assert len(contrast["per_unit"]) == 3
        assert contrast["verdict"] in {
            "scheduled_better_beyond_floor",
            "scheduled_worse",
            "scheduled_better_below_floor",
            "equivalent_within_floor",
            "inconclusive",
        }
        assert contrast["t_interval"]["lower"] <= contrast["t_interval"]["mean"] <= contrast["t_interval"]["upper"]
    assert report["confidence_level"] == pytest.approx(0.975)
    assert isinstance(report["gate_instrument_resolves"], bool)
    with pytest.raises(FileExistsError):
        screen.analyze(root, prereg_path)


def test_analyze_refuses_a_changed_preregistration(tiny_screen, tmp_path):
    root, prereg_path = tiny_screen
    edited = tmp_path / "prereg.json"
    edited.write_text(prereg_path.read_text().replace('"delta_nats": 0.05', '"delta_nats": 0.5'))
    with pytest.raises(ValueError, match="changed after launch"):
        screen.analyze(root, edited)
