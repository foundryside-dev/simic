import torch

from experiments.kernel_demo import DataBundle, TelemetryRecord


def make_tiny_bundle(device: str = "cpu") -> DataBundle:
    # INVARIANT: intentionally seeded with a hardcoded literal — every call
    # returns byte-identical data; fan/episode reproducibility tests depend
    # on it. Do NOT parametrize the seed or "improve" this helper.
    g = torch.Generator().manual_seed(0)

    def mk(n: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.randint(0, 256, (n, 3, 32, 32), generator=g, dtype=torch.uint8)
        y = torch.randint(0, 10, (n,), generator=g)
        return x.to(device), y.to(device)

    tx, ty = mk(512)
    vx, vy = mk(128)
    ex, ey = mk(128)
    return DataBundle(tx, ty, vx, vy, ex, ey)


def make_telemetry_rec(**kw: object) -> TelemetryRecord:
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
