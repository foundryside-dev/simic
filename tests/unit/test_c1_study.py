"""Fleet C1 (PDR-0057 G1, deficit screen, cost price): the pre-registered evaluation on synthetic units."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from experiments import c1_study as c1

HOSTS = ("under_normalized", "channel_starved", "no_spatial_mix", "mild")
SCALES = (1.1, 1.25, 1.5, 2.0)
CRITERIA: dict[str, Any] = {
    "margin": 0.02,
    "family_alpha": 0.025,
    "co_primary_hosts": ["under_normalized", "mild"],
    "step_down": [1.25, 1.5, 2.0],
    "deficit_min_gain": 0.05,
    "static_divergence_cap": 0.10,
    "trim": 0.1,
    "bootstrap_resamples": 2000,
    "bootstrap_seed": 7,
    "max_failed_units": 4,
    "comparator_divergence_cap": 0.025,
    "graft_divergence_cap": 0.025,
}


def _units(
    n: int = 96,
    graft_vs_scale: dict[str, dict[float, float]] | None = None,
    static_gain: dict[str, float] | None = None,
    slope: float = -0.08,
    sd: float = 0.05,
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Per (seed, host) late CE for seven arms. scale-up CE = noop + slope * log2(m) + noise."""
    rng = np.random.default_rng(seed)
    gvs = graft_vs_scale or {}
    sg = static_gain or {}
    units = []
    for s in range(n):
        for host in HOSTS:
            base = 1.6 + rng.normal(0, 0.05)
            arms: dict[str, Any] = {
                "no_growth": {"status": "completed", "late_ce": base, "param_steps": 1000, "installed_parameters": 1000}
            }
            for m in SCALES:
                arms[c1.scale_arm(m)] = {
                    "status": "completed",
                    "late_ce": base + slope * math.log2(m) + rng.normal(0, 0.01),
                    "param_steps": round(1000 * m),
                    "installed_parameters": round(1000 * m),
                }
            ref = arms[c1.scale_arm(1.25)]["late_ce"]
            arms["graft"] = {
                "status": "completed",
                "late_ce": ref + gvs.get(host, {}).get(1.25, 0.0) + rng.normal(0, sd),
                "param_steps": 1001,
                "installed_parameters": 1001,
            }
            arms["static"] = {
                "status": "completed",
                "late_ce": base - sg.get(host, 0.12) + rng.normal(0, 0.03),
                "param_steps": 1001,
                "installed_parameters": 1001,
            }
            units.append({"seed": 20000 + s, "host": host, "arms": arms})
    return units


def test_graft_equal_to_large_scaleup_is_non_inferior_at_every_step() -> None:
    # graft matches 1.25x; slope -0.08 makes 1.5x and 2.0x better by 0.02 and 0.06 nats
    units = _units(graft_vs_scale={h: {1.25: -0.1} for h in HOSTS})
    report = c1.evaluate(units, CRITERIA)
    g1 = report["g1"]["under_normalized"]
    assert g1["reading"] == "non_inferior" and g1["largest_m"] == 2.0
    assert [step["m"] for step in g1["steps"]] == [1.25, 1.5, 2.0]
    assert g1["co_primary"] is True and report["g1"]["channel_starved"]["co_primary"] is False


def test_step_down_stops_at_the_first_failure() -> None:
    units = _units(graft_vs_scale={h: {1.25: -0.01} for h in HOSTS})  # passes 1.25, fails 1.5 (0.02 worse)
    g1 = c1.evaluate(units, CRITERIA)["g1"]["under_normalized"]
    assert g1["reading"] == "non_inferior" and g1["largest_m"] == 1.25
    assert len(g1["steps"]) == 2 and g1["steps"][1]["non_inferior"] is False


def test_a_clearly_worse_graft_reads_inferior_and_refutes_c1() -> None:
    units = _units(graft_vs_scale={"under_normalized": {1.25: 0.08}})
    report = c1.evaluate(units, CRITERIA)
    assert report["g1"]["under_normalized"]["reading"] == "inferior"
    assert report["reading"]["c1"] == "refuted_at_bounded_scale"


def test_a_graft_near_the_margin_reads_inconclusive() -> None:
    units = _units(graft_vs_scale={"under_normalized": {1.25: 0.02}}, sd=0.08)
    g1 = c1.evaluate(units, CRITERIA)["g1"]["under_normalized"]
    assert g1["reading"] == "inconclusive" and g1["largest_m"] is None


