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
import itertools
import json
import math
import os
import queue
import re
import subprocess
import sys
import time
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from experiments.bounded_comparison import ARMS, REPO, git_identity, read_json, strict_json, verify_run
from experiments.bounded_data import RunSpec, cifar_source_hashes, file_hash, load_fit_dev, validated_spec

COST_FIELDS = ("optimizer_parameter_steps", "seed_train_examples", "calibration_examples")
DESCRIPTIVE_LEVEL = 0.95
UNIT_FIELDS = ("seed", "data", "outer_size")  # Set per unit or fixed by the screen, never by plan config.
PLAN_KEYS = {
    "study",
    "units",
    "config",
    "endpoint",
    "analysis",
    "decision",
    "linked_plans",
    "gated_by",
    "predictions",
    "disclosures",
    "deviations",
    "data_identity",
}
# fail_unit: a unit whose contrast arm diverged counts as a failed unit (PDR-0047).
# per_contrast: a unit enters each contrast iff both its arms finished; divergences are counted
# per arm and never fail the unit (PDR-0052: a static failure must not drop the no-growth pair).
DIVERGED_ARM_POLICIES = ("fail_unit", "per_contrast")
DATA_IDENTITY_KEYS = {"source_files", "fit_sha256", "dev_sha256"}
HEX64 = re.compile(r"[0-9a-f]{64}")


def analysis_module_hash() -> str:
    """The reading rules live in this module; launch pins it and analysis refuses drift (audit F-A)."""
    return file_hash(Path(__file__))


