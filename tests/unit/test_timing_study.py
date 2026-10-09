"""Rung 4 (PDR-0054): does graft timing, or the training horizon, change the outcome?

The criteria are tested on constructed units; the launcher and analysis on fakes; the
runner contract is tested elsewhere.
"""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from experiments import bounded_comparison as runner
from experiments import timing_study as ts
from experiments.bounded_data import RunSpec, file_hash

CELLS = {
    "T0": {"graft_epoch": 0, "epochs": 10},
    "T1": {"graft_epoch": 1, "epochs": 10},
    "T2": {"graft_epoch": 2, "epochs": 10},
    "T3": {"graft_epoch": 3, "epochs": 10},
    "T5": {"graft_epoch": 5, "epochs": 10},
    "H20": {"graft_epoch": 2, "epochs": 20},
}
CRITERIA = {
    "delta_timing": 0.02,
    "delta_horizon": 0.05,
    "family_alpha": 0.05,
    "timing_contrast": ["T0", "T3"],
    "timing_reference": "T2",
    "horizon_contrast": ["H20", "T2"],
    "lever_cell": "T0",
    "max_graft_failures_per_cell": 3,
    "max_static_failures": 10,
    "max_failed_runs": 2,
    "bootstrap_resamples": 500,
    "bootstrap_seed": 1,
}


def unit(
    cell: str, seed: int, graft: float, static: float = 1.40, ng: float = 1.55, *, graft_div: bool = False, static_div: bool = False
) -> dict[str, Any]:
    status = {
        "no_growth": "completed",
        "static": "diverged" if static_div else "completed",
        "scheduled": "diverged" if graft_div else "completed",
    }
    late = {"no_growth": ng, "static": None if static_div else static, "scheduled": None if graft_div else graft}
    horizon = "h20" if cell == "H20" else "h10"
    prefix = f"p-g2-{seed}" if cell in ("T2", "H20") else f"p-{cell}-{seed}"  # H20 continues T2
    return {
        "cell": cell,
        "seed": seed,
        "status": status,
        "late_ce": late,
        "replay_digest": {"no_growth": f"ng-{horizon}-{seed}", "static": f"st-{horizon}-{seed}"},
        "prefix_digest": prefix,
    }


def world(timing_slope: float, horizon_shrink: float, n: int = 40, noise: float = 0.01) -> list[dict[str, Any]]:
    """Graft late CE rises with later germination; at 20 epochs the graft-static gap shrinks by horizon_shrink."""
    import numpy as np

    rng = np.random.default_rng(0)
    units = []
    for seed in range(n):
        base = 1.46 + noise * float(rng.standard_normal())
        for cell, spec in CELLS.items():
            if cell == "H20":
                graft = base - horizon_shrink - 0.10 + noise * float(rng.standard_normal())
                units.append(unit(cell, seed, graft, static=1.30, ng=1.45))
            else:
                graft = base + timing_slope * spec["graft_epoch"] + noise * float(rng.standard_normal())
                units.append(unit(cell, seed, graft))
    return units


def test_three_way_classification_uses_the_given_margin() -> None:
    assert ts.classify({"lower": -0.04, "upper": -0.025}, 0.02) == "beyond_floor"
    assert ts.classify({"lower": -0.04, "upper": -0.025}, 0.05) == "flat"


def test_three_way_classification() -> None:
    assert ts.classify({"lower": 0.06, "upper": 0.09}, 0.05) == "beyond_floor"
    assert ts.classify({"lower": -0.09, "upper": -0.06}, 0.05) == "beyond_floor"
    assert ts.classify({"lower": -0.02, "upper": 0.03}, 0.05) == "flat"
    assert ts.classify({"lower": 0.01, "upper": 0.07}, 0.05) == "inconclusive"


