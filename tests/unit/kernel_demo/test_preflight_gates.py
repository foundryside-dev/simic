import json

import pytest

import experiments.kernel_demo as kd
from experiments.kernel_demo import (
    DESIGNED_WINNER,
    PATHOLOGIES,
    SEED_NAMES,
    Config,
    FanRecord,
    Normalizer,
    dataclass_gates_ok,
    draw_schedule,
    freeze_manifest,
    gate1_noop_sanity,
    gate2_signal,
    gate3_contrast,
    gate4_dominance,
    gate5_magnitude,
    gate6_horizon,
    gate7_now_vs_later,
    make_fan_record,
    measure_fan_density,
)

CFG = Config()


def _tele_cue(epoch: int, path_idx: int) -> dict[str, object]:
    gnm = [0.1, 0.1, 0.1]
    std = 0.1
    if path_idx < 3:
        gnm[path_idx] = 3.0
    else:
        std = 3.0
    return {
        "epoch": epoch,
        "train_loss": 1.0,
        "val_loss": 1.0,
        "val_acc": 0.5,
        "train_loss_delta": 0.0,
        "val_loss_delta": 0.0,
        "grad_norm_mean": gnm,
        "grad_norm_var": [0.1, 0.1, 0.1],
        "act_saturation": [0.3, 0.3, 0.3],
        "weight_norm": [1.0, 1.0, 1.0],
        "per_class_val_acc_std": std,
        "confusion_entropy": 2.0,
    }


def _flat_tele(epoch: int) -> dict[str, object]:
    d = _tele_cue(epoch, 0)
    d["grad_norm_mean"] = [0.1, 0.1, 0.1]
    d["per_class_val_acc_std"] = 0.1
    return d


def _fan(
    episode_seed: int,
    pathology: str,
    winner: str | None,
    fan_epoch: int = 6,
    kind: str = "fan",
    refan_k: int | None = None,
    noop_r: float = 0.45,
    win_r: float = 0.7,
    other_r: float = 0.5,
    rms: dict[str, float] | None = None,
    diverged: bool = False,
    cue: bool = True,
) -> FanRecord:
    arms: list[dict[str, object]] = []
    for name in SEED_NAMES:
        r = win_r if name == winner else other_r
        arms.append(
            {
                "name": name,
                "status": "diverged" if diverged else "ok",
                "r_val": 0.10 if diverged else r,
                "r_test": None,
                "rms_ratio_blend_entry": (rms or {}).get(name, 0.05),
            }
        )
    arms.append(
        {
            "name": "noop",
            "status": "diverged" if diverged else "ok",
            "r_val": 0.10 if diverged else noop_r,
            "r_test": None,
            "rms_ratio_blend_entry": None,
        }
    )
    p_idx = PATHOLOGIES.index(pathology)
    return make_fan_record(
        kind=kind,
        episode_seed=episode_seed,
        seed_namespace="preflight",
        split_role="preflight",
        pathology_id=pathology,
        fan_epoch=fan_epoch,
        refan_k=refan_k,
        schedule_id="s",
        policy_checkpoint_id=None,
        iteration=None,
        config_hash="c",
        frozen_block_hash="f",
        manifest_hash=None,
        common_future_hash="h",
        host_init_hash="i",
        env={},
        arms=arms,
        telemetry=[_tele_cue(e, p_idx) if cue else _flat_tele(e) for e in range(4)],
        decisions=None,
        gate_results=None,
    )


def _balanced_fixture(n_per_path: int = 5, mild_noop_wins: int = 3) -> list[FanRecord]:
    recs = []
    es = 0
    for path in PATHOLOGIES:
        for j in range(n_per_path):
            es += 1
            if path == "mild" and j < mild_noop_wins:
                recs.append(_fan(es, path, winner=None, noop_r=0.8))  # no-op wins the 5-arm argmax
            else:
                recs.append(_fan(es, path, winner=DESIGNED_WINNER[path]))
    return recs


def test_draw_schedule_two_ordered_in_window():
    for seed in range(50):
        a, b = draw_schedule(seed, CFG)
        lo, hi = CFG.window
        assert lo <= a < b <= hi  # ordered, distinct, inclusive window


