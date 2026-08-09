# PDR-0030 — Adopt elspeth's three-tier trust model as doctrine (ADR-0015); enforcement rides the wardline enhancement

Date: 2026-08-10   Status: accepted   Author: Claude (product-owner session 13)
Owner sign-off: RECEIVED 2026-08-10 — owner-directed: "we're also enhancing
wardline so it will provide this trust model coverage for us but for now
just adopt it in the ADR."
Related: ADR-0015 (the binding record), ADR-0006 (silent-default ban this
generalizes), ADR-0002 P2, memory: weft-suite-lineage

## Context

Owner asked for a review of elspeth's linting rules (~/elspeth,
`elspeth-lints` / `trust_tier.tier_model`) with intent to adopt its tiered
model. Review found: the three-tier trust model (owned/crash,
in-flight/explicit-invalid, external/validate-and-quarantine) plus L0–L3
import layering is the productized descendant of the exact silent-default
scar stratum that motivated Simic's reset; the 3,600-line analyzer's
allowlist/ratchet/judge machinery is brownfield retrofit cost Simic
(greenfield) does not need.

## Options

1. Port `elspeth-lints` wholesale now — carries the debt machinery without
   the debt.
2. Doctrine ADR + ruff posture edit + minimal `simic-lints` as a Phase A
   task (the review's original proposal).
3. **Doctrine ADR only; mechanical enforcement via the in-progress
   wardline trust-model enhancement** — chosen by owner.

## The call

ADR-0015 written and committed (5b66b97): tier table with fixed error
postures mapped to Simic's domains, defensive-pattern catalogue
generalized from ADR-0006 to all Tier-1/2 paths, declared Tier-3
boundaries, coarse L0–L3 layer map (leyline → tolaria/urborg → agent
domains → orchestration surfaces), zero-allowlist posture. The deferred
ruff posture (disable RUF019/RUF051/SIM401; add DTZ, T20) is recorded in
the ADR's consequences and lands with Phase A enforcement wiring. The
wardline enhancement inherits named acceptance criteria; meeting them
retires ADR-0006's plain-AST fallback plan. Phase A wiring tracked as
simic-8db0b87ed6.

## Rationale

Phase A binds code to contracts; the provenance doctrine must exist
before the contracts are authored — elspeth's retrofit machinery is the
measured price of adopting it late. Deferring enforcement to wardline
honors the standing Weft preference (don't hand-roll linters) and the
owner's statement that the enhancement is already in progress.

## Reversal trigger

If the wardline enhancement has not shipped trust-model coverage by the
time Phase A reaches enforcement wiring (Phase A target: complete by
2026-09-30, metrics.md), fall back to ADR-0006's plain-AST rule — the
mechanism narrows, the doctrine does not reopen. Tier-assignment
ambiguity on a record class is a design finding for the wave programme,
never grounds to soften a tier's error posture.
