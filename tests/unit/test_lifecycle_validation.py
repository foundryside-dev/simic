"""Lifecycle-v2 validation study: launch layout and the pre-declared acceptance criteria.

Design: docs/bounded-lifecycle-v2.md. Criteria are computed from per-unit summaries, so
they are tested here on constructed units; the runner contract is tested elsewhere.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pytest

from experiments import bounded_comparison as runner
from experiments import lifecycle_validation as lv
from experiments.bounded_data import RunSpec, file_hash


def test_rho_crosses_one_exactly_at_the_nesterov_limit() -> None:
    lr, m = 0.05, 0.9
    limit = 2 * (1 + m) / (lr * (1 + 2 * m))
    assert lv.rho(limit * 0.999, lr, m) < 1 < lv.rho(limit * 1.001, lr, m)
    assert lv.rho(1.0, lr, m) < 1


def test_growth_score_sums_only_the_expanding_steps() -> None:
    """kappa = 1/lr = 20 is nearly nilpotent (log rho ~ -18); a plain sum would let it swamp the growth."""
    expected = sum(math.log(lv.rho(k, 0.05, 0.9)) for k in (30.0, 40.0))
    assert lv.growth_score([10.0, 20.0, 30.0, 40.0], 0.05, 0.9) == pytest.approx(expected)
    assert lv.growth_score([0.3, 12.0, 20.0], 0.05, 0.9) == 0.0


def test_auc_is_mann_whitney_with_ties_half() -> None:
    assert lv.auc([3.0, 4.0], [1.0, 2.0]) == 1.0
    assert lv.auc([1.0], [1.0]) == 0.5
    assert lv.auc([1.0, 3.0], [2.0]) == 0.5


def test_mcnemar_exact_two_sided() -> None:
    assert lv.mcnemar_p(0, 0) == 1.0
    assert lv.mcnemar_p(6, 0) == pytest.approx(2 * 0.5**6)


def test_tost_equivalence() -> None:
    assert lv.tost_equivalent([0.01, -0.01, 0.0, 0.02, -0.02] * 4, margin=0.05, alpha=0.05) is True
    assert lv.tost_equivalent([0.2, 0.25, 0.3, 0.22] * 4, margin=0.05, alpha=0.05) is False


def unit(
    cell: str,
    variant: str,
    seed: int,
    *,
    sched_div: bool = False,
    stage: str = "training",
    kappas: list[float] | None = None,
    static_div: bool = False,
    late: float = 1.0,
) -> dict[str, Any]:
    trace = kappas if kappas is not None else [5.0, 6.0]
    host = "mild" if cell == "C" else "under_normalized"
    return {
        "cell": cell,
        "host": host,
        "variant": variant,
        "seed": seed,
        "status": {
            "no_growth": "completed",
            "static": "diverged" if static_div else "completed",
            "scheduled": "diverged" if sched_div else "completed",
        },
        "scheduled_divergence_stage": stage if sched_div else None,
        "scheduled_divergence_epoch": 2 if sched_div else None,
        "ste_kappa": trace,
        "ste_gain": [0.02] * len(trace),
        "ste_clamped_steps": 0,
        # An STE-step divergence: every row but the diverging one precedes it.
        "ste_rows_before_divergence": len(trace) - 1 if sched_div and stage == "training" else None,
        "late_ce": {"no_growth": 1.2, "static": None if static_div else 1.1, "scheduled": None if sched_div else late},
        "replay_digest": {"no_growth": f"ng-{host}-{seed}", "static": f"st-{cell}-{seed}"},
    }


def accepted_world() -> list[dict[str, Any]]:
    units = []
    for cell in ("A", "B", "C"):
        for seed in range(24):
            diverges = cell in ("A", "B") and seed < 6
            units.append(unit(cell, "v1", seed, sched_div=diverges, kappas=[40.0, 60.0] if diverges else [10.0, 20.0]))
            units.append(unit(cell, "v2", seed, kappas=[10.0, 13.0]))
    return units


PLAN = {
    "stable_cells": ["A", "B"],
    "regression_cell": "C",
    "tost_margin": 0.05,
    "alpha": 0.05,
    "auc_min": 0.9,
    "bilinear_allowance": 0.1,
    "lr": 0.05,
    "momentum": 0.9,
}


def test_a_world_matching_the_mechanism_is_accepted() -> None:
    report = lv.evaluate_criteria(accepted_world(), PLAN)
    assert report["c1_v2_stable"]["pass"] is True and report["c1_v2_stable"]["rule_of_three_upper"] == pytest.approx(3 / 48)
    c2 = report["c2_mechanism"]
    assert c2["falsification"]["sensitivity"] == 1.0 and c2["intervention"]["v1_only"] == 12 and c2["pass"] is True
    assert c2["ranking"]["within_cell_auc"] == 1.0 and c2["ranking"]["within_cell_pairs"] == 2 * 6 * 18
    assert report["c3_replay"]["pass"] is True
    assert report["accepted"] is True


def test_a_v2_divergence_fails_c1() -> None:
    units = accepted_world()
    next(u for u in units if u["cell"] == "A" and u["variant"] == "v2").update(
        status={"no_growth": "completed", "static": "completed", "scheduled": "diverged"}, scheduled_divergence_stage="blending"
    )
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c1_v2_stable"]["pass"] is False and report["accepted"] is False
    assert report["c1_v2_stable"]["stages"] == {"blending": 1}


def test_a_v1_divergence_below_the_limit_breaks_necessity() -> None:
    units = accepted_world()
    next(u for u in units if u["cell"] == "A" and u["variant"] == "v1" and u["status"]["scheduled"] == "diverged")["ste_kappa"] = [5.0, 9.0]
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c2_mechanism"]["falsification"]["sensitivity"] < 1.0 and report["c2_mechanism"]["pass"] is False


def test_replay_mismatch_fails_c3() -> None:
    units = accepted_world()
    next(u for u in units if u["variant"] == "v2")["replay_digest"]["static"] = "different"
    assert lv.evaluate_criteria(units, PLAN)["c3_replay"]["pass"] is False


def test_static_host_instability_is_reported_separately_and_does_not_hide_in_acceptance() -> None:
    units = accepted_world()
    next(u for u in units if u["cell"] == "A" and u["variant"] == "v1")["status"]["static"] = "diverged"
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c5_host_instability"]["static"]["A"]["diverged"] == 1
    assert report["c5_host_instability"]["present"] is True


def test_no_v1_divergence_makes_the_mechanism_untestable_not_passed() -> None:
    units = [unit(c, v, s) for c in ("A", "B", "C") for v in ("v1", "v2") for s in range(24)]
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c2_mechanism"]["pass"] is None and report["accepted"] is False


def test_a_pre_germination_divergence_is_host_instability_not_a_lifecycle_failure() -> None:
    units = accepted_world()
    target = next(u for u in units if u["cell"] == "A" and u["variant"] == "v2")
    target.update(
        status={"no_growth": "completed", "static": "completed", "scheduled": "diverged"},
        scheduled_divergence_stage="dormant",
        ste_kappa=[],
    )
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c1_v2_stable"]["pass"] is True
    assert report["c5_host_instability"]["scheduled_pre_germination"]["A"] == [target["seed"]]
    assert report["c5_host_instability"]["present"] is True


def test_a_germinated_divergence_without_an_ste_trace_is_a_sensitivity_miss() -> None:
    units = accepted_world()
    next(u for u in units if u["variant"] == "v1" and u["status"]["scheduled"] == "diverged")["ste_kappa"] = ["nan"]
    report = lv.evaluate_criteria(units, PLAN)["c2_mechanism"]
    assert report["falsification"]["sensitivity"] < 1.0 and report["pass"] is False
    assert report["nan_kappa_entries"] == 1 and len(report["unranked_units"]) == 1


def test_an_inf_kappa_counts_above_the_limit_with_infinite_amplification() -> None:
    assert lv.parse_kappa("inf") == math.inf and lv.parse_kappa("nan") is None
    assert lv.growth_score([1.0, math.inf], 0.05, 0.9) == math.inf


def test_a_v2_only_divergence_in_the_regression_cell_fails_c4() -> None:
    units = accepted_world()
    next(u for u in units if u["cell"] == "C" and u["variant"] == "v2").update(
        status={"no_growth": "completed", "static": "completed", "scheduled": "diverged"},
        scheduled_divergence_stage="training",
        late_ce={"no_growth": 1.2, "static": 1.1, "scheduled": None},
    )
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c4_regression_guard"]["pass"] is False and report["accepted"] is False
    assert report["c4_regression_guard"]["finite_pairs"] == 23


def test_performance_keeps_failure_rate_and_finite_performance_apart() -> None:
    table = lv.evaluate_criteria(accepted_world(), PLAN)["performance"]["A"]["v1"]
    scheduled = table["arms"]["scheduled"]
    assert (scheduled["n"], scheduled["diverged"], scheduled["finite_n"]) == (24, 6, 18)
    assert scheduled["divergence_rate"] == pytest.approx(0.25)
    assert table["finite_paired_contrasts"]["scheduled_minus_no_growth"]["excluded_pairs"] == 6


# --- the plan, the evidence boundary, launch and analysis ---

PLAN_PATH = runner.REPO / "docs" / "prereg" / "lifecycle-v2-validation.json"


def test_the_committed_plan_loads_and_covers_norm_conv_heavy_and_a_regression_cell() -> None:
    plan = lv.load_plan(PLAN_PATH)
    assert {(c["host"], c["seed_type"]) for c in plan["cells"].values()} == {
        ("under_normalized", "norm"),
        ("under_normalized", "conv_heavy"),
        ("mild", "conv_light"),
    }
    assert len(lv.jobs(plan)) == 3 * plan["units"]["count"]
    cfg = lv.expected_spec(plan, "A", "v2", lv.unit_seeds(plan)[0]).kernel_config()
    assert runner.c_star(cfg) == pytest.approx(
        2 * (1 + plan["criteria"]["momentum"]) / (plan["criteria"]["lr"] * (1 + 2 * plan["criteria"]["momentum"]))
    )


def _write(tmp_path: Path, plan: dict[str, Any]) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["criteria"].update(lr=0.1),  # c* would be computed from the wrong optimiser
        lambda p: p["config"].pop("trust_safety"),  # no silent RunSpec default
        lambda p: p["cells"]["A"].update(lifecycle="v2"),  # a cell cannot set the variant
        lambda p: p.update(variants=["v2"]),
        lambda p: p["criteria"].update(regression_cell="A"),
        lambda p: p["units"].update(first_seed=2101),  # reuses positive-control-v2 seeds
        lambda p: p["data_identity"].pop("fit_sha256"),
        lambda p: p.update(gated_by={"root": "x", "plan": "y", "reading": "z"}),
    ],
)
def test_plan_refusals(tmp_path: Path, mutate: Any) -> None:
    plan = json.loads(PLAN_PATH.read_text())
    mutate(plan)
    with pytest.raises(ValueError):
        lv.load_plan(_write(tmp_path, plan))


@pytest.fixture(scope="module")
def smoke_pair(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base = tmp_path_factory.mktemp("validation")
    runs = {}
    for variant in lv.VARIANTS:
        runs[variant] = base / variant
        runner.train(RunSpec(epochs=7, lifecycle=variant, seed_type="norm", host="under_normalized"), runs[variant])
    return runs


def test_unit_summary_reads_the_ste_trace_late_ce_and_replay_digests(smoke_pair: dict[str, Path]) -> None:
    spec = RunSpec(epochs=7)
    summaries = {}
    for variant, run in smoke_pair.items():
        runner.verify_run(run)
        summaries[variant] = lv.unit_summary(run, [4, 5, 6])
    steps = spec.train_size // spec.batch_size
    for summary in summaries.values():
        if summary["status"]["scheduled"] == "completed":
            assert len(summary["ste_kappa"]) == steps and summary["scheduled_divergence_stage"] is None
        for arm, status in summary["status"].items():
            assert (summary["late_ce"][arm] is None) == (status == "diverged")
    assert summaries["v1"]["replay_digest"] == summaries["v2"]["replay_digest"]


def test_unit_summary_takes_the_ste_trace_from_a_divergence_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from experiments import kernel_demo

    original = runner.ScaleAwareSlot.trust_region_loss
    calls = {"n": 0}

    def nan_on_second_step(self: Any, cfg: Any) -> Any:
        value = original(self, cfg)
        if self.stage is kernel_demo.Stage.TRAINING:
            calls["n"] += 1
            if calls["n"] == 2:
                return value * float("nan")
        return value

    monkeypatch.setattr(runner.ScaleAwareSlot, "trust_region_loss", nan_on_second_step)
    run = tmp_path / "run"
    runner.train(RunSpec(epochs=7), run)
    runner.verify_run(run)
    summary = lv.unit_summary(run, [4, 5, 6])
    assert summary["status"]["scheduled"] == "diverged" and summary["late_ce"]["scheduled"] is None
    assert summary["scheduled_divergence_stage"] == "training" and len(summary["ste_kappa"]) == 2
    assert summary["ste_rows_before_divergence"] == 1 and len(summary["ste_gain"]) == 2


def _small_plan(tmp_path: Path, device: str = "cuda") -> tuple[dict[str, Any], Path]:
    plan = json.loads(PLAN_PATH.read_text())
    plan["units"]["count"] = 3
    plan["config"]["device"] = device
    return plan, _write(tmp_path, plan)


def test_launch_runs_both_variants_of_a_seed_on_one_gpu_from_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan, path = _small_plan(tmp_path)
    snapshot = tmp_path / "fake-snapshot"
    snapshot.mkdir()
    monkeypatch.setattr(lv, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(lv, "make_snapshot", lambda dest: snapshot)
    monkeypatch.setattr(lv, "visible_gpus", lambda: [0, 1])
    monkeypatch.setattr(lv, "cifar_source_hashes", lambda root: plan["data_identity"]["source_files"])
    seen: list[dict[str, str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        seed = command[command.index("--seed") + 1]
        variant = command[command.index("--lifecycle") + 1]
        seen.append({"seed": seed, "variant": variant, "gpu": kwargs["env"]["CUDA_VISIBLE_DEVICES"], "cwd": str(kwargs["cwd"])})
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.lifecycle_validation.subprocess.run", fake_run)
    finished = lv.launch(tmp_path / "study", tmp_path, 2, path)
    assert len(seen) == len(finished["units"]) == 3 * 3 * 2
    assert {s["cwd"] for s in seen} == {str(snapshot)}
    for unit in finished["units"]:
        pair = [u for u in finished["units"] if (u["cell"], u["seed"]) == (unit["cell"], unit["seed"])]
        assert [u["variant"] for u in pair] == ["v1", "v2"] and len({u["gpu"] for u in pair}) == 1


def test_launch_refuses_a_data_root_without_the_pinned_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _plan, path = _small_plan(tmp_path)
    monkeypatch.setattr(lv, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(lv, "visible_gpus", lambda: [0, 1])
    monkeypatch.setattr(lv, "cifar_source_hashes", lambda root: {"data_batch_1": "0" * 64})
    with pytest.raises(RuntimeError, match="pinned"):
        lv.launch(tmp_path / "study", tmp_path, 2, path)


def _fake_study(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: tuple[tuple[str, int, str], ...] = ()
) -> tuple[Path, Path, dict[str, Any]]:
    plan, path = _small_plan(tmp_path)
    root = tmp_path / "study"
    root.mkdir()
    jobs = lv.jobs(plan)
    launch = {
        "prereg_sha256": file_hash(path),
        "analysis_module_sha256": lv.analysis_module_hash(),
        "git": {"commit": "x"},
        "jobs": [list(j) for j in jobs],
        "snapshot": str(runner.REPO),  # tests analyse from the checkout they run in
    }
    (root / "launch.json").write_text(json.dumps(launch))
    finished = [{"cell": c, "seed": s, "variant": v} for c, s in jobs for v in lv.VARIANTS]
    (root / "launch-finished.json").write_text(json.dumps({"units": finished}))
    monkeypatch.setattr(lv, "git_identity", lambda *a: {"commit": "x", "status": ""})

    def verify(run: Path) -> tuple[dict[str, Any], dict[str, Any], RunSpec]:
        variant, seed, cell = run.name, int(run.parent.name.split("-")[1]), run.parent.parent.name
        if (cell, seed, variant) in broken:
            raise RuntimeError("simulated unit crash")
        spec = lv.expected_spec(plan, cell, variant, seed)
        data = {k: plan["data_identity"][k] for k in ("source_files", "fit_sha256", "dev_sha256")}
        return {"spec": spec.__dict__, "data": data, "git": {"commit": "x"}}, {}, spec

    def summary(run: Path, late: list[int]) -> dict[str, Any]:
        variant, seed, cell = run.name, int(run.parent.name.split("-")[1]), run.parent.parent.name
        diverges = cell == "A" and variant == "v1" and seed == plan["units"]["first_seed"]
        u = unit(cell, variant, seed, sched_div=diverges, kappas=[40.0, 1e24] if diverges else [10.0])
        return {k: v for k, v in u.items() if k not in ("cell", "host", "variant", "seed")}

    monkeypatch.setattr(lv, "verify_run", verify)
    monkeypatch.setattr(lv, "unit_summary", summary)
    return root, path, plan


def test_analysis_publishes_once_with_a_reading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path, _plan = _fake_study(tmp_path, monkeypatch)
    report = lv.analyze(root, path)
    assert report["reading"] == "accepted" and report["n_units"] == 18
    assert json.loads((root / lv.REPORT).read_text())["reading"] == "accepted"
    with pytest.raises(FileExistsError):
        lv.analyze(root, path)


def test_a_failed_unit_beyond_the_allowance_is_instrument_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path, _plan = _fake_study(tmp_path, monkeypatch, broken=(("B", 4002, "v2"),))
    report = lv.analyze(root, path)
    assert report["reading"] == "instrument_failure" and report["failures"][0]["seed"] == 4002


def test_analysis_refuses_outside_the_snapshot_and_an_unfinished_fleet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path, _plan = _fake_study(tmp_path, monkeypatch)
    launch = json.loads((root / "launch.json").read_text())
    (root / "launch.json").write_text(json.dumps({**launch, "snapshot": str(tmp_path / "elsewhere")}))
    with pytest.raises(ValueError, match="snapshot"):
        lv.analyze(root, path)
    (root / "launch.json").write_text(json.dumps(launch))
    (root / "launch-finished.json").unlink()
    with pytest.raises(ValueError, match="not finished"):
        lv.analyze(root, path)


def test_a_unit_with_the_wrong_data_fails_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, path, _plan = _fake_study(tmp_path, monkeypatch)
    real_verify = lv.verify_run  # type: ignore[attr-defined]  # the fake installed by _fake_study

    def wrong_data(run: Path) -> Any:
        manifest, complete, spec = real_verify(run)
        if run.parent.name != "seed-4001" or run.parent.parent.name != "C" or run.name != "v2":
            return manifest, complete, spec
        return {**manifest, "data": {**manifest["data"], "fit_sha256": "0" * 64}}, complete, spec

    monkeypatch.setattr(lv, "verify_run", wrong_data)
    report = lv.analyze(root, path)
    assert report["reading"] == "instrument_failure" and len(report["failures"]) == 1
    assert "data identity" in report["failures"][0]["error"]


# --- pre-launch review amendments (statistics and theory reviews, 2026-10-08) ---


def _diverge(u: dict[str, Any], stage: str = "training", kappas: list[float] | None = None) -> None:
    trace = kappas if kappas is not None else u["ste_kappa"]
    u.update(
        status={**u["status"], "scheduled": "diverged"},
        scheduled_divergence_stage=stage,
        scheduled_divergence_epoch=2 if stage == "training" else 4,
        ste_kappa=trace,
        ste_rows_before_divergence=len(trace) - 1 if stage == "training" else None,
        late_ce={**u["late_ce"], "scheduled": None},
    )


def test_necessity_ignores_the_diverging_row_which_records_the_blow_up_itself() -> None:
    units = accepted_world()
    target = next(u for u in units if u["cell"] == "A" and u["variant"] == "v1" and u["status"]["scheduled"] == "diverged")
    target["ste_kappa"] = [10.0, 1e24]
    report = lv.evaluate_criteria(units, PLAN)["c2_mechanism"]
    assert report["falsification"]["sensitivity"] < 1.0 and report["pass"] is False
    assert report["falsification"]["positives_below_threshold"][0]["peak_over_c_star"] == pytest.approx(10.0 / report["c_star"])


def test_the_bilinear_allowance_keeps_a_near_limit_positive_while_the_strict_rate_is_reported() -> None:
    units = accepted_world()
    target = next(u for u in units if u["cell"] == "B" and u["variant"] == "v1" and u["status"]["scheduled"] == "diverged")
    target["ste_kappa"] = [26.0, 1e24]  # below c* = 27.14, above c*/1.1 = 24.68
    report = lv.evaluate_criteria(units, PLAN)["c2_mechanism"]
    assert report["falsification"]["sensitivity"] == 1.0 and report["pass"] is True
    assert report["falsification"]["sensitivity_strict_c_star"] == pytest.approx(11 / 12)


def test_a_post_ste_divergence_is_reported_with_its_host_flag_and_not_scored_as_mechanism() -> None:
    units = accepted_world()
    target = next(u for u in units if u["cell"] == "A" and u["variant"] == "v1" and u["seed"] == 20)
    _diverge(target, stage="blending", kappas=[5.0, 6.0])
    target["status"]["static"] = "diverged"
    report = lv.evaluate_criteria(units, PLAN)
    c2 = report["c2_mechanism"]
    assert c2["falsification"]["positives"] == 12 and c2["pass"] is True
    assert c2["post_ste_divergences"] == [{"cell": "A", "seed": 20, "stage": "blending", "epoch": 4, "host_coincident": True}]
    assert ["A", 20, "v1"] in report["c5_host_instability"]["host_coincident_lifecycle_divergences"]


def test_intervention_needs_a_seed_that_v1_loses_and_v2_keeps() -> None:
    units = accepted_world()
    for u in units:
        if u["variant"] == "v2" and u["cell"] in ("A", "B") and u["seed"] < 6:
            _diverge(u, stage="blending")
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c2_mechanism"]["intervention"]["v1_only"] == 0 and report["c2_mechanism"]["pass"] is False
    assert report["accepted"] is False


def test_ranking_never_gates_and_pools_pairs_only_within_a_cell() -> None:
    units = accepted_world()
    for u in units:
        if u["variant"] == "v1" and u["status"]["scheduled"] == "completed" and u["cell"] == "A":
            u["ste_kappa"] = [80.0, 90.0]  # survivors that grew more than the divergers
    report = lv.evaluate_criteria(units, PLAN)
    assert report["c2_mechanism"]["ranking"]["ranks_at_auc_min"] is False and report["c2_mechanism"]["pass"] is True
    assert report["accepted"] is True


def test_no_growth_must_replay_across_cells_that_share_a_host() -> None:
    units = accepted_world()
    next(u for u in units if u["cell"] == "B" and u["variant"] == "v1" and u["seed"] == 3)["replay_digest"]["no_growth"] = "x"
    report = lv.evaluate_criteria(units, PLAN)["c3_replay"]
    assert report["pass"] is False and ["under_normalized", "v1", 3] in report["cross_cell_mismatches"]


@pytest.mark.parametrize(("shift", "verdict"), [(0.0, "equivalent"), (0.2, "different"), (None, "inconclusive")])
def test_c4_separates_inconclusive_from_different(shift: float | None, verdict: str) -> None:
    units = accepted_world()
    c_v2 = sorted((u for u in units if u["cell"] == "C" and u["variant"] == "v2"), key=lambda u: u["seed"])
    for i, u in enumerate(c_v2):
        u["late_ce"]["scheduled"] = 1.0 + (shift if shift is not None else (0.3 if i % 2 else -0.3))
    report = lv.evaluate_criteria(units, PLAN)["c4_regression_guard"]
    assert report["verdict"] == verdict and report["pass"] is (verdict == "equivalent")


def test_per_cell_bounds_and_selection_split_are_reported() -> None:
    report = lv.evaluate_criteria(accepted_world(), PLAN)
    assert report["c1_v2_stable"]["per_cell"]["A"]["exact_bounds"]["upper_one_sided_95"] == pytest.approx(1 - 0.05 ** (1 / 24))
    assert report["c1_v2_stable"]["v1_codivergence_seeds"] == list(range(6))
    split = report["performance"]["A"]["v1"]["static_minus_no_growth_by_scheduled_outcome"]
    assert (split["scheduled_completed"]["n"], split["scheduled_diverged"]["n"]) == (18, 6)


def _synthetic_run(tmp_path: Path, step: int, rows: int) -> Path:
    run = tmp_path / f"run-{step}"
    run.mkdir()
    status = {"no_growth": "completed", "static": "completed", "scheduled": "diverged"}
    (run / "complete.json").write_text(json.dumps({"arm_status": status}))
    table = {"kappa_live": [30.0] * rows, "lam_t": [1.0] * rows, "gain": [0.02] * rows, "clamped": [False] * rows}
    records: list[dict[str, Any]] = [
        {"arm": arm, "kind": "epoch", "epoch": e, "dev": {"ce": 1.0}, "witness": {"seed_present": False}}
        for arm in ("no_growth", "static")
        for e in range(4)
    ]
    records.append(
        {
            "arm": "scheduled",
            "kind": "diverged",
            "epoch": 2,
            "step": step,
            "stage": "blending",
            "witness": {"seed_present": True, "ste": table},
        }
    )
    (run / "training.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return run


def test_unit_summary_counts_rows_before_an_in_step_or_a_scoring_divergence(tmp_path: Path) -> None:
    in_step = lv.unit_summary(_synthetic_run(tmp_path, step=5, rows=6), [3])
    scoring = lv.unit_summary(_synthetic_run(tmp_path, step=128, rows=128), [3])
    assert in_step["ste_rows_before_divergence"] == 5  # row 5 is the diverging step
    assert scoring["ste_rows_before_divergence"] == 128  # every training step preceded the scoring failure
    assert scoring["scheduled_divergence_epoch"] == 2 and scoring["late_ce"]["scheduled"] is None