def load_plan(path: Path) -> dict[str, Any]:
    plan = read_json(path)
    for key in ("study", "units", "config", "endpoint", "analysis", "decision"):
        if key not in plan:
            raise ValueError(f"plan missing {key}")
    if not set(plan) <= PLAN_KEYS:
        raise ValueError(f"unknown plan keys {sorted(set(plan) - PLAN_KEYS)}")
    validate_plan_fields(plan)
    contrasts = plan["analysis"].get("contrasts")
    if not isinstance(contrasts, dict) or not contrasts:
        raise ValueError("plan must declare contrasts")
    for name, contrast in contrasts.items():
        arms = contrast.get("arms")
        if not isinstance(arms, list) or len(arms) != 2 or any(arm not in ARMS for arm in arms) or arms[0] == arms[1]:
            raise ValueError(f"contrast {name} must name two distinct known arms")
        if contrast.get("role") not in ("co-primary", "descriptive"):
            raise ValueError(f"contrast {name} needs role co-primary or descriptive")
    if not any(c["role"] == "co-primary" for c in contrasts.values()):
        raise ValueError("plan must declare at least one co-primary contrast")
    rule = READING_RULES.get(plan["decision"].get("reading_rule"))
    if rule is None:
        raise ValueError(f"unknown reading rule; known: {sorted(READING_RULES)}")
    for key in rule.required_decision:
        cap = plan["decision"].get(key)
        if type(cap) is not int or not 0 <= cap < plan["units"]["count"]:
            raise ValueError(f"reading rule {plan['decision']['reading_rule']} requires decision.{key} as an int in [0, units.count)")
    if rule.policy is not None and plan["decision"]["diverged_arm_policy"] != rule.policy:
        raise ValueError(f"reading rule {plan['decision']['reading_rule']} requires diverged_arm_policy {rule.policy}")
    if "data_identity" in plan:
        pin = plan["data_identity"]
        if not isinstance(pin, dict) or set(pin) != DATA_IDENTITY_KEYS:
            raise ValueError(f"data_identity must pin exactly {sorted(DATA_IDENTITY_KEYS)}")
        files = pin["source_files"]
        hashes = [pin["fit_sha256"], pin["dev_sha256"], *(files.values() if isinstance(files, dict) else [])]
        if not isinstance(files, dict) or not files or not all(isinstance(h, str) and HEX64.fullmatch(h) for h in hashes):
            raise ValueError("data_identity hashes must be sha256 hex digests over a non-empty source_files map")
    for name, arms in rule.required_coprimary.items():
        declared = contrasts.get(name, {})
        if declared.get("role") != "co-primary" or declared.get("arms") != list(arms):
            raise ValueError(f"reading rule requires contrast {name} as co-primary with arms {list(arms)} in that order")
    config = plan["config"]
    required = {f for f in RunSpec.__dataclass_fields__ if f not in UNIT_FIELDS}
    if not isinstance(config, dict) or set(config) != required:  # Flush F5: no silent RunSpec defaults.
        raise ValueError(f"plan config must state exactly {sorted(required)}")
    validated_spec({**RunSpec().__dict__, **config, "data": "cifar"})
    late = plan["endpoint"]["late_epochs"]
    if not late or any(type(e) is not int or not 0 <= e < plan["config"]["epochs"] for e in late):
        raise ValueError("late_epochs must be epochs within the configured horizon")
    return plan


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_plan_fields(plan: dict[str, Any]) -> None:
    """Numeric and structural plan fields are checked at load, before any unit runs (sweep C-1)."""
    analysis, decision = plan["analysis"], plan["decision"]
    if not _number(analysis.get("family_alpha")) or not 0 < analysis["family_alpha"] < 1:
        raise ValueError("family_alpha must be in (0, 1)")
    if (
        type(analysis.get("bootstrap_resamples")) is not int
        or analysis["bootstrap_resamples"] < 1
        or type(analysis.get("bootstrap_seed")) is not int
    ):
        raise ValueError("bootstrap_resamples must be a positive int and bootstrap_seed an int")
    if not _number(decision.get("delta_nats")) or decision["delta_nats"] <= 0:
        raise ValueError("delta_nats must be positive")
    if type(decision.get("max_failed_units")) is not int or decision["max_failed_units"] < 0:
        raise ValueError("max_failed_units must be a non-negative int")
    if decision.get("diverged_arm_policy") not in DIVERGED_ARM_POLICIES:
        raise ValueError(f"diverged_arm_policy must be one of {DIVERGED_ARM_POLICIES}")
    late = plan["endpoint"].get("late_epochs")
    if not isinstance(late, list) or len(set(late)) != len(late):
        raise ValueError("late_epochs must be a list of distinct epochs")
    if "linked_plans" not in plan:  # Explicit, even when empty: absence must not mean "no links" (review 60683c4).
        raise ValueError("plan must declare linked_plans (use [] for none)")
    linked = plan["linked_plans"]
    if not isinstance(linked, list) or any(not Path(p).is_file() for p in linked):
        raise ValueError("linked_plans must list existing plan files")
    if "gated_by" not in plan:  # Flush F6: absence must not mean "ungated".
        raise ValueError("plan must declare gated_by (null for an ungated study)")
    gate = plan["gated_by"]
    if gate is not None and (
        not isinstance(gate, dict) or set(gate) != {"root", "plan", "reading"} or not all(isinstance(v, str) for v in gate.values())
    ):
        raise ValueError("gated_by must name root, plan and reading")


def expected_spec(plan: dict[str, Any], seed: int) -> RunSpec:
    """The exact specification every unit of this plan must have been trained under (sweep B-1)."""
    return validated_spec({**RunSpec().__dict__, **plan["config"], "seed": seed, "data": "cifar"})


def check_gate(plan: dict[str, Any], plan_path: Path) -> None:
    """A gated study launches only on its gate's published reading, and only as the gate pinned it (sweep E-2).

    The pin is matched by resolved path and content hash, so path spelling cannot cause a false refusal.
    """
    gate = plan["gated_by"]
    if gate is None:
        return
    report = read_json(Path(gate["root"]) / "screen_report.json")
    if report["reading"] != gate["reading"]:
        raise RuntimeError(f"gate not satisfied: {gate['root']} read {report['reading']!r}, not {gate['reading']!r}")
    pinned = read_json(Path(gate["root"]) / "launch.json")["linked_plan_sha256"]
    ours = (plan_path.resolve(), file_hash(plan_path))
    if ours not in {(Path(path).resolve(), sha) for path, sha in pinned.items()}:
        raise RuntimeError("gate not satisfied: this plan is not the one the gating study pinned")


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    units = plan["units"]
    seeds = list(range(units["first_seed"], units["first_seed"] + units["count"]))
    if set(seeds) & set(units["excluded_seeds"]):
        raise ValueError("declared seed range overlaps exploratory seeds")
    return seeds


