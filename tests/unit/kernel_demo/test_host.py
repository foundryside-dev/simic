import torch

from experiments.kernel_demo import PATHOLOGIES, build_host, host_init_hash


def test_all_pathologies_forward_and_param_range():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        out = h(torch.randn(2, 3, 32, 32), slot=None)
        assert out.shape == (2, 10)
        n = sum(q.numel() for q in h.parameters())
        assert 80_000 < n < 250_000, (p, n)  # all four, not one representative


def test_slot_interface_invariant_all_pathologies():
    for p in PATHOLOGIES:
        h = build_host(p, init_seed=1)
        feats = h.forward_to_slot(torch.randn(2, 3, 32, 32))
        assert feats.shape == (2, 64, 8, 8), p
        assert h.feat_channels == 64


def test_init_hash_is_seed_function():
    assert host_init_hash(build_host("mild", 5)) == host_init_hash(build_host("mild", 5))
    assert host_init_hash(build_host("mild", 5)) != host_init_hash(build_host("mild", 6))


def test_pathology_structure():
    un = build_host("under_normalized", 1)
    assert not any(isinstance(m, torch.nn.BatchNorm2d) for m in un.modules())
    nm = build_host("no_spatial_mix", 1)
    s2 = [m for m in nm.stage2.modules() if isinstance(m, torch.nn.Conv2d)]
    assert all(m.kernel_size == (1, 1) for m in s2)


def test_construction_does_not_touch_global_rng():
    before = torch.get_rng_state()
    build_host("mild", 7)
    assert torch.equal(before, torch.get_rng_state())
