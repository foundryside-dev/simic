import dataclasses

import pytest

import experiments.kernel_demo as kd
from experiments.kernel_demo import (
    BaseTrace,
    Config,
    EpisodeCtx,
    TwinDivergence,
    make_episode,
    run_arm,
    run_base,
    run_fan,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = dataclasses.replace(Config(), horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3))
FAN_EPOCH = 2


def _base(seed: int = 31) -> tuple[EpisodeCtx, BaseTrace]:
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", seed)
    trace = run_base(ctx, CFG, fan_epochs=(FAN_EPOCH,))
    return ctx, trace


def test_twin_matches_base_bitwise():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    arms, meta = run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, base, False)
    assert meta["twin_ok"]
    assert {a.name for a in arms} == {"norm", "attn", "conv_light", "conv_heavy", "noop"}


def test_corrupted_base_hashes_trip_twin_with_epoch():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    bad = dataclasses.replace(base, host_hashes=[*base.host_hashes[:3], "dead", *base.host_hashes[4:]])
    with pytest.raises(TwinDivergence) as ei:
        run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, bad, False)
    assert ei.value.first_bad_epoch == 3


def test_two_arms_from_one_snapshot_no_optimizer_leakage():
    # The class three reviewers hit: arm 1's seed groups must not touch arm 2.
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "conv_heavy", False)
    noop = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "noop", False)
    assert noop.host_hashes == base.host_hashes[FAN_EPOCH:]


def test_nullseed_arm_reproduces_base_hashes_exactly():
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    res = run_arm(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, "nullseed", False)
    assert res.host_hashes == base.host_hashes[FAN_EPOCH:]  # hash lists, never curves


def test_cross_arm_assertion_fires_on_injected_corruption(monkeypatch):
    ctx, base = _base()
    snap = base.snapshots[FAN_EPOCH]
    real = kd.state_hash
    calls = {"n": 0}

    def corrupt_third(module):
        calls["n"] += 1
        return "corrupt" if calls["n"] == 3 else real(module)

    monkeypatch.setattr(kd, "state_hash", corrupt_third)
    with pytest.raises((AssertionError, TwinDivergence)):
        run_fan(CFG, ctx.data, "cpu", 31, ctx.pathology, ctx.future, snap, base, False)


def test_base_divergence_skips_scheduled_fans(monkeypatch):
    import experiments.kernel_demo as k

    real = k.build_record

    def bomb(*a, **kw):
        rec = real(*a, **kw)
        if rec.epoch == 1:
            raise k.TelemetryDivergence("injected")
        return rec

    monkeypatch.setattr(k, "build_record", bomb)
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 41)
    trace = run_base(ctx, CFG, fan_epochs=(FAN_EPOCH,))
    assert trace.status == "diverged"
    assert trace.diverged_at == 1
    assert FAN_EPOCH not in trace.snapshots  # scheduled fan skipped, not run


def test_nonfinite_arm_is_measured_not_abort(monkeypatch):
    import experiments.kernel_demo as k

    ctx, trace = _base()
    snap = trace.snapshots[FAN_EPOCH]
    real = k.tau_init

    def huge_tau(seed, host_feats, cfg):
        g = real(seed, host_feats, cfg)
        if type(seed).__name__ == "ConvHeavySeed":
            seed.gain.data.fill_(1e30)
            return 1e30
        return g

    monkeypatch.setattr(k, "tau_init", huge_tau)
    arms, _ = run_fan(
        CFG,
        ctx.data,
        "cpu",
        31,
        ctx.pathology,
        ctx.future,
        snap,
        trace,
        read_test=False,
    )
    heavy = next(a for a in arms if a.name == "conv_heavy")
    assert heavy.status == "diverged"
    assert heavy.r_val == CFG.diverged_r
    finite = [a for a in arms if a.status == "ok"]
    assert finite  # finite arms completed and passed the cross-arm hash check
