"""The C1 checkpoint tables are the reports, formatted: every host, step and reading, no number re-derived."""

from __future__ import annotations

from typing import Any

from experiments import c1_study as c1
from experiments import c1_tables
from experiments import c1s_study as c1s
from tests.unit import test_c1_study as tc1


def _reports() -> tuple[dict[str, Any], dict[str, Any]]:
    units = tc1._units(n=40, static_gain={"mild": 0.12, "channel_starved": 0.0})
    report = {**c1.evaluate(units, tc1.CRITERIA), "failed_units": 0, "failed_seeds": []}
    bn = [u for u in units if u["host"] != "under_normalized"]
    for u in bn:
        u["arms"][c1s.ARM] = dict(u["arms"]["static"])
    supplement = {
        **c1s.evaluate(bn, tc1.CRITERIA, report["deficit_screen"]),
        "pairing": {"seeds": [1, 2], "mismatches": []},
        "failed_units": 0,
        "reading": {"instrument": "ok", "fleet_a_hosts": ["under_normalized", "mild"]},
    }
    return report, supplement


def test_every_host_step_and_reading_appears_with_the_reports_numbers() -> None:
    report, _ = _reports()
    text = c1_tables.render(report)
    for host, g in report["g1"].items():
        assert host in text and g["reading"] in text
        for step in g["steps"]:
            assert f"{step['mean']:+.3f} (upper {step['mean_upper']:+.3f})" in text
    for s in report["deficit_screen"].values():
        assert c1_tables._ci(s["static_gain"]) in text
    assert f"{report['lambda']['lambda']:+.4f}" in text and report["reading"]["c1"] in text


def test_the_supplement_adds_the_corrected_screen_and_marks_the_control_as_the_same_arm() -> None:
    report, supplement = _reports()
    text = c1_tables.render(report, supplement)
    assert "Corrected static gain" in text and "same arm (no BatchNorm)" in text
    assert c1_tables._ci(supplement["deficit_screen"]["mild"]["static_gain"]) in text
    assert "mismatches 0" in text and "['under_normalized', 'mild']" in text
    assert c1_tables._ci(supplement["corrected_minus_registered_static"]["mild"]) in text