def test_gate1_pass_and_fail():
    assert gate1_noop_sanity(_balanced_fixture(), CFG).ok
    zero_wins = [_fan(i, "mild", winner="conv_light") for i in range(1, 6)]
    res = gate1_noop_sanity(zero_wins, CFG)
    assert not res.ok


def test_gate1_all_diverged_is_measured_not_exception():
    recs = [_fan(i, "mild", winner=None, diverged=True) for i in range(1, 6)]
    res = gate1_noop_sanity(recs, CFG)
    assert not res.ok
    assert res.reason == "all arms diverged"


def test_gate2_pass_and_fail():
    ok = gate2_signal(_balanced_fixture(), CFG)
    assert ok.ok, ok.reason
    flat = [_fan(i, PATHOLOGIES[i % 4], winner=DESIGNED_WINNER[PATHOLOGIES[i % 4]], cue=False) for i in range(1, 21)]
    assert not gate2_signal(flat, CFG).ok


def test_gate3_pass_and_fail():
    # The floor is the PAIRED per-arm |R^fan - R^refan| noise at the same
    # (episode, epoch) — not the density statistic computed on refans, which
    # has the same expectation as the fan density itself.
    fans = _balanced_fixture()
    # es 1..5 are under_normalized (winner norm); paired refans move every arm
    # by 0.005 -> tiny noise floor, fan contrast clears 2x it.
    quiet_refans = [
        _fan(i, "under_normalized", winner="norm", kind="refan", refan_k=0, win_r=0.705, other_r=0.505, noop_r=0.455) for i in range(1, 6)
    ]
    assert gate3_contrast(fans, quiet_refans, CFG).ok
    # Flat fans against noisy refans: contrast 0.01 vs noise ~0.058 -> fail.
    flat_fans = [_fan(i, "mild", winner="norm", win_r=0.51, other_r=0.5, noop_r=0.5) for i in range(1, 11)]
    noisy_refans = [_fan(i, "mild", winner="norm", kind="refan", refan_k=0, win_r=0.60, other_r=0.45, noop_r=0.55) for i in range(1, 6)]
    assert not gate3_contrast(flat_fans, noisy_refans, CFG).ok


def test_gate3_unpaired_refans_is_loud_failure():
    fans = _balanced_fixture()
    unpaired = [_fan(100 + i, "mild", winner="norm", kind="refan", refan_k=0) for i in range(3)]
    res = gate3_contrast(fans, unpaired, CFG)
    assert not res.ok
    assert res.reason is not None and "paired" in res.reason


def test_run_refan_base_divergence_voids_not_crashes(tmp_path, monkeypatch):
    import dataclasses as dc

    from experiments.kernel_demo import Store, run_refan
    from tests.unit.kernel_demo.conftest import make_tiny_bundle

    tiny = dc.replace(CFG, horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3))
    real = kd.build_record

    def bomb(*a, **kw):
        rec = real(*a, **kw)
        if rec.epoch == 1:
            raise kd.TelemetryDivergence("injected")
        return rec

    monkeypatch.setattr(kd, "build_record", bomb)
    store = Store(tmp_path, fsync_every=1)
    run_refan(tiny, make_tiny_bundle(), "cpu", 77, 3, 0, store, 0)  # base diverges at epoch 1 < fan_epoch 3
    store.close()
    merged = Store(tmp_path).merge()
    assert len(merged) == 1
    assert merged[0].kind == "void_event" and merged[0].refan_k == 0
    assert (merged[0].gate_results or {}).get("event") == "refan_base_divergence"
    assert (merged[0].gate_results or {}).get("diverged_at") == 1


def test_gate4_pass_and_fail():
    assert gate4_dominance(_balanced_fixture(), CFG).ok
    dominated = [_fan(i, PATHOLOGIES[i % 4], winner="conv_heavy") for i in range(1, 9)] + [
        _fan(9, "mild", winner="conv_light"),
        _fan(10, "mild", winner="norm"),
    ]
    assert not gate4_dominance(dominated, CFG).ok  # 8/10 conv_heavy wins


