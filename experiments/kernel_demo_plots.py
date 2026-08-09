"""Plotting sidecar for the kernel demo — standalone, matplotlib-only.

Reads eval_results.json (--results) and/or a record store (--store), writes
PNGs under --out. Deliberately OUTSIDE kernel_demo.py: plots never touch the
semantic surface, and the demo runs without matplotlib installed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.kernel_demo import SEED_NAMES, FanRecord, Store

SPIKE_CRASH_MARGIN = 0.05  # spike-then-crash = max exceeds end-state by more than this


def _load_fans(store_root: str) -> list[FanRecord]:
    return [r for r in Store(store_root).merge() if r.kind in ("fan", "refan")]


def plot_arm_curves(fans: list[FanRecord], out: Path) -> None:
    by_path: dict[str, FanRecord] = {}
    for r in fans:
        by_path.setdefault(r.pathology_id, r)
    fig, axes = plt.subplots(1, max(1, len(by_path)), figsize=(4 * max(1, len(by_path)), 3), squeeze=False)
    for ax, (path, rec) in zip(axes[0], sorted(by_path.items()), strict=False):
        for a in rec.arms:
            curve = a.get("curve_val")
            if not isinstance(curve, list) or not curve:
                continue
            vals = [v for v in curve if isinstance(v, (int, float))]
            label = str(a["name"])
            if vals and max(vals) > vals[-1] + SPIKE_CRASH_MARGIN:
                label += " (spike-then-crash)"
            ax.plot(vals, label=label)
        ax.set_title(path)
        ax.set_xlabel("epoch (arm-local)")
        ax.set_ylabel("val acc")
        ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(out / "arm_curves.png", dpi=150)
    plt.close(fig)


def plot_alpha_beta(fans: list[FanRecord], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 3))
    plotted = 0
    for r in fans:
        for a in r.arms:
            log = a.get("alpha_beta_log")
            if isinstance(log, list) and log:
                alphas = [pair[0] for pair in log]
                betas = [pair[1] for pair in log]
                ax.plot(alphas, label=f"alpha {a['name']}", alpha=0.7)
                ax.plot(betas, "--", label=f"beta {a['name']}", alpha=0.7)
                plotted += 1
        if plotted >= 4:
            break
    ax.set_xlabel("epoch since germination")
    ax.set_ylabel("gate value")
    ax.set_title("alpha/beta trajectories")
    if plotted:
        ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(out / "alpha_beta.png", dpi=150)
    plt.close(fig)


def plot_money_chart_trio(results: dict[str, object], out: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3))
    mc = results.get("money_chart", {})
    ag = results.get("agreement", {})
    fal = results.get("falsifier", {})
    assert isinstance(mc, dict) and isinstance(ag, dict) and isinstance(fal, dict)
    axes[0].bar(["matched"], [mc.get("matched", 0)])
    axes[0].set_ylim(0, 4)
    axes[0].set_title(f"money chart (p={mc.get('p', float('nan')):.3f})")
    axes[1].bar(
        ["teacher-forced", "majority", "schedule-only"],
        [ag.get("teacher_forced", 0.0), ag.get("majority_null", 0.0), ag.get("schedule_only_null", 0.0)],
    )
    axes[1].set_title("agreement vs nulls")
    axes[2].bar(["deranged", "null CI hi"], [fal.get("deranged_agreement", 0.0), fal.get("null_ci_hi", 0.0)])
    axes[2].set_title("falsifier twin")
    fig.tight_layout()
    fig.savefig(out / "money_chart_trio.png", dpi=150)
    plt.close(fig)


def plot_tune_curve(store_root: str, out: Path) -> None:
    path = Path(store_root) / "policies" / "trained.json"
    if not path.exists():
        return
    curve = json.loads(path.read_text(encoding="utf-8")).get("curve", [])
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(curve, marker="o")
    ax.set_xlabel("checkpoint eval")
    ax.set_ylabel("tune loss")
    ax.set_title("tune curve (trained)")
    fig.tight_layout()
    fig.savefig(out / "tune_curve.png", dpi=150)
    plt.close(fig)


def plot_rms_blend_entry(fans: list[FanRecord], out: Path) -> None:
    per_seed: dict[str, list[float]] = {n: [] for n in SEED_NAMES}
    for r in fans:
        for a in r.arms:
            v = a.get("rms_ratio_blend_entry")
            name = str(a["name"])
            if name in per_seed and isinstance(v, (int, float)):
                per_seed[name].append(float(v))
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.boxplot([per_seed[n] or [0.0] for n in SEED_NAMES], tick_labels=list(SEED_NAMES))
    ax.set_ylabel("RMS(delta)/RMS(h) at blend entry")
    ax.set_title("RMS at blend entry")
    fig.tight_layout()
    fig.savefig(out / "rms_blend_entry.png", dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="kernel_demo_plots")
    ap.add_argument("--results", default=None)
    ap.add_argument("--store", default=None)
    ap.add_argument("--out", default="runs/kernel_demo/plots")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.store:
        fans = _load_fans(args.store)
        plot_arm_curves(fans, out)
        plot_alpha_beta(fans, out)
        plot_rms_blend_entry(fans, out)
        plot_tune_curve(args.store, out)
    if args.results:
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
        plot_money_chart_trio(results, out)
    print(f"plots written to {out}")


if __name__ == "__main__":
    main()
