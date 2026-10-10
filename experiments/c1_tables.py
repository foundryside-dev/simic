"""Fleet C1 checkpoint tables: the published reports, rendered as Markdown, numbers untouched by hand.

    python -m experiments.c1_tables C1_REPORT [C1S_REPORT]

Reads `c1_report.json` (and, when given, `c1s_report.json`) and prints the decision tables the
C1 checkpoint goes to John with: G1 per host and step, the deficit screen (registered and, with
C1-S, corrected), graft minus static, lambda, divergences and the reading. Every number is
formatted from the report; nothing is recomputed, so the note cannot disagree with the record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HOST_ORDER = ("under_normalized", "channel_starved", "no_spatial_mix", "mild")


def _hosts(section: dict[str, Any]) -> list[str]:
    return sorted(section, key=lambda h: HOST_ORDER.index(h) if h in HOST_ORDER else len(HOST_ORDER))


def _num(value: float | None, places: int = 3) -> str:
    return "—" if value is None else f"{value:+.{places}f}"


def _ci(block: dict[str, Any]) -> str:
    return f"{_num(block['mean'])} [{_num(block['lower'])}, {_num(block['upper'])}]"


def _pct(rate: float | None) -> str:
    return "—" if rate is None else f"{100 * rate:.1f}%"


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def g1_table(report: dict[str, Any]) -> str:
    rows = []
    for host in _hosts(report["g1"]):
        g = report["g1"][host]
        for step in g["steps"] or [None]:
            if step is None:
                rows.append([host, g["role"], g["reading"], "—", "—", "—", "—", _pct(g["graft_divergence"])])
                continue
            mean = f"{_num(step['mean'])} (upper {_num(step['mean_upper'])})"
            trimmed = f"{_num(step['trimmed'])} (upper {_num(step['trimmed_upper'])})"
            comparator = _pct(g["comparator_divergence"].get(f"scale_x{step['m']:g}"))
            ni = "yes" if step["non_inferior"] else "no"
            rows.append(
                [host, g["role"], g["reading"], f"{step['m']:g}x", mean, trimmed, ni, f"{_pct(g['graft_divergence'])} / {comparator}"]
            )
    header = ["Host", "Role", "Reading", "m", "Graft - scale-up, mean", "Trimmed mean", "Non-inferior", "Divergence graft / comparator"]
    return _table(header, rows)


def screen_table(report: dict[str, Any], supplement: dict[str, Any] | None) -> str:
    rows = []
    corrected = supplement["deficit_screen"] if supplement else {}
    for host in _hosts(report["deficit_screen"]):
        s = report["deficit_screen"][host]
        row = [host, _ci(s["static_gain"]), _pct(s["static_divergence_rate"]), "pass" if s["passes"] else "fail"]
        if supplement is not None:
            c = corrected.get(host)
            row += (
                [_ci(c["static_gain"]), _pct(c["static_divergence_rate"]), "pass" if c["passes"] else "fail"]
                if c
                else ["same arm (no BatchNorm)", "", ""]
            )
        rows.append(row)
    header = ["Host", "Registered static gain [95%]", "Divergence", "Screen"]
    if supplement is not None:
        header += ["Corrected static gain [95%]", "Divergence", "Screen"]
    return _table(header, rows)


def graft_static_table(report: dict[str, Any], supplement: dict[str, Any] | None) -> str:
    rows = []
    corrected = supplement["graft_minus_static_calibrated"] if supplement else {}
    for host in _hosts(report["graft_minus_static"]):
        row = [host, _ci(report["graft_minus_static"][host])]
        if supplement is not None:
            row.append(_ci(corrected[host]) if host in corrected else "same arm")
        rows.append(row)
    header = ["Host", "Graft - registered static [95%]"] + (["Graft - corrected static [95%]"] if supplement else [])
    return _table(header, rows)


def lambda_table(report: dict[str, Any]) -> str:
    lam = report["lambda"]
    rows = [["pooled", _num(lam["slope"], 4), _num(lam["lambda"], 4)]]
    rows += [[h, _num(lam["per_host_slope"][h], 4), ""] for h in _hosts(lam["per_host_slope"])]
    sens = lam["sensitivity_failures_at_chance"]
    rows.append(["sensitivity (failures at ln 10)", _num(sens["slope"], 4), _num(sens["lambda"], 4)])
    return _table(["Fit", "Slope (nats per doubling)", "λ"], rows) + f"\n\nExcluded runs in the primary fit: {lam['excluded_runs']}."


def failures_table(report: dict[str, Any]) -> str:
    rows = []
    for host in _hosts(report["failures"]):
        for arm, f in sorted(report["failures"][host].items()):
            if f["diverged"]:
                rows.append([host, arm, f"{f['diverged']}/{f['n']}", f"[{_pct(f['lower_95'])}, {_pct(f['upper_95'])}]"])
    if not rows:
        return "No arm diverged."
    return _table(["Host", "Arm", "Diverged", "95% (Clopper-Pearson)"], rows)


def render(report: dict[str, Any], supplement: dict[str, Any] | None = None) -> str:
    reading = report["reading"]
    parts = [
        "### Reading",
        "",
        f"- Instrument: `{reading['instrument']}`; failed units {report['failed_units']}, failed seeds {len(report['failed_seeds'])}.",
        f"- C1: `{reading['c1']}`; on `mild`: `{reading.get('c1_mild', '—')}`.",
        f"- Fleet A hosts, registered screen: {reading['fleet_a_hosts']}.",
    ]
    if supplement is not None:
        pairing = supplement["pairing"]
        parts += [
            f"- Fleet C1-S: instrument `{supplement['reading']['instrument']}`; pairing seeds {len(pairing['seeds'])}, "
            f"mismatches {len(pairing['mismatches'])}; failed units {supplement['failed_units']}.",
            f"- Fleet A hosts, corrected screen: {supplement['reading']['fleet_a_hosts']}.",
        ]
    parts += [
        "",
        "### G1: graft against uniform scale-up",
        "",
        g1_table(report),
        "",
        "### Deficit screen",
        "",
        screen_table(report, supplement),
        "",
        "### Graft minus static (descriptive)",
        "",
        graft_static_table(report, supplement),
        "",
        "### λ, the cost price",
        "",
        lambda_table(report),
        "",
        "### Divergences",
        "",
        failures_table(report),
    ]
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not 1 <= len(args) <= 2:
        raise SystemExit("usage: python -m experiments.c1_tables C1_REPORT [C1S_REPORT]")
    report = json.loads(Path(args[0]).read_text())
    supplement = json.loads(Path(args[1]).read_text()) if len(args) == 2 else None
    sys.stdout.write(render(report, supplement))


if __name__ == "__main__":
    main()