def train_command(plan: dict[str, Any], seed: int, output: Path, data_root: Path) -> list[str]:
    command = [sys.executable, "-B", "-m", "experiments.bounded_comparison", "train", "--data", "cifar"]
    command += ["--data-root", str(data_root), "--output", str(output)]
    for name, value in plan["config"].items():
        command += ["--" + name.replace("_", "-"), str(value)]
    return [*command, "--seed", str(seed)]  # Last, so nothing can override the unit's seed.


def visible_gpus() -> list[int]:
    import torch

    return list(range(torch.cuda.device_count()))


def make_snapshot(dest: Path) -> Path:
    """An immutable copy of HEAD's tracked files, with its identity (independent review, 2026-10-08).

    Units train, and the analysis runs, from this copy, so edits to the live checkout can
    neither change a running fleet nor fail its verification.
    """
    dest.mkdir(parents=False, exist_ok=False)
    head = git_identity()["commit"]
    archive = subprocess.run(["git", "archive", "--format=tar", head], cwd=REPO, check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    (dest / "SNAPSHOT.json").write_text(strict_json({"commit": head, "created_unix": time.time()}) + "\n")
    return dest


def launch(root: Path, data_root: Path, workers: int, plan_path: Path) -> dict[str, Any]:
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
    check_gate(plan, plan_path)
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    if "data_identity" in plan:
        pin = plan["data_identity"]
        if cifar_source_hashes(data_root) != pin["source_files"]:
            raise RuntimeError("data root does not hold the pinned source files")
        # The fit/dev selection is checked too, before any GPU time is spent (code review, PDR-0052).
        provenance = load_fit_dev(expected_spec(plan, unit_seeds(plan)[0]), data_root)[4]
        if (provenance["fit_sha256"], provenance["dev_sha256"]) != (pin["fit_sha256"], pin["dev_sha256"]):
            raise RuntimeError("data root does not yield the pinned fit/dev data")
    root.mkdir(parents=False, exist_ok=False)
    root = root.resolve()
    data_root = data_root.resolve()
    snapshot = make_snapshot(root / "src")
    seeds = unit_seeds(plan)
    launch_record = {
        "study": plan["study"]["id"],
        "plan_path": str(plan_path),
        "prereg_sha256": file_hash(plan_path),
        "analysis_module_sha256": analysis_module_hash(),
        # Plans that must stay frozen while this study runs, e.g. a graft study gated on it (PDR-0046 F7).
        "linked_plan_sha256": {str(Path(p)): file_hash(Path(p)) for p in plan["linked_plans"]},
        "git": git,
        "snapshot": str(snapshot),
        "gpus": gpus,
        "seeds": seeds,
        "workers": workers,
        "started_unix": time.time(),
    }
    (root / "launch.json").write_text(strict_json(launch_record) + "\n")
    base_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    base_env["PYTHONPATH"] = f"{snapshot}:{snapshot / 'src'}"
    free: queue.Queue[str] = queue.Queue()
    for slot in [str(g) for g in gpus] or [""] * workers:  # "" hides every GPU from CPU units.
        free.put(slot)

    def run(seed: int) -> dict[str, Any]:
        unit = root / f"seed-{seed}"
        gpu = free.get()  # One process per GPU: a device is held for the whole unit (GPU probe).
        try:
            env = dict(base_env, CUDA_VISIBLE_DEVICES=gpu)
            started = time.monotonic()
            # The runner prints every arm's summary; the file is sealed so undeclared arms stay unread (PDR-0046 F6).
            with (root / f"seed-{seed}.runner-stdout.sealed").open("w") as out, (root / f"seed-{seed}.stderr").open("w") as err:
                code = subprocess.run(
                    train_command(plan, seed, unit, data_root), cwd=snapshot, env=env, stdout=out, stderr=err, check=False
                ).returncode
            return {"seed": seed, "returncode": code, "wall_s": time.monotonic() - started, "gpu": gpu}
        finally:
            free.put(gpu)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, seeds))  # No retries: a failed unit is a recorded failure.
    finished = {"units": results, "finished_unix": time.time()}
    (root / "launch-finished.json").write_text(strict_json(finished) + "\n")
    return finished


