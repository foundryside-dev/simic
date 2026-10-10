"""Fleet C1-S (PDR-0057 G1 supplement; simic-e3803e8200): Fleet C1's deficit screen, static born at tau.

Fleet C1's static arm reads tau's host features in eval mode, so on a BatchNorm host it is born at
about 1/30 of tau (pilot: realised ratio 0.0013-0.0018 against 0.05). Its deficit screen on those
hosts cannot tell "no deficit" from that defect. John chose, in session on 2026-10-10, to keep
the fleet running and screen the BatchNorm hosts again afterwards with the corrected arm
(`atlas.Unit.static(..., calibration="train")`, `static_calibrated`).

The supplement trains only the corrected arm, on Fleet C1's own seeds, data and futures, and
reads it against Fleet C1's sealed no-growth and graft arms (the parent fleet):
- screen, per BatchNorm host, exactly as PDR-0057 and `c1_study.evaluate` define it: static beats
  no-growth by more than `deficit_min_gain` with the 95% lower bound above 0, and static diverges
  no more often than `static_divergence_cap`. The parent's registered screen is shown beside it;
- graft minus static_calibrated, descriptive;
- pairing: on the first `pairing_seeds` seeds the unit also re-trains no-growth on every
  BatchNorm host, and static_calibrated on the control host (no BatchNorm, where the corrected and
  registered arms are the same function). Both must equal the parent's records bit for bit, or
  the supplement makes no reading (`pairing_failure`).

The control host's screen is the parent's: there the two arms are one arm, which the pairing
check confirms on GPU. On every seed the corrected arm must also start where the parent's static
arm started (birth hashes that do not depend on the calibration mode, the future and the data),
and must have been born at tau.

Order (statistics review): a confirmatory launch needs the parent finished and is refused once
the parent's own report exists, so nothing here is chosen after the parent's results are known;
the plan pins the source of every module the arm and the reading run through. The analysis waits
for the parent's report. The registered BatchNorm screen never enters Fleet A: if this
supplement makes no reading, those hosts are unscreened and John decides. `c1_study` is
unchanged: the parent's snapshot analyses the parent.
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

from experiments import atlas
from experiments import c1_study as c1
from experiments.bounded_comparison import REPO, append_record, git_identity, read_json, runtime, source_identity, strict_json, write_json
from experiments.bounded_data import RunSpec, file_hash
from experiments.bounded_screen import binomial_bounds, interval, make_snapshot, visible_gpus
from experiments.kernel_demo import DESIGNED_WINNER, PATHOLOGIES

ARM = "static_calibrated"
REPORT = "c1s_report.json"
SCHEMA = "c1s-v1"
NO_BN_HOSTS = ("under_normalized",)  # kernel_demo Host: use_bn = pathology != "under_normalized"
PLAN_KEYS = {
    "study",
    "parent",
    "units",
    "hosts",
    "control_host",
    "pairing_seeds",
    "config",
    "data_identity",
    "criteria",
    "source_sha256",
    "fallback",
}
OPTIONAL_PLAN_KEYS = {"predictions", "disclosures", "deviations", "acceptance"}
SOURCE_FILES = tuple(
    f"experiments/{name}"
    for name in (
        "c1s_study.py",
        "c1_study.py",
        "atlas.py",
        "atlas_static.py",
        "atlas_fast.py",
        "atlas_hosts.py",
        "bounded_comparison.py",
        "bounded_data.py",
        "bounded_screen.py",
        "kernel_demo.py",
    )
)
# Birth fields that do not depend on the calibration mode: the corrected arm must start where the parent's static did.
IDENTITY_BIRTH_KEYS = (
    "body_init_sha256",
    "seed_before_calibration_sha256",
    "calibration_inputs_sha256",
    "calibration_examples",
    "host_unchanged_sha256",
    "host_optimizer_preserved_sha256",
)
TAU_TOLERANCE = 0.05  # relative; kernel_demo's tau self-test tolerance
CRITERIA_KEYS = {"deficit_min_gain", "static_divergence_cap", "max_failed_units"}
DESCRIPTIVE_LEVEL = c1.DESCRIPTIVE_LEVEL


# --- the plan ---


def load_parent_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    path = REPO / plan["parent"]["plan"]
    if file_hash(path) != plan["parent"]["plan_sha256"]:
        raise ValueError("the parent plan differs from the pinned sha256")
    return c1.load_plan(path), path


def load_plan(path: Path) -> dict[str, Any]:
    plan: dict[str, Any] = json.loads(path.read_text())
    if not set(plan) >= PLAN_KEYS or not set(plan) <= PLAN_KEYS | OPTIONAL_PLAN_KEYS:
        raise ValueError(f"plan keys must be {sorted(PLAN_KEYS)} plus optional {sorted(OPTIONAL_PLAN_KEYS)}")
    if set(plan["criteria"]) != CRITERIA_KEYS:
        raise ValueError(f"criteria keys must be exactly {sorted(CRITERIA_KEYS)}")
    if set(plan["parent"]) != {"plan", "plan_sha256", "root"}:
        raise ValueError("parent must pin plan, plan_sha256 and root")
    if not isinstance(plan["study"].get("pilot", False), bool):
        raise ValueError("study.pilot must be a boolean")
    parent, _ = load_parent_plan(plan)
    for key in ("units", "config", "data_identity"):
        if plan[key] != parent[key]:
            raise ValueError(f"{key} must equal the parent's: the supplement pairs on the parent's seeds, data and futures")
    for key in ("deficit_min_gain", "static_divergence_cap"):
        if plan["criteria"][key] != parent["criteria"][key]:
            raise ValueError(f"criteria.{key} must equal the parent's: the screen is unchanged, only the arm is corrected")
    hosts, control = plan["hosts"], plan["control_host"]
    if len(set(hosts)) != len(hosts) or set(hosts) != {h for h in parent["hosts"] if h not in NO_BN_HOSTS}:
        raise ValueError("hosts must be exactly the parent's BatchNorm hosts; a host without BatchNorm is the control")
    if control not in NO_BN_HOSTS or control not in parent["hosts"]:
        raise ValueError("the control host must be a parent host without BatchNorm")
    if type(plan["pairing_seeds"]) is not int or not 1 <= plan["pairing_seeds"] <= plan["units"]["count"]:
        raise ValueError("pairing_seeds must be an int between 1 and the unit count")
    if type(plan["criteria"]["max_failed_units"]) is not int or plan["criteria"]["max_failed_units"] < 0:
        raise ValueError("max_failed_units must be a non-negative int")
    if set(plan["source_sha256"]) != set(SOURCE_FILES):
        raise ValueError(f"source_sha256 must pin exactly {list(SOURCE_FILES)}")
    if not isinstance(plan["fallback"], str) or not plan["fallback"]:
        raise ValueError("the plan must state what happens when the supplement makes no reading")
    return plan


def check_sources(plan: dict[str, Any], root: Path) -> None:
    """The arm and the reading run through exactly the pinned source (statistics review)."""
    changed = [name for name in SOURCE_FILES if file_hash(root / name) != plan["source_sha256"][name]]
    if changed:
        raise RuntimeError(f"source differs from the plan's pins: {changed}")


def unit_seeds(plan: dict[str, Any]) -> list[int]:
    return c1.unit_seeds(plan)


def pairing_seeds(plan: dict[str, Any]) -> list[int]:
    return unit_seeds(plan)[: plan["pairing_seeds"]]


def expected_rows(plan: dict[str, Any], seed: int) -> set[tuple[str, str]]:
    rows = {(h, ARM) for h in plan["hosts"]}
    if seed in pairing_seeds(plan):
        rows |= {(h, "no_growth") for h in plan["hosts"]} | {(plan["control_host"], ARM)}
    return rows


def analysis_module_hash() -> str:
    return file_hash(Path(__file__))


# --- one unit: the corrected static arm on every BatchNorm host, and the pairing arms ---


def run_unit(plan: dict[str, Any], seed: int, output: Path, data_root: Path | None, plan_sha256: str) -> dict[str, Any]:
    """The manifest first, a row as each arm finishes, then complete.json seals the unit."""
    if output.exists():
        raise FileExistsError("output must be a fresh directory")
    parent, _ = load_parent_plan(plan)  # specs are the parent's, exactly: same config, seed, decision epoch
    epochs, d = plan["config"]["epochs"], parent["decision_epoch"]
    pairing = seed in pairing_seeds(plan)
    hosts = [*plan["hosts"], *([plan["control_host"]] if pairing else [])]
    base = atlas.Unit.load(c1.unit_spec(parent, seed, hosts[0]), data_root)
    c1._check_identity(base.provenance, plan["data_identity"])
    units = {h: dataclasses.replace(base, spec=c1.unit_spec(parent, seed, h)) for h in hosts}
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    write_json(
        output / "manifest.json",
        {
            "schema": SCHEMA,
            "study": plan["study"]["id"],
            "prereg_sha256": plan_sha256,
            "seed": seed,
            "pairing": pairing,
            "hosts": {h: {"label": u.host_label, "designed": DESIGNED_WINNER[h]} for h, u in units.items()},
            "data": base.provenance,
            "future_sha256": base.future.hash,
            "source": {
                **source_identity(),
                **{f"experiments/{n}": file_hash(here / n) for n in ("atlas.py", "atlas_static.py", "c1_study.py", "c1s_study.py")},
            },
            "git": git_identity(),
            "runtime": runtime(base.spec),
        },
    )
    count = 0
    with (output / "arms.jsonl").open("x") as fh:

        def emit(host: str, arm: str, unit: atlas.Unit, span: atlas.Span) -> None:
            nonlocal count
            installed = span.records[-1]["installed_parameters"] if span.records else 0
            append_record(fh, {**c1._row(seed, host, arm, unit.host_label, span, epochs, installed), "schema": SCHEMA})
            count += 1

        for host in plan["hosts"]:
            unit = units[host]
            emit(host, ARM, unit, unit.static(DESIGNED_WINNER[host], calibration="train"))
            if pairing:
                emit(host, "no_growth", unit, unit.trunk(decision_points=(d,)))  # as the parent trained it
        if pairing:
            control = units[plan["control_host"]]
            emit(plan["control_host"], ARM, control, control.static(DESIGNED_WINNER[plan["control_host"]], calibration="train"))
    completion = {
        "schema": SCHEMA,
        "status": "complete",
        "rows": count,
        "artifacts": {name: file_hash(output / name) for name in ("manifest.json", "arms.jsonl")},
    }
    write_json(output / "complete.json", completion)
    return completion


def verify_unit(root: Path, plan: dict[str, Any], *, seed: int, plan_sha256: str, commit: str) -> list[dict[str, Any]]:
    """Refuse a changed, foreign or malformed unit; return its rows."""
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
    c1._check_identity(manifest["data"], plan["data_identity"])
    rows = [json.loads(line) for line in (root / "arms.jsonl").read_text().splitlines()]
    keys = [(r["host"], r["arm"]) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != expected_rows(plan, seed):
        raise ValueError("unit rows differ from the plan")
    for r in rows:
        if r["seed"] != seed:
            raise ValueError("unit identity: a row belongs to another seed")
        if r["status"] not in ("completed", "diverged") or (r["status"] == "completed") != (r["late_ce"] is not None):
            raise ValueError(f"inconsistent status for {r['host']}/{r['arm']}")
        if r["late_ce"] is not None and not math.isfinite(r["late_ce"]):
            raise ValueError("a completed arm must have a finite late CE")
        if r["arm"] == ARM:  # the correction must have taken effect (PyTorch review)
            birth = r["birth"] or {}
            ratio = birth.get("realised_ratio_at_birth")
            tau = RunSpec(**plan["config"]).tau  # as the run's spec has it, default included
            if birth.get("calibration_mode") != "train":
                raise ValueError(f"{r['host']}/{ARM} was not calibrated in train mode")
            if not isinstance(ratio, float) or not math.isfinite(ratio) or abs(ratio - tau) > TAU_TOLERANCE * tau:
                raise ValueError(f"{r['host']}/{ARM} was born at ratio {ratio}, not tau = {tau}")
    return rows


# --- the reading ---


def _summary(row: dict[str, Any]) -> dict[str, Any]:
    return {"status": row["status"], "late_ce": row["late_ce"]}


def pairing_check(own: list[dict[str, Any]], parent: list[dict[str, Any]], control_host: str) -> list[str]:
    """Mismatches between this unit's pairing rows and the parent's; empty when every one is bitwise equal."""
    theirs = {(r["host"], r["arm"]): r for r in parent}
    problems = []
    for r in own:
        if r["arm"] == "no_growth":
            want = theirs[(r["host"], "no_growth")]
            records = r["records"]
            same = records == want["records"]
        elif r["host"] == control_host:
            want = theirs[(r["host"], "static")]
            records = [{**rec, "arm": "static"} for rec in r["records"]]
            birth = {k: v for k, v in (r["birth"] or {}).items() if k != "calibration_mode"}
            same = records == want["records"] and birth == want["birth"]
        else:
            continue
        same = same and all(r[k] == want[k] for k in ("initial_dev", "diverged", "costs"))
        if not same:
            problems.append(f"seed {r['seed']} {r['host']}/{r['arm']}")
    return problems


def identity_check(
    own: list[dict[str, Any]], parent: list[dict[str, Any]], own_manifest: dict[str, Any], parent_manifest: dict[str, Any]
) -> list[str]:
    """Every seed: the same future and data as the parent, and each corrected arm born from the parent's static start."""
    seed = own_manifest["seed"]
    problems = [f"seed {seed} {key}" for key in ("future_sha256", "data") if own_manifest[key] != parent_manifest[key]]
    theirs = {(r["host"], r["arm"]): r for r in parent}
    for r in own:
        if r["arm"] != ARM:
            continue
        want = theirs[(r["host"], "static")]["birth"] or {}
        if any((r["birth"] or {}).get(k) != want.get(k) for k in IDENTITY_BIRTH_KEYS):
            problems.append(f"seed {seed} {r['host']}/{ARM} birth")
    return problems


