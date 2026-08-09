import dataclasses

import pytest
import torch

from experiments.kernel_demo import (
    CommonFuture,
    Config,
    augment,
    data_split_id,
    split_indices,
)


def test_split_indices_partition_invariants():
    tr, va = split_indices(Config().run_seed)
    assert tr.shape == (45_000,) and va.shape == (5_000,)
    assert len(set(tr.tolist()) & set(va.tolist())) == 0
    tr2, va2 = split_indices(Config().run_seed)
    assert torch.equal(tr, tr2) and torch.equal(va, va2)


def test_common_future_deterministic_hash_sensitive_and_shapes():
    cfg = Config()
    a = CommonFuture.draw(42, n_train=1024, epochs=3, cfg=cfg)
    b = CommonFuture.draw(42, n_train=1024, epochs=3, cfg=cfg)
    c = CommonFuture.draw(43, n_train=1024, epochs=3, cfg=cfg)
    assert a.hash == b.hash and torch.equal(a.order, b.order)
    assert a.hash != c.hash
    steps = 1024 // cfg.batch_size
    assert a.order.shape == (3, steps * cfg.batch_size)  # [E, S*B]
    assert a.crops.shape == (3, steps, cfg.batch_size, 2)
    assert int(a.crops.max()) <= 8 and int(a.crops.min()) >= 0


def test_draw_rejects_subset_smaller_than_batch():
    cfg = Config()
    with pytest.raises(ValueError, match="zero steps"):
        CommonFuture.draw(1, n_train=64, epochs=1, cfg=cfg)


def test_augment_pure_function_no_rng():
    x = torch.randint(0, 256, (4, 3, 32, 32), dtype=torch.uint8)
    crops = torch.tensor([[0, 0], [8, 8], [4, 4], [2, 6]], dtype=torch.uint8)
    flips = torch.tensor([True, False, True, False])
    state = torch.get_rng_state()
    y1 = augment(x, crops, flips)
    y2 = augment(x, crops, flips)
    assert torch.equal(state, torch.get_rng_state())
    assert torch.equal(y1, y2)
    assert y1.shape == (4, 3, 32, 32) and y1.dtype == torch.float32
    assert not torch.equal(y1, augment(x, crops, ~flips))


def test_data_split_id_content_derived():
    assert data_split_id(Config()) == data_split_id(Config())
    assert data_split_id(Config()) != data_split_id(dataclasses.replace(Config(), run_seed=Config().run_seed + 1))
