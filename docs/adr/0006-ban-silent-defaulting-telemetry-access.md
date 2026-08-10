# ADR-0006 — Ban silent-defaulting telemetry access; hallucinated-interface patterns fail closed
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-08 · Status: accepted
Deciders: John (owner-directed rule and rationale, in-session 2026-08-08) ·

> **Namespec note (ADR-0008):** this record predates Namespec 2.0 and uses
> Namespec 1.0 names; read it through the concordance in
> [`0008-namespec-2.0.md`](0008-namespec-2.0.md).
Tracker: simic-108cdb52bc

Amends: —
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

The first scar stratum of the esper lineage
(`../design/01-claim.md#26-the-empirical-driver-the-predecessor-record`):
machine-generated telemetry code contained **hallucinated interfaces** —
plausible-looking accessors for fields that did not exist — and permissive
defaulting access (`.get()` with a silent default) converted those
hallucinations into zero-filled telemetry reads. The host signal existed;
the read path fabricated zeros over it, and the reward read collapsed
without one error raised. The predecessor's remediation was severe enough
to become tooling: a custom CI ban on defaulting telemetry access.

This is not merely a telemetry bug. It is an **AI-code-generation safety
rule**: a model can hallucinate an interface and then use permissive
access idioms to hide the hallucination behind silent defaults —
machine-generated plausible-looking code masking missing reality. Since
Simic is built substantially by code-generating agents, the defect class
must be unrepresentable, not reviewed for.

INV-38 (failure visibility), INV-24 (fail-closed typed compatibility) and
ADR-0002's runtime policy P2 (unmeasured ≠ zero) state the *principle*;
this ADR binds its **code-level enforcement** for Phase A onward.

## Decision

Telemetry access is **typed, explicit, and fail-closed**, enforced
mechanically:

1. **No silent defaults.** Absent values are represented as `None` or
   `validity_mask=false` — never silently converted to `0`, `[]`, `{}`,
   `""` or any other fabricated default. This applies to every
   telemetry-bearing record (`TelemetryEnvelope` first among them) and to
   every consumer-side read.
2. **Typed accessors only.** Field access on telemetry objects goes
   through schema-validated typed objects (Leyline contract types), never
   through dynamic dictionary-style access. Untyped defaulting access
   patterns (`.get(key, default)`, `getattr(obj, name, default)`,
   `dict[key] or default` idioms) on telemetry paths are **rejected in
   CI/lint**.
3. **Unknown names fail closed.** A read of a field the schema does not
   declare is an error at authoring time (type check) and at runtime
   (fail-closed), never a default. A hallucinated field name cannot
   return a value.
4. **Property tests accompany the contracts** (`tests/contracts/`):
   missing field ⇒ exception or explicit invalid marker, never zero;
   undeclared field name ⇒ fail closed; a `validity_mask=false` field is
   unreadable as a value through the typed accessor.
5. **The negative-space gate runs before any generative subsystem is
   enabled**: the poison-pill / signal-preservation harness
   (simic-5503bbe389) corrupts or drops fields and asserts loud refusal —
   never a well-formed defaulted envelope.

Enforcement wiring is Phase A work: the lint rule lands in pre-commit/CI
beside the forbidden-import checks (`../design/ops/repo-structure.md`),
preferring the Weft tooling's style-regime partitioning over a hand-rolled
linter where it fits, with a plain AST rule as fallback.

## Displaced constraints

None displaced. This ADR operationalizes INV-38, INV-24 and ADR-0002 P2 at
the code-access layer; it adds enforcement, not new constitutional
semantics. Scope note: the ban binds **telemetry and Leyline contract
paths**; ordinary non-contract mappings (build scripts, config plumbing)
are out of scope unless they feed a contract.

## Options considered

- **Convention plus code review** — rejected: the esper honour system;
  the defect class is specifically *plausible-looking* code, which is what
  review is worst at catching, and most authoring here is by the same
  class of model that produced the original hallucinations.
- **Permit `.get()` with a logged default** — rejected: a logged
  fabrication is still a fabrication; downstream consumers cannot
  distinguish it from measurement, which is exactly the silent-default
  class ADR-0002 P2 exists to kill.
- **Runtime validation only** — rejected as sole mechanism: it catches
  the read at execution, after the hallucinated interface is already
  woven through the code; the lint catches it at authoring time. Both are
  kept (defense in depth), but lint is the gate.

## Consequences

- The hallucinated-interface failure mode becomes unrepresentable on
  contract paths: there is no idiom left through which an invented field
  silently yields a value.
- Slight ergonomics cost on telemetry consumers (explicit
  validity handling instead of one-line defaults) — accepted; that
  explicitness *is* the record of what was and wasn't measured.
- Phase A acquires two concrete deliverables: the CI/lint rule and the
  contract property tests (folds into
  `../design/programme/evaluation.md#212-leyline-contract-tests`); the
  poison-pill harness (simic-5503bbe389) is the acceptance gate.
- The axiom-contract-engineering pack commission
  (`../product/commissioning/axiom-contract-engineering.md`) already
  carries silent-default elimination as its centre of gravity; this ADR
  is the binding rule that pack's guidance implements.
- **Reversal trigger:** none for the principle (absent-is-never-zero is
  constitutional). The *mechanism* may narrow: if the lint rule proves
  too coarse in practice (false positives on genuinely non-contract
  mappings), scope it tighter to Leyline contract types by a superseding
  ADR — never by relaxing the rule on contract paths.
