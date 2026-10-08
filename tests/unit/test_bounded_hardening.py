"""Runner hardening before round 2: selectable host/seed, fit-data calibration, enforced pairing."""

from __future__ import annotations

import dataclasses
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from experiments import bounded_comparison as runner
from experiments import bounded_data
from experiments.bounded_data import RunSpec, smoke_split, tensor_hash, validated_spec


@pytest.mark.parametrize("changes", [{"host": "nonexistent"}, {"seed_type": "nonexistent"}, {"host": 3}])
def test_spec_refuses_unknown_host_or_seed_type(changes):
    with pytest.raises(ValueError):
        validated_spec(dataclasses.asdict(dataclasses.replace(RunSpec(), **changes)))


def test_spec_defaults_keep_the_screen_v1_configuration():
    spec = RunSpec()
    assert (spec.host, spec.seed_type) == ("mild", "conv_light")


@pytest.fixture(scope="module")
def starved_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("hardening") / "run"
    runner.train(RunSpec(epochs=7, host="channel_starved", seed_type="conv_heavy"), root)
    return root


def test_selected_host_and_seed_type_are_built_and_recorded(starved_run):
    manifest, complete, _ = runner.verify_run(starved_run)
    assert manifest["host"] == "kernel-demo-channel_starved"
    assert manifest["seed_type"] == "conv_heavy"
    assert complete["summaries"]["no_growth"]["final_parameters"] != 142006
    assert complete["summaries"]["static"]["final_parameters"] > complete["summaries"]["no_growth"]["final_parameters"]


def test_seed_gain_is_calibrated_on_fit_inputs_not_development_inputs(starved_run):
    spec = RunSpec(epochs=7, host="channel_starved", seed_type="conv_heavy")
    tx, _ = smoke_split(spec, "fit")
    starts = [json.loads(line) for line in (starved_run / "training.jsonl").read_text().splitlines()]
    births = [r["birth"] for r in starts if r["kind"] == "arm_start" and r["birth"] is not None]
    births += [r["birth"] for r in starts if r["kind"] == "epoch" and r.get("birth")]
    assert births, "static arm must record a birth"
    for birth in births:
        assert birth["calibration_source"] == "fit"
        assert birth["calibration_inputs_sha256"] == tensor_hash(tx[: spec.batch_size])


def _tamper(run: Path, tmp_path: Path, mutate: Callable[[list[dict[str, Any]]], None]) -> Path:
    root = tmp_path / "copy"
    shutil.copytree(run, root)
    path = root / "training.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    mutate(records)
    path.write_text("".join(runner.strict_json(r) + "\n" for r in records))
    completion = json.loads((root / "complete.json").read_text())
    completion["artifacts"]["training.jsonl"] = bounded_data.file_hash(path)
    (root / "complete.json").write_text(json.dumps(completion))
    return root


