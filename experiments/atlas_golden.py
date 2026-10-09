"""PDR-0057 G0 golden check: the atlas reproduces rung 4's GPU records bitwise (wall time aside).

For each seed, one 10-epoch trunk with decision points 0, 1, 2, 3, 5 and a `norm` fork at each
must equal the rung-4 cells T0..T5. One 20-epoch trunk with a fork at 2 must equal H20. The
trunk must equal every cell's no_growth arm. Run on the same SKU, driver and build as rung 4:

    CUDA_VISIBLE_DEVICES=0 .venv/bin/python -B -m experiments.atlas_golden \
        --root runs/rung4-timing-horizon --data-root runs/cifar-fit-only --seeds 8001 8002 --out <json>
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

from experiments import atlas
from experiments.bounded_data import RunSpec, validated_spec

CELLS = {"T0": (0, 10), "T1": (1, 10), "T2": (2, 10), "T3": (3, 10), "T5": (5, 10), "H20": (2, 20)}


def _strip(record: dict[str, Any], arm: str | None = None) -> dict[str, Any]:
    out = {k: v for k, v in record.items() if k != "wall_s"}
    return out if arm is None else {**out, "arm": arm}


def first_difference(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> dict[str, Any] | None:
    """None when equal; otherwise where the two record lists first disagree."""
    if len(got) != len(want):
        return {"reason": "length", "got": len(got), "want": len(want)}
    for index, (a, b) in enumerate(zip(got, want, strict=True)):
        if a != b:
            keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            return {"reason": "record", "index": index, "epoch": b.get("epoch"), "keys": keys}
    return None


def _reference(run: Path, arm: str) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in (run / "training.jsonl").read_text().splitlines()]
    return [_strip(r) for r in rows if r["kind"] == "epoch" and r["arm"] == arm]


def check_seed(root: Path, data_root: Path, seed: int) -> dict[str, Any]:
    unit_dir = root / "units" / f"seed-{seed}"
    base = validated_spec(json.loads((unit_dir / "T2" / "manifest.json").read_text())["spec"])
    result: dict[str, Any] = {"seed": seed, "cells": {}}
    for epochs in (10, 20):
        spec: RunSpec = dataclasses.replace(base, epochs=epochs)
        cells = {c: t for c, (t, e) in CELLS.items() if e == epochs}
        unit = atlas.Unit.load(spec, data_root)
        trunk = unit.trunk(decision_points=tuple(sorted(set(cells.values()))))
        for cell, t in cells.items():
            run = unit_dir / cell
            no_growth = first_difference([_strip(r) for r in trunk.records], _reference(run, "no_growth"))
            branch = unit.branch(trunk.snapshots[t], action=spec.seed_type)
            got = [_strip(r, "scheduled") for r in trunk.records[:t]] + [_strip(r) for r in branch.records]
            scheduled = first_difference(got, _reference(run, "scheduled"))
            result["cells"][cell] = {"no_growth": no_growth, "scheduled": scheduled}
    result["equal"] = all(v is None for cell in result["cells"].values() for v in cell.values())
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    results = [check_seed(args.root, args.data_root, seed) for seed in args.seeds]
    report = {"all_equal": all(r["equal"] for r in results), "seeds": results}
    args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_equal": report["all_equal"], "seeds": {r["seed"]: r["equal"] for r in results}}))


if __name__ == "__main__":
    main()