def test_gate5_pass_and_fail():
    assert gate5_magnitude(_balanced_fixture(), CFG).ok
    bad_rms = {"norm": 0.04, "attn": 0.05, "conv_light": 0.06, "conv_heavy": 0.30}
    recs = [_fan(i, "mild", winner="norm", rms=bad_rms) for i in range(1, 6)]
    assert not gate5_magnitude(recs, CFG).ok


def test_gate6_pass_and_fail():
    early = [_fan(i, "mild", winner="norm", fan_epoch=6) for i in range(1, 6)]
    late_ok = [_fan(i, "mild", winner="norm", fan_epoch=14) for i in range(6, 11)]
    assert gate6_horizon(early + late_ok, CFG).ok
    late_flat = [_fan(i, "mild", winner="norm", fan_epoch=14, win_r=0.5, other_r=0.5, noop_r=0.5) for i in range(6, 11)]
    assert not gate6_horizon(early + late_flat, CFG).ok


def test_gate7_is_report_only():
    recs = [_fan(1, "mild", winner="norm", fan_epoch=6), _fan(1, "mild", winner="norm", fan_epoch=14, win_r=0.75)]
    res = gate7_now_vs_later(recs, CFG)
    assert res.ok  # report-only: never blocks
    assert "mean_gap" in res.detail


def _ok_gates() -> dict[str, dict[str, object]]:
    fans = _balanced_fixture()
    import dataclasses as dc

    return {
        "gate1": dc.asdict(gate1_noop_sanity(fans, CFG)),
        "gate4": dc.asdict(gate4_dominance(fans, CFG)),
    }


def test_freeze_refuses_failing_gates(tmp_path):
    gates = _ok_gates()
    gates["gate4"]["ok"] = False
    with pytest.raises(RuntimeError, match="gates not ok"):
        freeze_manifest(
            CFG, str(tmp_path), gates, Normalizer.identity(), {"best_minus_second": 0.1, "best_minus_noop": 0.2}, None, None, None
        )


def test_freeze_refuses_dirty_worktree(tmp_path, monkeypatch):
    monkeypatch.setattr(kd, "_worktree_clean", lambda: False)
    with pytest.raises(RuntimeError, match="dirty"):
        freeze_manifest(
            CFG, str(tmp_path), _ok_gates(), Normalizer.identity(), {"best_minus_second": 0.1, "best_minus_noop": 0.2}, None, None, None
        )


def test_freeze_refuses_head_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(kd, "_worktree_clean", lambda: True)
    monkeypatch.setattr(kd, "_git_rev", lambda: "bbb")
    (tmp_path / "certified.json").write_text(json.dumps({"git_rev": "aaa"}))
    with pytest.raises(RuntimeError, match="HEAD"):
        freeze_manifest(
            CFG, str(tmp_path), _ok_gates(), Normalizer.identity(), {"best_minus_second": 0.1, "best_minus_noop": 0.2}, None, None, None
        )


def test_freeze_writes_manifest_atomically(tmp_path, monkeypatch):
    monkeypatch.setattr(kd, "_worktree_clean", lambda: True)
    monkeypatch.setattr(kd, "_git_rev", lambda: "aaa")
    (tmp_path / "certified.json").write_text(json.dumps({"git_rev": "aaa"}))
    density = measure_fan_density(_balanced_fixture())
    manifest = freeze_manifest(CFG, str(tmp_path), _ok_gates(), Normalizer.identity(), density, None, None, None)
    on_disk = json.loads((tmp_path / "frozen.json").read_text())
    assert on_disk["manifest_hash"] == manifest["manifest_hash"]
    assert on_disk["spec_rev"] == "98083fd"
    assert "plan_authored_constants" in on_disk
    assert not (tmp_path / "frozen.json.tmp").exists()


def test_dataclass_gates_ok_helper():
    gates = _ok_gates()
    assert dataclass_gates_ok(gates)
    gates["gate1"]["ok"] = False
    assert not dataclass_gates_ok(gates)