def test_earlier_grafting_that_helps_beyond_delta_finds_a_lever() -> None:
    report = ts.evaluate(world(timing_slope=0.03, horizon_shrink=0.0), CELLS, CRITERIA)
    assert report["timing"]["classification"] == "beyond_floor" and report["timing"]["mean"] < 0
    assert report["reading"] == "lever_found"


def test_a_shrinking_gap_at_twenty_epochs_finds_a_lever() -> None:
    report = ts.evaluate(world(timing_slope=0.0, horizon_shrink=0.08), CELLS, CRITERIA)
    assert report["horizon"]["classification"] == "beyond_floor" and report["horizon"]["mean"] < 0
    assert report["reading"] == "lever_found"


def test_flat_timing_and_horizon_with_static_winning_everywhere_stops_the_ladder() -> None:
    report = ts.evaluate(world(timing_slope=0.0, horizon_shrink=0.0), CELLS, CRITERIA)
    assert report["timing"]["classification"] == "flat" and report["horizon"]["classification"] == "flat"
    assert report["static_wins_every_cell"] is True
    assert report["reading"] == "flat_stop"


def test_a_cell_where_static_does_not_clearly_win_blocks_the_stop() -> None:
    units = world(timing_slope=0.0, horizon_shrink=0.0)
    for u in units:
        if u["cell"] == "T5":  # outside the timing contrast  # graft and static indistinguishable here
            u["late_ce"]["scheduled"] = u["late_ce"]["static"] + (0.02 if u["seed"] % 2 else -0.02)
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["static_wins_every_cell"] is False and report["reading"] == "inconclusive"


def test_the_lever_cell_beating_static_finds_a_lever() -> None:
    units = world(timing_slope=0.0, horizon_shrink=0.0)
    for u in units:
        if u["cell"] == "T0":
            u["late_ce"]["scheduled"] = u["late_ce"]["static"] - 0.02
    assert ts.evaluate(units, CELLS, CRITERIA)["lever_cell"]["graft_beats_static"] is True


def test_graft_failures_are_capped_per_cell() -> None:
    units = world(timing_slope=0.03, horizon_shrink=0.0)
    for u in [u for u in units if u["cell"] == "T0"][:4]:
        u["status"]["scheduled"] = "diverged"
        u["late_ce"]["scheduled"] = None
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["reading"] == "graft_unstable" and report["graft_unstable_cells"] == ["T0"]
    assert report["divergences"]["T0"]["scheduled"]["diverged"] == 4


def test_static_failures_are_counted_once_per_seed_and_horizon() -> None:
    units = world(timing_slope=0.03, horizon_shrink=0.0)
    for u in units:
        if u["seed"] == 3 and u["cell"] != "H20":
            u["status"]["static"] = "diverged"
            u["late_ce"]["static"] = None
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["static_failures"] == 1  # one host trajectory, seen in five identical T cells
    assert report["reading"] == "lever_found"


def test_a_replay_mismatch_across_timing_cells_is_an_instrument_failure() -> None:
    units = world(timing_slope=0.03, horizon_shrink=0.0)
    next(u for u in units if u["cell"] == "T3")["replay_digest"]["static"] = "different"
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["replay"]["mismatches"] and report["reading"] == "instrument_failure"


def test_capture_fraction_is_described_per_cell() -> None:
    report = ts.evaluate(world(timing_slope=0.03, horizon_shrink=0.0), CELLS, CRITERIA)
    assert set(report["capture_fraction"]) == set(CELLS)
    assert report["capture_fraction"]["T0"]["estimate"] > report["capture_fraction"]["T5"]["estimate"]


def test_beyond_floor_in_the_adverse_direction_is_not_a_lever() -> None:
    later_better = ts.evaluate(world(timing_slope=-0.03, horizon_shrink=0.0), CELLS, CRITERIA)
    assert later_better["timing"]["favourable"] is False and later_better["reading"] == "changes_adversely"
    widening = ts.evaluate(world(timing_slope=0.0, horizon_shrink=-0.08), CELLS, CRITERIA)
    assert widening["horizon"]["favourable"] is False and widening["reading"] == "changes_adversely"


