import dataclasses
import inspect

import pytest
import torch

from experiments.kernel_demo import (
    Config,
    derive,
    frozen_block_hash,
    make_generator,
    rng_scope,
)


def test_derive_deterministic_label_sensitive_no_delimiter_collision():
    assert derive(1, "a") == derive(1, "a")
    assert derive(1, "a") != derive(1, "b")
    assert derive(1, "a", 0) != derive(1, "a", 1)
    assert derive(1, "a:b", "c") != derive(1, "a", "b:c")  # length-prefixed
    assert 0 <= derive(123, "x") < 2**64


def test_generator_hermetic_full_range():
    a = torch.rand(4, generator=make_generator(derive(7, "g")))
    b = torch.rand(4, generator=make_generator(derive(7, "g")))
    assert torch.equal(a, b)
    make_generator(2**64 - 1)  # full uint64, no mask


def test_rng_scope_isolates_and_reproduces():
    before = torch.get_rng_state()
    with rng_scope(make_generator(derive(9, "scope"))):
        torch.nn.Linear(4, 4)
    assert torch.equal(before, torch.get_rng_state())

    def build() -> torch.Tensor:
        with rng_scope(make_generator(derive(9, "build"))):
            return torch.nn.Linear(8, 8).weight

    assert torch.equal(build(), build())


def test_frozen_hash_covers_policy_and_gate_knobs_but_not_n_collect():
    c = Config()
    assert frozen_block_hash(c) == frozen_block_hash(Config())
    for f in ("lam", "policy_lr", "warmup_frac", "gate4_dominance_max"):
        changed = dataclasses.replace(c, **{f: getattr(c, f) * 2})
        assert frozen_block_hash(changed) != frozen_block_hash(c)
    more = dataclasses.replace(c, n_collect=400)  # spec's extension lever
    assert frozen_block_hash(more) == frozen_block_hash(c)


def test_config_hash_matches_fresh_subprocess():
    import os
    import subprocess
    import sys

    import experiments.kernel_demo as k

    out = subprocess.run(
        [sys.executable, "-c", "import experiments.kernel_demo as k; print(k.config_hash())"],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": "src:."},
    )
    assert out.stdout.strip() == k.config_hash()


def test_config_hash_covers_semantic_constants():
    import experiments.kernel_demo as k

    before = k.config_hash()
    k.semantic_const("__probe__", 1)
    try:
        assert k.config_hash() != before
    finally:
        del k._SEMANTIC_CONSTANTS["__probe__"]


def test_semantic_const_rejects_duplicate_name():
    import experiments.kernel_demo as k

    k.semantic_const("__dup__", 1)
    try:
        with pytest.raises(ValueError, match="__dup__"):
            k.semantic_const("__dup__", 2)
    finally:
        del k._SEMANTIC_CONSTANTS["__dup__"]


def test_every_public_symbol_is_classified():
    import experiments.kernel_demo as k

    unclassified = [
        name
        for name, obj in vars(k).items()
        if not name.startswith("_")
        and (inspect.isclass(obj) or inspect.isfunction(obj))
        and getattr(obj, "__module__", None) == "experiments.kernel_demo"
        and not any(obj is s for s in k._SEMANTIC_SURFACE)
        and name not in k._NON_SEMANTIC
    ]
    assert not unclassified, f"classify these: decorate @semantic or add to _NON_SEMANTIC with a reason: {unclassified}"
