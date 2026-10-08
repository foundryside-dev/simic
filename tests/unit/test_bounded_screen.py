"""Bounded multi-seed screen: plan-declared contrasts, named readings, costs, provenance."""

from __future__ import annotations

import copy
import json
import os
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
    "config": {
        "data_seed": 20261004,
        "train_size": 128,
        "dev_size": 64,
        "epochs": 7,
        "batch_size": 32,
        "graft_epoch": 2,
        "stage_k": 1,
        "stage_m": 2,
        "stage_f": 1,
        "threads": 1,
        "lr": 0.05,
        "tau": 0.05,
        "lam": 1.0,
        "host": "mild",
        "seed_type": "conv_light",
    },
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
    "decision": {"delta_nats": 0.05, "max_failed_units": 1, "reading_rule": "bounded-screen-v1", "diverged_arm_policy": "fail_unit"},
    "linked_plans": [],
    "gated_by": None,
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
    diverged: dict[int, str] | None = None,
) -> tuple[Path, Path]:
    """Analyze controlled per-unit values; the runner contract itself is tested elsewhere."""
    plan_dict = plan or BASE_PLAN
    plan_path = write_plan(tmp_path, plan_dict)
    root = tmp_path / "screen"
    root.mkdir()
    seeds = screen.unit_seeds(plan_dict)
    launch = {
        "prereg_sha256": file_hash(plan_path),
        "analysis_module_sha256": screen.analysis_module_hash(),
        "git": {"commit": "x"},
        "seeds": seeds,
    }
    (root / "launch.json").write_text(json.dumps(launch))
    (root / "launch-finished.json").write_text(json.dumps({"units": [{"seed": s, "returncode": 0} for s in seeds]}))
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    diverged = diverged or {}

    def verify(unit: Path) -> tuple[dict[str, Any], dict[str, Any], RunSpec]:
        seed = int(unit.name.split("-")[1])
        if seed in broken:
            raise RuntimeError("simulated unit crash")
        spec = screen.expected_spec(plan_dict, seed)
        manifest = {"spec": spec.__dict__, "data": {"fit_sha256": "f" * 64, "dev_sha256": "d" * 64}, "git": {"commit": "x"}}
        status = {arm: ("diverged" if diverged.get(seed) == arm else "completed") for arm in runner.ARMS}
        return manifest, {"arm_status": status}, spec

    monkeypatch.setattr(screen, "verify_run", verify)
    monkeypatch.setattr(screen, "late_ce", lambda unit, epochs, arms: {a: values[int(unit.name.split("-")[1])][a] for a in arms})
    monkeypatch.setattr(screen, "epoch_ce", lambda unit, arms: {a: [values[int(unit.name.split("-")[1])][a]] * 7 for a in arms})
    monkeypatch.setattr(screen, "unit_costs", lambda unit, arms: {a: dict.fromkeys((*screen.COST_FIELDS, "wall_s"), 1.0) for a in arms})
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
    late = screen.late_ce(unit, [4, 5, 6], runner.ARMS)
    assert set(late) == set(runner.ARMS) and all(np.isfinite(v) for v in late.values())
    records = [json.loads(line) for line in (unit / "training.jsonl").read_text().splitlines()]
    expected = np.mean([r["dev"]["ce"] for r in records if r["kind"] == "epoch" and r["arm"] == "static" and r["epoch"] in (4, 5, 6)])
    assert late["static"] == pytest.approx(expected)  # T-3: epoch selection and dev CE, not train CE
    costs = screen.unit_costs(unit, runner.ARMS)
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
    "decision": {"delta_nats": 0.05, "max_failed_units": 1, "reading_rule": "positive-control-v1", "diverged_arm_policy": "fail_unit"},
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
        (-0.02, 0.02, "control_fails_below_floor"),
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


@pytest.mark.parametrize("name", ["positive-control-v1", "graft-capture-v1"])
def test_historical_round_two_plans_predate_the_divergence_policy(name):
    # Frozen and hash-pinned; they declare no diverged-arm policy, so current tooling refuses them (PDR-0047).
    with pytest.raises(ValueError, match="diverged_arm_policy"):
        screen.load_plan(runner.REPO / "docs" / "prereg" / f"{name}.json")


