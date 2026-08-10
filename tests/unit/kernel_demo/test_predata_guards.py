"""Guards added pre-data (2026-08-10), from the architecture analysis.

Each of these closes a path where a wrong number would have looked entirely
ordinary. They are grouped because they share one deadline: the store is
append-only and eval is one-shot, so all three had to land before any
collection ran.
"""

import dataclasses
import json
from pathlib import Path

import pytest
import torch

from experiments.kernel_demo import (
    Config,
    FanRecord,
    Normalizer,
    Policy,
    Store,
    _query_dicts,
    config_hash,
    frozen_block_hash,
    make_fan_record,
    make_generator,
    run_train,
)
from tests.unit.kernel_demo.conftest import make_telemetry_rec


def _tele_dicts(n: int = 6) -> list[dict[str, object]]:
    return [dataclasses.asdict(make_telemetry_rec(epoch=e)) for e in range(n)]


def _flat_normalizer() -> Normalizer:
    return Normalizer.from_json(json.dumps({"medians": [0.0] * 20, "iqrs": [1.0] * 20}))


# --- 1. non-finite logits must be loud, not silent restraint -----------------


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_query_dicts_rejects_infinite_now_head(sign: float) -> None:
    # The pre-fix check ran on sigmoid(p_logit), and sigmoid(±inf) is 1.0/0.0
    # — both finite. So an isolated ±inf on now_head sailed through and read
    # as a CONFIDENT decision on every episode: -inf as restraint with lift
    # exactly 0, +inf as germinate-always. That is the silent-default class.
    pol = Policy(Config(), make_generator(1))
    with torch.no_grad():
        pol.now_head.bias.fill_(sign * float("inf"))
    with pytest.raises(RuntimeError, match="non-finite logits"):
        _query_dicts(pol, _flat_normalizer(), _tele_dicts(), mask=False)


def test_query_dicts_rejects_negative_infinite_seed_head() -> None:
    # -inf on seed_head survives softmax (exp(-inf)=0), so the post-squash
    # check passed this too. Only +inf produced a NaN that the old check
    # happened to catch.
    pol = Policy(Config(), make_generator(1))
    with torch.no_grad():
        pol.seed_head.bias[0] = -float("inf")
    with pytest.raises(RuntimeError, match="non-finite logits"):
        _query_dicts(pol, _flat_normalizer(), _tele_dicts(), mask=False)


def test_query_dicts_passes_a_healthy_policy() -> None:
    p, pi = _query_dicts(Policy(Config(), make_generator(1)), _flat_normalizer(), _tele_dicts(), mask=False)
    assert 0.0 <= p <= 1.0
    assert abs(sum(pi.values()) - 1.0) < 1e-5


def test_query_dicts_restores_training_mode_on_the_error_path() -> None:
    # The raise sits after policy.train(prior), deliberately: a check that
    # leaves the module in eval mode would corrupt any caller that catches.
    pol = Policy(Config(), make_generator(1))
    pol.train(True)
    with torch.no_grad():
        pol.now_head.bias.fill_(float("-inf"))
    with pytest.raises(RuntimeError):
        _query_dicts(pol, _flat_normalizer(), _tele_dicts(), mask=False)
    assert pol.training is True


# --- 3. train must refuse records from a superseded manifest generation ------


def _rec(manifest_hash: str, episode_seed: int, split_role: str) -> FanRecord:
    return make_fan_record(
        kind="fan",
        episode_seed=episode_seed,
        seed_namespace="train",
        split_role=split_role,
        pathology_id="mild",
        fan_epoch=5,
        refan_k=None,
        schedule_id="s",
        policy_checkpoint_id=None,
        iteration=None,
        config_hash=config_hash(),
        frozen_block_hash=frozen_block_hash(Config()),
        manifest_hash=manifest_hash,
        common_future_hash="h",
        host_init_hash="i",
        env={},
        arms=[{"name": n, "status": "ok", "r_val": 0.5, "r_test": None} for n in ("norm", "attn", "conv_light", "conv_heavy", "noop")],
        telemetry=[],
        decisions=None,
        gate_results=None,
    )


def _frozen(tmp_path: Path, manifest_hash: str) -> None:
    (tmp_path / "frozen.json").write_text(
        json.dumps(
            {
                "frozen_block_hash": frozen_block_hash(Config()),
                "config_hash": config_hash(),
                "manifest_hash": manifest_hash,
                "normalizer": {"medians": [0.0] * 20, "iqrs": [1.0] * 20},
                "fan_density": {"best_minus_second": 0.1, "best_minus_noop": 0.2},
                "beta_which": Config().beta_which_frac * 0.1,
                "beta_now": 0.2 / Config().beta_now_div,
            }
        ),
        encoding="utf-8",
    )


def test_train_refuses_records_from_a_superseded_manifest(tmp_path: Path) -> None:
    # freeze_manifest overwrites frozen.json in place while the shard store is
    # append-only, so a re-freeze re-points calibration at generation B while
    # the records still carry generation A. Nothing tied them together before:
    # the existing manifest check compares frozen.json to the LIVE cfg/source,
    # and load_for_training filters on split_role/kind only.
    store = Store(str(tmp_path))
    store.append(0, _rec("gen-A", 1, "train"))
    store.append(0, _rec("gen-A", 2, "tune"))
    _frozen(tmp_path, "gen-B")
    with pytest.raises(RuntimeError, match="superseded manifest generations"):
        run_train(Config(), str(tmp_path))


def test_train_names_the_stale_generation_in_the_refusal(tmp_path: Path) -> None:
    store = Store(str(tmp_path))
    store.append(0, _rec("gen-A", 1, "train"))
    store.append(0, _rec("gen-A", 2, "tune"))
    _frozen(tmp_path, "gen-B")
    with pytest.raises(RuntimeError) as exc:
        run_train(Config(), str(tmp_path))
    # The operator has to know WHICH generation to restore.
    assert "gen-A" in str(exc.value)
    assert "gen-B"[:12] in str(exc.value)
