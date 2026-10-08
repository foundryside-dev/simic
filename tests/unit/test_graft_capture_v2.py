"""Graft-capture v2 support in the screen: per-contrast divergence, a graft-failure gate, pinned data.

Design: PDR-0052. Lifecycle v2 removed the graft's divergence (PDR-0051), but the static
`norm` arm still diverges on this host (simic-9c5c3a2acf). A static failure must not take
the graft - no growth pair with it, and a graft failure must be counted, never dropped.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from experiments import bounded_screen as screen
from experiments.bounded_data import RunSpec
from tests.unit.test_bounded_screen import BASE_PLAN, fake_screen, unit_values, write_plan

GC2_PLAN: dict[str, Any] = copy.deepcopy(BASE_PLAN)
GC2_PLAN["decision"] = {
    "delta_nats": 0.05,
    "max_failed_units": 0,
    "reading_rule": "graft-capture-v2",
    "diverged_arm_policy": "per_contrast",
    "max_graft_failures": 1,
    "max_static_failures": 2,
}


def capture_values(n: int = 20) -> dict[int, dict[str, float]]:
    """About 40% capture: the graft beats no growth by 0.06, static by 0.15."""
    return unit_values(-0.06, static_shift=-0.15, static_sd=0.01, n=n)


def test_per_contrast_keeps_the_no_growth_pair_when_static_diverges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN, diverged={3: "static"})
    report = screen.analyze(root, plan)
    assert report["failures"] == []
    assert report["contrasts"]["scheduled_minus_no_growth"]["n_pairs"] == 20
    assert report["contrasts"]["scheduled_minus_static"]["n_pairs"] == 19
    assert report["contrasts"]["scheduled_minus_static"]["lost_pairs"] == [3]
    assert report["diverged_units_by_arm"]["static"] == 1
    assert report["reading"] == "partial_capture"


def test_the_same_divergence_still_fails_the_unit_under_fail_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = copy.deepcopy(GC2_PLAN)
    plan["decision"].update(diverged_arm_policy="fail_unit", reading_rule="graft-capture-v1", max_failed_units=1)
    for key in ("max_graft_failures", "max_static_failures"):
        del plan["decision"][key]
    root, path = fake_screen(tmp_path, monkeypatch, capture_values(), plan=plan, diverged={3: "static"})
    report = screen.analyze(root, path)
    assert [f["seed"] for f in report["failures"]] == [3]


def test_graft_failures_beyond_the_cap_read_graft_unstable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN, diverged={2: "scheduled", 5: "scheduled"})
    report = screen.analyze(root, plan)
    assert report["reading"] == "graft_unstable"
    assert report["diverged_units_by_arm"]["scheduled"] == 2
    assert report["arm_divergence_bounds"]["scheduled"]["upper_one_sided_95"] > 2 / 20


def test_graft_failures_within_the_cap_are_counted_and_read_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN, diverged={2: "scheduled"})
    report = screen.analyze(root, plan)
    assert report["reading"] == "partial_capture"
    assert report["contrasts"]["scheduled_minus_no_growth"]["n_pairs"] == 19


def test_static_failures_beyond_the_cap_make_the_static_comparison_not_credible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    diverged = dict.fromkeys((1, 2, 3), "static")
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN, diverged=diverged)
    assert screen.analyze(root, plan)["reading"] == "reopen_static_not_credible"


def test_lost_pairs_get_a_declared_imputation_sensitivity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN, diverged={3: "static"})
    sensitivity = screen.analyze(root, plan)["sensitivity"]
    assert sensitivity["lost_pairs"] == {"scheduled_minus_static": 1}
    assert set(sensitivity["readings"]) == {"impute_favour_first", "impute_favour_second"}
    assert sensitivity["robust"] is True


def test_capture_fraction_is_described_with_a_bootstrap_interval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, plan = fake_screen(tmp_path, monkeypatch, capture_values(), plan=GC2_PLAN)
    capture = screen.analyze(root, plan)["capture_fraction"]
    assert capture["n"] == 20 and capture["estimate"] == pytest.approx(0.4, abs=0.05)
    assert capture["bootstrap_interval"]["lower"] < capture["estimate"] < capture["bootstrap_interval"]["upper"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(diverged_arm_policy="fail_unit"),  # the v2 rule reads per-contrast evidence
        lambda d: d.pop("max_graft_failures"),
        lambda d: d.update(max_static_failures=-1),
    ],
)
def test_the_v2_rule_requires_its_policy_and_caps(tmp_path: Path, mutate: Any) -> None:
    plan = copy.deepcopy(GC2_PLAN)
    mutate(plan["decision"])
    with pytest.raises(ValueError):
        screen.load_plan(write_plan(tmp_path, plan))


DATA_IDENTITY = {"source_files": {"data_batch_1": "a" * 64}, "fit_sha256": "f" * 64, "dev_sha256": "d" * 64}


def test_a_pinned_data_identity_must_be_complete(tmp_path: Path) -> None:
    plan = copy.deepcopy(GC2_PLAN)
    plan["data_identity"] = {"fit_sha256": "f" * 64}
    with pytest.raises(ValueError, match="data_identity"):
        screen.load_plan(write_plan(tmp_path, plan))


def test_a_unit_with_unpinned_data_fails_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = copy.deepcopy(GC2_PLAN)
    plan["data_identity"] = DATA_IDENTITY
    root, path = fake_screen(tmp_path, monkeypatch, capture_values(), plan=plan)
    real_verify = screen.verify_run  # type: ignore[attr-defined]  # the fake installed by fake_screen

    def with_sources(unit: Path) -> tuple[dict[str, Any], dict[str, Any], RunSpec]:
        manifest, complete, spec = real_verify(unit)
        data = {**manifest["data"], "source_files": DATA_IDENTITY["source_files"]}
        if unit.name == "seed-4":
            data["fit_sha256"] = "0" * 64
        return {**manifest, "data": data}, complete, spec

    monkeypatch.setattr(screen, "verify_run", with_sources)
    report = screen.analyze(root, path)
    assert [f["seed"] for f in report["failures"]] == [4] and "pinned data" in report["failures"][0]["error"]
    assert report["reading"] == "instrument_failure"


def test_launch_refuses_a_data_root_that_differs_from_the_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = copy.deepcopy(GC2_PLAN)
    plan["data_identity"] = DATA_IDENTITY
    monkeypatch.setattr(screen, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "cifar_source_hashes", lambda root: {"data_batch_1": "b" * 64})
    with pytest.raises(RuntimeError, match="pinned"):
        screen.launch(tmp_path / "screen", tmp_path, 1, write_plan(tmp_path, plan))


def test_the_committed_sibling_plans_load_share_seeds_and_pin_the_validated_data() -> None:
    from experiments import lifecycle_validation as lv

    plans = {n: screen.load_plan(Path(f"docs/prereg/graft-capture-v2-{n}.json")) for n in ("norm", "conv-heavy")}
    assert screen.unit_seeds(plans["norm"]) == screen.unit_seeds(plans["conv-heavy"]) == list(range(7001, 7097))
    assert {p["config"]["seed_type"] for p in plans.values()} == {"norm", "conv_heavy"}
    validated = lv.load_plan(Path("docs/prereg/lifecycle-v2-validation.json"))
    for name, plan in plans.items():
        assert plan["config"]["lifecycle"] == "v2" and plan["config"]["device"] == "cuda"
        assert plan["data_identity"] == validated["data_identity"]
        assert plan["analysis"]["family_alpha"] == 0.025  # one family of four co-primaries across both plans
        assert set(screen.unit_seeds(plan)).isdisjoint(set(range(4001, 4025)) | {9207, 9208, 9209})
        other = "conv-heavy" if name == "norm" else "norm"
        assert plan["linked_plans"] == [f"docs/prereg/graft-capture-v2-{other}.json"]
