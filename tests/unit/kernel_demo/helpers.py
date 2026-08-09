"""Synthetic-fan helpers for learning tests (Task 12)."""

import torch

from experiments.kernel_demo import (
    PATHOLOGIES,
    SEED_NAMES,
    TELEMETRY_DIM,
    FanRecord,
    Normalizer,
    Policy,
    derive,
    fan_to_example,
    make_fan_record,
    train_tune_split,
)


def _tele(epoch: int, w: int) -> dict[str, object]:
    # Planted feature -> winner rule: winner index w lights one of
    # (grad_norm_mean[0..2], per_class_val_acc_std) at 3.0 vs 0.1 baseline.
    gnm = [0.1, 0.1, 0.1]
    std = 0.1
    if w < 3:
        gnm[w] = 3.0
    else:
        std = 3.0
    return {
        "epoch": epoch,
        "train_loss": 1.0,
        "val_loss": 1.0,
        "val_acc": 0.5,
        "train_loss_delta": 0.0,
        "val_loss_delta": 0.0,
        "grad_norm_mean": gnm,
        "grad_norm_var": [0.1, 0.1, 0.1],
        "act_saturation": [0.3, 0.3, 0.3],
        "weight_norm": [1.0, 1.0, 1.0],
        "per_class_val_acc_std": std,
        "confusion_entropy": 2.0,
    }


def synthetic_fans(n: int, seed: int) -> list[FanRecord]:
    # Assigns train/tune roles by the episode rule — the same split the
    # production path records at collection time.
    recs: list[FanRecord] = []
    for i in range(n):
        episode_seed = derive(seed, "synthetic-episode", i)
        w = derive(seed, "synthetic-winner", i) % 4
        winner = SEED_NAMES[w]
        arms: list[dict[str, object]] = [
            {"name": name, "status": "ok", "r_val": 0.7 if name == winner else 0.5, "r_test": None} for name in SEED_NAMES
        ]
        arms.append({"name": "noop", "status": "ok", "r_val": 0.45, "r_test": None})
        recs.append(
            make_fan_record(
                kind="fan",
                episode_seed=episode_seed,
                seed_namespace="train",
                split_role=train_tune_split(episode_seed),
                pathology_id=PATHOLOGIES[w],
                fan_epoch=5,
                refan_k=None,
                schedule_id="synthetic",
                policy_checkpoint_id=None,
                iteration=None,
                config_hash="synthetic",
                frozen_block_hash="synthetic",
                manifest_hash=None,
                common_future_hash="synthetic",
                host_init_hash="synthetic",
                env={},
                arms=arms,
                telemetry=[_tele(e, w) for e in range(6)],
                decisions=None,
                gate_results=None,
            )
        )
    return recs


def synthetic_holdout(records: list[FanRecord]) -> list[FanRecord]:
    # The tune-role episodes — a genuine holdout under the split actually used.
    return [r for r in records if r.split_role == "tune"]


def synthetic_agreement(policy: Policy, records: list[FanRecord]) -> float:
    nz = Normalizer.identity()
    hits = 0
    for rec in records:
        ex = fan_to_example(rec, nz)
        tokens = ex["tokens"]
        assert isinstance(tokens, torch.Tensor)
        with torch.no_grad():
            _, seed_logits = policy(tokens.unsqueeze(0), torch.tensor([tokens.shape[0]]))
        r = ex["r"]
        assert isinstance(r, torch.Tensor)
        hits += int(seed_logits[0].argmax()) == int(r.argmax())
    return hits / len(records)


def synthetic_batch(seed: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    g = torch.Generator().manual_seed(seed)
    b, t = 16, 6
    tokens = torch.randn(b, t, TELEMETRY_DIM, generator=g)
    lengths = torch.full((b,), t, dtype=torch.int64)
    r = 0.4 + 0.3 * torch.rand(b, 4, generator=g)
    r_noop = 0.4 + 0.1 * torch.rand(b, generator=g)
    return tokens, lengths, r, r_noop


def adversarial_batch_with_divergent_arm(seed: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    # One arm at 0.10, others ~0.70 — the N10 regime.
    g = torch.Generator().manual_seed(seed)
    b, t = 16, 6
    tokens = torch.randn(b, t, TELEMETRY_DIM, generator=g)
    lengths = torch.full((b,), t, dtype=torch.int64)
    r = 0.65 + 0.1 * torch.rand(b, 4, generator=g)
    r[:, 2] = 0.10
    r_noop = torch.full((b,), 0.5)
    return tokens, lengths, r, r_noop