def test_graft_study_excludes_every_positive_control_seed():
    control = json.loads((runner.REPO / "docs" / "prereg" / "positive-control-v1.json").read_text())
    graft = json.loads((runner.REPO / "docs" / "prereg" / "graft-capture-v1.json").read_text())
    assert set(screen.unit_seeds(control)) <= set(graft["units"]["excluded_seeds"])
    assert "scheduled" not in json.dumps(control["analysis"]["contrasts"])


GRAFT_PLAN: dict[str, Any] = {
    **BASE_PLAN,
    "decision": {"delta_nats": 0.05, "max_failed_units": 1, "reading_rule": "graft-capture-v1", "diverged_arm_policy": "fail_unit"},
}


@pytest.mark.parametrize(
    ("graft_shift", "static_shift", "reading"),
    [
        (-0.15, -0.15, "progress"),  # graft matches static and clears the floor
        (-0.08, -0.16, "partial_capture"),  # static significantly better, graft significantly better than nothing
        (0.0, -0.16, "reopen_static_wins"),  # static better, graft captures nothing
        (0.0, 0.0, "reopen_no_value"),
    ],
)
def test_graft_capture_rule_separates_partial_from_no_capture(tmp_path, monkeypatch, graft_shift, static_shift, reading):
    values = unit_values(graft_shift, static_shift=static_shift, static_sd=0.005)
    root, plan = fake_screen(tmp_path, monkeypatch, values, plan=GRAFT_PLAN)
    assert screen.analyze(root, plan)["reading"] == reading


def test_graft_capture_rule_covers_every_verdict_combination():
    verdicts = ("first_better_beyond_floor", "first_worse", "first_better_floor_not_cleared", "equivalent_within_floor", "inconclusive")
    for none_verdict in verdicts:
        for static_lower in (-0.1, 0.01):
            for half_width in (0.01, 0.5):
                report = {
                    "delta_nats": 0.05,
                    "contrasts": {
                        "scheduled_minus_no_growth": {"verdict": none_verdict, "t_interval": {"half_width": half_width, "upper": -0.2}},
                        "scheduled_minus_static": {
                            "verdict": "inconclusive",
                            "t_interval": {"half_width": half_width, "lower": static_lower},
                        },
                    },
                }
                assert screen.reading_graft_capture_v1(report)[0] in screen.GRAFT_CAPTURE_READINGS


def test_positive_control_names_a_detected_deficit_below_the_floor(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0, static_shift=-0.03, static_sd=0.005), plan=POSITIVE_CONTROL)
    report = screen.analyze(root, plan)
    assert report["reading"] == "control_fails_below_floor"
    assert "effect_for_80pct_progress" in report["contrasts"]["static_minus_no_growth"]


def test_report_carries_per_epoch_means_for_declared_arms_only(tmp_path):
    unit = tmp_path / "seed-1"
    runner.train(RunSpec(epochs=7), unit)
    trajectory = screen.epoch_ce(unit, runner.ARMS)
    assert set(trajectory) == set(runner.ARMS) and all(len(v) == 7 for v in trajectory.values())


def test_launch_records_linked_plan_hashes_and_seals_runner_stdout(tmp_path, monkeypatch):
    linked = tmp_path / "graft.json"
    linked.write_text("{}")
    plan = copy.deepcopy(BASE_PLAN)
    plan["units"]["count"] = 1
    plan["linked_plans"] = [str(linked)]
    path = write_plan(tmp_path, plan)
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "train_command", lambda *a: ["true"])
    screen.launch(tmp_path / "screen", tmp_path, 1, path)
    record = json.loads((tmp_path / "screen" / "launch.json").read_text())
    assert record["linked_plan_sha256"] == {str(linked): file_hash(linked)}
    assert (tmp_path / "screen" / "seed-1.runner-stdout.sealed").exists()
    assert not (tmp_path / "screen" / "seed-1.stdout").exists()


