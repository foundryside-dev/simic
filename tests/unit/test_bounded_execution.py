"""Execution profile: GPU device support (Academy-exact per SKU) and immutable source snapshots.

GPU probe: docs/results/2026-10-08-gpu-determinism-probe.md. Independent review (2026-10-08):
execution must run from pinned, immutable inputs, never the live checkout.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import torch

from experiments import bounded_comparison as runner
from experiments import bounded_screen as screen
from experiments.bounded_data import RunSpec, validated_spec

CUDA = pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device visible")


@pytest.mark.parametrize("device", ["cuda:1", "gpu", "mps", 0])
def test_spec_refuses_device_other_than_cpu_or_cuda(device: Any) -> None:
    with pytest.raises(ValueError):
        validated_spec(dataclasses.asdict(dataclasses.replace(RunSpec(), device=device)))


def test_cpu_profile_is_recorded_as_cpu() -> None:
    spec = RunSpec()
    runner.configure(spec)
    assert runner.runtime(spec)["device"] == "cpu"


@CUDA
def test_gpu_unit_trains_verifies_and_replays_bitwise(tmp_path: Path) -> None:
    spec = RunSpec(epochs=7, device="cuda", lifecycle="v2")
    first, second = tmp_path / "a", tmp_path / "b"
    runner.train(spec, first)
    runner.train(spec, second)
    manifest, _complete, _ = runner.verify_run(first)
    assert manifest["runtime"]["device"] == "cuda" and manifest["runtime"]["gpu_name"]

    def states(root: Path) -> list[str]:
        records = [json.loads(line) for line in (root / "training.jsonl").read_text().splitlines()]
        return [r["training_state_sha256"] for r in records if r["kind"] == "epoch"]

    assert states(first) == states(second)


def test_snapshot_is_an_immutable_copy_of_head_with_its_identity(tmp_path: Path) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=runner.REPO, capture_output=True, text=True, check=True).stdout.strip()
    snapshot = screen.make_snapshot(tmp_path / "src")
    assert json.loads((snapshot / "SNAPSHOT.json").read_text())["commit"] == head
    committed = subprocess.run(
        ["git", "show", "HEAD:experiments/bounded_comparison.py"], cwd=runner.REPO, capture_output=True, check=True
    ).stdout
    assert (snapshot / "experiments" / "bounded_comparison.py").read_bytes() == committed
    assert runner.git_identity(snapshot) == {"commit": head, "status": ""}


def test_launch_runs_every_unit_from_the_snapshot_with_one_gpu_each(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import copy

    from tests.unit.test_bounded_screen import BASE_PLAN, write_plan

    plan = copy.deepcopy(BASE_PLAN)
    plan["units"]["count"] = 4
    plan["config"]["device"] = "cuda"
    path = write_plan(tmp_path, plan)
    snapshot_dir = tmp_path / "fake-snapshot"
    snapshot_dir.mkdir()
    monkeypatch.setattr(screen, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "make_snapshot", lambda dest: snapshot_dir)
    monkeypatch.setattr(screen, "visible_gpus", lambda: [0, 1])
    seen: list[dict[str, str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        seen.append({"cwd": str(kwargs["cwd"]), "gpu": kwargs["env"]["CUDA_VISIBLE_DEVICES"], "pythonpath": kwargs["env"]["PYTHONPATH"]})
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("experiments.bounded_screen.subprocess.run", fake_run)
    screen.launch(tmp_path / "screen", tmp_path, 2, path)
    assert len(seen) == 4
    assert {s["cwd"] for s in seen} == {str(snapshot_dir)}
    assert all(s["pythonpath"].startswith(str(snapshot_dir)) for s in seen)
    assert {s["gpu"] for s in seen} <= {"0", "1"}
    record = json.loads((tmp_path / "screen" / "launch.json").read_text())
    assert record["snapshot"] == str(snapshot_dir)


def test_launch_refuses_more_gpu_workers_than_gpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import copy

    from tests.unit.test_bounded_screen import BASE_PLAN, write_plan

    plan = copy.deepcopy(BASE_PLAN)
    plan["config"]["device"] = "cuda"
    monkeypatch.setattr(screen, "git_identity", lambda *a: {"commit": "x", "status": ""})
    monkeypatch.setattr(screen, "visible_gpus", lambda: [0, 1])
    with pytest.raises(ValueError, match="one process per GPU"):
        screen.launch(tmp_path / "screen", tmp_path, 3, write_plan(tmp_path, plan))


def test_analysis_refuses_to_run_outside_the_launch_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.unit.test_bounded_screen import fake_screen, unit_values

    root, plan = fake_screen(tmp_path, monkeypatch, unit_values(0.0))
    launch = json.loads((root / "launch.json").read_text())
    launch["snapshot"] = str(tmp_path / "elsewhere")
    (root / "launch.json").write_text(json.dumps(launch))
    with pytest.raises(ValueError, match="snapshot"):
        screen.analyze(root, plan)