def evaluate(units: list[dict[str, Any]], criteria: dict[str, Any], parent_screen: dict[str, Any]) -> dict[str, Any]:
    """Per (seed, BatchNorm host): the parent's no_growth, graft and static, and this fleet's static_calibrated.

    The screen is `c1_study.evaluate`'s, term for term, with static_calibrated in static's place.
    """
    hosts = sorted({u["host"] for u in units}, key=lambda h: list(PATHOLOGIES).index(h))
    screen: dict[str, Any] = {}
    graft_minus: dict[str, Any] = {}
    failures: dict[str, Any] = {}
    completed_only: dict[str, Any] = {}
    corrected_minus_registered: dict[str, Any] = {}
    for host in hosts:
        rows = sorted((u for u in units if u["host"] == host), key=lambda u: u["seed"])
        score = {arm: np.array([c1._score(u["arms"][arm]) for u in rows]) for arm in ("no_growth", "graft", "static", ARM)}
        gain = interval(score["no_growth"] - score[ARM], DESCRIPTIVE_LEVEL)  # positive: static helps
        k = sum(u["arms"][ARM]["status"] != "completed" for u in rows)
        rate = k / len(rows)
        unstable = rate > criteria["static_divergence_cap"]
        screen[host] = {
            "n": len(rows),
            "static_gain": gain,
            "static_divergence_rate": rate,
            "unstable": unstable,
            "passes": gain["mean"] > criteria["deficit_min_gain"] and gain["lower"] > 0 and not unstable,
            "registered": parent_screen.get(host),
        }
        graft_minus[host] = {"n": len(rows), **interval(score["graft"] - score[ARM], DESCRIPTIVE_LEVEL)}
        failures[host] = {ARM: {"diverged": k, "n": len(rows), **binomial_bounds(k, len(rows))}}
        # Descriptive (statistics review): "failed by instability" apart from "no deficit", and the defect's size.
        both = [i for i, u in enumerate(rows) if u["arms"][ARM]["status"] == u["arms"]["no_growth"]["status"] == "completed"]
        completed_only[host] = (
            {"n": len(both), **interval((score["no_growth"] - score[ARM])[both], DESCRIPTIVE_LEVEL)} if len(both) > 1 else None
        )
        corrected_minus_registered[host] = {"n": len(rows), **interval(score[ARM] - score["static"], DESCRIPTIVE_LEVEL)}
    return {
        "deficit_screen": screen,
        "graft_minus_static_calibrated": graft_minus,
        "static_gain_completed_only": completed_only,
        "corrected_minus_registered_static": corrected_minus_registered,
        "failures": failures,
    }


