"""Offline fit/development data; outer loading is called only by evaluation.

Smoke data exercises learning and persistence, and is not CIFAR evidence.
External CIFAR bytes are checked by torchvision before deserialization.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from experiments.kernel_demo import PATHOLOGIES, SEED_NAMES, Config, derive, make_generator


@dataclass(frozen=True)
class RunSpec:
    data: str = "smoke"
    seed: int = 7
    data_seed: int = 20261004
    train_size: int = 128
    dev_size: int = 64
    outer_size: int = 128
    epochs: int = 10
    graft_epoch: int = 2  # Zero-based, germination BEFORE this epoch trains.
    batch_size: int = 32
    stage_k: int = 1
    stage_m: int = 2
    stage_f: int = 1
    threads: int = 1
    lr: float = 0.05
    tau: float = 0.05
    lam: float = 1.0
    host: str = "mild"
    seed_type: str = "conv_light"
    lifecycle: str = "v1"  # "v2": per-step trust-region curvature clamp (docs/bounded-lifecycle-v2.md)
    trust_safety: float = 0.5

    def validate(self) -> None:
        if self.data not in ("smoke", "cifar"):
            raise ValueError("data must be smoke or cifar")
        if self.host not in PATHOLOGIES:
            raise ValueError(f"host must be one of {PATHOLOGIES}")
        if self.seed_type not in SEED_NAMES:
            raise ValueError(f"seed_type must be one of {SEED_NAMES}")
        if self.lifecycle not in ("v1", "v2"):
            raise ValueError("lifecycle must be v1 or v2")
        if type(self.trust_safety) not in (int, float) or not 0 < self.trust_safety <= 1:
            raise ValueError("trust_safety must be in (0, 1]")
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if field.name not in ("data", "lr", "tau", "lam", "host", "seed_type", "lifecycle", "trust_safety") and type(value) is not int:
                raise ValueError(f"{field.name} must be an integer, not a boolean/coerced value")
        for name in ("train_size", "dev_size", "outer_size", "epochs", "batch_size", "stage_k", "stage_m", "stage_f", "threads"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not 0 <= self.seed < 2**64 or not 0 <= self.data_seed < 2**64:
            raise ValueError("seeds must be uint64")
        if self.graft_epoch < 0 or self.epochs < self.graft_epoch + self.stage_k + self.stage_m + self.stage_f + 1:
            raise ValueError("horizon must include the whole lifecycle and one fully coupled training epoch")
        if self.train_size % self.batch_size:
            raise ValueError("train_size must be divisible by batch_size; no examples are dropped")
        if self.train_size > 45000 or self.dev_size > 5000 or self.outer_size > 10000:
            raise ValueError("split size exceeds fixed 45000/5000/10000 limits")
        for name in ("lr", "tau", "lam"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not torch.isfinite(torch.tensor(value)) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")

    def kernel_config(self) -> Config:
        return Config(
            horizon=self.epochs,
            batch_size=self.batch_size,
            stage_k=self.stage_k,
            stage_m=self.stage_m,
            stage_f=self.stage_f,
            lr=self.lr,
            seed_lr=self.lr,
            tau=self.tau,
            lam=self.lam,
            run_seed=self.data_seed,
            eval_chunk=self.batch_size,
        )


def validated_spec(values: dict[str, Any]) -> RunSpec:
    """Return a specification only after the existing complete range checks."""
    spec = RunSpec(**values)
    spec.validate()
    return spec


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tensor_hash(*tensors: torch.Tensor) -> str:
    h = hashlib.sha256()
    for tensor in tensors:
        t = tensor.detach().cpu().contiguous()
        h.update(str((tuple(t.shape), t.dtype)).encode())
        h.update(t.numpy().tobytes())
    return h.hexdigest()


def validate_data(x: torch.Tensor, y: torch.Tensor, n: int) -> None:
    if x.dtype != torch.uint8 or x.shape != (n, 3, 32, 32) or y.dtype != torch.int64 or y.shape != (n,):
        raise ValueError("invalid image/label shape or dtype")
    if bool(((y < 0) | (y >= 10)).any()):
        raise ValueError("labels must be in [0, 10)")


def validated_data(x: torch.Tensor, y: torch.Tensor, n: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Assure only image/label dtype, shape, count and ten-class label range."""
    validate_data(x, y, n)
    return x, y


def smoke_split(spec: RunSpec, split: str) -> tuple[torch.Tensor, torch.Tensor]:
    """Independent colored-image examples from one learnable, ten-class rule."""
    n = {"fit": spec.train_size, "dev": spec.dev_size, "outer": spec.outer_size}[split]
    g = make_generator(derive(spec.data_seed, "smoke-data-v1", split))
    colors = torch.tensor(
        [
            [225, 35, 35],
            [35, 225, 35],
            [35, 35, 225],
            [225, 225, 35],
            [225, 35, 225],
            [35, 225, 225],
            [125, 35, 35],
            [35, 125, 35],
            [35, 35, 125],
            [125, 125, 125],
        ],
        dtype=torch.int16,
    )
    labels = (torch.arange(n) % 10)[torch.randperm(n, generator=g)]
    jitter = torch.randint(-16, 17, (n, 3, 32, 32), generator=g, dtype=torch.int16)
    images = (colors[labels, :, None, None] + jitter).clamp(0, 255).to(torch.uint8)
    validate_data(images, labels, n)
    return images, labels


