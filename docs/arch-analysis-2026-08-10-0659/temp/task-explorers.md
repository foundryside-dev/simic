# Task Specification — codebase-explorer subagents (8 parallel)

## Common Context

- **Workspace:** `docs/arch-analysis-2026-08-10-0659/`
- **Read first:** `01-discovery-findings.md`
- **Target:** `experiments/kernel_demo.py` (4,066 lines), `experiments/kernel_demo_plots.py`
- **Write to:** `temp/catalog-<n>-<slug>.md` (NOT the shared catalog — 8 concurrent
  appenders would clobber. Coordinator concatenates.)

## Output Contract (EXACT — from analyzing-unknown-codebases.md)

```markdown
## [Subsystem Name]

**Location:** `path` (lines X–Y)

**Responsibility:** [One sentence]

**Key Components:**
- `symbol` (line N) - [description]

**Dependencies:**
- Inbound: [subsystems depending on this]
- Outbound: [subsystems this depends on]

**Patterns Observed:**
- [pattern with line citation]

**Concerns:**
- [issue] OR "None observed (verified: error handling, validation, architecture, completeness)"

**Confidence:** [High/Medium/Low] - [files read, lines checked, verification steps]

---
```

No extra sections. No reordering. All 8 sections present.

## Standing Constraints

1. Single-file layout is a LOCKED spec decision (spec rev 6.1). Mark monolith-shaped
   findings "by design", not debt. The 1200-line budget overrun IS a valid finding.
2. Do not use Simic domain codenames (Leyline/Momir/etc.) — the demo is explicitly
   "NOT Simic". Use the author's own section names.
3. Report the certification/traceability machinery explicitly where present.
4. Dependency names must be drawn from the fixed subsystem-name list so the
   coordinator can reconcile bidirectionality.

## Fixed Subsystem Name List

1. Identity, Config & Determinism Spine
2. Data, Episodes & Telemetry
3. Host, Seeds & Slot Lifecycle
4. Counterfactual Fan Executor
5. Records & Store
6. Policy & Learning
7. Certification Battery
8. Run Orchestration & CLI
9. Plotting Sidecar

## Assignments

| # | Subsystem | Ranges |
|---|---|---|
| 1 | Identity, Config & Determinism Spine | 1–251, 917–989, 1534–1546, 2829–2847 |
| 2 | Data, Episodes & Telemetry | 252–554, 990–1141 |
| 3 | Host, Seeds & Slot Lifecycle | 555–916 |
| 4 | Counterfactual Fan Executor | 1142–1419 |
| 5 | Records & Store | 1420–1681 |
| 6 | Policy & Learning | 1682–1978 |
| 7 | Certification Battery | 1979–2306, 2502–3062, 3265–3339 |
| 8 | Run Orchestration & CLI (+ Plotting Sidecar as a 2nd entry) | 2307–2501, 3063–3264, 3340–4066, `kernel_demo_plots.py` |