def test_analysis_refuses_an_unfinished_fleet(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    (root / "launch-finished.json").unlink()
    with pytest.raises(ValueError, match="not finished"):
        screen.analyze(root, plan)
    assert not (root / "screen_report.json").exists()


def test_no_analysable_unit_is_raised_even_with_differing_messages(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=tuple(range(1, 21)))
    monkeypatch.setattr(screen, "verify_run", lambda unit: (_ for _ in ()).throw(FileNotFoundError(str(unit))))
    with pytest.raises(RuntimeError, match="no unit"):
        screen.analyze(root, plan)


def test_unit_whose_manifest_spec_disagrees_with_the_plan_is_a_failure(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    good = vars(screen)["verify_run"]  # the fake installed by fake_screen

    def impostor(unit: Path) -> Any:
        manifest, complete, spec = good(unit)
        if unit.name == "seed-3":
            manifest = {**manifest, "spec": {**manifest["spec"], "seed": 2}}
        return manifest, complete, spec

    monkeypatch.setattr(screen, "verify_run", impostor)
    report = screen.analyze(root, plan)
    assert [f["seed"] for f in report["failures"]] == [3] and "identity" in report["failures"][0]["error"]


@pytest.mark.parametrize(("failures", "reading_is_failure"), [(1, False), (2, True)])
def test_max_failed_units_boundary(tmp_path, monkeypatch, failures, reading_is_failure):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=tuple(range(1, failures + 1)))
    assert (screen.analyze(root, plan)["reading"] == "instrument_failure") is reading_is_failure


def test_a_diverged_contrast_arm_fails_the_unit_but_a_diverged_sealed_arm_does_not(tmp_path, monkeypatch):
    root, plan = fake_screen(
        tmp_path, monkeypatch, unit_values(0.0, static_shift=-0.3), plan=POSITIVE_CONTROL, diverged={2: "static", 5: "scheduled"}
    )
    report = screen.analyze(root, plan)
    assert [f["seed"] for f in report["failures"]] == [2]
    assert report["n_units"] == 19
    assert report["diverged_units_by_arm"] == {"no_growth": 0, "static": 1}  # sealed arm's status unreported


def test_instrument_failure_still_reports_observed_arm_means(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0), broken=(1, 2, 3))
    report = screen.analyze(root, plan)
    assert report["reading"] == "instrument_failure"
    assert set(report["observed_arm_late_ce_mean"]) == {"scheduled", "static", "no_growth"}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["analysis"].update(family_alpha=1.5),
        lambda p: p["analysis"].update(bootstrap_resamples=0),
        lambda p: p["decision"].update(delta_nats=-0.1),
        lambda p: p["decision"].update(max_failed_units=-1),
        lambda p: p["decision"].update(diverged_arm_policy="drop_unit"),
        lambda p: p["endpoint"].update(late_epochs=[5, 5, 6]),
        lambda p: p.update(linked_plans=["does/not/exist.json"]),
        lambda p: p.update(linked_plan=["typo.json"]),
    ],
)
def test_plan_numeric_and_structural_fields_are_validated(tmp_path, mutate):
    plan = copy.deepcopy(BASE_PLAN)
    mutate(plan)
    with pytest.raises(ValueError):
        screen.load_plan(write_plan(tmp_path, plan))


def test_launch_validates_workers_before_creating_anything(tmp_path, monkeypatch):
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    with pytest.raises(ValueError, match="workers"):
        screen.launch(tmp_path / "screen", tmp_path, 0, write_plan(tmp_path))
    assert not (tmp_path / "screen").exists()


def test_runner_stdout_really_lands_in_the_sealed_file(tmp_path, monkeypatch):
    plan = copy.deepcopy(BASE_PLAN)
    plan["units"]["count"] = 1
    path = write_plan(tmp_path, plan)
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "train_command", lambda *a: ["echo", "scheduled-arm-secret"])
    screen.launch(tmp_path / "screen", tmp_path, 1, path)
    assert "scheduled-arm-secret" in (tmp_path / "screen" / "seed-1.runner-stdout.sealed").read_text()


def gated_plan(tmp_path: Path, gate_root: Path, gate_plan: Path) -> Path:
    plan = copy.deepcopy(BASE_PLAN)
    plan["units"]["count"] = 1
    plan["gated_by"] = {"root": str(gate_root), "plan": str(gate_plan), "reading": "control_passes"}
    path = tmp_path / "gated.json"
    path.write_text(json.dumps(plan))
    return path


@pytest.mark.parametrize(
    ("reading", "pinned", "allowed"),
    [("control_passes", True, True), ("instrument_failure", True, False), ("control_passes", False, False)],
)
def test_gated_launch_requires_the_gate_reading_and_its_own_pinned_hash(tmp_path, monkeypatch, reading, pinned, allowed):
    gate_root = tmp_path / "gate"
    gate_root.mkdir()
    gate_plan = tmp_path / "gate-plan.json"
    gate_plan.write_text("{}")
    path = gated_plan(tmp_path, gate_root, gate_plan)
    (gate_root / "screen_report.json").write_text(json.dumps({"reading": reading}))
    (gate_root / "launch.json").write_text(json.dumps({"linked_plan_sha256": {str(path): file_hash(path) if pinned else "0" * 64}}))
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "train_command", lambda *a: ["true"])
    if allowed:
        screen.launch(tmp_path / "screen", tmp_path, 1, path)
    else:
        with pytest.raises(RuntimeError, match="gate"):
            screen.launch(tmp_path / "screen", tmp_path, 1, path)
        assert not (tmp_path / "screen").exists()


