"""Runtime refusal contracts at the bounded comparison's trust seams.

Restored from the retired Wardline witness module (c40972d): these tests never
needed the scanner. They are the only direct coverage of the refusal paths of
validated_spec, validated_data, evaluation_record and publish_evaluation.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import Any

import pytest
import torch

from experiments import bounded_comparison as runner
from experiments.bounded_data import RunSpec, validated_data, validated_spec


@pytest.mark.parametrize("changes", [{"epochs": 6}, {"train_size": True}, {"tau": float("inf")}])
def test_returning_spec_boundary_rejects_invalid_contract(changes):
    with pytest.raises(ValueError):
        validated_spec(dataclasses.asdict(dataclasses.replace(RunSpec(), **changes)))


@pytest.mark.parametrize("invalid", ["dtype", "shape", "label", "count"])
def test_returning_data_boundary_retains_real_rejection(invalid):
    x = torch.zeros((2, 3, 32, 32), dtype=torch.uint8)
    y = torch.tensor([0, 9], dtype=torch.int64)
    if invalid == "dtype":
        x = x.float()
    elif invalid == "shape":
        x = x[:, :, :31]
    elif invalid == "label":
        y[1] = 10
    with pytest.raises(ValueError):
        validated_data(x, y, 3 if invalid == "count" else 2)


def record_arguments() -> list[Any]:
    spec = RunSpec()
    score = {"ce": 1.0, "accuracy": 0.5, "examples": spec.outer_size}
    return [
        ({}, {"artifacts": {"manifest.json": "a" * 64}}, spec),
        {"outer_sha256": "b" * 64, "outer_source_files": {}, "size": spec.outer_size},
        {arm: copy.deepcopy(score) for arm in runner.ARMS},
        copy.deepcopy(score),
        0.1,
        "c" * 64,
    ]


@pytest.mark.parametrize("invalid", ["missing_arm", "nan", "count", "boolean", "identity", "negative_time"])
def test_evaluation_producer_refuses_incomplete_measured_evidence(invalid):
    args = record_arguments()
    if invalid == "missing_arm":
        del args[2]["static"]
    elif invalid == "nan":
        args[2]["static"]["ce"] = float("nan")
    elif invalid == "count":
        args[2]["static"]["examples"] -= 1
    elif invalid == "boolean":
        args[3]["accuracy"] = True
    elif invalid == "identity":
        args[1]["outer_sha256"] = "not-a-hash"
    else:
        args[4] = -1.0
    with pytest.raises(ValueError):
        runner.evaluation_record(*args)


def test_validated_record_reaches_actual_exclusive_publisher(tmp_path):
    record = runner.evaluation_record(*record_arguments())
    assert record["superiority_established"] is False
    assert runner.publish_evaluation(tmp_path, record) is record
    assert runner.read_json(tmp_path / "outer_evaluation.json") == record
    with pytest.raises(FileExistsError):
        runner.publish_evaluation(tmp_path, record)
