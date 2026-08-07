# Simic — Counterfactual Generative Morphogenesis

Simic is the third incarnation of ESPER (`~/esper`) and ESPER LITE
(`~/esper-lite`), redesigned around discoveries from those systems. It is a
lifecycle-driven neural training system in which new computational structure is
**generated from the live state of a host network** — not selected from a fixed
menu of human-authored blueprints — then conformed, compiled, QA-tested in
matched counterfactual branches, adjudicated against doing nothing, embodied
reversibly under warrant, and eventually retired.

## Canonical design authority

The HLD (v4.1, Namespec 1.0 — locked) is decomposed into standalone chapters
under **`docs/design/`** (ADR-0001). Entry point and §→file concordance:
**`docs/design/00-INDEX.md`**. Load `docs/design/02-constitution.md` (naming
constitution + the 44 INV-nn invariants) in every working session, plus the
chapters your task names — the index's reading paths say which. Cite
invariants as INV-nn, contracts by name, chapters by path#anchor; never bare
§-numbers in new text. The v4.1 monolith is archived, content-identical, at
`docs/concept/archive/simic-v4.1-monolith.md`;
`docs/concept/archive/simic-v2.0.md` is **superseded** — historical context
only; never ground design decisions on it. Everything below is a digest, not
a replacement.

ADRs live in `docs/adr/`. The product workspace (vision, roadmap, metrics,
current-state, PDRs under `decisions/`) is `docs/product/`, maintained via
the axiom-product-management ownership loop — treat it as owner-authored
state, not free-edit documentation.

## The fourteen domains

Three infrastructure domains carry prepositions (Leyline = contracts and the
deterministic request resolver; Tolaria = the single training/execution
substrate for mainline and branches; Sarpadia = append-only history, ancestry
and retrieval). Eleven agent domains carry verbs — the canonical sentence
(`docs/design/02-constitution.md`):

> Nissa observes and reports. Tamiyo plans. Narset commissions and acts.
> Momir designs. Elesh conforms. Tezzeret compiles. Urabrask tests the
> compiled result in Tolaria. Augustin judges the resulting evidence under
> Leyline. Kasmina embodies the admitted growth. Emrakul destroys what no
> longer earns continued tenancy. Sarpadia retains every precedent. Oona
> reveals the account.

The codenames are behavioural mandates and act as an architecture linter: a
subsystem acting contrary to its verb is exercising authority it must not have
(`02-constitution.md`, `04-architecture.md`, `domains/README.md`, and the
smell catalogue in `03-principles.md`). The core loop: Tolaria trains
the host → Nissa observes the ablated host and publishes the **same**
`TelemetryEnvelope` directly to Narset and Momir → Tamiyo grants a
`StrategicEnvelope` → Narset issues a narrow `GrowthIntent` (assignment brief;
diagnosis/topology/ancestry hints are schema-invalid) → Leyline's deterministic
resolver produces the canonical `GrowthRequest` → Momir designs raw candidates
(optionally conditioned on Sarpadia bootstrap ancestry) → Elesh canonicalises
and verifies → Tezzeret compiles without changing semantics → Urabrask runs QA
in Tolaria's matched common-future branches and certifies evidence → Augustin
adjudicates provider-blind against no-op and issues warrants → Kasmina
germinates/blends/commits under an admission warrant → Emrakul later
sedates/decays/lyses under maintenance warrants → Sarpadia records everything →
Oona reveals it. The newsroom rule (`appendices/newsroom.md`): **Nissa sends
the photograph; Narset sends only the assignment brief.**

## Non-negotiable invariants (`02-constitution.md` has all 44; these are the spine)

- **Academy exact replay:** identical snapshot + identical future data ⇒
  bitwise-identical traces; non-exact profiles carry measured uncertainty.
- **Mandatory no-op:** every admission and continued-tenancy case includes a
  measured no-intervention alternative with policy utility exactly zero.
- **QA/judgement split:** Urabrask certifies evidence but never issues
  verdicts or warrants; Augustin judges but never executes or alters tests.
- **Dual provider blindness:** neither Urabrask nor Augustin sees candidate
  source; blinding is by construction (fields absent, not ignored).
- **Warrants:** Kasmina never raises influence without a valid Augustin
  admission warrant; ordinary decay/lysis requires a maintenance warrant.
- **Assignment-brief boundary:** `GrowthIntent` carries scope and operational
  constraints only; equivalent intents resolve to one canonical request, and
  Momir never sees Narset hidden state.
- **Semantic identity:** artefact, QA report, decision and embodiment all
  reference the same canonical hash; Tezzeret preserves semantics.
- **Authority separation:** Narset pre-commit only, Emrakul post-commit only,
  Tamiyo never issues local transitions, Nissa never emits `should_grow`.
- **Complete history:** Sarpadia is append-only and retains failures, rejected
  pools, no-op wins and abstentions — never winners-only.
- **Oona isolation:** disconnecting observability cannot change training.
- **Leyline dependency direction:** contracts import nothing from subsystems.
- **Grouped statistics:** branches of one base trajectory never cross splits.
- **Scaffold discipline:** every run declares its three-axis `ScaffoldState`;
  withdrawal gates are independent; confirmatory transitions move one axis at
  a time.

## Target layout and sequencing