def test_a_diverged_graft_scores_chance_ce_and_is_never_dropped() -> None:
    units = _units(graft_vs_scale={h: {1.25: -0.1} for h in HOSTS})
    hit = [u for u in units if u["host"] == "under_normalized"][:3]
    for u in hit:
        u["arms"]["graft"] = {"status": "diverged", "late_ce": None, "param_steps": 1001, "installed_parameters": 1001}
    report = c1.evaluate(units, CRITERIA)
    first = report["g1"]["under_normalized"]["steps"][0]
    assert first["n"] == 96
    assert report["failures"]["under_normalized"]["graft"]["diverged"] == 3


def test_the_trimmed_companion_must_also_clear() -> None:
    """A pass carried by the mean alone (a heavy tail of graft wins) is not non-inferior."""
    units = _units(graft_vs_scale={h: {1.25: 0.03} for h in HOSTS}, sd=0.005)
    for u in [u for u in units if u["host"] == "under_normalized"][:12]:
        u["arms"]["graft"]["late_ce"] -= 0.6  # a few huge wins drag the mean under the margin
    first = c1.evaluate(units, CRITERIA)["g1"]["under_normalized"]["steps"][0]
    assert first["mean_upper"] < CRITERIA["margin"] and first["trimmed_upper"] >= CRITERIA["margin"]
    assert first["non_inferior"] is False


def test_deficit_screen_keeps_hosts_where_static_clearly_helps() -> None:
    units = _units(static_gain={"under_normalized": 0.14, "channel_starved": 0.12, "no_spatial_mix": 0.03, "mild": -0.01})
    screen = c1.evaluate(units, CRITERIA)["deficit_screen"]
    assert {h for h, v in screen.items() if v["passes"]} == {"under_normalized", "channel_starved"}
    assert screen["mild"]["passes"] is False


def test_static_instability_flags_the_host() -> None:
    units = _units()
    for u in [u for u in units if u["host"] == "no_spatial_mix"][:12]:
        u["arms"]["static"] = {"status": "diverged", "late_ce": None, "param_steps": 1001, "installed_parameters": 1001}
    screen = c1.evaluate(units, CRITERIA)["deficit_screen"]["no_spatial_mix"]
    assert screen["static_divergence_rate"] == pytest.approx(12 / 96)
    assert screen["unstable"] is True and screen["passes"] is False


def test_lambda_is_minus_the_scaleup_slope_and_never_negative() -> None:
    assert c1.evaluate(_units(slope=-0.08), CRITERIA)["lambda"]["lambda"] == pytest.approx(0.08, abs=0.01)
    flat = c1.evaluate(_units(slope=0.03), CRITERIA)["lambda"]
    assert flat["slope"] > 0 and flat["lambda"] == 0.0


def test_missing_arms_count_as_failed_units_and_can_fail_the_instrument() -> None:
    units = _units()
    for u in units[:5]:
        del u["arms"]["scale_x1.5"]
    report = c1.evaluate(units, CRITERIA)
    assert report["incomplete_units"] == 5 and report["reading"]["instrument"] == "instrument_failure"


# --- the unit runner, on CPU smoke data ---

import copy  # noqa: E402
import json as _json  # noqa: E402
from pathlib import Path  # noqa: E402

SMOKE_PLAN: dict[str, Any] = {
    "study": {"id": "c1-smoke"},
    "units": {"first_seed": 7, "count": 3},
    "hosts": ["under_normalized", "mild"],
    "decision_epoch": 1,
    "scales": [1.1, 1.25],
    "config": {"data": "smoke", "epochs": 7, "lifecycle": "v2", "device": "cpu"},
    "data_identity": {},
    "criteria": {**CRITERIA, "step_down": [1.25]},
}


def _write_plan(tmp_path: Path, plan: dict[str, Any]) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(_json.dumps(plan))
    return path


