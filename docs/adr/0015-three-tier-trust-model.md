# ADR-0015 — Adopt the three-tier trust model and layered import doctrine (elspeth lineage)

Date: 2026-08-10 · Status: accepted
Deciders: John (owner-directed adoption, in-session 2026-08-10) ·
Tracker: none yet — enforcement wiring is Phase A work (see Consequences);
wardline enhancement tracked upstream in the Weft suite

## Context

The elspeth project carries a **tiered trust model** — three data-trust
tiers with fixed error postures, plus an L0–L3 layer hierarchy with
import-direction enforcement — mechanically enforced by its `elspeth-lints`
analyzer (`trust_tier.tier_model`: the `.get()`/`getattr(default)`/
`hasattr`/silent-except defensive-pattern catalogue, upward-import
detection, and declared `@trust_boundary` suppression with static-literal
metadata). That model is the productized descendant of the same scar
stratum that motivated Simic's reset: the silent-default /
hallucinated-interface class recorded in
[`0006-ban-silent-defaulting-telemetry-access.md`](0006-ban-silent-defaulting-telemetry-access.md)
and `../design/01-claim.md#26-the-empirical-driver-the-predecessor-record`.

Simic already holds the pieces piecemeal: INV-02 (Leyline dependency
direction), INV-24 (fail-closed typed compatibility), INV-38 (failure
visibility), ADR-0002 runtime policy P2 (unmeasured ≠ zero), and ADR-0006
(code-level ban on defaulting access, scoped to telemetry and Leyline
contract paths). What is missing is the **general doctrine**: a provenance
tier for every datum that fixes its error posture, and a coarse layer map
that generalizes INV-02's direction rule across the fourteen domains.
Phase A binds code to contracts, so the doctrine must exist before the
contracts are authored, not be retrofitted (the elspeth retrofit cost —
allowlists, ratchets, blanket-suppression governance — is the measured
price of adopting it late).

Owner direction (2026-08-10): adopt the model **as doctrine now, by this
ADR only**. Mechanical enforcement will arrive through an in-progress
**wardline enhancement** that extends its trust-boundary gate to cover
this trust model; Simic does not port `elspeth-lints` and does not
hand-roll an analyzer now (consistent with the Weft style-regime
preference already recorded in ADR-0006's enforcement note).

## Decision

Simic adopts the three-tier trust model. Every value a Simic component
touches has exactly one provenance tier, and the tier fixes the error
posture:

| Tier | Provenance | Coercion | On anomaly |
|------|------------|----------|------------|
| **1 — owned canonical data** | Urborg records and ancestry; validated canonical Leyline contract instances (requests, artefacts, QA reports, warrants, decisions); canonical hashes | Never | **Crash immediately** — corruption of our own record is never survivable in place (INV-38) |
| **2 — measured values in flight** | Telemetry readings, QA measurements, branch outcomes, candidate evaluations — type-valid by contract, value-suspect by nature | Never | Explicit invalid marker or typed error result (`None` / `validity_mask=false` per ADR-0006) — never a fabricated default, never a crash that destroys the paired measurement |
| **3 — external input** | Datasets, host checkpoints from outside the system, configs, CLI arguments, anything crossing the process boundary | At the boundary only | Validate at ingress; quarantine failures; nothing unvalidated flows past the boundary |

Posture rules that follow:

1. **Defensive-access idioms are violations on Tier-1 and Tier-2 paths.**
   The elspeth catalogue is adopted as authoring doctrine: `.get(key,
   default)`, `getattr(obj, name, default)`, `hasattr`, `setdefault`,
   `pop(key, default)`, broad or silent `except`, `contextlib.suppress`,
   and `isinstance` guards outside a declared Tier-3 boundary. These
   idioms convert absent reality into plausible values — the exact
   mechanism of the predecessor's silent-zero collapse. ADR-0006 already
   bans them on telemetry/contract paths; this ADR generalizes the ban to
   everything Tier 1 or Tier 2.
2. **Tier-3 boundaries are declared, never implied.** Validation and
   coercion happen at named ingress surfaces whose boundary status is
   statically visible (elspeth's `@trust_boundary` pattern: declared
   metadata, static literals, malformed declaration fails loud and
   suppresses nothing). The concrete declaration mechanism is wardline's
   to define when the enhancement lands; until then, boundary modules are
   named in their package docstring and LLD.
3. **Layered import doctrine.** Import direction is enforced against a
   declared hierarchy, generalizing INV-02:
   - **L0 — `leyline/`**: imports nothing from any other Simic subsystem
     (INV-02 verbatim).
   - **L1 — substrate**: `tolaria/`, `urborg/` — may import L0 only.
   - **L2 — agent domains**: the eleven verb domains — may import L0–L1,
     never each other's internals (cross-domain traffic goes through
     Leyline contracts), and nothing imports `tamiyo/` (INV-35: Tamiyo
     disconnection cannot alter training).
   - **L3 — orchestration and analysis surfaces**: `controls/`,
     `curriculum/`, `experiments/`, `benchmarks/`, `analysis/`,
     `scripts/` — may import downward freely.

   This ADR fixes the doctrine and the coarse map. The precise
   per-domain edge list (including which L2→L2 contract imports are
   legal) is a Phase A deliverable beside the forbidden-import checks
   (`../design/ops/repo-structure.md`), where it can be argued against
   real package boundaries rather than speculated here.
