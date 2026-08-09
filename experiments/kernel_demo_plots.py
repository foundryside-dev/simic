"""Plotting sidecar for the kernel demo — standalone, matplotlib-only.

Reads eval_results.json (--results) and/or a record store (--store), writes
PNGs under --out. Deliberately OUTSIDE kernel_demo.py: plots never touch the
semantic surface, and the demo runs without matplotlib installed.

Reporting discipline, not decoration: this module never invents a datum. A
missing required field is an error, not a zero; a store holding more than one
experimental population is refused rather than pooled; an absent measurement
is labelled absent rather than plotted at the origin. Every run drops a
plot_manifest.json recording which records were selected.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterator
from itertools import islice
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.kernel_demo import AGREEMENT_MARGIN, SEED_NAMES, FanRecord, Store, end_state_R

SPIKE_CRASH_MARGIN = 0.05  # spike-then-crash = max exceeds end-state R by more than this
MAX_ALPHA_BETA_ARMS = 4  # legend stays readable; 2 lines drawn per arm


class PlotDataError(ValueError):
    """A required input was missing, malformed, or ambiguous."""


def require_number(mapping: dict[str, object], key: str, context: str) -> float:
    # Direct indexing, not .get(<default>): a wrong or truncated results file
    # must fail here rather than become a chart of zeros.
    try:
        value = mapping[key]
    except KeyError as exc:
        raise PlotDataError(f"{context}: missing required field {key!r}") from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlotDataError(f"{context}.{key}: expected number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        # _sanitize_json writes non-finite as null; a finite-looking nan here
        # would mean the producer changed, so refuse rather than paper over it.
        raise PlotDataError(f"{context}.{key}: expected finite number, got {result!r}")
    return result


def require_dict(mapping: dict[str, object], key: str, context: str) -> dict[str, object]:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise PlotDataError(f"{context}: missing required section {key!r}") from exc
    if not isinstance(value, dict):
        raise PlotDataError(f"{context}.{key}: expected object, got {type(value).__name__}")
    return value


def _finite_points(curve: object, context: str) -> list[tuple[int, float]]:
    # Keeps the ORIGINAL index with each value. curve_val entries are null
    # wherever _sanitize_json saw a non-finite number; dropping them and
    # replotting at contiguous x would silently relabel the epoch axis.
    if not isinstance(curve, list):
        raise PlotDataError(f"{context}: expected a list, got {type(curve).__name__}")
    points: list[tuple[int, float]] = []
    for i, v in enumerate(curve):
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise PlotDataError(f"{context}[{i}]: expected number or null, got {v!r}")
        f = float(v)
        if math.isfinite(f):
            points.append((i, f))
    return points


def _gapped(points: list[tuple[int, float]]) -> tuple[list[int], list[float]]:
    # nan at the dropped indices so matplotlib leaves a visible gap and the
    # x positions stay the true epoch numbers.
    if not points:
        return [], []
    xs = list(range(points[0][0], points[-1][0] + 1))
    by_x = dict(points)
    return xs, [by_x.get(x, math.nan) for x in xs]


def _spike_then_crash(points: list[tuple[int, float]]) -> bool:
    # end_state_R is the kernel's definition (mean of the final three) and it
    # raises below three entries — guard rather than let one short or diverged
    # arm abort the whole plot run. Note this consumes the FINITE values,
    # while the x axis above keeps the original indices: the two views of the
    # curve are deliberately different and must not be merged.
    vals = [v for _, v in points]
    if len(vals) < 3:
        return False
    return max(vals) > end_state_R(vals) + SPIKE_CRASH_MARGIN


def _provenance(rec: FanRecord) -> str:
    return f"{rec.seed_namespace}/{rec.split_role} fan_epoch={rec.fan_epoch}"


def _load_fans(
    store_root: str,
    *,
    namespace: str | None,
    split_role: str | None,
    include_refans: bool,
    manifest_hash: str | None,
) -> list[FanRecord]:
    # A store legitimately holds preflight, train, tune and eval populations
    # across several manifest generations. Pooling them into one boxplot would
    # be a fabricated aggregate, so select explicitly and refuse ambiguity.
    root = Path(store_root)
    shards = root / "shards"
    # Both checks precede Store(...), whose constructor mkdirs shards: a
    # mistyped --store must not create a new empty store and then report
    # success over blank plots.
    if not root.is_dir():
        raise PlotDataError(f"store does not exist: {root}")
    if not shards.is_dir():
        raise PlotDataError(f"store has no shards directory: {shards}")

    kinds = ("fan", "refan") if include_refans else ("fan",)
    store = Store(str(root))
    # Store.load is the kernel's own split_role accessor — reuse it so the
    # split semantics stay defined in one place. It cannot express namespace
    # or manifest, so those filter here.
    records = store.load(split_role, kinds) if split_role is not None else [r for r in store.merge() if r.kind in kinds]

    if namespace is not None:
        records = [r for r in records if r.seed_namespace == namespace]
    if manifest_hash is not None:
        records = [r for r in records if r.manifest_hash == manifest_hash]

    if not records:
        raise PlotDataError(
            f"no records in {root} matched kinds={kinds} namespace={namespace!r} split_role={split_role!r} manifest={manifest_hash!r}"
        )

    namespaces = sorted({r.seed_namespace for r in records})
    if namespace is None and len(namespaces) > 1:
        raise PlotDataError(f"store holds several seed namespaces {namespaces}; select one with --namespace")
    manifests = sorted({r.manifest_hash for r in records if r.manifest_hash is not None})
    if manifest_hash is None and len(manifests) > 1:
        raise PlotDataError(f"store holds several manifest generations {manifests}; select one with --manifest")
    return records


def plot_example_arm_curves(fans: list[FanRecord], out: Path) -> dict[str, str]:
    # "example", not "the": one record per pathology, chosen by the store's
    # canonical merge order. Reproducible but not representative, so the
    # selection is titled and recorded rather than left implicit.
    by_path: dict[str, FanRecord] = {}
    for r in fans:
        by_path.setdefault(r.pathology_id, r)
    if not by_path:
        raise PlotDataError("no fan records to plot arm curves for")

    selected = sorted(by_path.items())
    fig, axes = plt.subplots(1, len(selected), figsize=(4 * len(selected), 3.4), squeeze=False)
    try:
        for ax, (path, rec) in zip(axes[0], selected, strict=True):
            for a in rec.arms:
                curve = a.get("curve_val")
                if curve is None:
                    continue
                points = _finite_points(curve, f"{rec.fan_id}:{a['name']}.curve_val")
                if not points:
                    continue
                label = str(a["name"])
                if _spike_then_crash(points):
                    label += " (spike-then-crash)"
                xs, ys = _gapped(points)
                ax.plot(xs, ys, label=label)
            ax.set_title(f"{path}\n{_provenance(rec)}", fontsize=8)
            ax.set_xlabel("epoch (arm-local)")
            ax.set_ylabel("val acc")
            handles, _ = ax.get_legend_handles_labels()
            if handles:
                ax.legend(fontsize=6)
            else:
                ax.text(0.5, 0.5, "no plottable curve_val", transform=ax.transAxes, ha="center", fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "example_arm_curves.png", dpi=150)
    finally:
        plt.close(fig)
    return {path: rec.fan_id for path, rec in selected}


def _logged_arms(fans: list[FanRecord]) -> Iterator[tuple[FanRecord, dict[str, object], list[object]]]:
    for rec in fans:
        for a in rec.arms:
            log = a.get("alpha_beta_log")
            if isinstance(log, list) and log:
                yield rec, a, log


def plot_alpha_beta(fans: list[FanRecord], out: Path) -> list[str]:
    # islice, not a counter checked between records: the old bound only
    # stopped BETWEEN records, so a record carrying the optional nullseed arm
    # drew five arms instead of four. Bounded by construction now.
    fig, ax = plt.subplots(figsize=(6, 3.4))
    identities: list[str] = []
    try:
        for rec, arm, log in islice(_logged_arms(fans), MAX_ALPHA_BETA_ARMS):
            name = str(arm["name"])
            alphas: list[float] = []
            betas: list[float] = []
            for i, pair in enumerate(log):
                ctx = f"{rec.fan_id}:{name}.alpha_beta_log[{i}]"
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise PlotDataError(f"{ctx}: expected an (alpha, beta) pair, got {pair!r}")
                alphas.append(require_number({"alpha": pair[0]}, "alpha", ctx))
                betas.append(require_number({"beta": pair[1]}, "beta", ctx))
            # alpha_beta_log is appended at the END of epoch_tick, so entry 0
            # is the state after the first completed post-germination epoch.
            epochs = range(1, len(log) + 1)
            identity = f"{rec.pathology_id}@{rec.fan_epoch}:{name}"
            ax.plot(epochs, alphas, label=f"alpha {identity}", alpha=0.7)
            ax.plot(epochs, betas, "--", label=f"beta {identity}", alpha=0.7)
            identities.append(f"{rec.fan_id}:{name}")
        if not identities:
            raise PlotDataError("no arm carried a non-empty alpha_beta_log")
        ax.set_xlabel("completed epochs since germination")
        ax.set_ylabel("gate value")
        ax.set_title("alpha/beta trajectories")
        ax.legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(out / "alpha_beta.png", dpi=150)
    finally:
        plt.close(fig)
    return identities


def plot_money_chart_trio(results: dict[str, object], out: Path) -> None:
    mc = require_dict(results, "money_chart", "results")
    ag = require_dict(results, "agreement", "results")
    fal = require_dict(results, "falsifier", "results")
    matched = require_number(mc, "matched", "money_chart")
    money_p = require_number(mc, "p", "money_chart")
    teacher_forced = require_number(ag, "teacher_forced", "agreement")
    majority = require_number(ag, "majority_null", "agreement")
    schedule_only = require_number(ag, "schedule_only_null", "agreement")
    deranged = require_number(fal, "deranged_agreement", "falsifier")
    null_ci_hi = require_number(fal, "null_ci_hi", "falsifier")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
    try:
        # Each panel carries its pre-registered verdict rule as a dashed line:
        # the value alone does not say whether the gate passed.
        axes[0].bar(["matched"], [matched])
        axes[0].axhline(3, linestyle="--", color="k", label="required matches")
        axes[0].set_ylim(0, 4.2)
        axes[0].set_title(f"money chart (p={money_p:.3f})")
        axes[0].legend(fontsize=6)

        axes[1].bar(["teacher-forced", "majority", "schedule-only"], [teacher_forced, majority, schedule_only])
        axes[1].axhline(majority + AGREEMENT_MARGIN, linestyle="--", color="k", label=f"majority + {AGREEMENT_MARGIN}")
        axes[1].set_ylim(0, 1)
        axes[1].set_title("agreement vs nulls")
        axes[1].legend(fontsize=6)

        axes[2].bar(["deranged"], [deranged])
        axes[2].axhline(null_ci_hi, linestyle="--", color="k", label="null CI upper bound")
        axes[2].set_ylim(0, 1)
        axes[2].set_title("falsifier twin")
        axes[2].legend(fontsize=6)

        fig.tight_layout()
        fig.savefig(out / "money_chart_trio.png", dpi=150)
    finally:
        plt.close(fig)


def plot_tune_curve(store_root: str, out: Path) -> bool:
    path = Path(store_root) / "policies" / "trained.json"
    if not path.exists():
        return False  # no trained policy yet is a legitimate store state
    meta = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise PlotDataError(f"{path}: expected an object")
    # The single writer always emits 'curve', so absence means a foreign or
    # truncated file. An EMPTY curve is different and legitimate: train_policy
    # only appends when a tune batch exists, so an empty tune split yields no
    # checkpoint evaluations and there is nothing to plot.
    if "curve" not in meta:
        raise PlotDataError(f"{path}: missing required field 'curve'")
    curve = meta["curve"]
    if isinstance(curve, list) and not curve:
        return False
    points = _finite_points(curve, f"{path}:curve")
    if not points:
        raise PlotDataError(f"{path}: 'curve' has entries but none are finite")
    fig, ax = plt.subplots(figsize=(5, 3))
    try:
        xs, ys = _gapped(points)
        ax.plot(xs, ys, marker="o")
        ax.set_xlabel("checkpoint eval")
        ax.set_ylabel("tune loss")
        ax.set_title("tune curve (trained)")
        fig.tight_layout()
        fig.savefig(out / "tune_curve.png", dpi=150)
    finally:
        plt.close(fig)
    return True


def plot_rms_blend_entry(fans: list[FanRecord], out: Path) -> list[str]:
    per_seed: dict[str, list[float]] = {n: [] for n in SEED_NAMES}
    for r in fans:
        for a in r.arms:
            name = str(a["name"])
            if name not in per_seed:
                continue
            v = a.get("rms_ratio_blend_entry")
            if v is None:
                continue  # null = the arm never reached blend entry
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise PlotDataError(f"{r.fan_id}:{name}.rms_ratio_blend_entry: expected number or null, got {v!r}")
            if math.isfinite(float(v)):
                per_seed[name].append(float(v))

    # A seed with no measurement is OMITTED and named, never drawn at 0.0 —
    # the kernel treats an absent blend-entry measurement as a failure, and
    # zero would read as "the delta had no magnitude".
    series: list[list[float]] = []
    labels: list[str] = []
    missing: list[str] = []
    for name in SEED_NAMES:
        if per_seed[name]:
            series.append(per_seed[name])
            labels.append(f"{name}\n(n={len(per_seed[name])})")
        else:
            missing.append(name)
    if not series:
        raise PlotDataError("no RMS blend-entry measurements found")

    fig, ax = plt.subplots(figsize=(5, 3.4))
    try:
        ax.boxplot(series, tick_labels=labels)
        ax.set_ylabel("RMS(delta)/RMS(h) at blend entry")
        ax.set_title("RMS at blend entry")
        if missing:
            ax.text(
                0.99,
                0.02,
                f"No measurement: {', '.join(missing)}",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=7,
            )
        fig.tight_layout()
        fig.savefig(out / "rms_blend_entry.png", dpi=150)
    finally:
        plt.close(fig)
    return missing


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="kernel_demo_plots")
    ap.add_argument("--results", default=None)
    ap.add_argument("--store", default=None)
    ap.add_argument("--namespace", default=None, help="seed_namespace to select (refuses a mixed store without it)")
    ap.add_argument("--split-role", default=None, help="split_role to select")
    ap.add_argument("--manifest", default=None, help="manifest_hash to select (refuses a mixed store without it)")
    ap.add_argument("--include-refans", action="store_true")
    ap.add_argument("--out", default="runs/kernel_demo/plots")
    args = ap.parse_args(argv)
    if args.store is None and args.results is None:
        ap.error("at least one of --store or --results is required")

    # All input validation precedes the output mkdir: a bad invocation must
    # not litter a directory, same class of bug as Store() mkdir-ing shards.
    fans: list[FanRecord] | None = None
    results: dict[str, object] | None = None
    if args.store:
        fans = _load_fans(
            args.store,
            namespace=args.namespace,
            split_role=args.split_role,
            include_refans=args.include_refans,
            manifest_hash=args.manifest,
        )
    if args.results:
        loaded = json.loads(Path(args.results).read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise PlotDataError(f"{args.results}: expected a JSON object")
        results = loaded

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "results_path": args.results,
        "store_path": args.store,
        "namespace": args.namespace,
        "split_role": args.split_role,
        "manifest_hash": args.manifest,
        "include_refans": bool(args.include_refans),
        "written": [],
    }
    written: list[str] = []

    if fans is not None:
        manifest["record_count"] = len(fans)
        manifest["manifest_hashes_present"] = sorted({r.manifest_hash for r in fans if r.manifest_hash is not None})
        manifest["example_arm_curve_fan_ids"] = plot_example_arm_curves(fans, out)
        written.append("example_arm_curves.png")
        manifest["alpha_beta_arms"] = plot_alpha_beta(fans, out)
        written.append("alpha_beta.png")
        manifest["rms_seeds_without_measurement"] = plot_rms_blend_entry(fans, out)
        written.append("rms_blend_entry.png")
        if plot_tune_curve(args.store, out):
            written.append("tune_curve.png")
    if results is not None:
        plot_money_chart_trio(results, out)
        written.append("money_chart_trio.png")

    manifest["written"] = written
    (out / "plot_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"plots written to {out}: {', '.join(written)}")


if __name__ == "__main__":
    main()
