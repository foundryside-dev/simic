"""Graft lifecycle v2: a per-step trust-region curvature clamp, plus witnesses recorded in both variants.

Design: docs/bounded-lifecycle-v2.md (revised after Fable review). v1 must stay
numerically identical to the kernel Slot; v2 must bound kappa at every STE step.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
import torch

from experiments import bounded_comparison as runner
from experiments import kernel_demo
from experiments.bounded_data import RunSpec, validated_spec


def test_c_star_matches_the_nesterov_stability_limit() -> None:
    cfg = RunSpec().kernel_config()
    assert runner.c_star(cfg) == pytest.approx(2 * (1 + 0.9) / (0.05 * (1 + 2 * 0.9)))
    assert runner.c_star(cfg) == pytest.approx(27.142857, rel=1e-6)


@pytest.mark.parametrize("changes", [{"lifecycle": "v3"}, {"trust_safety": 0.0}, {"trust_safety": 1.5}, {"lifecycle": 2}])
def test_spec_refuses_unknown_lifecycle_or_safety(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        validated_spec(dataclasses.asdict(dataclasses.replace(RunSpec(), **changes)))


def test_spec_defaults_are_the_v1_lifecycle() -> None:
    spec = RunSpec()
    assert (spec.lifecycle, spec.trust_safety) == ("v1", 0.5)


def _training_slot(lifecycle: str, seed_type: str, h_scale: float) -> tuple[runner.ScaleAwareSlot, kernel_demo.Slot, torch.Tensor]:
    torch.manual_seed(0)
    spec = RunSpec(lifecycle=lifecycle, seed_type=seed_type)
    ours, theirs = runner.ScaleAwareSlot(spec), kernel_demo.Slot()
    seed = kernel_demo.build_seed(seed_type, 64, 11)
    for slot in (ours, theirs):
        slot.seed = seed
        slot.stage = kernel_demo.Stage.TRAINING
        slot.alpha = slot.beta = 0.0
    h = torch.randn(8, 64, 8, 8) * h_scale
    return ours, theirs, h


@pytest.mark.parametrize("seed_type", ["norm", "conv_heavy", "conv_light", "attn"])
def test_v1_trust_loss_is_bitwise_the_kernel_slot_and_leaves_seed_buffers_untouched(seed_type: str) -> None:
    ours, theirs, h = _training_slot("v1", seed_type, 0.2)
    cfg = RunSpec(lifecycle="v1", seed_type=seed_type).kernel_config()
    theirs(h)
    expected = theirs.trust_region_loss(cfg)
    assert ours.seed is not None
    ours(h)  # the forward itself legitimately updates train-mode BN statistics
    before = kernel_demo.state_hash(ours.seed)
    got = ours.trust_region_loss(cfg)
    assert kernel_demo.state_hash(ours.seed) == before  # the witness's extra forward must not
    assert torch.equal(got, expected)
    assert ours.last_witness is not None
    assert ours.last_witness["lam_t"] == cfg.lam and ours.last_witness["clamped"] is False


@pytest.mark.parametrize("seed_type", ["norm", "conv_heavy"])
def test_v2_clamps_the_trust_curvature_at_every_step(seed_type: str) -> None:
    ours, _, h = _training_slot("v2", seed_type, 0.1)
    spec = RunSpec(lifecycle="v2", seed_type=seed_type)
    cfg = spec.kernel_config()
    ours(h)
    ours.trust_region_loss(cfg)
    witness = ours.last_witness
    assert witness is not None
    assert witness["kappa_live"] > spec.trust_safety * runner.c_star(cfg)  # this scale violates the limit under v1
    assert witness["clamped"] is True and witness["lam_t"] < cfg.lam
    effective = witness["kappa_live"] * witness["lam_t"] / cfg.lam
    assert effective <= spec.trust_safety * runner.c_star(cfg) * (1 + 1e-9)


def test_v2_equals_v1_where_v1_is_safe() -> None:
    v2, _, h = _training_slot("v2", "conv_light", 1.0)
    v1, _, _ = _training_slot("v1", "conv_light", 1.0)
    cfg = RunSpec().kernel_config()
    v2(h)
    v1(h)
    assert torch.equal(v2.trust_region_loss(cfg), v1.trust_region_loss(cfg))
    assert v2.last_witness is not None and v2.last_witness["clamped"] is False


@pytest.fixture(scope="module")
def paired_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base = tmp_path_factory.mktemp("lifecycle")
    runs = {}
    for lifecycle in ("v1", "v2"):
        runs[lifecycle] = base / lifecycle
        runner.train(RunSpec(epochs=7, lifecycle=lifecycle), runs[lifecycle])
    return runs


def _records(root: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (root / "training.jsonl").read_text().splitlines()]


def test_both_variants_record_the_ste_witness_table_and_verify(paired_runs: dict[str, Path]) -> None:
    for lifecycle, root in paired_runs.items():
        _manifest, _complete, spec = runner.verify_run(root)
        ste = next(r for r in _records(root) if r["kind"] == "epoch" and r["arm"] == "scheduled" and r["epoch"] == spec.graft_epoch)
        table = ste["witness"]["ste"]
        steps = spec.train_size // spec.batch_size
        assert {k: len(v) for k, v in table.items()} == dict.fromkeys(("kappa_live", "lam_t", "gain", "clamped"), steps)
        if lifecycle == "v1":
            assert set(table["lam_t"]) == {spec.lam}


def test_every_seeded_epoch_records_gain_range_and_birth_records_the_tau_witness(paired_runs: dict[str, Path]) -> None:
    records = _records(paired_runs["v2"])
    seeded = [r for r in records if r["kind"] == "epoch" and r["arm"] != "no_growth" and r["witness"]["seed_present"]]
    assert seeded and all(r["witness"]["gain_min"] <= r["witness"]["gain_max"] for r in seeded)
    births = [r["birth"] for r in records if r.get("birth")]
    assert births and all(b["realised_ratio_at_birth"] > 0 for b in births)
    blend_entries = [r["witness"]["rms_ratio_blend_entry"] for r in seeded if "rms_ratio_blend_entry" in r["witness"]]
    assert len(blend_entries) == 1


def test_variant_independent_arms_are_bitwise_equal_across_variants(paired_runs: dict[str, Path]) -> None:
    """Free replay test: no growth and static do not depend on the lifecycle variant."""

    def comparable(root: Path, arm: str) -> list[dict[str, Any]]:
        return [{k: v for k, v in r.items() if k != "wall_s"} for r in _records(root) if r["arm"] == arm]

    for arm in ("no_growth", "static"):
        assert comparable(paired_runs["v1"], arm) == comparable(paired_runs["v2"], arm)


def test_divergence_in_ste_keeps_its_partial_witness_and_stage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_tr = runner.ScaleAwareSlot.trust_region_loss
    calls = {"n": 0}

    def nan_on_third_step(self: Any, cfg: Any) -> Any:
        value = original_tr(self, cfg)
        if self.stage is kernel_demo.Stage.TRAINING:
            calls["n"] += 1
            if calls["n"] == 3:  # the smoke config has 4 steps per epoch
                return value * float("nan")
        return value

    monkeypatch.setattr(runner.ScaleAwareSlot, "trust_region_loss", nan_on_third_step)
    root = tmp_path / "run"
    runner.train(RunSpec(epochs=7, lifecycle="v1"), root)
    runner.verify_run(root)
    diverged = next(r for r in _records(root) if r["kind"] == "diverged")
    assert diverged["stage"] == "training"
    assert len(diverged["witness"]["ste"]["kappa_live"]) == 3  # steps 0..2, including the one that went non-finite