def test_a_timing_effect_peaking_mid_range_blocks_the_stop() -> None:
    units = world(timing_slope=0.0, horizon_shrink=0.0)
    for u in units:
        if u["cell"] == "T1":
            u["late_ce"]["scheduled"] -= 0.04  # T0 and T3 equal; T1 clearly better
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["timing"]["classification"] == "flat"
    assert report["timing_shape"]["cells"]["T1"]["classification"] == "beyond_floor"
    assert report["reading"] == "inconclusive"


def test_a_long_cell_that_does_not_continue_its_short_twin_is_an_instrument_failure() -> None:
    units = world(timing_slope=0.03, horizon_shrink=0.0)
    next(u for u in units if u["cell"] == "H20")["prefix_digest"] = "different"
    report = ts.evaluate(units, CELLS, CRITERIA)
    assert report["replay"]["mismatches"][0][0] == "prefix" and report["reading"] == "instrument_failure"


def test_a_lever_cell_without_three_pairs_is_an_instrument_failure() -> None:
    units = world(timing_slope=0.0, horizon_shrink=0.0, n=40)
    for u in units:
        if u["cell"] in ("T0", "T1", "T2", "T3", "T5") and u["seed"] > 1:
            u["status"]["static"] = "diverged"
            u["late_ce"]["static"] = None
    assert ts.evaluate(units, CELLS, {**CRITERIA, "max_static_failures": 50})["reading"] == "instrument_failure"


# --- plan, launch and analysis ---

PLAN_PATH = runner.REPO / "docs" / "prereg" / "rung4-timing-horizon.json"


def base_plan() -> dict[str, Any]:
    validated = json.loads((runner.REPO / "docs" / "prereg" / "lifecycle-v2-validation.json").read_text())
    config = {k: v for k, v in validated["config"].items() if k not in ("graft_epoch", "epochs")}
    config.update(host="under_normalized", seed_type="norm", lifecycle="v2")
    return {
        "study": {"id": "test-timing"},
        "units": {"first_seed": 9901, "count": 3, "excluded_seeds": []},
        "cells": copy.deepcopy(CELLS),
        "config": config,
        "endpoint": {"late_window": 3},
        "data_identity": validated["data_identity"],
        "criteria": {**CRITERIA, "max_graft_failures_per_cell": 2, "max_static_failures": 2, "max_failed_runs": 2},
        "gated_by": None,
        "linked_plans": [],
    }


def write(tmp_path: Path, plan: dict[str, Any]) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path


def test_plan_loads_and_derives_late_windows(tmp_path: Path) -> None:
    plan = ts.load_plan(write(tmp_path, base_plan()))
    assert ts.late_epochs(plan, "T0") == [7, 8, 9] and ts.late_epochs(plan, "H20") == [17, 18, 19]
    assert ts.expected_spec(plan, "H20", 9901).epochs == 20 and ts.expected_spec(plan, "T5", 9901).graft_epoch == 5


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["cells"].update(T9={"graft_epoch": 9, "epochs": 10}),  # cannot fossilize inside the horizon
        lambda p: p["config"].update(epochs=10),  # a cell field set in config
        lambda p: p["criteria"].update(timing_contrast=["T0", "T7"]),
        lambda p: p["criteria"].update(timing_contrast=["T3", "T0"]),  # earlier graft must come first
        lambda p: p["criteria"].update(timing_contrast=["T0", "H20"]),  # across horizons
        lambda p: p["criteria"].update(horizon_contrast=["H20", "T3"]),  # different graft timing
        lambda p: p["criteria"].update(timing_reference="H20"),
        lambda p: p["cells"].update({"../x": {"graft_epoch": 4, "epochs": 10}}),
        lambda p: p["cells"].update(T2b={"graft_epoch": 2, "epochs": 10}),  # duplicate spec
        lambda p: p["endpoint"].update(late_window=8),  # window before germination in T5
        lambda p: p["criteria"].update(lever_cell="H40"),
        lambda p: p["criteria"].update(max_graft_failures_per_cell=3),  # not below units.count
        lambda p: p["data_identity"].pop("dev_sha256"),
        lambda p: p["units"].update(first_seed=7001, excluded_seeds=[7001]),
    ],
)
def test_plan_refusals(tmp_path: Path, mutate: Any) -> None:
    plan = base_plan()
    mutate(plan)
    with pytest.raises(ValueError):
        ts.load_plan(write(tmp_path, plan))