@pytest.fixture(scope="module")
def smoke_unit(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("c1") / "seed-7"
    c1.run_unit(c1.load_plan(_write_plan(tmp_path_factory.mktemp("p"), SMOKE_PLAN)), 7, out, None, "0" * 64)
    return out


def test_unit_writes_every_host_and_arm_and_verifies(smoke_unit: Path) -> None:
    commit = _json.loads((smoke_unit / "manifest.json").read_text())["git"]["commit"]
    summaries = c1.verify_unit(smoke_unit, SMOKE_PLAN, seed=7, plan_sha256="0" * 64, commit=commit)
    assert {s["host"] for s in summaries} == {"under_normalized", "mild"}
    for s in summaries:
        assert set(s["arms"]) == {"no_growth", "graft", "static", "scale_x1.1", "scale_x1.25"}
        done = {a: v["param_steps"] for a, v in s["arms"].items() if v["status"] == "completed"}
        order = [a for a in ("no_growth", "scale_x1.1", "scale_x1.25") if a in done]
        assert [done[a] for a in order] == sorted(done[a] for a in order)  # wider hosts cost more, when they finish
        for v in s["arms"].values():  # a diverged arm is a row with no late CE, never a missing row
            assert (v["late_ce"] is None) == (v["status"] == "diverged")


def test_unit_arms_match_the_atlas_and_the_runner(smoke_unit: Path) -> None:
    """The graft is the atlas fork at the decision point; the no-op the trunk (both pinned to the runner elsewhere)."""
    from experiments import atlas

    rows = {(r["host"], r["arm"]): r for r in map(_json.loads, (smoke_unit / "arms.jsonl").read_text().splitlines())}
    spec = c1.unit_spec(SMOKE_PLAN, 7, "mild")
    unit = atlas.Unit.load(spec)
    trunk = unit.trunk(decision_points=(1,))
    graft = unit.branch(trunk.snapshots[1], action="conv_light")

    def strip(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{k: v for k, v in r.items() if k != "wall_s"} for r in rs]

    assert strip(rows[("mild", "no_growth")]["records"]) == strip(trunk.records)
    assert strip(rows[("mild", "graft")]["records"]) == strip(graft.records)
    assert rows[("mild", "graft")]["records"][0]["birth"]["body_init_sha256"]


def test_verify_refuses_a_changed_file_or_a_missing_arm(smoke_unit: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    for name in ("manifest.json", "complete.json", "arms.jsonl"):
        (bad / name).write_text((smoke_unit / name).read_text())
    lines = (bad / "arms.jsonl").read_text().splitlines()
    (bad / "arms.jsonl").write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(ValueError, match="changed"):
        c1.verify_unit(bad, SMOKE_PLAN, seed=7, plan_sha256="0" * 64, commit="x")


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["criteria"].pop("trim"),
        lambda p: p.update(hosts=["under_normalized", "healthy"]),
        lambda p: p["criteria"].update(co_primary_hosts=["channel_starved"]),
        lambda p: p["criteria"].update(step_down=[1.5]),
        lambda p: p.update(extra=1),
    ],
)
def test_load_plan_refuses_malformed_plans(tmp_path: Path, change: Any) -> None:
    plan = copy.deepcopy(SMOKE_PLAN)
    change(plan)
    with pytest.raises((ValueError, KeyError)):
        c1.load_plan(_write_plan(tmp_path, plan))


def test_an_unstable_comparator_blocks_the_c1_claim() -> None:
    """A diverged scale-up scores chance CE, which would hand the graft a free pass: the host reads comparator_unstable."""
    units = _units(graft_vs_scale={h: {1.25: 0.0} for h in HOSTS})
    for u in [u for u in units if u["host"] == "under_normalized"][:10]:
        u["arms"]["scale_x1.25"] = {"status": "diverged", "late_ce": None, "param_steps": 600, "installed_parameters": 600}
    report = c1.evaluate(units, CRITERIA)
    g1 = report["g1"]["under_normalized"]
    assert g1["reading"] == "comparator_unstable" and g1["largest_m"] is None
    assert g1["comparator_divergence"]["scale_x1.25"] == pytest.approx(10 / 96)
    assert report["reading"]["c1"] == "comparator_unstable"
    assert report["g1"]["mild"]["reading"] != "comparator_unstable"


def test_unit_refuses_data_that_differ_from_the_pinned_identity(tmp_path: Path) -> None:
    plan = copy.deepcopy(SMOKE_PLAN)
    plan["data_identity"] = {"fit_sha256": "0" * 64}
    with pytest.raises(ValueError, match="data identity"):
        c1.run_unit(c1.load_plan(_write_plan(tmp_path, plan)), 7, tmp_path / "u", None, "0" * 64)


# --- Code review (2026-10-10): data checks, crash-safe units, identity checks, launch/analyze/resume ---