def cifar_metadata() -> dict[str, Any]:
    from torchvision.datasets import CIFAR10

    return {"base_folder": CIFAR10.base_folder, "train_files": CIFAR10.train_list, "outer_files": CIFAR10.test_list, "meta": CIFAR10.meta}


def cifar_source_hashes(root: Path) -> dict[str, str]:
    meta = cifar_metadata()
    folder = root / meta["base_folder"]
    return {name: file_hash(folder / name) for name in [*(name for name, _ in meta["train_files"]), meta["meta"]["filename"]]}


def _read_cifar(root: Path, *, train: bool) -> tuple[torch.Tensor, torch.Tensor]:
    from torchvision.datasets import CIFAR10
    from torchvision.datasets.utils import check_integrity

    # The stock train constructor's integrity check opens test_batch too.
    # Narrow ONLY training's check to the selected canonical fit files/meta.
    class FitOnlyCIFAR10(CIFAR10):  # type: ignore[misc]  # torchvision is an untyped third-party base.
        def _check_integrity(self) -> bool:
            folder = Path(self.root) / self.base_folder
            return all(check_integrity(str(folder / name), md5) for name, md5 in self.train_list) and check_integrity(
                str(folder / self.meta["filename"]), self.meta["md5"]
            )

    dataset = FitOnlyCIFAR10(str(root), train=True, download=False) if train else CIFAR10(str(root), train=False, download=False)
    x = torch.from_numpy(dataset.data).permute(0, 3, 1, 2).contiguous()
    y = torch.tensor(dataset.targets, dtype=torch.int64)
    return x, y


def _cifar(root: Path, *, train: bool) -> tuple[torch.Tensor, torch.Tensor]:
    x, y = _read_cifar(root, train=train)
    return validated_data(x, y, 50000 if train else 10000)


def load_fit_dev(spec: RunSpec, root: Path | None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, dict[str, Any]]:
    spec = validated_spec(dataclasses.asdict(spec))
    if spec.data == "smoke":
        tx, ty = smoke_split(spec, "fit")
        dx, dy = smoke_split(spec, "dev")
        provenance: dict[str, Any] = {
            "kind": "synthetic-learnable-engineering-only",
            "source_files": {},
            "outer_identity": {"rule": "smoke-data-v1", "seed": derive(spec.data_seed, "smoke-data-v1", "outer"), "size": spec.outer_size},
        }
    else:
        if root is None:
            raise ValueError("cifar requires a local --data-root")
        x, y = _cifar(root, train=True)
        perm = torch.randperm(50000, generator=make_generator(derive(spec.data_seed, "cifar-fit-dev-v1")))
        fit_idx, dev_idx = perm[: spec.train_size], perm[45000 : 45000 + spec.dev_size]
        tx, ty, dx, dy = x[fit_idx], y[fit_idx], x[dev_idx], y[dev_idx]
        provenance = {
            "kind": "CIFAR10-prospective-split-not-pristine-benchmark",
            "source_files": cifar_source_hashes(root),
            "fit_indices": fit_idx.tolist(),
            "dev_indices": dev_idx.tolist(),
            "outer_identity": {
                "canonical_files_md5": [list(p) for p in cifar_metadata()["outer_files"]],
                "selection": "first-n-official-test",
                "size": spec.outer_size,
            },
        }
    provenance.update(
        {
            "fit_sha256": tensor_hash(tx, ty),
            "fit_calibration_prefix_sha256": tensor_hash(tx[: spec.batch_size]),
            "dev_sha256": tensor_hash(dx, dy),
            "fit_size": len(ty),
            "dev_size": len(dy),
            "data_seed": spec.data_seed,
        }
    )
    return tx, ty, dx, dy, provenance


def load_outer(spec: RunSpec, root: Path | None, provenance: dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    spec = validated_spec(dataclasses.asdict(spec))
    if spec.data == "smoke":
        expected = {"rule": "smoke-data-v1", "seed": derive(spec.data_seed, "smoke-data-v1", "outer"), "size": spec.outer_size}
        if provenance["outer_identity"] != expected:
            raise ValueError("outer generation identity mismatch")
        x, y = smoke_split(spec, "outer")
        files: dict[str, str] = {}
    else:
        if root is None or cifar_source_hashes(root) != provenance["source_files"]:
            raise ValueError("training source files changed or data root missing")
        if provenance["outer_identity"]["canonical_files_md5"] != [list(p) for p in cifar_metadata()["outer_files"]]:
            raise ValueError("canonical outer identity mismatch")
        x, y = _cifar(root, train=False)
        x, y = x[: spec.outer_size], y[: spec.outer_size]
        folder = root / cifar_metadata()["base_folder"]
        files = {name: file_hash(folder / name) for name, _ in cifar_metadata()["outer_files"]}
    validate_data(x, y, spec.outer_size)
    return x, y, {"outer_sha256": tensor_hash(x, y), "outer_source_files": files, "size": len(y)}
