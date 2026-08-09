import pytest
import torch

from experiments.kernel_demo import (
    REPLAY_REFUSAL_KEYS,
    enable_class1,
    env_block,
    state_hash,
)


def test_class1_flags_set(monkeypatch):
    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    enable_class1()
    assert torch.backends.cudnn.deterministic
    assert not torch.backends.cudnn.benchmark
    assert not torch.backends.cuda.matmul.allow_tf32
    assert torch.are_deterministic_algorithms_enabled()


def test_enable_class1_rejects_stray_cublas_config(monkeypatch):
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    with pytest.raises(RuntimeError, match="CUBLAS_WORKSPACE_CONFIG"):
        enable_class1()


def test_state_hash_canonicalizes_signed_zero():
    m1 = torch.nn.Linear(2, 2)
    m2 = torch.nn.Linear(2, 2)
    m2.load_state_dict(m1.state_dict())
    with torch.no_grad():
        m1.bias[0] = 0.0
        m2.bias[0] = -0.0
    assert state_hash(m1) == state_hash(m2)


def test_env_block_keys_and_refusal_subset():
    e = env_block("cpu", worker_count=4)
    assert set(REPLAY_REFUSAL_KEYS) <= set(e)
    assert "worker_count" in e and "worker_count" not in REPLAY_REFUSAL_KEYS
