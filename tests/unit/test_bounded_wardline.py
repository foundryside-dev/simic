"""Real bounded ingress and publication contracts; no training or outer reads."""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import torch

from experiments import bounded_comparison as runner
from experiments.bounded_data import RunSpec, file_hash, validated_data, validated_spec


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


def test_marker_dependency_byte_drift_refused(monkeypatch):
    original = file_hash

    def changed_hash(path: Path) -> str:
        if path == runner.MARKER_PACKAGE / "pyproject.toml":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(runner, "file_hash", changed_hash)
    with pytest.raises(RuntimeError, match="official marker dependency source drift"):
        runner.source_identity()


@pytest.fixture(scope="module")
def wardline_bin() -> str:
    binary = os.environ.get("WARDLINE_BIN") or shutil.which("wardline")
    if not binary:
        pytest.skip("set WARDLINE_BIN to run the official local Wardline integration witnesses")
    if not Path(binary).is_file():
        pytest.fail("configured Wardline binary is missing")
    return binary


def copy_actual_modules(root: Path) -> None:
    (root / "experiments").mkdir(parents=True)
    for name in ("__init__.py", "bounded_comparison.py", "bounded_data.py", "kernel_demo.py"):
        shutil.copyfile(runner.REPO / "experiments" / name, root / "experiments" / name)
    (root / "weft.toml").write_text('[wardline]\nsource_roots = ["experiments"]\n')


def scan_copy(binary: str, root: Path) -> tuple[subprocess.CompletedProcess[str], list[dict[str, Any]]]:
    report = root / "findings.jsonl"
    result = subprocess.run(
        [
            binary,
            "scan",
            str(root),
            "--fail-on",
            "ERROR",
            "--fail-on-inert",
            "--fail-on-unanalyzed",
            "--local-only",
            "--format",
            "jsonl",
            "--output",
            str(report),
            "--cache-dir",
            str(root / "cache"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert report.is_file(), result.stderr
    return result, [json.loads(line) for line in report.read_text().splitlines()]


def test_official_scanner_accepts_actual_boundaries_and_lists_qualnames(wardline_bin, tmp_path):
    copy_actual_modules(tmp_path)
    result, findings = scan_copy(wardline_bin, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 recognized trust boundaries" in result.stderr + result.stdout
    assert not [row for row in findings if row["severity"] == "ERROR"]
    coverage = subprocess.run(
        [wardline_bin, "decorator-coverage", str(tmp_path), "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env={key: value for key, value in os.environ.items() if key not in ("WARDLINE_LOOMWEAVE_URL", "WARDLINE_FILIGREE_URL")},
    )
    rows = json.loads(coverage.stdout)["rows"]
    expected = {
        "experiments.bounded_comparison." + name
        for name in (
            "_read_json_text",
            "read_json",
            "_read_training_lines",
            "verify_run",
            "_read_checkpoint",
            "restore_checkpoint",
            "evaluation_record",
            "publish_evaluation",
            "parse_arguments",
        )
    } | {"experiments.bounded_data." + name for name in ("validated_spec", "validated_data", "_read_cifar", "load_fit_dev", "load_outer")}
    assert {row["qualname"] for row in rows} == expected
    assert all(row["verdict"] == "clean" for row in rows)


def test_scanner_rejects_removed_actual_data_validation(wardline_bin, tmp_path):
    copy_actual_modules(tmp_path)
    source = tmp_path / "experiments/bounded_data.py"
    text = source.read_text()
    check = "    validate_data(x, y, n)\n    return x, y\n"
    assert text.count(check) == 1
    source.write_text(text.replace(check, "    return x, y\n"))
    result, findings = scan_copy(wardline_bin, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert any(
        row["rule_id"] == "PY-WL-102" and row["qualname"] == "experiments.bounded_data.validated_data" and row["severity"] == "ERROR"
        for row in findings
    )


def test_scanner_rejects_actual_evaluator_bypassing_verification(wardline_bin, tmp_path):
    copy_actual_modules(tmp_path)
    source = tmp_path / "experiments/bounded_comparison.py"
    text = source.read_text()
    tree = ast.parse(text)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "evaluate")
    lines = text.splitlines(keepends=True)
    assert function.end_lineno is not None
    lines[function.body[0].lineno - 1 : function.end_lineno] = [
        '    return publish_evaluation(root, _read_json_text(root / "manifest.json"))\n'
    ]
    source.write_text("".join(lines))
    result, findings = scan_copy(wardline_bin, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert any(
        row["rule_id"] == "PY-WL-105" and row["qualname"] == "experiments.bounded_comparison.evaluate" and row["severity"] == "ERROR"
        for row in findings
    )
