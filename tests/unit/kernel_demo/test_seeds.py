import pytest
import torch

from experiments.kernel_demo import (
    SEED_NAMES,
    Config,
    build_host,
    build_seed,
    split_decay_groups,
    tau_init,
)


@pytest.mark.parametrize("name", SEED_NAMES)
def test_delta_zero_before_tau_init(name):
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(2, 64, 8, 8)
    assert torch.equal(s(h), torch.zeros_like(h))


@pytest.mark.parametrize("name", SEED_NAMES)
def test_tau_init_hits_target_rms_in_training_mode(name):
    cfg = Config()
    s = build_seed(name, channels=64, init_seed=3)
    h = torch.randn(16, 64, 8, 8)
    g = tau_init(s, h, cfg)
    assert g != 0.0
    s.train()  # measure in the SAME mode tau_init calibrated (D11)
    with torch.no_grad():
        ratio = s(h).pow(2).mean().sqrt() / h.pow(2).mean().sqrt()
    assert abs(ratio.item() - cfg.tau) / cfg.tau < 0.05


def test_param_budgets_pinned():
    counts = {n: sum(p.numel() for p in build_seed(n, 64, 1).parameters()) for n in SEED_NAMES}
    assert counts["norm"] < 300
    assert 2_000 < counts["attn"] < 12_000
    assert 5_000 < counts["conv_light"] < 20_000
    assert 35_000 < counts["conv_heavy"] < 90_000


def test_no_decay_rule_catches_sequential_bn_affines():
    s = build_seed("conv_heavy", 64, 1)
    decay, no_decay = split_decay_groups(s)
    assert any(n.endswith("gain") for n, _ in no_decay)
    assert any(isinstance(m, torch.nn.BatchNorm2d) for m in s.modules())
    for n, p in decay:
        assert p.ndim > 1, f"1-d param {n} leaked into decay group"


def test_config_hash_call_order_independent():
    import experiments.kernel_demo as k

    before = k.config_hash()
    build_host("mild", 3)
    build_seed("conv_heavy", 64, 4)
    build_seed("conv_heavy", 64, 4)  # repeat call — the rev 3 drift case
    assert k.config_hash() == before