import subprocess  # noqa: E402

from experiments.atlas_hosts import scaled_config  # noqa: E402
from experiments.bounded_comparison import REPO  # noqa: E402
from experiments.bounded_data import file_hash  # noqa: E402


def test_cifar_plans_must_pin_the_full_data_identity(tmp_path: Path) -> None:
    plan = copy.deepcopy(SMOKE_PLAN)
    plan["config"] = {**plan["config"], "data": "cifar", "train_size": 4096, "dev_size": 5000}
    with pytest.raises(ValueError, match="data_identity"):
        c1.load_plan(_write_plan(tmp_path, plan))


def test_data_identity_is_checked_before_any_output_exists(tmp_path: Path) -> None:
    plan = copy.deepcopy(SMOKE_PLAN)
    plan["data_identity"] = {"fit_sha256": "0" * 64}
    with pytest.raises(ValueError, match="data identity"):
        c1.run_unit(c1.load_plan(_write_plan(tmp_path, plan)), 7, tmp_path / "u", None, "0" * 64)
    assert not (tmp_path / "u").exists()


def test_a_crash_mid_unit_keeps_the_manifest_and_finished_rows_but_no_seal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from experiments import atlas

    real = atlas.Unit.static
    calls = {"n": 0}

    def flaky(self: atlas.Unit, seed_type: str) -> atlas.Span:
        calls["n"] += 1
        if calls["n"] == 2:  # the second host's static arm
            raise RuntimeError("simulated crash")
        return real(self, seed_type)

    monkeypatch.setattr(atlas.Unit, "static", flaky)
    out = tmp_path / "u"
    with pytest.raises(RuntimeError, match="simulated"):
        c1.run_unit(c1.load_plan(_write_plan(tmp_path, SMOKE_PLAN)), 7, out, None, "0" * 64)
    assert (out / "manifest.json").is_file() and not (out / "complete.json").exists()
    rows = [_json.loads(line) for line in (out / "arms.jsonl").read_text().splitlines()]
    assert {r["host"] for r in rows if r["host"] == "under_normalized"} == {"under_normalized"}
    assert len([r for r in rows if r["host"] == "under_normalized"]) == 5  # every first-host arm was kept


def test_static_and_scaled_arms_match_the_atlas(smoke_unit: Path) -> None:
    import dataclasses

    from experiments import atlas

    rows = {(r["host"], r["arm"]): r for r in map(_json.loads, (smoke_unit / "arms.jsonl").read_text().splitlines())}
    unit = atlas.Unit.load(c1.unit_spec(SMOKE_PLAN, 7, "mild"))

    def strip(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{k: v for k, v in r.items() if k != "wall_s"} for r in rs]

    assert strip(rows[("mild", "static")]["records"]) == strip(unit.static("conv_light").records)
    scaled = dataclasses.replace(unit, host_cfg=scaled_config("mild", 1.1)).trunk(decision_points=())
    assert strip(rows[("mild", "scale_x1.1")]["records"]) == strip(scaled.records)


def test_verify_binds_the_unit_to_its_seed_plan_and_commit(smoke_unit: Path) -> None:
    manifest = _json.loads((smoke_unit / "manifest.json").read_text())
    ok = {"seed": 7, "plan_sha256": "0" * 64, "commit": manifest["git"]["commit"]}
    assert c1.verify_unit(smoke_unit, SMOKE_PLAN, **ok)
    for bad in ({"seed": 8}, {"plan_sha256": "1" * 64}, {"commit": "f" * 40}):
        with pytest.raises(ValueError):
            c1.verify_unit(smoke_unit, SMOKE_PLAN, **{**ok, **bad})


def test_verify_refuses_rows_that_differ_from_the_plan_even_when_resealed(smoke_unit: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "manifest.json").write_text((smoke_unit / "manifest.json").read_text())
    lines = (smoke_unit / "arms.jsonl").read_text().splitlines()
    (bad / "arms.jsonl").write_text("\n".join(lines[:-1]) + "\n")
    seal = {"schema": c1.SCHEMA, "status": "complete", "rows": len(lines) - 1}
    seal["artifacts"] = {n: file_hash(bad / n) for n in ("manifest.json", "arms.jsonl")}
    (bad / "complete.json").write_text(_json.dumps(seal))
    commit = _json.loads((smoke_unit / "manifest.json").read_text())["git"]["commit"]
    with pytest.raises(ValueError, match="differ"):
        c1.verify_unit(bad, SMOKE_PLAN, seed=7, plan_sha256="0" * 64, commit=commit)


