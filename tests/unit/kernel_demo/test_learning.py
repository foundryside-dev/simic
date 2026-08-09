import dataclasses

import pytest
import torch

from experiments.kernel_demo import (
    Config,
    Normalizer,
    Policy,
    SplitViolation,
    make_generator,
    measure_fan_density,
    money_chart_permutation_pvalue,
    policy_loss,
    sign_flip_pvalue,
    train_policy,
    warmup_schedule,
)
from tests.unit.kernel_demo.helpers import (
    adversarial_batch_with_divergent_arm,
    synthetic_agreement,
    synthetic_batch,
    synthetic_fans,
    synthetic_holdout,
)

DENSITY = {"best_minus_second": 0.05, "best_minus_noop": 0.08}


def test_policy_learns_synthetic_mapping_on_true_holdout():
    recs = synthetic_fans(n=120, seed=5)
    pol, _info = train_policy(
        recs,
        Config(),
        Normalizer.identity(),
        make_generator(0),
        frozen_density=DENSITY,
        steps=600,
    )
    assert synthetic_agreement(pol, synthetic_holdout(recs)) > 0.6


def test_warmup_schedule_boundary():
    assert warmup_schedule(0, 100, 0.3) is False
    assert warmup_schedule(29, 100, 0.3) is False
    assert warmup_schedule(30, 100, 0.3) is True
    assert warmup_schedule(99, 100, 0.3) is True


def test_j_now_stopgrad_leaves_which_gradients_unchanged():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    batch = synthetic_batch(seed=9)

    def head_grads(enable_now: bool) -> tuple[torch.Tensor, ...]:
        loss = policy_loss(pol, batch, cfg, beta_which=0.01, beta_now=0.036, enable_now=enable_now)
        return torch.autograd.grad(loss, list(pol.seed_head.parameters()))

    for a, b in zip(head_grads(False), head_grads(True), strict=True):
        assert torch.allclose(a, b, atol=1e-6)  # WHICH trains at 1x regardless of p


def test_now_head_gradient_alive_with_divergent_arm_present():
    cfg = Config()
    pol = Policy(cfg, make_generator(1))
    batch = adversarial_batch_with_divergent_arm(seed=3)
    loss = policy_loss(pol, batch, cfg, beta_which=0.01, beta_now=0.036, enable_now=True)
    grads = torch.autograd.grad(loss, list(pol.now_head.parameters()), allow_unused=True)
    assert any(g is not None and g.abs().sum() > 0 for g in grads)


def test_train_policy_rejects_untrainable_records():
    recs = synthetic_fans(n=10, seed=1)
    recs[3] = dataclasses.replace(recs[3], kind="refan")
    with pytest.raises(SplitViolation):
        train_policy(recs, Config(), Normalizer.identity(), make_generator(0), frozen_density=DENSITY, steps=10)


def test_money_chart_permutation_four_classes():
    # Two classes at 10/10 give P(both rows match under shuffle) ~ 0.33 —
    # mathematically incapable of clearing 0.05; four classes are required.
    paths = [c for c in "abcd" for _ in range(10)]
    picks = [w for w in "wxyz" for _ in range(10)]
    designed = dict(zip("abcd", "wxyz", strict=True))
    obs, p = money_chart_permutation_pvalue(paths, picks, designed, n=4000, seed=3)
    assert obs == 4 and p < 0.05


def test_sign_flip_pvalue_calibration():
    # Fixed-seed form of a 5%-flaky property: valid while the permutation
    # draw order is untouched. On failure, investigate the draw-order
    # change — do not reseed to green.
    g = torch.Generator().manual_seed(1)
    null_lifts = torch.randn(100, generator=g) * 0.01
    assert sign_flip_pvalue(null_lifts, n=2000, seed=2) > 0.05
    assert sign_flip_pvalue(null_lifts + 0.02, n=2000, seed=2) < 0.01


def test_measure_fan_density_empty_is_loud():
    with pytest.raises(ValueError, match="no fan records"):
        measure_fan_density([])