@pytest.mark.parametrize("field", ["commit", "data"])
def test_unit_from_another_commit_or_data_sample_is_a_failure(tmp_path, monkeypatch, field):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    good = vars(screen)["verify_run"]

    def stray(unit: Path) -> Any:
        manifest, complete, spec = good(unit)
        if unit.name == "seed-4":
            if field == "commit":
                manifest = {**manifest, "git": {"commit": "y"}}
            else:
                manifest = {**manifest, "data": {"fit_sha256": "e" * 64, "dev_sha256": "d" * 64}}
        return manifest, complete, spec

    monkeypatch.setattr(screen, "verify_run", stray)
    report = screen.analyze(root, plan)
    assert [f["seed"] for f in report["failures"]] == [4] and "identity" in report["failures"][0]["error"]


def test_analysis_refuses_when_launched_and_finished_seeds_disagree(tmp_path, monkeypatch):
    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    finished = json.loads((root / "launch-finished.json").read_text())
    finished["units"] = finished["units"][:-1]
    (root / "launch-finished.json").write_text(json.dumps(finished))
    with pytest.raises(ValueError, match="disagree"):
        screen.analyze(root, plan)


def test_plan_must_declare_linked_plans_explicitly(tmp_path):
    plan = copy.deepcopy(BASE_PLAN)
    del plan["linked_plans"]
    with pytest.raises(ValueError, match="linked_plans"):
        screen.load_plan(write_plan(tmp_path, plan))


def test_gate_accepts_the_pinned_plan_by_hash_whatever_path_spelling(tmp_path, monkeypatch):
    gate_root = tmp_path / "gate"
    gate_root.mkdir()
    gate_plan = tmp_path / "gate-plan.json"
    gate_plan.write_text("{}")
    path = gated_plan(tmp_path, gate_root, gate_plan)
    (gate_root / "screen_report.json").write_text(json.dumps({"reading": "control_passes"}))
    relative = Path(os.path.relpath(path))
    (gate_root / "launch.json").write_text(json.dumps({"linked_plan_sha256": {str(relative): file_hash(path)}}))
    monkeypatch.setattr(screen, "git_identity", lambda: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "train_command", lambda *a: ["true"])
    screen.launch(tmp_path / "screen", tmp_path, 1, path.resolve())


@pytest.mark.parametrize("missing", ["host", "seed_type", "train_size", "lr", "epochs"])
def test_plan_config_must_state_every_run_field(tmp_path, missing):
    """Flush F5: an omitted config key silently fell back to a RunSpec default."""
    plan = copy.deepcopy(BASE_PLAN)
    del plan["config"][missing]
    with pytest.raises(ValueError, match="config"):
        screen.load_plan(write_plan(tmp_path, plan))


def test_plan_must_declare_gated_by_explicitly(tmp_path):
    """Flush F6: an absent gated_by meant an ungated launch."""
    plan = copy.deepcopy(BASE_PLAN)
    del plan["gated_by"]
    with pytest.raises(ValueError, match="gated_by"):
        screen.load_plan(write_plan(tmp_path, plan))


@pytest.mark.parametrize(
    ("none_hw", "static_lower", "static_hw", "reading"),
    [
        (0.5, 0.01, 0.01, "reopen_instrument_imprecise"),  # imprecision outranks static-wins
        (0.01, -0.1, 0.5, "reopen_static_not_credible"),
    ],
)
def test_graft_capture_rule_precedence_for_imprecision_and_credibility(none_hw, static_lower, static_hw, reading):
    """Flush F11: these branches had no test; a reordering mutant passed the suite."""
    report = {
        "delta_nats": 0.05,
        "contrasts": {
            "scheduled_minus_no_growth": {"verdict": "inconclusive", "t_interval": {"half_width": none_hw, "upper": 0.1}},
            "scheduled_minus_static": {"verdict": "inconclusive", "t_interval": {"half_width": static_hw, "lower": static_lower}},
        },
    }
    assert screen.reading_graft_capture_v1(report)[0] == reading
