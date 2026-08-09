import torch

from experiments.kernel_demo import (
    EPOCH_FEATURE_IDX,
    TELEMETRY_DIM,
    Config,
    Normalizer,
    Policy,
    TelemetryRecord,
    decide_live,
    make_generator,
    schedule_only_mask,
)
from tests.unit.kernel_demo.conftest import make_telemetry_rec


def _rec_at(epoch: int) -> TelemetryRecord:
    return make_telemetry_rec(epoch=epoch)


def test_shapes_and_determinism():
    pol = Policy(Config(), make_generator(1))
    x = torch.randn(3, 7, TELEMETRY_DIM)
    lengths = torch.tensor([7, 5, 2])
    p1, s1 = pol(x, lengths)
    p2, _s2 = pol(x, lengths)
    assert p1.shape == (3,) and s1.shape == (3, 4)
    assert torch.equal(p1, p2)


def test_causality_future_tokens_do_not_leak():
    pol = Policy(Config(), make_generator(1))
    x = torch.randn(1, 7, TELEMETRY_DIM)
    lengths = torch.tensor([4])
    p_a, s_a = pol(x, lengths)
    x2 = x.clone()
    x2[0, 5:] += 100.0
    p_b, s_b = pol(x2, lengths)
    assert torch.equal(p_a, p_b) and torch.equal(s_a, s_b)


def test_policy_param_count_pinned():
    n = sum(p.numel() for p in Policy(Config(), make_generator(1)).parameters())
    assert 70_000 < n < 130_000


def test_schedule_only_mask_batched_and_1d():
    v = torch.arange(TELEMETRY_DIM, dtype=torch.float32)
    m = schedule_only_mask(v)
    assert m[EPOCH_FEATURE_IDX] == v[EPOCH_FEATURE_IDX]
    assert m.abs().sum() == v[EPOCH_FEATURE_IDX].abs()
    x = torch.randn(2, 7, TELEMETRY_DIM)
    mx = schedule_only_mask(x)
    assert torch.equal(mx[..., EPOCH_FEATURE_IDX], x[..., EPOCH_FEATURE_IDX])
    others = [i for i in range(TELEMETRY_DIM) if i != EPOCH_FEATURE_IDX]
    assert mx[..., others].abs().sum() == 0


def test_decide_live_window_boundaries_inclusive():
    pol = Policy(Config(), make_generator(1))
    nz = Normalizer.identity()
    tele = [_rec_at(e) for e in range(20)]
    for epoch, allowed in [(4, False), (5, True), (15, True), (16, False)]:
        fire, _ = decide_live(pol, nz, tele[: epoch + 1], epoch, Config())
        if not allowed:
            assert fire is False
