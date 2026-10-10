"""Fleet C1-S: Fleet C1's deficit screen re-read with the static arm born at tau (simic-e3803e8200).

The supplement trains only `static_calibrated`, on the parent fleet's seeds, and pairs it with the
parent's sealed no-growth and graft arms. What must hold:
- the plan cannot drift from the parent: same seeds, config, data and screen criteria; BatchNorm
  hosts screened, a host without BatchNorm as the control;
- on pairing seeds the unit's no-growth, and its control-host static_calibrated, equal the
  parent's no-growth and registered static bit for bit, on real units from both code paths;
- the screen is `c1_study.evaluate`'s, term for term, with static_calibrated in static's place;
- a pairing mismatch, a missing parent analysis or an unfinished parent stops the reading.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from experiments import c1_study as c1
from experiments import c1s_study as c1s
from experiments.bounded_comparison import REPO
from experiments.bounded_data import file_hash
from tests.unit import test_c1_study as tc1

PARENT_PLAN: dict[str, Any] = {**copy.deepcopy(tc1.SMOKE_PLAN), "study": {"id": "c1-smoke-parent"}}
SEEDS = (7, 8, 9)
COMMIT = "fixture-commit"  # units record git identity; pinned so a commit landing mid-build cannot split them (PyTorch review)


def _pins() -> dict[str, str]:
    return {name: file_hash(REPO / name) for name in c1s.SOURCE_FILES}


def _supplement_plan(parent_path: Path, parent_root: Path, **change: Any) -> dict[str, Any]:
    parent = json.loads(parent_path.read_text())
    plan = {
        "study": {"id": "c1s-smoke"},
        "parent": {"plan": str(parent_path), "plan_sha256": file_hash(parent_path), "root": str(parent_root)},
        "units": parent["units"],
        "hosts": ["mild"],
        "control_host": "under_normalized",
        "pairing_seeds": 2,
        "config": parent["config"],
        "data_identity": parent["data_identity"],
        "criteria": {
            "deficit_min_gain": parent["criteria"]["deficit_min_gain"],
            "static_divergence_cap": parent["criteria"]["static_divergence_cap"],
            "max_failed_units": 0,
        },
        "source_sha256": _pins(),
        "fallback": "No reading: the BatchNorm hosts are unscreened and John decides.",
    }
    plan.update(change)
    return plan


def _write(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(json.dumps(data))
    return path


@pytest.fixture(scope="module")
def fleets(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """A real three-seed parent fleet (c1_study.run_unit) and its supplement (c1s_study.run_unit), on CPU."""
    base = tmp_path_factory.mktemp("c1s")
    parent_path = _write(base / "parent.json", PARENT_PLAN)
    parent_root = base / "parent"
    plan_path = _write(base / "plan.json", _supplement_plan(parent_path, parent_root))
    root = base / "supplement"
    with pytest.MonkeyPatch.context() as mp:
        for module in (c1, c1s):
            mp.setattr(module, "git_identity", lambda *a: {"commit": COMMIT, "status": ""})
        for seed in SEEDS:
            c1.run_unit(c1.load_plan(parent_path), seed, parent_root / "units" / f"seed-{seed}", None, file_hash(parent_path))
            c1s.run_unit(c1s.load_plan(plan_path), seed, root / "units" / f"seed-{seed}", None, file_hash(plan_path))
    return {"base": base, "parent_path": parent_path, "parent_root": parent_root, "plan_path": plan_path, "root": root}


def _rows(run: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (run / "arms.jsonl").read_text().splitlines()]


def test_units_carry_the_corrected_arm_and_pairing_rows_only_on_pairing_seeds(fleets: dict[str, Path]) -> None:
    plan = c1s.load_plan(fleets["plan_path"])
    for seed, pairing in ((7, True), (8, True), (9, False)):
        rows = _rows(fleets["root"] / "units" / f"seed-{seed}")
        keys = {(r["host"], r["arm"]) for r in rows}
        assert keys == c1s.expected_rows(plan, seed)
        assert (("mild", "no_growth") in keys) is pairing and (("under_normalized", c1s.ARM) in keys) is pairing
        mild = next(r for r in rows if (r["host"], r["arm"]) == ("mild", c1s.ARM))
        assert mild["birth"]["calibration_mode"] == "train" and mild["status"] == "completed"


def test_pairing_rows_equal_the_parents_bitwise(fleets: dict[str, Path]) -> None:
    for seed in (7, 8):
        own = _rows(fleets["root"] / "units" / f"seed-{seed}")
        parent = _rows(fleets["parent_root"] / "units" / f"seed-{seed}")
        assert c1s.pairing_check(own, parent, "under_normalized") == []


def test_the_corrected_arm_differs_from_the_registered_one_on_a_bn_host(fleets: dict[str, Path]) -> None:
    own = {(r["host"], r["arm"]): r for r in _rows(fleets["root"] / "units" / "seed-7")}
    parent = {(r["host"], r["arm"]): r for r in _rows(fleets["parent_root"] / "units" / "seed-7")}
    assert own[("mild", c1s.ARM)]["birth"]["gain_at_birth"] > 5 * parent[("mild", "static")]["birth"]["gain_at_birth"]


def test_pairing_check_names_any_changed_record(fleets: dict[str, Path]) -> None:
    own = _rows(fleets["root"] / "units" / "seed-7")
    parent = _rows(fleets["parent_root"] / "units" / "seed-7")
    for r in parent:
        if (r["host"], r["arm"]) in (("mild", "no_growth"), ("under_normalized", "static")):
            r["records"][-1]["dev"]["ce"] += 1e-12
    assert c1s.pairing_check(own, parent, "under_normalized") == ["seed 7 mild/no_growth", f"seed 7 under_normalized/{c1s.ARM}"]


def test_verify_refuses_a_missing_or_extra_pairing_row(fleets: dict[str, Path], tmp_path: Path) -> None:
    plan = c1s.load_plan(fleets["plan_path"])
    commit = COMMIT
    rows = c1s.verify_unit(fleets["root"] / "units" / "seed-9", plan, seed=9, plan_sha256=file_hash(fleets["plan_path"]), commit=commit)
    assert {(r["host"], r["arm"]) for r in rows} == {("mild", c1s.ARM)}
    with pytest.raises(ValueError, match="rows differ"):  # seed 9's rows read as if it were a pairing seed
        c1s.verify_unit(
            fleets["root"] / "units" / "seed-9",
            {**plan, "pairing_seeds": 3},
            seed=9,
            plan_sha256=file_hash(fleets["plan_path"]),
            commit=commit,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"hosts": ["under_normalized"]}, "BatchNorm"),
        ({"control_host": "mild", "hosts": ["mild"]}, "control"),
        ({"pairing_seeds": 0}, "pairing_seeds"),
        ({"pairing_seeds": 4}, "pairing_seeds"),
        ({"units": {"first_seed": 7, "count": 4}}, "units"),
        ({"config": {**tc1.SMOKE_PLAN["config"], "epochs": 8}}, "config"),
        ({"criteria": {"deficit_min_gain": 0.04, "static_divergence_cap": 0.10, "max_failed_units": 0}}, "deficit_min_gain"),
        ({"criteria": {"deficit_min_gain": 0.05, "static_divergence_cap": 0.10}}, "criteria keys"),
        ({"surprise": 1}, "plan keys"),
        ({"hosts": []}, "BatchNorm"),
        ({"fallback": ""}, "no reading"),
        ({"source_sha256": {"experiments/c1s_study.py": "0" * 64}}, "source_sha256"),
    ],
)
def test_load_plan_refuses_drift_from_the_parent(fleets: dict[str, Path], tmp_path: Path, change: dict[str, Any], message: str) -> None:
    plan = _supplement_plan(fleets["parent_path"], fleets["parent_root"], **change)
    with pytest.raises(ValueError, match=message):
        c1s.load_plan(_write(tmp_path / "bad.json", plan))


def test_load_plan_refuses_a_changed_parent_plan(fleets: dict[str, Path], tmp_path: Path) -> None:
    plan = _supplement_plan(fleets["parent_path"], fleets["parent_root"])
    plan["parent"]["plan_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="parent plan"):
        c1s.load_plan(_write(tmp_path / "bad.json", plan))


def test_the_screen_is_c1s_screen_term_for_term() -> None:
    units = tc1._units(n=40, static_gain={"mild": 0.12, "channel_starved": 0.0})
    for u in units:
        u["arms"][c1s.ARM] = dict(u["arms"]["static"])
    criteria = tc1.CRITERIA
    theirs = c1.evaluate(units, criteria)["deficit_screen"]
    ours = c1s.evaluate([u for u in units if u["host"] != "under_normalized"], criteria, theirs)["deficit_screen"]
    for host, reading in ours.items():
        assert {k: v for k, v in reading.items() if k != "registered"} == theirs[host]
        assert reading["registered"] == theirs[host]
    assert ours["mild"]["passes"] is True and ours["channel_starved"]["passes"] is False


def test_the_screen_scores_a_diverged_corrected_arm_at_chance_and_flags_instability() -> None:
    units = [u for u in tc1._units(n=40) if u["host"] == "mild"]
    for i, u in enumerate(units):
        u["arms"][c1s.ARM] = dict(u["arms"]["static"])
        if i < 5:  # 12.5% > the 10% cap
            u["arms"][c1s.ARM] = {"status": "diverged", "late_ce": None}
    screen = c1s.evaluate(units, tc1.CRITERIA, {})["deficit_screen"]["mild"]
    assert screen["static_divergence_rate"] == 5 / 40 and screen["unstable"] is True and screen["passes"] is False


# --- launch and analysis, over the real three-seed fleets ---


def _publishable(
    fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch, parent_instrument: str = "ok", parent_screen_passes: bool = True
) -> tuple[Path, Path]:
    """Launch records for both fleets, and the parent's own report, as their launches and analysis would write them."""
    parent_root, root = fleets["parent_root"], fleets["root"]
    parent_launch = {"prereg_sha256": file_hash(fleets["parent_path"]), "git": {"commit": COMMIT}, "jobs": list(SEEDS)}
    _write(parent_root / "launch.json", parent_launch)
    _write(parent_root / "launch-finished.json", {"units": [{"seed": s} for s in SEEDS]})
    screen = {"under_normalized": {"passes": parent_screen_passes}, "mild": {"passes": False}}
    reading = {"instrument": parent_instrument, "fleet_a_hosts": ["under_normalized"]}
    _write(parent_root / c1.REPORT, {"deficit_screen": screen, "reading": reading})
    launch = {
        "prereg_sha256": file_hash(fleets["plan_path"]),
        "analysis_module_sha256": c1s.analysis_module_hash(),
        "git": {"commit": COMMIT},
        "jobs": list(SEEDS),
        "snapshot": str(REPO),
    }
    _write(root / "launch.json", launch)
    _write(root / "launch-finished.json", {"units": [{"seed": s} for s in SEEDS]})
    monkeypatch.setattr(c1s, "git_identity", lambda *a: {"commit": COMMIT, "status": ""})
    (root / c1s.REPORT).unlink(missing_ok=True)
    return root, fleets["plan_path"]


