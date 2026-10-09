"""Atlas unit records (PDR-0057 G0, item 5): a mandatory no-op per decision point, failures kept as rows.

`run_unit` writes one seed's trunk and every (decision point, action, replicate) branch.
`verify_unit` refuses a unit that is missing a no-op, duplicates a branch, or whose replicate-0
no-op does not continue the trunk bitwise. `effects` scores each action against its own no-op,
with a diverged branch at chance-level CE, never dropped.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from experiments import atlas
from experiments.bounded_comparison import ArmDivergedError
from experiments.bounded_data import RunSpec

SPEC = RunSpec(epochs=7, host="mild", seed_type="conv_light", lifecycle="v2")  # a BN host: snapshots carry running stats
PLAN = {"decision_points": (1,), "actions": ("norm", "conv_light"), "replicates": (0, 1)}


@pytest.fixture(scope="module")
def unit_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("atlas") / "seed-7"
    atlas.run_unit(SPEC, root, None, **PLAN)  # type: ignore[arg-type]
    return root


def _rows(root: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (root / "branches.jsonl").read_text().splitlines()]


def test_every_decision_and_replicate_has_a_noop_and_each_action(unit_root: Path) -> None:
    keys = {(r["decision_epoch"], r["replicate"], r["action"]) for r in _rows(unit_root)}
    assert keys == {(1, r, a) for r in (0, 1) for a in ("noop", "norm", "conv_light")}
    assert (unit_root / "complete.json").is_file()


def test_verify_accepts_a_written_unit(unit_root: Path) -> None:
    summary = atlas.verify_unit(unit_root)
    assert summary["branches"] == 6 and summary["noop_twin_matches_trunk"] is True


def test_rows_carry_late_ce_costs_and_the_future_they_ran_on(unit_root: Path) -> None:
    for row in _rows(unit_root):
        assert row["status"] == "completed"
        assert math.isfinite(row["late_ce"])
        assert row["costs"]["optimizer_parameter_steps"] > 0
        assert len(row["future_sha256"]) == 64
    noops = {r["replicate"]: r for r in _rows(unit_root) if r["action"] == "noop"}
    assert noops[0]["future_sha256"] != noops[1]["future_sha256"]


def _tamper(root: Path, tmp_path: Path, keep: Any) -> Path:
    copy = tmp_path / "tampered"
    copy.mkdir()
    for name in ("manifest.json", "trunk.jsonl", "complete.json"):
        (copy / name).write_text((root / name).read_text())
    rows = [r for r in _rows(root) if keep(r)]
    (copy / "branches.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return copy


def test_verify_refuses_a_missing_noop(unit_root: Path, tmp_path: Path) -> None:
    bad = _tamper(unit_root, tmp_path, lambda r: not (r["action"] == "noop" and r["replicate"] == 1))
    with pytest.raises(ValueError, match="no-op"):
        atlas.verify_unit(bad)


def test_verify_refuses_a_duplicate_branch(unit_root: Path, tmp_path: Path) -> None:
    rows = _rows(unit_root)
    bad = _tamper(unit_root, tmp_path, lambda r: True)
    (bad / "branches.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [*rows, rows[0]]))
    with pytest.raises(ValueError, match="duplicate"):
        atlas.verify_unit(bad)


def test_verify_refuses_a_noop_twin_that_does_not_continue_the_trunk(unit_root: Path, tmp_path: Path) -> None:
    bad = _tamper(unit_root, tmp_path, lambda r: True)
    rows = _rows(unit_root)
    for row in rows:
        if row["action"] == "noop" and row["replicate"] == 0:
            row["records"][0]["training_state_sha256"] = "0" * 64
    (bad / "branches.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="trunk"):
        atlas.verify_unit(bad)


def test_effects_are_against_the_same_replicates_noop(unit_root: Path) -> None:
    rows = _rows(unit_root)
    late = {(r["replicate"], r["action"]): r["late_ce"] for r in rows}
    eff = {(e["replicate"], e["action"]): e["effect"] for e in atlas.effects(rows)}
    assert set(eff) == {(r, a) for r in (0, 1) for a in ("norm", "conv_light")}
    for (rep, action), value in eff.items():
        assert value == late[(rep, action)] - late[(rep, "noop")]


def test_a_diverged_branch_is_a_row_scored_at_chance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = atlas.train_epoch  # type: ignore[attr-defined]

    def flaky(host: Any, slot: Any, opt: Any, spec: RunSpec, future: Any, x: Any, y: Any, epoch: int) -> dict[str, Any]:
        if slot.seed is not None and type(slot.seed).__name__ != "NormSeed" and epoch == 2:
            raise ArmDivergedError(epoch=epoch, step=3, reason="injected", stage=slot.stage.value)
        return real(host, slot, opt, spec, future, x, y, epoch)

    monkeypatch.setattr(atlas, "train_epoch", flaky)
    root = tmp_path / "seed-7"
    atlas.run_unit(SPEC, root, None, decision_points=(1,), actions=("norm", "conv_light"), replicates=(0,))
    rows = {r["action"]: r for r in _rows(root)}
    assert rows["conv_light"]["status"] == "diverged" and rows["conv_light"]["late_ce"] is None
    assert rows["conv_light"]["diverged"]["reason"] == "injected"
    atlas.verify_unit(root)
    eff = {e["action"]: e for e in atlas.effects(list(rows.values()))}
    assert eff["conv_light"]["effect"] == pytest.approx(math.log(10) - rows["noop"]["late_ce"])
    assert eff["conv_light"]["diverged"] is True


def test_run_unit_refuses_an_existing_output(unit_root: Path) -> None:
    with pytest.raises(FileExistsError):
        atlas.run_unit(SPEC, unit_root, None, **PLAN)  # type: ignore[arg-type]
