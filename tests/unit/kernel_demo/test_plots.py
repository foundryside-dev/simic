"""Reporting-discipline tests for the plotting sidecar.

The sidecar's job is to refuse to invent data. These cover the four ways it
could fabricate a research artefact: a missing field read as zero, an absent
measurement drawn at the origin, an epoch axis silently relabelled, and a
mistyped store path creating an empty store and reporting success.
"""

import json
from pathlib import Path

import pytest

from experiments.kernel_demo import SEED_NAMES, FanRecord, Store, make_fan_record
from experiments.kernel_demo_plots import (
    MAX_ALPHA_BETA_ARMS,
    PlotDataError,
    _load_fans,
    main,
    plot_alpha_beta,
    plot_example_arm_curves,
    plot_money_chart_trio,
    plot_rms_blend_entry,
)


def _rec(
    episode_seed: int = 1,
    *,
    arms: list[dict[str, object]] | None = None,
    seed_namespace: str = "eval",
    split_role: str = "eval",
    manifest_hash: str | None = "m0",
    pathology_id: str = "mild",
) -> FanRecord:
    return make_fan_record(
        kind="fan",
        episode_seed=episode_seed,
        seed_namespace=seed_namespace,
        split_role=split_role,
        pathology_id=pathology_id,
        fan_epoch=5,
        refan_k=None,
        schedule_id="s",
        policy_checkpoint_id=None,
        iteration=None,
        config_hash="c",
        frozen_block_hash="f",
        manifest_hash=manifest_hash,
        common_future_hash="h",
        host_init_hash="i",
        env={},
        arms=arms if arms is not None else [{"name": "noop", "status": "ok", "r_val": 0.4}],
        telemetry=[],
        decisions=None,
        gate_results=None,
    )


def _results() -> dict[str, object]:
    return {
        "money_chart": {"matched": 3, "p": 0.01},
        "agreement": {"teacher_forced": 0.7, "majority_null": 0.4, "schedule_only_null": 0.3},
        "falsifier": {"deranged_agreement": 0.35, "null_ci_hi": 0.5},
    }


def test_nonexistent_store_fails_without_creating_it(tmp_path: Path) -> None:
    # Store.__init__ mkdirs shards/, so the existence check must run BEFORE
    # it — otherwise a typo'd --store yields blank plots and a success line.
    missing = tmp_path / "kerne_demo"
    with pytest.raises(PlotDataError, match="store does not exist"):
        _load_fans(str(missing), namespace=None, split_role=None, include_refans=False, manifest_hash=None)
    assert not missing.exists()


def test_main_without_any_input_is_an_argparse_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--out", str(tmp_path / "plots")])
    assert not (tmp_path / "plots").exists()  # validation precedes the mkdir


def test_missing_agreement_field_raises_rather_than_plotting_zero(tmp_path: Path) -> None:
    results = _results()
    agreement = results["agreement"]
    assert isinstance(agreement, dict)
    del agreement["teacher_forced"]
    with pytest.raises(PlotDataError, match="agreement: missing required field 'teacher_forced'"):
        plot_money_chart_trio(results, tmp_path)


def test_null_p_is_refused_not_formatted(tmp_path: Path) -> None:
    results = _results()
    results["money_chart"] = {"matched": 3, "p": None}
    with pytest.raises(PlotDataError, match="expected number"):
        plot_money_chart_trio(results, tmp_path)


def test_alpha_beta_bound_holds_across_many_records(tmp_path: Path) -> None:
    # The old bound only checked BETWEEN records, so a record carrying five
    # logged arms drew five. Twenty such records must still yield four.
    arms: list[dict[str, object]] = [
        {"name": n, "status": "ok", "alpha_beta_log": [[0.1, 0.2], [0.3, 0.4]]} for n in (*SEED_NAMES, "nullseed")
    ]
    fans = [_rec(i, arms=arms) for i in range(1, 21)]
    identities = plot_alpha_beta(fans, tmp_path)
    assert len(identities) == MAX_ALPHA_BETA_ARMS
    assert len(set(identities)) == MAX_ALPHA_BETA_ARMS  # labels disambiguate


def test_seed_without_rms_measurement_is_labelled_not_zeroed(tmp_path: Path) -> None:
    arms: list[dict[str, object]] = [{"name": SEED_NAMES[0], "status": "ok", "rms_ratio_blend_entry": 0.3}]
    arms += [{"name": n, "status": "diverged", "rms_ratio_blend_entry": None} for n in SEED_NAMES[1:]]
    missing = plot_rms_blend_entry([_rec(1, arms=arms)], tmp_path)
    assert missing == list(SEED_NAMES[1:])
    assert (tmp_path / "rms_blend_entry.png").exists()