def test_launch_runs_every_cell_of_a_seed_on_one_gpu_from_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = base_plan()
    path = write(tmp_path, plan)
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    monkeypatch.setattr(ts, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(ts, "make_snapshot", lambda dest: snapshot)
    monkeypatch.setattr(ts, "visible_gpus", lambda: [0, 1])
    monkeypatch.setattr(ts, "cifar_source_hashes", lambda root: plan["data_identity"]["source_files"])
    monkeypatch.setattr(
        ts, "load_fit_dev", lambda spec, root: (None, None, None, None, {k: plan["data_identity"][k] for k in ("fit_sha256", "dev_sha256")})
    )
    seen: list[tuple[str, str, str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        seen.append(
            (command[command.index("--seed") + 1], command[command.index("--graft-epoch") + 1], kwargs["env"]["CUDA_VISIBLE_DEVICES"])
        )
        assert kwargs["cwd"] == snapshot
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.timing_study.subprocess.run", fake_run)
    finished = ts.launch(tmp_path / "study", tmp_path, 2, path)
    assert len(seen) == len(finished["units"]) == 3 * 6
    for seed in {s for s, _, _ in seen}:
        assert len({gpu for s, _, gpu in seen if s == seed}) == 1  # every cell of a seed on one device


def _fake_study(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: tuple[tuple[str, int], ...] = ()) -> tuple[Path, Path]:
    plan = base_plan()
    path = write(tmp_path, plan)
    root = tmp_path / "study"
    root.mkdir()
    loaded = ts.load_plan(path)
    launch = {
        "prereg_sha256": file_hash(path),
        "analysis_module_sha256": ts.analysis_module_hash(),
        "git": {"commit": "x"},
        "jobs": ts.unit_seeds(loaded),
        "snapshot": str(runner.REPO),
    }
    (root / "launch.json").write_text(json.dumps(launch))
    finished = [{"cell": c, "seed": s} for s in ts.unit_seeds(loaded) for c in loaded["cells"]]
    (root / "launch-finished.json").write_text(json.dumps({"units": finished}))
    monkeypatch.setattr(ts, "git_identity", lambda *a: {"commit": "x", "status": ""})
    synthetic = {(u["cell"], u["seed"] + 9901): u for u in world(timing_slope=0.03, horizon_shrink=0.0, n=3)}

    def verify(run: Path) -> tuple[dict[str, Any], dict[str, Any], RunSpec]:
        cell, seed = run.name, int(run.parent.name.split("-")[1])
        if (cell, seed) in broken:
            raise RuntimeError("simulated crash")
        spec = ts.expected_spec(loaded, cell, seed)
        data = {k: plan["data_identity"][k] for k in ("source_files", "fit_sha256", "dev_sha256")}
        return {"spec": spec.__dict__, "data": data, "git": {"commit": "x"}}, {}, spec

    def summary(run: Path, late: list[int]) -> dict[str, Any]:
        u = synthetic[(run.name, int(run.parent.name.split("-")[1]))]
        return {k: u[k] for k in ("status", "late_ce", "replay_digest", "prefix_digest")}

    monkeypatch.setattr(ts, "verify_run", verify)
    monkeypatch.setattr(ts, "run_summary", lambda run, late, short: summary(run, late))
    return root, path


def test_analysis_publishes_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path = _fake_study(tmp_path, monkeypatch)
    report = ts.analyze(root, path)
    assert report["n_runs"] == 18 and report["failures"] == []
    assert json.loads((root / ts.REPORT).read_text())["reading"] == report["reading"]
    with pytest.raises(FileExistsError):
        ts.analyze(root, path)


def test_analysis_refuses_outside_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path = _fake_study(tmp_path, monkeypatch)
    launch = json.loads((root / "launch.json").read_text())
    (root / "launch.json").write_text(json.dumps({**launch, "snapshot": str(tmp_path / "elsewhere")}))
    with pytest.raises(ValueError, match="snapshot"):
        ts.analyze(root, path)


def test_a_crashed_run_is_recorded_and_beyond_the_allowance_is_instrument_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path = _fake_study(tmp_path, monkeypatch, broken=(("T0", 9901), ("T5", 9902), ("H20", 9903)))
    report = ts.analyze(root, path)
    assert len(report["failures"]) == 3 and report["reading"] == "instrument_failure"


def test_the_committed_rung4_plan_matches_the_owner_signed_decide() -> None:
    plan = ts.load_plan(PLAN_PATH)
    assert {c: (v["graft_epoch"], v["epochs"]) for c, v in plan["cells"].items()} == {
        "T0": (0, 10),
        "T1": (1, 10),
        "T2": (2, 10),
        "T3": (3, 10),
        "T5": (5, 10),
        "H20": (2, 20),
    }
    assert (plan["config"]["host"], plan["config"]["seed_type"], plan["config"]["lifecycle"]) == ("under_normalized", "norm", "v2")
    assert (plan["criteria"]["delta_timing"], plan["criteria"]["delta_horizon"]) == (0.02, 0.05)
    assert plan["criteria"]["timing_contrast"] == ["T0", "T3"] and plan["criteria"]["lever_cell"] == "T0"
    used = set(range(7001, 7097)) | set(range(9301, 9328)) | set(range(4001, 4025))
    assert set(ts.unit_seeds(plan)).isdisjoint(used)


def test_an_interrupted_fleet_resumes_from_its_own_snapshot_and_keeps_partial_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = base_plan()
    path = write(tmp_path, plan)
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    monkeypatch.setattr(ts, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(ts, "make_snapshot", lambda dest: snapshot)
    monkeypatch.setattr(ts, "visible_gpus", lambda: [0, 1])
    monkeypatch.setattr(ts, "cifar_source_hashes", lambda root: plan["data_identity"]["source_files"])
    monkeypatch.setattr(
        ts, "load_fit_dev", lambda spec, root: (None, None, None, None, {k: plan["data_identity"][k] for k in ("fit_sha256", "dev_sha256")})
    )
    trained: list[str] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        out = Path(command[command.index("--output") + 1])
        out.mkdir(parents=True)
        (out / "complete.json").write_text("{}")
        trained.append(f"{out.parent.name}/{out.name}")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.timing_study.subprocess.run", fake_run)
    root = tmp_path / "study"
    ts.launch(root, tmp_path, 2, path)
    # Simulate an interruption: the fleet never finished and one run died mid-way.
    (root / "launch-finished.json").unlink()
    (ts.unit_dir(root, 9902, "T3") / "complete.json").unlink()
    trained.clear()
    finished = ts.launch(root, tmp_path, 2, path, resume=True)
    assert trained == ["seed-9902/T3"]
    assert sum(1 for u in finished["units"] if u.get("resumed")) == 17
    assert list((root / "units" / "seed-9902").glob("T3.partial-*"))  # set aside, never deleted
    (root / "launch-finished.json").unlink()
    path.write_text(json.dumps({**plan, "study": {"id": "changed"}}))
    with pytest.raises(RuntimeError, match="resume refused"):
        ts.launch(root, tmp_path, 2, path, resume=True)