def test_verify_run_refuses_unpaired_initial_hosts(starved_run, tmp_path):
    def mutate(records):
        start = next(r for r in records if r["kind"] == "arm_start" and r["arm"] == "static")
        start["host_initial_parameter_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="pairing"):
        runner.verify_run(_tamper(starved_run, tmp_path, mutate))


def test_verify_run_refuses_divergence_before_the_graft(starved_run, tmp_path):
    def mutate(records):
        epoch0 = next(r for r in records if r["kind"] == "epoch" and r["arm"] == "scheduled" and r["epoch"] == 0)
        epoch0["training_state_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="pairing"):
        runner.verify_run(_tamper(starved_run, tmp_path, mutate))


def test_calibration_prefix_is_not_the_development_prefix(starved_run):
    spec = RunSpec(epochs=7, host="channel_starved", seed_type="conv_heavy")
    dx, _ = smoke_split(spec, "dev")
    start = next(json.loads(line) for line in (starved_run / "training.jsonl").read_text().splitlines() if '"static"' in line)
    assert start["birth"]["calibration_inputs_sha256"] != tensor_hash(dx[: spec.batch_size])


def test_verify_run_refuses_a_birth_calibrated_on_other_inputs(starved_run, tmp_path):
    def mutate(records: list[dict[str, Any]]) -> None:
        start = next(r for r in records if r["kind"] == "arm_start" and r["arm"] == "static")
        start["birth"]["calibration_inputs_sha256"] = "1" * 64

    with pytest.raises(ValueError, match="calibration"):
        runner.verify_run(_tamper(starved_run, tmp_path, mutate))


def test_verify_run_refuses_a_non_fit_calibration_source(starved_run, tmp_path):
    def mutate(records: list[dict[str, Any]]) -> None:
        start = next(r for r in records if r["kind"] == "arm_start" and r["arm"] == "static")
        start["birth"]["calibration_source"] = "dev"

    with pytest.raises(ValueError, match="fit"):
        runner.verify_run(_tamper(starved_run, tmp_path, mutate))


def test_evaluate_rebuilds_the_selected_host_and_seed(starved_run, tmp_path):
    root = tmp_path / "eval"
    shutil.copytree(starved_run, root)
    record = runner.evaluate(root)
    assert set(record["scores"]) >= set(runner.ARMS)


def test_cli_rejects_unknown_host_as_a_usage_error():
    with pytest.raises(SystemExit):
        runner.parse_arguments(["train", "--output", "x", "--host", "nonexistent"])


@pytest.fixture(scope="module")
def diverged_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The scheduled arm diverges in its germination epoch; the unit must still complete (PDR-0047)."""
    root = tmp_path_factory.mktemp("diverged") / "run"
    spec = RunSpec(epochs=7)
    original = runner.train_epoch

    def flaky(host: Any, slot: Any, opt: Any, spec_: RunSpec, future: Any, x: Any, y: Any, epoch: int) -> dict[str, Any]:
        if slot.seed is not None and slot.alpha == 0.0 and epoch == spec_.graft_epoch:
            raise runner.ArmDivergedError(epoch=epoch, step=3, reason="non-finite training objective")
        return original(host, slot, opt, spec_, future, x, y, epoch)

    import pytest as _pytest

    with _pytest.MonkeyPatch.context() as mp:
        mp.setattr(runner, "train_epoch", flaky)
        runner.train(spec, root)
    return root


def test_a_diverged_arm_is_recorded_and_the_unit_completes(diverged_run: Path) -> None:
    _manifest, complete, spec = runner.verify_run(diverged_run)
    assert complete["arm_status"] == {"no_growth": "completed", "static": "completed", "scheduled": "diverged"}
    scheduled = complete["summaries"]["scheduled"]
    assert scheduled["status"] == "diverged" and scheduled["diverged_epoch"] == spec.graft_epoch
    assert "final_dev" not in scheduled
    assert not (diverged_run / "scheduled.pt").exists()
    assert (diverged_run / "static.pt").exists()
    records = [json.loads(line) for line in (diverged_run / "training.jsonl").read_text().splitlines()]
    last = [r for r in records if r["arm"] == "scheduled"][-1]
    assert last["kind"] == "diverged" and last["epoch"] == spec.graft_epoch


def test_verify_run_refuses_a_diverged_summary_without_its_record(diverged_run: Path, tmp_path: Path) -> None:
    def mutate(records: list[dict[str, Any]]) -> None:
        records[:] = [r for r in records if r["kind"] != "diverged"]

    with pytest.raises(ValueError):
        runner.verify_run(_tamper(diverged_run, tmp_path, mutate))


def test_evaluate_refuses_a_run_with_a_diverged_arm(diverged_run: Path, tmp_path: Path) -> None:
    root = tmp_path / "eval"
    shutil.copytree(diverged_run, root)
    with pytest.raises(ValueError, match="diverged"):
        runner.evaluate(root)


def _train_with(monkeypatch: pytest.MonkeyPatch, root: Path, target: str, inject: Any) -> Path:
    monkeypatch.setattr(target, inject)
    runner.train(RunSpec(epochs=7), root)
    return root


@pytest.mark.parametrize("path", ["objective", "gradient", "scoring"])
def test_every_non_finite_detector_records_a_divergence_instead_of_aborting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    """Induce real non-finite values at each detector, only in the scheduled arm after germination (review 60683c4)."""
    from experiments import kernel_demo

    original_tr = kernel_demo.Slot.trust_region_loss
    original_score = runner.score

    def nan_trust_region(self: Any, cfg: Any) -> Any:
        value = original_tr(self, cfg)
        return value * float("nan") if self.stage is kernel_demo.Stage.TRAINING else value

    def nan_gradient_trust_region(self: Any, cfg: Any) -> Any:
        value = original_tr(self, cfg)
        if self.stage is kernel_demo.Stage.TRAINING and self.last_delta is not None:
            return value + _nan_grad(self.last_delta)  # finite forward, NaN backward
        return value

    def nan_score(host: Any, slot: Any, x: Any, y: Any, batch_size: int) -> Any:
        if slot.seed is not None and slot.alpha == 0.0:
            x = x.float() * float("nan")
            return original_score(host, slot, x, y, batch_size)
        return original_score(host, slot, x, y, batch_size)

    injected = {
        "objective": ("experiments.kernel_demo.Slot.trust_region_loss", nan_trust_region),
        "gradient": ("experiments.kernel_demo.Slot.trust_region_loss", nan_gradient_trust_region),
        "scoring": ("experiments.bounded_comparison.score", nan_score),
    }[path]
    root = _train_with(monkeypatch, tmp_path / path, *injected)
    _manifest, complete, spec = runner.verify_run(root)
    assert complete["arm_status"] == {"no_growth": "completed", "static": "completed", "scheduled": "diverged"}
    assert complete["summaries"]["scheduled"]["diverged_epoch"] == spec.graft_epoch


def _nan_grad(t: Any) -> Any:
    """Zero in the forward pass, NaN in the backward pass: a finite objective with a non-finite gradient."""
    import torch

    class NanGrad(torch.autograd.Function):
        @staticmethod
        def forward(ctx: Any, x: Any) -> Any:
            return x.sum() * 0.0

        @staticmethod
        def backward(ctx: Any, grad: Any) -> Any:
            return torch.full_like(t, float("nan"))

    return NanGrad.apply(t)  # type: ignore[no-untyped-call]


@pytest.mark.parametrize(
    ("field", "value"),
    [("diverged_step", -7), ("diverged_step", 10**6), ("costs.seed_train_examples", -1), ("costs.optimizer_parameter_steps", "x")],
)
def test_forged_divergence_summary_is_refused(diverged_run: Path, tmp_path: Path, field: str, value: Any) -> None:
    root = tmp_path / "forged"
    shutil.copytree(diverged_run, root)
    completion = json.loads((root / "complete.json").read_text())
    target = completion["summaries"]["scheduled"]
    if "." in field:
        outer, inner = field.split(".")
        target[outer][inner] = value
    else:
        target[field] = value
    (root / "complete.json").write_text(json.dumps(completion))
    with pytest.raises(ValueError):
        runner.verify_run(root)


def test_divergence_record_and_summary_must_agree(diverged_run: Path, tmp_path: Path) -> None:
    def mutate(records: list[dict[str, Any]]) -> None:
        next(r for r in records if r["kind"] == "diverged")["step"] += 1

    with pytest.raises(ValueError, match="agree"):
        runner.verify_run(_tamper(diverged_run, tmp_path, mutate))