def test_no_rms_measurements_at_all_raises(tmp_path: Path) -> None:
    arms: list[dict[str, object]] = [{"name": n, "rms_ratio_blend_entry": None} for n in SEED_NAMES]
    with pytest.raises(PlotDataError, match="no RMS blend-entry measurements"):
        plot_rms_blend_entry([_rec(1, arms=arms)], tmp_path)


def test_curve_with_null_middle_keeps_its_epoch_positions(tmp_path: Path) -> None:
    # _sanitize_json writes non-finite as null; [0.30, null, 0.34] must plot
    # at x = 0, 2 — not compressed onto 0, 1.
    from experiments.kernel_demo_plots import _finite_points, _gapped

    xs, ys = _gapped(_finite_points([0.30, None, 0.34], "t"))
    assert xs == [0, 1, 2]
    assert ys[0] == 0.30 and ys[2] == 0.34
    assert ys[1] != ys[1]  # nan — a visible gap, not an interpolated point

    arms: list[dict[str, object]] = [{"name": "noop", "status": "ok", "curve_val": [0.30, None, 0.34]}]
    plot_example_arm_curves([_rec(1, arms=arms)], tmp_path)
    assert (tmp_path / "example_arm_curves.png").exists()


def test_spike_then_crash_uses_the_kernel_end_state_definition() -> None:
    from experiments.kernel_demo_plots import _finite_points, _spike_then_crash

    # A curve on which the two definitions DISAGREE, which is the whole point:
    # final point 0.50, so peak 0.52 clears it by 0.02 (< margin) and the old
    # final-point rule would say "no crash". end_state_R = mean(0.40, 0.40,
    # 0.50) = 0.4333, which the peak clears by 0.087 (> margin).
    assert _spike_then_crash(_finite_points([0.30, 0.52, 0.40, 0.40, 0.50], "t"))
    flat = _finite_points([0.40, 0.42, 0.44], "t")
    assert not _spike_then_crash(flat)
    assert not _spike_then_crash(_finite_points([0.4, 0.5], "t"))  # < 3 entries: guarded, not raised


def test_mixed_manifest_hashes_are_refused_unless_selected(tmp_path: Path) -> None:
    store = Store(str(tmp_path / "store"))
    store.append(0, _rec(1, manifest_hash="m0"))
    store.append(0, _rec(2, manifest_hash="m1"))
    with pytest.raises(PlotDataError, match="several manifest generations"):
        _load_fans(str(tmp_path / "store"), namespace=None, split_role=None, include_refans=False, manifest_hash=None)
    picked = _load_fans(str(tmp_path / "store"), namespace=None, split_role=None, include_refans=False, manifest_hash="m0")
    assert [r.manifest_hash for r in picked] == ["m0"]


def test_mixed_namespaces_are_refused_unless_selected(tmp_path: Path) -> None:
    store = Store(str(tmp_path / "store"))
    store.append(0, _rec(1, seed_namespace="preflight", split_role="preflight"))
    store.append(0, _rec(2))
    with pytest.raises(PlotDataError, match="several seed namespaces"):
        _load_fans(str(tmp_path / "store"), namespace=None, split_role=None, include_refans=False, manifest_hash=None)
    picked = _load_fans(str(tmp_path / "store"), namespace="eval", split_role=None, include_refans=False, manifest_hash=None)
    assert [r.seed_namespace for r in picked] == ["eval"]


def test_plot_manifest_records_the_selected_population(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store = Store(str(store_root))
    arms: list[dict[str, object]] = [
        {"name": n, "status": "ok", "curve_val": [0.3, 0.4, 0.5], "rms_ratio_blend_entry": 0.2, "alpha_beta_log": [[0.1, 0.2]]}
        for n in SEED_NAMES
    ]
    store.append(0, _rec(1, arms=arms))
    out = tmp_path / "plots"
    main(["--store", str(store_root), "--results", str(_write_results(tmp_path)), "--out", str(out)])
    manifest = json.loads((out / "plot_manifest.json").read_text(encoding="utf-8"))
    assert manifest["record_count"] == 1
    assert manifest["manifest_hashes_present"] == ["m0"]
    assert list(manifest["example_arm_curve_fan_ids"]) == ["mild"]
    assert "money_chart_trio.png" in manifest["written"]


def _write_results(tmp_path: Path) -> Path:
    p = tmp_path / "eval_results.json"
    p.write_text(json.dumps(_results()), encoding="utf-8")
    return p
