"""Rung 4 (PDR-0054): does graft timing, or the training horizon, change the outcome?

Plan: docs/prereg/rung4-timing-horizon.json. One host and seed type; cells differ only in
when the graft germinates (graft_epoch) and how long training runs (epochs). Every cell of
a seed runs on one GPU from one immutable snapshot. Two free replay tests follow:
- no growth and static do not depend on graft timing, so their records match bitwise
  across cells of the same horizon;
- the runner's common future is prefix-stable (bounded_comparison.draw_future), so a
  long-horizon cell replays the same-timing short cell bitwise over their shared epochs.

Co-primaries (one family, Bonferroni over three):
- timing: graft late CE, the plan's early cell minus its late cell, paired by seed;
- horizon: (graft - static) at the long horizon minus at the short one, paired by seed;
- the lever cell: does the graft beat static there?

Timing and horizon are classified beyond_floor, flat or inconclusive by one interval against
their own margins; beyond_floor is split by sign into a favourable lever and an adverse
change. The owner's stop (flat_stop) needs timing flat, every short-horizon cell flat
against the reference cell, horizon flat, and static winning in every cell: an intersection,
so it needs no correction and is the hard reading to reach. Failure rates are reported apart
from finite performance; a graft failure is counted against its cell, never dropped.

Outer/test data is never read: this module has no evaluate path.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import queue
import re
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from experiments.bounded_comparison import ARMS, git_identity, read_json, strict_json, verify_run
from experiments.bounded_data import RunSpec, cifar_source_hashes, file_hash, load_fit_dev, validated_spec
from experiments.bounded_screen import HEX64, binomial_bounds, capture_fraction, interval, make_snapshot, visible_gpus
from experiments.lifecycle_validation import unit_summary

UNIT_FIELDS = ("seed", "data", "outer_size")
CELL_FIELDS = ("graft_epoch", "epochs")
CELL_NAME = re.compile(r"[A-Za-z0-9_-]+")
HOST_ARMS = ("no_growth", "static")
REPORT = "timing_report.json"
PLAN_KEYS = {
    "study",
    "units",
    "cells",
    "config",
    "endpoint",
    "data_identity",
    "criteria",
    "gated_by",
    "linked_plans",
    "predictions",
    "disclosures",
    "deviations",
}
REQUIRED_PLAN_KEYS = PLAN_KEYS - {"predictions", "disclosures", "deviations"}
CRITERIA_KEYS = {
    "delta_timing",
    "delta_horizon",
    "family_alpha",
    "timing_contrast",
    "timing_reference",
    "horizon_contrast",
    "lever_cell",
    "max_graft_failures_per_cell",
    "max_static_failures",
    "max_failed_runs",
    "bootstrap_resamples",
    "bootstrap_seed",
}
DESCRIPTIVE_LEVEL = 0.95


# --- the criteria ---


def classify(ci: dict[str, float], delta: float) -> str:
    """One interval, three outcomes: clearly beyond the margin (either sign), inside it, or neither."""
    if ci["upper"] < -delta or ci["lower"] > delta:
        return "beyond_floor"
    if -delta < ci["lower"] and ci["upper"] < delta:
        return "flat"
    return "inconclusive"


def _late(units: list[dict[str, Any]], cell: str) -> dict[int, dict[str, Any]]:
    return {u["seed"]: u["late_ce"] for u in units if u["cell"] == cell}


def _contrast(diffs: list[float], level: float, delta: float) -> dict[str, Any]:
    if len(diffs) < 3:
        return {"n_pairs": len(diffs), "classification": None, "favourable": None}
    ci = interval(np.asarray(diffs), level)
    kind = classify(ci, delta)
    # Negative favours the earlier graft / the longer horizon: the direction a lever would take.
    return {"n_pairs": len(diffs), **ci, "interval_level": level, "margin": delta, "classification": kind, "favourable": ci["mean"] < 0}


def evaluate(units: list[dict[str, Any]], cells: dict[str, dict[str, int]], criteria: dict[str, Any]) -> dict[str, Any]:
    """The pre-registered reading over per-run summaries (cell, seed, status, late_ce, replay digests)."""
    level = 1 - criteria["family_alpha"] / 3  # Bonferroni over timing, horizon and the lever cell.
    late = {cell: _late(units, cell) for cell in cells}
    seeds = sorted({u["seed"] for u in units})
    short = min(spec["epochs"] for spec in cells.values())

    # Failure rates, apart from performance. Static is identical across cells of one horizon,
    # so it is counted once per (seed, horizon); the graft is counted in every cell.
    divergences: dict[str, Any] = {}
    for cell in cells:
        group = [u for u in units if u["cell"] == cell]
        divergences[cell] = {
            arm: {"diverged": (k := sum(u["status"][arm] == "diverged" for u in group)), "n": len(group), **binomial_bounds(k, len(group))}
            for arm in ARMS
        }
    static_lost = {(u["seed"], cells[u["cell"]]["epochs"]) for u in units if u["status"]["static"] == "diverged"}
    graft_unstable = sorted(c for c in cells if divergences[c]["scheduled"]["diverged"] > criteria["max_graft_failures_per_cell"])

    # Free replay tests: host arms across cells of one horizon; long cells against the
    # same-timing short cell over their shared epochs.
    mismatches: list[list[Any]] = []
    for epochs in sorted({spec["epochs"] for spec in cells.values()}):
        same_horizon = [c for c in cells if cells[c]["epochs"] == epochs]
        for seed in seeds:
            for arm in HOST_ARMS:
                digests = {u["replay_digest"][arm] for u in units if u["seed"] == seed and u["cell"] in same_horizon}
                if len(digests) > 1:
                    mismatches.append(["host_arm", epochs, seed, arm])
    by_run = {(u["cell"], u["seed"]): u for u in units}
    for long_cell, spec in cells.items():
        twins = [c for c in cells if cells[c]["graft_epoch"] == spec["graft_epoch"] and cells[c]["epochs"] == short and c != long_cell]
        if spec["epochs"] == short or not twins:
            continue
        for seed in seeds:
            pair = (by_run.get((long_cell, seed)), by_run.get((twins[0], seed)))
            if pair[0] is not None and pair[1] is not None and pair[0]["prefix_digest"] != pair[1]["prefix_digest"]:
                mismatches.append(["prefix", long_cell, seed])

    def graft(cell: str, seed: int) -> float | None:
        row = late[cell].get(seed)
        return None if row is None else row["scheduled"]

    def gap(cell: str, seed: int) -> float | None:
        row = late[cell].get(seed)
        if row is None or row["scheduled"] is None or row["static"] is None:
            return None
        return float(row["scheduled"] - row["static"])

    def paired(f: Any, a: str, b: str) -> list[float]:
        return [x - y for s in seeds if (x := f(a, s)) is not None and (y := f(b, s)) is not None]

    early, late_cell = criteria["timing_contrast"]
    long_cell, short_cell = criteria["horizon_contrast"]
    reference = criteria["timing_reference"]
    timing = _contrast(paired(graft, early, late_cell), level, criteria["delta_timing"])
    horizon = _contrast(paired(gap, long_cell, short_cell), level, criteria["delta_horizon"])
    # The stop needs every short-horizon cell flat against the reference, not only the endpoints
    # (product review: a timing effect peaking mid-range must not read as flat).
    shape = {
        c: _contrast(paired(graft, c, reference), level, criteria["delta_timing"])
        for c in cells
        if cells[c]["epochs"] == short and c != reference
    }

    per_cell: dict[str, Any] = {}
    for cell in cells:
        per_cell[cell] = {"graft_minus_static": _contrast([g for s in seeds if (g := gap(cell, s)) is not None], level, 0.0)}
        finite = {arm: [row[arm] for row in late[cell].values() if row[arm] is not None] for arm in ARMS}
        per_cell[cell]["finite_late_ce_mean"] = {arm: float(np.mean(v)) if v else None for arm, v in finite.items()}
        per_cell[cell]["finite_n"] = {arm: len(v) for arm, v in finite.items()}
    static_wins = all(per_cell[c]["graft_minus_static"].get("lower", -math.inf) > 0 for c in cells)
    lever = per_cell[criteria["lever_cell"]]["graft_minus_static"]

    report: dict[str, Any] = {
        "confidence_level": level,
        "timing": {"cells": [early, late_cell], **timing},
        "timing_shape": {"reference": reference, "cells": shape},
        "horizon": {"cells": [long_cell, short_cell], **horizon},
        "lever_cell": {
            "cell": criteria["lever_cell"],
            "n_pairs": lever["n_pairs"],
            "graft_beats_static": lever["n_pairs"] >= 3 and lever.get("upper", math.inf) < 0,
        },
        "static_wins_every_cell": static_wins,
        "per_cell": per_cell,
        "divergences": divergences,
        "static_failures": len(static_lost),
        "graft_unstable_cells": graft_unstable,
        "replay": {"mismatches": mismatches},
        "capture_fraction": {
            cell: capture_fraction(
                {s: {a: v for a, v in row.items() if v is not None} for s, row in late[cell].items()},
                criteria["bootstrap_resamples"],
                criteria["bootstrap_seed"],
            )
            for cell in cells
        },
        "timing_slope_secondary": _slope(units, cells, short),
    }
    report["reading"] = _reading(report, criteria)
    return report


def _slope(units: list[dict[str, Any]], cells: dict[str, dict[str, int]], short: int) -> dict[str, Any] | None:
    """Secondary, never gating: per-seed OLS slope of graft late CE on graft_epoch over the short-horizon cells."""
    group = sorted((c for c in cells if cells[c]["epochs"] == short), key=lambda c: cells[c]["graft_epoch"])
    slopes = []
    for seed in sorted({u["seed"] for u in units}):
        pts = [(cells[u["cell"]]["graft_epoch"], u["late_ce"]["scheduled"]) for u in units if u["seed"] == seed and u["cell"] in group]
        pts = [(x, y) for x, y in pts if y is not None]
        if len(pts) == len(group) >= 3:
            x, y = np.array([p[0] for p in pts], dtype=float), np.array([p[1] for p in pts])
            slopes.append(float(np.polyfit(x, y, 1)[0]))
    return {"n": len(slopes), **interval(np.asarray(slopes), DESCRIPTIVE_LEVEL)} if len(slopes) >= 3 else None


def _reading(report: dict[str, Any], criteria: dict[str, Any]) -> str:
    """Precedence: instrument, graft stability, static credibility, lever, adverse change, the stop, otherwise inconclusive."""
    primaries = (report["timing"], report["horizon"], *report["timing_shape"]["cells"].values())
    if report["replay"]["mismatches"] or any(c["classification"] is None for c in primaries) or report["lever_cell"]["n_pairs"] < 3:
        return "instrument_failure"
    if report["graft_unstable_cells"]:
        return "graft_unstable"
    if report["static_failures"] > criteria["max_static_failures"]:
        return "static_not_credible"
    moved = [c for c in (report["timing"], report["horizon"]) if c["classification"] == "beyond_floor"]
    if any(c["favourable"] for c in moved) or report["lever_cell"]["graft_beats_static"]:
        return "lever_found"
    if moved:
        return "changes_adversely"  # The outcome changes, but not in a direction anyone would pull.
    if all(c["classification"] == "flat" for c in primaries) and report["static_wins_every_cell"]:
        return "flat_stop"
    return "inconclusive"


# --- the plan ---


def analysis_module_hash() -> str:
    return file_hash(Path(__file__))


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    units = plan["units"]
    seeds = list(range(units["first_seed"], units["first_seed"] + units["count"]))
    if set(seeds) & set(units["excluded_seeds"]):
        raise ValueError("declared seed range overlaps seeds used by earlier studies")
    return seeds


def expected_spec(plan: dict[str, Any], cell: str, seed: int) -> RunSpec:
    return validated_spec({**RunSpec().__dict__, **plan["config"], **plan["cells"][cell], "seed": seed, "data": "cifar"})


def late_epochs(plan: dict[str, Any], cell: str) -> list[int]:
    horizon, window = plan["cells"][cell]["epochs"], plan["endpoint"]["late_window"]
    return list(range(horizon - window, horizon))


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _pair(value: Any, cells: dict[str, Any], key: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2 or any(c not in cells for c in value) or value[0] == value[1]:
        raise ValueError(f"{key} must name two distinct declared cells")
    return value[0], value[1]


def load_plan(path: Path) -> dict[str, Any]:
    plan = read_json(path)
    if not REQUIRED_PLAN_KEYS <= set(plan) <= PLAN_KEYS:
        raise ValueError(f"plan must state {sorted(REQUIRED_PLAN_KEYS)} and nothing outside {sorted(PLAN_KEYS)}")
    if not isinstance(plan["study"], dict) or not isinstance(plan["study"].get("id"), str):
        raise ValueError("study.id must be a string")
    if plan["gated_by"] is not None or plan["linked_plans"] != []:
        raise ValueError("this study runs ungated and unlinked")
    units = plan["units"]
    if not isinstance(units, dict) or type(units.get("first_seed")) is not int or type(units.get("count")) is not int or units["count"] < 3:
        raise ValueError("units need an int first_seed and a count of at least 3")
    if not isinstance(units.get("excluded_seeds"), list):
        raise ValueError("units must list excluded_seeds")
    unit_seeds(plan)
    required = set(RunSpec.__dataclass_fields__) - set(UNIT_FIELDS) - set(CELL_FIELDS)
    if not isinstance(plan["config"], dict) or set(plan["config"]) != required:
        raise ValueError(f"plan config must state exactly {sorted(required)}")
    cells = plan["cells"]
    if not isinstance(cells, dict) or len(cells) < 2 or any(not isinstance(c, dict) or set(c) != set(CELL_FIELDS) for c in cells.values()):
        raise ValueError(f"cells must each state exactly {list(CELL_FIELDS)}")
    if any(not CELL_NAME.fullmatch(name) for name in cells):
        raise ValueError("cell names must match [A-Za-z0-9_-]+ (they are path components)")
    if len({(c["graft_epoch"], c["epochs"]) for c in cells.values()}) != len(cells):
        raise ValueError("two cells declare the same graft_epoch and horizon")
    endpoint = plan["endpoint"]
    if not isinstance(endpoint, dict) or type(endpoint.get("late_window")) is not int or endpoint["late_window"] < 1:
        raise ValueError("endpoint.late_window must be a positive int")
    for cell, spec in cells.items():
        expected_spec(plan, cell, unit_seeds(plan)[0])  # The graft must fossilize inside each cell's horizon.
        if spec["epochs"] - endpoint["late_window"] <= spec["graft_epoch"]:
            raise ValueError(f"cell {cell}: the late window must start after germination")
    criteria = plan["criteria"]
    if not isinstance(criteria, dict) or set(criteria) != CRITERIA_KEYS:
        raise ValueError(f"criteria must state exactly {sorted(CRITERIA_KEYS)}")
    short = min(c["epochs"] for c in cells.values())
    early, late_cell = _pair(criteria["timing_contrast"], cells, "timing_contrast")
    if (
        cells[early]["epochs"] != short
        or cells[late_cell]["epochs"] != short
        or cells[early]["graft_epoch"] >= cells[late_cell]["graft_epoch"]
    ):
        raise ValueError("timing_contrast must name an earlier then a later graft, both at the short horizon")
    long_cell, short_cell = _pair(criteria["horizon_contrast"], cells, "horizon_contrast")
    if cells[long_cell]["graft_epoch"] != cells[short_cell]["graft_epoch"] or cells[long_cell]["epochs"] <= cells[short_cell]["epochs"]:
        raise ValueError("horizon_contrast must name a longer then a shorter horizon at the same graft timing")
    if criteria["timing_reference"] not in cells or cells[criteria["timing_reference"]]["epochs"] != short:
        raise ValueError("timing_reference must be a short-horizon cell")
    if criteria["lever_cell"] not in cells:
        raise ValueError("lever_cell must be a declared cell")
    if not all(_number(criteria[k]) and criteria[k] > 0 for k in ("delta_timing", "delta_horizon")) or not (
        _number(criteria["family_alpha"]) and 0 < criteria["family_alpha"] < 1
    ):
        raise ValueError("delta_timing and delta_horizon > 0; family_alpha in (0, 1)")
    runs = units["count"] * len(cells)
    for key, bound in (
        ("max_graft_failures_per_cell", units["count"]),
        ("max_static_failures", units["count"] * 2),
        ("max_failed_runs", runs),
    ):
        if type(criteria[key]) is not int or not 0 <= criteria[key] < bound:
            raise ValueError(f"{key} must be an int in [0, {bound})")
    if (
        type(criteria["bootstrap_resamples"]) is not int
        or criteria["bootstrap_resamples"] < 1
        or type(criteria["bootstrap_seed"]) is not int
    ):
        raise ValueError("bootstrap_resamples must be a positive int and bootstrap_seed an int")
    pin = plan["data_identity"]
    if not isinstance(pin, dict) or set(pin) != {"source_files", "fit_sha256", "dev_sha256"}:
        raise ValueError("data_identity must pin source_files, fit_sha256 and dev_sha256")
    files = pin["source_files"]
    hashes = [pin["fit_sha256"], pin["dev_sha256"], *(files.values() if isinstance(files, dict) else [])]
    if not isinstance(files, dict) or not files or not all(isinstance(h, str) and HEX64.fullmatch(h) for h in hashes):
        raise ValueError("data_identity hashes must be sha256 hex digests over a non-empty source_files map")
    return plan


def unit_dir(root: Path, seed: int, cell: str) -> Path:
    return root / "units" / f"seed-{seed}" / cell


def train_command(spec: RunSpec, output: Path, data_root: Path) -> list[str]:
    command = [
        sys.executable,
        "-B",
        "-m",
        "experiments.bounded_comparison",
        "train",
        "--data-root",
        str(data_root),
        "--output",
        str(output),
    ]
    for name, value in dataclasses.asdict(spec).items():
        if name != "seed":
            command += ["--" + name.replace("_", "-"), str(value)]
    return [*command, "--seed", str(spec.seed)]


def run_summary(run: Path, late: list[int], short: int) -> dict[str, Any]:
    """unit_summary plus the digest of every record before the short horizon (the prefix replay test)."""
    records = [json.loads(line) for line in (run / "training.jsonl").read_text().splitlines()]
    prefix = [{k: v for k, v in r.items() if k != "wall_s"} for r in records if r["kind"] == "arm_start" or r["epoch"] < short]
    digest = hashlib.sha256(json.dumps(prefix, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return {**unit_summary(run, late), "prefix_digest": digest}


# --- launch and analysis ---


def _check_inputs(plan: dict[str, Any], data_root: Path) -> None:
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    pin = plan["data_identity"]
    if cifar_source_hashes(data_root) != pin["source_files"]:
        raise RuntimeError("data root does not hold the pinned source files")
    provenance = load_fit_dev(expected_spec(plan, next(iter(plan["cells"])), unit_seeds(plan)[0]), data_root)[4]
    if (provenance["fit_sha256"], provenance["dev_sha256"]) != (pin["fit_sha256"], pin["dev_sha256"]):
        raise RuntimeError("data root does not yield the pinned fit/dev data")


def launch(root: Path, data_root: Path, workers: int, plan_path: Path, resume: bool = False) -> dict[str, Any]:
    """Train every (seed, cell). With resume, an interrupted fleet continues from its own snapshot.

    Resume is allowed only for the same plan, module and commit; finished runs (complete.json
    present) are kept, a partial run directory is set aside, never deleted, and retrained.
    """
    plan = load_plan(plan_path)
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be a positive int")
    gpus: list[int] = []
    if plan["config"]["device"] == "cuda":
        gpus = visible_gpus()
        if not gpus or workers > len(gpus):
            raise ValueError(f"one process per GPU: {workers} workers requested, {len(gpus)} GPUs visible")
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to launch from a dirty tree: the commit must pin the frozen procedure")
    _check_inputs(plan, data_root)
    if resume:
        root = root.resolve()
        record = read_json(root / "launch.json")
        if (record["prereg_sha256"], record["analysis_module_sha256"], record["git"]["commit"]) != (
            file_hash(plan_path),
            analysis_module_hash(),
            git["commit"],
        ):
            raise RuntimeError("resume refused: plan, analysis module or commit differ from the original launch")
        if (root / "launch-finished.json").exists():
            raise RuntimeError("resume refused: the fleet already finished")
        snapshot = Path(record["snapshot"])
        data_root = Path(record["data_root"])
    else:
        root.mkdir(parents=False, exist_ok=False)
        root = root.resolve()
        data_root = data_root.resolve()
        snapshot = make_snapshot(root / "src")
        record = {
            "study": plan["study"]["id"],
            "plan_path": str(plan_path),
            "prereg_sha256": file_hash(plan_path),
            "analysis_module_sha256": analysis_module_hash(),
            "git": git,
            "snapshot": str(snapshot),
            "data_root": str(data_root),
            "gpus": gpus,
            "jobs": unit_seeds(plan),
            "workers": workers,
            "started_unix": time.time(),
        }
        (root / "launch.json").write_text(strict_json(record) + "\n")
    base_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    base_env["PYTHONPATH"] = f"{snapshot}:{snapshot / 'src'}"
    free: queue.Queue[str] = queue.Queue()
    for slot in [str(g) for g in gpus[:workers]] or [""] * workers:
        free.put(slot)
    progress = root / "progress.jsonl"

    def run(seed: int) -> list[dict[str, Any]]:
        gpu = free.get()  # Every cell of a seed on one device: the replay tests never cross devices.
        try:
            results = []
            for cell in plan["cells"]:
                out = unit_dir(root, seed, cell)
                result: dict[str, Any] = {"cell": cell, "seed": seed, "gpu": gpu}
                try:
                    if (out / "complete.json").exists():
                        result.update(returncode=0, resumed=True, wall_s=0.0)
                    else:
                        if out.exists():  # A run interrupted mid-way: keep it for inspection, retrain.
                            out.rename(out.with_name(f"{cell}.partial-{int(time.time())}"))
                        out.parent.mkdir(parents=True, exist_ok=True)
                        started = time.monotonic()
                        with (out.parent / f"{cell}.stdout").open("w") as stdout, (out.parent / f"{cell}.stderr").open("w") as stderr:
                            code = subprocess.run(
                                train_command(expected_spec(plan, cell, seed), out, data_root),
                                cwd=snapshot,
                                env=dict(base_env, CUDA_VISIBLE_DEVICES=gpu),
                                stdout=stdout,
                                stderr=stderr,
                                check=False,
                            ).returncode
                        result.update(returncode=code, wall_s=time.monotonic() - started)
                except Exception as error:  # One cell's launcher error is recorded; the fleet continues.
                    result.update(returncode=None, error=f"{type(error).__name__}: {error}")
                with progress.open("a") as log:
                    log.write(strict_json(result) + "\n")
                results.append(result)
            return results
        finally:
            free.put(gpu)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = [unit for batch in pool.map(run, unit_seeds(plan)) for unit in batch]  # No retries within a launch.
    finished = {"units": results, "finished_unix": time.time()}
    (root / "launch-finished.json").write_text(strict_json(finished) + "\n")
    return finished


def analyze(root: Path, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    plan_sha = file_hash(plan_path)
    launched = read_json(root / "launch.json")
    if not Path(__file__).resolve().is_relative_to(Path(launched["snapshot"]).resolve()):
        raise ValueError(f"analysis must run from the launch snapshot {launched['snapshot']} (PYTHONPATH), not the live checkout")
    if launched["prereg_sha256"] != plan_sha:
        raise ValueError("pre-registration changed after launch")
    if launched["analysis_module_sha256"] != analysis_module_hash():
        raise ValueError("analysis module changed since launch")
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to analyze from a dirty tree")
    out = root / REPORT
    if out.exists():
        raise FileExistsError("report already published; the analysis runs once")
    if not (root / "launch-finished.json").is_file():
        raise ValueError("fleet not finished: launch-finished.json is missing, so analysis would be an interim look")
    planned = {(cell, seed) for seed in unit_seeds(plan) for cell in plan["cells"]}
    finished = {(u["cell"], u["seed"]) for u in read_json(root / "launch-finished.json")["units"]}
    if finished != planned or set(launched["jobs"]) != set(unit_seeds(plan)):
        raise ValueError("launched, finished and planned runs disagree")
    pin = plan["data_identity"]
    short = min(c["epochs"] for c in plan["cells"].values())
    units: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for seed in unit_seeds(plan):
        for cell in plan["cells"]:
            run = unit_dir(root, seed, cell)
            try:
                manifest, _complete, _spec = verify_run(run)
                if manifest["spec"] != expected_spec(plan, cell, seed).__dict__:
                    raise ValueError("unit identity: manifest spec disagrees with the plan")
                if manifest["git"]["commit"] != launched["git"]["commit"]:
                    raise ValueError("unit identity: commit disagrees with the launch")
                data = manifest["data"]
                if (data["source_files"], data["fit_sha256"], data["dev_sha256"]) != (
                    pin["source_files"],
                    pin["fit_sha256"],
                    pin["dev_sha256"],
                ):
                    raise ValueError("unit identity: data differ from the pinned data identity")
                units.append({"cell": cell, "seed": seed, **run_summary(run, late_epochs(plan, cell), short)})
            except Exception as error:  # Every failure is recorded, never silently dropped.
                failures.append(
                    {"cell": cell, "seed": seed, "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()}
                )
    if not units:
        raise RuntimeError(f"no run is analysable ({len(failures)} failures); nothing published")
    report: dict[str, Any] = {
        "study": plan["study"]["id"],
        "plan_sha256": plan_sha,
        "analysis_git": git,
        "analyzed_unix": time.time(),
        "n_runs": len(units),
        "failures": failures,
        **evaluate(units, plan["cells"], plan["criteria"]),
    }
    if len(failures) > plan["criteria"]["max_failed_runs"]:
        report["reading"] = "instrument_failure"  # Criteria above are observed on the analysable runs only.
    out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    go = sub.add_parser("launch")
    go.add_argument("--root", type=Path, required=True)
    go.add_argument("--plan", type=Path, required=True)
    go.add_argument("--data-root", type=Path, required=True)
    go.add_argument("--workers", type=int, required=True)
    go.add_argument("--resume", action="store_true", help="continue an interrupted fleet from its own snapshot")
    look = sub.add_parser("analyze")
    look.add_argument("--root", type=Path, required=True)
    look.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "launch":
        print(strict_json(launch(args.root, args.data_root, args.workers, args.plan, resume=args.resume)))
    else:
        print(json.dumps(analyze(args.root, args.plan), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
