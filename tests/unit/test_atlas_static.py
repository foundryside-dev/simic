"""Static arm with train-mode tau calibration (simic-e3803e8200).

The registered static arm (`Unit.static`, through the frozen runner's `attach_seed`) reads the
host's slot features for tau in eval mode. At step zero a BatchNorm host's running statistics are
untrained, so the static seed is born far below tau on every BN host (Fleet C1 pilot: realised
ratio 0.0013-0.0018 against 0.05). The corrected arm reads them in train mode, the mode of the
first training step, with every host buffer restored. It must:
- be born at tau on every host;
- equal the registered static arm bit for bit on a host without BatchNorm, apart from its labels;
- leave the host, the optimizer and the RNG exactly as it found them.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
import torch

from experiments import atlas, atlas_static
from experiments import bounded_comparison as runner
from experiments.bounded_data import RunSpec
from experiments.kernel_demo import build_optimizer, state_hash

HOSTS = [
    ("under_normalized", "norm"),
    ("mild", "conv_light"),
    ("channel_starved", "conv_heavy"),
    ("no_spatial_mix", "attn"),
]
BN_HOSTS = HOSTS[1:]


def _ratio(birth: dict[str, Any]) -> float:
    value = birth["realised_ratio_at_birth"]
    return float(value["value"] if isinstance(value, dict) else value)


def _born(host: str, seed_type: str, attach: Any) -> tuple[dict[str, Any], Any, Any, Any]:
    spec = RunSpec(epochs=7, host=host, seed_type=seed_type, lifecycle="v2")
    unit = atlas.Unit.load(spec)
    h = atlas.make_host(spec, None, unit.device)
    slot = runner.ScaleAwareSlot(spec)
    opt = build_optimizer(h, spec.kernel_config())
    return attach(h, slot, opt, spec, unit.tx), h, slot, opt


def _registered(h: Any, slot: Any, opt: Any, spec: RunSpec, x: torch.Tensor) -> dict[str, Any]:
    return runner.attach_seed(h, slot, opt, spec, x, static=True)


@pytest.mark.parametrize(("host", "seed_type"), HOSTS)
def test_train_calibrated_static_is_born_at_tau_on_every_host(host: str, seed_type: str) -> None:
    birth, _h, slot, _opt = _born(host, seed_type, atlas_static.attach_static_train_calibrated)
    assert _ratio(birth) == pytest.approx(RunSpec().tau, rel=1e-3)
    assert birth["calibration_mode"] == atlas_static.CALIBRATION_MODE
    assert slot.stage.value == "fossilized" and slot.alpha == slot.beta == 1.0


@pytest.mark.parametrize(("host", "seed_type"), BN_HOSTS)
def test_registered_static_is_born_below_tau_on_bn_hosts(host: str, seed_type: str) -> None:
    """The defect the corrected arm exists for, pinned so a change to the registered arm is seen."""
    birth, *_ = _born(host, seed_type, _registered)
    assert _ratio(birth) < RunSpec().tau / 5
    assert "calibration_mode" not in birth  # the registered birth record is the frozen runner's, unchanged


@pytest.mark.parametrize(("host", "seed_type"), HOSTS)
def test_calibration_leaves_host_optimizer_and_rng_untouched(host: str, seed_type: str) -> None:
    spec = RunSpec(epochs=7, host=host, seed_type=seed_type, lifecycle="v2")
    unit = atlas.Unit.load(spec)
    h = atlas.make_host(spec, None, unit.device)
    h.eval()  # a non-default mode, to see that each module's mode comes back
    modes = [m.training for m in h.modules()]
    buffers = {k: v.clone() for k, v in h.state_dict().items()}
    slot = runner.ScaleAwareSlot(spec)
    opt = build_optimizer(h, spec.kernel_config())
    host_hash, opt_hash, rng = state_hash(h), runner.optimizer_host_hash(opt), torch.get_rng_state().clone()
    atlas_static.attach_static_train_calibrated(h, slot, opt, spec, unit.tx)
    assert state_hash(h) == host_hash and runner.optimizer_host_hash(opt) == opt_hash
    assert all(torch.equal(buffers[k], v) for k, v in h.state_dict().items())
    assert [m.training for m in h.modules()] == modes
    assert torch.equal(rng, torch.get_rng_state())


def test_no_bn_host_train_calibrated_static_is_the_registered_static_bitwise() -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="under_normalized", seed_type="norm", lifecycle="v2"))
    registered = unit.static("norm")
    corrected = unit.static("norm", calibration="train")
    assert registered.diverged is None and corrected.diverged is None
    assert registered.birth is not None and corrected.birth is not None
    assert [r["arm"] for r in corrected.records] == ["static_calibrated"] * len(corrected.records)
    assert [{**r, "arm": "static"} for r in corrected.records] == registered.records
    assert {k: v for k, v in corrected.birth.items() if k != "calibration_mode"} == registered.birth
    assert corrected.initial_dev == registered.initial_dev and corrected.costs == registered.costs


def test_bn_host_train_calibrated_static_runs_and_differs() -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2"))
    registered = unit.static("conv_light")
    corrected = unit.static("conv_light", calibration="train")
    assert corrected.diverged is None and len(corrected.records) == len(registered.records)
    assert registered.birth is not None and corrected.birth is not None
    assert _ratio(corrected.birth) == pytest.approx(RunSpec().tau, rel=1e-3)
    assert corrected.birth["gain_at_birth"] > 5 * registered.birth["gain_at_birth"]


def test_unknown_calibration_is_refused() -> None:
    unit = atlas.Unit.load(RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2"))
    with pytest.raises(ValueError, match="calibration"):
        unit.static("conv_light", calibration="eval-ish")


def test_one_germination_only() -> None:
    spec = RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2")
    unit = atlas.Unit.load(spec)
    h = atlas.make_host(spec, None, unit.device)
    slot = runner.ScaleAwareSlot(spec)
    opt = build_optimizer(h, spec.kernel_config())
    atlas_static.attach_static_train_calibrated(h, slot, opt, spec, unit.tx)
    with pytest.raises(RuntimeError, match="one lifetime germination"):
        atlas_static.attach_static_train_calibrated(h, slot, opt, dataclasses.replace(spec), unit.tx)