def test_a_trunk_that_diverges_before_the_decision_fails_the_graft_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from experiments import atlas

    real = atlas.Unit.trunk

    def early(self: atlas.Unit, decision_points: tuple[int, ...]) -> atlas.Span:
        if not decision_points:
            return real(self, decision_points)
        span = atlas.Span(costs=self._fresh_costs())
        span.diverged = {"epoch": 0, "step": 3, "reason": "injected", "stage": "dormant", "witness": {"seed_present": False}, "birth": None}
        return span

    monkeypatch.setattr(atlas.Unit, "trunk", early)
    out = tmp_path / "u"
    c1.run_unit(c1.load_plan(_write_plan(tmp_path, SMOKE_PLAN)), 7, out, None, "0" * 64)
    rows = {(r["host"], r["arm"]): r for r in map(_json.loads, (out / "arms.jsonl").read_text().splitlines())}
    assert rows[("mild", "no_growth")]["status"] == "diverged"
    assert rows[("mild", "graft")]["status"] == "diverged" and "before the decision" in rows[("mild", "graft")]["diverged"]["reason"]


def _launch_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, plan: dict[str, Any]) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    path = repo / "docs" / "plan.json"
    path.write_text(_json.dumps(plan))
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    monkeypatch.setattr(c1, "REPO", repo)
    monkeypatch.setattr(c1, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(c1, "make_snapshot", lambda dest: snapshot)
    monkeypatch.setattr(c1, "visible_gpus", lambda: [0, 1])
    return path, snapshot


def test_launch_runs_each_seed_once_on_one_gpu_from_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {**copy.deepcopy(SMOKE_PLAN), "config": {**SMOKE_PLAN["config"], "device": "cuda"}}
    path, snapshot = _launch_env(tmp_path, monkeypatch, plan)
    seen: list[tuple[str, str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        assert kwargs["cwd"] == snapshot and command[command.index("--plan") + 1] == str(snapshot / "docs" / "plan.json")
        seen.append((command[command.index("--seed") + 1], kwargs["env"]["CUDA_VISIBLE_DEVICES"]))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.c1_study.subprocess.run", fake_run)
    finished = c1.launch(tmp_path / "study", tmp_path, 2, path)
    assert sorted(s for s, _ in seen) == ["7", "8", "9"] and len(finished["units"]) == 3
    assert {g for _, g in seen} <= {"0", "1"}


def test_launch_preflight_refuses_exposed_test_data_and_plans_outside_the_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, _ = _launch_env(tmp_path, monkeypatch, SMOKE_PLAN)
    exposed = tmp_path / "data"
    (exposed / "cifar-10-batches-py").mkdir(parents=True)
    (exposed / "cifar-10-batches-py" / "test_batch").write_text("x")
    with pytest.raises(RuntimeError, match="test_batch"):
        c1.launch(tmp_path / "study", exposed, 1, path)
    outside = tmp_path / "plan.json"
    outside.write_text(_json.dumps(SMOKE_PLAN))
    with pytest.raises(ValueError, match="repository"):
        c1.launch(tmp_path / "study2", tmp_path, 1, outside)
    assert not (tmp_path / "study").exists() and not (tmp_path / "study2").exists()
    with pytest.raises(ValueError, match="workers"):
        c1.launch(tmp_path / "study3", tmp_path, 0, path)


def test_resume_keeps_finished_seeds_and_sets_partial_ones_aside(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, _ = _launch_env(tmp_path, monkeypatch, SMOKE_PLAN)
    ran: list[str] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        ran.append(command[command.index("--seed") + 1])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.c1_study.subprocess.run", fake_run)
    root = tmp_path / "study"
    c1.launch(root, tmp_path, 1, path)
    (root / "launch-finished.json").unlink()
    (root / "units" / "seed-7").mkdir(parents=True)
    (root / "units" / "seed-7" / "complete.json").write_text("{}")
    (root / "units" / "seed-8").mkdir(parents=True)  # interrupted: no seal
    ran.clear()
    c1.launch(root, tmp_path, 1, path, resume=True)
    assert sorted(ran) == ["8", "9"]
    assert any(p.name.startswith("seed-8.partial-") for p in (root / "units").iterdir())


def _fake_fleet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, plan: dict[str, Any], broken: tuple[int, ...] = ()) -> tuple[Path, Path]:
    root = tmp_path / "study"
    root.mkdir()
    path = _write_plan(tmp_path, plan)
    loaded = c1.load_plan(path)
    launch: dict[str, Any] = {"prereg_sha256": file_hash(path), "analysis_module_sha256": c1.analysis_module_hash()}
    launch |= {"git": {"commit": "x"}, "jobs": c1.unit_seeds(loaded), "snapshot": str(REPO)}
    (root / "launch.json").write_text(_json.dumps(launch))
    (root / "launch-finished.json").write_text(_json.dumps({"units": [{"seed": s} for s in c1.unit_seeds(loaded)]}))
    monkeypatch.setattr(c1, "git_identity", lambda *a: {"commit": "x", "status": ""})
    synthetic = {
        u["seed"] - 20000 + loaded["units"]["first_seed"]: u for u in _units(n=loaded["units"]["count"]) if u["host"] in loaded["hosts"]
    }
    by_seed: dict[int, list[dict[str, Any]]] = {}
    for u in _units(n=loaded["units"]["count"]):
        if u["host"] in loaded["hosts"]:
            by_seed.setdefault(u["seed"] - 20000 + loaded["units"]["first_seed"], []).append(
                {**u, "seed": u["seed"] - 20000 + loaded["units"]["first_seed"]}
            )
    assert synthetic

    def verify(run: Path, plan: dict[str, Any], *, seed: int, plan_sha256: str, commit: str) -> list[dict[str, Any]]:
        assert run.name == f"seed-{seed}" and plan_sha256 == launch["prereg_sha256"] and commit == "x"
        if seed in broken:
            raise RuntimeError("simulated crash")
        return by_seed[seed]

    monkeypatch.setattr(c1, "verify_unit", verify)
    return root, path


FLEET_PLAN: dict[str, Any] = {
    **copy.deepcopy(SMOKE_PLAN),
    "units": {"first_seed": 101, "count": 40},
    "scales": [1.1, 1.25, 1.5, 2.0],
    "criteria": CRITERIA,
}


def test_analysis_publishes_once_from_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path = _fake_fleet(tmp_path, monkeypatch, FLEET_PLAN)
    report = c1.analyze(root, path)
    assert report["reading"]["instrument"] == "ok" and report["failed_seeds"] == []
    assert _json.loads((root / c1.REPORT).read_text())["reading"] == report["reading"]
    with pytest.raises(FileExistsError):
        c1.analyze(root, path)


def test_a_pilot_never_produces_a_reading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {**copy.deepcopy(FLEET_PLAN), "study": {"id": "pilot", "pilot": True}}
    root, path = _fake_fleet(tmp_path, monkeypatch, plan)
    report = c1.analyze(root, path)
    assert report["reading"]["c1"] == "pilot_no_reading" and report["reading"]["fleet_a_hosts"] == []
    assert report["g1"]["under_normalized"]["steps"]  # the spreads are still reported, for sizing


def test_crashed_seeds_and_incomplete_units_count_together_against_the_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {**copy.deepcopy(FLEET_PLAN), "criteria": {**CRITERIA, "max_failed_units": 4}}
    root, path = _fake_fleet(tmp_path, monkeypatch, plan, broken=(101, 102))  # 2 seeds x 2 hosts = 4 units: at the cap
    assert c1.analyze(root, path)["reading"]["instrument"] == "ok"
    (tmp_path / "b").mkdir()
    root2, path2 = _fake_fleet(tmp_path / "b", monkeypatch, plan, broken=(101, 102, 103))  # 6 units: over
    assert c1.analyze(root2, path2)["reading"]["instrument"] == "instrument_failure"


def test_analysis_refuses_a_fleet_whose_finished_seeds_differ_from_the_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path = _fake_fleet(tmp_path, monkeypatch, FLEET_PLAN)
    (root / "launch-finished.json").write_text(_json.dumps({"units": [{"seed": 101}]}))
    with pytest.raises(ValueError, match="planned"):
        c1.analyze(root, path)


# --- Statistics review (2026-10-10): F1 truncation, F3 graft cap, F4 caps below trim, F5 lambda ---


def test_an_unstable_large_comparator_truncates_the_step_down_but_keeps_earlier_steps() -> None:
    units = _units(graft_vs_scale={h: {1.25: -0.1} for h in HOSTS})
    for u in [u for u in units if u["host"] == "under_normalized"][:10]:
        u["arms"]["scale_x2"] = {"status": "diverged", "late_ce": None, "param_steps": 900, "installed_parameters": 2000}
    g1 = c1.evaluate(units, CRITERIA)["g1"]["under_normalized"]
    assert g1["reading"] == "non_inferior" and g1["largest_m"] == 1.5 and g1["comparator_unstable_at"] == 2.0
    assert [s["m"] for s in g1["steps"]] == [1.25, 1.5]


def test_a_refutation_survives_an_unstable_larger_comparator() -> None:
    units = _units(graft_vs_scale={"under_normalized": {1.25: 0.08}})
    for u in [u for u in units if u["host"] == "under_normalized"][:10]:
        u["arms"]["scale_x1.5"] = {"status": "diverged", "late_ce": None, "param_steps": 900, "installed_parameters": 1500}
    report = c1.evaluate(units, CRITERIA)
    assert report["g1"]["under_normalized"]["reading"] == "inferior" and report["reading"]["c1"] == "refuted_at_bounded_scale"


def test_a_diverging_graft_reads_graft_unstable_and_never_supports_c1() -> None:
    units = _units(graft_vs_scale={h: {1.25: -0.1} for h in HOSTS})
    for u in [u for u in units if u["host"] == "under_normalized"][:5]:
        u["arms"]["graft"] = {"status": "diverged", "late_ce": None, "param_steps": 1001, "installed_parameters": 1001}
    report = c1.evaluate(units, CRITERIA)
    assert report["g1"]["under_normalized"]["reading"] == "graft_unstable" and report["reading"]["c1"] == "graft_unstable"


def test_divergence_caps_must_sit_below_the_trim(tmp_path: Path) -> None:
    for key in ("comparator_divergence_cap", "graft_divergence_cap"):
        plan = copy.deepcopy(SMOKE_PLAN)
        plan["criteria"][key] = 0.1  # equal to the trim
        with pytest.raises(ValueError, match="trim"):
            c1.load_plan(_write_plan(tmp_path, plan))


def test_lambda_keeps_units_whose_no_growth_diverged_and_reports_a_failure_sensitivity() -> None:
    units = _units(slope=-0.08)
    for u in units[:8]:
        u["arms"]["no_growth"] = {"status": "diverged", "late_ce": None, "param_steps": 300, "installed_parameters": 1000}
    lam = c1.evaluate(units, CRITERIA)["lambda"]
    assert lam["lambda"] == pytest.approx(0.08, abs=0.01) and lam["excluded_runs"] == 8
    assert lam["sensitivity_failures_at_chance"]["slope"] < lam["slope"]  # chance CE at the base (x = 0) steepens the fall


def test_the_committed_fleet_c1_plan_matches_pdr_0057() -> None:
    """The confirmatory plan carries the signed design, fresh seeds, and no pilot flag."""
    plan = c1.load_plan(REPO / "docs" / "prereg" / "fleet-c1.json")
    crit = plan["criteria"]
    assert plan["study"]["pilot"] is False and plan["decision_epoch"] == 1
    assert plan["hosts"] == ["under_normalized", "channel_starved", "no_spatial_mix", "mild"]
    assert crit["co_primary_hosts"] == ["under_normalized", "mild"] and crit["step_down"] == [1.25, 1.5, 2.0]
    assert (crit["margin"], crit["family_alpha"], crit["deficit_min_gain"], crit["trim"]) == (0.02, 0.025, 0.05, 0.1)
    assert crit["comparator_divergence_cap"] < crit["trim"] and crit["graft_divergence_cap"] < crit["trim"]
    seeds = set(c1.unit_seeds(plan))
    assert seeds == set(range(10001, 10769))
    seen = set(range(1001, 9425)) | set(range(9901, 9911))  # every bounded study, pilot and probe so far
    assert seeds.isdisjoint(seen)
    reserved = set(range(13001, 13193)) | set(range(13401, 13449)) | set(range(14001, 14193))  # Fleet A, G3 audit, G4
    assert seeds.isdisjoint(reserved) and max(seeds) < 15001  # host family starts at 15001
    pilot = c1.load_plan(REPO / "docs" / "prereg" / "fleet-c1-pilot.json")
    assert plan["data_identity"] == pilot["data_identity"] and plan["config"] == pilot["config"]
