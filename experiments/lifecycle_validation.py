"""Lifecycle-v2 validation study: launch the fleet and compute the pre-declared criteria.

Design: docs/bounded-lifecycle-v2.md. Plan: docs/prereg/lifecycle-v2-validation.json.

Each (cell, seed) is one job. It trains the v1 run and then the v2 run of that seed on
the same GPU, so the replay criterion (C3) never depends on which device ran a variant.
Units train, and the analysis runs, from one immutable source snapshot.

The study reports two things separately for every cell, variant and arm:
- the failure rate (how many units diverged);
- finite performance (late dev CE over the units that finished).
A mean over survivors is never presented as the arm's performance.

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
import subprocess
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from experiments.bounded_comparison import ARMS, git_identity, read_json, strict_json, verify_run
from experiments.bounded_data import RunSpec, cifar_source_hashes, file_hash, validated_spec
from experiments.bounded_screen import interval, make_snapshot, visible_gpus

VARIANTS = ("v1", "v2")
UNIT_FIELDS = ("seed", "data", "outer_size")  # Set per unit or fixed by the study, never by plan config.
CELL_FIELDS = ("host", "seed_type")  # Set per cell.
VARIANT_FIELD = "lifecycle"  # Set per variant.
HOST_ARMS = ("no_growth", "static")  # Independent of the lifecycle variant: their records must replay bitwise.
PRE_GERMINATION = ("dormant",)  # A scheduled arm that diverges before its seed exists is host instability (C5).
PLAN_KEYS = {
    "study",
    "units",
    "cells",
    "variants",
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
CRITERIA_KEYS = {"stable_cells", "regression_cell", "tost_margin", "alpha", "auc_min", "max_failed_units", "lr", "momentum"}
REPORT = "lifecycle_report.json"
PERFORMANCE_LEVEL = 0.95  # Descriptive intervals only; no performance contrast is adjudicated here.


# --- the mechanism: Nesterov momentum-SGD along one direction of curvature kappa ---


def rho(kappa: float, lr: float, m: float) -> float:
    """Spectral radius of torch's Nesterov map (dampening 0) on a quadratic of curvature kappa.

    State (p, v): v' = m v + kappa p; p' = p - lr (kappa p + m v'). It crosses 1 at
    kappa = 2(1+m) / (lr (1+2m)), the c* the runner records against.
    """
    matrix = np.array([[1 - lr * kappa * (1 + m), -lr * m * m], [kappa, m]], dtype=np.float64)
    return float(np.max(np.abs(np.linalg.eigvals(matrix))))


def amplification(kappas: list[float], lr: float, m: float) -> float:
    """Cumulative growth along the gain direction over the STE steps: the sum of log rho(kappa_t)."""
    if any(math.isinf(k) for k in kappas):
        return math.inf
    return float(sum(math.log(rho(k, lr, m)) for k in kappas))


def parse_kappa(value: Any) -> float | None:
    """A recorded kappa: a finite number, or the explicit tag "inf". "nan" is reported, never ranked."""
    if value == "inf":
        return math.inf
    if type(value) in (int, float) and math.isfinite(value):
        return float(value)
    return None


# --- statistics ---


def auc(positives: list[float], negatives: list[float]) -> float | None:
    """Mann-Whitney AUC: P(positive ranks above negative), ties counted half. None when a side is empty."""
    if not positives or not negatives:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar test on the discordant pairs b and c."""
    n = b + c
    if n == 0:
        return 1.0
    return float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5)))


def tost_equivalent(diffs: list[float], margin: float, alpha: float) -> bool:
    """Paired TOST in its interval form: the (1 - 2 alpha) t interval lies inside (-margin, margin).

    The interval form stays defined when every difference is identical (sd 0).
    """
    values = np.asarray(diffs, dtype=np.float64)
    n = len(values)
    half = float(stats.t.ppf(1 - alpha, n - 1)) * float(values.std(ddof=1)) / math.sqrt(n)
    mean = float(values.mean())
    return bool(-margin < mean - half and mean + half < margin)


