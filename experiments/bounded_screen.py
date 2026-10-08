"""Multi-seed development screen over the bounded comparison (PDR-0044).

`launch` trains one bounded-comparison run per declared seed, in parallel CPU
processes, into a fresh screen directory. `analyze` verifies every completed
run with the runner's own `verify_run`, reduces each unit to one paired
difference per contrast, and applies the decision rules frozen in
`docs/prereg/bounded-screen-v1.json`. The unit of inference is one training
seed; arms within a seed are matched repeated measures, never extra samples.

Outer/test data is never read: this module has no evaluate path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from experiments.bounded_comparison import ARMS, REPO, git_identity, read_json, strict_json, verify_run
from experiments.bounded_data import file_hash

PREREG = REPO / "docs/prereg/bounded-screen-v1.json"
CONTRASTS = {"scheduled_minus_no_growth": ("scheduled", "no_growth"), "scheduled_minus_static": ("scheduled", "static")}
DESCRIPTIVE_CONTRASTS = {"static_minus_no_growth": ("static", "no_growth")}


def load_prereg(path: Path = PREREG) -> dict[str, Any]:
    prereg = read_json(path)
    for key in ("study", "units", "config", "endpoint", "analysis", "decision"):
        if key not in prereg:
            raise ValueError(f"pre-registration missing {key}")
    return prereg


def unit_seeds(prereg: dict[str, Any]) -> list[int]:
    units = prereg["units"]
    seeds = list(range(units["first_seed"], units["first_seed"] + units["count"]))
    if set(seeds) & set(units["excluded_seeds"]):
        raise ValueError("declared seed range overlaps exploratory seeds")
    return seeds


def train_command(prereg: dict[str, Any], seed: int, output: Path, data_root: Path) -> list[str]:
    config = prereg["config"]
    command = [sys.executable, "-B", "-m", "experiments.bounded_comparison", "train", "--data", "cifar"]
    command += ["--data-root", str(data_root), "--output", str(output), "--seed", str(seed)]
    for name, value in config.items():
        command += ["--" + name.replace("_", "-"), str(value)]
    return command


def launch(root: Path, data_root: Path, workers: int, prereg_path: Path = PREREG) -> dict[str, Any]:
    prereg = load_prereg(prereg_path)
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to launch from a dirty tree: the commit must pin the frozen procedure")
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    root.mkdir(parents=False, exist_ok=False)
    seeds = unit_seeds(prereg)
    launch_record = {
        "study": prereg["study"]["id"],
        "prereg_sha256": file_hash(prereg_path),
        "git": git,
        "seeds": seeds,
        "workers": workers,
        "started_unix": time.time(),
    }
    (root / "launch.json").write_text(strict_json(launch_record) + "\n")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env["PYTHONPATH"] = f"{REPO}:{REPO / 'src'}"

    def run(seed: int) -> dict[str, Any]:
        unit = root / f"seed-{seed}"
        started = time.monotonic()
        with (root / f"seed-{seed}.stdout").open("w") as out, (root / f"seed-{seed}.stderr").open("w") as err:
            code = subprocess.run(
                train_command(prereg, seed, unit, data_root), cwd=REPO, env=env, stdout=out, stderr=err, check=False
            ).returncode
        return {"seed": seed, "returncode": code, "wall_s": time.monotonic() - started}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, seeds))  # No retries: a failed unit is a recorded failure.
    finished = {"units": results, "finished_unix": time.time()}
    (root / "launch-finished.json").write_text(strict_json(finished) + "\n")
    return finished


def late_ce(root: Path, epochs: list[int]) -> dict[str, float]:
    """Mean development CE over the declared late epochs, per arm, from verified evidence."""
    lines = (root / "training.jsonl").read_text().splitlines()
    by_arm: dict[str, dict[int, float]] = {arm: {} for arm in ARMS}
    for line in lines:
        record = json.loads(line)
        if record["kind"] == "epoch":
            by_arm[record["arm"]][record["epoch"]] = float(record["dev"]["ce"])
    return {arm: sum(by_arm[arm][e] for e in epochs) / len(epochs) for arm in ARMS}


def interval(diffs: np.ndarray, level: float) -> dict[str, float]:
    n = len(diffs)
    mean = float(diffs.mean())
    sd = float(diffs.std(ddof=1))
    half = float(stats.t.ppf(0.5 + level / 2, n - 1)) * sd / math.sqrt(n)
    return {"mean": mean, "sd": sd, "lower": mean - half, "upper": mean + half, "half_width": half}


def bootstrap(diffs: np.ndarray, level: float, resamples: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    means = rng.choice(diffs, size=(resamples, len(diffs)), replace=True).mean(axis=1)
    lo, hi = np.quantile(means, [0.5 - level / 2, 0.5 + level / 2])
    return {"lower": float(lo), "upper": float(hi)}


def mde(sd: float, n: int, alpha_two_sided: float, power: float) -> float:
    return float((stats.t.ppf(1 - alpha_two_sided / 2, n - 1) + stats.t.ppf(power, n - 1)) * sd / math.sqrt(n))


def contrast_verdict(ci: dict[str, float], delta: float) -> str:
    """Frozen per-contrast reading; negative differences favour the scheduled graft."""
    if ci["upper"] < -delta:
        return "scheduled_better_beyond_floor"
    if ci["lower"] > 0:
        return "scheduled_worse"
    if ci["upper"] < 0:
        return "scheduled_better_below_floor"
    if -delta < ci["lower"] and ci["upper"] < delta:
        return "equivalent_within_floor"
    return "inconclusive"


def analyze(root: Path, prereg_path: Path = PREREG) -> dict[str, Any]:
    prereg = load_prereg(prereg_path)
    launch_record = read_json(root / "launch.json")
    if launch_record["prereg_sha256"] != file_hash(prereg_path):
        raise ValueError("pre-registration changed after launch")
    out = root / "screen_report.json"
    if out.exists():
        raise FileExistsError("screen report already published; the analysis runs once")
    epochs = prereg["endpoint"]["late_epochs"]
    analysis = prereg["analysis"]
    delta = prereg["decision"]["delta_nats"]
    units: dict[int, dict[str, float]] = {}
    failures: list[dict[str, Any]] = []
    for seed in unit_seeds(prereg):
        unit = root / f"seed-{seed}"
        try:
            verify_run(unit)
            units[seed] = late_ce(unit, epochs)
        except (OSError, ValueError, KeyError) as error:  # Recorded, never silently dropped.
            failures.append({"seed": seed, "error": f"{type(error).__name__}: {error}"})
    n = len(units)
    if len(failures) > prereg["decision"]["max_failed_units"] or n < 3:
        report: dict[str, Any] = {"study": prereg["study"]["id"], "verdict": "instrument_failure", "failures": failures, "n_units": n}
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return report
    seeds = sorted(units)
    level = 1 - analysis["family_alpha"] / len(CONTRASTS)  # Bonferroni over the co-primary family.
    contrasts: dict[str, Any] = {}
    for name, (a, b) in {**CONTRASTS, **DESCRIPTIVE_CONTRASTS}.items():
        diffs = np.array([units[s][a] - units[s][b] for s in seeds])
        ci = interval(diffs, level)
        entry: dict[str, Any] = {
            "per_unit": dict(zip(map(str, seeds), diffs.tolist(), strict=True)),
            "t_interval": ci,
            "bootstrap_interval": bootstrap(diffs, level, analysis["bootstrap_resamples"], analysis["bootstrap_seed"]),
            "wilcoxon_p": float(stats.wilcoxon(diffs).pvalue) if np.any(diffs != 0) else 1.0,
            "fraction_scheduled_or_first_better": float(np.mean(diffs < 0)),
            "worst_decile": float(np.quantile(diffs, 0.9)),
            "mde_at_80_power": mde(ci["sd"], n, analysis["family_alpha"] / len(CONTRASTS), 0.8),
            "role": "co-primary" if name in CONTRASTS else "descriptive",
        }
        if name in CONTRASTS:
            entry["verdict"] = contrast_verdict(ci, delta)
        contrasts[name] = entry
    # The gate asks whether the matched no-op contrast resolves (PDR-0043); the
    # static comparator's own variance is a separate credibility question.
    resolves = contrasts["scheduled_minus_no_growth"]["t_interval"]["half_width"] <= delta
    credible = contrasts["scheduled_minus_static"]["t_interval"]["half_width"] <= delta
    static_wins = contrasts["scheduled_minus_static"]["t_interval"]["lower"] > 0
    report = {
        "study": prereg["study"]["id"],
        "n_units": n,
        "failures": failures,
        "confidence_level": level,
        "delta_nats": delta,
        "arm_late_ce_mean": {arm: float(np.mean([units[s][arm] for s in seeds])) for arm in ARMS},
        "contrasts": contrasts,
        "gate_instrument_resolves": resolves,
        "static_comparison_credible": credible,
        "adr0018_reopen_trigger": static_wins or not resolves or not credible,
        "adr0018_reopen_reasons": [
            reason
            for reason, hit in (("static_wins", static_wins), ("instrument_imprecise", not resolves), ("static_not_credible", not credible))
            if hit
        ],
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    go = sub.add_parser("launch")
    go.add_argument("--root", type=Path, required=True)
    go.add_argument("--data-root", type=Path, required=True)
    go.add_argument("--workers", type=int, required=True)
    look = sub.add_parser("analyze")
    look.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "launch":
        print(strict_json(launch(args.root, args.data_root, args.workers)))
    else:
        print(json.dumps(analyze(args.root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
