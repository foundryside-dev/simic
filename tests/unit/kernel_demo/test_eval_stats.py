import json

import pytest

from experiments.kernel_demo import (
    PATHOLOGIES,
    Config,
    class_derangement,
    config_hash,
    fan_identity,
    frozen_block_hash,
    make_fan_record,
    run_eval,
    verdict,
    when_contrast,
    wilson_interval,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle


def test_wilson_interval_known_value():
    lo, hi = wilson_interval(8, 10, 0.05)
    assert abs(lo - 0.4902) < 1e-3
    assert abs(hi - 0.9433) < 1e-3


def test_derangement_never_maps_a_class_to_itself():
    classes = list(PATHOLOGIES)
    for seed in range(20):
        m = class_derangement(classes, seed)
        assert set(m) == set(classes)
        assert sorted(m.values()) == sorted(classes)  # a permutation
        assert all(m[c] != c for c in classes)  # deranged


def test_when_contrast_six_episode_fixture_with_two_never_germinates():
    eps: list[dict[str, object]] = [
        {"germinated": True, "lift": 0.1},
        {"germinated": True, "lift": 0.2},
        {"germinated": True, "lift": 0.3},
        {"germinated": True, "lift": 0.4},
        {"germinated": False, "lift": 0.0},  # never-germinate = 0
        {"germinated": False, "lift": 0.0},
    ]
    out = when_contrast(eps)
    rm, um, gr = out["restricted_mean"], out["unrestricted_mean"], out["germination_rate"]
    assert rm is not None and um is not None and gr is not None
    assert abs(rm - 0.25) < 1e-12
    assert abs(um - 1.0 / 6) < 1e-12
    assert abs(gr - 4 / 6) < 1e-12


def test_when_contrast_no_germination_restricted_mean_is_none():
    # A conditional mean over zero acted episodes is undefined — None, never
    # a silent 0.0 (the silent-zero scar class).
    out = when_contrast([{"germinated": False, "lift": -0.05}, {"germinated": False, "lift": 0.03}])
    assert out["restricted_mean"] is None
    assert out["germination_rate"] == 0.0


def _results(all_pass: bool = True) -> dict[str, object]:
    return {
        "lift": {
            "trained_mean": 0.05 if all_pass else -0.01,
            "trained_p": 0.01 if all_pass else 0.3,
            "paired_vs_schedule_only_p": 0.02,
        },
        "agreement": {"teacher_forced": 0.6, "majority_null": 0.3},
        "money_chart": {"matched": 4, "p": 0.01},
        "falsifier": {"deranged_agreement": 0.3, "null_ci_hi": 0.45},
    }


def test_verdict_all_pass_and_lift_fail():
    v = verdict(_results(True), Config())
    assert set(v) == {"lift_positive", "beats_schedule_only", "agreement_beats_null", "money_chart", "falsifier_collapses"}
    assert all(v.values())
    v2 = verdict(_results(False), Config())
    assert not v2["lift_positive"]
    assert v2["money_chart"]  # the other booleans are independent


def test_eval_one_shot_refusal(tmp_path):
    (tmp_path / "eval_results.json").write_text("{}")
    with pytest.raises(RuntimeError, match="one-shot"):
        run_eval(Config(), make_tiny_bundle(), "cpu", str(tmp_path))


def test_eval_incomplete_collection_refusal(tmp_path):
    (tmp_path / "frozen.json").write_text(
        json.dumps(
            {
                "frozen_block_hash": frozen_block_hash(Config()),
                "config_hash": config_hash(),
                "manifest_hash": "m",
                "normalizer": {"medians": [0.0] * 20, "iqrs": [1.0] * 20},
            }
        )
    )
    with pytest.raises(RuntimeError, match="incomplete collection"):
        run_eval(Config(), make_tiny_bundle(), "cpu", str(tmp_path))


def test_resume_identity_matches_stored_fan_id():
    # The resume skip-set is keyed on fan_identity — this equality IS the
    # crash-resume-without-double-counting mechanism.
    rec = make_fan_record(
        kind="policy_run",
        episode_seed=7,
        seed_namespace="eval",
        split_role="eval",
        pathology_id="mild",
        fan_epoch=None,
        refan_k=None,
        schedule_id="s",
        policy_checkpoint_id="trained:abc",
        iteration=None,
        config_hash="c",
        frozen_block_hash="f",
        manifest_hash="m",
        common_future_hash="h",
        host_init_hash="i",
        env={},
        arms=[],
        telemetry=[],
        decisions=[],
        gate_results=None,
    )
    assert rec.fan_id == fan_identity(7, None, "policy_run", None, "trained:abc", None)