def binomial_bounds(k: int, n: int) -> dict[str, float]:
    """Exact (Clopper-Pearson) bounds on a failure rate: two-sided 95% and one-sided 95% upper."""
    lower = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    upper = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    upper_one_sided = 1.0 if k == n else float(stats.beta.ppf(0.95, k + 1, n - k))
    return {"lower_95": lower, "upper_95": upper, "upper_one_sided_95": upper_one_sided}


# --- the pre-declared criteria (docs/bounded-lifecycle-v2.md) ---


def _diverged(unit: dict[str, Any], arm: str) -> bool:
    return bool(unit["status"][arm] == "diverged")


def _lifecycle_divergence(unit: dict[str, Any]) -> bool:
    """The scheduled arm diverged after its seed was germinated (the lifecycle's domain)."""
    return _diverged(unit, "scheduled") and unit["scheduled_divergence_stage"] not in PRE_GERMINATION


def _pre_germination(unit: dict[str, Any]) -> bool:
    return _diverged(unit, "scheduled") and unit["scheduled_divergence_stage"] in PRE_GERMINATION


def _by_seed(units: list[dict[str, Any]], cell: str, variant: str) -> dict[int, dict[str, Any]]:
    return {u["seed"]: u for u in units if u["cell"] == cell and u["variant"] == variant}