Code goes under `src/simic/<subsystem>/` — one package per domain (`leyline/`,
`tolaria/`, `sarpadia/`, `tamiyo/`, `narset/`, `nissa/`, `momir/`, `elesh/`,
`tezzeret/`, `urabrask/`, `augustin/`, `kasmina/`, `emrakul/`, `oona/`) plus
`controls/`, `curriculum/`, `benchmarks/`, `experiments/`, `analysis/`,
`scripts/`, with
`tests/{namespec,contracts,observation_routing,request_resolution,bootstrap_withdrawal,scaffold_withdrawal,unit,integration,training,determinism,counterfactual,authority,blinding,end_to_end}/`
— see `ops/repo-structure.md`. Implementation follows Phases A–K in
`programme/phases.md`: **Phase A (Namespec, Leyline contracts and dependency
boundaries) comes first**; MVP scope is in `programme/phases.md`; the first
repository milestones are in `ops/repo-structure.md`. Python is the working
language.

## Current state (2026-08-08)

Phase A bootstrap. The Python scaffold is in place (pyproject with uv,
`src/simic/`, `tests/`, pre-commit) but carries no functional code yet —
substantive content is the HLD and the Weft tooling below. First engineering
work is Phase A (Namespec, Leyline contracts, dependency boundaries).
Licensed Apache-2.0. The project name was locked as Simic on 2026-08-08
(`programme/risks-and-open-decisions.md`); subsystem boundaries are locked
too. Design-review findings and
open design decisions are tracked in filigree under the `hld-review` label.

<!-- filigree:instructions:v3.1.0:c1c023c3 -->
<!-- filigree:last-writer:filigree install -->
## Filigree Issue Tracker

`filigree` tracks this project's work. Use it to find, claim, update and close
issues: `filigree session-context` at session start, then
`filigree start-next-work --assignee <name>`.

Full reference: the **filigree-workflow** skill (patterns, priorities,
observations, error codes), `filigree --help`, and the `mcp__filigree__*` tool
schemas. Prefer the MCP tools when available; fall back to the CLI.

Two rules `--help` will not tell you:

1. Claim atomically: `work_start` / `work_start_next` (MCP) or `start-work` /
   `start-next-work` (CLI). Never chain a claim with a separate status update;
   that two-step form races other agents.
2. On `SCHEMA_MISMATCH` the installed filigree is older than the project
   database. Surface it to the user; do not retry.
<!-- /filigree:instructions -->

<!-- loomweave:instructions:v1.5.0:39edbf6d -->
<!-- loomweave:last-writer:loomweave install -->
## Loomweave (code structure + SEI identity)

Loomweave pre-extracts this repo into a queryable map — entities, their
call/reference/import/relation edges, and subsystems — each carrying a Stable
Entity Identity (SEI). Ask its `mcp__loomweave__*` tools, not grep, for "what
calls X", "what subclasses X", "where is X defined", "find the thing that
does Y".

- Never hand-construct an entity id: take it from `entity_find` / `entity_at` /
  `entity_resolve`, and bind cross-tool records on the `sei`, not the `id`.
- If `project_status_get` reports stale, re-index before answering.

Full reference: `loomweave-workflow` skill, `loomweave --help`, MCP schemas.
<!-- /loomweave:instructions -->

<!-- wardline:instructions:v1:bcd19330 -->
<!-- wardline:last-writer:wardline install -->
This project uses **wardline** as its trust-boundary gate. Before handing back code that touches external input, run `wardline scan . --fail-on ERROR` (exit 0 = clean, 1 = gate tripped, 2 = wardline error) and fix findings at the boundary, not the sink. The full scan -> explain -> fix -> rescan loop and the baseline-vs-waiver discipline live in the `wardline-gate` skill.
<!-- /wardline:instructions -->

## Plainweave (definitional lifecycle — ADR-0002)

Named definitional units (Leyline contract shapes, invariants, telemetry
standards) live under plainweave's sign/lock regime
(`docs/adr/0002-information-management-regime.md`). Before implementing
against or changing a named definition, check its baseline status via
`mcp__plainweave__*` tools (e.g. `plainweave_baseline_get`,
`plainweave_requirement_search`); a locked definition changes only through a
recorded event, never a silent edit. The store is initialized but seeding is
pending (simic-357c92664c) — absence of a baseline means "not yet seeded",
not "unmanaged".

<!-- warpline:instructions:v1.3.0 -->
## Warpline (temporal change-impact)

`warpline` answers "if I touch X, what breaks, and what must I re-verify?".
Prefer the MCP tools (`mcp__warpline__*`); fall back to the `warpline` CLI.

Call `warpline_change_list` (shim: `changed`) for a rev range first, then follow
its `next_actions` into `reverify` / `blast_radius`. A `completeness` of
`NO_SNAPSHOT` means warpline cannot see, NOT that nothing is affected.

Enrich-only, local-only, advisory: warpline never gates. The `warpline-workflow`
skill carries the full tool set, the closed vocabularies, and the loop.
<!-- /warpline:instructions -->

<!-- legis:instructions:v1.5.0:37065fbc -->
## Legis (git/CI + governance)

Legis is the git/CI and governance layer of the Weft suite: graded policy
enforcement over branch/commit/PR/check context, recorded in an append-only
audit trail keyed to stable code identity (SEI), so it survives rename/move.

Reach for it when a policy fires at the CI/git boundary, when a change needs a
recordable override or human sign-off, or when you need git/CI context.

- Prefer the `mcp__legis__*` MCP tools; fall back to the `legis` CLI.
- Clear a fired policy through `override_submit` (MCP-only), which grades it
  (self-clear / judged / escalated) and records it — routing around it leaves
  no trail.

Full reference: the `legis-workflow` skill, `legis --help`, MCP schemas.
<!-- /legis:instructions -->
