import dataclasses

import torch

from experiments.kernel_demo import (
    SEED_NAMES,
    Config,
    end_state_R,
    germinate,
    make_episode,
    state_hash,
    take_snapshot,
    train_one_epoch,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = dataclasses.replace(Config(), horizon=4, batch_size=64, stage_k=1, stage_m=1, stage_f=1)


def _run_hash(seed: int) -> str:
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", seed)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    return state_hash(ctx.host)


def test_same_seed_same_episode_cpu_bitwise():
    assert _run_hash(11) == _run_hash(11)
    assert _run_hash(11) != _run_hash(12)


def test_snapshot_captures_restorable_state():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
    train_one_epoch(ctx, 0)
    snap = take_snapshot(ctx)
    h_at_snap = state_hash(ctx.host)
    train_one_epoch(ctx, 1)  # ctx moves on; snapshot must not
    fresh = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
    fresh.host.load_state_dict(snap.host_state)
    assert state_hash(fresh.host) == h_at_snap


def test_germinate_leaves_host_bn_stats_bitwise_unchanged():
    for name in SEED_NAMES:
        ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 21)
        train_one_epoch(ctx, 0)
        before = state_hash(ctx.host)
        germinate(ctx, name)  # tau-init runs host in eval/no_grad
        assert state_hash(ctx.host) == before, name


def test_read_test_wall():
    ctx = make_episode(CFG, make_tiny_bundle(), "cpu", 22, read_test=False)
    for e in range(CFG.horizon):
        train_one_epoch(ctx, e)
    assert ctx.curves_test is None


def test_tiny_bundle_byte_identical_across_calls():
    a, b = make_tiny_bundle(), make_tiny_bundle()
    assert torch.equal(a.train_x, b.train_x)
    assert torch.equal(a.val_y, b.val_y)


def test_end_state_r():
    assert end_state_R([0.1, 0.2, 0.3, 0.4, 0.5]) == (0.3 + 0.4 + 0.5) / 3
