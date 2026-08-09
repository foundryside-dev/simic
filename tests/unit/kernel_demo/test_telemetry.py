import dataclasses

import pytest
import torch

from experiments.kernel_demo import (
    EPOCH_FEATURE_IDX,
    TELEMETRY_DIM,
    Normalizer,
    TelemetryDivergence,
    TelemetryRecord,
    confusion_stats,
    record_to_vector,
)
from tests.unit.kernel_demo.conftest import make_telemetry_rec


def test_record_rejects_nonfinite():
    with pytest.raises(TelemetryDivergence):
        make_telemetry_rec(val_loss=float("inf"))
    with pytest.raises(TelemetryDivergence):
        make_telemetry_rec(grad_norm_var=(0.1, float("nan"), 0.3))


def test_blindness_no_forbidden_fields():
    names = {f.name for f in dataclasses.fields(TelemetryRecord)}
    for forbidden in ("pathology", "wall", "device", "worker", "time"):
        assert not any(forbidden in n for n in names)


def test_vector_epoch_first_and_normalizer_roundtrip():
    v = record_to_vector(make_telemetry_rec())
    assert v.shape == (TELEMETRY_DIM,)
    assert v[EPOCH_FEATURE_IDX] == 3.0
    n = Normalizer()
    n.fit([v, v * 2, v * 3])
    assert torch.allclose(n.apply(v * 2), torch.zeros(TELEMETRY_DIM), atol=1e-6)
    n2 = Normalizer.from_json(n.to_json())
    assert torch.allclose(n2.apply(v), n.apply(v))


def test_confusion_stats_separate_uniform_from_structured():
    labels = torch.arange(10).repeat(50)
    perfect = torch.nn.functional.one_hot(labels, 10).float() * 10
    confused = perfect.clone()
    wrong = torch.nn.functional.one_hot(torch.full((50,), 5), 10).float() * 10
    confused[labels == 3] = wrong
    std_p, _ = confusion_stats(perfect, labels)
    std_c, ent_c = confusion_stats(confused, labels)
    assert std_c > std_p
    assert ent_c < 2.0  # concentrated confusion → low off-diagonal entropy
