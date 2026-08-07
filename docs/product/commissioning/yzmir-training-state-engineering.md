# Commissioning update — yzmir-training-state-engineering

Status: pack **in flight** upstream · Tracker: simic-e84fe6737c · Roster: PDR-0011
Apply this brief to the in-flight skill-creator prompt. This is a **scope
addition**, not just re-citation: the original prompt's framing assumed
universal bitwise replay; v4.1 makes exact replay one regime among three.

## Grounding correction

Ground in the decomposed HLD chapters, entry point
`docs/design/00-INDEX.md`. Cite chapters by path#anchor, invariants as
INV-nn, contracts by name — never bare §-numbers. The old grounding file
(`docs/concept/simic_new.md`) no longer exists.

## Corrected citations

- `Snapshot` contract: `docs/design/05-leyline-contracts.md#911-snapshot`
  (was §9.7).
- Statistical unit (base host trajectory, branches never cross splits):
  `docs/design/07-counterfactual-engine.md#149-statistical-unit` (was
  §14.7); INV-32.
- Determinism and calibration gates:
  `docs/design/programme/evaluation.md#214-tolaria-training-determinism-and-field-calibration-gates`
  (was §21.4).

## Scope addition — the execution-regime model (v4.1)

The pack must adopt Tolaria's three-regime model
(`docs/design/domains/tolaria.md`) instead of assuming universal bitwise
replay:

- **Academy-exact** — causal reference and metrology profile. Device,
  kernels, library/compiler versions, dtype, thread count, random state,
  optimiser state, dataloader state and future minibatches pinned; restore
  + common future ⇒ bitwise-identical traces (INV-05). Deliberately narrow;
  retained permanently as a reference capability, not the factory-floor
  profile.
- **Calibrated-stochastic** — bounded nondeterminism with repeated matched
  branches (replicate groups); outcome distribution, ranking stability and
  decision disagreement measured against Academy-exact.
- **Field** — production kernels, mixed precision, distributed execution;
  evidence carries execution uncertainty and escalates to Academy-exact on
  thin margin, high risk, or expired calibration (INV-43).

Consequences the pack's guidance must carry:

- Non-exact regimes carry **measured uncertainty fields**
  (\(\sigma_{\mathrm{exec}}\)) rather than pretending determinism:
  `docs/design/07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins`.
- Regime advancement is gated **decision-aware**: ranking agreement,
  selection regret, accept/no-op disagreement and tail cases inside
  declared limits (INV-44), not merely numeric closeness.
- \(\sigma_{\mathrm{exec}}\) is load-bearing beyond QA: it sizes the
  admission/retention hysteresis band (ADR-0005, INV-33), so
  training-state capture must preserve whatever the calibration machinery
  needs to keep measuring it.
- Regime state is one axis of the three-axis `ScaffoldState`
  (`docs/design/appendices/scaffold-pattern.md`); withdrawal gates are
  independent and one-axis-at-a-time (INV-39, INV-40, INV-41).

## Interplay note

The Field withdrawal gates are statistics owned by
yzmir-counterfactual-statistics (selection regret, coverage, calibration) —
this pack owns the state capture/restore machinery that makes those
statistics measurable, not the statistics themselves.