# --- launch and analyze ---


def _parent_root(plan: dict[str, Any]) -> Path:
    return Path(plan["parent"]["root"])


def launch(root: Path, data_root: Path, workers: int, plan_path: Path, resume: bool = False) -> dict[str, Any]:
    """`c1_study.launch` for this module's units: a snapshot, one process per GPU, after the parent finished."""
    plan = load_plan(plan_path)
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be a positive int")
    parent_root = _parent_root(plan)
    if not (parent_root / "launch-finished.json").is_file():
        raise RuntimeError("the parent fleet has not finished; the supplement runs after it")
    if read_json(parent_root / "launch.json")["prereg_sha256"] != plan["parent"]["plan_sha256"]:
        raise RuntimeError("the parent root was launched from another plan")
    if not resume and not plan["study"].get("pilot", False) and (parent_root / c1.REPORT).exists():
        raise RuntimeError("the parent's report exists: a confirmatory supplement launches before the parent's results are read")
    check_sources(plan, REPO)
    try:
        plan_in_repo = plan_path.resolve().relative_to(REPO)
    except ValueError as error:
        raise ValueError("the plan must be committed inside the repository, so the snapshot holds it") from error
    c1._check_inputs(load_parent_plan(plan)[0], data_root)
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
    snapshot_plan = snapshot / plan_in_repo

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
                command = [sys.executable, "-B", "-m", "experiments.c1s_study", "unit", "--plan", str(snapshot_plan), "--seed", str(seed)]
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
    parent_plan, _ = load_parent_plan(plan)
    launched = read_json(root / "launch.json")
    if not Path(__file__).resolve().is_relative_to(Path(launched["snapshot"]).resolve()):
        raise ValueError(f"analysis must run from the launch snapshot {launched['snapshot']}, not the live checkout")
    if launched["prereg_sha256"] != file_hash(plan_path):
        raise ValueError("pre-registration changed after launch")
    if launched["analysis_module_sha256"] != analysis_module_hash():
        raise ValueError("analysis module changed since launch")
    check_sources(plan, REPO)
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
    parent_root = _parent_root(plan)
    parent_launch = read_json(parent_root / "launch.json")
    if parent_launch["prereg_sha256"] != plan["parent"]["plan_sha256"]:
        raise ValueError("the parent root was launched from another plan")
    parent_report_path = parent_root / c1.REPORT
    if not parent_report_path.is_file():
        raise ValueError("the parent fleet's own analysis must publish first")
    parent_report = read_json(parent_report_path)

    units: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for seed in unit_seeds(plan):
        try:
            parent_dir = parent_root / "units" / f"seed-{seed}"
            parent_summary = c1.verify_unit(
                parent_dir, parent_plan, seed=seed, plan_sha256=parent_launch["prereg_sha256"], commit=parent_launch["git"]["commit"]
            )
            parent_rows = [json.loads(line) for line in (parent_dir / "arms.jsonl").read_text().splitlines()]
            own_dir = root / "units" / f"seed-{seed}"
            own = verify_unit(own_dir, plan, seed=seed, plan_sha256=launched["prereg_sha256"], commit=launched["git"]["commit"])
            manifests = read_json(own_dir / "manifest.json"), read_json(parent_dir / "manifest.json")
        except Exception as error:  # every failure is recorded, never silently dropped
            failures.append({"seed": seed, "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
            continue
        mismatches += identity_check(own, parent_rows, *manifests)
        mismatches += pairing_check(own, parent_rows, plan["control_host"])
        by_host = {s["host"]: s for s in parent_summary}
        for r in own:
            if r["arm"] == ARM and r["host"] in plan["hosts"]:
                arms = {a: by_host[r["host"]]["arms"][a] for a in ("no_growth", "graft", "static")}
                units.append({"seed": seed, "host": r["host"], "arms": {**arms, ARM: _summary(r)}})
    if not units:
        raise RuntimeError(f"no unit is analysable ({len(failures)} failed seeds); nothing published")
    report: dict[str, Any] = {
        "study": plan["study"]["id"],
        "plan_sha256": launched["prereg_sha256"],
        "parent": {
            "study": parent_plan["study"]["id"],
            "plan": plan["parent"]["plan"],
            "plan_sha256": parent_launch["prereg_sha256"],
            "commit": parent_launch["git"]["commit"],
            "report_sha256": file_hash(parent_report_path),
            "control_host_screen": parent_report["deficit_screen"].get(plan["control_host"]),
            "reading": parent_report["reading"],
        },
        "analysis_git": git_identity(),
        "analyzed_unix": time.time(),
        "failed_seeds": failures,
        "pairing": {"seeds": pairing_seeds(plan), "mismatches": mismatches},
        **evaluate(units, plan["criteria"], parent_report["deficit_screen"]),
    }
    failed_units = len(failures) * len(plan["hosts"])
    report["failed_units"] = failed_units
    checked = [s for s in pairing_seeds(plan) if s not in {f["seed"] for f in failures}]
    parent_reading = parent_report["reading"]
    parent_ok = parent_reading["instrument"] == "ok" and (plan["study"].get("pilot", False) or not parent_reading.get("pilot", False))
    if not parent_ok:  # a voided parent voids the control's screen and the pairing (statistics review)
        instrument = "parent_failure"
    elif mismatches or not checked:
        instrument = "pairing_failure"
    elif failed_units > plan["criteria"]["max_failed_units"]:
        instrument = "instrument_failure"
    else:
        instrument = "ok"
    control = report["parent"]["control_host_screen"]
    hosts_passing: list[str] = []
    if instrument == "ok":
        hosts_passing = [plan["control_host"]] if control and control["passes"] else []
        hosts_passing += [h for h in plan["hosts"] if report["deficit_screen"].get(h, {}).get("passes")]
    report["reading"] = {"instrument": instrument, "fleet_a_hosts": hosts_passing}  # the registered BN screen never enters
    if plan["study"].get("pilot", False):
        report["reading"] = {"instrument": instrument, "pilot": True, "fleet_a_hosts": []}
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
