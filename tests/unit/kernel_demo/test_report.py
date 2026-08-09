import json
from pathlib import Path

import pytest

from experiments.kernel_demo import (
    Config,
    FanRecord,
    Store,
    config_hash,
    env_block,
    make_fan_record,
    run_replay,
    run_report,
)


def _eval_fan(episode_seed: int, manifest_hash: str, cfg_hash: str = "c", env: dict[str, object] | None = None) -> FanRecord:
    arms: list[dict[str, object]] = [
        {"name": n, "status": "ok", "r_val": 0.5, "r_test": 0.5, "rms_ratio_blend_entry": 0.05}
        for n in ("norm", "attn", "conv_light", "conv_heavy")
    ]
    arms.append({"name": "noop", "status": "ok", "r_val": 0.45, "r_test": 0.45, "rms_ratio_blend_entry": None})
    return make_fan_record(
        kind="fan",
        episode_seed=episode_seed,
        seed_namespace="eval",
        split_role="eval",
        pathology_id="mild",
        fan_epoch=6,
        refan_k=None,
        schedule_id="s",
        policy_checkpoint_id=None,
        iteration=None,
        config_hash=cfg_hash,
        frozen_block_hash="f",
        manifest_hash=manifest_hash,
        common_future_hash="h",
        host_init_hash="i",
        env=env or {},
        arms=arms,
        telemetry=[],
        decisions=None,
        gate_results=None,
    )


def _results_fixture(manifest_hash: str = "m") -> dict[str, object]:
    return {
        "manifest_hash": manifest_hash,
        "lift": {
            "trained_mean": 0.05,
            "trained_p": 0.01,
            "paired_vs_schedule_only_p": 0.02,
            "per_comparator": {
                c: {"mean_lift": 0.03, "germination_rate": 0.7} for c in ("trained", "random", "schedule_only", "fixed_epoch")
            },
        },
        "agreement": {"teacher_forced": 0.6, "majority_null": 0.3, "schedule_only_null": 0.35},
        "money_chart": {"matched": 4, "p": 0.01},
        "falsifier": {"deranged_agreement": 0.3, "null_ci_hi": 0.45, "derangement": {}},
        "ceiling": {"estimate": 0.8, "wilson_ci": [0.6, 0.9], "pairs": 30, "label": "lower bound, test units"},
        "when_contrast": {"unrestricted_mean": 0.02, "restricted_mean": 0.04, "germination_rate": 0.7},
        "restraint_regret": {"last_grid_point_mean": 0.01, "per_point": [0.01]},
        "chosen_seed_marginal": {"norm": 10},
        "per_grid_point": [{"p": 0.6, "A": 0.05}, {"p": 0.4, "A": -0.01}],
        "power_note": {"mde_lift_at_n_eval": 0.05, "mde_agreement_at_grid": 0.08, "density_source": "manifest"},
        "verdict": {"lift_positive": True},
    }


def _report_store(tmp_path: Path, manifest_hashes: list[str]) -> None:
    s = Store(tmp_path)
    for i, mh in enumerate(manifest_hashes):
        s.append(0, _eval_fan(100 + i, mh))
    s.close()
    (tmp_path / "eval_results.json").write_text(json.dumps(_results_fixture()))
    (tmp_path / "frozen.json").write_text(
        json.dumps(
            {
                "manifest_hash": "m",
                "beta_which": 0.01,
                "beta_now": 0.036,
                "det_mode_cost": {"slowdown": 1.2},
                "concurrency_factor": 1.5,
                "fan_density": {"best_minus_second": 0.05, "best_minus_noop": 0.08},
            }
        )
    )
    pol = tmp_path / "policies"
    pol.mkdir(exist_ok=True)
    (pol / "trained.json").write_text(json.dumps({"checkpoint_id": "abc", "curve": [1.0, 0.9]}))


def test_report_renders_on_fixture(tmp_path):
    _report_store(tmp_path, ["m", "m"])
    rep = run_report(Config(), str(tmp_path))
    for key in ("lift_table", "agreement", "money_chart", "diverged_observed", "per_seed_failure_rates", "realized_p_by_sign"):
        assert key in rep, key


def test_report_refuses_mixed_manifest(tmp_path):
    _report_store(tmp_path, ["m1", "m2"])
    with pytest.raises(RuntimeError, match="mixed manifest_hash"):
        run_report(Config(), str(tmp_path))


def test_replay_refuses_doctored_env(tmp_path):
    doctored = env_block("cpu", 1)
    doctored["torch_version"] = "0.0.doctored"
    rec = _eval_fan(7, "m", cfg_hash=config_hash(), env=doctored)
    s = Store(tmp_path)
    s.append(0, rec)
    s.close()
    with pytest.raises(RuntimeError, match="env"):
        run_replay(Config(), rec.fan_id, str(tmp_path), "cpu")


def test_replay_refuses_doctored_config_hash(tmp_path):
    rec = _eval_fan(7, "m", cfg_hash="doctored", env=env_block("cpu", 1))
    s = Store(tmp_path)
    s.append(0, rec)
    s.close()
    with pytest.raises(RuntimeError, match="config_hash"):
        run_replay(Config(), rec.fan_id, str(tmp_path), "cpu")
