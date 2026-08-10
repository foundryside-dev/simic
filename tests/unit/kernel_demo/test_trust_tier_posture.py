"""ADR-0015 Tier-1 posture: a missing key in one of our own artefacts is corruption.

The distinction these tests pin (ADR-0002 P2, ADR-0006, ADR-0015 rule 1):

  explicit null  -> a RECORDED absence. Legitimate. "not calibrated against a
                    specific n", "no deterministic-mode cost measured on CPU".
  missing key    -> CORRUPTION of our own record. Loud, always.

`.get(key)` collapses those two into one value, which is how a REFUSAL GUARD
comes to silently pass. Three of the guards below exist to stop a campaign
being run or replayed against a manifest calibrated on different data; before
this posture was enforced, deleting one key from frozen.json disabled them
without a word.
"""

import json
from pathlib import Path

import pytest

from experiments.kernel_demo import (
    Config,
    config_hash,
    frozen_block_hash,
    run_eval,
    run_replay,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

CFG = Config()


def _manifest(**overrides: object) -> dict[str, object]:
    m: dict[str, object] = {
        "frozen_block_hash": frozen_block_hash(CFG),
        "config_hash": config_hash(),
        "manifest_hash": "m",
        "normalizer": {"medians": [0.0] * 20, "iqrs": [1.0] * 20},
        "n_train": None,
        "data_split_id": None,
        "gate8_outcome": None,
    }
    m.update(overrides)
    return m


def _write(tmp_path: Path, manifest: dict[str, object]) -> None:
    (tmp_path / "frozen.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_eval_n_train_guard_is_loud_when_the_key_is_absent(tmp_path):
    # The guard protecting the ONE-SHOT eval. Absent key must not wave it through.
    m = _manifest()
    del m["n_train"]
    _write(tmp_path, m)
    with pytest.raises(KeyError):
        run_eval(CFG, make_tiny_bundle(), "cpu", str(tmp_path))


def test_eval_accepts_an_explicit_null_n_train(tmp_path):
    # Explicit null is a recorded absence and stays legitimate — the guard is
    # skipped, and eval proceeds to fail for its own unrelated reason.
    _write(tmp_path, _manifest())
    with pytest.raises(RuntimeError, match="incomplete collection"):
        run_eval(CFG, make_tiny_bundle(), "cpu", str(tmp_path))


@pytest.mark.parametrize("key", ["gate8_outcome", "data_split_id", "n_train", "manifest_hash"])
def test_replay_refuses_a_manifest_missing_any_tier1_key(tmp_path, key):
    # run_replay treats frozen.json as OPTIONAL — but if it exists, its keys are
    # not. `.get("gate8_outcome") or {}` + `.get("ok", True)` previously meant a
    # corrupt manifest silently replayed single-worker, skipping the very gate-8
    # contingency the recorded finding exists to honour.
    m = _manifest()
    del m[key]
    _write(tmp_path, m)
    with pytest.raises((KeyError, RuntimeError)) as ei:
        run_replay(CFG, "nonexistent-fan-id", str(tmp_path), "cpu")
    # Never a silent pass: either the Tier-1 KeyError, or the store refusing
    # first because the fan_id is not there. Both are loud; neither invents.
    assert not isinstance(ei.value, ValueError)
