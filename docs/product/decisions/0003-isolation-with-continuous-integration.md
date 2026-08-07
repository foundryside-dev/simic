# PDR-0003 — Build strategy: isolated component builds, continuous integration into a walking skeleton

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — strategy discussed and confirmed in-session 2026-08-08.
Related: PDR-0002 (doc tiering), HLD §24 (stub ladder), §25 (Phases A–K),
§20–21 (cross-component test tree)

## Context
The owner proposed building each of the fourteen subsystems in isolation and
then integrating. Simic's hardest properties are *system* properties that no
component exhibits alone: Academy exact replay (INV-5) spans the whole execution
stack; canonical semantic identity (INV-20) is a five-party agreement across
Momir→Elesh→Tezzeret→Urabrask/Augustin→Kasmina; blinding by construction
(INV-37) and the warrant chain are inherently multi-party.

## Options considered
1. **Big-bang: build all fourteen in isolation, integrate at the end** — pro:
   maximum parallelism on paper; con: every emergent-invariant violation is
   discovered at once, at maximum sunk cost — the definition of a compromised
   instrument. Rejected.
2. **Strictly serial phase-by-phase, no parallel work** — pro: always
   integrated; con: forfeits the parallelism that contract-first development
   legitimately buys. Rejected.
3. **Isolation for building, continuous integration for landing (chosen).**

## The call
- **Contract-first isolation:** after Phase A, components are developed and
  unit-tested against Leyline contracts and fixtures — never against each
  other's internals; forbidden-import lint enforces boundaries mechanically.
- **Walking skeleton early:** Phases B and D produce a running, deterministic
  train/snapshot/branch/replay loop (host only). Counterfactual branching is the
  single riskiest mechanism, so it is integrated earliest, not last.
- **Land by stub replacement:** every subsystem enters the running system by
  replacing its §24 stub (fixed Tamiyo envelope, heuristic Narset, rule-driven
  Elesh/Urabrask, fixed blind Augustin, fixed Kasmina schedules) — nothing waits
  on a shelf.
- **Done means integrated:** a component is complete only when the
  cross-component suites (`authority/`, `blinding/`, `determinism/`,
  `integration/`, `end_to_end/`) pass with it swapped in.
- **Parallelism:** permitted wherever contracts decouple workstreams; merges
  happen in dependency order as components complete, never as one integration
  event.

## Rationale
§24/§25 already encode the stub ladder and phase ordering — this decision makes
the integration discipline explicit rather than inventing structure. Integration
risk dominates in a system whose guarantees are compositional; the owner's
experiment-value principle (never build a compromised instrument) applies to the
codebase itself.

## Reversal trigger
If keeping the skeleton green becomes the bottleneck (e.g. the Academy
determinism gate blocks all merges for more than a week), revisit the
integration cadence explicitly — never silently bypass the gates.
