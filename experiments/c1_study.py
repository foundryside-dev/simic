"""Fleet C1 (PDR-0057 G1; ADR-0019): is a targeted graft worth a uniformly bigger host?

For every seed and host, one process trains seven arms on the atlas (experiments/atlas.py):
- no growth: the host, untouched;
- graft: the host's pre-declared seed (`DESIGNED_WINNER`), germinated at the decision point,
  forked from the no-growth trunk's snapshot;
- static: the same seed attached fully coupled at birth, the oracle ceiling;
- uniform scale-up: the same pathology widened to about m times the parameters, no slot.

The pre-registered readings (`evaluate`):
- G1, per host: graft minus scale-up at m, non-inferiority at the plan's margin, stepping down
  m = 1.25 -> 1.5 -> 2.0. Co-primary hosts share the family alpha (Bonferroni). Each step must
  clear on the paired mean and on the trimmed mean (bootstrap): a heavy tail cannot carry it.
  The step-down stops at the first scale-up arm that diverges more often than the plan's cap
  (a failed comparator scores chance CE and must not pass the graft); steps already tested
  stand. If the graft itself diverges more often than its cap, the host reads `graft_unstable`.
- graft minus static on every host: a named co-reading, descriptive.
- deficit screen: a host enters Fleet A only if static beats its no-growth arm by more than the
  plan's gain with the 95% lower bound above 0, and static does not diverge too often.
- the cost price lambda = max(0, -slope) of no-growth-family CE on log2 of the parameter
  multiple (equal to the parameter-step multiple for completed runs), with seed-and-host fixed
  effects, pooled over hosts, completed runs only; a sensitivity fit scores failures at ln 10.
  It is frozen for every later gate.

A diverged arm scores chance-level CE (ln 10) and is never dropped. Outer/test data is never read.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import queue
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from experiments import atlas
from experiments.atlas_hosts import base_config, config_hash, parameter_count, scaled_config
from experiments.bounded_comparison import REPO, append_record, git_identity, read_json, runtime, source_identity, strict_json, write_json
from experiments.bounded_data import RunSpec, cifar_source_hashes, file_hash, load_fit_dev, validated_spec
from experiments.bounded_screen import DATA_IDENTITY_KEYS, binomial_bounds, interval, make_snapshot, visible_gpus
from experiments.kernel_demo import DESIGNED_WINNER, PATHOLOGIES

CHANCE_CE = math.log(10)
BASE_ARMS = ("no_growth", "graft", "static")
REPORT = "c1_report.json"
SCHEMA = "c1-v1"
PLAN_KEYS = {
    "study",
    "units",
    "hosts",
    "decision_epoch",
    "scales",
    "config",
    "data_identity",
    "criteria",
    "predictions",
    "disclosures",
    "deviations",
}
REQUIRED_PLAN_KEYS = PLAN_KEYS - {"predictions", "disclosures", "deviations"}
CRITERIA_KEYS = {
    "margin",
    "family_alpha",
    "co_primary_hosts",
    "step_down",
    "deficit_min_gain",
    "static_divergence_cap",
    "trim",
    "bootstrap_resamples",
    "bootstrap_seed",
    "max_failed_units",
    "comparator_divergence_cap",
    "graft_divergence_cap",
}
DESCRIPTIVE_LEVEL = 0.95


def scale_arm(m: float) -> str:
    return f"scale_x{m:g}"


# --- the pre-registered evaluation ---


def _score(arm: dict[str, Any]) -> float:
    return float(arm["late_ce"]) if arm["status"] == "completed" else CHANCE_CE


def _trimmed(x: np.ndarray, trim: float) -> float:
    return float(stats.trim_mean(x, trim))


def _one_sided(diffs: np.ndarray, alpha: float, trim: float, resamples: int, seed: int) -> dict[str, Any]:
    """Paired mean and trimmed-mean bounds at one-sided level 1 - alpha (both directions)."""
    n = len(diffs)
    mean, sd = float(diffs.mean()), float(diffs.std(ddof=1))
    half = float(stats.t.ppf(1 - alpha, n - 1)) * sd / math.sqrt(n)
    rng = np.random.default_rng(seed)
    boot = np.array([_trimmed(diffs[rng.integers(0, n, n)], trim) for _ in range(resamples)])
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "mean_lower": mean - half,
        "mean_upper": mean + half,
        "trimmed": _trimmed(diffs, trim),
        "trimmed_lower": float(np.quantile(boot, alpha)),
        "trimmed_upper": float(np.quantile(boot, 1 - alpha)),
        "alpha_one_sided": alpha,
    }


def _failure_rate(rows: list[dict[str, Any]], arm: str) -> float:
    return float(sum(u["arms"][arm]["status"] != "completed" for u in rows) / len(rows))


def evaluate(units: list[dict[str, Any]], criteria: dict[str, Any]) -> dict[str, Any]:
    """The pre-registered readings over per-(seed, host) arm summaries."""
    required = (*BASE_ARMS, *(scale_arm(m) for m in criteria["step_down"]))
    complete = [u for u in units if all(a in u["arms"] for a in required)]
    incomplete = len(units) - len(complete)
    hosts = sorted({u["host"] for u in complete}, key=lambda h: list(PATHOLOGIES).index(h) if h in PATHOLOGIES else 99)
    alpha = criteria["family_alpha"] / len(criteria["co_primary_hosts"])
    margin, trim = criteria["margin"], criteria["trim"]
    resamples, bseed = criteria["bootstrap_resamples"], criteria["bootstrap_seed"]

    g1: dict[str, Any] = {}
    static_reading: dict[str, Any] = {}
    screen: dict[str, Any] = {}
    failures: dict[str, Any] = {}
    for host in hosts:
        rows = sorted((u for u in complete if u["host"] == host), key=lambda u: u["seed"])
        score = {arm: np.array([_score(u["arms"][arm]) for u in rows]) for arm in required}

        comparator = {scale_arm(m): _failure_rate(rows, scale_arm(m)) for m in criteria["step_down"]}
        graft_rate = _failure_rate(rows, "graft")
        steps: list[dict[str, Any]] = []
        unstable_at = None
        for m in criteria["step_down"]:
            # A diverged scale-up scores chance CE and would hand the graft a free pass: the
            # step-down stops at the first unstable comparator; steps already tested stand.
            if comparator[scale_arm(m)] > criteria["comparator_divergence_cap"]:
                unstable_at = m
                break
            step = {"m": m, **_one_sided(score["graft"] - score[scale_arm(m)], alpha, trim, resamples, bseed)}
            step["non_inferior"] = step["mean_upper"] < margin and step["trimmed_upper"] < margin
            step["inferior"] = step["mean_lower"] > margin and step["trimmed_lower"] > margin
            steps.append(step)
            if not step["non_inferior"]:
                break
        passed = [s["m"] for s in steps if s["non_inferior"]]
        if graft_rate > criteria["graft_divergence_cap"]:  # the IUT cannot read a diverging graft as inferior
            reading, passed = "graft_unstable", []
        elif passed:
            reading = "non_inferior"
        elif not steps:
            reading = "comparator_unstable"
        else:
            reading = "inferior" if steps[0]["inferior"] else "inconclusive"
        g1[host] = {
            "co_primary": host in criteria["co_primary_hosts"],
            "role": "co_primary" if host in criteria["co_primary_hosts"] else "exploratory",
            "reading": reading,
            "largest_m": passed[-1] if passed else None,
            "comparator_unstable_at": unstable_at,
            "comparator_divergence": comparator,
            "graft_divergence": graft_rate,
            "steps": steps,
        }
        static_reading[host] = {"n": len(rows), **interval(score["graft"] - score["static"], DESCRIPTIVE_LEVEL)}
        gain = interval(score["no_growth"] - score["static"], DESCRIPTIVE_LEVEL)  # positive: static helps
        k_static = sum(u["arms"]["static"]["status"] != "completed" for u in rows)
        rate = k_static / len(rows)
        unstable = rate > criteria["static_divergence_cap"]
        screen[host] = {
            "n": len(rows),
            "static_gain": gain,
            "static_divergence_rate": rate,
            "unstable": unstable,
            "passes": gain["mean"] > criteria["deficit_min_gain"] and gain["lower"] > 0 and not unstable,
        }
        failures[host] = {
            arm: {
                "diverged": (k := sum(u["arms"][arm]["status"] != "completed" for u in rows)),
                "n": len(rows),
                **binomial_bounds(k, len(rows)),
            }
            for arm in required
        }

    lam = _lambda(complete)
    un = g1.get("under_normalized", {}).get("reading")
    c1 = {
        "non_inferior": "supported_at_bounded_scale",
        "inferior": "refuted_at_bounded_scale",
        "inconclusive": "inconclusive",
        "comparator_unstable": "comparator_unstable",
        "graft_unstable": "graft_unstable",
    }.get(un or "", "not_evaluated")
    return {
        "n_units": len(units),
        "incomplete_units": incomplete,
        "g1": g1,
        "graft_minus_static": static_reading,
        "deficit_screen": screen,
        "lambda": lam,
        "failures": failures,
        "reading": {
            "instrument": "instrument_failure" if incomplete > criteria["max_failed_units"] else "ok",
            "c1": c1,
            "c1_mild": g1.get("mild", {}).get("reading", "not_evaluated"),
            "fleet_a_hosts": [h for h in hosts if screen[h]["passes"]],
        },
    }


def _lambda(units: list[dict[str, Any]]) -> dict[str, Any]:
    """lambda = max(0, -slope) of CE on log2(parameter multiple), seed-and-host fixed effects, pooled.

    x is log2 of installed parameters over the host's own: for completed runs, which all train the
    same steps, that equals the parameter-step multiple, and it is known even when an arm failed.
    The primary fit uses completed runs; the sensitivity fit scores failures at ln 10, because
    failures concentrated on wide hosts would bias the primary slope (statistics review F5).
    """

    def fit(include_failures: bool) -> tuple[float, dict[str, float], int]:
        xs: list[float] = []
        ys: list[float] = []
        per_host: dict[str, list[tuple[float, float]]] = {}
        excluded = 0
        for u in units:
            family = [v for a, v in u["arms"].items() if a == "no_growth" or a.startswith("scale_x")]
            base = u["arms"]["no_growth"]["installed_parameters"]
            points = [
                (math.log2(v["installed_parameters"] / base), _score(v)) for v in family if include_failures or v["status"] == "completed"
            ]
            excluded += len(family) - len(points)
            if len(points) < 2:
                continue
            mx, my = sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
            for x, y in points:
                xs.append(x - mx)
                ys.append(y - my)
                per_host.setdefault(u["host"], []).append((x - mx, y - my))
        dx, dy = np.array(xs), np.array(ys)
        slope = float((dx * dy).sum() / (dx * dx).sum()) if (dx * dx).sum() > 0 else 0.0
        host_slopes = {
            h: float(sum(a * b for a, b in pts) / sum(a * a for a, _ in pts))
            for h, pts in per_host.items()
            if sum(a * a for a, _ in pts) > 0
        }
        return slope, host_slopes, excluded

    slope, host_slopes, excluded = fit(False)
    sensitivity, _, _ = fit(True)
    return {
        "slope": slope,
        "lambda": max(0.0, -slope),
        "per_host_slope": host_slopes,
        "excluded_runs": excluded,
        "sensitivity_failures_at_chance": {"slope": sensitivity, "lambda": max(0.0, -sensitivity)},
        "pooled_over_hosts": True,
    }


# --- one unit: every host and arm for one seed ---


def unit_spec(plan: dict[str, Any], seed: int, host: str) -> RunSpec:
    values = {**plan["config"], "seed": seed, "host": host, "seed_type": DESIGNED_WINNER[host], "graft_epoch": plan["decision_epoch"]}
    return validated_spec(values)


def _row(seed: int, host: str, arm: str, label: str, span: atlas.Span, epochs: int, installed: int) -> dict[str, Any]:
    completed = span.diverged is None
    return {
        "schema": SCHEMA,
        "seed": seed,
        "host": host,
        "arm": arm,
        "host_label": label,
        "status": "completed" if completed else "diverged",
        "late_ce": atlas._late_ce(span, epochs) if completed else None,
        "final_dev": span.records[-1]["dev"] if completed else None,
        "initial_dev": span.initial_dev,
        "diverged": span.diverged,
        "costs": span.costs,
        "param_steps": span.costs["optimizer_parameter_steps"],
        "installed_parameters": installed,
        "birth": span.birth,
        "records": span.records,
    }


def _check_identity(provenance: dict[str, Any], pin: dict[str, Any]) -> None:
    for key, pinned in pin.items():  # the data must be the plan's, byte for byte
        if provenance.get(key) != pinned:
            raise ValueError(f"data identity: {key} differs from the plan's pinned value")


def run_unit(plan: dict[str, Any], seed: int, output: Path, data_root: Path | None, plan_sha256: str) -> dict[str, Any]:
    """Every host and arm for one seed. The manifest is written first and rows as each arm finishes;
    complete.json seals the unit, so a crash keeps finished arms for inspection (code review)."""
    if output.exists():
        raise FileExistsError("output must be a fresh directory")
    d, epochs, hosts = plan["decision_epoch"], plan["config"]["epochs"], plan["hosts"]
    # Data, future and pinned RNG streams carry no host term: load once, re-spec per host.
    base = atlas.Unit.load(unit_spec(plan, seed, hosts[0]), data_root)
    _check_identity(base.provenance, plan["data_identity"])
    units = {h: dataclasses.replace(base, spec=unit_spec(plan, seed, h)) for h in hosts}
    output.mkdir(parents=True)
    hosts_meta: dict[str, Any] = {}
    for host, unit in units.items():
        hosts_meta[host] = {
            "label": unit.host_label,
            "designed": DESIGNED_WINNER[host],
            "installed_parameters": parameter_count(base_config(host)),
        }
        for m in plan["scales"]:
            cfg = scaled_config(host, m)
            hosts_meta[host][scale_arm(m)] = {
                "config": dataclasses.asdict(cfg),
                "config_sha256": config_hash(cfg),
                "installed_parameters": parameter_count(cfg),
            }
    here = Path(__file__).resolve().parent
    write_json(
        output / "manifest.json",
        {
            "schema": SCHEMA,
            "study": plan["study"]["id"],
            "prereg_sha256": plan_sha256,
            "seed": seed,
            "hosts": hosts_meta,
            "data": base.provenance,
            "future_sha256": base.future.hash,
            "source": {
                **source_identity(),
                **{f"experiments/{n}": file_hash(here / n) for n in ("atlas.py", "atlas_hosts.py", "c1_study.py")},
            },
            "git": git_identity(),
            "runtime": runtime(base.spec),
        },
    )
    count = 0
    with (output / "arms.jsonl").open("x") as fh:

        def emit(host: str, arm: str, label: str, span: atlas.Span, installed: int) -> None:
            nonlocal count
            append_record(fh, _row(seed, host, arm, label, span, epochs, installed))
            count += 1

        for host, unit in units.items():
            designed, meta = DESIGNED_WINNER[host], hosts_meta[host]
            trunk = unit.trunk(decision_points=(d,))
            emit(host, "no_growth", unit.host_label, trunk, meta["installed_parameters"])
            if d in trunk.snapshots:
                graft = unit.branch(trunk.snapshots[d], action=designed)
            else:  # the trunk diverged before the decision: the graft never ran, and scores as a failure
                graft = atlas.Span(costs=dict(trunk.costs), diverged={"reason": "trunk diverged before the decision", "epoch": d})
            emit(host, "graft", unit.host_label, graft, graft.records[-1]["installed_parameters"] if graft.records else 0)
            static = unit.static(designed)
            emit(host, "static", unit.host_label, static, static.records[-1]["installed_parameters"] if static.records else 0)
            for m in plan["scales"]:
                scaled = dataclasses.replace(unit, host_cfg=scaled_config(host, m))
                emit(host, scale_arm(m), scaled.host_label, scaled.trunk(decision_points=()), meta[scale_arm(m)]["installed_parameters"])
    completion = {
        "schema": SCHEMA,
        "status": "complete",
        "rows": count,
        "artifacts": {name: file_hash(output / name) for name in ("manifest.json", "arms.jsonl")},
    }
    write_json(output / "complete.json", completion)
    return completion


def verify_unit(root: Path, plan: dict[str, Any], *, seed: int, plan_sha256: str, commit: str) -> list[dict[str, Any]]:
    """Refuse a unit whose files changed, that belongs to another seed, plan or commit, whose data
    differ from the pin, or whose rows differ from the plan; return its per-host summaries."""
    completion = read_json(root / "complete.json")
    for name, digest in completion["artifacts"].items():
        if file_hash(root / name) != digest:
            raise ValueError(f"{name} changed after completion")
    manifest = read_json(root / "manifest.json")
    if (manifest["seed"], manifest["prereg_sha256"], manifest["git"]["commit"], manifest["study"]) != (
        seed,
        plan_sha256,
        commit,
        plan["study"]["id"],
    ):
        raise ValueError("unit identity: seed, plan, commit or study differ from the launch")
    _check_identity(manifest["data"], plan["data_identity"])
    rows = [json.loads(line) for line in (root / "arms.jsonl").read_text().splitlines()]
    keys = [(r["host"], r["arm"]) for r in rows]
    expected = {(h, a) for h in plan["hosts"] for a in (*BASE_ARMS, *(scale_arm(m) for m in plan["scales"]))}
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("unit rows differ from the plan")
    for r in rows:
        if r["seed"] != seed:
            raise ValueError("unit identity: a row belongs to another seed")
        if r["status"] not in ("completed", "diverged") or (r["status"] == "completed") != (r["late_ce"] is not None):
            raise ValueError(f"inconsistent status for {r['host']}/{r['arm']}")
        if r["late_ce"] is not None and not math.isfinite(r["late_ce"]):
            raise ValueError("a completed arm must have a finite late CE")
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        out.setdefault(r["host"], {"seed": r["seed"], "host": r["host"], "arms": {}})["arms"][r["arm"]] = {
            "status": r["status"],
            "late_ce": r["late_ce"],
            "param_steps": r["param_steps"],
            "installed_parameters": r["installed_parameters"],
        }
    return list(out.values())


# --- the plan ---


def load_plan(path: Path) -> dict[str, Any]:
    plan: dict[str, Any] = json.loads(path.read_text())
    if not set(plan) >= REQUIRED_PLAN_KEYS or not set(plan) <= PLAN_KEYS:
        raise ValueError(f"plan keys must be {sorted(REQUIRED_PLAN_KEYS)} plus optional predictions/disclosures/deviations")
    if set(plan["criteria"]) != CRITERIA_KEYS:
        raise ValueError(f"criteria keys must be exactly {sorted(CRITERIA_KEYS)}")
    crit = plan["criteria"]
    if not set(plan["hosts"]) <= set(PATHOLOGIES) or len(set(plan["hosts"])) != len(plan["hosts"]):
        raise ValueError("hosts must be distinct pathologies")
    if not set(crit["co_primary_hosts"]) <= set(plan["hosts"]) or not crit["co_primary_hosts"]:
        raise ValueError("co-primary hosts must be planned hosts")
    if list(crit["step_down"]) != sorted(crit["step_down"]) or not set(crit["step_down"]) <= set(plan["scales"]):
        raise ValueError("step_down must be increasing planned scales")
    if not 0 < crit["trim"] < 0.5 or not 0 < crit["family_alpha"] < 0.5 or crit["margin"] <= 0:
        raise ValueError("trim, alpha and margin out of range")
    if not 0 <= crit["comparator_divergence_cap"] < crit["trim"] or not 0 <= crit["graft_divergence_cap"] < crit["trim"]:
        raise ValueError("divergence caps must sit below the trim, or failures could reach the trimmed companion (statistics review F4)")
    if plan["config"].get("data") == "cifar" and set(plan["data_identity"]) != DATA_IDENTITY_KEYS:
        raise ValueError(f"a cifar plan's data_identity must pin exactly {sorted(DATA_IDENTITY_KEYS)}")
    if not isinstance(plan["study"].get("pilot", False), bool):
        raise ValueError("study.pilot must be a boolean")
    units = plan["units"]
    if type(units["first_seed"]) is not int or type(units["count"]) is not int or units["count"] < 3:
        raise ValueError("units need an integer first_seed and a count of at least 3")
    for host in plan["hosts"]:
        unit_spec(plan, units["first_seed"], host)  # every host's spec must validate
    return plan


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    return list(range(plan["units"]["first_seed"], plan["units"]["first_seed"] + plan["units"]["count"]))


def analysis_module_hash() -> str:
    return file_hash(Path(__file__))


# --- launch and analyze ---


def _check_inputs(plan: dict[str, Any], data_root: Path) -> None:
    """Pre-flight, before any side effect: no test data in view, and the pinned data on disk."""
    if (data_root / "cifar-10-batches-py" / "test_batch").exists():
        raise RuntimeError("data root exposes test_batch; use a training-only view")
    pin = plan["data_identity"]
    if not pin:
        return
    if cifar_source_hashes(data_root) != pin["source_files"]:
        raise RuntimeError("data root does not hold the pinned source files")
    provenance = load_fit_dev(unit_spec(plan, unit_seeds(plan)[0], plan["hosts"][0]), data_root)[4]
    if (provenance["fit_sha256"], provenance["dev_sha256"]) != (pin["fit_sha256"], pin["dev_sha256"]):
        raise RuntimeError("data root does not yield the pinned fit/dev data")


def launch(root: Path, data_root: Path, workers: int, plan_path: Path, resume: bool = False) -> dict[str, Any]:
    """Train every seed (all hosts and arms) from an immutable snapshot, one process per GPU."""
    plan = load_plan(plan_path)
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be a positive int")
    try:
        plan_in_repo = plan_path.resolve().relative_to(REPO)
    except ValueError as error:
        raise ValueError("the plan must be committed inside the repository, so the snapshot holds it") from error
    _check_inputs(plan, data_root)
    gpus: list[int] = []
    if plan["config"]["device"] == "cuda":
        gpus = visible_gpus()
        if not gpus or workers > len(gpus):
            raise ValueError(f"one process per GPU: {workers} workers requested, {len(gpus)} GPUs visible")
    git = git_identity()
    if git["status"]:
        raise RuntimeError("refusing to launch from a dirty tree: the commit must pin the frozen procedure")
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
        snapshot, data_root = Path(record["snapshot"]), Path(record["data_root"])
    else:
        root.mkdir(parents=False, exist_ok=False)
        root, data_root = root.resolve(), data_root.resolve()
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
    env = dict(
        os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONPATH=f"{snapshot}:{snapshot / 'src'}"
    )
    free: queue.Queue[str] = queue.Queue()
    for slot in [str(g) for g in gpus[:workers]] or [""] * workers:
        free.put(slot)
    snapshot_plan = snapshot / plan_in_repo  # the committed plan, as the snapshot holds it

    def run(seed: int) -> dict[str, Any]:
        gpu = free.get()
        out = root / "units" / f"seed-{seed}"
        result: dict[str, Any] = {"seed": seed, "gpu": gpu}
        try:
            if (out / "complete.json").exists():
                result.update(returncode=0, resumed=True, wall_s=0.0)
            else:
                if out.exists():
                    out.rename(out.with_name(f"seed-{seed}.partial-{int(time.time())}"))
                out.parent.mkdir(parents=True, exist_ok=True)
                started = time.monotonic()
                command = [sys.executable, "-B", "-m", "experiments.c1_study", "unit", "--plan", str(snapshot_plan), "--seed", str(seed)]
                command += ["--output", str(out), "--data-root", str(data_root), "--plan-sha256", record["prereg_sha256"]]
                with (out.parent / f"seed-{seed}.stdout").open("w") as so, (out.parent / f"seed-{seed}.stderr").open("w") as se:
                    code = subprocess.run(
                        command, cwd=snapshot, env=dict(env, CUDA_VISIBLE_DEVICES=gpu), stdout=so, stderr=se, check=False
                    ).returncode
                result.update(returncode=code, wall_s=time.monotonic() - started)
        except Exception as error:
            result.update(returncode=None, error=f"{type(error).__name__}: {error}")
        finally:
            free.put(gpu)
        with (root / "progress.jsonl").open("a") as log:
            log.write(strict_json(result) + "\n")
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, unit_seeds(plan)))
    finished = {"units": results, "finished_unix": time.time()}
    (root / "launch-finished.json").write_text(strict_json(finished) + "\n")
    return finished


def analyze(root: Path, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    launched = read_json(root / "launch.json")
    if not Path(__file__).resolve().is_relative_to(Path(launched["snapshot"]).resolve()):
        raise ValueError(f"analysis must run from the launch snapshot {launched['snapshot']}, not the live checkout")
    if launched["prereg_sha256"] != file_hash(plan_path):
        raise ValueError("pre-registration changed after launch")
    if launched["analysis_module_sha256"] != analysis_module_hash():
        raise ValueError("analysis module changed since launch")
    if git_identity()["status"]:
        raise RuntimeError("refusing to analyze from a dirty tree")
    out = root / REPORT
    if out.exists():
        raise FileExistsError("report already published; the analysis runs once")
    if not (root / "launch-finished.json").is_file():
        raise ValueError("fleet not finished: analysis would be an interim look")
    planned = set(unit_seeds(plan))
    finished = {u["seed"] for u in read_json(root / "launch-finished.json")["units"]}
    if finished != planned or set(launched["jobs"]) != planned:
        raise ValueError("launched, finished and planned seeds disagree")
    units: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for seed in unit_seeds(plan):
        try:
            units.extend(
                verify_unit(
                    root / "units" / f"seed-{seed}",
                    plan,
                    seed=seed,
                    plan_sha256=launched["prereg_sha256"],
                    commit=launched["git"]["commit"],
                )
            )
        except Exception as error:  # Every failure is recorded, never silently dropped.
            failures.append({"seed": seed, "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
    if not units:
        raise RuntimeError(f"no unit is analysable ({len(failures)} failed seeds); nothing published")
    report = {
        "study": plan["study"]["id"],
        "plan_sha256": launched["prereg_sha256"],
        "analysis_git": git_identity(),
        "analyzed_unix": time.time(),
        "failed_seeds": failures,
        **evaluate(units, plan["criteria"]),
    }
    failed_units = report["incomplete_units"] + len(failures) * len(plan["hosts"])
    report["failed_units"] = failed_units
    report["reading"]["instrument"] = "instrument_failure" if failed_units > plan["criteria"]["max_failed_units"] else "ok"
    if plan["study"].get("pilot", False):  # a pilot sizes the fleet; it never reads (code review)
        report["reading"] = {"instrument": report["reading"]["instrument"], "pilot": True, "c1": "pilot_no_reading", "fleet_a_hosts": []}
    out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_launch = sub.add_parser("launch")
    p_launch.add_argument("--root", type=Path, required=True)
    p_launch.add_argument("--plan", type=Path, required=True)
    p_launch.add_argument("--data-root", type=Path, required=True)
    p_launch.add_argument("--workers", type=int, default=1)
    p_launch.add_argument("--resume", action="store_true")
    p_unit = sub.add_parser("unit")
    p_unit.add_argument("--plan", type=Path, required=True)
    p_unit.add_argument("--seed", type=int, required=True)
    p_unit.add_argument("--output", type=Path, required=True)
    p_unit.add_argument("--data-root", type=Path, required=True)
    p_unit.add_argument("--plan-sha256", required=True)
    p_analyze = sub.add_parser("analyze")
    p_analyze.add_argument("--root", type=Path, required=True)
    p_analyze.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "launch":
        print(strict_json(launch(args.root, args.data_root, args.workers, args.plan, args.resume)))
    elif args.command == "unit":
        if file_hash(args.plan) != args.plan_sha256:
            raise ValueError("unit plan differs from the launched pre-registration")
        print(strict_json(run_unit(load_plan(args.plan), args.seed, args.output, args.data_root, args.plan_sha256)))
    else:
        print(json.dumps(analyze(args.root, args.plan)["reading"]))


if __name__ == "__main__":
    main()
