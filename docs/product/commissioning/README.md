# Skill-pack commissioning — queue state and citation discipline

Tracker: simic-e84fe6737c · Roster decision: PDR-0011
(`../decisions/0011-skill-capability-roster.md`)

Five packs were commissioned for simic via skill-creator prompts written
against HLD v2.0. Those prompts were conversation artifacts and are not on
disk; this directory is now the durable home for commissioning state. The
files here are **update briefs**: apply them to the in-flight upstream
prompt/session for the named pack, or use them as the grounding section
when a prompt is re-issued.

## Status (2026-08-08)

| Pack | Status | Prompt action |
|---|---|---|
| yzmir-counterfactual-statistics | **Landed** (v0.1.0) | None — domains unchanged, pack stays valid. Note: more load-bearing under v4.1 — the Field withdrawal gates are selection-regret / coverage / calibration statistics (`../../design/programme/evaluation.md#214-tolaria-training-determinism-and-field-calibration-gates`, `../../design/programme/risks-and-open-decisions.md`). |
| yzmir-structure-synthesis | **Landed** (v0.1.0) | None — domains unchanged. |
| axiom-tensor-compiler-engineering | **Landed** (v0.1.0) | None — domains unchanged. |
| axiom-contract-engineering | **Re-commissioned 2026-08-08** | Owner is commissioning from the consolidated prompt in `axiom-contract-engineering.md` (supersedes the in-flight build and the delta-brief approach for this pack) |
| yzmir-training-state-engineering | **In flight** | Apply `yzmir-training-state-engineering.md` — scope addition, not just re-citation. Applied form ready 2026-08-08: `yzmir-training-state-engineering-updated-prompt.md` (original prompt recovered from the 2026-08-07 drafting session + brief applied, all citations verified against `docs/design/`, plus further drift fixed: TrialPlan→`TestPlan`, Phase C→Phases B/D, v2.0 invariant numbers remapped). Relay that file upstream, or re-issue from it if the in-flight build is superseded |

Next commission after the in-flight pair lands (PDR-0011): Nissa telemetry /
representation diagnostics — the one agent domain with zero pack coverage.

## Citation discipline (applies to every prompt)

The v2.0 monolith is superseded and the v4.1 monolith is an archived
pointer stub. Prompts must ground in the decomposed chapters:

- Entry point: `docs/design/00-INDEX.md` (reading paths + §→file concordance).
- Cite chapters by **path#anchor**, invariants as **INV-nn**, contracts by
  **name** — never bare §-numbers, which is the defect class that motivated
  this task.

## §-shift map (v2.0 refs the old prompts carried)

| Old citation | Current home |
|---|---|
| Snapshot §9.7 | `Snapshot` contract — `docs/design/05-leyline-contracts.md#911-snapshot` |
| Contract tests §21.1 | `docs/design/programme/evaluation.md#212-leyline-contract-tests` |
| Urabrask tests §21.4 | `docs/design/programme/evaluation.md#217-urabrask-tests` |
| Statistical unit §14.7 | `docs/design/07-counterfactual-engine.md#149-statistical-unit` |
| Tolaria spec §13.2 | `docs/design/domains/tolaria.md` (execution regimes) |
| Execution-uncertainty margins §14.4.1 | `docs/design/07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins` |
| Grounding file docs/concept/simic_new.md | `docs/design/` chapters via `00-INDEX.md` |
