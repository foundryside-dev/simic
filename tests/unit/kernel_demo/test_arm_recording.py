"""Spec rev 6.2 — the additive per-arm recording, and the wall it stands behind.

The recording is offline-study material. The wall is that the LEARNER never
sees it: post-decision telemetry on the training path is a time-travel channel
that would silently invalidate the headline.
"""

import dataclasses
from typing import cast

import torch

import experiments.kernel_demo as kd
from experiments.kernel_demo import (
    SEED_NAMES,
    BaseTrace,
    Config,
    EpisodeCtx,
    FanRecord,
    Normalizer,
    fan_to_example,
    make_episode,
    make_fan_record,
    run_arm,
    run_base,
    run_fan,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = dataclasses.replace(Config(), horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3))
FAN_EPOCH = 2


def _base(seed: int = 31) -> tuple[EpisodeCtx, BaseTrace]:
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", seed)
    return ctx, run_base(ctx, CFG, fan_epochs=(FAN_EPOCH,))


def test_seed_arm_records_post_decision_telemetry_to_the_horizon():
    ctx, base = _base()
    arm = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, base.snapshots[FAN_EPOCH], "conv_light", False)
    assert arm.telemetry is not None
    # One record per epoch from the fan epoch to the horizon — the arm's own
    # trajectory, not the base prefix.
    assert len(arm.telemetry) == CFG.horizon - FAN_EPOCH
    assert [t["epoch"] for t in arm.telemetry] == list(range(FAN_EPOCH, CFG.horizon))
    # All 20 dimensions, not just the accuracy curve.
    assert set(arm.telemetry[0]) == {f.name for f in dataclasses.fields(kd.TelemetryRecord)}


def test_noop_arm_also_records_its_trajectory():
    # The no-op is the comparand every continued-tenancy question needs.
    ctx, base = _base()
    arm = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, base.snapshots[FAN_EPOCH], "noop", False)
    assert arm.telemetry is not None and len(arm.telemetry) == CFG.horizon - FAN_EPOCH


def test_cost_and_horizon_influence_are_recorded():
    ctx, base = _base()
    arm = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, base.snapshots[FAN_EPOCH], "conv_heavy", False)
    assert arm.wall_s is not None and arm.wall_s > 0.0
    assert arm.peak_mem_bytes is None  # CPU run: absent, never a fabricated 0
    assert arm.g_at_horizon is not None
    assert arm.rms_ratio_horizon is not None and arm.rms_ratio_horizon > 0.0


def test_noop_arm_has_no_influence_measurement():
    # An arm with no seed owes no influence number — absent, not zero.
    ctx, base = _base()
    arm = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, base.snapshots[FAN_EPOCH], "noop", False)
    assert arm.g_at_horizon is None
    assert arm.rms_ratio_horizon is None


def test_delta_weights_land_in_the_sidecar_not_the_record(tmp_path):
    ctx, base = _base()
    arms, _ = run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, base.snapshots[FAN_EPOCH], base, False, delta_dir=tmp_path)
    for name in SEED_NAMES:
        assert (tmp_path / f"{name}.pt").exists()
        assert torch.load(tmp_path / f"{name}.pt", weights_only=True)  # non-empty state dict
    assert not list(tmp_path.glob("*.tmp"))  # atomic replace left no debris
    # The weights are NOT in the serialized arm payload.
    for a in arms:
        assert "state_dict" not in dataclasses.asdict(a)


def _rec_with_arm_telemetry(arm_tele: list[dict[str, object]]) -> FanRecord:
    base_tele = [dataclasses.asdict(kd._selftest_telemetry_stub(e)) for e in range(3)]
    return make_fan_record(
        kind="fan",
        episode_seed=1,
        seed_namespace="dev",
        split_role="train",
        pathology_id="mild",
        fan_epoch=3,
        refan_k=None,
        schedule_id="t",
        policy_checkpoint_id=None,
        iteration=None,
        config_hash="t",
        frozen_block_hash="t",
        manifest_hash=None,
        common_future_hash="t",
        host_init_hash="t",
        env={},
        arms=[{"name": n, "status": "ok", "r_val": 0.5, "r_test": None, "telemetry": arm_tele} for n in ("noop", *SEED_NAMES)],
        telemetry=base_tele,
        decisions=None,
        gate_results=None,
    )


def test_learner_ignores_arm_telemetry():
    # THE wall. Poison every arm's post-decision trajectory; the learner's
    # input must not move by a single bit.
    nz = Normalizer.identity()
    clean = fan_to_example(_rec_with_arm_telemetry([dataclasses.asdict(kd._selftest_telemetry_stub(e)) for e in range(3)]), nz)
    dirty = fan_to_example(_rec_with_arm_telemetry([dataclasses.asdict(kd._selftest_telemetry_stub(e, poison=True)) for e in range(3)]), nz)
    assert torch.equal(cast(torch.Tensor, clean["tokens"]), cast(torch.Tensor, dirty["tokens"]))
    assert torch.equal(cast(torch.Tensor, clean["r"]), cast(torch.Tensor, dirty["r"]))
    assert clean["r_noop"] == dirty["r_noop"]
    assert clean["length"] == dirty["length"]


def test_selftest_step_enforces_the_same_wall():
    # The check is in the certified artifact, not only in the test suite.
    result = kd.run_selftest(CFG, "cpu")
    step = cast(dict[str, dict[str, object]], result["steps"])["learner_ignores_arm_telemetry"]
    assert step["status"] == "pass", step
