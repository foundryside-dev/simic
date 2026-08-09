import dataclasses
import json
import time
from pathlib import Path

import pytest

from experiments.kernel_demo import (
    Config,
    DataBundle,
    Store,
    TwinDivergence,
    config_hash,
    derive,
    frozen_block_hash,
    run_collect,
    run_collection_episode,
    train_tune_split,
)
from tests.unit.kernel_demo.conftest import make_tiny_bundle

TINY = dataclasses.replace(Config(), horizon=6, stage_k=1, stage_m=1, stage_f=1, batch_size=64, window=(1, 3), n_collect=4, fsync_every=1)


def tiny_loader(cfg: Config, device: str, subset: int | None) -> DataBundle:
    # Module-level so multiprocessing spawn can pickle it by reference.
    return make_tiny_bundle(device)


def bomb_runner(
    cfg: Config,
    data: DataBundle,
    device: str,
    episode_seed: int,
    namespace: str,
    store: Store,
    worker_id: int,
    read_test: bool,
    *,
    manifest_hash: str | None = None,
    worker_count: int = 1,
) -> None:
    if episode_seed == derive(cfg.run_seed, "train", 0):
        raise TwinDivergence(3)
    time.sleep(0.5)  # let the sibling's halt land between episodes deterministically
    run_collection_episode(
        cfg, data, device, episode_seed, namespace, store, worker_id, read_test, manifest_hash=manifest_hash, worker_count=worker_count
    )


def _write_frozen(tmp_path: Path, cfg: Config) -> None:
    (tmp_path / "frozen.json").write_text(
        json.dumps(
            {
                "frozen_block_hash": frozen_block_hash(cfg),
                "config_hash": config_hash(),
                "gate_results": {"all": {"ok": True}},
                "manifest_hash": "m",
            }
        )
    )


def test_collect_idempotent_and_roles(tmp_path):
    _write_frozen(tmp_path, TINY)
    out = run_collect(TINY, str(tmp_path), ["cpu"], 2, data_loader=tiny_loader)
    assert out["ok"]
    fans = [r for r in Store(tmp_path).merge() if r.kind == "fan" and r.seed_namespace == "train"]
    assert len({r.episode_seed for r in fans}) == 4
    assert len(fans) == 8  # two fans per episode
    for r in fans:
        assert r.split_role == train_tune_split(r.episode_seed)  # roles from the tune rule
    out2 = run_collect(TINY, str(tmp_path), ["cpu"], 2, data_loader=tiny_loader)
    assert out2["collected"] == 0  # re-invocation collects zero new episodes
    assert len([r for r in Store(tmp_path).merge() if r.kind == "fan"]) == 8


def test_collect_refuses_without_manifest(tmp_path):
    with pytest.raises(RuntimeError, match=r"frozen\.json"):
        run_collect(TINY, str(tmp_path), ["cpu"], 1, data_loader=tiny_loader)


def test_collect_refuses_on_config_mismatch(tmp_path):
    _write_frozen(tmp_path, dataclasses.replace(TINY, tau=0.99))
    with pytest.raises(RuntimeError, match="frozen_block_hash"):
        run_collect(TINY, str(tmp_path), ["cpu"], 1, data_loader=tiny_loader)


def test_divergence_halts_and_reports(tmp_path):
    _write_frozen(tmp_path, TINY)
    out = run_collect(TINY, str(tmp_path), ["cpu"], 2, data_loader=tiny_loader, episode_runner=bomb_runner)
    assert out["halted"] and not out["ok"]
    reports = list(tmp_path.glob("divergence_*.json"))
    assert reports
    rep = json.loads(reports[0].read_text())
    for key in (
        "episode_seed",
        "arm_name",
        "first_bad_epoch",
        "config_hash",
        "frozen_block_hash",
        "manifest_hash",
        "env_block",
        "host_init_hash",
    ):
        assert key in rep, key
    fans = [r for r in Store(tmp_path).merge() if r.kind == "fan"]
    assert len({r.episode_seed for r in fans}) < 4  # sibling stopped early, pre-halt shards remain valid
