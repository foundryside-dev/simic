"""Atlas hosts (PDR-0057 G0 item 6): uniform scale-up of each pathology, and an unimpaired reference.

The kernel's `Host` is @semantic and stays untouched. `atlas_hosts` rebuilds the same wiring from a
config, so at scale 1 every pathology must equal the kernel host bitwise (same shapes, same init draw).
Scaled hosts widen every stage by one factor, keep the pathology (BN, gain, kernel size, starved
ratio), and record the realised parameter multiple.
"""

from __future__ import annotations

import pytest
import torch

from experiments import atlas_hosts as ah
from experiments import kernel_demo as kd


def _params(module: torch.nn.Module) -> int:
    return sum(p.numel() for p in module.parameters())


@pytest.mark.parametrize("pathology", kd.PATHOLOGIES)
def test_scale_one_is_the_kernel_host_bitwise(pathology: str) -> None:
    ours = ah.build(ah.base_config(pathology), init_seed=123)
    theirs = kd.build_host(pathology, 123)
    a, b = ours.state_dict(), theirs.state_dict()
    assert list(a) == list(b)
    assert all(torch.equal(a[k], b[k]) for k in a)
    x = torch.randn(4, 3, 32, 32)
    ours.eval(), theirs.eval()
    assert torch.equal(ours(x), theirs(x))


def test_reference_is_unimpaired() -> None:
    cfg = ah.base_config("reference")
    assert (cfg.w1, cfg.w2, cfg.w3, cfg.s2_mid, cfg.use_bn, cfg.gain, cfg.s2_kernel) == (24, 64, 80, 64, True, 1.0, 3)
    host = ah.build(cfg, init_seed=1)
    assert host.forward_to_slot(torch.randn(2, 3, 32, 32)).shape == (2, 64, 8, 8)


@pytest.mark.parametrize("pathology", [*kd.PATHOLOGIES, "reference"])
@pytest.mark.parametrize("target", [1.1, 1.25, 1.5, 2.0])
def test_scaled_host_hits_the_target_multiple_and_keeps_the_pathology(pathology: str, target: float) -> None:
    base = ah.base_config(pathology)
    cfg = ah.scaled_config(pathology, target)
    realised = ah.parameter_multiple(cfg, base)
    assert abs(realised - target) <= 0.05 * target
    assert (cfg.use_bn, cfg.gain, cfg.s2_kernel) == (base.use_bn, base.gain, base.s2_kernel)
    assert all(w % ah.WIDTH_STEP == 0 for w in (cfg.w1, cfg.w2, cfg.w3, cfg.s2_mid))
    if pathology == "channel_starved":
        assert cfg.s2_mid < cfg.w2  # the starved middle stays starved
    host = ah.build(cfg, init_seed=5)
    assert _params(host) == ah.parameter_count(cfg)
    assert host(torch.randn(2, 3, 32, 32)).shape == (2, 10)


def test_scaled_configs_are_deterministic_and_named() -> None:
    a, b = ah.scaled_config("mild", 1.5), ah.scaled_config("mild", 1.5)
    assert a == b and a.name == "mild@x1.5"
    assert ah.config_hash(a) == ah.config_hash(b) != ah.config_hash(ah.base_config("mild"))


def test_unknown_host_is_refused() -> None:
    with pytest.raises(ValueError):
        ah.base_config("healthy")
    with pytest.raises(ValueError):
        ah.scaled_config("mild", 0.9)
