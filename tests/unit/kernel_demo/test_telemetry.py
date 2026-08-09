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


def _rec(**kw: object) -> TelemetryRecord:
    base: dict[str, object] = {
        "epoch": 3,
        "train_loss": 1.2,
        "val_loss": 1.3,
        "val_acc": 0.41,
        "train_loss_delta": -0.1,
        "val_loss_delta": -0.05,
        "grad_norm_mean": (1.0, 2.0, 3.0),
        "grad_norm_var": (0.1, 0.2, 0.3),
        "act_saturation": (0.5, 0.4, 0.3),
        "weight_norm": (10.0, 11.0, 12.0),
        "per_class_val_acc_std": 0.05,
        "confusion_entropy": 2.1,
    }
    base.update(kw)
    return TelemetryRecord(
        epoch=int(base["epoch"]),  # type: ignore
        train_loss=float(base["train_loss"]),  # type: ignore
        val_loss=float(base["val_loss"]),  # type: ignore
        val_acc=float(base["val_acc"]),  # type: ignore
        train_loss_delta=float(base["train_loss_delta"]),  # type: ignore
        val_loss_delta=float(base["val_loss_delta"]),  # type: ignore
        grad_norm_mean=tuple(base["grad_norm_mean"]),  # type: ignore
        grad_norm_var=tuple(base["grad_norm_var"]),  # type: ignore
        act_saturation=tuple(base["act_saturation"]),  # type: ignore
        weight_norm=tuple(base["weight_norm"]),  # type: ignore
        per_class_val_acc_std=float(base["per_class_val_acc_std"]),  # type: ignore
        confusion_entropy=float(base["confusion_entropy"]),  # type: ignore
    )


def test_record_rejects_nonfinite():
    with pytest.raises(TelemetryDivergence):
        _rec(val_loss=float("inf"))
    with pytest.raises(TelemetryDivergence):
        _rec(grad_norm_var=(0.1, float("nan"), 0.3))


def test_blindness_no_forbidden_fields():
    names = {f.name for f in dataclasses.fields(TelemetryRecord)}
    for forbidden in ("pathology", "wall", "device", "worker", "time"):
        assert not any(forbidden in n for n in names)


def test_vector_epoch_first_and_normalizer_roundtrip():
    v = record_to_vector(_rec())
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
