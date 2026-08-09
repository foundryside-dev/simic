"""Kernel Demo — "Simic in 20 minutes".

Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
exactly what Simic proper rejects (generation from live host state). This
demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis.

Spec (LOCKED, rev 6): docs/superpowers/specs/2026-08-09-kernel-demo-design.md
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import torch

SCHEMA_VERSION = 1

_SEMANTIC_SURFACE: list[Callable[..., object]] = []


def semantic[T: Callable[..., object]](obj: T) -> T:
    # Import-time registration, exactly once per process. NEVER call from a
    # factory: call-time registration made config_hash depend on call order
    # (rev 3 defect — a worker mid-episode and a fresh parent disagreed).
    _SEMANTIC_SURFACE.append(obj)
    return obj


_SEMANTIC_CONSTANTS: dict[str, object] = {}


def semantic_const[T](name: str, value: T) -> T:
    # Behavior-changing module constants that are neither Config fields nor
    # source-hashable classes/functions. Registered at definition, import
    # time — same discipline as @semantic, same reason. Register only plain
    # Python values (tuples/dicts/ints/strs) — never tensors or other objects
    # whose repr truncates or reads global state. Register a constant iff
    # changing its value changes computed numbers or gate outcomes;
    # documentation-only lists (FORBIDDEN_RELAXATIONS, MODES) and
    # independently-recorded identities (SCHEMA_VERSION — already in every
    # record) stay out.
    if name in _SEMANTIC_CONSTANTS:
        raise ValueError(f"semantic_const duplicate: {name}")
    _SEMANTIC_CONSTANTS[name] = value
    return value


_NON_SEMANTIC: dict[str, str] = {
    # name -> stated reason a public symbol is NOT on the semantic surface.
    # Default for new public classes/functions is @semantic; entry here is
    # the explicit opt-out (test_every_public_symbol_is_classified enforces).
    "Config": "field values covered by frozen_block_hash; unfrozen fields are licensed operational levers",
    "semantic": "hash mechanism — an edit changes every hash by construction",
    "semantic_const": "hash mechanism",
    "config_hash": "hash mechanism",
    "frozen_block_hash": "hash mechanism",
    "main": "CLI orchestration; every semantic step it dispatches is independently on the surface",
}


@semantic
def derive(seed: int, *labels: str | int) -> int:
    h = hashlib.sha256()
    h.update(seed.to_bytes(8, "big"))
    for label in labels:
        part = str(label).encode()
        h.update(len(part).to_bytes(4, "big"))
        h.update(part)
    return int.from_bytes(h.digest()[:8], "big")


@semantic
def make_generator(seed: int, device: str | torch.device = "cpu") -> torch.Generator:
    g = torch.Generator(device=device)
    # full uint64 is accepted; do NOT mask (seed aliasing). CPU and CUDA
    # generators produce different streams for the same seed — all current
    # call sites use the CPU default; do not assume cross-device comparability.
    g.manual_seed(seed)
    return g


@semantic
@contextlib.contextmanager
def rng_scope(gen: torch.Generator) -> Iterator[None]:
    # nn.Module constructors draw from the GLOBAL stream in reset_parameters();
    # this scope reroutes those draws to the named generator and restores the
    # process-global stream afterwards.
    prior = torch.get_rng_state()
    torch.set_rng_state(gen.get_state())
    try:
        yield
    finally:
        gen.set_state(torch.get_rng_state())
        torch.set_rng_state(prior)


@dataclass(frozen=True)
class Config:
    # frozen: lifecycle + reward
    tau: float = 0.05
    tau_eps: float = 1e-6  # plan-authored (spec names no value)
    lam: float = 1.0
    stage_k: int = 3
    stage_m: int = 3
    stage_f: int = 2
    horizon: int = 40
    window: tuple[int, int] = (5, 15)  # inclusive both ends
    t_star: int = 10
    lr: float = 0.05
    momentum: float = 0.9
    wd: float = 5e-4
    seed_lr: float = 0.05
    diverged_r: float = 0.10
    fans_per_episode: int = 2
    preflight_refans: int = 12  # gate-3 noise-floor refans (plan-authored, owner sign-off at freeze)
    # frozen: statistics
    n_preflight: int = 30
    n_eval: int = 100
    alpha_level: float = 0.05
    permutation_resamples: int = 10_000
    beta_which_frac: float = 0.2
    beta_now_div: float = 2.2
    # frozen: gate thresholds (D9 — plan-chosen, owner sign-off at freeze)
    gate1_min_mild_noop_wins: int = 2
    gate2_probe_min_acc: float = 0.5
    gate3_contrast_mult: float = 2.0
    gate4_dominance_max: float = 0.40
    gate5_rms_band: float = 2.0
    gate6_late_density_mult: float = 0.5
    # frozen: policy training schedule (plan-authored; selects the checkpoint)
    policy_lr: float = 1e-3
    policy_batch_size: int = 64
    policy_steps: int = 4000
    warmup_frac: float = 0.3
    # NOT frozen
    n_collect: int = 300  # spec's "extend collection pre-eval" lever
    d_model: int = 64
    n_layers: int = 2
    tune_frac: float = 0.2
    batch_size: int = 128
    eval_chunk: int = 1000  # plan-authored
    fsync_every: int = 20  # plan-authored durability cadence
    run_seed: int = 20260809


FROZEN_FIELDS: tuple[str, ...] = (
    "tau",
    "tau_eps",
    "lam",
    "stage_k",
    "stage_m",
    "stage_f",
    "horizon",
    "window",
    "t_star",
    "lr",
    "momentum",
    "wd",
    "seed_lr",
    "diverged_r",
    "fans_per_episode",
    "preflight_refans",
    "n_preflight",
    "n_eval",
    "alpha_level",
    "permutation_resamples",
    "beta_which_frac",
    "beta_now_div",
    "gate1_min_mild_noop_wins",
    "gate2_probe_min_acc",
    "gate3_contrast_mult",
    "gate4_dominance_max",
    "gate5_rms_band",
    "gate6_late_density_mult",
    "policy_lr",
    "policy_batch_size",
    "policy_steps",
    "warmup_frac",
)


def frozen_block_hash(cfg: Config) -> str:
    lines = sorted(f"{k}={getattr(cfg, k)!r}" for k in FROZEN_FIELDS)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def config_hash() -> str:
    h = hashlib.sha256()
    for src in sorted(inspect.getsource(obj) for obj in _SEMANTIC_SURFACE):
        h.update(src.encode())
    for name in sorted(_SEMANTIC_CONSTANTS):
        h.update(f"{name}={_SEMANTIC_CONSTANTS[name]!r}".encode())
    return h.hexdigest()


MODES = ("selftest", "preflight", "collect", "train", "eval", "report", "replay")


@semantic
def enable_class1() -> None:  # real body lands in Task 7
    pass


def main(argv: list[str] | None = None) -> None:
    enable_class1()  # MUST be the first statement of every process
    ap = argparse.ArgumentParser(prog="kernel_demo")
    sub = ap.add_subparsers(dest="mode", required=True)
    for m in MODES:
        p = sub.add_parser(m)
        p.add_argument("--store", default="runs/kernel_demo")
        p.add_argument("--device", default="cuda:0")
        p.add_argument("--subset", type=int, default=None)  # dev-speed flag
        if m == "replay":
            p.add_argument("fan_id")
    args = ap.parse_args(argv)
    raise SystemExit(f"not implemented: {args.mode}")


if __name__ == "__main__":
    main()
