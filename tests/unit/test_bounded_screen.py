"""Bounded multi-seed screen: plan-declared contrasts, named readings, costs, provenance."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments import bounded_comparison as runner
from experiments import bounded_screen as screen
from experiments.bounded_data import RunSpec, file_hash

BASE_PLAN: dict[str, Any] = {
    "study": {"id": "test-screen", "status": "confirmatory"},
    "units": {"first_seed": 1, "count": 20, "excluded_seeds": []},
    "config": {"data_seed": 20261004, "train_size": 128, "dev_size": 64, "epochs": 7, "host": "mild", "seed_type": "conv_light"},
    "endpoint": {"late_epochs": [4, 5, 6]},
    "analysis": {
        "contrasts": {
            "scheduled_minus_no_growth": {"arms": ["scheduled", "no_growth"], "role": "co-primary"},
            "scheduled_minus_static": {"arms": ["scheduled", "static"], "role": "co-primary"},
            "static_minus_no_growth": {"arms": ["static", "no_growth"], "role": "descriptive"},
        },
        "family_alpha": 0.05,
        "bootstrap_resamples": 2000,
        "bootstrap_seed": 1,
    },
    "decision": {"delta_nats": 0.05, "max_failed_units": 1, "reading_rule": "bounded-screen-v1"},
}


def write_plan(tmp_path: Path, plan: dict[str, Any] | None = None) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan or BASE_PLAN))
    return path


def fake_screen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    values: dict[int, dict[str, float]],
    plan: dict[str, Any] | None = None,
    broken: tuple[int, ...] = (),
) -> tuple[Path, Path]:
    """Analyze controlled per-unit values; the runner contract itself is tested elsewhere."""
    plan_path = write_plan(tmp_path, plan)
    root = tmp_path / "screen"
    root.mkdir()
    (root / "launch.json").write_text(
        json.dumps({"prereg_sha256": file_hash(plan_path), "analysis_module_sha256": screen.analysis_module_hash()})
    )
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})

    def verify(unit: Path) -> None:
        if int(unit.name.split("-")[1]) in broken:
            raise RuntimeError("simulated unit crash")

    monkeypatch.setattr(screen, "verify_run", verify)
    monkeypatch.setattr(screen, "late_ce", lambda unit, epochs: values[int(unit.name.split("-")[1])])
    monkeypatch.setattr(
        screen, "unit_costs", lambda unit: {arm: dict.fromkeys((*screen.COST_FIELDS, "wall_s"), 1.0) for arm in runner.ARMS}
    )
    return root, plan_path


def unit_values(
    scheduled_shift: float, static_shift: float = 0.0, static_sd: float = 0.01, n: int = 20, seed: int = 0
) -> dict[int, dict[str, float]]:
    rng = np.random.default_rng(seed)
    return {
        s: {
            "no_growth": 1.10,
            "scheduled": 1.10 + scheduled_shift + 0.005 * float(rng.standard_normal()),
            "static": 1.10 + static_shift + static_sd * float(rng.standard_normal()),
        }
        for s in range(1, n + 1)
    }


def test_plan_requires_contrasts_with_known_arms_and_a_known_reading_rule(tmp_path):
    bad = copy.deepcopy(BASE_PLAN)
    bad["analysis"]["contrasts"]["x"] = {"arms": ["scheduled", "nonexistent"], "role": "co-primary"}
    with pytest.raises(ValueError, match="arm"):
        screen.load_plan(write_plan(tmp_path, bad))
    bad = copy.deepcopy(BASE_PLAN)
    bad["decision"]["reading_rule"] = "made-up"
    with pytest.raises(ValueError, match="reading rule"):
        screen.load_plan(write_plan(tmp_path, bad))


def test_overlapping_exploratory_seed_is_refused():
    plan = copy.deepcopy(BASE_PLAN)
    plan["units"]["excluded_seeds"] = [3]
    with pytest.raises(ValueError, match="overlaps"):
        screen.unit_seeds(plan)


def test_train_command_carries_host_and_seed_type(tmp_path):
    command = screen.train_command(BASE_PLAN, 5, tmp_path / "u", tmp_path)
    assert command[command.index("--host") + 1] == "mild"
    assert command[command.index("--seed-type") + 1] == "conv_light"


@pytest.mark.parametrize(
    ("lower", "upper", "verdict"),
    [
        (-0.2, -0.06, "first_better_beyond_floor"),
        (0.01, 0.2, "first_worse"),
        (-0.1, -0.01, "first_better_floor_not_cleared"),
        (-0.04, 0.04, "equivalent_within_floor"),
        (-0.2, 0.2, "inconclusive"),
    ],
)
def test_contrast_verdicts_follow_the_frozen_table(lower, upper, verdict):
    assert screen.contrast_verdict({"lower": lower, "upper": upper}, 0.05) == verdict


def test_effect_needed_for_a_progress_reading_matches_the_audit():
    # Screen v1 audit: sd 0.0544, n 48, alpha 0.025 -> ~0.075 nats for 80% power beyond -delta.
    assert screen.effect_for_progress(0.0544, 48, 0.025, 0.8, 0.05) == pytest.approx(0.075, abs=0.001)


def test_reading_no_value_when_the_graft_is_flat(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    assert screen.analyze(root, plan)["reading"] == "reopen_no_value"


def test_reading_progress_when_the_graft_clears_the_floor(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(-0.2, static_shift=-0.2))
    assert screen.analyze(root, plan)["reading"] == "progress"


def test_reading_precedence_static_wins_before_not_credible(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0, static_shift=-0.5, static_sd=0.3))
    report = screen.analyze(root, plan)
    static = report["contrasts"]["scheduled_minus_static"]["t_interval"]
    assert static["lower"] > 0 and static["half_width"] > 0.05
    assert report["reading"] == "reopen_static_wins"


def test_reading_static_not_credible_keeps_the_gate(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0, static_sd=0.4))
    report = screen.analyze(root, plan)
    assert report["gate_instrument_resolves"] is True
    assert report["reading"] == "reopen_static_not_credible"


def test_any_unit_exception_is_recorded_as_a_failure(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=(4,))
    report = screen.analyze(root, plan)
    assert [f["seed"] for f in report["failures"]] == [4]
    assert "RuntimeError" in report["failures"][0]["error"]
    assert report["n_units"] == 19


def test_too_many_failures_is_instrument_failure(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=(2, 3))
    assert screen.analyze(root, plan)["reading"] == "instrument_failure"


def test_report_carries_costs_provenance_and_progress_threshold(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    report = screen.analyze(root, plan)
    assert report["plan_sha256"] == file_hash(plan)
    assert set(report["analysis_git"]) == {"commit", "status"}
    assert report["analyzed_unix"] > 0
    assert set(report["arm_costs_mean"]) == set(runner.ARMS)
    assert report["contrasts"]["scheduled_minus_no_growth"]["effect_for_80pct_progress"] > report["delta_nats"]


def test_analysis_refuses_changed_plan_and_republication(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    screen.analyze(root, plan)
    with pytest.raises(FileExistsError):
        screen.analyze(root, plan)
    edited = tmp_path / "edited.json"
    edited.write_text(plan.read_text().replace('"delta_nats": 0.05', '"delta_nats": 0.5'))
    (root / "screen_report.json").unlink()
    with pytest.raises(ValueError, match="changed after launch"):
        screen.analyze(root, edited)


def test_launch_refuses_dirty_tree_and_exposed_test_batch(tmp_path, monkeypatch):
    plan = write_plan(tmp_path)
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": " M file"})
    with pytest.raises(RuntimeError, match="dirty"):
        screen.launch(tmp_path / "screen", tmp_path, 1, plan)
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    (tmp_path / "cifar-10-batches-py").mkdir()
    (tmp_path / "cifar-10-batches-py" / "test_batch").write_text("")
    with pytest.raises(RuntimeError, match="test_batch"):
        screen.launch(tmp_path / "screen", tmp_path, 1, plan)
    assert not (tmp_path / "screen").exists()


def test_late_ce_and_costs_read_a_real_verified_unit(tmp_path):
    unit = tmp_path / "seed-1"
    runner.train(RunSpec(epochs=7), unit)
    runner.verify_run(unit)
    late = screen.late_ce(unit, [4, 5, 6])
    assert set(late) == set(runner.ARMS) and all(np.isfinite(v) for v in late.values())
    costs = screen.unit_costs(unit)
    assert costs["static"]["optimizer_parameter_steps"] > costs["no_growth"]["optimizer_parameter_steps"]


def test_analysis_refuses_a_changed_analysis_module_or_dirty_tree(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    launch = json.loads((root / "launch.json").read_text())
    launch["analysis_module_sha256"] = "0" * 64
    (root / "launch.json").write_text(json.dumps(launch))
    with pytest.raises(ValueError, match="analysis module changed"):
        screen.analyze(root, plan)
    launch["analysis_module_sha256"] = screen.analysis_module_hash()
    (root / "launch.json").write_text(json.dumps(launch))
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": " M f"})
    with pytest.raises(RuntimeError, match="dirty"):
        screen.analyze(root, plan)


def test_descriptive_contrasts_get_no_verdict_and_a_nominal_interval(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    descriptive = screen.analyze(root, plan)["contrasts"]["static_minus_no_growth"]
    assert descriptive["verdict"] is None
    assert "effect_for_80pct_progress" not in descriptive
    assert descriptive["interval_level"] == 0.95


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda p: p["analysis"]["contrasts"].update({k: {**v, "role": "descriptive"} for k, v in p["analysis"]["contrasts"].items()}),
            "co-primary",
        ),
        (lambda p: p["analysis"]["contrasts"].pop("scheduled_minus_static"), "requires contrast"),
        (lambda p: p["endpoint"].update(late_epochs=[5, 6, 7]), "late_epochs"),
    ],
)
def test_plan_is_validated_before_any_unit_runs(tmp_path, mutate, message):
    plan = copy.deepcopy(BASE_PLAN)
    mutate(plan)
    with pytest.raises(ValueError, match=message):
        screen.load_plan(write_plan(tmp_path, plan))


POSITIVE_CONTROL = {
    **BASE_PLAN,
    "analysis": {
        **BASE_PLAN["analysis"],
        "contrasts": {"static_minus_no_growth": {"arms": ["static", "no_growth"], "role": "co-primary"}},
    },
    "decision": {"delta_nats": 0.05, "max_failed_units": 1, "reading_rule": "positive-control-v1"},
}


def test_undeclared_arms_are_sealed_out_of_the_report(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(-0.3, static_shift=-0.2), plan=POSITIVE_CONTROL)
    report = screen.analyze(root, plan)
    assert set(report["arm_late_ce_mean"]) == set(report["arm_costs_mean"]) == {"static", "no_growth"}
    assert "scheduled" not in json.dumps(report)


@pytest.mark.parametrize(
    ("static_shift", "static_sd", "reading"),
    [
        (-0.3, 0.02, "control_passes"),
        (0.2, 0.02, "control_fails_static_worse"),
        (-0.05, 0.4, "control_imprecise"),
        (0.0, 0.02, "control_fails_no_effect"),
        (-0.02, 0.02, "control_fails_no_effect"),
    ],
)
def test_positive_control_readings_are_detection_first(tmp_path, monkeypatch, static_shift, static_sd, reading):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0, static_shift=static_shift, static_sd=static_sd), plan=POSITIVE_CONTROL)
    assert screen.analyze(root, plan)["reading"] == reading


def test_positive_control_readings_cover_every_verdict_and_precision_state():
    for verdict in (
        "first_better_beyond_floor",
        "first_worse",
        "first_better_floor_not_cleared",
        "equivalent_within_floor",
        "inconclusive",
    ):
        for half_width in (0.01, 0.5):
            report = {
                "delta_nats": 0.05,
                "contrasts": {"static_minus_no_growth": {"verdict": verdict, "t_interval": {"half_width": half_width}}},
            }
            assert screen.reading_positive_control_v1(report)[0] in screen.POSITIVE_CONTROL_READINGS


def test_paired_interval_and_mde_match_hand_computation():
    diffs = np.array([0.1, -0.1, 0.2, 0.0])
    ci = screen.interval(diffs, 0.95)
    assert ci["mean"] == pytest.approx(0.05)
    assert ci["half_width"] == pytest.approx(3.182446 * np.std(diffs, ddof=1) / 2, rel=1e-5)
    assert screen.mde(0.1, 48, 0.025, 0.8) == pytest.approx(0.0457, abs=0.0005)


@pytest.mark.parametrize(("lower", "upper"), [(-0.04, 0.0), (-0.01, 0.09)])
def test_verdict_boundaries(lower, upper):
    expected = "equivalent_within_floor" if upper < 0.05 else "inconclusive"
    assert screen.contrast_verdict({"lower": lower, "upper": upper}, 0.05) == expected


def test_coprimary_family_level_and_imprecise_reading(tmp_path, monkeypatch):
    values = unit_values(0.0)
    rng = np.random.default_rng(3)
    for v in values.values():
        v["scheduled"] = 1.10 + 0.4 * float(rng.standard_normal())
    root, plan = fake_screen(tmp_path, monkeypatch, values)
    report = screen.analyze(root, plan)
    assert report["confidence_level"] == pytest.approx(0.975)
    assert report["reading"] == "reopen_instrument_imprecise"


def test_plan_with_swapped_arms_for_a_rule_contrast_is_refused(tmp_path):
    plan = copy.deepcopy(BASE_PLAN)
    plan["analysis"]["contrasts"]["scheduled_minus_no_growth"]["arms"] = ["no_growth", "scheduled"]
    with pytest.raises(ValueError, match="in that order"):
        screen.load_plan(write_plan(tmp_path, plan))


@pytest.mark.parametrize("config_change", [{"seed": 1}, {"data": "smoke"}, {"bogus": 3}, {"host": "nonexistent"}])
def test_plan_config_cannot_override_unit_fields_or_name_unknown_ones(tmp_path, config_change):
    plan = copy.deepcopy(BASE_PLAN)
    plan["config"].update(config_change)
    with pytest.raises(ValueError):
        screen.load_plan(write_plan(tmp_path, plan))


def test_unit_seed_comes_last_in_the_train_command(tmp_path):
    command = screen.train_command(BASE_PLAN, 7, tmp_path / "u", tmp_path)
    assert command[-2:] == ["--seed", "7"]


def test_identical_failure_in_every_unit_is_raised_not_published(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=tuple(range(1, 21)))
    with pytest.raises(RuntimeError, match="analysis-side"):
        screen.analyze(root, plan)
    assert not (root / "screen_report.json").exists()
