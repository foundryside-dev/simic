# ADR-0013 — Scope Academy exactness to a declared execution-stack identity (INV-05 amended)

Date: 2026-08-09 · Status: accepted
Deciders: John (owner concern raised session 11: bitwise precision is
"either inspired or going to footgun us in 6 months"; scoping confirmed) ·
Tracker: simic-d1bdc7173f

## Context

Academy exactness is the design's metrology lab: branch difference equals
intervention effect with no ε, and any divergence fails loudly — the
direct answer to the predecessor's silent-instrument failures. But bitwise
identity does not survive changes of GPU model, driver, CUDA/library
version or kernel-selection profile. As written, INV-05 is implicitly
per-stack; left implicit, the first driver upgrade reads as a
constitutional violation instead of a re-baselining event, the repo
ossifies around pinned versions, and the determinism tax (deterministic
kernels cost multiples on some ops; some ops have no deterministic GPU
path) gets paid by default instead of by decision.

## Decision

1. **Stack identity.** The Academy-exact determinism contract binds to a
   **declared execution-stack identity** — hardware model, driver and
   runtime versions, framework version, kernel-selection profile — pinned
   and recorded with the profile. Bitwise identity is defined *within* a
   stack identity; it is never a portability claim across stacks.
2. **Pin and re-baseline.** The lab is pinned; the factory floats. Moving
   the pin is a named **re-baselining event**: replay fixtures re-run
   under the candidate stack, acceptance recorded, both stack identities
   and the transition retained in Urborg provenance (INV-36 — a new
   record, never a rewrite). The pin record's contract shape lands with
   the Phase A Leyline contracts alongside the execution manifest.
3. **Measure the tax early.** Phase B measures the exactness tax
   (deterministic-kernel overhead) on the actual MVP hosts and feeds the
   §22.11 cost model (simic-642c2c1823); the Academy operating point is
   chosen from that data, not defaulted. The device class is not the
   profile: the lab may be hosted on CPU — where exactness is nearly
   free for MVP-scale hosts — reserving GPUs for calibrated-stochastic
   and Field regimes.
4. **Topology-change discipline.** Inserting a growth changes kernel
   shapes and fusion choices — same semantics, different kernels. The
   paired-branch rules for kernel selection and RNG streams across
   topology change are named as a Tolaria LLD deliverable (the
   morphogenetic-replay hard case), not left to be discovered in code.

## Displaced constraints

INV-05 amended.

- Old: "**Academy exact replay:** identical snapshot plus identical
  future data produces bitwise-identical traces under Tolaria's
  Academy-exact determinism contract; non-exact profiles carry measured
  uncertainty rather than pretending to satisfy this invariant."
- New: "**Academy exact replay:** identical snapshot plus identical
  future data produces bitwise-identical traces under Tolaria's
  Academy-exact determinism contract, within the profile's declared,
  pinned execution-stack identity; moving the pin is a recorded
  re-baselining event, never a silent equivalence claim; non-exact
  profiles carry measured uncertainty rather than pretending to satisfy
  this invariant. (ADR-0013)"

No other invariant changes. INV-43/44 (calibration envelope and
decision-aware gates) are load-bearing context, unchanged.

## Options considered

- **Leave INV-05 unscoped (status quo).** Rejected: the invariant would
  be false as read the first time hardware or drivers change, and a
  constitution whose flagship invariant is quietly false teaches readers
  to discount the rest.
- **Weaken to statistical equivalence.** Rejected: bitwise-with-scope is
  strictly stronger than approximate-everywhere; the loud-failure
  property is the point (esper-lite scar).
- **Pin the whole system to one stack forever.** Rejected: that is the
  ossification footgun — the factory must float while only the lab pins.

## Consequences

Constitution INV-05 carries the scope; Tolaria's chapter states the pin,
the re-baseline event, the CPU-hosting option, and the topology-change
LLD seam; Phase B gains the tax-measurement milestone. Reversal trigger:
if re-baselining events become frequent enough to dominate lab
maintenance (stack churn faster than the fixture suite can absorb),
revisit whether the Academy profile should bind to a slower-moving
software stack (e.g. CPU-only) by ADR.
