import pytest

from experiments.kernel_demo import (
    SCHEMA_VERSION,
    FanRecord,
    SplitViolation,
    Store,
    _assert_trainable,
    decode_record,
    encode_record,
    load_for_training,
    make_fan_record,
)


def _rec(
    episode_seed: int = 1,
    fan_epoch: int | None = 5,
    split_role: str = "train",
    kind: str = "fan",
    **kw: object,
) -> FanRecord:
    # make_fan_record derives fan_id from the identity tuple — tests never
    # hardcode fan_id. Any field may be overridden via kw without collision.
    fields: dict[str, object] = {
        "kind": kind,
        "episode_seed": episode_seed,
        "seed_namespace": "train",
        "split_role": split_role,
        "pathology_id": "mild",
        "fan_epoch": fan_epoch,
        "refan_k": None,
        "schedule_id": "s",
        "policy_checkpoint_id": None,
        "iteration": None,
        "config_hash": "c",
        "frozen_block_hash": "f",
        "manifest_hash": None,
        "common_future_hash": "h",
        "host_init_hash": "i",
        "env": {"torch": "2.13"},
        "arms": [
            {
                "name": "noop",
                "status": "ok",
                "r_val": 0.4,
                "r_test": None,
                "curve_val": [0.1, float("nan")],
                "curve_test": None,
                "init_seed": 0,
                "g_at_init": None,
                "rms_ratio_blend_entry": None,
                "hash_after_training": None,
                "host_hashes": None,
                "alpha_beta_log": None,
            }
        ],
        "telemetry": [{"epoch": 1, "grad_norm_mean": [1.0, 2.0, 3.0]}],
        "decisions": None,
        "gate_results": None,
    }
    fields.update(kw)
    return make_fan_record(**fields)  # type: ignore[arg-type]


def test_nonfinite_roundtrips_as_null_and_tuples_as_lists():
    line = encode_record(_rec())
    assert "NaN" not in line
    r = decode_record(line)
    curve = r.arms[0]["curve_val"]
    assert isinstance(curve, list) and curve[1] is None
    assert r.telemetry[0]["grad_norm_mean"] == [1.0, 2.0, 3.0]


def test_decode_refuses_wrong_schema_version():
    line = encode_record(_rec()).replace(f'"schema_version": {SCHEMA_VERSION}', '"schema_version": 999')
    with pytest.raises(ValueError, match="schema_version"):
        decode_record(line)


def test_shards_merge_content_ordered_and_unique(tmp_path):
    s = Store(tmp_path)
    s.append(1, _rec(episode_seed=9, fan_epoch=7))
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=9))
    got = [(r.episode_seed, r.fan_epoch) for r in s.merge()]
    assert got == [(2, 5), (2, 9), (9, 7)]


def test_merge_rejects_duplicate_fan_identity(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(1, _rec(episode_seed=2, fan_epoch=5))  # same identity, other shard
    with pytest.raises(ValueError, match="duplicate fan_id"):
        s.merge()


def test_comparator_policy_runs_do_not_collide(tmp_path):
    s = Store(tmp_path)
    a = _rec(kind="policy_run", split_role="eval", policy_checkpoint_id="trained")
    b = _rec(kind="policy_run", split_role="eval", policy_checkpoint_id="random")
    assert a.fan_id != b.fan_id
    s.append(0, a)
    s.append(0, b)
    assert len(s.merge()) == 2  # no false duplicate trip


def test_merge_handles_event_records_beside_fans(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(episode_seed=2, fan_epoch=5))
    s.append(0, _rec(episode_seed=2, fan_epoch=None, kind="extension_event"))
    kinds = [r.kind for r in s.merge()]
    assert kinds.count("fan") == 1
    assert kinds.count("extension_event") == 1


def test_split_wall_fires_on_the_yield_path(tmp_path):
    s = Store(tmp_path)
    s.append(0, _rec(split_role="train"))
    s.append(0, _rec(episode_seed=3, split_role="eval"))
    ok = load_for_training(s)
    assert all(r.split_role in ("train", "tune") for r in ok)
    with pytest.raises(SplitViolation):
        _assert_trainable([_rec(episode_seed=4, split_role="eval")])
    with pytest.raises(SplitViolation):
        _assert_trainable([_rec(episode_seed=5, kind="refan")])