def test_analysis_reads_once_with_the_pairing_confirmed(fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan_path = _publishable(fleets, monkeypatch)
    report = c1s.analyze(root, plan_path)
    assert report["pairing"] == {"seeds": [7, 8], "mismatches": []} and report["failed_seeds"] == []
    assert report["reading"]["instrument"] == "ok"
    assert report["deficit_screen"]["mild"]["n"] == 3 and report["deficit_screen"]["mild"]["registered"] == {"passes": False}
    assert report["reading"]["fleet_a_hosts"][0] == "under_normalized"  # the control's screen is the parent's
    assert set(report["reading"]) == {"instrument", "fleet_a_hosts"}  # the registered BN screen never enters
    assert report["parent"]["reading"]["fleet_a_hosts"] == ["under_normalized"]
    assert report["static_gain_completed_only"]["mild"]["n"] == 3 and "mild" in report["corrected_minus_registered_static"]
    with pytest.raises(FileExistsError):
        c1s.analyze(root, plan_path)


def test_a_pairing_mismatch_stops_the_reading(fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan_path = _publishable(fleets, monkeypatch)
    monkeypatch.setattr(c1s, "pairing_check", lambda own, parent, control: ["seed 7 mild/no_growth"] if own[0]["seed"] == 7 else [])
    report = c1s.analyze(root, plan_path)
    assert report["reading"]["instrument"] == "pairing_failure" and report["reading"]["fleet_a_hosts"] == []


def test_analysis_waits_for_the_parents_own_analysis(fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan_path = _publishable(fleets, monkeypatch)
    (fleets["parent_root"] / c1.REPORT).unlink()
    with pytest.raises(ValueError, match="parent fleet's own analysis"):
        c1s.analyze(root, plan_path)


def test_launch_waits_for_the_parent_fleet(fleets: dict[str, Path], tmp_path: Path) -> None:
    parent_root = tmp_path / "unfinished"
    parent_root.mkdir()
    plan_path = _write(tmp_path / "plan.json", _supplement_plan(fleets["parent_path"], parent_root))
    with pytest.raises(RuntimeError, match="has not finished"):
        c1s.launch(tmp_path / "out", tmp_path, 1, plan_path)
    assert not (tmp_path / "out").exists()


def test_the_committed_plan_is_the_approved_supplement_to_the_running_fleet() -> None:
    plan = c1s.load_plan(REPO / "docs/prereg/fleet-c1s.json")
    parent, _ = c1s.load_parent_plan(plan)
    assert plan["parent"] == {
        "plan": "docs/prereg/fleet-c1.json",
        "plan_sha256": file_hash(REPO / "docs/prereg/fleet-c1.json"),
        "root": "/home/john/simic-worktrees/fleet-c1/runs/fleet-c1",
    }
    assert c1s.unit_seeds(plan) == c1.unit_seeds(parent) == list(range(10001, 10769))
    assert sorted(plan["hosts"]) == ["channel_starved", "mild", "no_spatial_mix"] and plan["control_host"] == "under_normalized"
    assert plan["pairing_seeds"] == 48 and plan["study"]["pilot"] is False
    assert plan["criteria"] == {"deficit_min_gain": 0.05, "static_divergence_cap": 0.10, "max_failed_units": 22}
    c1s.check_sources(plan, REPO)  # once Fleet C1-S has launched, compare against its snapshot instead
    dry = c1s.load_plan(REPO / "docs/prereg/fleet-c1s-dryrun.json")
    assert dry["study"]["pilot"] is True and dry["pairing_seeds"] == dry["units"]["count"] and dry["hosts"] == plan["hosts"]


# --- review fixes (2026-10-10): every seed tied to the parent, the correction verified, ordering, pins ---


def _resealed_copy(src: Path, dst: Path, edit: Any) -> Path:
    """A copy of a unit with its rows edited and its seal recomputed, so only the content checks can refuse it."""
    dst.mkdir(parents=True)
    rows = [edit(r) for r in _rows(src)]
    (dst / "arms.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (dst / "manifest.json").write_text((src / "manifest.json").read_text())
    complete = json.loads((src / "complete.json").read_text())
    complete["artifacts"] = {name: file_hash(dst / name) for name in ("manifest.json", "arms.jsonl")}
    (dst / "complete.json").write_text(json.dumps(complete))
    return dst


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda b: {**b, "calibration_mode": "registered"}, "train mode"),
        (lambda b: {**b, "realised_ratio_at_birth": 0.0017}, "not tau"),
        (lambda b: {**b, "realised_ratio_at_birth": "nan"}, "not tau"),
    ],
)
def test_verify_refuses_a_corrected_arm_that_was_not_born_at_tau(fleets: dict[str, Path], tmp_path: Path, edit: Any, message: str) -> None:
    plan = c1s.load_plan(fleets["plan_path"])

    def change(r: dict[str, Any]) -> dict[str, Any]:
        return {**r, "birth": edit(r["birth"])} if (r["host"], r["arm"]) == ("mild", c1s.ARM) else r

    unit = _resealed_copy(fleets["root"] / "units" / "seed-9", tmp_path / "seed-9", change)
    with pytest.raises(ValueError, match=message):
        c1s.verify_unit(unit, plan, seed=9, plan_sha256=file_hash(fleets["plan_path"]), commit=COMMIT)


def test_identity_check_ties_every_seed_to_the_parents_start(fleets: dict[str, Path]) -> None:
    own_dir, parent_dir = fleets["root"] / "units" / "seed-9", fleets["parent_root"] / "units" / "seed-9"
    own, parent = _rows(own_dir), _rows(parent_dir)
    manifests = json.loads((own_dir / "manifest.json").read_text()), json.loads((parent_dir / "manifest.json").read_text())
    assert c1s.identity_check(own, parent, *manifests) == []  # a non-pairing seed, checked all the same
    moved = [{**r, "birth": {**r["birth"], "body_init_sha256": "0" * 64}} if r["arm"] == c1s.ARM else r for r in own]
    assert c1s.identity_check(moved, parent, *manifests) == [f"seed 9 mild/{c1s.ARM} birth"]
    other_future = {**manifests[0], "future_sha256": "0" * 64}
    assert c1s.identity_check(own, parent, other_future, manifests[1]) == ["seed 9 future_sha256"]


def test_a_failed_parent_voids_the_reading(fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan_path = _publishable(fleets, monkeypatch, parent_instrument="instrument_failure")
    report = c1s.analyze(root, plan_path)
    assert report["reading"] == {"instrument": "parent_failure", "fleet_a_hosts": []}


def test_a_confirmatory_launch_is_refused_once_the_parents_report_exists(fleets: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    _publishable(fleets, monkeypatch)  # writes the parent's report
    with pytest.raises(RuntimeError, match="before the parent's results"):
        c1s.launch(fleets["base"] / "late", fleets["base"], 1, fleets["plan_path"])
    assert not (fleets["base"] / "late").exists()


def test_launch_and_analysis_refuse_source_that_differs_from_the_pins(fleets: dict[str, Path], tmp_path: Path) -> None:
    plan = _supplement_plan(fleets["parent_path"], fleets["parent_root"])
    plan["source_sha256"]["experiments/atlas_static.py"] = "0" * 64
    with pytest.raises(RuntimeError, match=r"atlas_static\.py"):
        c1s.check_sources(c1s.load_plan(_write(tmp_path / "plan.json", plan)), REPO)
    c1s.check_sources(c1s.load_plan(fleets["plan_path"]), REPO)  # the true pins pass