4. **Zero-allowlist posture.** Simic is greenfield: no suppression
   corpus, no ratchets, no grandfathering. If a suppression is ever
   genuinely needed, it is introduced at that moment with owner sign-off,
   an owner, a rationale, and an expiry — elspeth's allowlist discipline
   adopted only at the point of first need, never as standing machinery.

## Displaced constraints

None displaced. This ADR generalizes INV-02 into a coarse layer map and
operationalizes INV-24, INV-35 and INV-38 (with ADR-0002 P2 and ADR-0006)
into a provenance-tier doctrine. No invariant's wording changes; the
constitution's authority boundaries are untouched.

## Options considered

- **Port `elspeth-lints` wholesale** — rejected: the 3,600-line
  `tier_model` rule plus its debt machinery (allowlists, per-file blanket
  ratchets, rationale judge, parity harness) exists to retrofit the
  doctrine onto ~364k lines of brownfield code. Simic has none; carrying
  that machinery in would import the scar tissue without the wound.
- **Hand-roll a minimal `simic-lints` now** — deferred by owner call
  (2026-08-10): wardline is being enhanced to provide trust-model
  coverage, and the Weft suite is the designated home for style-regime
  enforcement. ADR-0006's plain-AST fallback rule remains the contingency
  if the enhancement slips past Phase A's enforcement-wiring milestone.
- **Doctrine by convention and review** — rejected for the same reason
  ADR-0006 rejected it: the defect class is plausible-looking code,
  which is what review is worst at, authored substantially by the same
  class of model that produced the original hallucinations.

## Consequences

- Every record class defined in Phase A Leyline contracts carries a tier
  assignment; the wave:4-leyline contract-shape work should record the
  tier alongside each shape it defines.
- The wardline enhancement inherits concrete acceptance criteria: cover
  the defensive-pattern catalogue on Tier-1/Tier-2 paths, the declared
  Tier-3 boundary mechanism, and layer import direction. Meeting them is
  the gate for retiring ADR-0006's plain-AST fallback plan.
- Ruff posture must not fight the doctrine: when Phase A enforcement
  wiring lands, `pyproject.toml` disables the rules that push code toward
  defaulting access (RUF019, RUF051, SIM401) and adds `DTZ` (Urborg
  timestamps) and `T20` to the select list. Recorded here so the
  deferral is not a loss; deliberately not applied today with no code to
  lint.
- Authoring cost: explicit validity handling instead of one-line
  defaults, and contract-mediated cross-domain imports — accepted;
  as ADR-0006 puts it, the explicitness *is* the record.
- **Reversal triggers:** if the wardline enhancement has not landed by
  Phase A enforcement wiring, fall back to ADR-0006's plain-AST rule
  (mechanism narrows, doctrine unchanged). If tier assignment proves
  genuinely ambiguous for a record class, that is a design finding for
  the wave programme — resolved by clarifying the contract, never by
  softening the tier's error posture. The layer map's L1/L2 split may be
  re-cut by a superseding ADR when Phase A's real package boundaries
  argue for it; L0's isolation (INV-02) and the Tamiyo no-inbound rule
  (INV-35) are constitutional and not reopenable here.