def _dev_ce_by_epoch(root: Path, arms: tuple[str, ...] | list[str]) -> dict[str, dict[int, float]]:
    """Development CE per epoch for the requested arms only.

    Every record is parsed (kind and arm are read), but values are extracted only for
    the requested arms; a sealed arm's metrics are never read into the analysis.
    """
    by_arm: dict[str, dict[int, float]] = {arm: {} for arm in arms}
    for line in (root / "training.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record["kind"] == "epoch" and record["arm"] in by_arm:
            by_arm[record["arm"]][record["epoch"]] = float(record["dev"]["ce"])
    return by_arm


def late_ce(root: Path, epochs: list[int], arms: tuple[str, ...] | list[str]) -> dict[str, float]:
    """Mean development CE over the declared late epochs, per requested arm, from verified evidence."""
    by_arm = _dev_ce_by_epoch(root, arms)
    return {arm: sum(by_arm[arm][e] for e in epochs) / len(epochs) for arm in arms}


def epoch_ce(root: Path, arms: tuple[str, ...] | list[str]) -> dict[str, list[float]]:
    """Development CE at every epoch, per requested arm, from verified evidence."""
    by_arm = _dev_ce_by_epoch(root, arms)
    return {arm: [by_arm[arm][e] for e in sorted(by_arm[arm])] for arm in arms}


def unit_costs(root: Path, arms: tuple[str, ...] | list[str]) -> dict[str, dict[str, float]]:
    """Per-arm work from the verified completion record, for the requested arms."""
    summaries = read_json(root / "complete.json")["summaries"]
    return {
        arm: {**{name: float(summaries[arm]["costs"][name]) for name in COST_FIELDS}, "wall_s": float(summaries[arm]["wall_s"])}
        for arm in arms
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
        return "first_better_floor_not_cleared"
    if -delta < ci["lower"] and ci["upper"] < delta:
        return "equivalent_within_floor"
    return "inconclusive"


def reading_screen_v1(report: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    """Screen v1 readings with explicit precedence: imprecision, then static wins, then credibility, then value."""
    delta = report["delta_nats"]
    vs_none = report["contrasts"]["scheduled_minus_no_growth"]
    vs_static = report["contrasts"]["scheduled_minus_static"]
    gates = {
        "gate_instrument_resolves": vs_none["t_interval"]["half_width"] <= delta,
        "static_comparison_credible": vs_static["t_interval"]["half_width"] <= delta,
    }
    if not gates["gate_instrument_resolves"]:
        return "reopen_instrument_imprecise", gates
    if vs_static["t_interval"]["lower"] > 0:
        return "reopen_static_wins", gates
    if not gates["static_comparison_credible"]:
        return "reopen_static_not_credible", gates
    if vs_none["verdict"] == "first_better_beyond_floor":
        return "progress", gates
    return "reopen_no_value", gates


POSITIVE_CONTROL_READINGS = (
    "control_passes",
    "control_fails_static_worse",
    "control_imprecise",
    "control_fails_below_floor",
    "control_fails_no_effect",
)


def reading_positive_control_v1(report: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    """Detection first: does static capacity beat no growth beyond the floor on this host?"""
    primary = report["contrasts"]["static_minus_no_growth"]
    gates = {"control_precise": primary["t_interval"]["half_width"] <= report["delta_nats"]}
    if primary["verdict"] == "first_better_beyond_floor":
        return "control_passes", gates
    if primary["verdict"] == "first_worse":
        return "control_fails_static_worse", gates
    if not gates["control_precise"]:
        return "control_imprecise", gates
    if primary["verdict"] == "first_better_floor_not_cleared":
        return "control_fails_below_floor", gates  # A real deficit smaller than the floor, not "no effect" (F4).
    return "control_fails_no_effect", gates


GRAFT_CAPTURE_READINGS = (
    "reopen_instrument_imprecise",
    "partial_capture",
    "reopen_static_wins",
    "reopen_static_not_credible",
    "progress",
    "reopen_no_value",
)


def reading_graft_capture_v1(report: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    """Does the graft repair the deficit? Partial repair is named, not swallowed by 'static wins' (PDR-0046 F1)."""
    delta = report["delta_nats"]
    vs_none = report["contrasts"]["scheduled_minus_no_growth"]
    vs_static = report["contrasts"]["scheduled_minus_static"]
    graft_helps = vs_none["verdict"] in ("first_better_beyond_floor", "first_better_floor_not_cleared")
    static_wins = vs_static["t_interval"]["lower"] > 0
    gates = {
        "gate_instrument_resolves": vs_none["t_interval"]["half_width"] <= delta,
        "static_comparison_credible": vs_static["t_interval"]["half_width"] <= delta,
        "graft_beats_no_growth": graft_helps,
        "static_beats_graft": static_wins,
    }
    if not gates["gate_instrument_resolves"]:
        return "reopen_instrument_imprecise", gates
    if static_wins and graft_helps:
        return "partial_capture", gates
    if static_wins:
        return "reopen_static_wins", gates
    if not gates["static_comparison_credible"]:
        return "reopen_static_not_credible", gates
    if vs_none["verdict"] == "first_better_beyond_floor":
        return "progress", gates
    return "reopen_no_value", gates


GRAFT_CAPTURE_V2_READINGS = ("graft_unstable", *GRAFT_CAPTURE_READINGS)


def reading_graft_capture_v2(report: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    """graft-capture-v1's precedence behind two failure gates (PDR-0052).

    The graft's own divergences are counted against it, never dropped. Static divergences
    beyond the cap leave too few static pairs for the static comparison to be trusted.
    """
    diverged = report["diverged_units_by_arm"]
    v1_reading, v1_gates = reading_graft_capture_v1(report)  # Published whatever the gates decide (review).
    gates = {
        "graft_failures_within_cap": diverged["scheduled"] <= report["max_graft_failures"],
        "static_failures_within_cap": diverged["static"] <= report["max_static_failures"],
        **v1_gates,
    }
    if not gates["graft_failures_within_cap"]:
        return "graft_unstable", gates
    if not gates["static_failures_within_cap"]:
        if not v1_gates["gate_instrument_resolves"]:
            return "reopen_instrument_imprecise", gates
        return "reopen_static_not_credible", gates
    return v1_reading, gates


@dataclass(frozen=True)
class ReadingRule:
    apply: Callable[[dict[str, Any]], tuple[str, dict[str, bool]]]
    required_coprimary: dict[str, tuple[str, str]]
    required_decision: tuple[str, ...] = ()
    policy: str | None = None


READING_RULES = {
    # The older rules were frozen under fail_unit and run only under it (code review, PDR-0052).
    "bounded-screen-v1": ReadingRule(
        reading_screen_v1,
        {"scheduled_minus_no_growth": ("scheduled", "no_growth"), "scheduled_minus_static": ("scheduled", "static")},
        policy="fail_unit",
    ),
    "positive-control-v1": ReadingRule(
        reading_positive_control_v1, {"static_minus_no_growth": ("static", "no_growth")}, policy="fail_unit"
    ),
    "graft-capture-v1": ReadingRule(
        reading_graft_capture_v1,
        {"scheduled_minus_no_growth": ("scheduled", "no_growth"), "scheduled_minus_static": ("scheduled", "static")},
        policy="fail_unit",
    ),
    "graft-capture-v2": ReadingRule(
        reading_graft_capture_v2,
        {"scheduled_minus_no_growth": ("scheduled", "no_growth"), "scheduled_minus_static": ("scheduled", "static")},
        required_decision=("max_graft_failures", "max_static_failures"),
        policy="per_contrast",
    ),
}


def binomial_bounds(k: int, n: int) -> dict[str, float]:
    """Exact (Clopper-Pearson) bounds on a failure rate: two-sided 95% and one-sided 95% upper."""
    lower = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    upper = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    upper_one_sided = 1.0 if k == n else float(stats.beta.ppf(0.95, k + 1, n - k))
    return {"lower_95": lower, "upper_95": upper, "upper_one_sided_95": upper_one_sided}


def capture_fraction(units: dict[int, dict[str, float]], resamples: int, seed: int) -> dict[str, Any] | None:
    """Descriptive: the graft's mean gain over no growth as a fraction of static's, with a paired bootstrap.

    Over units where all three arms finished; a ratio of means, never a verdict.
    """
    full = [s for s in sorted(units) if {"scheduled", "static", "no_growth"} <= set(units[s])]
    if len(full) < 3:
        return None
    graft = np.array([units[s]["scheduled"] - units[s]["no_growth"] for s in full])
    static = np.array([units[s]["static"] - units[s]["no_growth"] for s in full])
    if static.mean() >= 0:
        return {
            "n": len(full),
            "estimate": None,
            "bootstrap_interval": None,
            "note": "denominator (static - no growth) is >= 0 on these units: no deficit to capture",
        }
    idx = np.random.default_rng(seed).integers(0, len(full), size=(resamples, len(full)))
    denominators = static[idx].mean(axis=1)
    estimate = float(graft.mean() / static.mean())
    reached_zero = int((denominators >= 0).sum())
    if reached_zero:  # A ratio whose denominator can reach zero has no meaningful interval (reviews).
        return {
            "n": len(full),
            "estimate": estimate,
            "bootstrap_interval": None,
            "note": f"denominator (static - no growth) reached >= 0 in {reached_zero} of {resamples} resamples",
        }
    lo, hi = np.quantile(graft[idx].mean(axis=1) / denominators, [0.025, 0.975])
    return {"n": len(full), "estimate": estimate, "bootstrap_interval": {"lower": float(lo), "upper": float(hi), "level": 0.95}}


def contrast_entries(
    analysis: dict[str, Any], pairs: dict[str, tuple[list[int], np.ndarray]], lost: dict[str, list[int]], delta: float
) -> tuple[dict[str, Any], float]:
    """Every declared contrast from its paired differences; co-primaries are Bonferroni-adjusted and adjudicated."""
    primaries = [name for name, c in analysis["contrasts"].items() if c["role"] == "co-primary"]
    alpha_each = analysis["family_alpha"] / len(primaries)  # Bonferroni over the co-primary family.
    level = 1 - alpha_each
    contrasts: dict[str, Any] = {}
    for name, contrast in analysis["contrasts"].items():
        seeds, diffs = pairs[name]
        primary = contrast["role"] == "co-primary"
        contrast_level = level if primary else DESCRIPTIVE_LEVEL
        if len(diffs) < 3:
            contrasts[name] = {"arms": contrast["arms"], "role": contrast["role"], "n_pairs": len(diffs), "lost_pairs": lost[name]}
            continue
        ci = interval(diffs, contrast_level)
        entry: dict[str, Any] = {
            "arms": list(contrast["arms"]),
            "role": contrast["role"],
            "interval_level": contrast_level,
            "n_pairs": len(diffs),
            "lost_pairs": lost[name],
            "per_unit": dict(zip(map(str, seeds), diffs.tolist(), strict=True)),
            "t_interval": ci,
            "bootstrap_interval": bootstrap(diffs, contrast_level, analysis["bootstrap_resamples"], analysis["bootstrap_seed"]),
            "wilcoxon_p": float(stats.wilcoxon(diffs).pvalue) if np.any(diffs != 0) else 1.0,
            "fraction_first_better": float(np.mean(diffs < 0)),
            "worst_decile": float(np.quantile(diffs, 0.9)),
            "verdict": None,  # Descriptive contrasts are described, never adjudicated (audit F-B).
        }
        if primary:
            entry["mde_vs_zero_80pct"] = mde(ci["sd"], len(diffs), alpha_each, 0.8)
            entry["effect_for_80pct_progress"] = effect_for_progress(ci["sd"], len(diffs), alpha_each, 0.8, delta)
            entry["verdict"] = contrast_verdict(ci, delta)
        contrasts[name] = entry
    return contrasts, level


def analyze(root: Path, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    plan_sha = file_hash(plan_path)
    launched = read_json(root / "launch.json")
    if not Path(__file__).resolve().is_relative_to(Path(launched["snapshot"]).resolve()):
        raise ValueError(f"analysis must run from the launch snapshot {launched['snapshot']} (PYTHONPATH), not the live checkout")
    if launched["prereg_sha256"] != plan_sha:
        raise ValueError("pre-registration changed after launch")
    if launched.get("analysis_module_sha256") != analysis_module_hash():
        raise ValueError("analysis module changed since launch: the reading rule is not the one that was frozen")
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to analyze from a dirty tree")
    out = root / "screen_report.json"
    if out.exists():
        raise FileExistsError("screen report already published; the analysis runs once")
    if not (root / "launch-finished.json").is_file():
        raise ValueError("fleet not finished: launch-finished.json is missing, so analysis would be an interim look")
    finished_seeds = {u["seed"] for u in read_json(root / "launch-finished.json")["units"]}
    if finished_seeds != set(launched["seeds"]) or finished_seeds != set(unit_seeds(plan)):
        raise ValueError("launched, finished and planned seeds disagree")
    epochs = plan["endpoint"]["late_epochs"]
    analysis = plan["analysis"]
    decision = plan["decision"]
    policy = decision["diverged_arm_policy"]
    rule = READING_RULES[decision["reading_rule"]]
    delta = decision["delta_nats"]
    pinned = plan.get("data_identity")
    declared = [arm for arm in ARMS if any(arm in c["arms"] for c in analysis["contrasts"].values())]
    diverged_by_arm = dict.fromkeys(declared, 0)  # Sealed arms' status is not reported either.
    verified = 0
    reference_data: tuple[str, str] | None = None
    units: dict[int, dict[str, float]] = {}  # Late CE of each unit's finished declared arms.
    costs: dict[int, dict[str, dict[str, float]]] = {}
    trajectories: dict[int, dict[str, list[float]]] = {}
    failures: list[dict[str, Any]] = []
    for seed in unit_seeds(plan):
        unit = root / f"seed-{seed}"
        try:
            manifest, complete, _ = verify_run(unit)
            if manifest["spec"] != expected_spec(plan, seed).__dict__ or manifest["git"]["commit"] != launched["git"]["commit"]:
                raise ValueError("unit identity: manifest spec or commit disagrees with the plan and launch")
            data_identity = (manifest["data"]["fit_sha256"], manifest["data"]["dev_sha256"])
            if pinned is not None and (manifest["data"]["source_files"], *data_identity) != (
                pinned["source_files"],
                pinned["fit_sha256"],
                pinned["dev_sha256"],
            ):  # The pin is checked first: it is the stronger identity.
                raise ValueError("unit identity: data differ from the pinned data identity")
            reference_data = reference_data or data_identity
            if data_identity != reference_data:
                raise ValueError("unit identity: fit/dev data differ from the other units")
            verified += 1
            for arm in declared:
                diverged_by_arm[arm] += complete["arm_status"][arm] == "diverged"
            lost = [arm for arm in declared if complete["arm_status"][arm] == "diverged"]
            if lost and policy == "fail_unit":
                raise ValueError(f"contrast arm diverged: {lost} (diverged_arm_policy fail_unit)")
            finite = [arm for arm in declared if complete["arm_status"][arm] == "completed"]
            units[seed] = late_ce(unit, epochs, finite)
            costs[seed] = unit_costs(unit, declared)
            trajectories[seed] = epoch_ce(unit, finite)
        except Exception as error:  # Any unit failure is recorded, never silently dropped (audit F8).
            failures.append({"seed": seed, "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
    if not units:
        raise RuntimeError(
            f"no unit is analysable ({len(failures)} failures); nothing published, treat as analysis-side until shown otherwise"
        )
    seeds = sorted(units)
    pair_seeds = {
        name: [s for s in seeds if c["arms"][0] in units[s] and c["arms"][1] in units[s]] for name, c in analysis["contrasts"].items()
    }
    lost_pairs = {name: [s for s in seeds if s not in pair_seeds[name]] for name in analysis["contrasts"]}
    report: dict[str, Any] = {
        "study": plan["study"]["id"],
        "plan_sha256": plan_sha,
        "analysis_git": git,
        "analyzed_unix": time.time(),
        "n_units": len(units),
        "failures": failures,
        "delta_nats": delta,
        "reading_rule": decision["reading_rule"],
        "diverged_arm_policy": policy,
        "diverged_units_by_arm": diverged_by_arm,
        "arm_divergence_bounds": {arm: binomial_bounds(k, verified) for arm, k in diverged_by_arm.items()} if verified else {},
        **{key: decision[key] for key in rule.required_decision},
    }
    too_few = [name for name, c in analysis["contrasts"].items() if c["role"] == "co-primary" and len(pair_seeds[name]) < 3]
    if len(failures) > decision["max_failed_units"] or len(units) < 3 or too_few:
        report["reading"] = "instrument_failure"
        report["observed_arm_late_ce_mean"] = {
            arm: float(np.mean(vals)) if (vals := [units[s][arm] for s in seeds if arm in units[s]]) else None for arm in declared
        }
        out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        return report

    def paired(name: str) -> tuple[list[int], np.ndarray]:
        first, second = analysis["contrasts"][name]["arms"]
        return pair_seeds[name], np.array([units[s][first] - units[s][second] for s in pair_seeds[name]])

    pairs = {name: paired(name) for name in analysis["contrasts"]}
    contrasts, level = contrast_entries(analysis, pairs, lost_pairs, delta)
    # Arms outside every declared contrast are sealed: trained for pairing, never summarised (audit F-G).
    finite_seeds = {arm: [s for s in seeds if arm in units[s]] for arm in declared}
    report.update(
        {
            "confidence_level": level,
            "arm_finite_n": {arm: len(finite_seeds[arm]) for arm in declared},
            # Every per-arm summary covers the same units: those where the arm finished (code review S4).
            "arm_late_ce_mean": {
                arm: float(np.mean([units[s][arm] for s in finite_seeds[arm]])) if finite_seeds[arm] else None for arm in declared
            },
            "arm_costs_mean": {
                arm: {k: float(np.mean([costs[s][arm][k] for s in finite_seeds[arm]])) for k in (*COST_FIELDS, "wall_s")}
                if finite_seeds[arm]
                else None
                for arm in declared
            },
            "arm_epoch_dev_ce_mean": {
                arm: np.mean([trajectories[s][arm] for s in finite_seeds[arm]], axis=0).tolist() if finite_seeds[arm] else None
                for arm in declared
            },
            "contrasts": contrasts,
        }
    )
    if {"scheduled", "static", "no_growth"} <= set(declared):
        report["capture_fraction"] = capture_fraction(units, analysis["bootstrap_resamples"], analysis["bootstrap_seed"])
    report["reading"], gates = rule.apply(report)
    report.update(gates)
    if policy == "per_contrast":
        # Declared sensitivity (PDR-0052): impute each lost co-primary pair at the observed extreme
        # favouring one arm, independently per contrast (every corner), and re-read. A heuristic,
        # not a bound: a diverged arm may lie outside the observed range. The headline stays on finished pairs.
        primaries = [name for name, c in analysis["contrasts"].items() if c["role"] == "co-primary" and lost_pairs[name]]
        readings = {}
        for corner in itertools.product((0, 1), repeat=len(primaries)):
            imputed = dict(pairs)
            labels = []
            for name, side in zip(primaries, corner, strict=True):
                seeds_, diffs = pairs[name]
                fill = np.min(diffs) if side == 0 else np.max(diffs)  # Negative favours the first arm.
                imputed[name] = (seeds_, np.concatenate([diffs, np.full(len(lost_pairs[name]), fill)]))
                labels.append(f"{name}=favour_{analysis['contrasts'][name]['arms'][side]}")
            alternative, _ = contrast_entries(analysis, {n: (list(range(len(d))), d) for n, (_, d) in imputed.items()}, lost_pairs, delta)
            readings["|".join(labels)] = rule.apply({**report, "contrasts": alternative})[0]
        report["sensitivity"] = {
            "lost_pairs": {name: len(lost_pairs[name]) for name in primaries},
            "readings": readings,
            "robust": all(r == report["reading"] for r in readings.values()),
        }
        if {"scheduled", "static", "no_growth"} <= set(declared):
            # Are static losses selective? Graft - no growth is observable on the units that lost static.
            def graft_gain(group: list[int]) -> dict[str, Any]:
                gains = [units[s]["scheduled"] - units[s]["no_growth"] for s in group]
                return {"n": len(gains), "scheduled_minus_no_growth_mean": float(np.mean(gains)) if gains else None}

            both = [s for s in seeds if {"scheduled", "no_growth"} <= set(units[s])]
            report["static_loss_diagnostic"] = {
                "static_finished": graft_gain([s for s in both if "static" in units[s]]),
                "static_diverged": graft_gain([s for s in both if "static" not in units[s]]),
            }
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
