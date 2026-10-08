"""Multi-seed development screens over the bounded comparison (PDR-0044 onward).

`launch` trains one bounded-comparison run per declared seed, in parallel CPU
processes, into a fresh screen directory. `analyze` verifies every completed
run with the runner's own `verify_run`, reduces each unit to one paired
difference per plan-declared contrast, and applies the plan's named reading
rule. The unit of inference is one training seed; arms within a seed are
matched repeated measures, never extra samples.

Plans live in `docs/prereg/`. Screen v1 (`bounded-screen-v1.json`) predates
this schema and is kept unchanged as the historical record.

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
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from experiments.bounded_comparison import ARMS, REPO, git_identity, read_json, strict_json, verify_run
from experiments.bounded_data import file_hash

COST_FIELDS = ("optimizer_parameter_steps", "seed_train_examples", "calibration_examples")


def load_plan(path: Path) -> dict[str, Any]:
    plan = read_json(path)
    for key in ("study", "units", "config", "endpoint", "analysis", "decision"):
        if key not in plan:
            raise ValueError(f"plan missing {key}")
    contrasts = plan["analysis"].get("contrasts")
    if not isinstance(contrasts, dict) or not contrasts:
        raise ValueError("plan must declare contrasts")
    for name, contrast in contrasts.items():
        arms = contrast.get("arms")
        if not isinstance(arms, list) or len(arms) != 2 or any(arm not in ARMS for arm in arms) or arms[0] == arms[1]:
            raise ValueError(f"contrast {name} must name two distinct known arms")
        if contrast.get("role") not in ("co-primary", "descriptive"):
            raise ValueError(f"contrast {name} needs role co-primary or descriptive")
    if plan["decision"].get("reading_rule") not in READING_RULES:
        raise ValueError(f"unknown reading rule; known: {sorted(READING_RULES)}")
    return plan


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    units = plan["units"]
    seeds = list(range(units["first_seed"], units["first_seed"] + units["count"]))
    if set(seeds) & set(units["excluded_seeds"]):
        raise ValueError("declared seed range overlaps exploratory seeds")
    return seeds


def train_command(plan: dict[str, Any], seed: int, output: Path, data_root: Path) -> list[str]:
    command = [sys.executable, "-B", "-m", "experiments.bounded_comparison", "train", "--data", "cifar"]
    command += ["--data-root", str(data_root), "--output", str(output), "--seed", str(seed)]
    for name, value in plan["config"].items():
        command += ["--" + name.replace("_", "-"), str(value)]
    return command


def launch(root: Path, data_root: Path, workers: int, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to launch from a dirty tree: the commit must pin the frozen procedure")
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    root.mkdir(parents=False, exist_ok=False)
    seeds = unit_seeds(plan)
    launch_record = {
        "study": plan["study"]["id"],
        "plan_path": str(plan_path),
        "prereg_sha256": file_hash(plan_path),
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
                train_command(plan, seed, unit, data_root), cwd=REPO, env=env, stdout=out, stderr=err, check=False
            ).returncode
        return {"seed": seed, "returncode": code, "wall_s": time.monotonic() - started}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, seeds))  # No retries: a failed unit is a recorded failure.
    finished = {"units": results, "finished_unix": time.time()}
    (root / "launch-finished.json").write_text(strict_json(finished) + "\n")
    return finished


def late_ce(root: Path, epochs: list[int]) -> dict[str, float]:
    """Mean development CE over the declared late epochs, per arm, from verified evidence."""
    by_arm: dict[str, dict[int, float]] = {arm: {} for arm in ARMS}
    for line in (root / "training.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record["kind"] == "epoch":
            by_arm[record["arm"]][record["epoch"]] = float(record["dev"]["ce"])
    return {arm: sum(by_arm[arm][e] for e in epochs) / len(epochs) for arm in ARMS}


def unit_costs(root: Path) -> dict[str, dict[str, float]]:
    """Per-arm work from the verified completion record."""
    summaries = read_json(root / "complete.json")["summaries"]
    return {
        arm: {**{name: float(summaries[arm]["costs"][name]) for name in COST_FIELDS}, "wall_s": float(summaries[arm]["wall_s"])}
        for arm in ARMS
    }


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
    """Smallest true difference from zero detected with the given power."""
    return float((stats.t.ppf(1 - alpha_two_sided / 2, n - 1) + stats.t.ppf(power, n - 1)) * sd / math.sqrt(n))


def effect_for_progress(sd: float, n: int, alpha_two_sided: float, power: float, delta: float) -> float:
    """True benefit needed for the whole interval to clear -delta with the given power (audit F1)."""
    return delta + mde(sd, n, alpha_two_sided, power)


def contrast_verdict(ci: dict[str, float], delta: float) -> str:
    """Frozen per-contrast reading, checked in this order; negative differences favour the first arm."""
    if ci["upper"] < -delta:
        return "first_better_beyond_floor"
    if ci["lower"] > 0:
        return "first_worse"
    if ci["upper"] < 0:
        return "first_better_below_floor"
    if -delta < ci["lower"] and ci["upper"] < delta:
        return "equivalent_within_floor"
    return "inconclusive"


def reading_screen_v1(report: dict[str, Any]) -> str:
    """Screen v1 readings with explicit precedence: imprecision, then static wins, then credibility, then value."""
    delta = report["delta_nats"]
    vs_none = report["contrasts"]["scheduled_minus_no_growth"]
    vs_static = report["contrasts"]["scheduled_minus_static"]
    report["gate_instrument_resolves"] = vs_none["t_interval"]["half_width"] <= delta
    report["static_comparison_credible"] = vs_static["t_interval"]["half_width"] <= delta
    if not report["gate_instrument_resolves"]:
        return "reopen_instrument_imprecise"
    if vs_static["t_interval"]["lower"] > 0:
        return "reopen_static_wins"
    if not report["static_comparison_credible"]:
        return "reopen_static_not_credible"
    if vs_none["verdict"] == "first_better_beyond_floor":
        return "progress"
    return "reopen_no_value"


READING_RULES: dict[str, Callable[[dict[str, Any]], str]] = {"bounded-screen-v1": reading_screen_v1}


def analyze(root: Path, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    plan_sha = file_hash(plan_path)
    if read_json(root / "launch.json")["prereg_sha256"] != plan_sha:
        raise ValueError("pre-registration changed after launch")
    out = root / "screen_report.json"
    if out.exists():
        raise FileExistsError("screen report already published; the analysis runs once")
    epochs = plan["endpoint"]["late_epochs"]
    analysis = plan["analysis"]
    decision = plan["decision"]
    delta = decision["delta_nats"]
    units: dict[int, dict[str, float]] = {}
    costs: dict[int, dict[str, dict[str, float]]] = {}
    failures: list[dict[str, Any]] = []
    for seed in unit_seeds(plan):
        unit = root / f"seed-{seed}"
        try:
            verify_run(unit)
            units[seed] = late_ce(unit, epochs)
            costs[seed] = unit_costs(unit)
        except Exception as error:  # Any unit failure is recorded, never silently dropped (audit F8).
            failures.append({"seed": seed, "error": f"{type(error).__name__}: {error}"})
    report: dict[str, Any] = {
        "study": plan["study"]["id"],
        "plan_sha256": plan_sha,
        "analysis_git": git_identity(),
        "analyzed_unix": time.time(),
        "n_units": len(units),
        "failures": failures,
        "delta_nats": delta,
        "reading_rule": decision["reading_rule"],
    }
    if len(failures) > decision["max_failed_units"] or len(units) < 3:
        report["reading"] = "instrument_failure"
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return report
    seeds = sorted(units)
    n = len(seeds)
    primaries = [name for name, c in analysis["contrasts"].items() if c["role"] == "co-primary"]
    alpha_each = analysis["family_alpha"] / len(primaries)  # Bonferroni over the co-primary family.
    level = 1 - alpha_each
    contrasts: dict[str, Any] = {}
    for name, contrast in analysis["contrasts"].items():
        first, second = contrast["arms"]
        diffs = np.array([units[s][first] - units[s][second] for s in seeds])
        ci = interval(diffs, level)
        contrasts[name] = {
            "arms": [first, second],
            "role": contrast["role"],
            "per_unit": dict(zip(map(str, seeds), diffs.tolist(), strict=True)),
            "t_interval": ci,
            "bootstrap_interval": bootstrap(diffs, level, analysis["bootstrap_resamples"], analysis["bootstrap_seed"]),
            "wilcoxon_p": float(stats.wilcoxon(diffs).pvalue) if np.any(diffs != 0) else 1.0,
            "fraction_first_better": float(np.mean(diffs < 0)),
            "worst_decile": float(np.quantile(diffs, 0.9)),
            "mde_vs_zero_80pct": mde(ci["sd"], n, alpha_each, 0.8),
            "effect_for_80pct_progress": effect_for_progress(ci["sd"], n, alpha_each, 0.8, delta),
            "verdict": contrast_verdict(ci, delta),
        }
    report.update(
        {
            "confidence_level": level,
            "arm_late_ce_mean": {arm: float(np.mean([units[s][arm] for s in seeds])) for arm in ARMS},
            "arm_costs_mean": {
                arm: {k: float(np.mean([costs[s][arm][k] for s in seeds])) for k in (*COST_FIELDS, "wall_s")} for arm in ARMS
            },
            "contrasts": contrasts,
        }
    )
    report["reading"] = READING_RULES[decision["reading_rule"]](report)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    go = sub.add_parser("launch")
    go.add_argument("--root", type=Path, required=True)
    go.add_argument("--plan", type=Path, required=True)
    go.add_argument("--data-root", type=Path, required=True)
    go.add_argument("--workers", type=int, required=True)
    look = sub.add_parser("analyze")
    look.add_argument("--root", type=Path, required=True)
    look.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "launch":
        print(strict_json(launch(args.root, args.data_root, args.workers, args.plan)))
    else:
        print(json.dumps(analyze(args.root, args.plan), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
