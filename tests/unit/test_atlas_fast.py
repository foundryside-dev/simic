"""Atlas exact-records speed tier (spike S3 item 3): fewer host-device syncs, the same records.

`atlas_fast.train_epoch` and `atlas_fast.score` must return exactly what the frozen runner's
`train_epoch` and `score` return, leave the training state bitwise identical, and diverge at the
same step with the same record. Control flow is unchanged: the objective's finiteness is still
checked every step, and the per-parameter gradient checks are combined into one check per step.
Only value reads (CE, objective, gains, squared-gradient sums) move to the end of the epoch, where
Python accumulates them in the original order.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import pytest
import torch

from experiments import atlas, atlas_fast
from experiments import bounded_comparison as runner
from experiments.bounded_data import RunSpec

CASES = [
    ("under_normalized", "norm", "v2"),
    ("mild", "conv_heavy", "v1"),  # BN host, BN seed
    ("channel_starved", "conv_light", "v2"),
    ("no_spatial_mix", "attn", "v2"),
]


def _state(unit: atlas.Unit, t: int, action: str | None) -> tuple[Any, Any, Any]:
    trunk = unit.trunk(decision_points=(t,))
    host, slot, opt = atlas.materialize(trunk.snapshots[t], unit.spec, unit.device)
    if action is not None:
        runner.attach_seed(host, slot, opt, dataclasses.replace(unit.spec, seed_type=action), unit.tx, static=False)
    return host, slot, opt


def _run(fn: Any, unit: atlas.Unit, t: int, action: str | None, epochs: int) -> tuple[list[dict[str, Any]], list[Any], str]:
    host, slot, opt = _state(unit, t, action)
    out, scores = [], []
    for epoch in range(t, t + epochs):
        out.append(fn["train"](host, slot, opt, unit.spec, unit.future, unit.tx, unit.ty, epoch))
        scores.append(fn["score"](host, slot, unit.dx, unit.dy, unit.spec.batch_size))
    return out, scores, runner.training_state_hash(host, slot, opt)


SLOW = {"train": runner.train_epoch, "score": runner.score}
FAST = {"train": atlas_fast.train_epoch, "score": atlas_fast.score}


@pytest.mark.parametrize(("host", "seed_type", "lifecycle"), CASES)
def test_fast_epochs_are_the_frozen_epochs_bitwise_through_every_stage(host: str, seed_type: str, lifecycle: str) -> None:
    """Graft at epoch 1, then TRAINING, BLENDING x2, FOSSILIZING, FOSSILIZED: every stage of the lifecycle."""
    unit = atlas.Unit.load(RunSpec(epochs=7, host=host, seed_type=seed_type, lifecycle=lifecycle))
    slow = _run(SLOW, unit, 1, seed_type, 6)
    fast = _run(FAST, unit, 1, seed_type, 6)
    assert fast == slow


def test_fast_no_growth_epochs_are_bitwise() -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2"))
    assert _run(FAST, unit, 0, None, 3) == _run(SLOW, unit, 0, None, 3)


def _divergence(fn: Any, unit: atlas.Unit, sabotage: str) -> dict[str, Any]:
    host, slot, opt = _state(unit, 1, "norm")
    if sabotage == "objective":
        with torch.no_grad():
            next(host.parameters()).fill_(math.inf)
    else:  # a non-finite gradient from step 3 on, through a parameter hook seen by both paths
        calls = {"n": 0}

        def hook(grad: torch.Tensor) -> torch.Tensor:
            calls["n"] += 1
            return grad * math.inf if calls["n"] >= 4 else grad

        next(host.parameters()).register_hook(hook)
    with pytest.raises(runner.ArmDivergedError) as stop:
        fn["train"](host, slot, opt, unit.spec, unit.future, unit.tx, unit.ty, 1)
    e = stop.value
    return {"epoch": e.epoch, "step": e.step, "reason": e.reason, "stage": e.stage, "witness": e.witness}


@pytest.mark.parametrize("sabotage", ["objective", "gradient"])
def test_fast_divergence_is_the_frozen_divergence(sabotage: str) -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="under_normalized", seed_type="norm", lifecycle="v2"))
    fast, slow = _divergence(FAST, unit, sabotage), _divergence(SLOW, unit, sabotage)
    assert fast == slow and fast["step"] == (0 if sabotage == "objective" else 3)


def test_fast_score_refuses_non_finite_logits_and_restores_state() -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2"))
    host, slot, _opt = _state(unit, 1, None)
    host.train()
    with torch.no_grad():
        host.fc.bias.fill_(math.nan)
    rng = torch.get_rng_state().clone()
    with pytest.raises(runner.NonFiniteError):
        atlas_fast.score(host, slot, unit.dx, unit.dy, unit.spec.batch_size)
    assert host.training is True and torch.equal(rng, torch.get_rng_state())  # modes and RNG restored