def _c1(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """v2 is stable: zero lifecycle divergences in the stable cells."""
    stable = [u for u in units if u["variant"] == "v2" and u["cell"] in plan["stable_cells"]]
    failed = [u for u in stable if _lifecycle_divergence(u)]
    n, k = len(stable), len(failed)
    paired: dict[str, Any] = {}
    for cell in plan["stable_cells"]:
        v1, v2 = _by_seed(units, cell, "v1"), _by_seed(units, cell, "v2")
        seeds = sorted(set(v1) & set(v2))
        b = sum(_lifecycle_divergence(v1[s]) and not _lifecycle_divergence(v2[s]) for s in seeds)
        c = sum(not _lifecycle_divergence(v1[s]) and _lifecycle_divergence(v2[s]) for s in seeds)
        paired[cell] = {"pairs": len(seeds), "v1_only": b, "v2_only": c, "mcnemar_p": mcnemar_p(b, c)}
    return {
        "pass": n > 0 and k == 0,
        "n": n,
        "diverged": k,
        "stages": dict(Counter(u["scheduled_divergence_stage"] for u in failed)),
        "diverged_seeds": sorted((u["cell"], u["seed"]) for u in failed),
        "rule_of_three_upper": 3 / n if n else None,
        "exact_bounds": binomial_bounds(k, n) if n else None,
        "paired_v1_v2": paired,
    }


def _c2(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """The mechanism, on v1 units: max kappa > c* is necessary for divergence; amplification ranks it."""
    lr, m = plan["lr"], plan["momentum"]
    limit = 2 * (1 + m) / (lr * (1 + 2 * m))
    v1 = [u for u in units if u["variant"] == "v1"]
    positives = [u for u in v1 if _lifecycle_divergence(u)]
    negatives = [u for u in v1 if u["status"]["scheduled"] == "completed"]

    def kappas(unit: dict[str, Any]) -> list[float]:
        return [k for k in (parse_kappa(v) for v in unit["ste_kappa"]) if k is not None]

    def over_limit(unit: dict[str, Any]) -> bool:
        values = kappas(unit)
        return bool(values) and max(values) > limit

    def score(unit: dict[str, Any]) -> float | None:
        values = kappas(unit)
        return amplification(values, lr, m) if values else None

    pos_scores = [s for s in map(score, positives) if s is not None]
    neg_scores = [s for s in map(score, negatives) if s is not None]
    sensitivity = sum(map(over_limit, positives)) / len(positives) if positives else None
    specificity = sum(not over_limit(u) for u in negatives) / len(negatives) if negatives else None
    area = auc(pos_scores, neg_scores)
    testable = bool(positives) and bool(negatives)
    return {
        "pass": (sensitivity == 1.0 and area is not None and area >= plan["auc_min"]) if testable else None,
        "c_star": limit,
        "positives": len(positives),
        "negatives": len(negatives),
        "positive_stages": dict(Counter(u["scheduled_divergence_stage"] for u in positives)),
        "positives_below_limit": sorted((u["cell"], u["seed"]) for u in positives if not over_limit(u)),
        "unranked_units": sorted((u["cell"], u["seed"]) for u in positives + negatives if score(u) is None),
        "nan_kappa_entries": sum(1 for u in positives + negatives for v in u["ste_kappa"] if parse_kappa(v) is None),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "auc": area,
    }


def _c3(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """A free replay test: the host arms do not depend on the variant, so their records match bitwise."""
    pairs, mismatches = 0, []
    for cell in sorted({u["cell"] for u in units}):
        v1, v2 = _by_seed(units, cell, "v1"), _by_seed(units, cell, "v2")
        for seed in sorted(set(v1) & set(v2)):
            pairs += 1
            mismatches += [[cell, seed, arm] for arm in HOST_ARMS if v1[seed]["replay_digest"][arm] != v2[seed]["replay_digest"][arm]]
    return {"pass": pairs > 0 and not mismatches, "pairs": pairs, "mismatches": mismatches}


def _c4(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """Regression guard: where v1 is safe, v2 is v1 in both failure rate and finite performance."""
    cell, alpha, margin = plan["regression_cell"], plan["alpha"], plan["tost_margin"]
    v1, v2 = _by_seed(units, cell, "v1"), _by_seed(units, cell, "v2")
    seeds = sorted(set(v1) & set(v2))
    v2_only = [s for s in seeds if _lifecycle_divergence(v2[s]) and not _lifecycle_divergence(v1[s])]
    finite = [s for s in seeds if v1[s]["late_ce"]["scheduled"] is not None and v2[s]["late_ce"]["scheduled"] is not None]
    diffs = [v2[s]["late_ce"]["scheduled"] - v1[s]["late_ce"]["scheduled"] for s in finite]
    equivalent = tost_equivalent(diffs, margin, alpha) if len(diffs) >= 3 else None
    return {
        "pass": equivalent is True and not v2_only,
        "pairs": len(seeds),
        "v2_only_divergences": v2_only,
        "finite_pairs": len(finite),
        "tost_equivalent": equivalent,
        "v2_minus_v1": interval(np.asarray(diffs), 1 - 2 * alpha) if len(diffs) >= 3 else None,
    }


def _c5(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """Host instability, reported apart from the lifecycle: host-arm and pre-germination divergences."""
    cells = sorted({u["cell"] for u in units})
    report: dict[str, Any] = {}
    for arm in HOST_ARMS:
        report[arm] = {}
        for cell in cells:
            seeds = sorted({u["seed"] for u in units if u["cell"] == cell})
            hit = sorted({u["seed"] for u in units if u["cell"] == cell and _diverged(u, arm)})
            report[arm][cell] = {"n_seeds": len(seeds), "diverged": len(hit), "seeds": hit}
    report["scheduled_pre_germination"] = {
        cell: sorted({u["seed"] for u in units if u["cell"] == cell and _pre_germination(u)}) for cell in cells
    }
    present = any(entry["diverged"] for arm in HOST_ARMS for entry in report[arm].values())
    return {**report, "present": present or any(report["scheduled_pre_germination"].values())}


def _performance(units: list[dict[str, Any]]) -> dict[str, Any]:
    """Per cell, variant and arm: failure rate and finite performance, side by side and never merged."""
    table: dict[str, Any] = {}
    for cell in sorted({u["cell"] for u in units}):
        table[cell] = {}
        for variant in VARIANTS:
            group = [u for u in units if u["cell"] == cell and u["variant"] == variant]
            if not group:
                continue
            arms: dict[str, Any] = {}
            for arm in ARMS:
                k = sum(_diverged(u, arm) for u in group)
                finite = [u["late_ce"][arm] for u in group if u["late_ce"][arm] is not None]
                arms[arm] = {
                    "n": len(group),
                    "diverged": k,
                    "divergence_rate": k / len(group),
                    "divergence_bounds": binomial_bounds(k, len(group)),
                    "finite_n": len(finite),
                    "finite_late_ce_mean": float(np.mean(finite)) if finite else None,
                    "finite_late_ce_sd": float(np.std(finite, ddof=1)) if len(finite) > 1 else None,
                }
            contrasts: dict[str, Any] = {}
            for first, second in (("scheduled", "no_growth"), ("static", "no_growth"), ("scheduled", "static")):
                both = [u for u in group if u["late_ce"][first] is not None and u["late_ce"][second] is not None]
                diffs = np.asarray([u["late_ce"][first] - u["late_ce"][second] for u in both])
                contrasts[f"{first}_minus_{second}"] = {
                    "finite_pairs": len(both),
                    "excluded_pairs": len(group) - len(both),
                    "t_interval": interval(diffs, PERFORMANCE_LEVEL) if len(both) >= 3 else None,
                }
            table[cell][variant] = {"arms": arms, "finite_paired_contrasts": contrasts}
    return table


def evaluate_criteria(units: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """C1-C4 decide acceptance; C5 and the performance table are reported and never decide it."""
    report: dict[str, Any] = {
        "c1_v2_stable": _c1(units, plan),
        "c2_mechanism": _c2(units, plan),
        "c3_replay": _c3(units, plan),
        "c4_regression_guard": _c4(units, plan),
        "c5_host_instability": _c5(units, plan),
        "performance": _performance(units),
    }
    report["accepted"] = all(report[c]["pass"] is True for c in ("c1_v2_stable", "c2_mechanism", "c3_replay", "c4_regression_guard"))
    return report


# --- evidence: one verified run reduced to the fields the criteria read ---


def _replay_digest(records: list[dict[str, Any]], arm: str) -> str:
    """Every record of the arm except its wall clock, canonically encoded."""
    comparable = [{k: v for k, v in r.items() if k != "wall_s"} for r in records if r["arm"] == arm]
    return hashlib.sha256(json.dumps(comparable, sort_keys=True, allow_nan=False).encode()).hexdigest()


def unit_summary(run: Path, late_epochs: list[int]) -> dict[str, Any]:
    """Statuses, the scheduled arm's STE kappa trace and divergence stage, late CE and replay digests.

    Call only on a run that verify_run accepted. Late CE is None for an arm that diverged.
    """
    status = dict(read_json(run / "complete.json")["arm_status"])
    records = [json.loads(line) for line in (run / "training.jsonl").read_text().splitlines()]
    scheduled = [r for r in records if r["arm"] == "scheduled"]
    divergence = next((r for r in scheduled if r["kind"] == "diverged"), None)
    kappas: list[Any] = []
    for record in scheduled:
        if record["kind"] in ("epoch", "diverged") and "ste" in record["witness"]:
            kappas += record["witness"]["ste"]["kappa_live"]
    late: dict[str, float | None] = {}
    for arm in ARMS:
        ce = {r["epoch"]: float(r["dev"]["ce"]) for r in records if r["arm"] == arm and r["kind"] == "epoch"}
        late[arm] = sum(ce[e] for e in late_epochs) / len(late_epochs) if status[arm] == "completed" else None
    return {
        "status": status,
        "scheduled_divergence_stage": None if divergence is None else divergence["stage"],
        "ste_kappa": kappas,
        "late_ce": late,
        "replay_digest": {arm: _replay_digest(records, arm) for arm in HOST_ARMS},
    }


# --- the plan ---


def analysis_module_hash() -> str:
    return file_hash(Path(__file__))


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def expected_spec(plan: dict[str, Any], cell: str, variant: str, seed: int) -> RunSpec:
    """The exact specification one unit must have been trained under."""
    fields = {**RunSpec().__dict__, **plan["config"], **plan["cells"][cell], VARIANT_FIELD: variant, "seed": seed, "data": "cifar"}
    return validated_spec(fields)


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    units = plan["units"]
    seeds = list(range(units["first_seed"], units["first_seed"] + units["count"]))
    if set(seeds) & set(units["excluded_seeds"]):
        raise ValueError("declared seed range overlaps seeds used by earlier studies")
    return seeds


def load_plan(path: Path) -> dict[str, Any]:
    plan = read_json(path)
    if not REQUIRED_PLAN_KEYS <= set(plan) <= PLAN_KEYS:
        raise ValueError(f"plan must state {sorted(REQUIRED_PLAN_KEYS)} and nothing outside {sorted(PLAN_KEYS)}")
    if plan["gated_by"] is not None:
        raise ValueError("this study runs ungated (gated_by null)")
    if not isinstance(plan["linked_plans"], list) or any(not Path(p).is_file() for p in plan["linked_plans"]):
        raise ValueError("linked_plans must list existing plan files")
    if plan["variants"] != list(VARIANTS):
        raise ValueError(f"variants must be exactly {list(VARIANTS)}")
    units = plan["units"]
    if type(units.get("first_seed")) is not int or type(units.get("count")) is not int or units["count"] < 3:
        raise ValueError("units need an int first_seed and a count of at least 3")
    if not isinstance(units.get("excluded_seeds"), list):
        raise ValueError("units must list excluded_seeds")
    unit_seeds(plan)
    required = set(RunSpec.__dataclass_fields__) - set(UNIT_FIELDS) - set(CELL_FIELDS) - {VARIANT_FIELD}
    if not isinstance(plan["config"], dict) or set(plan["config"]) != required:
        raise ValueError(f"plan config must state exactly {sorted(required)}")
    cells = plan["cells"]
    if not isinstance(cells, dict) or not cells or any(not isinstance(c, dict) or set(c) != set(CELL_FIELDS) for c in cells.values()):
        raise ValueError(f"every cell must state exactly {list(CELL_FIELDS)}")
    criteria = plan["criteria"]
    if not isinstance(criteria, dict) or set(criteria) != CRITERIA_KEYS:
        raise ValueError(f"criteria must state exactly {sorted(CRITERIA_KEYS)}")
    stable, regression = criteria["stable_cells"], criteria["regression_cell"]
    if not isinstance(stable, list) or not stable or not set(stable) <= set(cells) or regression not in cells or regression in stable:
        raise ValueError("stable_cells must be declared cells; regression_cell a different declared cell")
    if not all(_number(criteria[k]) for k in ("tost_margin", "alpha", "auc_min", "lr", "momentum")):
        raise ValueError("criteria thresholds must be finite numbers")
    if criteria["tost_margin"] <= 0 or not 0 < criteria["alpha"] < 0.5 or not 0.5 < criteria["auc_min"] <= 1:
        raise ValueError("tost_margin > 0, alpha in (0, 0.5), auc_min in (0.5, 1]")
    if type(criteria["max_failed_units"]) is not int or criteria["max_failed_units"] < 0:
        raise ValueError("max_failed_units must be a non-negative int")
    for cell in cells:
        for variant in VARIANTS:
            cfg = expected_spec(plan, cell, variant, unit_seeds(plan)[0]).kernel_config()
            if (cfg.seed_lr, cfg.momentum) != (criteria["lr"], criteria["momentum"]):
                raise ValueError("criteria lr/momentum must be the seed group's optimiser settings (they define c*)")
    late = plan["endpoint"].get("late_epochs")
    if not isinstance(late, list) or not late or len(set(late)) != len(late):
        raise ValueError("late_epochs must be a non-empty list of distinct epochs")
    if any(type(e) is not int or not 0 <= e < plan["config"]["epochs"] for e in late):
        raise ValueError("late_epochs must be epochs within the configured horizon")
    identity = plan["data_identity"]
    if not isinstance(identity, dict) or set(identity) != {"source_files", "fit_sha256", "dev_sha256"}:
        raise ValueError("data_identity must pin source_files, fit_sha256 and dev_sha256")
    return plan


def jobs(plan: dict[str, Any]) -> list[tuple[str, int]]:
    """One job per (cell, seed); a job trains every variant of that seed on one device."""
    return [(cell, seed) for cell in plan["cells"] for seed in unit_seeds(plan)]


def unit_dir(root: Path, cell: str, seed: int, variant: str) -> Path:
    return root / "units" / cell / f"seed-{seed}" / variant


def train_command(spec: RunSpec, output: Path, data_root: Path) -> list[str]:
    command = [sys.executable, "-B", "-m", "experiments.bounded_comparison", "train"]
    command += ["--data-root", str(data_root), "--output", str(output)]
    for name, value in dataclasses.asdict(spec).items():
        if name != "seed":
            command += ["--" + name.replace("_", "-"), str(value)]
    return [*command, "--seed", str(spec.seed)]  # Last, so nothing can override the unit's seed.


# --- launch and analysis ---


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
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    if cifar_source_hashes(data_root) != plan["data_identity"]["source_files"]:
        raise RuntimeError("data root does not hold the pinned source files")
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
        "jobs": [[cell, seed] for cell, seed in jobs(plan)],
        "workers": workers,
        "started_unix": time.time(),
    }
    (root / "launch.json").write_text(strict_json(record) + "\n")
    base_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    base_env["PYTHONPATH"] = f"{snapshot}:{snapshot / 'src'}"
    free: queue.Queue[str] = queue.Queue()
    for slot in [str(g) for g in gpus[:workers]] or [""] * workers:  # "" hides every GPU from CPU units.
        free.put(slot)

    def run(job: tuple[str, int]) -> list[dict[str, Any]]:
        cell, seed = job
        gpu = free.get()  # The device is held for every variant of this seed (C3 never crosses devices).
        try:
            results = []
            for variant in VARIANTS:
                out = unit_dir(root, cell, seed, variant)
                out.parent.mkdir(parents=True, exist_ok=True)
                started = time.monotonic()
                with (out.parent / f"{variant}.stdout").open("w") as stdout, (out.parent / f"{variant}.stderr").open("w") as stderr:
                    code = subprocess.run(
                        train_command(expected_spec(plan, cell, variant, seed), out, data_root),
                        cwd=snapshot,
                        env=dict(base_env, CUDA_VISIBLE_DEVICES=gpu),
                        stdout=stdout,
                        stderr=stderr,
                        check=False,
                    ).returncode
                results.append(
                    {"cell": cell, "seed": seed, "variant": variant, "returncode": code, "gpu": gpu, "wall_s": time.monotonic() - started}
                )
            return results
        finally:
            free.put(gpu)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = [unit for batch in pool.map(run, jobs(plan)) for unit in batch]  # No retries.
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
    out = root / REPORT
    if out.exists():
        raise FileExistsError("report already published; the analysis runs once")
    if not (root / "launch-finished.json").is_file():
        raise ValueError("fleet not finished: launch-finished.json is missing, so analysis would be an interim look")
    planned = {(cell, seed, variant) for cell, seed in jobs(plan) for variant in VARIANTS}
    finished = {(u["cell"], u["seed"], u["variant"]) for u in read_json(root / "launch-finished.json")["units"]}
    if finished != planned or {tuple(j) for j in launched["jobs"]} != set(jobs(plan)):
        raise ValueError("launched, finished and planned units disagree")
    identity = plan["data_identity"]
    units: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for cell, seed in jobs(plan):
        for variant in VARIANTS:
            run = unit_dir(root, cell, seed, variant)
            try:
                manifest, _complete, _spec = verify_run(run)
                if manifest["spec"] != expected_spec(plan, cell, variant, seed).__dict__:
                    raise ValueError("unit identity: manifest spec disagrees with the plan")
                if manifest["git"]["commit"] != launched["git"]["commit"]:
                    raise ValueError("unit identity: commit disagrees with the launch")
                data = manifest["data"]
                if (data["source_files"], data["fit_sha256"], data["dev_sha256"]) != (
                    identity["source_files"],
                    identity["fit_sha256"],
                    identity["dev_sha256"],
                ):
                    raise ValueError("unit identity: data differ from the pinned data identity")
                units.append({"cell": cell, "variant": variant, "seed": seed, **unit_summary(run, plan["endpoint"]["late_epochs"])})
            except Exception as error:  # Every failure is recorded, never silently dropped.
                failures.append(
                    {
                        "cell": cell,
                        "variant": variant,
                        "seed": seed,
                        "error": f"{type(error).__name__}: {error}",
                        "traceback": traceback.format_exc(),
                    }
                )
    if not units:
        raise RuntimeError(f"no unit is analysable ({len(failures)} failures); nothing published")
    report: dict[str, Any] = {
        "study": plan["study"]["id"],
        "plan_sha256": plan_sha,
        "analysis_git": git_identity(),
        "analyzed_unix": time.time(),
        "n_units": len(units),
        "failures": failures,
        "criteria": evaluate_criteria(units, plan["criteria"]),
    }
    if len(failures) > plan["criteria"]["max_failed_units"]:
        report["reading"] = "instrument_failure"  # Criteria above are observed on the analysable units only.
    else:
        report["reading"] = "accepted" if report["criteria"]["accepted"] else "rejected"
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
