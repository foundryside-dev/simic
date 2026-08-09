import torch

from experiments.kernel_demo import (
    Config,
    Slot,
    Stage,
    append_seed_group,
    build_host,
    build_optimizer,
    build_seed,
    cosine_ease,
    tau_init,
)


def _armed_slot(stage: Stage) -> tuple[Config, Slot, torch.Tensor]:
    cfg = Config()
    slot = Slot()
    slot.seed = build_seed("conv_light", 64, 7)
    h = torch.randn(4, 64, 8, 8, requires_grad=True)
    tau_init(slot.seed, h.detach(), cfg)
    slot.stage = stage
    return cfg, slot, h


def test_training_forward_is_value_exact_host():
    _, slot, h = _armed_slot(Stage.TRAINING)
    assert torch.equal(slot(h), h)


def test_training_isolates_host_gradient_but_trains_seed():
    _, slot, h = _armed_slot(Stage.TRAINING)
    slot(h).sum().backward()
    assert h.grad is not None and torch.allclose(h.grad, torch.ones_like(h))
    assert slot.seed is not None
    g = slot.seed.gain.grad
    assert g is not None and g.abs().item() > 0


def test_blending_trains_seed_while_host_gradient_isolated():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha, slot.beta = 0.5, 0.0
    slot(h).sum().backward()
    assert h.grad is not None and torch.allclose(h.grad, torch.ones_like(h))  # beta=0: input detached
    assert slot.seed is not None
    g = slot.seed.gain.grad
    assert g is not None and g.abs().item() > 0  # BLENDING must TRAIN the seed


def test_trust_region_positive_only_in_training():
    cfg, slot, h = _armed_slot(Stage.TRAINING)
    slot(h)
    assert slot.trust_region_loss(cfg).item() > 0


def test_rms_ratio_reads_last_forward():
    _, slot, h = _armed_slot(Stage.BLENDING)
    slot.alpha = 0.01
    slot(h)
    assert slot.rms_ratio() > 0


def test_optimizer_groups_and_seed_append():
    cfg = Config()
    host = build_host("mild", 1)
    opt = build_optimizer(host, cfg)
    n0 = len(opt.param_groups)
    append_seed_group(opt, build_seed("norm", 64, 2), cfg)
    assert len(opt.param_groups) == n0 + 2
    assert opt.param_groups[-1]["weight_decay"] == 0.0
    assert opt.param_groups[-1]["lr"] == cfg.seed_lr


def test_cosine_ease_endpoints():
    assert cosine_ease(0.0) == 0.0
    assert abs(cosine_ease(1.0) - 1.0) < 1e-12
