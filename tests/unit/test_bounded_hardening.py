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
