"""Experiments — L3 orchestration and analysis surface (ADR-0015).

Layer: **L3**. May import downward freely; nothing in `src/simic/` may import
from here.

## Declared trust boundaries (ADR-0015 rule 2, interim docstring form)

ADR-0015 requires Tier-3 boundaries to be **declared, never implied**, and
fixes the interim mechanism until wardline's trust-model enhancement lands:
boundary surfaces are named in the package docstring and the LLD. This is that
declaration for the `experiments` package. It is a statement of where
validation is owed — the analyzer does not yet read it (see "Why this is not
executable yet" below).

### Tier 3 — external input. Validate at ingress; nothing unvalidated flows past.

| Surface | Ingress | Posture today |
|---|---|---|
| `kernel_demo.load_data` | CIFAR-10 from disk / torchvision download (`runs/data`) | Shape and split sizes checked by `--selftest` `partition_check`; content trusted to torchvision |
| `kernel_demo.main` (argparse) | CLI arguments — `--store`, `--device`, `--subset`, `--workers`, `--limit`, `--extend`, `fan_id` | Types enforced by argparse; `--device` is passed to `torch.device` unvalidated; `--subset`/`--workers` are unbounded |
| `kernel_demo.enable_class1` | `CUBLAS_WORKSPACE_CONFIG` environment variable | **The model boundary in this package** — validates and raises on any unexpected value rather than tolerating it |
| `kernel_demo._git_rev`, `_worktree_clean`, `gate8_pressure`, `run_selftest` | `subprocess` output (git, sibling interpreters) | `check=True`; stdout parsed positionally |
| `kernel_demo._load_policy` | `torch.load` of a policy checkpoint | `weights_only=True` |
| `kernel_demo.run_arm` (rev 6.2) | `torch.save`/`torch.load` of the Δ-weight sidecar | Write side only in-repo; **any future reader of this sidecar is a new Tier-3 boundary and must validate at ingress** |
| `kernel_demo_plots` | `eval_results.json`, record store | `require_number` / `require_dict` — direct indexing, loud on absence, refuses non-finite. The reference implementation of a Tier-3 ingress check in this repo |

### Tier 1 — owned canonical data. Never coerced; crash on corruption.

`kernel_demo.Store.merge` / `decode_record` (the JSONL record store),
`frozen.json`, `certified.json`, `eval_results.json` as read back by the demo's
own modes. These are our own records: a `schema_version` mismatch, a duplicate
`fan_id`, or a torn interior line **raises** rather than degrading, which is the
correct Tier-1 posture (INV-38).

**Known doctrine gap, not fixed here:** several manifest reads use
`.get(key)` on this Tier-1 path — `manifest.get("n_train")`,
`manifest.get("data_split_id")`, `manifest.get("gate8_outcome") or {}`,
`certified.get("det_mode_cost")`. Absence silently satisfies the guard rather
than failing it, and three of those are *refusal guards* (collect/eval/replay
refusing a manifest calibrated against different data). ADR-0015 rule 1 bans
this idiom on Tier-1 paths and ADR-0006 predates it; Simic declared a
zero-allowlist posture, so this is a violation to be decided on, not a waiver
to be written. Recorded for the owner rather than silently changed, because the
file is a locked, pre-registered experiment.

### Tier 2 — measured values in flight.

`TelemetryRecord` and everything derived from it. Posture is already correct
and load-bearing: construction asserts every field finite and raises
`TelemetryDivergence`; `_sanitize_json` writes non-finite as `null` plus a
status, never a bare `NaN` and never a fabricated `0.0`; `_as_float` is loud on
`None`. This is ADR-0006's ban implemented, and it is the scar that motivated
the reset.

## Why this is not executable yet

Wardline's boundary vocabulary is `@external_boundary` / `@trust_boundary` /
`@trusted`, imported from `wardline.decorators` — a runtime import. Two things
block adopting it here today:

1. `wardline` is not a dependency of this project (not importable in `.venv`).
2. `experiments/kernel_demo.py` is pinned by its spec to **torch + torchvision
   only**; adding a third runtime import would breach that pin.

So `wardline scan` reports `0 trust boundaries recognized` and its taint gate is
**inert repo-wide** — it passes while checking nothing. This docstring is the
declaration ADR-0015 asks for in the meantime; making it mechanical is Phase-A
work on `simic-8db0b87ed6`, and needs a decision on how wardline's decorators
enter a project whose experiment file is dependency-pinned.
"""
